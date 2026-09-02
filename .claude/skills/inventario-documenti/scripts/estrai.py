#!/usr/bin/env python3
"""
Estrazione del testo di OGNI file censito nel manifest.

Regola che governa tutto: un file non e' "fatto" perche' il programma non ha
sollevato eccezioni. Un PDF scansionato restituisce zero caratteri senza errori,
e da li' nasce l'analisi che sembra completa ma non lo e'. Percio' ogni file
riceve uno stato esplicito, e "poco testo rispetto alle pagine" e' un allarme,
non un successo.

Stati possibili:
  OK             testo estratto e plausibile
  OCR_OK         era una scansione, l'OCR ha prodotto testo
  RICHIEDE_OCR   scansione riconosciuta, OCR non disponibile o non richiesto
  VUOTO          il file non contiene testo (puo' essere legittimo)
  NON_TESTUALE   immagine, CAD, archivio: nessun testo da estrarre per natura
  PROTETTO       cifrato o protetto da password
  MANCA_STRUMENTO  serve un programma non installato (il messaggio dice quale)
  ERRORE         lettura fallita, motivo registrato
  DUPLICATO      contenuto identico a un file gia' estratto
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, zipfile, zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from xml.etree import ElementTree as ET

# Sotto questa densita' di caratteri per pagina un PDF e' quasi certamente
# una scansione: il testo "estratto" sono solo intestazioni o timbri digitali.
SOGLIA_CARATTERI_PER_PAGINA = 100
# Sotto questa soglia una singola pagina si considera muta (nessun testo utile).
SOGLIA_PAGINA_MUTA = 50
# Motori che fanno gia' l'OCR da soli: su questi non ha senso rilanciarlo.
MOTORI_CON_OCR = {"docling"}
EXT2CAT_RUNTIME = {
    ".pdf": "pdf", ".docx": "testo", ".doc": "testo", ".rtf": "testo", ".odt": "testo",
    ".xlsx": "foglio", ".xls": "foglio", ".ods": "foglio", ".pptx": "presentazione",
    ".ppt": "presentazione", ".odp": "presentazione", ".msg": "mail", ".eml": "mail",
    ".png": "immagine", ".jpg": "immagine", ".zip": "archivio",
}
LINGUE_OCR = "ita+eng"


def ha(prog):
    return shutil.which(prog) is not None


def esegui(cmd, timeout=600):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 124, b"", "timeout"
    except FileNotFoundError as e:
        return 127, b"", str(e)


# ---------------------------------------------------------------- OOXML (stdlib)
# docx/xlsx/pptx sono archivi zip con XML dentro: si leggono senza dipendenze.
# Vale la pena farlo a mano perche' cosi' la skill funziona su qualsiasi
# macchina, anche senza openpyxl o python-docx installati.

def _testo_xml(dato: bytes, tag_paragrafo=None) -> str:
    """Concatena il testo dei nodi <t>, inserendo un a capo per paragrafo."""
    try:
        root = ET.fromstring(dato)
    except ET.ParseError:
        return ""
    pezzi = []
    for el in root.iter():
        t = el.tag.rsplit("}", 1)[-1]
        if t == "t" and el.text:
            pezzi.append(el.text)
        elif t in ("br", "cr", "tab"):
            pezzi.append(" ")
        elif tag_paragrafo and t == tag_paragrafo:
            pezzi.append("\n")
    return re.sub(r"\n{3,}", "\n\n", "".join(pezzi))


def leggi_docx(p: Path):
    with zipfile.ZipFile(p) as z:
        nomi = set(z.namelist())
        parti = ["word/document.xml"]
        # Intestazioni, pie' di pagina, note e commenti contengono spesso
        # protocolli e date: in un contenzioso servono quanto il corpo.
        parti += sorted(n for n in nomi
                        if re.match(r"word/(header|footer|footnotes|endnotes|comments)\d*\.xml$", n))
        out = []
        for n in parti:
            if n in nomi:
                out.append(_testo_xml(z.read(n), tag_paragrafo="p"))
    return "\n".join(out), 0


def _stringhe_condivise(z):
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except ET.ParseError:
        return []
    fuori = []
    for si in root:
        fuori.append("".join(t.text or "" for t in si.iter()
                             if t.tag.rsplit("}", 1)[-1] == "t"))
    return fuori


def leggi_xlsx(p: Path):
    """Tutti i fogli, compresi quelli NASCOSTI: nei CME e' li' che si annidano
    i fogli di calcolo intermedi che spiegano un prezzo."""
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    rns = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    with zipfile.ZipFile(p) as z:
        nomi = set(z.namelist())
        sst = _stringhe_condivise(z)
        # mappa rId -> file del foglio
        target = {}
        if "xl/_rels/workbook.xml.rels" in nomi:
            for rel in ET.fromstring(z.read("xl/_rels/workbook.xml.rels")):
                target[rel.get("Id")] = "xl/" + rel.get("Target", "").lstrip("/").replace("xl/", "")
        fogli = []
        if "xl/workbook.xml" in nomi:
            wb = ET.fromstring(z.read("xl/workbook.xml"))
            for sh in wb.iter(f"{ns}sheet"):
                fogli.append((sh.get("name", "?"), target.get(sh.get(f"{rns}id"), ""),
                              sh.get("state", "visible")))
        if not fogli:
            fogli = [(n, n, "visible") for n in sorted(nomi) if n.startswith("xl/worksheets/sheet")]

        out = []
        for nome_foglio, percorso, stato in fogli:
            if percorso not in nomi:
                continue
            try:
                ws = ET.fromstring(z.read(percorso))
            except ET.ParseError:
                continue
            etichetta = f"\n===== FOGLIO: {nome_foglio}" + (
                f"  [NASCOSTO: {stato}]" if stato != "visible" else "") + " =====\n"
            righe = []
            for row in ws.iter(f"{ns}row"):
                celle = []
                for c in row.iter(f"{ns}c"):
                    v = c.find(f"{ns}v")
                    testo = ""
                    if c.get("t") == "s" and v is not None:
                        try:
                            testo = sst[int(v.text)]
                        except (ValueError, IndexError, TypeError):
                            testo = ""
                    elif c.get("t") == "inlineStr":
                        testo = "".join(t.text or "" for t in c.iter(f"{ns}t"))
                    elif v is not None:
                        testo = v.text or ""
                    celle.append(testo.replace("\t", " ").strip())
                while celle and not celle[-1]:
                    celle.pop()
                if any(celle):
                    righe.append("\t".join(celle))
            if righe:
                out.append(etichetta + "\n".join(righe))
    return "\n".join(out), 0


def leggi_pptx(p: Path):
    with zipfile.ZipFile(p) as z:
        diapo = sorted(n for n in z.namelist()
                       if re.match(r"ppt/(slides|notesSlides)/\w+\d+\.xml$", n))
        out = []
        for n in diapo:
            out.append(f"\n===== {n.split('/')[-1]} =====\n" + _testo_xml(z.read(n), "p"))
    return "\n".join(out), len(diapo)


# ---------------------------------------------------------------- PDF
def pdf_docling(p: Path):
    """Motore preferito: Docling (IBM Research).

    Riconosce il layout con modelli addestrati invece che con euristiche, il che
    conta soprattutto sulle tabelle - un libretto delle misure o un CME sono
    tabelle, e da li' escono i numeri che finiscono in una riserva. Include
    l'OCR sulle pagine acquisite a scanner, quindi copre da solo il caso che
    altrimenti resterebbe bloccante.

    Il testo viene ricomposto pagina per pagina seguendo la provenienza di ogni
    elemento, e le pagine che non producono nulla restano segmenti vuoti: senza
    questo allineamento il controllo sul PDF misto non funzionerebbe e le
    citazioni fonte:pagina risulterebbero sfasate.
    """
    try:
        from docling.document_converter import DocumentConverter
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException as e:
        return None, 0, f"docling non utilizzabile ({type(e).__name__})"

    try:
        doc = DocumentConverter().convert(str(p)).document
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException as e:
        # Docling puo' fallire su PDF malformati dove i motori piu' rozzi
        # cavano comunque qualcosa: conviene lasciar proseguire il ripiego.
        return None, 0, f"docling: {type(e).__name__}: {e}"

    try:
        n_pagine = len(getattr(doc, "pages", {}) or {})
        per_pagina = {}
        for elemento, _ in doc.iterate_items():
            pezzo = ""
            if hasattr(elemento, "export_to_markdown"):   # tabelle
                try:
                    pezzo = elemento.export_to_markdown(doc)
                except TypeError:
                    pezzo = elemento.export_to_markdown()
                except Exception:
                    pezzo = ""
            if not pezzo:
                pezzo = getattr(elemento, "text", "") or ""
            if not pezzo.strip():
                continue
            prov = getattr(elemento, "prov", None)
            n = getattr(prov[0], "page_no", 1) if prov else 1
            per_pagina.setdefault(n, []).append(pezzo)

        if per_pagina:
            ultima = max(max(per_pagina), n_pagine or 0)
            pagine = ["\n".join(per_pagina.get(i, [])) for i in range(1, ultima + 1)]
            return "\f".join(pagine), len(pagine), ""

        # Nessuna provenienza utilizzabile: si rinuncia all'allineamento ma non
        # al contenuto. Il numero di pagine dichiarato resta quello vero, cosi'
        # il controllo sulle pagine mute continua a funzionare per conteggio.
        testo = doc.export_to_markdown()
        return testo, n_pagine or max(1, testo.count("\f") + 1), ""
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException as e:
        return None, 0, f"docling, lettura del risultato: {type(e).__name__}: {e}"


def pdf_pdftotext(p: Path):
    rc, so, se = esegui(["pdftotext", "-layout", "-enc", "UTF-8", str(p), "-"])
    if rc != 0:
        return None, 0, se
    t = so.decode("utf-8", "replace")
    return t, max(1, t.count("\f")), ""


def pdf_pypdf(p: Path):
    try:
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException as e:
        # Non solo "non installato": una libreria nativa mal compilata puo'
        # sollevare eccezioni che non derivano da Exception e che, se non
        # intercettate qui, farebbero fallire l'intero lotto per un file.
        return None, 0, f"pypdf non utilizzabile ({type(e).__name__})"
    try:
        r = PdfReader(str(p))
        if getattr(r, "is_encrypted", False):
            try:
                r.decrypt("")
            except Exception:
                return None, 0, "PDF cifrato"
        pagine = [(pg.extract_text() or "") for pg in r.pages]
        return "\f".join(pagine), len(pagine), ""
    except Exception as e:
        return None, 0, f"pypdf: {e}"


def pdf_ocr(p: Path):
    """OCR reale della scansione. ocrmypdf e' la strada migliore perche'
    scrive anche il PDF ricercabile; tesseract da solo e' il ripiego."""
    if ha("ocrmypdf"):
        with tempfile.TemporaryDirectory() as d:
            side, uscita = Path(d) / "t.txt", Path(d) / "o.pdf"
            rc, _, se = esegui(["ocrmypdf", "--force-ocr", "-l", LINGUE_OCR,
                                "--sidecar", str(side), str(p), str(uscita)], timeout=3600)
            if side.exists():
                return side.read_text("utf-8", "replace"), "ocrmypdf", ""
            return None, "ocrmypdf", se[-400:]
    if ha("pdftoppm") and ha("tesseract"):
        with tempfile.TemporaryDirectory() as d:
            rc, _, se = esegui(["pdftoppm", "-r", "300", "-png", str(p), str(Path(d) / "pg")],
                               timeout=3600)
            testi = []
            for img in sorted(Path(d).glob("pg*.png")):
                rc, so, _ = esegui(["tesseract", str(img), "stdout", "-l", LINGUE_OCR], timeout=600)
                testi.append(so.decode("utf-8", "replace"))
            if testi:
                return "\f".join(testi), "tesseract", ""
            return None, "tesseract", se[-400:]
    return None, "", "nessun motore OCR (installare ocrmypdf oppure tesseract)"


def _decodifica_stringa(b: bytes) -> str:
    """Stringa letterale PDF: gestisce gli escape e l'ottale."""
    fuori, i = [], 0
    while i < len(b):
        c = b[i:i+1]
        if c == b"\\" and i + 1 < len(b):
            d = b[i+1:i+2]
            mappa = {b"n": "\n", b"r": "\n", b"t": "\t", b"b": "", b"f": "",
                     b"(": "(", b")": ")", b"\\": "\\"}
            if d in mappa:
                fuori.append(mappa[d]); i += 2; continue
            m = re.match(rb"[0-7]{1,3}", b[i+1:i+4])
            if m:
                fuori.append(chr(int(m.group(), 8))); i += 1 + len(m.group()); continue
            i += 2; continue
        fuori.append(c.decode("latin-1")); i += 1
    return "".join(fuori)


def _testo_da_contenuto(cont: bytes) -> str:
    """Ricava il testo dagli operatori di disegno di un flusso PDF."""
    pezzi = []
    schema = rb"\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]+>|T\*|Td|TD|ET|Tj|TJ|'"
    for m in re.finditer(schema, cont, re.S):
        tok = m.group()
        if tok.startswith(b"("):
            pezzi.append(_decodifica_stringa(tok[1:-1]))
        elif tok.startswith(b"<"):
            esa = re.sub(rb"\s", b"", tok[1:-1])
            if len(esa) % 2:
                esa += b"0"
            try:
                grezzo = bytes.fromhex(esa.decode("ascii"))
                pezzi.append(grezzo.decode("utf-16-be" if grezzo[:2] == b"\xfe\xff" else "latin-1",
                                           "replace").lstrip("\ufeff"))
            except ValueError:
                pass
        elif tok in (b"Td", b"TD", b"T*", b"ET", b"'"):
            pezzi.append("\n")
    return re.sub(r"[ \t]{2,}", " ", re.sub(r"\n{3,}", "\n\n", "".join(pezzi)))


def _oggetti_pdf(dato: bytes):
    return {int(m.group(1)): m.group(2)
            for m in re.finditer(rb"(\d+)\s+0\s+obj\b(.*?)\bendobj", dato, re.S)}


def _flusso(corpo: bytes) -> bytes:
    import re as _re
    m = _re.search(rb"stream\r?\n", corpo)
    if not m:
        return b""
    grezzo = corpo[m.end():]
    f = grezzo.rfind(b"endstream")
    if f >= 0:
        grezzo = grezzo[:f]
    grezzo = grezzo.rstrip(b"\r\n")
    try:
        return zlib.decompress(grezzo)
    except zlib.error:
        try:
            return zlib.decompressobj().decompress(grezzo)
        except Exception:
            return grezzo


def pdf_stdlib(p: Path):
    """Ultimo ripiego, senza alcuna dipendenza esterna.

    Estrae pagina per pagina e non salta quelle prive di testo: per esse emette
    un segmento vuoto. L'allineamento conta due volte. Serve a chi cita un
    documento per pagina, e soprattutto permette di accorgersi delle pagine
    scansionate dentro un PDF altrimenti nativo: se le pagine mute sparissero
    dal risultato, il documento sembrerebbe integro pur essendo monco.
    """
    dato = p.read_bytes()
    if not dato.startswith(b"%PDF-"):
        return None, 0, "l'intestazione non e' quella di un PDF"
    if re.search(rb"/Encrypt\b", dato):
        return None, 0, "PDF cifrato"

    oggetti = _oggetti_pdf(dato)
    pagine = [c for c in oggetti.values() if re.search(rb"/Type\s*/Page\b(?!s)", c)]
    if pagine:
        testi = []
        for corpo in pagine:
            rif = re.search(rb"/Contents\s+(?:(\d+)\s+0\s+R|\[(.*?)\])", corpo, re.S)
            pezzi = []
            if rif:
                numeri = ([int(rif.group(1))] if rif.group(1)
                          else [int(x) for x in re.findall(rb"(\d+)\s+0\s+R", rif.group(2))])
                for n in numeri:
                    cont = _flusso(oggetti.get(n, b""))
                    if b"Tj" in cont or b"TJ" in cont:
                        pezzi.append(_testo_da_contenuto(cont))
            testi.append("\n".join(pezzi))
        return "\f".join(testi), len(pagine), ""

    # Nessun oggetto pagina raggiungibile: succede con gli xref compressi
    # (PDF 1.5+). Si ripiega sulla scansione grezza dei flussi, accettando di
    # perdere l'allineamento ma non il contenuto.
    conta = len(re.findall(rb"/Type\s*/Page(?![s])", dato)) or 1
    testi = []
    for m in re.finditer(rb"stream\r?\n", dato):
        f = dato.find(b"endstream", m.end())
        if f < 0:
            continue
        grezzo = dato[m.end():f].rstrip(b"\r\n")
        try:
            cont = zlib.decompress(grezzo)
        except zlib.error:
            try:
                cont = zlib.decompressobj().decompress(grezzo)
            except Exception:
                cont = grezzo
        if b"Tj" in cont or b"TJ" in cont:
            testi.append(_testo_da_contenuto(cont))
    return "\f".join(testi), conta, ""


def _pagine_mute(testo: str, dichiarate: int):
    """Quali pagine non hanno prodotto testo.

    E' il controllo che smaschera il PDF misto: un fascicolo unico in cui alcune
    pagine sono native e altre acquisite a scanner. La densita' media non lo
    rivela, perche' le pagine native la tengono alta e il documento sembra
    perfettamente estratto; ma le pagine mute sono contenuto che non abbiamo, e
    sono spesso proprio quelle firmate.
    """
    segmenti = testo.split("\f")
    if dichiarate and len(segmenti) == dichiarate:
        mute = [i for i, s in enumerate(segmenti, 1) if len(s.strip()) < SOGLIA_PAGINA_MUTA]
        return len(mute), mute
    con_testo = sum(1 for s in segmenti if len(s.strip()) >= SOGLIA_PAGINA_MUTA)
    return max(0, dichiarate - con_testo), []


def leggi_pdf(p: Path, ocr_modo, motore_scelto="auto"):
    # I motori si provano in ordine di qualita' decrescente. Docling e' il
    # preferito perche' e' l'unico che legge le tabelle con un modello di layout
    # e che porta l'OCR con se'; gli altri restano come ripiego, cosi' la skill
    # continua a funzionare su una macchina dove non e' installato nulla.
    tentativi = []
    if motore_scelto in ("auto", "docling"):
        tentativi.append(("docling", pdf_docling))
    if motore_scelto in ("auto", "classico"):
        if ha("pdftotext"):
            tentativi.append(("pdftotext", pdf_pdftotext))
        tentativi += [("pypdf", pdf_pypdf), ("stdlib", pdf_stdlib)]

    testo, pagine, err, metodo_base = None, 0, "nessun motore disponibile", ""
    for nome, funzione in tentativi:
        testo, pagine, e = funzione(p)
        metodo_base = nome
        if testo is not None:
            break
        err = e or err
    if testo is None:
        if "cifrat" in err.lower() or "encrypt" in err.lower():
            return "", 0, "PROTETTO", "", err
        if ocr_modo != "no":
            t, motore, e2 = pdf_ocr(p)
            if t:
                return t, max(1, t.count("\f") + 1), "OCR_OK", motore, ""
            return "", 0, "MANCA_STRUMENTO", "", f"{err}; {e2}"
        return "", 0, "MANCA_STRUMENTO", "", err + " (installare poppler-utils o pypdf)"

    pagine = max(pagine, 1)
    n_mute, quali = _pagine_mute(testo, pagine)
    con_testo = pagine - n_mute

    def con_ocr(motivo, stato_se_fallisce):
        """Tenta l'OCR; se manca o non migliora, resta lo stato bloccante."""
        if metodo_base in MOTORI_CON_OCR:
            # Rilanciare l'OCR sarebbe inutile e il messaggio "installare
            # ocrmypdf" sarebbe fuorviante: il riconoscimento ottico e' gia'
            # avvenuto. Se il testo resta scarso il problema e' un altro - la
            # scansione e' di cattiva qualita' - e va detto per quello che e',
            # perche' richiede un occhio umano e non un pacchetto in piu'.
            return (testo, pagine,
                    "TESTO_INSUFFICIENTE" if stato_se_fallisce == "RICHIEDE_OCR"
                    else stato_se_fallisce, metodo_base,
                    f"{motivo}; il riconoscimento ottico di {metodo_base} e' gia' stato"
                    " applicato: la scansione e' probabilmente illeggibile e va"
                    " verificata a mano")
        if ocr_modo == "no":
            return testo, pagine, stato_se_fallisce, metodo_base, motivo
        t, motore, e2 = pdf_ocr(p)
        if t and len(t.strip()) > len(testo.strip()):
            return t, max(pagine, t.count("\f") + 1), "OCR_OK", motore, ""
        return testo, pagine, stato_se_fallisce, metodo_base, f"{motivo}; OCR non riuscito: {e2}"

    if con_testo == 0:
        return con_ocr(f"nessuna delle {pagine} pagine produce testo: e' una scansione",
                       "RICHIEDE_OCR")
    if n_mute > 0:
        dove = ((" (pagine " + ", ".join(map(str, quali[:12]))
                 + ("..." if len(quali) > 12 else "") + ")") if quali else "")
        return con_ocr(f"PDF misto: {n_mute} pagine su {pagine} non producono testo{dove};"
                       f" quel contenuto NON e' stato acquisito", "PDF_MISTO")
    densita = len(testo.strip()) / pagine
    if densita < SOGLIA_CARATTERI_PER_PAGINA:
        return con_ocr(f"solo {densita:.0f} caratteri/pagina: probabile scansione", "RICHIEDE_OCR")
    return testo, pagine, "OK", metodo_base, ""


# ---------------------------------------------------------------- altri formati
def leggi_semplice(p: Path):
    dato = p.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return dato.decode(enc), 0
        except UnicodeDecodeError:
            continue
    return dato.decode("utf-8", "replace"), 0


def leggi_html(p: Path):
    t, _ = leggi_semplice(p)
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    import html as _h
    return re.sub(r"[ \t]{2,}", " ", _h.unescape(t)), 0


def leggi_eml(p: Path):
    import email
    from email import policy
    m = email.message_from_bytes(p.read_bytes(), policy=policy.default)
    testa = [f"{k}: {m.get(k,'')}" for k in ("From", "To", "Cc", "Date", "Subject")]
    corpo, allegati = "", []
    try:
        parte = m.get_body(preferencelist=("plain", "html"))
        if parte:
            corpo = parte.get_content()
            if parte.get_content_type() == "text/html":
                corpo = re.sub(r"(?s)<[^>]+>", " ", corpo)
    except Exception as e:
        corpo = f"[corpo non leggibile: {e}]"
    for a in m.iter_attachments():
        if a.get_filename():
            allegati.append(a.get_filename())
    if allegati:
        testa.append("Allegati: " + ", ".join(allegati))
    return "\n".join(testa) + "\n\n" + corpo, 0


def via_libreoffice(p: Path, formato="txt"):
    """Ripiego universale per .doc .rtf .odt .xls .ppt e simili.
    LibreOffice apre praticamente tutto il legacy dell'ufficio tecnico."""
    prog = "soffice" if ha("soffice") else ("libreoffice" if ha("libreoffice") else None)
    if not prog:
        return None, "LibreOffice non installato"
    with tempfile.TemporaryDirectory() as d:
        rc, _, se = esegui([prog, "--headless", "--norestore",
                            f"-env:UserInstallation=file://{d}/profilo",
                            "--convert-to", formato, "--outdir", d, str(p)], timeout=900)
        prodotti = list(Path(d).glob(f"*.{formato.split(':')[0]}"))
        if not prodotti:
            return None, f"conversione fallita: {se[-300:]}"
        q = prodotti[0]
        if formato.startswith("txt"):
            for enc in ("utf-8", "cp1252", "latin-1"):
                try:
                    return q.read_text(enc), ""
                except UnicodeDecodeError:
                    continue
            return q.read_text("utf-8", "replace"), ""
        dest = Path(tempfile.mkdtemp()) / q.name
        shutil.copy2(q, dest)
        return dest, ""


def tipo_reale(p: Path, ext: str):
    """Riconosce il formato dai byte iniziali, non dall'estensione.

    Nei fascicoli reali l'estensione mente spesso: un .xls salvato da Excel
    recente e' in realta' un .xlsx, un .doc rinominato a mano e' un .docx, un
    allegato di posta arriva senza estensione. Fidarsi del nome del file
    manderebbe questi documenti sul convertitore sbagliato, che fallisce e li
    fa finire tra gli irrecuperabili pur essendo perfettamente leggibili.

    Restituisce (estensione_effettiva, avviso) dove l'avviso e' non vuoto solo
    quando il contenuto smentisce l'estensione: e' un'informazione che l'utente
    deve vedere, perche' spesso segnala un file rinominato per sbaglio.
    """
    try:
        with p.open("rb") as f:
            testa = f.read(8)
    except OSError:
        return ext, ""

    def esito(vero):
        if vero == ext:
            return ext, ""
        return vero, f"estensione {ext or '(assente)'} ma il contenuto e' {vero}"

    if testa.startswith(b"%PDF-"):
        return esito(".pdf")
    if testa.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(p) as z:
                nomi = z.namelist()
        except (zipfile.BadZipFile, OSError):
            return ext, ""
        if "word/document.xml" in nomi:
            return esito(".docx")
        if "xl/workbook.xml" in nomi:
            return esito(".xlsx")
        if "ppt/presentation.xml" in nomi:
            return esito(".pptx")
        if any(n.startswith("content.xml") for n in nomi):
            # OpenDocument: lo tratta LibreOffice, ma almeno non finisce
            # sul percorso sbagliato per colpa del nome.
            return esito(ext if ext in (".odt", ".ods", ".odp") else ".odt")
        return esito(".zip")
    if testa.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        # Contenitore OLE2: sono i vecchi formati Office (.doc .xls .ppt) e i .msg.
        if ext in (".doc", ".xls", ".ppt", ".msg"):
            return ext, ""
        return ".doc", f"estensione {ext or '(assente)'} ma il contenuto e' un file Office legacy"
    if testa.startswith(b"{\\rt"):
        return esito(".rtf")
    if testa[:4] in (b"\x89PNG",) or testa[:3] == b"\xff\xd8\xff" or testa[:4] == b"GIF8":
        return esito(".png" if testa[:4] == b"\x89PNG" else ".jpg")
    return ext, ""


def estrai_uno(v: dict, radice: Path, cartella_testi: Path, ocr_modo: str,
               motore: str = "auto"):
    p = radice / v["percorso"]
    cat, ext = v["categoria"], v["ext"]
    testo, pagine, stato, metodo, nota = "", 0, "ERRORE", "", ""
    ext_reale, avviso = tipo_reale(p, ext)
    if avviso:
        ext = ext_reale
        cat = EXT2CAT_RUNTIME.get(ext, cat)
    try:
        if cat in ("immagine", "cad", "archivio"):
            stato, nota = "NON_TESTUALE", "nessun testo da estrarre per natura del file"
            if cat == "immagine" and ocr_modo != "no" and ha("tesseract"):
                rc, so, _ = esegui(["tesseract", str(p), "stdout", "-l", LINGUE_OCR], timeout=300)
                if rc == 0 and len(so.strip()) > 20:
                    testo, stato, metodo = so.decode("utf-8", "replace"), "OCR_OK", "tesseract"
                    nota = ""
        elif ext == ".pdf":
            testo, pagine, stato, metodo, nota = leggi_pdf(p, ocr_modo, motore)
        elif ext in (".docx",):
            testo, pagine = leggi_docx(p); stato, metodo = "OK", "ooxml"
        elif ext in (".xlsx", ".xlsm", ".xltx"):
            testo, pagine = leggi_xlsx(p); stato, metodo = "OK", "ooxml"
        elif ext in (".pptx",):
            testo, pagine = leggi_pptx(p); stato, metodo = "OK", "ooxml"
        elif ext in (".txt", ".md", ".csv", ".tsv", ".json", ".xml"):
            testo, pagine = leggi_semplice(p); stato, metodo = "OK", "diretto"
        elif ext in (".html", ".htm"):
            testo, pagine = leggi_html(p); stato, metodo = "OK", "html"
        elif ext == ".eml":
            testo, pagine = leggi_eml(p); stato, metodo = "OK", "email"
        elif ext == ".msg":
            try:
                import extract_msg
                m = extract_msg.Message(str(p))
                testo = (f"From: {m.sender}\nTo: {m.to}\nDate: {m.date}\n"
                         f"Subject: {m.subject}\n\n{m.body or ''}")
                stato, metodo = "OK", "extract_msg"
            except ImportError:
                stato, nota = "MANCA_STRUMENTO", "installare: pip install extract-msg"
            except Exception as e:
                stato, nota = "ERRORE", str(e)
        elif ext in (".doc", ".rtf", ".odt", ".xls", ".ods", ".ppt", ".odp"):
            # I fogli legacy vanno prima portati a xlsx, altrimenti la conversione
            # in txt appiattisce tutto su un solo foglio e si perdono dati.
            if ext in (".xls", ".ods"):
                q, err = via_libreoffice(p, "xlsx")
                if isinstance(q, Path):
                    testo, pagine = leggi_xlsx(q)
                    shutil.rmtree(q.parent, ignore_errors=True)
                    stato, metodo = "OK", "libreoffice+ooxml"
                else:
                    stato, nota = "MANCA_STRUMENTO", err
            else:
                t, err = via_libreoffice(p, "txt:Text (encoded):UTF8")
                if t is None:
                    t, err2 = via_libreoffice(p, "txt")
                    err = err or err2
                if t is None:
                    stato, nota = "MANCA_STRUMENTO", err
                else:
                    testo, stato, metodo = t, "OK", "libreoffice"
        else:
            t, err = via_libreoffice(p, "txt")
            if t is None:
                stato, nota = "NON_TESTUALE", f"estensione {ext or '(nessuna)'} non gestita; {err}"
            else:
                testo, stato, metodo = t, "OK", "libreoffice"
    except zipfile.BadZipFile:
        stato, nota = "ERRORE", "archivio Office corrotto o file rinominato"
    except PermissionError:
        stato, nota = "ERRORE", "permesso negato"
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException as e:
        # Rete di sicurezza deliberatamente larga: su un fascicolo di centinaia
        # di atti, un singolo file corrotto o una libreria difettosa non devono
        # far perdere il lavoro su tutti gli altri. Il file viene marcato come
        # ERRORE e comparira' nel cancello di copertura.
        stato, nota = "ERRORE", f"{type(e).__name__}: {e}"

    testo = (testo or "").replace("\x00", "")
    if stato == "OK" and len(testo.strip()) == 0:
        stato, nota = "VUOTO", nota or "il file non contiene testo estraibile"

    if testo.strip():
        dest = cartella_testi / f"{v['id']:04d}__{re.sub(r'[^A-Za-z0-9._-]+', '_', v['nome'])[:80]}.txt"
        intestazione = (f"### FILE #{v['id']}: {v['percorso']}\n"
                        f"### metodo={metodo} pagine={pagine} caratteri={len(testo)}\n\n")
        dest.write_text(intestazione + testo, encoding="utf-8")
        v["testo"] = str(dest.name)
    # La nota viene riscritta da zero a ogni estrazione, non accodata a quella
    # precedente: un rilancio serve a produrre una diagnosi aggiornata, e una
    # nota stratificata finirebbe per contenere consigli ormai sbagliati -
    # per esempio "installare ocrmypdf" accanto a un file poi letto da Docling.
    note = [x for x in (avviso, nota) if x]
    v.update(estrazione=stato, metodo=metodo, caratteri=len(testo.strip()),
             pagine=pagine, nota="; ".join(dict.fromkeys(note)))
    return v


def main():
    ap = argparse.ArgumentParser(description="Estrae il testo di ogni file del manifest.")
    ap.add_argument("inventario", help="cartella _inventario (o la radice della commessa)")
    ap.add_argument("--ocr", choices=["auto", "no"], default="auto",
                    help="auto = usa l'OCR sulle scansioni se disponibile (default)")
    ap.add_argument("--motore", choices=["auto", "docling", "classico"], default="auto",
                    help="auto = usa Docling se installato, altrimenti i motori classici")
    ap.add_argument("--jobs", type=int, default=max(2, (os.cpu_count() or 4) // 2))
    ap.add_argument("--solo-mancanti", action="store_true",
                    help="rilavora solo i file non ancora completati")
    a = ap.parse_args()

    base = Path(a.inventario).expanduser().resolve()
    inv = base if (base / "manifest.json").exists() else base / "_inventario"
    mf = inv / "manifest.json"
    if not mf.exists():
        sys.exit(f"ERRORE: manifest non trovato in {inv}. Eseguire prima inventario.py.")
    M = json.loads(mf.read_text("utf-8"))
    radice, testi = Path(M["radice"]), inv / "testi"
    testi.mkdir(exist_ok=True)

    da_fare = [v for v in M["file"]
               if not a.solo_mancanti or v["estrazione"] in ("DA_FARE", "ERRORE", "MANCA_STRUMENTO")]
    # I duplicati per contenuto si estraggono una volta sola: e' lo stesso testo.
    visti = {}
    lavoro = []
    for v in da_fare:
        if v["sha256"] and v["sha256"] in visti:
            v.update(estrazione="DUPLICATO", metodo="", caratteri=0,
                     nota=f"contenuto identico a #{visti[v['sha256']]}")
            continue
        if v["sha256"]:
            visti[v["sha256"]] = v["id"]
        lavoro.append(v)

    disponibile = "no"
    if a.motore in ("auto", "docling"):
        try:
            import docling  # noqa: F401
            disponibile = "si"
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:
            disponibile = "no"
    print(f"Estrazione di {len(lavoro)} file (OCR: {a.ocr}, motore: {a.motore}, "
          f"Docling installato: {disponibile})...")
    if a.motore == "auto" and disponibile == "no":
        print("  Nota: senza Docling i PDF vengono letti con i motori classici,")
        print("        meno accurati sulle tabelle. Vedi references/formati.md.")
    fatti = 0
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for v in ex.map(lambda x: estrai_uno(x, radice, testi, a.ocr, a.motore), lavoro):
            fatti += 1
            if fatti % 10 == 0 or fatti == len(lavoro):
                print(f"  {fatti}/{len(lavoro)}", flush=True)

    mf.write_text(json.dumps(M, ensure_ascii=False, indent=1), encoding="utf-8")
    conta = {}
    for v in M["file"]:
        conta[v["estrazione"]] = conta.get(v["estrazione"], 0) + 1
    print("\nEsito estrazione:")
    for s, n in sorted(conta.items(), key=lambda x: -x[1]):
        print(f"  {s:16s} {n:5d}")
    print("\nProssimo passo: registro.py stato")


if __name__ == "__main__":
    main()
