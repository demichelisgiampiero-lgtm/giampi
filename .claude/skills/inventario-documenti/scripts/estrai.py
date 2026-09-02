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


def pdf_stdlib(p: Path):
    """Ultimo ripiego, senza alcuna dipendenza esterna.

    Non regge PDF complessi quanto poppler, ma copre i PDF generati
    digitalmente (che sono la maggioranza degli atti di gara e di contabilita')
    e soprattutto permette al controllo di densita' di funzionare comunque:
    meglio un testo imperfetto ma misurabile che un file dichiarato illeggibile.
    """
    dato = p.read_bytes()
    if not dato.startswith(b"%PDF-"):
        return None, 0, "l'intestazione non e' quella di un PDF"
    if re.search(rb"/Encrypt\b", dato):
        return None, 0, "PDF cifrato"
    pagine = len(re.findall(rb"/Type\s*/Page(?![s])", dato)) or 1
    testi = []
    for m in re.finditer(rb"stream\r?\n", dato):
        inizio = m.end()
        fine = dato.find(b"endstream", inizio)
        if fine < 0:
            continue
        grezzo = dato[inizio:fine].rstrip(b"\r\n")
        try:
            cont = zlib.decompress(grezzo)
        except zlib.error:
            try:
                cont = zlib.decompressobj().decompress(grezzo)
            except Exception:
                cont = grezzo
        if b"Tj" in cont or b"TJ" in cont:
            testi.append(_testo_da_contenuto(cont))
    if not testi:
        # Nessun operatore di testo: e' una scansione pura. Restituire stringa
        # vuota (non None) e' voluto: fa scattare il controllo di densita'
        # e quindi l'OCR, invece di far credere che il file sia illeggibile.
        return "", pagine, ""
    return "\f".join(testi), pagine, ""


def leggi_pdf(p: Path, ocr_modo):
    testo, pagine, err = pdf_pdftotext(p) if ha("pdftotext") else (None, 0, "pdftotext assente")
    metodo_base = "pdftotext"
    if testo is None:
        testo, pagine, err2 = pdf_pypdf(p)
        metodo_base, err = "pypdf", (err2 or err)
    if testo is None:
        testo, pagine, err3 = pdf_stdlib(p)
        metodo_base, err = "stdlib", (err3 or err)
    if testo is None:
        if "cifrat" in err.lower() or "encrypt" in err.lower():
            return "", 0, "PROTETTO", "", err
        if ocr_modo != "no":
            t, motore, e2 = pdf_ocr(p)
            if t:
                return t, max(1, t.count("\f")), "OCR_OK", motore, ""
            return "", 0, "MANCA_STRUMENTO", "", f"{err}; {e2}"
        return "", 0, "MANCA_STRUMENTO", "", err + " (installare poppler-utils o pypdf)"

    pagine = max(pagine, 1)
    densita = len(testo.strip()) / pagine
    if densita < SOGLIA_CARATTERI_PER_PAGINA:
        if ocr_modo == "no":
            return testo, pagine, "RICHIEDE_OCR", metodo_base, \
                   f"solo {densita:.0f} caratteri/pagina: e' una scansione"
        t, motore, e2 = pdf_ocr(p)
        if t and len(t.strip()) > len(testo.strip()):
            return t, max(1, t.count("\f")), "OCR_OK", motore, ""
        return testo, pagine, "RICHIEDE_OCR", metodo_base, \
               f"solo {densita:.0f} caratteri/pagina; OCR non riuscito: {e2}"
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


def estrai_uno(v: dict, radice: Path, cartella_testi: Path, ocr_modo: str):
    p = radice / v["percorso"]
    cat, ext = v["categoria"], v["ext"]
    testo, pagine, stato, metodo, nota = "", 0, "ERRORE", "", ""
    try:
        if cat in ("immagine", "cad", "archivio"):
            stato, nota = "NON_TESTUALE", "nessun testo da estrarre per natura del file"
            if cat == "immagine" and ocr_modo != "no" and ha("tesseract"):
                rc, so, _ = esegui(["tesseract", str(p), "stdout", "-l", LINGUE_OCR], timeout=300)
                if rc == 0 and len(so.strip()) > 20:
                    testo, stato, metodo = so.decode("utf-8", "replace"), "OCR_OK", "tesseract"
                    nota = ""
        elif ext == ".pdf":
            testo, pagine, stato, metodo, nota = leggi_pdf(p, ocr_modo)
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
    v.update(estrazione=stato, metodo=metodo, caratteri=len(testo.strip()),
             pagine=pagine, nota=(v.get("nota") or "") and v["nota"] + "; " or "")
    v["nota"] = (v["nota"] + nota).strip("; ")
    return v


def main():
    ap = argparse.ArgumentParser(description="Estrae il testo di ogni file del manifest.")
    ap.add_argument("inventario", help="cartella _inventario (o la radice della commessa)")
    ap.add_argument("--ocr", choices=["auto", "no"], default="auto",
                    help="auto = usa l'OCR sulle scansioni se disponibile (default)")
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

    print(f"Estrazione di {len(lavoro)} file (OCR: {a.ocr})...")
    fatti = 0
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for v in ex.map(lambda x: estrai_uno(x, radice, testi, a.ocr), lavoro):
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
