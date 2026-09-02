#!/usr/bin/env python3
"""
Censimento deterministico di una cartella e delle sue sottocartelle.

Produce _inventario/manifest.json (+ .csv): l'elenco COMPLETO dei file presenti.
Questo elenco e' la checklist da cui nessun documento puo' sfuggire: tutto cio'
che viene dopo (estrazione, lettura, report) si misura contro questo numero.
"""
import argparse, csv, hashlib, json, os, sys
from datetime import datetime
from pathlib import Path

CATEGORIE = {
    "pdf":           {".pdf"},
    "foglio":        {".xlsx", ".xlsm", ".xltx", ".xls", ".ods", ".csv", ".tsv"},
    "testo":         {".docx", ".doc", ".rtf", ".odt", ".txt", ".md", ".xml",
                      ".json", ".html", ".htm"},
    "mail":          {".msg", ".eml"},
    "presentazione": {".pptx", ".ppt", ".odp"},
    "immagine":      {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".heic"},
    "cad":           {".dwg", ".dxf", ".dwf", ".ifc", ".rvt", ".skp"},
    "archivio":      {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz"},
}
EXT2CAT = {e: c for c, exts in CATEGORIE.items() for e in exts}

# File di sistema e cartelle di servizio: non sono documenti della commessa.
# Restano comunque contati come "ignorati" per trasparenza.
IGNORA_NOMI = {".DS_Store", "Thumbs.db", "desktop.ini", ".gitkeep", "Icon\r"}
IGNORA_DIR  = {"_inventario", ".git", ".svn", ".hg", "__pycache__", ".Trash",
               "$RECYCLE.BIN", "System Volume Information", ".idea", ".vscode",
               "node_modules", ".venv", "venv"}


def sha256(path: Path, blocco=1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(blocco)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def scansiona(radice: Path, includi_nascosti=False, segui_link=False):
    """Cammina l'albero. Restituisce (file_trovati, ignorati, errori_accesso)."""
    trovati, ignorati, errori = [], [], []
    for dirpath, dirnames, filenames in os.walk(radice, followlinks=segui_link,
                                                onerror=lambda e: errori.append(str(e))):
        # Pota le cartelle di servizio in-place, cosi' os.walk non ci entra.
        dirnames[:] = [d for d in sorted(dirnames)
                       if d not in IGNORA_DIR and (includi_nascosti or not d.startswith("."))]
        for nome in sorted(filenames):
            p = Path(dirpath) / nome
            if nome in IGNORA_NOMI or nome.startswith("~$"):
                ignorati.append((str(p.relative_to(radice)), "file di sistema/lock"))
                continue
            if not includi_nascosti and nome.startswith("."):
                ignorati.append((str(p.relative_to(radice)), "file nascosto"))
                continue
            try:
                if p.is_symlink() and not segui_link:
                    ignorati.append((str(p.relative_to(radice)), "collegamento simbolico"))
                    continue
                st = p.stat()
            except OSError as e:
                errori.append(f"{p}: {e}")
                continue
            trovati.append((p, st))
    return trovati, ignorati, errori


def main():
    ap = argparse.ArgumentParser(description="Censimento esaustivo di una cartella documenti.")
    ap.add_argument("cartella", help="cartella radice della commessa")
    ap.add_argument("--out", help="cartella di lavoro (default: <cartella>/_inventario)")
    ap.add_argument("--includi-nascosti", action="store_true")
    ap.add_argument("--segui-link", action="store_true")
    ap.add_argument("--no-hash", action="store_true",
                    help="salta il calcolo sha256 (piu' veloce, ma niente rilevamento duplicati)")
    a = ap.parse_args()

    radice = Path(a.cartella).expanduser().resolve()
    if not radice.is_dir():
        sys.exit(f"ERRORE: '{radice}' non e' una cartella.")
    out = Path(a.out).expanduser().resolve() if a.out else radice / "_inventario"
    out.mkdir(parents=True, exist_ok=True)
    (out / "testi").mkdir(exist_ok=True)

    trovati, ignorati, errori = scansiona(radice, a.includi_nascosti, a.segui_link)

    voci, per_hash = [], {}
    for i, (p, st) in enumerate(trovati, start=1):
        ext = p.suffix.lower()
        h = "" if a.no_hash else sha256(p)
        nota = ""
        if h and h in per_hash:
            nota = f"duplicato di #{per_hash[h]}"
        elif h:
            per_hash[h] = i
        voci.append({
            "id": i,
            "percorso": str(p.relative_to(radice)),
            "cartella": str(p.parent.relative_to(radice)) or ".",
            "nome": p.name,
            "ext": ext,
            "categoria": EXT2CAT.get(ext, "altro"),
            "byte": st.st_size,
            "modificato": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            "sha256": h,
            # stato di ESTRAZIONE, riempito da estrai.py
            "estrazione": "DA_FARE",
            "metodo": "",
            "caratteri": 0,
            "pagine": 0,
            # stato di LETTURA, riempito da registro.py
            "lettura": "DA_LEGGERE",
            "sintesi": "",
            "nota": nota,
        })

    manifest = {
        "radice": str(radice),
        "creato": datetime.now().isoformat(timespec="seconds"),
        "totale_file": len(voci),
        "ignorati": [{"percorso": p, "motivo": m} for p, m in ignorati],
        "errori_accesso": errori,
        "file": voci,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    with (out / "manifest.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(voci[0].keys()) if voci else ["id"], delimiter=";")
        w.writeheader()
        w.writerows(voci)

    # Riepilogo a schermo: e' la prima cosa che l'utente deve vedere e riconoscere.
    per_cat, per_dir = {}, {}
    for v in voci:
        per_cat[v["categoria"]] = per_cat.get(v["categoria"], 0) + 1
        per_dir[v["cartella"]] = per_dir.get(v["cartella"], 0) + 1
    print(f"Radice   : {radice}")
    print(f"TROVATI  : {len(voci)} file in {len(per_dir)} cartelle")
    for c, n in sorted(per_cat.items(), key=lambda x: -x[1]):
        print(f"  {c:14s} {n:5d}")
    dupl = sum(1 for v in voci if v["nota"].startswith("duplicato"))
    if dupl:
        print(f"  (di cui {dupl} duplicati per contenuto identico)")
    if ignorati:
        print(f"IGNORATI : {len(ignorati)} (file di sistema/nascosti) - elencati nel manifest")
    if errori:
        print(f"ATTENZIONE: {len(errori)} errori di accesso:")
        for e in errori[:10]:
            print("  " + e)
    print(f"\nManifest : {out/'manifest.json'}")
    print("Prossimo passo: estrai.py")


if __name__ == "__main__":
    main()
