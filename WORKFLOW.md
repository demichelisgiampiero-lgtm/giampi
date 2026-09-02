# Analisi di una commessa — istruzioni operative

Questo file è scritto per essere dato a Claude Code su una macchina che **non
conosce nulla** di come è nato. Contiene tutto il necessario per eseguire
l'analisi documentale completa di un fascicolo di commessa.

> **Come si usa.** Apri Claude Code nella cartella di questo repository e digli:
> *«Segui `WORKFLOW.md` sulla cartella `<percorso della commessa>`».*

---

## Cosa fa, in una riga

Prende una cartella di atti di commessa e produce un'analisi in cui **ogni
documento risulta letto o esplicitamente escluso con motivazione**, e ogni
affermazione è ancorata a una citazione verificata.

## Perché serve

Un'analisi documentale incompleta non dà errore: dà una relazione che sembra
finita. Tre modi in cui accade, che non si coprono a vicenda:

1. **Il documento non c'è** — è una scansione da cui non è stato estratto nulla,
   oppure sta in una sottocartella che nessuno ha aperto.
2. **C'è ma nessuno l'ha guardato** — è indicizzato, ma nessuna ricerca l'ha mai
   restituito. Una ricerca dà solo ciò che la domanda chiede.
3. **È stato letto ma citato male** — il virgolettato non corrisponde a quanto
   scritto nella pagina citata.

A ciascuno corrisponde un cancello, e i cancelli non si aggirano.

---

## Convenzioni adottate

Sono decisioni prese in fase di progetto. Se una non corrisponde al modo di
lavorare dell'utente, **chiediglielo prima di partire** e adeguati.

| | Convenzione |
|---|---|
| Perimetro | Si analizza l'intera cartella. Oltre ~300 documenti, proporre un perimetro ristretto e **dichiararlo nella relazione**. |
| Soglia OCR | Un documento è segnalato quando meno del **12%** delle parole risulta italiano riconoscibile. Segnala, non blocca. |
| Lettura mirata | Oltre ~80 pagine si legge in modo mirato e **lo si dichiara**, invece di fingere una lettura integrale. |
| Esclusioni | Un atto irrecuperabile lo esclude **sempre l'utente**, non l'agente. Raccogliere le richieste in un elenco unico a fine fase. |
| Duplicati | Stesso contenuto in due cartelle = **un documento solo**, con nota della doppia collocazione. |
| Versioni | `Capitolato.pdf` e `Capitolato_rev2.pdf` sono due documenti. Quale sia il contrattuale **lo decide l'utente**. |
| PDF da OCR | Scritto **accanto** all'originale con suffisso `_OCR`. L'originale non si tocca mai: in un contenzioso è la prova. |

## Postura

Tenta da solo ciò che è reversibile e senza conseguenze: rilanciare l'OCR,
cambiare motore, reindicizzare, far rileggere un lotto, riformulare una ricerca.

Chiedi all'utente ciò che decide lui: escludere un atto, installare software,
restringere il perimetro, stabilire quale versione è la contrattuale.
**Raccogli queste richieste in un elenco unico a fine fase**, invece di
interromperlo a ogni intoppo.

---

## Passo 0 — Ricognizione dell'ambiente

Non promettere nulla prima di sapere cosa c'è.

```bash
python3 plugins/commessa-forense/scripts/ricognizione.py
```

Esce con codice **1** se manca qualcosa di bloccante, e stampa i comandi di
installazione per il sistema in uso. In quel caso: riportali all'utente,
attendi che li esegua, e ripeti.

Se manca `verify` in `commessa-rag` (è la v1), **il terzo cancello non
esisterà**: dillo adesso, non alla consegna.

### Il tranello di `needs_ocr`

`needs_ocr` di `commessa-rag` significa **«non ho ricavato testo»**, non «è una
scansione». Ci finisce dentro anche un PDF nativo che il suo estrattore non è
riuscito ad aprire — una tabella `xref` danneggiata basta.

Verificato sul campo: lo stesso file dà `0 pagine, 0 caratteri` a `pdfplumber`
e `1 pagina, 165 caratteri` a un estrattore che ignora la struttura di
indicizzazione. Mandarlo all'OCR sarebbe il rimedio sbagliato — si rasterizza
una pagina per riconoscere da capo parole già presenti, perdendo accuratezza.

Il Passo 1 distingue i due casi perché legge con un metodo diverso. Se un file
è `needs_ocr` per `commessa-rag` ma il Passo 1 ne ha estratto il testo, è un
**file danneggiato**: ripararlo e reindicizzare, non passarlo all'OCR.

```bash
qpdf --qdf --object-streams=disable danneggiato.pdf riparato.pdf
```

---

## Passo 1 — Acquisizione

```bash
python3 plugins/commessa-forense/scripts/copertura.py censisci "<CARTELLA>"
python3 plugins/commessa-forense/scripts/integrita.py "<CARTELLA>"
```

Il censimento fissa **il denominatore**: da qui in poi ogni affermazione sulla
completezza si misura contro quel numero. Mostralo all'utente subito — se dice
«mancano i verbali», si è scoperto in trenta secondi che la cartella indicata
non è quella giusta, invece che ad analisi finita.

`integrita.py` controlla ogni PDF **pagina per pagina**, passa all'OCR le
scansioni scrivendo un PDF ricercabile accanto all'originale, e ne **misura la
resa** sulla quota di parole italiane riconosciute.

Esiti in `<CARTELLA>/_inventario/integrita.json`:

| Esito | Significato | Cosa fare |
|---|---|---|
| `INTEGRO` | tutte le pagine hanno testo | nulla |
| `OCR_OK` | scansione riconosciuta con resa buona | nulla |
| `OCR_POVERO` | l'OCR ha reso poco | **non blocca**, ma da questi documenti non si citano virgolettati senza verificarli sull'originale. Portare l'avvertenza fino alla relazione. |
| `DA_OCR_*` | nessun motore OCR disponibile | bloccante: far installare l'OCR |
| `OCR_FALLITO_*` | l'OCR è girato ma non ha prodotto nulla | bloccante: probabile scansione illeggibile |
| `ILLEGGIBILE` | cifrato, corrotto, o struttura non leggibile | bloccante: chiedere una copia sana o la password |

Poi rilancia il censimento, perché riconosca i PDF appena prodotti:

```bash
python3 plugins/commessa-forense/scripts/copertura.py censisci "<CARTELLA>"
```

### ▌CANCELLO 1 — Integrità

**Superato quando** nessun PDF resta in stato `DA_OCR_*`, `OCR_FALLITO_*` o
`ILLEGGIBILE`.

Se qualcosa resta e non è risolvibile, va **escluso dall'utente** con una
motivazione, che finirà sotto i suoi occhi nella tabella di copertura.

---

## Passo 2 — Indicizzazione

Il percorso di `rag.py` lo dà il Passo 0. Poi:

```bash
python3 "<RAG>" init     --folder "<CARTELLA>"
python3 "<RAG>" index    --folder "<CARTELLA>"
python3 "<RAG>" gate     --folder "<CARTELLA>"
python3 "<RAG>" timeline --folder "<CARTELLA>"
```

Dopo il Passo 1 il suo `needs_ocr` dovrebbe essere **vuoto per costruzione**. Se
non lo è, qualcosa a monte non ha funzionato: capirlo prima di proseguire, non
dopo.

Conserva l'esito di `timeline`: è l'ossatura cronologica degli atti, e serve al
Passo 4 per costruire le domande.

---

## Passo 3 — Lettura

```bash
python3 plugins/commessa-forense/scripts/copertura.py da-leggere "<CARTELLA>" --limite 500
```

Dividi i documenti **per cartella** — non a caso — in 3 o 4 lotti, e lancia
altrettanti agenti `lettore-atti` in parallelo, **nello stesso messaggio**.
Dividere per cartella tiene insieme gli atti che si richiamano (i SAL con i SAL,
la corrispondenza con la corrispondenza).

**Sotto ~50 documenti conviene un lettore solo, in sequenza**: vede tutto il
fascicolo nell'ordine e coglie i richiami tra un atto e l'altro mentre legge.

Il testo di ogni documento si ottiene dall'indice:

```bash
python3 "<RAG>" page --folder "<CARTELLA>" --file "<percorso relativo>" --pagina <n>
```

Per i documenti con una versione `_OCR`, leggi quella: è l'unica che ha testo.

Ogni documento va registrato con **una riga di sintesi**, in un'unica chiamata
per lotto:

```bash
python3 plugins/commessa-forense/scripts/copertura.py letto "<CARTELLA>" --da-stdin <<'FINE'
{"id":12,"sintesi":"OdS n.7 del 14/03/2024, prot. 4471: sospensione parziale km 3+200/4+100 per sottoservizi non rilevati in progetto."}
{"id":13,"sintesi":"PEC 02/04/2024 della SA: nega i maggiori oneri della riserva n.3, imputando la sospensione a carente organizzazione di cantiere."}
FINE
```

**La sintesi è obbligatoria** e lo script rifiuta le registrazioni che ne sono
prive. Non è burocrazia: una riga del genere è impossibile da scrivere senza
aver aperto il documento, ed è ciò che distingue «l'atto è disponibile» da
«l'atto è stato guardato».

Scrivi **fatti, non impressioni**: date, protocolli, importi, articoli
richiamati, chi scrive a chi, quantità e prezzi se è un computo.
*«Corrispondenza varia»* non è una sintesi. *«PEC 02/04/2024 della SA che nega i
maggiori oneri della riserva n.3»* lo è.

Annota anche ciò che appare **anomalo** rispetto agli altri atti del lotto — una
quantità che non torna, una data fuori sequenza, un richiamo a un documento mai
visto. Segnalalo senza trarne conclusioni: chi legge il fascicolo intero le
trarrà meglio.

### Documenti oltre ~80 pagine

Leggi indice, premesse e le parti pertinenti; cerca mirato i termini che
contano; **dichiaralo**:

```bash
python3 plugins/commessa-forense/scripts/copertura.py parziale "<CARTELLA>" 7 \
  --sintesi "Capitolato, 412 pagine. Letti: indice, artt. 1-40 (oneri e termini), Capo VII (riserve)." \
  --motivo "documento di 412 pagine: lettura mirata sugli articoli rilevanti per la riserva"
```

La lettura parziale dichiarata è legittima. Quella spacciata per integrale no.

### ▌CANCELLO 2 — Copertura e attendibilità della lettura

Due controlli, perché una copertura senza attendibilità non vale nulla: aver
letto tutto ma male non è meglio che non aver letto.

**a) Ho guardato tutto?**

```bash
python3 plugins/commessa-forense/scripts/copertura.py stato "<CARTELLA>"
```

Fa quadrare tre numeri: **censiti**, **indicizzati**, **letti uno per uno**.
Esce con codice **1** finché restano documenti non letti, assenti dall'indice o
**indicizzati solo in parte**.

Quest'ultimo caso è il più insidioso e non lo segnala nessun altro strumento: un
PDF con alcune pagine native e altre scansionate risulta verde nell'indice,
perché lo stato guarda il documento e non le pagine. Verificato eseguendo
`index_pdf` di `rag.py` su un registro di 5 pagine con 2 acquisite a scanner:
`status='indexed'`, chunk ricercabili solo sulle pagine `[1, 2, 5]`. Le pagine
mute sono di norma proprio quelle firmate.

**Finché esce 1, l'analisi non è finita.** Per escludere un atto irrecuperabile:

```bash
python3 plugins/commessa-forense/scripts/copertura.py escludi "<CARTELLA>" 4 \
  --motivo "verbale acquisito a scanner, OCR non riuscito: contenuto NON acquisito"
```

**b) Quello che ho scritto sui documenti è vero?**

```bash
python3 plugins/commessa-forense/scripts/qualita.py ancoraggio "<CARTELLA>"
```

Ogni scheda contiene fatti duri — date, protocolli, importi, articoli, quantità
— e ognuno viene cercato nel testo del documento. Il confronto è **per valore e
non per forma**: `121.500,00`, `121500.0` e `121.500` sono lo stesso importo, e
segnalarli come diversi produrrebbe falsi allarmi a raffica.

| Esito | Significato | Cosa fare |
|---|---|---|
| `ANCORATA` | ogni dato dichiarato si ritrova nel documento | nulla |
| `DA_VERIFICARE` | **il dato non esiste nel documento** | bloccante: correggere la scheda prima di usarne i numeri |
| `FUORI_INDICE` | il dato è nel file ma l'indice non l'ha raccolto | il dato non è citabile finché non si ripara l'estrazione |
| `SENZA_APPIGLI` | la scheda non contiene nulla di controllabile | rileggere il documento |
| `GENERICA` | scheda troppo breve o di rito | rileggere il documento |

`DA_VERIFICARE` è il caso grave: significa che chi ha letto ha scritto un dato
che nel documento non c'è. In una riserva un numero inventato è il rilievo che
fa cadere l'affermazione che sostiene.

`FUORI_INDICE` non è colpa di chi ha letto: è la catena che perde contenuto. La
causa tipica è che l'estrattore `.docx` di `commessa-rag` raccoglie paragrafi e
tabelle **ma non intestazioni e piè di pagina** — ed è lì che negli atti
italiani stanno numero di protocollo e data. Verificato: `Prot. 4471 del
14/03/2024` è nel file e non nell'indice. Finché non è risolto, quei riferimenti
si possono leggere ma **non citare**: vanno riportati come dato di scheda, non
come citazione `fonte:pagina`.

**c) Seconda lettura a campione** (facoltativa, per fascicoli che finiranno in
contraddittorio)

```bash
python3 plugins/commessa-forense/scripts/qualita.py campione "<CARTELLA>" --quota 0.15
```

Sceglie chi rileggere dando la precedenza a dove sbagliare costa di più: le
schede già segnalate, le letture dichiarate parziali, quelle che portano gli
importi più alti, più un sorteggio del resto **con seme fisso**, perché una
verifica che non si può ripetere non è una verifica.

Rileggi quei documenti **senza guardare la scheda esistente** — altrimenti non è
una seconda lettura, è una conferma — e registra:

```bash
python3 plugins/commessa-forense/scripts/qualita.py rilettura "<CARTELLA>" --da-stdin <<'FINE'
{"id":21,"sintesi":"..."}
FINE
python3 plugins/commessa-forense/scripts/qualita.py confronta "<CARTELLA>"
```

Il confronto segnala solo le **contraddizioni** sullo stesso tipo di dato. Che
il secondo lettore abbia notato un dettaglio in più non è un errore del primo:
è il motivo per cui si rilegge.

---

## Passo 4 — Merito

Solo ora l'analisi vera. Due basi complementari, e servono entrambe:

- **`_inventario/schede.md`** — l'indice ragionato: dice cosa c'è in ogni atto,
  compresi quelli che nessuna ricerca avrebbe pescato;
- **l'indice di `commessa-rag`** — per le citazioni verificabili `fonte:pagina`
  di ogni fatto destinato alla relazione.

```bash
python3 "<RAG>" search --folder "<CARTELLA>" \
  --queries "sospensione lavori" "fermo cantiere" "sosta forzata" --k 12 --explain
```

Leggi sempre il campo `avvisi`: dice cosa il motore ha tolto di mezzo (documenti
senza data esclusi dai filtri, atti fuori dal filtro di categoria). **Prima di
scrivere «non risulta agli atti», ripeti la ricerca senza filtri.**

Regola non negoziabile: **cita o taci**. Nessun fatto di commessa senza
`fonte:pagina`.

Per il merito quantitativo — scostamenti di computo, matrice del danno, prezzi
nuovi — passa alla skill `cme-claims`. Per gli export, a `cme-plugin`.

---

## Passo 5 — Consegna

### ▌CANCELLO 3 — Fondatezza

```bash
python3 "<RAG>" verify --folder "<CARTELLA>" --bozza "<bozza.md>" --strict
```

Accerta che ogni virgolettato esista davvero nella pagina citata. Esce con
codice **1** se resta un rilievo bloccante.

Gli esiti `APPROSSIMATO` **non sono un via libera**: significano che il testo c'è
ma non nella forma scritta, e vanno riallineati all'originale prima della firma.
`verify` controlla i virgolettati, non le parafrasi: un'affermazione parafrasata
con citazione sbagliata passa il cancello, quindi la revisione umana resta
necessaria.

### La relazione si apre con la copertura

```bash
python3 plugins/commessa-forense/scripts/copertura.py report "<CARTELLA>"
```

Produce `copertura.md` e `schede.md` in `_inventario/`.

Metti la tabella di copertura **all'inizio della relazione, non in appendice**:
chi legge deve sapere su quanto si fonda l'analisi prima di leggerne le
conclusioni. Qualcosa del genere:

> Analizzati **47 documenti su 47** presenti nella cartella e nelle
> sottocartelle: 41 letti integralmente, 2 parzialmente (capitolati oltre 300
> pagine, letti sugli articoli pertinenti), 3 allegati grafici privi di testo,
> 1 escluso — verbale scansionato, OCR non riuscito: **contenuto non acquisito**.

E se qualcosa è rimasto fuori, dillo anche **nel corpo**, in chiaro: un atto non
acquisito può cambiare le conclusioni, e l'utente deve poter decidere se
procurarselo prima di usarle.

---

## Se qualcosa va storto

| Sintomo | Causa probabile | Rimedio |
|---|---|---|
| `needs_ocr` su un PDF che sembra normale | file danneggiato, non scansione | `qpdf --qdf --object-streams=disable in.pdf out.pdf`, poi reindicizza |
| L'OCR gira ma rende caratteri senza senso | scansione storta o a bassa risoluzione | `ocrmypdf --deskew --clean --force-ocr -l ita in.pdf out.pdf` |
| Un `.xls` non si apre | è un `.xlsx` rinominato | `integrita.py` lo riconosce dai byte iniziali; per `rag.py` rinominare il file |
| `verify` non esiste | `commessa-rag` è la v1 | aggiornare la skill, oppure dichiarare che la bozza **non è verificata** |
| Il cancello 2 non passa mai | qualche documento non è mai stato registrato | `copertura.py da-leggere` per vedere quali |
| Un protocollo non si trova nell'indice | sta nell'intestazione del Word, che `rag.py` non legge | leggerlo dalla scheda, non citarlo come `fonte:pagina` |
| `ancoraggio` segnala un importo corretto | forme numeriche diverse | il confronto è per valore: se accade, è un difetto da segnalare |

## Limiti noti, da dichiarare all'utente

- **Questo flusso non è mai stato eseguito per intero.** Gli script sono
  collaudati singolarmente su un fascicolo di prova sintetico; la lettura in
  parallelo con più agenti non è mai girata.
- **L'OCR non è mai stato eseguito**: sulla macchina di sviluppo non c'era alcun
  motore installato. Il percorso che produce il PDF ricercabile è scritto e non
  verificato: è la prima cosa da controllare.
- Il fascicolo di prova era **sintetico**, costruito per contenere le trappole
  note. Verifica la meccanica, non sostituisce una commessa reale.

Se durante l'esecuzione qualcosa non torna, **dillo invece di aggirarlo**: il
senso di questo flusso è esattamente che si opponga alla fretta di consegnare.
