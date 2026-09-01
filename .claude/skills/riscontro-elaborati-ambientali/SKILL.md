---
name: riscontro-elaborati-ambientali
description: >-
  Riscontro critico di elaborati ambientali italiani per procedimenti di VIA,
  verifica di assoggettabilità (screening art. 19 D.Lgs. 152/2006), valutazione
  di incidenza e recupero ambientale di cave e siti: Studio Preliminare
  Ambientale, Studio di Impatto Ambientale, Studio di Incidenza, relazioni
  tecniche e geologiche, piani di monitoraggio ambientale, computi e allegati di
  progetto. Verifica i contenuti obbligatori sulla griglia dell'Allegato IV-bis e
  sui criteri dell'Allegato V, controlla la vigenza delle norme citate,
  l'aritmetica dei dati e — soprattutto — incrocia più elaborati della stessa
  commessa per far emergere le contraddizioni fra documenti, che sono i vizi più
  gravi e i meno visibili. Usare questa skill ogni volta che l'utente carica o
  nomina uno SPA, un SIA, uno studio di incidenza, una relazione tecnica o
  geologica, un piano di monitoraggio, un certificato di destinazione
  urbanistica o altri atti di una pratica ambientale, e chiede di analizzarli,
  revisionarli, verificarli, confrontarli, correggerli o di usarne uno come
  modello — anche se non nomina l'Allegato IV-bis, lo screening o la VIA, e anche
  se chiede genericamente "guarda questo documento" o "che ne pensi".
---

# Riscontro di elaborati ambientali

Questa skill serve a esaminare elaborati di pratiche ambientali italiane con il
rigore di chi dovrà difenderli in istruttoria, o contestarli.

Il committente tipico non vuole un riassunto: vuole sapere **dove il documento
cede**. Un riassunto lo sa scrivere da sé; quello che non può fare in fretta è
riscontrare 90 pagine contro una griglia normativa, far quadrare i numeri e
accorgersi che due elaborati firmati dicono cose incompatibili.

## Prima di tutto: preparare gli strumenti

Gli elaborati arrivano in `.docx`, `.pdf` nativo o `.pdf` scansionato, e capita
di dover installare qualcosa. Esegui:

```bash
bash scripts/setup.sh
```

Poi estrai ogni documento con lo script bundled, che gestisce i tre formati,
ricade automaticamente sull'OCR quando il PDF non ha livello testo, e stampa
subito il profilo strutturale:

```bash
python scripts/estrai.py <file> --out <dir>
```

Non riscrivere questi passaggi a mano: sono già stati sbagliati abbastanza volte.
Le insidie note (LibreOffice che non converte, poppler assente, `cryptography` di
sistema rotto) sono in `references/ambiente.md`, da leggere solo se qualcosa
fallisce.

## Il metodo, in cinque passi

### 1. Classificare il documento prima di leggerlo

Il nome del file mente. `SPACAS009_PMA_R02.pdf` è un Piano di Monitoraggio
Ambientale, non uno Studio Preliminare Ambientale; «SPA» designa sia lo Studio
*Preliminare* Ambientale (art. 19, screening) sia lo Studio di *Prefattibilità*
Ambientale (ex art. 20 D.P.R. 207/2010, oggi nel PFTE), che hanno indice e
finalità diversi.

Apri la copertina e le prime pagine e stabilisci **cosa è davvero**, perché da
questo dipende quale griglia applicare. `references/tipologie-elaborati.md`
elenca i tipi ricorrenti con i tratti che li distinguono.

Se il committente lo ha chiamato in un altro modo, diglielo subito e con
naturalezza: è un'informazione utile, non un rilievo.

### 2. Misurare le proporzioni

Conta pagine, paragrafi e tabelle **per capitolo** — lo script lo fa per te. Le
proporzioni raccontano il documento prima del merito.

In uno SPA reale la trattazione dello screening occupava 7 pagine su 94, il
resto era studio di incidenza: il rapporto ha rivelato che era uno studio di
incidenza con un cappello di screening, prima ancora di leggerne una riga di
merito. Un capitolo portante lungo mezza pagina, o un'appendice più lunga del
corpo, sono segnali dello stesso tipo.

### 3. Riscontrare sulla griglia, non sull'impressione

Per lo screening: contenuti obbligatori dell'**Allegato IV-bis**, criteri
dell'**Allegato V**. La griglia completa, con la checklist voce per voce, è in
`references/griglia-allegato-iv-bis.md`.

Per ogni voce assegna: **presente / parziale / assente**, e motiva.

Il passaggio che fa la differenza è distinguere il **trattamento reale** dalla
**citazione di stile**. Cerca il termine nel testo e guarda *dove* ricorre: se
«cumulo» compare dieci volte e tutte dentro la descrizione di cosa la guida
metodologica richiederebbe, il cumulo non è stato valutato — il documento ne
parla, non lo fa. Lo stesso vale per alternative, opzione zero, rischio
climatico, transfrontalierità.

### 4. Verificare aritmetica e vigenza

**I numeri devono quadrare fra loro.** Volume ÷ numero di viaggi = capacità
dell'automezzo; conferimenti giornalieri × giornate = totale; tonnellate ÷ metri
cubi = densità plausibile. Quando tornano, dillo: è un indice di affidabilità
dell'intero elaborato. Quando non tornano, hai trovato qualcosa.

Controlla anche i conteggi interni: «sei componenti su nove» va verificato
contando le righe della tabella di sintesi.

**Le norme citate vanno riscontrate alla data di redazione.** Un elaborato del
2018 che fonda lo screening sull'art. 20 del D.Lgs. 152/2006 cita una norma già
sostituita dall'art. 19 per effetto del D.Lgs. 104/2017. Verifica anche le
abrogazioni differite: il D.P.R. 120/2017 reca un'abrogazione subordinata
all'entrata in vigore di un decreto attuativo, e se quel decreto è in vigore
tutto ciò che vi si fonda cade.

### 5. Incrociare gli elaborati

**È il passo di maggior valore, e quello che nessuno fa.** I vizi peggiori non
stanno dentro un documento: stanno *fra* i documenti della stessa commessa, dove
nessun lettore singolo li vede.

Casi reali incontrati:

- lo SPA assume il regime di sottoprodotto come **esclusivo e determinante** per
  la classificazione dell'opera; la relazione tecnica firmata lo qualifica come
  **eventuale** («qualora vengano impiegate…»). Letti separatamente, entrambi
  sembrano corretti;
- la relazione geologica dichiara l'assenza di vincolo idrogeologico; il
  certificato di destinazione urbanistica lo attesta. Qui non è una divergenza
  di opinioni: un atto certificativo smentisce un elaborato di parte;
- gli elaborati indicano tre particelle catastali, il C.D.U. ne individua cinque;
- lo stesso fatto — una classificazione PAI in P4/R4 — è pregiudiziale di
  ammissibilità in un documento e semplice raccomandazione esecutiva in un altro.

Quando disponi di più elaborati, costruisci un **registro delle discordanze**:
numerale, indica per ciascuna i documenti coinvolti e, se uno dei due è un atto
certificativo o un provvedimento, segnalalo — quella non è una discordanza da
comporre, è un errore da correggere.

Se rivedi una **versione successiva** di un documento già esaminato, non
rileggerlo da zero: verifica voce per voce se le discordanze del registro sono
chiuse, aperte, o **riformulate in forma peggiore** — capita, ed è il rilievo
più prezioso. Controlla anche gli effetti collaterali: una rinumerazione dei
capitoli invalida tutti i rinvii incrociati degli altri elaborati.

## Regola trasversale: cita o taci

Ogni riferimento normativo o si riscontra sulla fonte, o si marca
`[DA VERIFICARE]` indicando la fonte da consultare. Mai a memoria.

Quando manca la fonte, si può comunque scrivere il testo nominando l'istituto
per esteso — «piano di utilizzo», «dichiarazione di avvenuto utilizzo» — e
lasciando il numero d'articolo da apporre. Un elaborato che dichiara ciò che non
sa è più forte di uno che finge completezza: è esattamente ciò che distingue una
bozza tecnica utilizzabile da una che espone il committente.

## Struttura del rapporto

Adatta le sezioni al caso, ma questo impianto regge bene:

```
# Titolo — documento esaminato
Tabella d'identificazione: oggetto, procedura, consistenza, data, firma
## Giudizio d'insieme            (3-6 righe, il quadro; niente suspense)
## Difetti sostanziali           (numerati, ciascuno con la citazione testuale)
## Difetti formali               (tabella)
## Cosa il documento fa bene     (mai ometterla — vedi sotto)
## Copertura della griglia       (tabella requisito → esito)
## Da fare                       (liste separate: interno al testo / dipendente da acquisizioni)
```

Cita **testualmente** il passaggio contestato, tra virgolette, con il
riferimento a pagina o capitolo. Un rilievo senza la frase che lo fonda non è
verificabile e il committente non può usarlo.

La sezione su ciò che funziona non è cortesia: serve a proteggere le parti buone
dalle riscritture successive, e a indicare cosa riutilizzare altrove. Se un
elaborato scadente contiene un buon apparato di condizioni ambientali, quello va
salvato.

Ordina i rilievi per **gravità**, non per ordine di pagina. Il primo rilievo è
quello che farebbe respingere l'istanza.

## Se ti viene chiesto di intervenire sul documento

Modifica sempre una **copia**, mai l'originale, e verificalo dopo:

- confronto paragrafo per paragrafo di tutto ciò che è fuori dall'ambito
  dell'intervento, per dimostrare che è rimasto intatto;
- validazione strutturale del file prodotto;
- se il rendering non è disponibile, dillo — non dichiarare una verifica visiva
  che non hai fatto.

Riscrivendo una clausola, la regola è **eliminare i rinvii in bianco**. Formule
come «materiali consentiti dal titolo autorizzativo», «ovvero altri materiali
ammessi», «quando applicabile» sono la porta da cui entra la riqualificazione
dell'opera. Scrivi in positivo e in via esclusiva, elenca in negativo ciò che è
escluso, e chiudi con una clausola che impedisce l'interpretazione estensiva.

## Tenere il diario

Le commesse durano più di una sessione e il contesto non sopravvive. Mantieni un
`DIARIO.md` con cronologia, decisioni prese, questioni aperte e vincoli tecnici
appresi. Aggiornalo quando chiudi un passo, non alla fine.
