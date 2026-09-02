---
name: analisi-commessa
description: Analisi documentale ESAUSTIVA e verificabile di una commessa di appalto - censimento, integrita' dei PDF pagina per pagina con OCR a monte, indicizzazione citabile, lettura registrata di ogni atto e tre cancelli che impediscono di consegnare un'analisi incompleta o non fondata. USARE SEMPRE quando l'utente chiede di analizzare, esaminare, spogliare o passare in rassegna "tutti i documenti", "tutta la cartella", "le sottocartelle", un "fascicolo", una "commessa" o un "archivio di progetto", e come primo passo di qualsiasi perizia, riserva o claim che parta da una cartella di atti. NON usare per un singolo file gia' indicato, ne' per una ricerca puntuale in un fascicolo gia' analizzato.
argument-hint: [percorso della cartella della commessa]
---

# Analisi di commessa — orchestrazione

Coordini quattro fasi e **tre cancelli**. I cancelli presidiano i tre modi in
cui un'analisi documentale sbaglia, e sono diversi tra loro: non avere il
documento, non averlo guardato, aver scritto una cosa che dentro non c'e'.
Nessuno dei tre copre gli altri due.

Non fai tu il lavoro delle fasi: lo affidi agli agenti e verifichi gli esiti.

## Postura

**Tenta le soluzioni sicure da solo, interpella l'utente solo sulle decisioni
sue.** Rilanciare l'OCR, riprovare con un altro motore, reindicizzare, far
rileggere un lotto: fallo e basta. Escludere un atto irrecuperabile, installare
software sulla sua macchina, restringere il perimetro: sono scelte sue.
Presentagliele **in un elenco unico** alla fine di una fase, non interrompendolo
a ogni intoppo.

## Passo 0 — Verificare gli strumenti, prima di promettere qualcosa

Questo plugin orchestra skill esterne e non le sostituisce. Se mancano, dillo
subito invece di scoprirlo a meta' strada:

```
python3 <percorso>/commessa-rag/scripts/rag.py --help
```
Nei sottocomandi devono comparire `verify`, `context` e `timeline`. Se `verify`
manca, il motore e' la v1: **il terzo cancello non esistera'**, e va dichiarato
all'utente prima di cominciare, non alla consegna.

Verifica anche i motori di estrazione e OCR:
```
for p in pdftotext ocrmypdf tesseract; do command -v $p >/dev/null && echo "OK $p" || echo "-- $p mancante"; done
python3 -c "import pdfplumber, openpyxl, docx" 2>&1
```
Attenzione a un tranello: quando a `commessa-rag` mancano le sue librerie,
marca `needs_ocr` **anche i PDF perfettamente nativi**. Manderesti l'utente a
riprendere a mano documenti che non hanno alcun problema di scansione. Se quel
controllo fallisce, il problema e' una libreria, non l'OCR: dillo cosi'.

## Fase 1 — Acquisizione → **Cancello 1: integrita'**

Affida all'agente `acquisizione-atti` la cartella indicata.

Al ritorno, il cancello e' superato quando nessun PDF resta in stato
`DA_OCR_*`, `OCR_FALLITO_*` o `ILLEGGIBILE`. Gli `OCR_POVERO` non bloccano ma
**vanno portati avanti**: sono i documenti da cui non si potranno citare
virgolettati senza verificarli sull'originale, e questa informazione deve
arrivare fino alla relazione finale.

## Fase 2 — Indicizzazione

```
python3 <rag.py> init  --folder "<cartella>"
python3 <rag.py> index --folder "<cartella>"
python3 <rag.py> gate  --folder "<cartella>"
python3 <rag.py> timeline --folder "<cartella>"
```
Dopo la fase 1 il suo `needs_ocr` dovrebbe essere vuoto per costruzione: se non
lo e', qualcosa della fase 1 non ha funzionato e va capito prima di proseguire.

La `timeline` da' l'ossatura cronologica degli atti: tienila, servira' alla
fase 4 per le domande multi-hop.

## Fase 3 — Lettura → **Cancello 2: copertura**

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/copertura.py da-leggere "<cartella>" --limite 500
```
Dividi i documenti **per cartella** — non a caso — in 3 o 4 lotti, e lancia
altrettanti agenti `lettore-atti` in parallelo, uno per lotto, nello stesso
messaggio. Dividere per cartella mantiene insieme gli atti che si richiamano
(i SAL con i SAL, la corrispondenza con la corrispondenza), il che rende le
schede piu' utili.

Sotto una cinquantina di documenti un solo agente in sequenza rende di piu':
vede tutto il fascicolo nell'ordine e coglie i richiami mentre legge.

Poi:
```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/copertura.py stato "<cartella>"
```
Esce con codice 1 finche' restano documenti non letti, assenti dall'indice o
**indicizzati solo in parte**. Quest'ultimo caso e' il piu' insidioso e non lo
segnala nessun altro strumento: un PDF con alcune pagine native e altre
scansionate risulta verde nell'indice perche' lo stato guarda il documento e
non le pagine. Le pagine mute sono di norma proprio quelle firmate.

Finche' il cancello esce 1, **l'analisi non e' finita**. Non aggirarlo: se un
documento e' irrecuperabile, fallo escludere dall'utente con una motivazione,
che finira' sotto i suoi occhi nella tabella di copertura.

## Fase 4 — Merito

Ora, e solo ora, l'analisi di merito. Hai due basi complementari:
- `_inventario/schede.md`, l'indice ragionato: ti dice **cosa c'e'** in ogni
  atto, compresi quelli che nessuna ricerca avrebbe pescato;
- l'indice di `commessa-rag`, per ottenere le **citazioni verificabili**
  `fonte:pagina` di ogni fatto che finira' nella relazione.

Usale entrambe: le schede evitano di ignorare un atto perche' non e' venuto
fuori da una query; le citazioni rendono difendibile cio' che scrivi. Per il
merito quantitativo (scostamenti di computo, matrice del danno, prezzi nuovi)
passa a `cme-claims`; per gli export a `cme-plugin`.

Regola non negoziabile, che eredito da `commessa-rag`: **cita o taci**. Nessun
fatto di commessa senza `fonte:pagina`. Se un fatto non risulta, si scrive che
non risulta agli atti — e solo dopo aver ripetuto la ricerca senza filtri.

## Fase 5 — Consegna → **Cancello 3: fondatezza**

Affida la bozza all'agente `verifica-consegna`. Se torna non consegnabile,
correggi e ripeti: non e' un parere, e' un esito.

## La relazione si apre con la copertura

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/copertura.py report "<cartella>"
```
Metti la tabella **all'inizio**, non in appendice: chi legge deve sapere su
quanto si fonda l'analisi prima di leggerne le conclusioni. E se qualcosa e'
rimasto fuori, dillo anche nel corpo, in chiaro — un atto non acquisito puo'
cambiare le conclusioni, e l'utente deve poter decidere se procurarselo prima
di usarle.
