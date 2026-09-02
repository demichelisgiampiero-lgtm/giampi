---
name: inventario-documenti
description: Analisi ESAUSTIVA e verificabile di tutti i documenti in una cartella e nelle sue sottocartelle, con censimento, estrazione (PDF nativi e scansionati con OCR, Excel, Word, legacy, e-mail) e cancello di copertura che impedisce di concludere l'analisi finche' ogni file non risulta letto o esplicitamente escluso con motivazione. USARE SEMPRE quando l'utente chiede di analizzare, esaminare, leggere, spogliare o passare in rassegna "tutti i documenti", "tutti i file", "tutta la cartella", "le sottocartelle", un "fascicolo", una "commessa", un "archivio di progetto" o "quello che trovi nella cartella X", anche se non chiede esplicitamente una verifica di completezza. Usarla anche come primo passo di qualsiasi analisi documentale su cartella prima di cme-claims, commessa-rag o di una perizia, perche' garantisce che nessun documento venga saltato. NON usare per un singolo file gia' indicato dall'utente, ne' per cercare una singola informazione puntuale in un archivio gia' inventariato.
---

# Inventario documenti — analisi esaustiva con copertura verificabile

## Il problema che questa skill risolve

Quando qualcuno chiede «analizza tutti i documenti nella cartella», la tentazione
naturale e' procedere per esplorazione: si aprono i file che dal nome sembrano
rilevanti, si coglie il senso generale, ci si ferma quando si ritiene di aver
capito abbastanza. Su un fascicolo di commessa questo produce un'analisi che
*sembra* completa e non lo e'. Ed e' il tipo di errore peggiore, perche' e'
silenzioso: non c'e' nessun messaggio di errore, solo una relazione con dentro
un buco che nessuno vede.

Ci sono tre modi tipici in cui un documento sparisce senza far rumore:

1. **Non viene mai aperto.** Sta in una sottocartella profonda, ha un nome poco
   evocativo (`doc_scan_0043.pdf`), e l'esplorazione non ci arriva.
2. **Viene aperto ma e' vuoto.** E' un PDF scansionato: l'estrazione restituisce
   zero caratteri senza sollevare eccezioni, e il file risulta "processato".
3. **Viene letto a meta'.** Un Excel con fogli nascosti, un Word con il
   protocollo nell'intestazione, una PEC con l'allegato che conta.

Il rimedio non e' impegnarsi di piu'. E' togliere la discrezionalita' su *cosa*
leggere: prima si conta cosa c'e', poi si estrae tutto, poi si legge contando, e
alla fine un controllo automatico verifica che i due numeri coincidano. Se non
coincidono, l'analisi non si consegna.

## Il flusso in quattro fasi

Gli script stanno in `scripts/` e lavorano su una cartella di servizio
`_inventario/` creata dentro la cartella analizzata. Sono autosufficienti: non
richiedono librerie da installare, usano quelle presenti se ci sono.

### Fase 1 — Censimento

```bash
python3 scripts/inventario.py "/percorso/della/cartella"
```

Cammina l'albero e scrive `_inventario/manifest.json`. Da qui in poi **il numero
di file censiti e' il numero di riferimento**: ogni affermazione sulla
completezza si misura contro quello.

Mostrare all'utente il riepilogo che lo script stampa, prima di proseguire. Serve
a lui per riconoscere il proprio fascicolo — se dice «mancano i verbali», si e'
scoperto subito che la cartella indicata non e' quella giusta, invece che a
analisi finita.

### Fase 2 — Estrazione

```bash
python3 scripts/estrai.py "/percorso/della/cartella"
```

Estrae il testo di ogni file e assegna a ciascuno uno stato esplicito. Gli stati
che contano davvero sono quelli che si fermano:

- `RICHIEDE_OCR` — il PDF e' una scansione e l'OCR non e' disponibile. **Non e'
  un dettaglio tecnico: e' un documento il cui contenuto non abbiamo.** Nei
  fascicoli di commessa le scansioni sono proprio gli atti che pesano di piu':
  verbali firmati, ordini di servizio, corrispondenza protocollata.
- `MANCA_STRUMENTO` — serve un programma non installato. Il messaggio dice quale.
- `ERRORE`, `PROTETTO` — il file non si e' aperto.

Se compaiono questi stati, leggere `references/formati.md` per il comando di
installazione, proporlo all'utente, e rilanciare con `--solo-mancanti`.
Se l'utente non puo' o non vuole installare nulla, si prosegue — ma quei
documenti vanno esclusi *esplicitamente* (Fase 4), non fatti sparire.

### Fase 3 — Lettura registrata

Questa e' la fase che cambia il comportamento, ed e' bene capire perche'
funziona. Registrare la lettura di un file richiede di scrivere una riga su cosa
contiene: quella riga e' impossibile da produrre senza aver davvero aperto il
documento. E' il motivo per cui la sintesi e' obbligatoria e lo script rifiuta le
registrazioni che ne sono prive.

```bash
python3 scripts/registro.py da-leggere "/percorso" --limite 15
```

Poi, per ogni gruppo: leggere i testi estratti indicati (sono normali file `.txt`
in `_inventario/testi/`) e registrarli **in un'unica chiamata**, una riga JSON
per documento:

```bash
python3 scripts/registro.py letto "/percorso" --da-stdin <<'FINE'
{"id":12,"sintesi":"Ordine di servizio n.7 del 14/03/2024: sospensione parziale km 3+200/4+100 per sottoservizi non rilevati."}
{"id":13,"sintesi":"Verbale di sospensione 20/03/2024, firmato DL e impresa. Ripresa non ancora disposta."}
FINE
```

Criteri per una sintesi utile: **fatti, non impressioni**. Date, numeri di
protocollo, importi, articoli richiamati, chi scrive a chi. «Corrispondenza
varia» non e' una sintesi; «PEC 02/04/2024 della SA che nega i maggiori oneri
della riserva n.3» lo e'. Queste righe diventano `schede.md`, l'indice ragionato
del fascicolo: e' un prodotto che ha valore per l'utente anche da solo.

Sul dimensionamento dei gruppi: procedere a lotti di circa 10-15 documenti, o
meno se sono voluminosi. Non serve leggere tutto il fascicolo prima di
registrare — registrare lotto per lotto significa che il lavoro fatto resta
tracciato anche se la sessione si interrompe.

**Documenti molto voluminosi.** Un capitolato da 400 pagine non entra
comodamente in lettura integrale. In quel caso: leggere indice, premesse e le
parti pertinenti all'incarico, cercare mirato i termini che contano, e
registrare onestamente cosa si e' fatto:

```bash
python3 scripts/registro.py parziale "/percorso" 7 \
  --sintesi "Capitolato speciale, 412 pagine. Letti: indice, artt. 1-40 (oneri e termini), Capo VII (riserve)." \
  --motivo "documento di 412 pagine: lettura mirata sugli articoli rilevanti per la riserva"
```

La lettura parziale dichiarata e' legittima e comparira' come tale nella tabella
di copertura. La lettura parziale spacciata per integrale e' il problema che
questa skill esiste per impedire.

### Fase 4 — Cancello di copertura

```bash
python3 scripts/registro.py stato "/percorso"
```

Lo script esce con codice 1 finche' restano file non estratti o non letti, e
dice quali. **Finche' esce 1, l'analisi non e' finita.** Non ci sono scorciatoie
qui: se un documento non si riesce proprio a trattare, si esclude motivando, e la
motivazione finisce nel report sotto gli occhi dell'utente.

```bash
python3 scripts/registro.py escludi "/percorso" 4 \
  --motivo "PDF scansionato, OCR non disponibile: contenuto non acquisito"
```

Quando il cancello passa:

```bash
python3 scripts/registro.py report "/percorso"
```

produce `copertura.md` e `schede.md` in `_inventario/`.

## Come consegnare l'analisi

Aprire la risposta con la tabella di copertura — non chiuderla in fondo. Il
lettore deve sapere *su quanto* si fonda l'analisi prima di leggerne le
conclusioni, non dopo. Bastano poche righe:

> Analizzati **47 documenti su 47** presenti nella cartella e nelle
> sottocartelle: 41 letti integralmente, 2 parzialmente (capitolati oltre 300
> pagine, letti sugli articoli pertinenti), 3 allegati grafici senza testo, 1
> escluso (verbale scansionato, OCR non riuscito — **contenuto non acquisito**).

Poi l'analisi vera e propria. E se qualcosa e' rimasto fuori, dirlo qui, in
chiaro, non solo nell'allegato: un documento non acquisito puo' cambiare le
conclusioni, e l'utente deve poter decidere se procurarselo prima di usarle.

## Quando l'utente chiede una cosa specifica

Se la domanda e' mirata («quanto vale la riserva n.3?»), il fascicolo va
comunque coperto per intero: e' proprio nei documenti che sembrano irrilevanti
che si trova la PEC che cambia la risposta. Quello che cambia e' la profondita'
di lettura, non la copertura — sui documenti lontani dal tema basta una sintesi
breve, ma vanno aperti.

## Rapporto con le altre skill

Questa skill copre l'**acquisizione**: garantisce che tutto sia stato letto.
L'analisi di merito resta alle skill specialistiche, che vanno usate dopo:

- `cme-claims` — confronto CME contrattuale/eseguito, matrice del danno
- `commessa-rag` — ricerca citabile con riferimento fonte:pagina
- `cme-plugin` — conversione ed export di computi

I testi in `_inventario/testi/` sono normali file `.txt` gia' pronti da dare in
pasto a quelle skill, quindi il lavoro di estrazione non va rifatto.

## Approfondimenti

- `references/formati.md` — come viene trattato ogni formato, cosa installare
  per OCR e file legacy, e i limiti noti di ciascun metodo di estrazione
- `references/risoluzione-problemi.md` — cosa fare quando il cancello non passa
