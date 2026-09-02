#!/usr/bin/env python3
"""
Ricognizione dell'ambiente: cosa c'e' e cosa manca, prima di cominciare.

Va eseguito per primo, per non accorgersi a meta' analisi che uno strumento
manca. Il controllo sulle librerie di commessa-rag e' quello che conta di piu':
se non riesce a importarle, il suo estrattore non ricava testo da nessun PDF e
li marca tutti 'needs_ocr' - un'etichetta che significa "non ho ricavato testo",
non "e' una scansione". Seguirla alla lettera porterebbe a passare all'OCR
documenti nativi, rasterizzando e riconoscendo da capo parole gia' presenti.
"""
import argparse, importlib.util, json, os, platform, shutil, subprocess, sys
from pathlib import Path

VERDE, ROSSO, GIALLO = "OK  ", "MANCA", "opz."


def c_e(prog):
    return shutil.which(prog)


def modulo(nome):
    try:
        return importlib.util.find_spec(nome) is not None
    except (ImportError, ValueError):
        return False


def esegui(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return 127, ""


def comandi_installazione():
    s = platform.system()
    if s == "Windows":
        return ["  Aprire PowerShell COME AMMINISTRATORE:",
                "    choco install tesseract poppler",
                "    (in Tesseract spuntare i dati lingua Italiano)",
                "  Poi, in un prompt normale:",
                "    pip install ocrmypdf pdfplumber openpyxl python-docx olefile snowballstemmer"]
    if s == "Darwin":
        return ["    brew install ocrmypdf tesseract-lang poppler",
                "    pip3 install pdfplumber openpyxl python-docx olefile snowballstemmer"]
    return ["    sudo apt install ocrmypdf tesseract-ocr tesseract-ocr-ita poppler-utils",
            "    pip3 install pdfplumber openpyxl python-docx olefile snowballstemmer"]


def trova_rag(indicato=None):
    """Cerca rag.py di commessa-rag nei posti dove le skill vengono installate."""
    if indicato:
        p = Path(indicato).expanduser()
        if p.is_file():
            return p
        if (p / "scripts" / "rag.py").is_file():
            return p / "scripts" / "rag.py"
        return None
    basi = [Path.home() / ".claude" / "skills", Path.home() / ".claude" / "plugins",
            Path.cwd() / ".claude" / "skills"]
    for b in basi:
        if b.is_dir():
            for q in b.rglob("commessa-rag/scripts/rag.py"):
                return q
    return None


def main():
    ap = argparse.ArgumentParser(description="Verifica l'ambiente prima di analizzare una commessa.")
    ap.add_argument("--rag", help="percorso di rag.py o della cartella commessa-rag")
    ap.add_argument("--json", action="store_true", help="stampa solo il risultato in JSON")
    a = ap.parse_args()

    esito = {"sistema": f"{platform.system()} {platform.release()}",
             "python": platform.python_version(), "bloccanti": [], "avvisi": []}
    righe = []

    def voce(stato, nome, dettaglio=""):
        righe.append(f"  [{stato}] {nome}" + (f"  {dettaglio}" if dettaglio else ""))

    # --- 1. commessa-rag -----------------------------------------------------
    righe.append("\ncommessa-rag (indice e citazioni)")
    rag = trova_rag(a.rag)
    if not rag:
        voce(ROSSO, "rag.py non trovato",
             "indicarlo con --rag, oppure installare la skill commessa-rag")
        esito["bloccanti"].append("commessa-rag non installato")
        esito["rag"] = None
    else:
        esito["rag"] = str(rag)
        voce(VERDE, "rag.py", str(rag))
        rc, out = esegui([sys.executable, str(rag), "--help"])
        v2 = "verify" in out
        voce(VERDE if v2 else ROSSO, "versione v2 (comando verify)",
             "" if v2 else "e' la v1: il cancello sui virgolettati NON esistera'")
        if not v2:
            esito["bloccanti"].append("commessa-rag e' la v1, manca 'verify'")

        # Le librerie di rag.py, se mancano, lo fanno degradare in silenzio.
        # Non basta cercarne la cartella: una libreria con estensioni native mal
        # compilate e' presente su disco e solleva comunque errore all'uso, e
        # dichiararla installata darebbe una falsa sicurezza. Si prova a
        # importarla davvero, in un processo separato e con la stessa cartella
        # di dipendenze che rag.py antepone al proprio percorso.
        ambiente = dict(os.environ)
        suo = Path.home() / ".commessa-rag" / "pydeps"
        if suo.is_dir():
            ambiente["PYTHONPATH"] = str(suo) + os.pathsep + ambiente.get("PYTHONPATH", "")
        mancanti = []
        for m in ("pdfplumber", "openpyxl", "docx", "olefile", "snowballstemmer"):
            try:
                r = subprocess.run([sys.executable, "-c", f"import {m}"],
                                   capture_output=True, timeout=90, env=ambiente)
                if r.returncode != 0:
                    mancanti.append(m)
            except (subprocess.TimeoutExpired, OSError):
                mancanti.append(m)
        if mancanti:
            voce(ROSSO, "librerie di estrazione", "mancano: " + ", ".join(mancanti))
            righe.append("        ATTENZIONE: senza queste, rag.py marca 'needs_ocr' anche i")
            righe.append("        PDF nativi. Non e' un problema di scansione: e' una libreria.")
            esito["bloccanti"].append("librerie di rag.py non utilizzabili: " + ", ".join(mancanti))
        else:
            voce(VERDE, "librerie di estrazione", "pdfplumber, openpyxl, python-docx, olefile")

    # --- 2. OCR --------------------------------------------------------------
    righe.append("\nOCR (necessario per gli atti scansionati)")
    ocrmypdf, tess, ppm = c_e("ocrmypdf"), c_e("tesseract"), c_e("pdftoppm")
    if ocrmypdf:
        voce(VERDE, "ocrmypdf", ocrmypdf)
    elif tess and ppm:
        voce(GIALLO, "ocrmypdf assente", "si usera' tesseract, con resa inferiore")
        esito["avvisi"].append("ocrmypdf assente: ripiego su tesseract")
    else:
        voce(ROSSO, "nessun motore OCR", "gli atti scansionati resteranno senza testo")
        esito["bloccanti"].append("nessun motore OCR")

    if tess:
        rc, out = esegui([tess, "--list-langs"])
        ita = "ita" in out.split()
        voce(VERDE if ita else ROSSO, "lingua italiana per l'OCR",
             "" if ita else "manca il pacchetto 'ita': l'OCR sbagliera' gli accenti")
        if not ita:
            esito["bloccanti"].append("tesseract senza pacchetto lingua italiana")
    elif ocrmypdf:
        voce(GIALLO, "tesseract non nel PATH", "ocrmypdf potrebbe averlo incorporato")

    # --- 3. estrazione PDF ---------------------------------------------------
    righe.append("\nEstrazione PDF")
    voce(VERDE if c_e("pdftotext") else GIALLO, "pdftotext (poppler)",
         "" if c_e("pdftotext") else "assente: si usera' un estrattore interno, meno preciso sulle tabelle")
    if not c_e("pdftotext"):
        esito["avvisi"].append("poppler assente: tabelle meno precise")
    voce(VERDE if modulo("docling") else GIALLO, "docling",
         "" if modulo("docling") else "assente: opzionale, migliora molto le tabelle")

    # --- 4. il resto ---------------------------------------------------------
    righe.append("\nAltro")
    voce(VERDE if c_e("soffice") or c_e("libreoffice") else GIALLO, "LibreOffice",
         "" if c_e("soffice") or c_e("libreoffice") else "assente: i formati .doc/.xls vecchi non si aprono")
    voce(VERDE if modulo("extract_msg") else GIALLO, "extract-msg",
         "" if modulo("extract_msg") else "assente: le e-mail .msg di Outlook non si leggono (riesportarle in .eml)")

    if a.json:
        print(json.dumps(esito, ensure_ascii=False, indent=1)); return 0

    print("=" * 66)
    print("RICOGNIZIONE DELL'AMBIENTE")
    print("=" * 66)
    print(f"  Sistema: {esito['sistema']}   Python: {esito['python']}")
    print("\n".join(righe))
    print("\n" + "=" * 66)
    if esito["bloccanti"]:
        print("NON SI PUO' PARTIRE. Da risolvere:")
        for b in esito["bloccanti"]:
            print(f"  - {b}")
        print("\nComandi di installazione per questo sistema:")
        for r in comandi_installazione():
            print(r)
        print("\nPoi rieseguire questa ricognizione.")
        return 1
    if esito["avvisi"]:
        print("SI PUO' PARTIRE, con queste avvertenze:")
        for w in esito["avvisi"]:
            print(f"  - {w}")
    else:
        print("AMBIENTE COMPLETO. Si puo' partire.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
