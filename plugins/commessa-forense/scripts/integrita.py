#!/usr/bin/env python3
"""
Integrita' dei PDF e OCR a monte.

Fa le due cose che l'indicizzatore di commessa-rag non fa, e le fa prima che
indicizzi, cosi' che quando tocca a lui il fascicolo sia gia' sano:

1. Controlla ogni PDF PAGINA PER PAGINA. Un fascicolo in cui alcune pagine sono
   native e altre acquisite a scanner supera qualsiasi controllo basato sulla
   media: le pagine native tengono alta la resa e il documento sembra integro
   mentre quelle mute spariscono. In un registro di contabilita' le pagine
   scansionate sono di norma proprio quelle firmate.

2. Passa all'OCR le scansioni e ne MISURA la resa. Un OCR che gira senza errori
   ma produce caratteri senza senso e' peggio di un OCR mancato, perche' il
   testo illeggibile viene indicizzato e citato. La misura serve a produrre
   l'elenco corto dei documenti da riprendere a mano.

Tutto in locale: gli atti di un contenzioso non escono dalla macchina.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile, unicodedata, zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SOGLIA_PAGINA_MUTA = 50        # sotto questi caratteri una pagina non ha testo utile
SOGLIA_QUALITA_OCR = 0.12      # quota minima di parole comuni italiane riconosciute
LINGUE_OCR = "ita+eng"

# Parole italiane ad altissima frequenza piu' il lessico ricorrente di appalti e
# contabilita' dei lavori. Servono a misurare se un testo e' italiano leggibile:
# la prosa vera ne contiene in quantita', il rumore di un OCR fallito quasi mai.
PAROLE_COMUNI = set("""
il lo la i gli le un uno una di a da in con su per tra fra del dello della dei degli
delle al allo alla ai agli alle dal dallo dalla dai dagli dalle nel nello nella nei
negli nelle sul sullo sulla sui sugli sulle col coi e ed o od ma se che chi cui non
si ne ci vi come dove quando quanto quale quali questo questa questi queste quello
quella quelli quelle stesso stessa essere sono stato stata stati state era erano
sara essere avere ha hanno aveva avevano avuto viene vengono venga stata deve devono
puo possono presente presenti seguente seguenti sopra sotto oltre entro senza contro
dopo prima durante mediante ai sensi articolo art comma lettera punto allegato
lavori lavoro opera opere appalto appaltatore appaltante stazione impresa direttore
direzione cantiere contratto contrattuale importo importi euro prezzo prezzi prezzo
unitario quantita computo metrico estimativo variante perizia riserva riserve
iscritta iscritte registro contabilita libretto misure stato avanzamento sal
certificato pagamento collaudo ultimazione consegna sospensione ripresa proroga
verbale ordine servizio comunicazione nota protocollo prot data del oggetto
responsabile procedimento rup progetto progettazione esecuzione esecutivo
oneri sicurezza ribasso offerta gara bando disciplinare capitolato speciale
scavo rilevato conglomerato bituminoso barriera sicurezza opere murarie
metri metro cubi cubo quadrati quadrato lineari ml mq mc kg ton corpo
maggiori minori nuovi nuovo compensato compenso danno risarcimento
""".split())


def normalizza(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t.lower())
                   if unicodedata.category(c) != "Mn")


def qualita_testo(testo: str):
    """Quanto un testo somiglia a italiano leggibile.

    Restituisce (quota_parole_riconosciute, n_parole). Non e' un giudizio
    linguistico: e' un rilevatore di spazzatura. Un OCR riuscito su una pagina
    italiana supera ampiamente la soglia; uno fallito produce token che non
    somigliano a nulla e resta vicino a zero.
    """
    parole = re.findall(r"[a-zA-Zàèéìòùáíóúäöü]{2,}", normalizza(testo))
    if len(parole) < 20:
        return None, len(parole)      # troppo poche per misurare
    riconosciute = sum(1 for p in parole if p in PAROLE_COMUNI)
    return riconosciute / len(parole), len(parole)


def ha(prog):
    return shutil.which(prog) is not None


def esegui(cmd, timeout=3600):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 124, b"", "timeout"
    except FileNotFoundError as e:
        return 127, b"", str(e)


# ------------------------------------------------------- lettura per pagina
def _decodifica(b: bytes) -> str:
    fuori, i = [], 0
    while i < len(b):
        c = b[i:i + 1]
        if c == b"\\" and i + 1 < len(b):
            d = b[i + 1:i + 2]
            mappa = {b"n": "\n", b"r": "\n", b"t": "\t", b"(": "(", b")": ")", b"\\": "\\"}
            if d in mappa:
                fuori.append(mappa[d]); i += 2; continue
            m = re.match(rb"[0-7]{1,3}", b[i + 1:i + 4])
            if m:
                fuori.append(chr(int(m.group(), 8))); i += 1 + len(m.group()); continue
            i += 2; continue
        fuori.append(c.decode("latin-1")); i += 1
    return "".join(fuori)


def _testo_contenuto(cont: bytes) -> str:
    pezzi = []
    for m in re.finditer(rb"\((?:\\.|[^\\()])*\)|<[0-9A-Fa-f\s]+>|T\*|Td|TD|ET|Tj|TJ|'", cont, re.S):
        tok = m.group()
        if tok.startswith(b"("):
            pezzi.append(_decodifica(tok[1:-1]))
        elif tok.startswith(b"<"):
            esa = re.sub(rb"\s", b"", tok[1:-1])
            if len(esa) % 2:
                esa += b"0"
            try:
                g = bytes.fromhex(esa.decode("ascii"))
                pezzi.append(g.decode("utf-16-be" if g[:2] == b"\xfe\xff" else "latin-1",
                                      "replace").lstrip("﻿"))
            except ValueError:
                pass
        else:
            pezzi.append("\n")
    return re.sub(r"\n{3,}", "\n\n", "".join(pezzi))


def pagine_stdlib(p: Path):
    """Testo di ogni pagina, senza dipendenze. Le pagine mute restano vuote:
    e' l'assenza, non la presenza, l'informazione che stiamo cercando."""
    dato = p.read_bytes()
    if not dato.startswith(b"%PDF-"):
        return None, "non e' un PDF"
    if re.search(rb"/Encrypt\b", dato):
        return None, "PDF cifrato"
    oggetti = {int(m.group(1)): m.group(2)
               for m in re.finditer(rb"(\d+)\s+0\s+obj\b(.*?)\bendobj", dato, re.S)}
    pagine = [c for c in oggetti.values() if re.search(rb"/Type\s*/Page\b(?!s)", c)]
    if not pagine:
        return None, "struttura del PDF non leggibile (xref compresso)"
    fuori = []
    for corpo in pagine:
        rif = re.search(rb"/Contents\s+(?:(\d+)\s+0\s+R|\[(.*?)\])", corpo, re.S)
        pezzi = []
        if rif:
            numeri = ([int(rif.group(1))] if rif.group(1)
                      else [int(x) for x in re.findall(rb"(\d+)\s+0\s+R", rif.group(2))])
            for n in numeri:
                c = oggetti.get(n, b"")
                m = re.search(rb"stream\r?\n", c)
                if not m:
                    continue
                g = c[m.end():]
                f = g.rfind(b"endstream")
                g = (g[:f] if f >= 0 else g).rstrip(b"\r\n")
                try:
                    cont = zlib.decompress(g)
                except zlib.error:
                    try:
                        cont = zlib.decompressobj().decompress(g)
                    except Exception:
                        cont = g
                if b"Tj" in cont or b"TJ" in cont:
                    pezzi.append(_testo_contenuto(cont))
        fuori.append("\n".join(pezzi))
    return fuori, ""


def pagine_pdftotext(p: Path):
    rc, so, se = esegui(["pdftotext", "-layout", "-enc", "UTF-8", str(p), "-"], timeout=600)
    if rc != 0:
        return None, se[-200:]
    return so.decode("utf-8", "replace").split("\f"), ""


def leggi_pagine(p: Path):
    if ha("pdftotext"):
        pg, err = pagine_pdftotext(p)
        if pg is not None:
            while pg and not pg[-1].strip():
                pg.pop()
            return pg, "pdftotext", err
    pg, err = pagine_stdlib(p)
    return pg, "stdlib", err


# ------------------------------------------------------- OCR
def ocr_su_disco(sorgente: Path, destinazione: Path):
    """Produce un PDF ricercabile accanto all'originale.

    Scrivere il risultato su disco, invece di tenerlo in memoria, e' il punto:
    l'indicizzatore di commessa-rag richiede l'OCR "a monte" e legge dal file.
    L'originale non viene mai toccato - in un contenzioso e' la prova.
    """
    if ha("ocrmypdf"):
        with tempfile.TemporaryDirectory() as d:
            side = Path(d) / "t.txt"
            rc, _, se = esegui(["ocrmypdf", "--redo-ocr", "--deskew", "-l", LINGUE_OCR,
                                "--sidecar", str(side), str(sorgente), str(destinazione)])
            if destinazione.exists():
                return side.read_text("utf-8", "replace") if side.exists() else "", "ocrmypdf", ""
            # --redo-ocr rifiuta certi PDF: si ripiega sul riconoscimento forzato.
            rc, _, se2 = esegui(["ocrmypdf", "--force-ocr", "--deskew", "-l", LINGUE_OCR,
                                 "--sidecar", str(side), str(sorgente), str(destinazione)])
            if destinazione.exists():
                return side.read_text("utf-8", "replace") if side.exists() else "", "ocrmypdf", ""
            return None, "ocrmypdf", (se2 or se)[-300:]
    if ha("pdftoppm") and ha("tesseract"):
        with tempfile.TemporaryDirectory() as d:
            esegui(["pdftoppm", "-r", "300", "-png", str(sorgente), str(Path(d) / "pg")])
            immagini = sorted(Path(d).glob("pg*.png"))
            if not immagini:
                return None, "tesseract", "conversione in immagini fallita"
            testi, pezzi = [], []
            for img in immagini:
                base = str(img.with_suffix(""))
                esegui(["tesseract", str(img), base, "-l", LINGUE_OCR, "pdf", "txt"], timeout=900)
                q = Path(base + ".pdf")
                if q.exists():
                    pezzi.append(q)
                t = Path(base + ".txt")
                testi.append(t.read_text("utf-8", "replace") if t.exists() else "")
            if pezzi and ha("pdfunite"):
                esegui(["pdfunite"] + [str(x) for x in pezzi] + [str(destinazione)])
            if not destinazione.exists() and pezzi:
                shutil.copy2(pezzi[0], destinazione)
            return "\f".join(testi), "tesseract", ("" if destinazione.exists()
                                                   else "PDF ricercabile non prodotto")
    return None, "", "nessun motore OCR installato (installare ocrmypdf oppure tesseract)"


def motori_disponibili():
    return {p: ha(p) for p in ("pdftotext", "ocrmypdf", "tesseract", "pdftoppm", "pdfunite")}


# ------------------------------------------------------- analisi di un PDF
def esamina(percorso: Path, radice: Path, ocr_attivo: bool, suffisso: str):
    rel = str(percorso.relative_to(radice))
    esito = {"file": rel, "stato": "", "pagine": 0, "pagine_mute": [], "motore": "",
             "qualita_ocr": None, "ocr_prodotto": "", "nota": ""}
    pagine, motore, err = leggi_pagine(percorso)
    esito["motore"] = motore
    if pagine is None:
        esito.update(stato="ILLEGGIBILE", nota=err)
        return esito

    esito["pagine"] = len(pagine)
    mute = [i for i, t in enumerate(pagine, 1) if len(t.strip()) < SOGLIA_PAGINA_MUTA]
    esito["pagine_mute"] = mute

    if not mute:
        esito["stato"] = "INTEGRO"
        return esito

    tipo = "SCANSIONE" if len(mute) == len(pagine) else "MISTO"
    if not ocr_attivo:
        esito.update(stato=f"DA_OCR_{tipo}",
                     nota=f"{len(mute)} pagine su {len(pagine)} senza testo")
        return esito

    destinazione = percorso.with_name(percorso.stem + suffisso + ".pdf")
    testo, quale, err = ocr_su_disco(percorso, destinazione)
    if testo is None:
        esito.update(stato=f"OCR_FALLITO_{tipo}", nota=err)
        return esito

    quota, n_parole = qualita_testo(testo)
    esito["ocr_prodotto"] = str(destinazione.relative_to(radice))
    esito["qualita_ocr"] = round(quota, 3) if quota is not None else None
    esito["motore"] = f"{motore}+{quale}"

    if quota is None:
        esito.update(stato="OCR_POVERO",
                     nota=f"l'OCR ha prodotto solo {n_parole} parole: troppo poche "
                          "per essere un documento di testo, va guardato a mano")
    elif quota < SOGLIA_QUALITA_OCR:
        esito.update(stato="OCR_POVERO",
                     nota=f"solo il {quota:.0%} delle parole e' italiano riconoscibile "
                          f"(soglia {SOGLIA_QUALITA_OCR:.0%}): scansione di cattiva qualita', "
                          "da riprendere a mano prima di citarne virgolettati")
    else:
        esito.update(stato="OCR_OK",
                     nota=f"{len(mute)} pagine riconosciute, {quota:.0%} di parole italiane")
    return esito


def main():
    ap = argparse.ArgumentParser(description="Integrita' pagina per pagina dei PDF e OCR a monte.")
    ap.add_argument("cartella")
    ap.add_argument("--no-ocr", action="store_true", help="solo diagnosi, non produce nulla")
    ap.add_argument("--suffisso", default="_OCR",
                    help="suffisso del PDF ricercabile prodotto (default: _OCR)")
    ap.add_argument("--jobs", type=int, default=max(2, (os.cpu_count() or 4) // 2))
    ap.add_argument("--out", help="dove scrivere integrita.json (default: <cartella>/_inventario)")
    a = ap.parse_args()

    radice = Path(a.cartella).expanduser().resolve()
    if not radice.is_dir():
        sys.exit(f"ERRORE: '{radice}' non e' una cartella.")
    out = Path(a.out).expanduser().resolve() if a.out else radice / "_inventario"
    out.mkdir(parents=True, exist_ok=True)

    motori = motori_disponibili()
    ocr_attivo = not a.no_ocr and (motori["ocrmypdf"] or (motori["tesseract"] and motori["pdftoppm"]))
    print("Strumenti: " + ", ".join(f"{k}={'si' if v else 'NO'}" for k, v in motori.items()))
    if not ocr_attivo and not a.no_ocr:
        print("ATTENZIONE: nessun motore OCR. Le scansioni resteranno senza testo.")
        print("  Debian/Ubuntu: sudo apt install ocrmypdf tesseract-ocr-ita poppler-utils")
        print("  macOS: brew install ocrmypdf tesseract-lang poppler")
        print("  Windows: choco install tesseract poppler && pip install ocrmypdf")

    # I PDF gia' prodotti da noi non vanno riesaminati, o si moltiplicherebbero.
    pdf = [p for p in sorted(radice.rglob("*"))
           if p.is_file() and p.suffix.lower() == ".pdf"
           and a.suffisso not in p.stem and "_inventario" not in p.parts]
    print(f"\nPDF da esaminare: {len(pdf)}")

    esiti = []
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for i, e in enumerate(ex.map(lambda p: esamina(p, radice, ocr_attivo, a.suffisso), pdf), 1):
            esiti.append(e)
            if i % 5 == 0 or i == len(pdf):
                print(f"  {i}/{len(pdf)}", flush=True)

    conta = {}
    for e in esiti:
        conta[e["stato"]] = conta.get(e["stato"], 0) + 1
    (out / "integrita.json").write_text(
        json.dumps({"radice": str(radice), "strumenti": motori, "riepilogo": conta,
                    "file": esiti}, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\nEsito:")
    for s, n in sorted(conta.items(), key=lambda x: -x[1]):
        print(f"  {s:22s} {n:4d}")

    # L'elenco corto: i documenti che meritano un intervento umano.
    critici = [e for e in esiti if e["stato"] not in ("INTEGRO", "OCR_OK")]
    if critici:
        print(f"\nDA RIPRENDERE A MANO ({len(critici)}):")
        for e in critici:
            print(f"  [{e['stato']}] {e['file']}")
            print(f"      {e['nota']}")
    print(f"\nDettaglio: {out/'integrita.json'}")
    return 1 if critici else 0


if __name__ == "__main__":
    sys.exit(main())
