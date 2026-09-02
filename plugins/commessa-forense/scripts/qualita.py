#!/usr/bin/env python3
"""
Controllo di qualita' sulla lettura.

I tre cancelli dimostrano che ogni documento e' stato APERTO e che ogni
virgolettato ESISTE. Nessuno dimostra che il documento sia stato CAPITO: una
scheda superficiale, o con una data sbagliata, passa il cancello di copertura
come una scritta bene. Questo e' il divario che lo script chiude.

Il principio e' lo stesso della verifica dei virgolettati, applicato pero' a
cio' che il lettore ha scritto di suo: una scheda contiene FATTI DURI - date,
protocolli, importi, articoli, quantita' - e quei fatti devono trovarsi
davvero nel documento. Un importo che nella scheda c'e' e nel documento no
non e' una sfumatura interpretativa: e' un numero inventato, e in una riserva
un numero inventato e' il rilievo che fa cadere l'affermazione.

Tre livelli, dal piu' economico al piu' costoso:

  ancoraggio  su TUTTE le schede, deterministico: ogni fatto duro dichiarato
              deve comparire nel testo del documento
  campione    sceglie quali documenti meritano una seconda lettura, dando la
              precedenza a quelli dove sbagliare costa di piu'
  confronta   mette a fronte prima e seconda lettura e segnala le divergenze

Il testo dei documenti viene letto dall'indice di commessa-rag: e' la stessa
fonte su cui ha lavorato il lettore, quindi il confronto e' leale.
"""
import argparse, hashlib, json, random, re, sqlite3, sys, unicodedata
from datetime import datetime
from pathlib import Path

MESI = {"gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6,
        "luglio": 7, "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11,
        "dicembre": 12}
MESI_INV = {v: k for k, v in MESI.items()}

# Una scheda che non contiene alcun fatto duro non e' necessariamente sbagliata,
# ma non e' verificabile da nessuno: va guardata da un umano.
MIN_CARATTERI_SCHEDA = 40
FRASI_GENERICHE = ("corrispondenza varia", "documenti vari", "atti vari", "vedi allegato",
                   "documentazione di progetto", "vari documenti", "non rilevante",
                   "documento tecnico", "allegato generico")


def piatto(t: str) -> str:
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


# --------------------------------------------------------------- numeri
def valori(testo: str):
    """Tutti i numeri del testo, come valori.

    Il confronto avviene sui VALORI e non sulle stringhe, perche' lo stesso
    importo si scrive in modi diversi a seconda di dove lo si legge: un Excel
    restituisce 121500.0, un PDF stampa 121.500,00, una scheda scrive
    121.500. Confrontare le stringhe produrrebbe falsi allarmi a raffica, e un
    controllo che grida al lupo troppo spesso smette di essere usato.
    """
    fuori = set()
    for m in re.finditer(r"\d[\d.,]*\d|\d", testo):
        grezzo = m.group()
        for v in interpreta(grezzo):
            fuori.add(round(v, 2))
    return fuori


def interpreta(grezzo: str):
    """Le letture plausibili di un numero scritto. '1.250' vale 1250 all'italiana
    e 1.25 all'inglese: si tengono buone entrambe, perche' scartare quella
    giusta produrrebbe un falso allarme su un dato corretto."""
    fuori = []
    g = grezzo.strip(".,")
    if not g:
        return fuori
    # forma italiana piena: 121.500,00
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+,\d+", g):
        fuori.append(float(g.replace(".", "").replace(",", ".")))
    # migliaia all'italiana senza decimali: 121.500
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", g):
        fuori.append(float(g.replace(".", "")))
    # decimale con virgola: 8,45
    elif re.fullmatch(r"\d+,\d+", g):
        fuori.append(float(g.replace(",", ".")))
    # forma inglese: 121,500.00
    elif re.fullmatch(r"\d{1,3}(?:,\d{3})+\.\d+", g):
        fuori.append(float(g.replace(",", "")))
    elif re.fullmatch(r"\d{1,3}(?:,\d{3})+", g):
        fuori.append(float(g.replace(",", "")))
    elif re.fullmatch(r"\d+\.\d+", g):
        fuori.append(float(g))                       # 8.45
        if re.fullmatch(r"\d{1,3}\.\d{3}", g):       # ...oppure 1.250 all'italiana
            fuori.append(float(g.replace(".", "")))
    elif re.fullmatch(r"\d+", g):
        fuori.append(float(g))
    return fuori


# --------------------------------------------------------------- estrazione fatti
def fatti(testo: str):
    """I fatti duri dichiarati in una scheda, ciascuno con il suo tipo."""
    trovati = []
    p = piatto(testo)

    # date in cifre
    for m in re.finditer(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b", testo):
        g, me, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a < 100:
            a += 2000
        if 1 <= g <= 31 and 1 <= me <= 12:
            trovati.append(("data", (g, me, a), m.group()))
    # date per esteso
    for m in re.finditer(r"\b(\d{1,2})\s+(" + "|".join(MESI) + r")\s+(\d{4})\b", p):
        trovati.append(("data", (int(m.group(1)), MESI[m.group(2)], int(m.group(3))), m.group()))

    # importi: solo con decimali o preceduti da 'euro', per non raccogliere
    # ogni numero di pagina che passa
    for m in re.finditer(r"(?:euro|eur|€)\s*([\d.,]+)|([\d.]{1,3}(?:\.\d{3})*,\d{2})\b", testo, re.I):
        g = (m.group(1) or m.group(2) or "").strip(".,")
        for v in interpreta(g):
            if v >= 1:
                trovati.append(("importo", round(v, 2), m.group().strip()))

    # protocolli e numeri d'atto
    for m in re.finditer(r"\bprot(?:ocollo)?\.?\s*n?\.?\s*([A-Za-z0-9][\w./-]*)", p):
        trovati.append(("protocollo", re.sub(r"\D", "", m.group(1)) or m.group(1), m.group().strip()))
    for m in re.finditer(r"\b(riserva|ods|ordine di servizio|sal|perizia|variante|rep|repertorio|"
                         r"partita|verbale)\s*(?:n\.?|numero)?\s*(\d{1,6})\b", p):
        trovati.append((f"atto:{m.group(1)}", int(m.group(2)), m.group().strip()))

    # riferimenti normativi
    for m in re.finditer(r"\bart\.?\s*(\d{1,3})", p):
        trovati.append(("articolo", int(m.group(1)), m.group().strip()))
    for m in re.finditer(r"\bd\.?\s*lgs\.?\s*(?:n\.?)?\s*(\d{1,3})\s*/\s*(\d{4})", p):
        trovati.append(("norma", (int(m.group(1)), int(m.group(2))), m.group().strip()))

    # quantita' con unita' di misura
    for m in re.finditer(r"\b(mc|mq|ml|kmq|kg|ton|cad)\s*([\d.,]+)|([\d.,]+)\s*(mc|mq|ml|kg|ton)\b", p):
        g = (m.group(2) or m.group(3) or "").strip(".,")
        for v in interpreta(g):
            trovati.append(("quantita", round(v, 2), m.group().strip()))

    # deduplica mantenendo l'ordine
    visti, fuori = set(), []
    for tipo, valore, testuale in trovati:
        chiave = (tipo, str(valore))
        if chiave not in visti:
            visti.add(chiave)
            fuori.append({"tipo": tipo, "valore": valore, "come_scritto": testuale})
    return fuori


def ancorato(fatto, testo_doc, numeri_doc):
    """Il fatto compare nel documento? Il confronto e' per valore, non per forma."""
    tipo, v = fatto["tipo"], fatto["valore"]
    p = piatto(testo_doc)
    if tipo == "data":
        g, me, a = v
        forme = [f"{g:02d}/{me:02d}/{a}", f"{g}/{me}/{a}", f"{g:02d}-{me:02d}-{a}",
                 f"{g}.{me}.{a}", f"{a}-{me:02d}-{g:02d}",
                 f"{g} {MESI_INV[me]} {a}", f"{g:02d}/{me:02d}/{str(a)[2:]}"]
        return any(f in p for f in forme)
    if tipo == "norma":
        n, anno = v
        return bool(re.search(rf"\b{n}\s*/\s*{anno}\b", p)) or (f"{n}/{anno}" in p)
    if tipo == "articolo":
        return bool(re.search(rf"\bart\.?\s*{v}\b", p)) or bool(re.search(rf"\b{v}\b", p))
    if tipo == "protocollo":
        return str(v) in re.sub(r"\D", " ", p).split() or str(v) in p
    if tipo.startswith("atto:"):
        return bool(re.search(rf"\b{v}\b", p))
    return float(v) in numeri_doc          # importi e quantita'



# --------------------------------------------------------------- testo grezzo
def testo_grezzo(percorso: Path) -> str:
    """Il testo del file letto direttamente, senza passare dall'indice.

    Serve a distinguere due situazioni che il solo confronto con l'indice
    confonderebbe: un dato che il lettore si e' inventato, e un dato che nel
    documento c'e' ma che la catena di indicizzazione non ha raccolto. Il
    secondo caso e' frequente e insidioso - l'estrattore .docx di commessa-rag
    legge paragrafi e tabelle ma non intestazioni e pie' di pagina, che e'
    dove negli atti italiani vivono numero di protocollo e data - e va
    riportato come un guasto della catena, non come un errore di chi ha letto.
    """
    ext = percorso.suffix.lower()
    try:
        if ext in (".docx", ".xlsx", ".xlsm", ".pptx"):
            import zipfile
            from xml.etree import ElementTree as ET
            with zipfile.ZipFile(percorso) as z:
                nomi = z.namelist()
                pezzi = []
                for n in nomi:
                    if not n.endswith(".xml") or n.startswith("docProps"):
                        continue
                    if not (n.startswith("word/") or n.startswith("xl/") or n.startswith("ppt/")):
                        continue
                    try:
                        root = ET.fromstring(z.read(n))
                    except ET.ParseError:
                        continue
                    for el in root.iter():
                        if el.tag.rsplit("}", 1)[-1] in ("t", "v") and el.text:
                            pezzi.append(el.text)
                return " ".join(pezzi)
        if ext == ".pdf":
            pagine, _ = pagine_pdf(percorso)
            return "\f".join(pagine or [])
        return percorso.read_bytes().decode("utf-8", "replace")
    except (OSError, ValueError, KeyError):
        return ""


def pagine_pdf(percorso: Path):
    """Riusa l'estrattore per pagina della fase di integrita'."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from integrita import leggi_pagine
        pagine, _, _ = leggi_pagine(percorso)
        return pagine, ""
    except (ImportError, OSError, ValueError) as e:
        return None, str(e)


# --------------------------------------------------------------- accesso ai dati
def carica_copertura(cartella):
    f = Path(cartella).expanduser().resolve() / "_inventario" / "copertura.json"
    if not f.exists():
        sys.exit(f"ERRORE: nessun censimento in {f}. Eseguire prima: copertura.py censisci")
    return f, json.loads(f.read_text("utf-8"))


def trova_indice(radice: Path):
    import tempfile
    h = hashlib.sha1(str(radice).encode("utf-8")).hexdigest()[:16]
    for c in (radice / ".commessa-rag" / "index.db",
              Path.home() / ".commessa-rag" / h / "index.db",
              Path(tempfile.gettempdir()) / ".commessa-rag" / h / "index.db"):
        if c.exists():
            return c
    return None


def testi_documenti(radice: Path):
    """{percorso: testo completo} dall'indice di commessa-rag."""
    db = trova_indice(radice)
    if not db:
        return None
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    fuori = {}
    for path, testo in con.execute(
            "SELECT d.path, group_concat(p.text, ' ') FROM documents d "
            "JOIN pages p ON p.doc_id = d.id GROUP BY d.path"):
        fuori[path] = testo or ""
    con.close()
    return fuori


# --------------------------------------------------------------- 1. ancoraggio
def esamina_scheda(v, testi, radice: Path):
    """Verdetto su una scheda: i suoi fatti si ritrovano nel documento?"""
    sintesi = (v.get("sintesi") or "").strip()
    r = {"id": v["id"], "percorso": v["percorso"], "verdetto": "", "fatti": 0,
         "non_ancorati": [], "fuori_indice": [], "nota": ""}
    if v["lettura"] in ("SENZA_TESTO", "ESCLUSO"):
        r["verdetto"] = "NON_APPLICABILE"; return r
    if v["lettura"] == "DA_LEGGERE":
        r["verdetto"] = "NON_LETTO"; return r

    if len(sintesi) < MIN_CARATTERI_SCHEDA or piatto(sintesi) in FRASI_GENERICHE:
        r["verdetto"] = "GENERICA"
        r["nota"] = f"scheda di {len(sintesi)} caratteri: non dice abbastanza per essere verificata"
        return r

    chiavi = [v["percorso"]] + ([v["versione_ocr"]] if v.get("versione_ocr") else [])
    testo = next((testi[c] for c in chiavi if c in testi), None)
    if testo is None:
        r["verdetto"] = "NON_VERIFICABILE"
        r["nota"] = "il documento non e' nell'indice: impossibile confrontare"
        return r

    elenco = fatti(sintesi)
    r["fatti"] = len(elenco)
    if not elenco:
        r["verdetto"] = "SENZA_APPIGLI"
        r["nota"] = ("nessun dato verificabile: niente date, protocolli, importi o articoli. "
                     "Puo' essere corretta, ma nessuno puo' controllarla")
        return r

    numeri = valori(testo)
    mancanti = [f for f in elenco if not ancorato(f, testo, numeri)]
    if not mancanti:
        r["verdetto"] = "ANCORATA"
        return r

    # Un dato assente dall'indice non e' ancora un dato inventato: puo' esserci
    # nel file e non essere stato raccolto. Si controlla il file stesso prima di
    # accusare chi ha letto.
    grezzo = testo_grezzo(radice / v["percorso"])
    numeri_grezzi = valori(grezzo) if grezzo else set()
    inventati, fuori_indice = [], []
    for fa in mancanti:
        voce = {"tipo": fa["tipo"], "scritto": fa["come_scritto"]}
        if grezzo and ancorato(fa, grezzo, numeri_grezzi):
            fuori_indice.append(voce)
        else:
            inventati.append(voce)
    r["non_ancorati"] = inventati
    r["fuori_indice"] = fuori_indice
    if inventati:
        r["verdetto"] = "DA_VERIFICARE"
        r["nota"] = f"{len(inventati)} dati su {len(elenco)} non esistono nel documento"
    else:
        r["verdetto"] = "FUORI_INDICE"
        r["nota"] = (f"{len(fuori_indice)} dati esistono nel file ma non nell'indice: "
                     "non sono ricercabili ne' citabili finche' l'estrazione non li raccoglie")
    return r


def cmd_ancoraggio(a):
    f, S = carica_copertura(a.cartella)
    radice = Path(S["radice"])
    testi = testi_documenti(radice)
    if testi is None:
        sys.exit("ERRORE: indice di commessa-rag non trovato. Eseguire prima: rag.py index")

    esiti = [esamina_scheda(v, testi, radice) for v in S["file"]]
    conta = {}
    for e in esiti:
        conta[e["verdetto"]] = conta.get(e["verdetto"], 0) + 1
    (f.parent / "qualita.json").write_text(
        json.dumps({"eseguito_il": datetime.now().isoformat(timespec="seconds"),
                    "riepilogo": conta, "schede": esiti}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    print("ANCORAGGIO DELLE SCHEDE AL TESTO DEI DOCUMENTI\n")
    etichette = {"ANCORATA": "ogni dato dichiarato si ritrova nel documento",
                 "DA_VERIFICARE": "dati dichiarati che NON si trovano nel documento",
                 "SENZA_APPIGLI": "schede senza alcun dato verificabile",
                 "GENERICA": "schede troppo brevi o di rito",
                 "FUORI_INDICE": "dati presenti nel file ma non raccolti dall'indice",
                 "NON_VERIFICABILE": "documento assente dall'indice",
                 "NON_LETTO": "non ancora letti",
                 "NON_APPLICABILE": "senza testo o esclusi"}
    for k in ("ANCORATA", "DA_VERIFICARE", "FUORI_INDICE", "SENZA_APPIGLI", "GENERICA",
              "NON_VERIFICABILE", "NON_LETTO", "NON_APPLICABILE"):
        if conta.get(k):
            print(f"  {conta[k]:4d}  {k:17s} {etichette[k]}")

    sospette = [e for e in esiti if e["verdetto"] == "DA_VERIFICARE"]
    if sospette:
        print(f"\nDA VERIFICARE — {len(sospette)} schede dichiarano dati che nel documento non ci sono:")
        for e in sospette:
            print(f"\n  #{e['id']} {e['percorso']}")
            for x in e["non_ancorati"]:
                print(f"      [{x['tipo']}] «{x['scritto']}»  non trovato nel testo")
    persi = [e for e in esiti if e.get("fuori_indice")]
    if persi:
        print(f"\nPERSI DALLA CATENA — {len(persi)} schede citano dati che il file contiene")
        print("ma che l'indice non ha raccolto: non sono ricercabili ne' citabili.")
        for e in persi:
            print(f"\n  #{e['id']} {e['percorso']}")
            for x in e["fuori_indice"]:
                print(f"      [{x['tipo']}] «{x['scritto']}»  nel file si', nell'indice no")
        print("\n  Causa tipica: l'estrattore .docx raccoglie paragrafi e tabelle ma non")
        print("  intestazioni e pie' di pagina, dove negli atti italiani stanno protocollo")
        print("  e data. Finche' non e' risolto, quei riferimenti non si possono citare.")
    deboli = [e for e in esiti if e["verdetto"] in ("SENZA_APPIGLI", "GENERICA")]
    if deboli:
        print(f"\nDA RILEGGERE — {len(deboli)} schede non contengono nulla di controllabile:")
        for e in deboli[:20]:
            print(f"  #{e['id']:4d} [{e['verdetto']}] {e['percorso']}")
        if len(deboli) > 20:
            print(f"  ... e altre {len(deboli)-20}")

    print(f"\nDettaglio: {f.parent/'qualita.json'}")
    if sospette:
        print("\nUn dato dichiarato e non presente nel documento va corretto PRIMA di usarlo:")
        print("in una riserva un numero inventato fa cadere l'affermazione che sostiene.")
        return 1
    if persi or deboli:
        print("\nNessun dato risulta inventato, ma restano rilievi da sistemare.")
        return 1
    return 0


# --------------------------------------------------------------- 2. campione
def cmd_campione(a):
    f, S = carica_copertura(a.cartella)
    esiti = {}
    q = f.parent / "qualita.json"
    if q.exists():
        esiti = {e["id"]: e for e in json.loads(q.read_text("utf-8"))["schede"]}

    leggibili = [v for v in S["file"] if v["lettura"] in ("LETTO", "PARZIALE")]
    if not leggibili:
        print("Nessuna scheda da controllare."); return 0

    obbligati, motivi = [], {}

    def aggiungi(v, motivo):
        if v["id"] not in motivi:
            obbligati.append(v); motivi[v["id"]] = motivo

    # 1. Cio' che l'ancoraggio ha gia' segnalato.
    for v in leggibili:
        e = esiti.get(v["id"])
        if e and e["verdetto"] in ("DA_VERIFICARE", "SENZA_APPIGLI", "GENERICA"):
            aggiungi(v, f"ancoraggio: {e['verdetto']}")
    # 2. Le letture dichiarate parziali: e' li' che si e' scelto cosa non leggere.
    for v in leggibili:
        if v["lettura"] == "PARZIALE":
            aggiungi(v, "lettura parziale")
    # 3. Dove sbagliare costa di piu': le schede che portano gli importi maggiori.
    con_importi = []
    for v in leggibili:
        imp = [x["valore"] for x in fatti(v.get("sintesi") or "") if x["tipo"] == "importo"]
        if imp:
            con_importi.append((max(imp), v))
    for _, v in sorted(con_importi, key=lambda x: -x[0])[:a.quanti_importi]:
        aggiungi(v, "tra gli importi piu' alti dichiarati")

    # 4. Un campione casuale del resto, con seme fisso perche' la selezione sia
    #    ripetibile: una verifica che non si puo' rifare non e' una verifica.
    resto = [v for v in leggibili if v["id"] not in motivi]
    n = max(0, round(len(resto) * a.quota))
    rnd = random.Random(a.seme)
    sorteggiati = rnd.sample(resto, min(n, len(resto)))
    for v in sorteggiati:
        motivi[v["id"]] = f"campione casuale (seme {a.seme})"

    scelti = obbligati + sorteggiati
    scelti.sort(key=lambda v: v["id"])
    (f.parent / "campione.json").write_text(
        json.dumps({"seme": a.seme, "quota": a.quota,
                    "documenti": [{"id": v["id"], "percorso": v["percorso"],
                                   "motivo": motivi[v["id"]]} for v in scelti]},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"Schede lette: {len(leggibili)}   da ricontrollare: {len(scelti)} "
          f"({100.0*len(scelti)/len(leggibili):.0f}%)\n")
    for v in scelti:
        print(f"  #{v['id']:4d}  {v['percorso']}")
        print(f"          {motivi[v['id']]}")
    print("\nRileggere questi documenti SENZA guardare la scheda esistente, e registrare:")
    print("  qualita.py rilettura <cartella> --da-stdin")
    return 0


# --------------------------------------------------------------- 3. riletture
def cmd_rilettura(a):
    f, S = carica_copertura(a.cartella)
    dest = f.parent / "riletture.json"
    R = json.loads(dest.read_text("utf-8")) if dest.exists() else {}
    validi = {v["id"] for v in S["file"]}
    n, errori = 0, []
    for riga in sys.stdin:
        riga = riga.strip()
        if not riga:
            continue
        try:
            d = json.loads(riga)
        except json.JSONDecodeError as e:
            errori.append(f"riga non valida ({e})"); continue
        if int(d.get("id", -1)) not in validi:
            errori.append(f"id #{d.get('id')} inesistente"); continue
        if not d.get("sintesi"):
            errori.append(f"#{d['id']}: sintesi mancante"); continue
        R[str(int(d["id"]))] = {"sintesi": d["sintesi"].strip(),
                                "letto_il": datetime.now().isoformat(timespec="seconds")}
        n += 1
    dest.write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Registrate {n} riletture.")
    for e in errori:
        print("  ATTENZIONE: " + e)
    return 1 if errori else 0


# --------------------------------------------------------------- 4. confronto
def cmd_confronta(a):
    f, S = carica_copertura(a.cartella)
    dest = f.parent / "riletture.json"
    if not dest.exists():
        sys.exit("ERRORE: nessuna rilettura registrata. Vedi: qualita.py campione")
    R = json.loads(dest.read_text("utf-8"))
    per_id = {v["id"]: v for v in S["file"]}

    divergenti, concordi = [], 0
    for sid, ril in sorted(R.items(), key=lambda x: int(x[0])):
        v = per_id.get(int(sid))
        if not v:
            continue
        prima = {(x["tipo"], str(x["valore"])): x["come_scritto"] for x in fatti(v.get("sintesi") or "")}
        dopo = {(x["tipo"], str(x["valore"])): x["come_scritto"] for x in fatti(ril["sintesi"])}
        solo_prima = {k: t for k, t in prima.items() if k not in dopo}
        solo_dopo = {k: t for k, t in dopo.items() if k not in prima}
        # Una divergenza pesa solo se i due lettori si contraddicono sullo stesso
        # tipo di dato. Che il secondo abbia notato un dettaglio in piu' non e'
        # un errore del primo: e' il motivo per cui si rilegge.
        tipi_prima = {k[0] for k in solo_prima}
        tipi_dopo = {k[0] for k in solo_dopo}
        contrasto = tipi_prima & tipi_dopo
        if contrasto:
            divergenti.append((v, solo_prima, solo_dopo, contrasto))
        else:
            concordi += 1

    print(f"RILETTURE A CONFRONTO: {len(R)}   concordi: {concordi}   divergenti: {len(divergenti)}\n")
    for v, sp, sd, contrasto in divergenti:
        print(f"  #{v['id']} {v['percorso']}")
        print(f"      in contrasto su: {', '.join(sorted(contrasto))}")
        for (tipo, _), t in sp.items():
            if tipo in contrasto:
                print(f"        1a lettura: [{tipo}] «{t}»")
        for (tipo, _), t in sd.items():
            if tipo in contrasto:
                print(f"        2a lettura: [{tipo}] «{t}»")
        print()
    if divergenti:
        print("Due letture indipendenti dello stesso atto danno dati diversi: aprire il")
        print("documento e stabilire quale sia giusta prima di usarne i numeri.")
        return 1
    print("Nessuna contraddizione fra prima e seconda lettura.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ancoraggio", help="verifica che i dati delle schede esistano nei documenti")
    p.add_argument("cartella"); p.set_defaults(f=cmd_ancoraggio)
    p = sub.add_parser("campione", help="sceglie i documenti da rileggere")
    p.add_argument("cartella")
    p.add_argument("--quota", type=float, default=0.15, help="frazione del resto da sorteggiare")
    p.add_argument("--quanti-importi", type=int, default=5,
                   help="quante schede con gli importi piu' alti includere sempre")
    p.add_argument("--seme", type=int, default=1, help="seme del sorteggio, per poterlo ripetere")
    p.set_defaults(f=cmd_campione)
    p = sub.add_parser("rilettura", help="registra le seconde letture (righe JSON su stdin)")
    p.add_argument("cartella"); p.add_argument("--da-stdin", action="store_true")
    p.set_defaults(f=cmd_rilettura)
    p = sub.add_parser("confronta", help="mette a fronte prima e seconda lettura")
    p.add_argument("cartella"); p.set_defaults(f=cmd_confronta)
    a = ap.parse_args()
    sys.exit(a.f(a))


if __name__ == "__main__":
    main()
