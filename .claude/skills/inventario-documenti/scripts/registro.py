#!/usr/bin/env python3
"""
Registro di lettura e cancello di copertura.

Serve a separare due cose che vengono sempre confuse, ed e' la confusione da cui
nasce l'analisi incompleta: che un testo sia stato ESTRATTO non significa che sia
stato LETTO. L'estrazione la fa una macchina e si verifica da sola; la lettura la
fa il modello e finora non lasciava traccia. Qui lascia traccia, file per file.

Comandi:
  stato        tabella di copertura; esce con codice 1 se il fascicolo non e' coperto
  da-leggere   elenco dei file ancora da leggere, con il percorso del testo estratto
  letto        registra la lettura di uno o piu' file (con una sintesi di una riga)
  parziale     registra una lettura parziale, motivandola
  escludi      esclude un file dall'analisi, motivandola
  report       scrive copertura.md e schede.md nella cartella _inventario
"""
import argparse, json, sys
from datetime import datetime
from pathlib import Path

# Stati di estrazione che NON impediscono di chiudere l'analisi: o non c'e'
# testo per natura del file, o e' una copia di un documento gia' letto.
ESTRAZIONE_ACCETTABILE = {"OK", "OCR_OK", "NON_TESTUALE", "DUPLICATO", "VUOTO"}
# Stati che bloccano: c'e' contenuto che non abbiamo, e fingere di no e' il bug.
ESTRAZIONE_BLOCCANTE = {"DA_FARE", "RICHIEDE_OCR", "PDF_MISTO", "MANCA_STRUMENTO",
                        "ERRORE", "PROTETTO"}
# Un file senza testo da leggere non richiede lettura.
NON_RICHIEDE_LETTURA = {"NON_TESTUALE", "DUPLICATO", "VUOTO"}


def carica(percorso):
    base = Path(percorso).expanduser().resolve()
    inv = base if (base / "manifest.json").exists() else base / "_inventario"
    mf = inv / "manifest.json"
    if not mf.exists():
        sys.exit(f"ERRORE: manifest non trovato in {inv}. Eseguire prima inventario.py.")
    return inv, mf, json.loads(mf.read_text("utf-8"))


def salva(mf, M):
    mf.write_text(json.dumps(M, ensure_ascii=False, indent=1), encoding="utf-8")


def indice(M):
    return {v["id"]: v for v in M["file"]}


def classifica(M):
    """Ripartisce i file nelle categorie che contano per il cancello."""
    da_estrarre, da_leggere, letti, parziali, esclusi, non_serve = [], [], [], [], [], []
    for v in M["file"]:
        if v["lettura"] == "ESCLUSO":
            esclusi.append(v); continue
        if v["estrazione"] in ESTRAZIONE_BLOCCANTE:
            da_estrarre.append(v); continue
        if v["estrazione"] in NON_RICHIEDE_LETTURA:
            non_serve.append(v); continue
        if v["lettura"] == "LETTO":
            letti.append(v)
        elif v["lettura"] == "PARZIALE":
            parziali.append(v)
        else:
            da_leggere.append(v)
    return da_estrarre, da_leggere, letti, parziali, esclusi, non_serve


def tabella(M):
    tot = M["totale_file"]
    da_e, da_l, letti, parz, escl, non_serve = classifica(M)
    coperti = len(letti) + len(parz) + len(non_serve) + len(escl)
    perc = 100.0 * coperti / tot if tot else 100.0
    righe = [
        f"File censiti nella cartella e sottocartelle : {tot}",
        f"  letti integralmente                       : {len(letti)}",
        f"  letti parzialmente (motivati)             : {len(parz)}",
        f"  senza testo da leggere (immagini/CAD/dupl): {len(non_serve)}",
        f"  esclusi con motivazione                   : {len(escl)}",
        f"  ESTRAZIONE NON RIUSCITA                   : {len(da_e)}",
        f"  ESTRATTI MA NON ANCORA LETTI              : {len(da_l)}",
        "",
        f"COPERTURA: {coperti}/{tot} = {perc:.1f}%",
    ]
    return "\n".join(righe), da_e, da_l, perc


def cmd_stato(a):
    inv, mf, M = carica(a.inventario)
    testo, da_e, da_l, perc = tabella(M)
    print(testo)
    if da_e:
        print("\nBLOCCANTE - estrazione non riuscita su questi file:")
        for v in da_e[:40]:
            print(f"  #{v['id']:4d} [{v['estrazione']}] {v['percorso']}"
                  + (f"  <- {v['nota']}" if v["nota"] else ""))
        if len(da_e) > 40:
            print(f"  ... e altri {len(da_e)-40}")
        print("\n  Come sbloccare: risolvere lo strumento mancante e rilanciare")
        print("  estrai.py <cartella> --solo-mancanti, oppure escludere i file")
        print("  uno per uno con: registro.py escludi <id> --motivo \"...\"")
    if da_l:
        print(f"\nBLOCCANTE - {len(da_l)} file estratti ma non ancora letti.")
        print("  Elencarli con: registro.py da-leggere <cartella>")
    if da_e or da_l:
        print("\nESITO: fascicolo NON coperto. Non chiudere l'analisi in questo stato.")
        return 1
    print("\nESITO: copertura completa. L'analisi puo' essere consegnata.")
    return 0


def cmd_da_leggere(a):
    inv, mf, M = carica(a.inventario)
    _, da_l, _, _, _, _ = classifica(M)
    if a.categoria:
        da_l = [v for v in da_l if v["categoria"] == a.categoria]
    da_l.sort(key=lambda v: (v["cartella"], v["nome"]))
    if not da_l:
        print("Nessun file in attesa di lettura.")
        return 0
    print(f"{len(da_l)} file da leggere. Prossimi {min(a.limite, len(da_l))}:\n")
    for v in da_l[:a.limite]:
        t = inv / "testi" / v.get("testo", "")
        print(f"#{v['id']:4d}  {v['percorso']}")
        print(f"       {v['caratteri']:>8d} caratteri, {v['pagine'] or '-'} pagine  ->  {t}")
    return 0


def _registra(M, id_, modo, sintesi, motivo=""):
    idx = indice(M)
    if id_ not in idx:
        return f"id #{id_} inesistente"
    v = idx[id_]
    v["lettura"] = modo
    v["sintesi"] = sintesi.strip()
    v["letto_il"] = datetime.now().isoformat(timespec="seconds")
    if motivo:
        v["nota"] = (v["nota"] + "; " if v["nota"] else "") + f"lettura parziale: {motivo}"
    return None


def cmd_letto(a):
    inv, mf, M = carica(a.inventario)
    errori, n = [], 0
    if a.da_stdin:
        # Formato: una riga JSON per file, {"id":12,"sintesi":"..."}.
        # Serve per registrare un lotto di file in una sola chiamata invece di
        # una per file, che sarebbe insostenibile su fascicoli da centinaia di atti.
        for riga in sys.stdin:
            riga = riga.strip()
            if not riga:
                continue
            try:
                d = json.loads(riga)
            except json.JSONDecodeError as e:
                errori.append(f"riga non valida ({e}): {riga[:60]}")
                continue
            if not d.get("sintesi"):
                errori.append(f"#{d.get('id')}: sintesi mancante, non registrato")
                continue
            e = _registra(M, int(d["id"]), d.get("modo", "LETTO"), d["sintesi"], d.get("motivo", ""))
            if e:
                errori.append(e)
            else:
                n += 1
    else:
        if not a.sintesi:
            sys.exit("ERRORE: serve --sintesi. Una riga che dica cosa contiene il documento;\n"
                     "e' la prova che il file e' stato davvero aperto e non solo elencato.")
        for i in a.id:
            e = _registra(M, i, "LETTO", a.sintesi)
            if e:
                errori.append(e)
            else:
                n += 1
    salva(mf, M)
    print(f"Registrati {n} file come letti.")
    for e in errori:
        print("  ATTENZIONE: " + e)
    return 1 if errori else 0


def cmd_parziale(a):
    inv, mf, M = carica(a.inventario)
    e = _registra(M, a.id, "PARZIALE", a.sintesi, a.motivo)
    if e:
        sys.exit(e)
    salva(mf, M)
    print(f"#{a.id} registrato come letto parzialmente.")
    return 0


def cmd_escludi(a):
    inv, mf, M = carica(a.inventario)
    idx = indice(M)
    for i in a.id:
        if i not in idx:
            print(f"  ATTENZIONE: id #{i} inesistente"); continue
        idx[i]["lettura"] = "ESCLUSO"
        idx[i]["sintesi"] = f"ESCLUSO: {a.motivo}"
    salva(mf, M)
    print(f"Esclusi {len(a.id)} file. La motivazione comparira' nella tabella di copertura.")
    return 0


def cmd_report(a):
    inv, mf, M = carica(a.inventario)
    testo, da_e, da_l, perc = tabella(M)
    da_e2, da_l2, letti, parz, escl, non_serve = classifica(M)

    r = ["# Tabella di copertura documentale", "",
         f"Cartella analizzata: `{M['radice']}`  ",
         f"Censimento del {M['creato']}", "", "```", testo, "```", ""]
    if parz:
        r += ["## Documenti letti parzialmente", ""]
        r += [f"- `{v['percorso']}` — {v['nota']}" for v in parz] + [""]
    if escl:
        r += ["## Documenti esclusi dall'analisi", ""]
        r += [f"- `{v['percorso']}` — {v['sintesi']}" for v in escl] + [""]
    if da_e2:
        r += ["## Documenti NON estratti (contenuto non disponibile)", ""]
        r += [f"- `{v['percorso']}` — {v['estrazione']}: {v['nota']}" for v in da_e2] + [""]
    if da_l2:
        r += ["## Documenti estratti ma non letti", ""]
        r += [f"- `{v['percorso']}`" for v in da_l2] + [""]
    if M.get("ignorati"):
        r += ["## File ignorati dal censimento", ""]
        r += [f"- `{x['percorso']}` — {x['motivo']}" for x in M["ignorati"]] + [""]
    (inv / "copertura.md").write_text("\n".join(r), encoding="utf-8")

    s = ["# Indice ragionato del fascicolo", "",
         "Una riga per documento, nell'ordine delle cartelle.", ""]
    corrente = None
    for v in sorted(M["file"], key=lambda v: (v["cartella"], v["nome"])):
        if v["cartella"] != corrente:
            corrente = v["cartella"]
            s += ["", f"## {corrente}", ""]
        if v["lettura"] in ("LETTO", "PARZIALE", "ESCLUSO"):
            etichetta = {"LETTO": "", "PARZIALE": " *(lettura parziale)*",
                         "ESCLUSO": " *(escluso)*"}[v["lettura"]]
            descrizione = v["sintesi"] or "—"
        elif v["estrazione"] in NON_RICHIEDE_LETTURA:
            # Non e' un buco: e' un file che per sua natura non ha testo, o la
            # copia di un atto gia' letto. Dirlo esplicitamente evita che l'indice
            # sembri incompleto quando invece e' completo.
            etichetta = ""
            descrizione = {"NON_TESTUALE": "*(nessun testo: allegato grafico o binario)*",
                           "DUPLICATO": f"*(copia identica — {v['nota']})*",
                           "VUOTO": "*(file privo di contenuto testuale)*"}[v["estrazione"]]
        else:
            etichetta = " *(NON LETTO)*"
            descrizione = f"*(estrazione: {v['estrazione']})*"
        s.append(f"- **#{v['id']} {v['nome']}**{etichetta} — {descrizione}")
    (inv / "schede.md").write_text("\n".join(s), encoding="utf-8")
    print(f"Scritti:\n  {inv/'copertura.md'}\n  {inv/'schede.md'}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("stato", help="tabella di copertura (esce 1 se incompleta)")
    p.add_argument("inventario"); p.set_defaults(f=cmd_stato)

    p = sub.add_parser("da-leggere", help="elenca i file ancora da leggere")
    p.add_argument("inventario"); p.add_argument("--limite", type=int, default=15)
    p.add_argument("--categoria"); p.set_defaults(f=cmd_da_leggere)

    p = sub.add_parser("letto", help="registra la lettura")
    p.add_argument("inventario"); p.add_argument("id", type=int, nargs="*")
    p.add_argument("--sintesi", help="una riga su cosa contiene il documento")
    p.add_argument("--da-stdin", action="store_true",
                   help="legge righe JSON {\"id\":N,\"sintesi\":\"...\"} per registrare un lotto")
    p.set_defaults(f=cmd_letto)

    p = sub.add_parser("parziale", help="registra una lettura parziale motivata")
    p.add_argument("inventario"); p.add_argument("id", type=int)
    p.add_argument("--sintesi", required=True); p.add_argument("--motivo", required=True)
    p.set_defaults(f=cmd_parziale)

    p = sub.add_parser("escludi", help="esclude un file motivando")
    p.add_argument("inventario"); p.add_argument("id", type=int, nargs="+")
    p.add_argument("--motivo", required=True); p.set_defaults(f=cmd_escludi)

    p = sub.add_parser("report", help="scrive copertura.md e schede.md")
    p.add_argument("inventario"); p.set_defaults(f=cmd_report)

    a = ap.parse_args()
    sys.exit(a.f(a))


if __name__ == "__main__":
    main()
