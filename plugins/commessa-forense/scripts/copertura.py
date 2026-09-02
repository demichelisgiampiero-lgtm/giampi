#!/usr/bin/env python3
"""
Cancello di copertura: fa quadrare tre numeri che di norma nessuno confronta.

  CENSITI      quanti file ci sono davvero nella cartella e nelle sottocartelle
  INDICIZZATI  quanti ne ha acquisiti il motore di ricerca (commessa-rag)
  LETTI        quanti sono stati effettivamente guardati, uno per uno

Il terzo numero e' quello che manca a tutti gli altri strumenti, e la ragione e'
strutturale: una ricerca restituisce solo cio' che la domanda pesca. Un atto che
nessuna query recupera non entra mai nell'analisi e nessuno se ne accorge - il
motore certifica che il documento e' DISPONIBILE, non che qualcuno l'abbia letto.

Il divario fra il primo e il secondo numero e' altrettanto interessante: sono i
file che il motore ha saltato in silenzio.
"""
import argparse, hashlib, json, os, re, sqlite3, sys
from datetime import datetime
from pathlib import Path

IGNORA_NOMI = {".DS_Store", "Thumbs.db", "desktop.ini", ".gitkeep"}
IGNORA_DIR = {"_inventario", ".commessa-rag", ".git", ".svn", "__pycache__",
              ".Trash", "$RECYCLE.BIN", "System Volume Information", "node_modules"}
SENZA_TESTO = {".dwg", ".dxf", ".dwf", ".ifc", ".rvt", ".skp", ".jpg", ".jpeg",
               ".png", ".tif", ".tiff", ".bmp", ".gif", ".heic", ".zip", ".rar",
               ".7z", ".p7m", ".mp4", ".mov"}


def stato_file(percorso):
    return Path(percorso).expanduser().resolve() / "_inventario" / "copertura.json"


def carica(cartella):
    f = stato_file(cartella)
    if not f.exists():
        sys.exit(f"ERRORE: nessun censimento in {f}. Eseguire prima: copertura.py censisci")
    return f, json.loads(f.read_text("utf-8"))


def salva(f, S):
    f.write_text(json.dumps(S, ensure_ascii=False, indent=1), encoding="utf-8")


# --------------------------------------------------------------- censimento
def cmd_censisci(a):
    radice = Path(a.cartella).expanduser().resolve()
    if not radice.is_dir():
        sys.exit(f"ERRORE: '{radice}' non e' una cartella.")
    suffisso = a.suffisso

    trovati, derivati, ignorati = [], {}, []
    for dirpath, dirnames, filenames in os.walk(radice):
        dirnames[:] = [d for d in sorted(dirnames)
                       if d not in IGNORA_DIR and not d.startswith(".")]
        for nome in sorted(filenames):
            p = Path(dirpath) / nome
            if nome in IGNORA_NOMI or nome.startswith("~$") or nome.startswith("."):
                ignorati.append({"percorso": str(p.relative_to(radice)),
                                 "motivo": "file di sistema o nascosto"})
                continue
            rel = str(p.relative_to(radice))
            # Un PDF prodotto dal nostro OCR non e' un altro documento: e' la
            # versione leggibile di quello originale. Contarlo a parte gonfierebbe
            # il denominatore e farebbe sembrare il fascicolo piu' grande di com'e'.
            if p.suffix.lower() == ".pdf" and p.stem.endswith(suffisso):
                originale = str((p.parent / (p.stem[: -len(suffisso)] + ".pdf")
                                 ).relative_to(radice))
                derivati[originale] = rel
                continue
            trovati.append((p, rel))

    voci = []
    for i, (p, rel) in enumerate(sorted(trovati, key=lambda x: x[1]), 1):
        ext = p.suffix.lower()
        voci.append({
            "id": i, "percorso": rel, "cartella": str(Path(rel).parent),
            "nome": p.name, "ext": ext, "byte": p.stat().st_size,
            "senza_testo": ext in SENZA_TESTO,
            "versione_ocr": derivati.get(rel, ""),
            "lettura": "SENZA_TESTO" if ext in SENZA_TESTO else "DA_LEGGERE",
            "sintesi": "", "nota": "",
        })

    S = {"radice": str(radice), "censito_il": datetime.now().isoformat(timespec="seconds"),
         "totale": len(voci), "ignorati": ignorati, "file": voci}
    f = stato_file(a.cartella)
    f.parent.mkdir(parents=True, exist_ok=True)
    salva(f, S)

    per_ext = {}
    for v in voci:
        per_ext[v["ext"] or "(nessuna)"] = per_ext.get(v["ext"] or "(nessuna)", 0) + 1
    print(f"Radice  : {radice}")
    print(f"CENSITI : {len(voci)} documenti")
    for e, n in sorted(per_ext.items(), key=lambda x: -x[1])[:10]:
        print(f"  {e:12s} {n:4d}")
    if derivati:
        print(f"  ({len(derivati)} versioni OCR riconosciute come derivate, non ricontate)")
    if ignorati:
        print(f"IGNORATI: {len(ignorati)} file di sistema")
    print(f"\nStato   : {f}")
    return 0


# --------------------------------------------------------------- indice rag
def trova_indice(radice: Path):
    """L'indice di commessa-rag puo' stare in tre posti diversi a seconda che
    il filesystem regga SQLite. Li proviamo nello stesso ordine del motore."""
    candidati = [radice / ".commessa-rag" / "index.db"]
    h = hashlib.sha1(str(radice).encode("utf-8")).hexdigest()[:16]
    candidati.append(Path.home() / ".commessa-rag" / h / "index.db")
    import tempfile
    candidati.append(Path(tempfile.gettempdir()) / ".commessa-rag" / h / "index.db")
    for c in candidati:
        if c.exists():
            return c
    return None


def leggi_indice(radice: Path):
    """Restituisce {percorso: (stato, n_pagine, n_pagine_con_testo)} oppure None."""
    db = trova_indice(radice)
    if not db:
        return None, None
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        righe = con.execute("SELECT path, status, n_pages, n_text_pages FROM documents").fetchall()
        con.close()
    except sqlite3.Error as e:
        return None, f"indice illeggibile: {e}"
    return {r[0]: (r[1], r[2], r[3]) for r in righe}, str(db)


# --------------------------------------------------------------- stato
def classifica(S, indice):
    da_leggere, letti, parziali, esclusi, senza_testo = [], [], [], [], []
    for v in S["file"]:
        if v["lettura"] == "ESCLUSO":
            esclusi.append(v)
        elif v["lettura"] == "SENZA_TESTO":
            senza_testo.append(v)
        elif v["lettura"] == "LETTO":
            letti.append(v)
        elif v["lettura"] == "PARZIALE":
            parziali.append(v)
        else:
            da_leggere.append(v)
    non_indicizzati, pagine_perse = [], []
    if indice is not None:
        # commessa-rag registra quante pagine ha un documento e quante ne hanno
        # prodotto testo, ma il suo cancello guarda solo lo stato complessivo:
        # basta una pagina leggibile perche' l'intero atto risulti verde. Il
        # divario fra i due numeri e' proprio l'elenco delle pagine che nessuna
        # ricerca potra' mai restituire - di norma le scansioni firmate.
        for percorso, (stato, n_pag, n_testo) in sorted(indice.items()):
            if stato == "indexed" and n_pag and n_testo < n_pag:
                pagine_perse.append((percorso, n_pag, n_testo))
        for v in S["file"]:
            if v["senza_testo"] or v["lettura"] == "ESCLUSO":
                continue
            candidati = [v["percorso"]] + ([v["versione_ocr"]] if v["versione_ocr"] else [])
            stato = next((indice[c][0] for c in candidati if c in indice), None)
            if stato != "indexed":
                non_indicizzati.append((v, stato or "assente dall'indice"))
    return (da_leggere, letti, parziali, esclusi, senza_testo,
            non_indicizzati, pagine_perse)


def cmd_stato(a):
    f, S = carica(a.cartella)
    radice = Path(S["radice"])
    indice, dove = leggi_indice(radice)
    da_l, letti, parz, escl, senza, non_idx, perse = classifica(S, indice)
    tot = S["totale"]
    coperti = len(letti) + len(parz) + len(escl) + len(senza)
    perc = 100.0 * coperti / tot if tot else 100.0

    print(f"CENSITI nella cartella e sottocartelle : {tot}")
    if indice is None:
        print(f"INDICIZZATI da commessa-rag            : indice non trovato"
              f"{' - ' + dove if dove else ''}")
        print("  (eseguire: rag.py init && rag.py index, poi ripetere)")
    else:
        print(f"INDICIZZATI da commessa-rag            : {len(indice)}"
              f"   [{dove}]")
    print(f"LETTI uno per uno                      : {len(letti)}")
    print(f"  letti parzialmente (motivati)         : {len(parz)}")
    print(f"  senza testo (grafici, CAD, archivi)   : {len(senza)}")
    print(f"  esclusi con motivazione               : {len(escl)}")
    print(f"  DA LEGGERE                            : {len(da_l)}")
    print(f"\nCOPERTURA DI LETTURA: {coperti}/{tot} = {perc:.1f}%")

    problemi = False
    if perse:
        problemi = True
        print(f"\nBLOCCANTE - {len(perse)} documenti indicizzati solo IN PARTE:")
        for percorso, n_pag, n_testo in perse[:25]:
            spiega = ("pagine acquisite a scanner dentro un PDF altrimenti leggibile"
                      if percorso.lower().endswith(".pdf")
                      else "parti del documento prive di testo")
            print(f"  {percorso}")
            print(f"      {n_pag - n_testo} su {n_pag} non ricercabili: {spiega}")
        if len(perse) > 25:
            print(f"  ... e altri {len(perse)-25}")
        print("  L'indice li da' per buoni: il suo stato guarda il documento, non le pagine.")
        print("  Risolvere con integrita.py (OCR sulle pagine mute) e reindicizzare.")
    if non_idx:
        problemi = True
        print(f"\nBLOCCANTE - {len(non_idx)} documenti censiti ma NON nell'indice:")
        for v, st in non_idx[:25]:
            print(f"  [{st}] {v['percorso']}")
        if len(non_idx) > 25:
            print(f"  ... e altri {len(non_idx)-25}")
        print("  Sono atti che nessuna ricerca potra' mai restituire.")
        print("  Risolvere con integrita.py (OCR) e rag.py index, oppure escludere motivando.")
    if da_l:
        problemi = True
        print(f"\nBLOCCANTE - {len(da_l)} documenti non ancora letti.")
        print("  Elencarli con: copertura.py da-leggere <cartella>")
    if problemi:
        print("\nESITO: fascicolo NON coperto. Non chiudere l'analisi in questo stato.")
        return 1
    print("\nESITO: copertura completa. L'analisi puo' essere consegnata.")
    return 0


def cmd_da_leggere(a):
    f, S = carica(a.cartella)
    indice, _ = leggi_indice(Path(S["radice"]))
    da_l = [v for v in S["file"] if v["lettura"] == "DA_LEGGERE"]
    if a.cartella_filtro:
        da_l = [v for v in da_l if v["cartella"].startswith(a.cartella_filtro)]
    if not da_l:
        print("Nessun documento in attesa di lettura.")
        return 0
    print(f"{len(da_l)} da leggere. Prossimi {min(a.limite, len(da_l))}:\n")
    for v in da_l[:a.limite]:
        rif = v["versione_ocr"] or v["percorso"]
        pag = ""
        if indice and rif in indice:
            pag = f", {indice[rif][2]}/{indice[rif][1]} pagine con testo"
        print(f"#{v['id']:4d}  {v['percorso']}{pag}")
        if v["versione_ocr"]:
            print(f"        (leggere la versione OCR: {v['versione_ocr']})")
    print("\nIl testo si ottiene da: rag.py page --folder <cartella> --file <rel> --pagina <n>")
    return 0


def _registra(S, id_, modo, sintesi, motivo=""):
    for v in S["file"]:
        if v["id"] == id_:
            v["lettura"] = modo
            v["sintesi"] = sintesi.strip()
            v["letto_il"] = datetime.now().isoformat(timespec="seconds")
            if motivo:
                v["nota"] = (v["nota"] + "; " if v["nota"] else "") + motivo
            return None
    return f"id #{id_} inesistente"


def cmd_letto(a):
    f, S = carica(a.cartella)
    errori, n = [], 0
    if a.da_stdin:
        for riga in sys.stdin:
            riga = riga.strip()
            if not riga:
                continue
            try:
                d = json.loads(riga)
            except json.JSONDecodeError as e:
                errori.append(f"riga non valida ({e}): {riga[:60]}"); continue
            if not d.get("sintesi"):
                errori.append(f"#{d.get('id')}: sintesi mancante, non registrato"); continue
            e = _registra(S, int(d["id"]), d.get("modo", "LETTO"), d["sintesi"], d.get("motivo", ""))
            if e:
                errori.append(e)
            else:
                n += 1
    else:
        if not a.sintesi:
            sys.exit("ERRORE: serve --sintesi. Una riga su cosa contiene il documento: e'\n"
                     "la prova che e' stato aperto e non soltanto elencato.")
        for i in a.id:
            e = _registra(S, i, "LETTO", a.sintesi)
            if e:
                errori.append(e)
            else:
                n += 1
    salva(f, S)
    print(f"Registrati {n} documenti come letti.")
    for e in errori:
        print("  ATTENZIONE: " + e)
    return 1 if errori else 0


def cmd_parziale(a):
    f, S = carica(a.cartella)
    e = _registra(S, a.id, "PARZIALE", a.sintesi, f"lettura parziale: {a.motivo}")
    if e:
        sys.exit(e)
    salva(f, S); print(f"#{a.id} registrato come letto parzialmente."); return 0


def cmd_escludi(a):
    f, S = carica(a.cartella)
    for i in a.id:
        e = _registra(S, i, "ESCLUSO", f"ESCLUSO: {a.motivo}")
        if e:
            print("  ATTENZIONE: " + e)
    salva(f, S)
    print(f"Esclusi {len(a.id)} documenti; la motivazione comparira' nella tabella di copertura.")
    return 0


def cmd_report(a):
    f, S = carica(a.cartella)
    radice = Path(S["radice"])
    indice, dove = leggi_indice(radice)
    da_l, letti, parz, escl, senza, non_idx, perse = classifica(S, indice)
    tot = S["totale"]
    coperti = len(letti) + len(parz) + len(escl) + len(senza)
    out = f.parent

    r = ["# Tabella di copertura documentale", "",
         f"Cartella: `{radice}`  ", f"Censimento del {S['censito_il']}", "",
         "| Voce | Numero |", "|---|---:|",
         f"| Documenti presenti nella cartella e sottocartelle | **{tot}** |",
         f"| Indicizzati e quindi ricercabili | {len(indice) if indice else 'n/d'} |",
         f"| Letti integralmente | {len(letti)} |",
         f"| Letti parzialmente (motivati) | {len(parz)} |",
         f"| Senza testo (grafici, CAD, archivi) | {len(senza)} |",
         f"| Esclusi con motivazione | {len(escl)} |",
         f"| **Copertura** | **{coperti}/{tot} = {100.0*coperti/tot if tot else 100:.1f}%** |", ""]
    if parz:
        r += ["## Letti parzialmente", ""] + [f"- `{v['percorso']}` — {v['nota']}" for v in parz] + [""]
    if escl:
        r += ["## Esclusi dall'analisi", ""] + [f"- `{v['percorso']}` — {v['sintesi']}" for v in escl] + [""]
    if perse:
        r += ["## Indicizzati solo in parte", "",
              "Documenti presenti nell'indice in cui alcune pagine non sono ricercabili.", ""]
        r += [f"- `{p}` — {n-t} pagine su {n} non ricercabili" for p, n, t in perse] + [""]
    if non_idx:
        r += ["## Non ricercabili (assenti dall'indice)", ""]
        r += [f"- `{v['percorso']}` — {st}" for v, st in non_idx] + [""]
    if da_l:
        r += ["## NON LETTI", ""] + [f"- `{v['percorso']}`" for v in da_l] + [""]
    (out / "copertura.md").write_text("\n".join(r), encoding="utf-8")

    s = ["# Indice ragionato del fascicolo", ""]
    corrente = None
    for v in sorted(S["file"], key=lambda v: (v["cartella"], v["nome"])):
        if v["cartella"] != corrente:
            corrente = v["cartella"]; s += ["", f"## {corrente}", ""]
        if v["lettura"] in ("LETTO", "PARZIALE", "ESCLUSO"):
            etich = {"LETTO": "", "PARZIALE": " *(lettura parziale)*",
                     "ESCLUSO": " *(escluso)*"}[v["lettura"]]
            desc = v["sintesi"] or "—"
        elif v["lettura"] == "SENZA_TESTO":
            etich, desc = "", "*(allegato grafico o binario: nessun testo)*"
        else:
            etich, desc = " *(NON LETTO)*", "—"
        s.append(f"- **#{v['id']} {v['nome']}**{etich} — {desc}")
    (out / "schede.md").write_text("\n".join(s), encoding="utf-8")
    print(f"Scritti:\n  {out/'copertura.md'}\n  {out/'schede.md'}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("censisci"); p.add_argument("cartella")
    p.add_argument("--suffisso", default="_OCR"); p.set_defaults(f=cmd_censisci)
    p = sub.add_parser("stato"); p.add_argument("cartella"); p.set_defaults(f=cmd_stato)
    p = sub.add_parser("da-leggere"); p.add_argument("cartella")
    p.add_argument("--limite", type=int, default=15)
    p.add_argument("--cartella-filtro", default=""); p.set_defaults(f=cmd_da_leggere)
    p = sub.add_parser("letto"); p.add_argument("cartella"); p.add_argument("id", type=int, nargs="*")
    p.add_argument("--sintesi"); p.add_argument("--da-stdin", action="store_true")
    p.set_defaults(f=cmd_letto)
    p = sub.add_parser("parziale"); p.add_argument("cartella"); p.add_argument("id", type=int)
    p.add_argument("--sintesi", required=True); p.add_argument("--motivo", required=True)
    p.set_defaults(f=cmd_parziale)
    p = sub.add_parser("escludi"); p.add_argument("cartella"); p.add_argument("id", type=int, nargs="+")
    p.add_argument("--motivo", required=True); p.set_defaults(f=cmd_escludi)
    p = sub.add_parser("report"); p.add_argument("cartella"); p.set_defaults(f=cmd_report)
    a = ap.parse_args()
    sys.exit(a.f(a))


if __name__ == "__main__":
    main()
