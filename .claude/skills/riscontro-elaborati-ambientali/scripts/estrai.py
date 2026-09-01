#!/usr/bin/env python3
"""Estrae testo, tabelle e profilo strutturale da un elaborato .docx o .pdf.

Gestisce i tre casi che si incontrano nelle pratiche ambientali italiane:
  - .docx           -> python-docx, con le tabelle rese leggibili
  - .pdf nativo     -> pdfplumber
  - .pdf scansione  -> rasterizzazione con pypdfium2 + OCR tesseract (ita)

Il fallback all'OCR e' automatico: se il PDF restituisce meno di una soglia
minima di caratteri per pagina, il livello testo non c'e' e si passa a OCR.

Uso:
    python estrai.py <file> [--out DIR] [--no-ocr] [--dpi-scale 2.2]

Produce <DIR>/<nome>.txt e stampa a video il profilo strutturale piu' la
scansione di copertura dei criteri dell'Allegato V.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

# Termini la cui presenza (e soprattutto il cui contesto) dice se un criterio
# dell'Allegato V e' stato davvero trattato o solo nominato.
CRITERI = {
    "cumulo con altri progetti": ["cumul"],
    "alternative / opzione zero": ["alternativ", "opzione zero"],
    "cambiamento climatico": ["cambiamento climatico", "cambiamenti climatici"],
    "rischio incidenti / calamita": ["gravi incidenti", "calamit"],
    "natura transfrontaliera": ["transfrontalier"],
    "rifiuti e residui": ["rifiut", "residu"],
    "emissioni e atmosfera": ["atmosfer", "emission", "polver"],
    "rumore e vibrazioni": ["rumore", "vibrazion"],
    "salute umana": ["salute"],
    "acque sotterranee": ["acque sotterranee", "falda"],
    "biodiversita / Natura 2000": ["biodiversit", "natura 2000", "zsc", "sic ", "zps"],
    "paesaggio e patrimonio": ["paesagg", "patrimonio culturale", "archeolog"],
    "traffico e viabilita": ["traffic", "viabilit"],
    "monitoraggio": ["monitoragg"],
    "mitigazione": ["mitigaz"],
}

MIN_CHAR_PER_PAGE = 80  # sotto questa soglia il PDF si considera scansionato


def log(msg):
    print(msg, flush=True)


def estrai_docx(path):
    import docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    d = docx.Document(path)
    righe, struttura = [], []
    n_par = n_tab = 0
    for child in d.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p = Paragraph(child, d)
            n_par += 1
            testo = p.text.strip()
            if not testo:
                continue
            stile = p.style.name if p.style is not None else "Normal"
            if stile.startswith(("Heading", "Title")):
                struttura.append((stile, testo, len(righe)))
                righe.append(f"\n[{stile}] {testo}")
            else:
                righe.append(f"[{stile}] {testo}" if stile != "Normal" else testo)
        elif tag == "tbl":
            t = Table(child, d)
            n_tab += 1
            righe.append(f"\n<<<TABELLA {n_tab}>>>")
            for r in t.rows:
                righe.append(" | ".join(c.text.strip().replace("\n", " / ") for c in r.cells))
            righe.append("<<<FINE TABELLA>>>\n")

    cp = d.core_properties
    meta = {
        "paragrafi": n_par, "tabelle": n_tab,
        "autore": cp.author, "creato": str(cp.created), "modificato": str(cp.modified),
    }
    return "\n".join(righe), meta, struttura


def pdf_ha_testo(path, campione=5):
    """Decide se il PDF ha un livello testo campionando le prime pagine.

    Estrarre tutte le pagine solo per scoprire che e' una scansione costa
    minuti su documenti corposi: bastano le prime per capirlo.
    """
    import pdfplumber

    with pdfplumber.open(path) as pdf:
        n = len(pdf.pages)
        quante = min(campione, n)
        car = sum(len(pdf.pages[i].extract_text() or "") for i in range(quante))
        meta = {k: v for k, v in (pdf.metadata or {}).items()
                if k in ("Title", "Author", "Creator", "CreationDate", "ModDate")}
    meta["pagine"] = n
    return car / max(quante, 1), meta


def estrai_pdf_nativo(path):
    import pdfplumber

    parti = []
    with pdfplumber.open(path) as pdf:
        for i, pg in enumerate(pdf.pages, 1):
            parti.append(f"\n===== PAG {i} =====\n{pg.extract_text() or ''}")
    return "".join(parti)


def estrai_pdf_ocr(path, scale):
    import pypdfium2 as pdfium

    if not shutil.which("tesseract"):
        raise RuntimeError(
            "PDF scansionato ma tesseract non e' installato. "
            "Esegui scripts/setup.sh, oppure rilancia con --no-ocr."
        )
    tmp = os.path.join(os.path.dirname(os.path.abspath(path)), ".ocr_tmp")
    os.makedirs(tmp, exist_ok=True)
    try:
        pdf = pdfium.PdfDocument(path)
        parti = []
        for i in range(len(pdf)):
            png = os.path.join(tmp, f"p{i + 1:03d}.png")
            pdf[i].render(scale=scale).to_pil().save(png)
            out = subprocess.run(
                ["tesseract", png, "-", "-l", "ita", "--psm", "6"],
                capture_output=True, text=True,
            )
            parti.append(f"\n===== PAG {i + 1} =====\n{out.stdout}")
            log(f"  OCR pagina {i + 1}/{len(pdf)}")
        return "".join(parti), {"pagine": len(pdf), "ocr": True}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def profilo_pdf(testo):
    """Ricava un indice approssimativo da un PDF: righe che sembrano titoli."""
    pat = re.compile(r"^\s*((?:\d+\.){1,3}\s+\S.{2,90}|[A-ZÀÈÉÌÒÙ][A-ZÀÈÉÌÒÙ \-']{9,90})\s*$")
    voci = []
    for n, riga in enumerate(testo.splitlines()):
        m = pat.match(riga)
        if m:
            voci.append((m.group(1).strip(), n))
    return voci


def copertura(testo):
    basso = testo.lower()
    esiti = []
    for criterio, chiavi in CRITERI.items():
        tot = sum(basso.count(k.lower()) for k in chiavi)
        esiti.append((criterio, tot))
    return esiti


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--out", default=".", help="directory di destinazione del .txt")
    ap.add_argument("--no-ocr", action="store_true", help="non ricadere sull'OCR")
    ap.add_argument("--dpi-scale", type=float, default=2.2, help="scala di rasterizzazione per l'OCR")
    a = ap.parse_args()

    src = a.file
    if not os.path.exists(src):
        sys.exit(f"File non trovato: {src}")
    os.makedirs(a.out, exist_ok=True)
    nome = os.path.splitext(os.path.basename(src))[0]
    dst = os.path.join(a.out, nome + ".txt")
    ext = os.path.splitext(src)[1].lower()

    struttura = None
    if ext in (".docx", ".dotx"):
        testo, meta, struttura = estrai_docx(src)
    elif ext == ".pdf":
        media, meta = pdf_ha_testo(src)
        if media >= MIN_CHAR_PER_PAGE:
            testo = estrai_pdf_nativo(src)
        else:
            log(f"Livello testo assente o insufficiente ({media:.0f} car./pagina sul campione):")
            log("il PDF e' con ogni probabilita' una scansione.")
            if a.no_ocr:
                log("OCR disabilitato: estraggo comunque, il risultato sara' incompleto.")
                testo = estrai_pdf_nativo(src)
            else:
                log(f"Passo all'OCR su {meta['pagine']} pagine — puo' richiedere qualche minuto.")
                testo, meta_ocr = estrai_pdf_ocr(src, a.dpi_scale)
                meta.update(meta_ocr)
    else:
        sys.exit(f"Formato non gestito: {ext}. Attesi .docx o .pdf")

    with open(dst, "w") as f:
        f.write(testo)

    log("\n" + "=" * 62)
    log(f"ESTRATTO  ->  {dst}   ({len(testo):,} caratteri)".replace(",", "."))
    log("=" * 62)
    log("\nMetadati: " + ", ".join(f"{k}={v}" for k, v in meta.items() if v))

    log("\n--- PROFILO STRUTTURALE ---")
    if struttura:
        for stile, titolo, pos in struttura:
            livello = "  " * (int(stile[-1]) - 1 if stile[-1].isdigit() else 0)
            log(f"{livello}{titolo[:88]}")
        log(f"\n({len(struttura)} intestazioni)")
    else:
        voci = profilo_pdf(testo)
        for titolo, _ in voci[:60]:
            log(f"  {titolo[:88]}")
        log(f"\n({len(voci)} titoli probabili — su PDF l'indice e' euristico, verificalo)")

    log("\n--- COPERTURA DEI CRITERI (occorrenze grezze) ---")
    log("Zero = criterio assente. Valore alto NON significa trattato: leggi il")
    log("contesto, spesso il termine ricorre solo nella descrizione del metodo.\n")
    for criterio, n in copertura(testo):
        segno = "  " if n else "!!"
        log(f" {segno} {n:>4}  {criterio}")
    log("")


if __name__ == "__main__":
    main()
