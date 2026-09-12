#!/usr/bin/env python3
"""Verifica le letture parziali motivate con «riproduce un atto gia' letto».

Movente (commessa Caltagirone, 10 settembre 2026). Il D.D.G. n. 3/2024 fu
registrato come lettura parziale con la motivazione «riproduce il parere 627,
gia' letto»: ventuno pagine restarono fuori. Dentro c'erano i pareri CTS
350/2023 e 526/2023, che non esistono in nessun altro punto del fascicolo, e da
li' e' uscito il riscontro sulla CA 4 lett. i). La motivazione era falsa e
nessuno poteva accorgersene, perche' `--motivo` e' prosa e la prosa non si
controlla.

Questo modulo la controlla. Prende le pagine che una lettura parziale NON ha
letto, ne estrae i 5-grammi di parole e cerca ognuno nel testo dell'atto che si
dichiara riprodotto. Una pagina che si ritrova la' dentro e' davvero una copia;
una che non si ritrova e' una pagina che nessuno ha letto.

Non giudica il merito e non legge il contenuto: dice soltanto se cio' che e'
stato affermato regge. Il testo lo prende dall'indice di commessa-rag, che e' la
stessa fonte da cui legge il resto della filiera.

Uso da riga di comando:

    parziali_confronto.py <cartella> --atto "<percorso rel>" \\
        --pagine "1-8,34-39" --riproduce "<percorso rel>"

Esce 0 se la riproduzione regge, 1 se restano pagine scoperte, 2 sugli errori
d'uso. Puo' essere usato anche come modulo: `confronta()` restituisce l'esito,
`spiega()` lo mette in parole.
"""

import argparse
import hashlib
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

# --------------------------------------------------------------------------- #
# Parametri                                                                    #
# --------------------------------------------------------------------------- #

N_GRAMMA = 5
# Quota dei 5-grammi della pagina da ritrovare nel riferimento perche' la pagina
# sia considerata davvero riprodotta. Non e' 1.0 perche' due tirature dello
# stesso testo differiscono per intestazioni, numeri di pagina e sillabazione.
SOGLIA_COPERTURA = 0.90
# Sotto questa quantita' di 5-grammi la pagina non ha abbastanza testo perche'
# il confronto significhi qualcosa: non si promuove e non si boccia, si dichiara
# indecidibile. Una tavola grafica sta qui, e infatti di una tavola nessuno puo'
# affermare che «riproduce» un altro atto.
MIN_GRAMMI = 8

ESITO_RIPRODOTTA = "RIPRODOTTA"
ESITO_SCOPERTA = "SCOPERTA"
ESITO_INDECIDIBILE = "INDECIDIBILE"

NON_PAGINATO = ("non-paginato", "non paginato", "n.d.", "nd")


# --------------------------------------------------------------------------- #
# Testo                                                                        #
# --------------------------------------------------------------------------- #

def _parole(testo: str):
    """Le parole del testo, normalizzate come le normalizza l'indice.

    Minuscole e senza diacritici, perche' `commessa-rag` indicizza con
    `remove_diacritics`: confrontare in modo piu' severo del motore che ha
    prodotto il testo darebbe scoperte finte.
    """
    if not testo:
        return []
    t = unicodedata.normalize("NFKD", testo)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.findall(r"[0-9a-z]+", t.casefold())


def _grammi(parole, n=N_GRAMMA):
    """I 5-grammi di parole, come insieme.

    Cinque parole perche' quattro le fa combaciare il lessico burocratico (in
    un fascicolo di appalto «ai sensi dell'articolo» ricorre ovunque) e sei
    rendono il confronto fragile a una virgola di differenza.
    """
    if len(parole) < n:
        return set()
    return {tuple(parole[i:i + n]) for i in range(len(parole) - n + 1)}


# --------------------------------------------------------------------------- #
# Pagine dichiarate                                                            #
# --------------------------------------------------------------------------- #

def pagine_dichiarate(spec: str):
    """L'insieme dei numeri di pagina che «1-5,32,40» dichiara.

    `None` se la dicitura e' «non-paginato», che non e' un errore: e' un
    documento che pagine non ne ha (foglio di calcolo, e-mail).
    Solleva ValueError se la dicitura non si legge.

    copertura.conta_pagine() risponde a «quante»; qui serve «quali», che e' la
    domanda del confronto.
    """
    if not spec or not spec.strip():
        return set()
    if spec.strip().casefold() in NON_PAGINATO:
        return None
    fuori = set()
    for pezzo in spec.replace(";", ",").split(","):
        pezzo = pezzo.strip()
        if not pezzo:
            continue
        m = re.fullmatch(r"(\d{1,6})\s*[-–]\s*(\d{1,6})", pezzo)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if b < a:
                raise ValueError(f"intervallo rovesciato: {pezzo}")
            fuori.update(range(a, b + 1))
            continue
        if pezzo.isdigit():
            fuori.add(int(pezzo))
            continue
        raise ValueError(f"non si legge: {pezzo}")
    return fuori


# --------------------------------------------------------------------------- #
# Indice                                                                       #
# --------------------------------------------------------------------------- #

def trova_indice(radice: Path):
    """Lo stesso ordine di ricerca di copertura.trova_indice().

    Ripetuto qui invece di importarlo per non creare una dipendenza circolare:
    copertura importa questo modulo.
    """
    candidati = [radice / ".commessa-rag" / "index.db"]
    h = hashlib.sha1(str(radice).encode("utf-8")).hexdigest()[:16]
    candidati.append(Path.home() / ".commessa-rag" / h / "index.db")
    import tempfile
    candidati.append(Path(tempfile.gettempdir()) / ".commessa-rag" / h / "index.db")
    for c in candidati:
        if c.exists():
            return c
    return None


def _pagine_di(con, percorso: str):
    """{numero_pagina: testo} per un percorso, dall'indice. {} se assente."""
    fuori = {}
    for pag, testo in con.execute(
            "SELECT p.page, p.text FROM pages p JOIN documents d ON d.id = p.doc_id "
            "WHERE d.path = ?", (percorso,)):
        fuori[int(pag)] = testo or ""
    return fuori


# --------------------------------------------------------------------------- #
# Il confronto                                                                 #
# --------------------------------------------------------------------------- #

def confronta(radice, percorso, spec_pagine, riferimenti, soglia=SOGLIA_COPERTURA):
    """Le pagine non lette di `percorso` si ritrovano in `riferimenti`?

    `riferimenti` e' un percorso o una lista di percorsi: gli atti che la
    motivazione dichiara gia' letti e di cui questo sarebbe copia.

    Restituisce un dizionario:
      regge        bool - vero solo se nessuna pagina resta scoperta o indecidibile
      motivo       str  - perche' non regge, quando non regge
      pagine       list - [(numero, esito, quota)] per ogni pagina non dichiarata
      scoperte     list - i numeri delle pagine che non si ritrovano
      indecidibili list - i numeri delle pagine senza testo sufficiente
    """
    radice = Path(radice)
    if isinstance(riferimenti, (str, Path)):
        riferimenti = [str(riferimenti)]
    riferimenti = [str(r) for r in riferimenti if str(r).strip()]

    vuoto = {"regge": False, "motivo": "", "pagine": [], "scoperte": [], "indecidibili": []}

    if not riferimenti:
        vuoto["motivo"] = "nessun atto di riferimento indicato"
        return vuoto

    db = trova_indice(radice)
    if not db:
        vuoto["motivo"] = ("indice di commessa-rag non trovato: il confronto non e' "
                           "eseguibile. Indicizzare la cartella e ripetere.")
        return vuoto

    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    except sqlite3.Error as err:
        vuoto["motivo"] = f"indice non leggibile: {err}"
        return vuoto

    try:
        mie = _pagine_di(con, percorso)
        if not mie:
            vuoto["motivo"] = (f"«{percorso}» non e' nell'indice, o non ne ha testo: "
                               f"senza testo non si puo' affermare che riproduca nulla.")
            return vuoto

        grammi_rif = set()
        trovati = []
        for r in riferimenti:
            pagine_r = _pagine_di(con, r)
            if not pagine_r:
                continue
            trovati.append(r)
            for testo in pagine_r.values():
                grammi_rif |= _grammi(_parole(testo))
        if not trovati:
            vuoto["motivo"] = ("nessuno degli atti di riferimento e' nell'indice: "
                               + ", ".join(riferimenti))
            return vuoto
        if not grammi_rif:
            vuoto["motivo"] = ("gli atti di riferimento non hanno testo in indice: "
                               "il confronto non direbbe nulla.")
            return vuoto
    finally:
        con.close()

    try:
        lette = pagine_dichiarate(spec_pagine)
    except ValueError as err:
        vuoto["motivo"] = f"--pagine non si legge ({err})"
        return vuoto

    if lette is None:
        # Documento non paginato: si confronta il testo intero, che e' l'unica
        # unita' che ha.
        da_verificare = sorted(mie)
        lette = set()
    else:
        da_verificare = sorted(p for p in mie if p not in lette)

    if not da_verificare:
        return {"regge": True, "motivo": "", "pagine": [], "scoperte": [], "indecidibili": []}

    pagine, scoperte, indecidibili = [], [], []
    for p in da_verificare:
        g = _grammi(_parole(mie[p]))
        if len(g) < MIN_GRAMMI:
            pagine.append((p, ESITO_INDECIDIBILE, 0.0))
            indecidibili.append(p)
            continue
        quota = len(g & grammi_rif) / len(g)
        if quota >= soglia:
            pagine.append((p, ESITO_RIPRODOTTA, quota))
        else:
            pagine.append((p, ESITO_SCOPERTA, quota))
            scoperte.append(p)

    regge = not scoperte and not indecidibili
    return {"regge": regge, "motivo": "", "pagine": pagine,
            "scoperte": scoperte, "indecidibili": indecidibili}


def _intervalli(numeri):
    """[1,2,3,7,9,10] -> «1-3, 7, 9-10». Per stampare elenchi lunghi."""
    numeri = sorted(set(numeri))
    if not numeri:
        return ""
    pezzi, a = [], numeri[0]
    b = a
    for n in numeri[1:]:
        if n == b + 1:
            b = n
            continue
        pezzi.append(str(a) if a == b else f"{a}-{b}")
        a = b = n
    pezzi.append(str(a) if a == b else f"{a}-{b}")
    return ", ".join(pezzi)


def spiega(esito, percorso="", riferimenti=""):
    """L'esito in parole, da mostrare a chi ha registrato la lettura."""
    if esito["regge"]:
        return ""
    righe = []
    if esito["motivo"]:
        righe.append(f"CONFRONTO NON ESEGUIBILE: {esito['motivo']}")
        righe.append("  Finche' non e' eseguibile, la motivazione «riproduce un atto")
        righe.append("  gia' letto» non e' verificata e non si registra.")
        return "\n".join(righe)

    righe.append("RIFIUTATO - la riproduzione dichiarata non regge al confronto.")
    if percorso:
        righe.append(f"  Atto        : {percorso}")
    if riferimenti:
        righe.append(f"  Riferimento : {riferimenti}")
    if esito["scoperte"]:
        righe.append(f"  Pagine NON riprodotte: {_intervalli(esito['scoperte'])}")
        peggiori = sorted((q, p) for p, e, q in esito["pagine"] if e == ESITO_SCOPERTA)[:5]
        for q, p in peggiori:
            righe.append(f"    p. {p}: solo il {100*q:.0f}% del testo si ritrova nel riferimento")
    if esito["indecidibili"]:
        righe.append(f"  Pagine senza testo bastante: {_intervalli(esito['indecidibili'])}")
        righe.append("    di queste non si puo' affermare che riproducano alcunche'.")
    righe.append("")
    righe.append("  Quelle pagine vanno LETTE, oppure la lettura va motivata altrimenti")
    righe.append("  (--causa MIRATA, che non afferma nulla sul loro contenuto).")
    righe.append("  Movente: Caltagirone, D.D.G. 3/2024. Ventuno pagine date per copia")
    righe.append("  del parere 627 contenevano i pareri 350/2023 e 526/2023, unici nel")
    righe.append("  fascicolo, e da li' e' uscito il riscontro sulla CA 4 lett. i).")
    return "\n".join(righe)


# --------------------------------------------------------------------------- #
# Rassegna di un fascicolo gia' lavorato                                       #
# --------------------------------------------------------------------------- #

# La stessa lista vive anche in copertura.py. La duplicazione e' voluta: i due
# file devono funzionare da soli. copertura deve riconoscere l'affermazione
# anche se questo modulo non c'e' (un verificatore mancante non e' un
# lasciapassare), e questo modulo deve poter passare in rassegna un fascicolo
# senza tirarsi dietro l'intero copertura.
RIPRODUZIONE_AFFERMATA = (
    # Il contenuto sta in un ALTRO atto.
    "riproduc", "gia letto", "gia letta", "gia lette", "gia letti",
    "copia di", "copia del", "copia della", "e copia", "identic",
    "duplicat", "stesso testo", "medesimo testo", "stesso contenuto",
    "medesimo contenuto", "gia presente", "gia acquisit", "gia visto",
    "riportato in", "riportata in", "si ritrova in", "coincide con",
    # Il contenuto si ripete DENTRO lo stesso atto, o ricalca una struttura
    # gia' vista altrove. E' la stessa affermazione - «il resto e' gia' noto» -
    # e va provata allo stesso modo.
    #
    # Misurato l'11 settembre 2026 sul registro vero di Caltagirone: delle 175
    # letture parziali, le spie del primo gruppo ne intercettavano ZERO e queste
    # ne intercettano QUARANTA, che lasciano fuori 2.803 pagine. Fra queste,
    # cinque relazioni di calcolo da 231 a 584 pagine (#687-#692), tutte con la
    # sola copertina letta e tutte motivate con «struttura standard gia'
    # riscontrata su POD1». Il primo elenco era tarato sul caso del D.D.G. 3 e
    # cieco all'idioma che i lettori usano davvero.
    "ripetitiv", "ripetut", "ripetizion",
    "struttura standard", "struttura analoga", "stessa struttura",
    "medesima struttura", "gia riscontrat", "del tutto simil", "uguale a",
)


def afferma_riproduzione(motivo: str) -> bool:
    """Il motivo sostiene che il contenuto sta gia' altrove?"""
    if not motivo:
        return False
    t = unicodedata.normalize("NFKD", motivo)
    t = "".join(c for c in t if not unicodedata.combining(c)).casefold()
    t = re.sub(r"[\u0027\u2019\u02bc`]+", "", t)
    t = re.sub(r"\s+", " ", t)
    return any(spia in t for spia in RIPRODUZIONE_AFFERMATA)


def rassegna(cartella):
    """Le letture parziali che AFFERMANO una riproduzione senza averla provata.

    Serve sui fascicoli lavorati prima che il confronto esistesse. Non puo'
    verificarle da sola - la motivazione e' prosa e non dice in forma
    utilizzabile QUALE atto sarebbe riprodotto - ma sa dire quali sono, ed e'
    esattamente l'elenco che su Caltagirone nessuno aveva.
    """
    import json
    reg = Path(cartella).expanduser().resolve() / "_inventario" / "copertura.json"
    if not reg.exists():
        return None, f"registro non trovato: {reg}"
    try:
        S = json.loads(reg.read_text(encoding="utf-8"))
    except (OSError, ValueError) as err:
        return None, f"registro non leggibile: {err}"
    byid = {v.get("id"): v for v in S.get("file", [])}
    fuori, disallineate = [], []
    for v in S.get("file", []):
        if v.get("lettura") != "PARZIALE":
            continue
        nota = v.get("nota") or ""
        if not afferma_riproduzione(nota):
            continue
        if v.get("riproduce"):
            continue          # dichiarata e verificata al momento della registrazione
        causa = (v.get("causa_parziale") or "").upper()
        if causa:
            # Qualcuno ha guardato questa lettura e ne ha dichiarato la causa: non e'
            # piu' un'affermazione lasciata li'. Resta pero' una contraddizione da
            # sanare - la causa dice MIRATA, la motivazione scritta dice ancora che il
            # contenuto sta altrove - e chi legge la scheda vede solo la seconda.
            # Misurato il 12 settembre 2026 su Caltagirone, sulle cinque relazioni POD:
            # il confronto le ha bocciate, sono state dichiarate MIRATA, e la nota e'
            # rimasta quella di prima.
            v = dict(v)
            v["_causa"] = causa
            disallineate.append(v)
            continue
        v = dict(v)
        v["_rimandi"] = _rimandi_della_nota(nota, byid)
        fuori.append(v)
    return fuori, "", disallineate


def _rimandi_della_nota(nota, byid):
    """I rimandi «id NNN» scritti dentro una motivazione, risolti sul registro.

    Un id scritto in prosa e' un riferimento PENDENTE: nulla lo tiene valido, e
    un ricensimento rinumera i documenti senza toccare le note. Misurato l'11
    settembre 2026 su Caltagirone: cinque relazioni di calcolo elettrico
    (POD2..POD6) rimandavano a «POD1 (id 678)», ma l'id 678 dopo il ricensimento
    era la Relazione Tecnico Agronomica. Gli id erano slittati di +9 - POD1 era
    diventato il 687 - e tutti e cinque i rimandi erano silenziosamente sbagliati.

    E' anche la ragione per cui `--riproduce` prende un PERCORSO e non un id:
    un percorso sopravvive a un ricensimento, un id no.
    """
    fuori = []
    for m in re.finditer(r"\bid\.?\s*(\d{1,5})\b", nota, re.I):
        n = int(m.group(1))
        d = byid.get(n)
        fuori.append({
            "id": n,
            "nome": d.get("nome") if d else None,
            "lettura": d.get("lettura") if d else None,
            "pagine_lette": (d.get("pagine_lette") or "") if d else "",
        })
    return fuori


# --------------------------------------------------------------------------- #
# Riga di comando                                                              #
# --------------------------------------------------------------------------- #

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Verifica che le pagine non lette di un atto si ritrovino "
                    "davvero nell'atto che si dichiara riprodotto.")
    ap.add_argument("cartella")
    ap.add_argument("--rassegna", action="store_true",
                    help="passa in rassegna il fascicolo: elenca le letture parziali che "
                         "affermano una riproduzione senza averla provata")
    ap.add_argument("--atto", help="percorso relativo dell'atto letto in parte")
    ap.add_argument("--pagine", help='pagine lette: "1-5,32,40"')
    ap.add_argument("--riproduce", action="append",
                    help="percorso relativo dell'atto di cui sarebbe copia "
                         "(ripetibile per piu' atti)")
    ap.add_argument("--soglia", type=float, default=SOGLIA_COPERTURA)
    a = ap.parse_args(argv)

    if a.rassegna:
        sospette, err, disallineate = rassegna(a.cartella)
        if err:
            print(f"ERRORE: {err}", file=sys.stderr)
            return 2
        def _stampa_disallineate():
            if not disallineate:
                return
            print()
            print(f"{len(disallineate)} letture con causa dichiarata ma MOTIVAZIONE non riallineata:")
            for v in disallineate:
                print(f"  #{v.get('id')} [{v['_causa']}] {v.get('percorso')}")
                print(f"      motivo ancora: {(v.get('nota') or '').strip()[:110]}")
            print()
            print("  La causa dichiarata smentisce la motivazione scritta. Non sono")
            print("  affermazioni lasciate senza controllo - qualcuno le ha guardate - ma")
            print("  chi legge la scheda vede solo la motivazione. Vanno riscritte con")
            print("  'copertura.py parziale', che aggiorna anche sintesi e motivo.")

        if not sospette:
            print("OK - nessuna lettura parziale afferma una riproduzione non provata.")
            _stampa_disallineate()
            return 0
        print(f"{len(sospette)} letture parziali AFFERMANO una riproduzione mai verificata:")
        print()
        catene = 0
        for v in sospette:
            print(f"  #{v.get('id')} {v.get('percorso')}")
            print(f"      pagine lette: {v.get('pagine_lette') or '(non dichiarate)'}")
            print(f"      motivo      : {(v.get('nota') or '').strip()}")
            for r in v.get("_rimandi") or []:
                if r["nome"] is None:
                    print(f"      !! rimanda a id {r['id']}, che nel registro NON ESISTE")
                    continue
                print(f"      rimanda a id {r['id']} -> {r['nome']}  [{r['lettura']}]")
                if r["lettura"] == "PARZIALE":
                    catene += 1
                    print(f"         !! CATENA: anche quello e' letto in parte "
                          f"(pagine {r['pagine_lette'] or 'non dichiarate'}). "
                          f"L'affermazione poggia su un atto a sua volta non letto.")
        if catene:
            print()
            print(f"  {catene} rimandi puntano a un atto a sua volta letto solo in parte.")
            print("  Un id scritto in prosa e' un riferimento pendente: un ricensimento")
            print("  rinumera i documenti e le note restano indietro. Verificare a mano")
            print("  che l'id citato sia ancora quello inteso.")
        print()
        print("  Ciascuna sostiene che il resto dell'atto sta in un altro documento,")
        print("  e nessuno l'ha controllato. Per verificarne una:")
        print('    parziali_confronto.py <cartella> --atto "<percorso>" \\')
        print('        --pagine "<quelle lette>" --riproduce "<atto che sarebbe copiato>"')
        print()
        print("  Movente: Caltagirone, D.D.G. 3/2024. Una di queste teneva fuori ventuno")
        print("  pagine con dentro due pareri CTS unici nel fascicolo.")
        _stampa_disallineate()
        return 1

    mancanti = [n for n, v in (("--atto", a.atto), ("--pagine", a.pagine),
                               ("--riproduce", a.riproduce)) if not v]
    if mancanti:
        ap.error("senza --rassegna servono: " + ", ".join(mancanti))

    radice = Path(a.cartella).expanduser().resolve()
    esito = confronta(radice, a.atto, a.pagine, a.riproduce, a.soglia)
    if esito["regge"]:
        n = len(esito["pagine"])
        print(f"OK - le {n} pagine non lette si ritrovano nel riferimento.")
        return 0
    print(spiega(esito, a.atto, ", ".join(a.riproduce)))
    return 2 if esito["motivo"] else 1


if __name__ == "__main__":
    sys.exit(main())
