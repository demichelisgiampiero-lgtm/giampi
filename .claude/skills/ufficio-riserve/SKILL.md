---
name: ufficio-riserve
description: >-
  Ufficio Riserve — analizza la documentazione di un appalto di opere civili
  (contratto, CSA, cronoprogramma, SAL, registro di contabilità, libretto delle
  misure, ordini di servizio, verbali, perizie, corrispondenza di cantiere) e
  costruisce le riserve dell'appaltatore giuridicamente "inattaccabili" ai sensi
  del D.Lgs. 36/2023 (Allegato II.14). Usala quando l'utente deve individuare i
  fatti pregiudizievoli, qualificarli giuridicamente, verificare tempestività e
  decadenza, quantificare il quantum e redigere il testo della riserva e il
  dossier probatorio. Trigger: "riserva", "riserve appaltatore", "iscrivere una
  riserva", "claim cantiere", "SAL", "registro di contabilità", "decadenza
  riserve", "accordo bonario".
---

# Ufficio Riserve — costruzione di riserve "inattaccabili"

## 1. Cosa fa questa skill

Trasforma la documentazione di un appalto di opere civili in **riserve
dell'appaltatore blindate**: ogni riserva prodotta è tempestiva, specifica,
quantificata, motivata e ancorata a una base giuridico-contrattuale, così da
**resistere alla contestazione** della stazione appaltante, del direttore dei
lavori (DL), del collaudatore, del Collegio Consultivo Tecnico (CCT) e del
giudice, senza incorrere in **decadenza**.

"Inattaccabile" qui significa: **nessuno dei vizi che fanno respingere una
riserva è presente** — non è tardiva, non è generica, non è priva di domanda,
non è priva di quantum, non è priva di prova, non è scaduta per mancata
conferma.

> Questa skill produce bozze tecnico-giuridiche di supporto al RUP, al
> direttore tecnico e al legale. **Non sostituisce il parere dell'avvocato**:
> ogni riserva con effetti decadenziali va validata da un professionista
> abilitato prima dell'iscrizione.

## 2. Quadro normativo (sintesi operativa)

Riferimento: **D.Lgs. 36/2023, Allegato II.14** (contabilità e direzione dei
lavori) e art. 115 (controllo tecnico-contabile). Dettaglio completo in
[`reference/normativa-riserve.md`](reference/normativa-riserve.md).

Regole che determinano la validità (tutte **a pena di decadenza**):

1. **Dove**: la riserva si iscrive nel **registro di contabilità** (oggi anche
   dematerializzato), al momento della firma; va **confermata in ogni SAL** e
   ribadita nel **conto finale**.
2. **Quando (tempestività)**: all'atto della firma del documento contabile
   immediatamente successivo al **verificarsi o cessare** del fatto che ha
   prodotto il pregiudizio. L'iscrizione tardiva = decadenza.
3. **Esplicazione e quantificazione**: entro **15 giorni** dalla firma
   l'appaltatore deve **esplicare** la riserva e **quantificare** le domande in
   modo preciso. Mancata/insufficiente esplicazione nei termini = decadenza.
4. **Controdeduzioni DL**: il DL formula le proprie **motivate deduzioni** nei
   **15 giorni** successivi (la loro assenza non sana la riserva, ma genera
   responsabilità del DL).
5. **Fatti continuativi**: per fatti ad andamento continuo la riserva va
   **rinnovata/aggiornata** nel quantum ad ogni atto contabile finché il fatto
   persiste.
6. **Soglia accordo bonario**: quando l'importo delle riserve raggiunge la
   soglia di legge (rif. art. 210/211 e Allegato; ordine del **~5%–15%**
   dell'importo contrattuale) si attiva il procedimento di **accordo bonario**.
7. **CCT**: per opere sopra soglia/strategiche, le riserve possono essere
   esaminate dal **Collegio Consultivo Tecnico**.

## 3. Workflow (8 fasi)

Esegui in ordine. Non saltare la fase 4 (tempestività) e la 7 (checklist): sono
quelle che rendono la riserva inattaccabile.

### Fase 1 — Acquisizione e indicizzazione documentale
Raccogli e cataloga i documenti d'appalto. Elenco e tassonomia in
[`reference/documenti-input.md`](reference/documenti-input.md). Per ogni
documento registra: tipo, data, protocollo, autore, e i fatti rilevanti.
Costruisci una **timeline** unica degli eventi di cantiere (cronologia
contrattuale vs reale).

### Fase 2 — Individuazione dei fatti pregiudizievoli
Scorri la documentazione e isola ogni evento che genera **maggiore onere,
danno, ritardo o pregiudizio** all'appaltatore. Catalogo dei tipi ricorrenti in
[`reference/tassonomia-riserve.md`](reference/tassonomia-riserve.md)
(es.: ritardata consegna aree, sospensioni illegittime, varianti e maggiori
quantità, anomalie/carenze progettuali, interferenze e sovrapposizioni,
andamento anomalo dei lavori, oneri di sicurezza aggiuntivi, revisione prezzi,
ritardati pagamenti/interessi).

### Fase 3 — Qualificazione giuridico-contrattuale
Per ogni fatto, individua la **base normativa e contrattuale** (articolo del
D.Lgs. 36/2023, clausola del CSA, prescrizione del contratto/cronoprogramma) e
il **titolo della pretesa** (inadempimento SA, factum principis, sopravvenienza,
errore progettuale, ecc.). Senza titolo giuridico chiaro la riserva è
aggredibile per genericità.

### Fase 4 — Verifica tempestività e mappa delle decadenze ⚠️
Per ciascun fatto incrocia la **data dell'evento** con la **data del primo atto
contabile utile** (firma registro/SAL). Determina:
- se la riserva è stata (o va) iscritta **nei termini**;
- la **scadenza dei 15 giorni** per l'esplicazione/quantificazione;
- per fatti continuativi, le **conferme** dovute ad ogni SAL.
Produci un **registro delle scadenze** con semaforo (verde = nei termini,
giallo = in scadenza, rosso = decaduta/da motivare la rimessione in termini).
Questa è la fase che salva o affossa il claim.

### Fase 5 — Quantificazione (quantum)
Calcola l'importo della pretesa con metodo trasparente e replicabile. Distingui
**maggiori oneri** documentati (costi diretti, manodopera, mezzi, materiali),
**danni** (improduttività, prolungamento, spese generali — formule tipo
Hudson/Emden/Eichleay come riferimento metodologico, vedi
[`reference/best-practice-internazionali.md`](reference/best-practice-internazionali.md)),
**interessi** e **revisione**. Ogni voce deve essere **ancorata a una prova**.

### Fase 6 — Analisi del ritardo (delay analysis), se rilevante
Per riserve da tempo/ritardo, applica un metodo riconosciuto (as-planned vs
as-built, time impact analysis, windows) collegando **causa → effetto → giorni
→ costo**. Vedi best practice internazionali nel reference dedicato.

### Fase 7 — Redazione della riserva
Scrivi il testo usando il modello in
[`reference/template-riserva.md`](reference/template-riserva.md): intestazione,
fatto, base giuridico-contrattuale, domanda, quantum con calcolo, richiami
probatori, riserva di aggiornamento per fatti continuativi.

### Fase 8 — Checklist di inattaccabilità (gate finale) ✅
Sottoponi ogni riserva alla
[`reference/checklist-inattaccabilita.md`](reference/checklist-inattaccabilita.md).
Se anche **un solo** requisito è "NO", **non** dichiarare la riserva pronta:
evidenzia il gap e come colmarlo. Output finale solo a checklist piena.

## 4. Output prodotti

1. **Timeline degli eventi** (contrattuale vs reale) con i fatti pregiudizievoli.
2. **Schede riserva** (una per fatto): testo pronto all'iscrizione + quantum.
3. **Registro delle scadenze/decadenze** con semaforo.
4. **Dossier probatorio**: per ogni riserva, l'elenco puntuale dei documenti a
   supporto (con protocollo e data).
5. **Cruscotto soglia accordo bonario**: somma riserve vs soglia di legge.
6. **Report dei gap**: cosa manca per rendere inattaccabile ogni riserva.

## 5. Principi guida (non negoziabili)

- **Niente genericità**: ogni riserva indica fatto, titolo, domanda, quantum,
  prova. Una riserva "con riserva di quantificare" senza seguito è decaduta.
- **Tempestività prima di tutto**: meglio una riserva iscritta nei termini e poi
  esplicata, che una perfetta ma tardiva.
- **Contemporaneous records**: la prova si costruisce in corso d'opera, non a
  posteriori. Segnala sempre quali registrazioni mancano.
- **Causa-effetto dimostrata**: collega ogni pretesa economica al fatto e alla
  clausola, con nesso causale esplicito.
- **Tracciabilità**: ogni numero deve essere rifacibile dalla SA partendo dai
  documenti citati.
- **Conferma e rinnovo**: ricorda sempre le conferme ai SAL e al conto finale.

## 6. Domande da porre all'utente se mancano dati

- Qual è la **data dell'ultimo atto contabile firmato** e la data del **prossimo
  SAL**? (per calcolare le scadenze)
- Il registro di contabilità è **cartaceo o dematerializzato**?
- L'importo contrattuale (per la **soglia accordo bonario**)?
- Esiste già un **CCT** insediato?
- Quali documenti probatori sono **effettivamente disponibili** (giornale
  lavori, foto datate, OdS, corrispondenza PEC)?
