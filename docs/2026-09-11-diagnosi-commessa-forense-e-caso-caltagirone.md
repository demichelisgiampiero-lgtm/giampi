# `commessa-forense` — diagnosi, il caso Caltagirone e il piano di intervento

**Data:** 11 settembre 2026
**Branch:** `claude/recall-software-evaluation-llmvtv`
**Fonti esaminate:** il plugin `commessa-forense` v0.10.0 (copia marketplace su Drive),
`AUDIT_2026-09-05_indice-forense-nei-plugin.md`, `HANDOFF.md` della commessa Caltagirone
"Balchino" (agg. 10/09/2026).

---

## AVVERTENZA — questo documento corregge quello di stamattina

Il documento `2026-09-11-valutazione-recall-e-diagnosi-commessa-rag.md`, scritto prima di avere
accesso al plugin, proponeva di costruire una skill nuova chiamata `schedatura-atti`.

**Quella proposta e' ritirata.** `commessa-forense` fa gia' quel lavoro, e lo fa meglio: era una
proposta formulata senza aver visto il codice.

Resta valida, e anzi confermata dai fatti di Caltagirone, la diagnosi sull'OCR e sulla qualita'
dell'estrazione.

---

## 1. Cos'e' davvero `commessa-forense`

Plugin maturo: **~275 KB di Python**, tre agenti, una skill di orchestrazione.
Cinque fasi e tre cancelli.

| Fase | Cosa fa | Cancello |
|---|---|---|
| 0 · Ricognizione | verifica motore, eseguibili, librerie | — |
| 1 · Acquisizione | OCR a monte; stati `DA_OCR`, `OCR_FALLITO`, `OCR_POVERO`, `ILLEGGIBILE` | **integrita'** |
| 2 · Indicizzazione | `commessa-rag`: `init`, `index`, `gate`, `timeline` | — |
| 3 · Lettura | agenti `lettore-atti` in parallelo per lotti → `_inventario/schede.rpt` | **copertura** |
| 4 · Merito | schede (dove guardare) + citazioni `fonte:pagina` (cosa affermare) | — |
| 5 · Consegna | agente `verifica-consegna` sulla bozza | **fondatezza** |

Script principali: `copertura.py` (73 KB), `qualita.py` (88 KB), `integrita.py` (49 KB),
`ricognizione.py`, `sguardo.py` (rende le pagine in JPEG per guardare le firme a vista),
`prova_ancoraggio.py`, `prova_integrita.py`, `strumenti.py`.

**Non va ricostruito da capo.** Dentro ci sono nove difetti trovati e corretti su un fascicolo
reale di 191 file, piu' i casi ALATRI e Cava Luserta. Ricostruire significa ricomprare quelle
lezioni una per una, sulle commesse vere.

---

## 2. Il difetto strutturale: i consumatori non leggono l'inventario

Questo e' il punto che l'utente ha descritto per primo, con parole sue:

> *"un elenco di tutti i documenti presenti e tutti i documenti letti, in modo che poi si possa
> ragionare e applicare anche altri plugin, ma su un elenco di documenti che abbiamo letto e che
> abbiamo indicizzato."*

E' esattamente il **difetto A** gia' censito nell'audit del 5 settembre:

> **A** — l'entry point non cerca `_inventario/copertura.json` / `schede.rpt` e **cataloga per nome**

Stato rilevato dall'audit:

| Plugin | legge l'inventario prodotto da `commessa-forense`? |
|---|---|
| `commessa-forense` | — *(e' il produttore)* |
| `ufficio-claims` | **si'** |
| `ufficio-valutazioni-ambientali` | **si'** — corretto il 05-09-2026, v0.5.3 |
| `ufficio-verifiche-progettuali` | **NO** |
| `ufficio-put` | **NO** |
| `ufficio-progettazione` | **NO** |
| `ufficio-legale-amministrativo` | **NO** |

**Due su sei leggono la base. Gli altri quattro catalogano per nome file.**

Conseguenza pratica: `commessa-forense` fa OCR, censimento, lettura e schede; poi si invoca un
plugin specialistico e quello **riparte dai nomi dei file**, buttando via tutto. Non legge male:
**non legge affatto, indovina dal nome.**

E' da qui che nascono le tre lamentele ricorrenti — ci mettiamo tantissimo tempo, non li abbiamo
letti bene, abbiamo dovuto rivederli molte volte. Il motore di lettura funziona; **il suo
risultato non viene riusato da nessuno.**

---

## 3. Il caso Caltagirone — quattro errori, con i numeri

Fonte: `HANDOFF.md` della commessa, §§ 0, 11, 12, 14.

### 3.1 La copertura dichiara 100% con il 19% delle pagine lette

> Lettura: **781/781** — 570 integrali, 175 parziali · **3.155/16.402 pagine (19,2%)**

Il cancello e' verde. Il fascicolo e' letto per un quinto.

**Perche' i due numeri divergono:** `781/781` conta i **documenti**, `19,2%` conta le **pagine**.
Un atto risulta "letto" anche se il lettore ne ha aperte 3 pagine su 123. I 570 letti per intero
sono i documenti corti (PEC, lettere, verbali); i 175 parziali sono i malloppi (studio
idrologico-idraulico 123 pp., calcoli, datasheet, relazioni).

**Il 19% non e' di per se' un errore.** Leggere 123 pagine di studio idraulico per ricavarne una
portata e' tempo sprecato: la lettura mirata e' tecnica corretta. **L'errore e' che il cruscotto
mostra `781/781` e non dice che 13.000 pagine non sono mai state aperte**, ne' quali, ne' perche'.

### 3.2 Le letture parziali si autocertificavano — e una era falsa

Il **D.D.G. n. 3/2024** fu marcato parziale con motivazione *"riproduce il parere 627, gia' letto"*.
Ventuno pagine saltate.

Dentro c'erano i **pareri CTS 350/2023 e 526/2023, che non esistono in nessun altro punto del
fascicolo**. Da li' e' uscito il riscontro sulla **CA 4 lett. i)** (i movimenti terra ritenuti
ottemperati perche' la tavola RS07AEG0003A0 li limitava a stradelle e guadi).

Quelle pagine erano contate come lette. Il difetto e' stato trovato **il 10/09, a mano**, non da
uno strumento.

### 3.3 L'indicizzazione si e' dichiarata completa tre volte senza esserlo

> *"Tre volte il 09/09 l'indice si e' dichiarato completo (623, poi 1.051 documenti) mentre
> mancavano intere cartelle."*

Causa documentata: **`rag.py index --max-seconds N` su un fascicolo grande e' una trappola.** Ogni
giro riparte dall'inizio dell'alfabeto, ricalcola lo sha256 di ogni file e riprocessa sempre i
`needs_ocr`/`needs_attest` (non vengono mai saltati). Con ~180 di questi il tetto si consuma dentro
`As Build`/`Esecutivo` e la coda dell'alfabeto (`TeRS`, `Terre rocce`) non viene mai raggiunta.

**E il giro esce 0 anche quando scade**: un timeout che si presenta come successo.

### 3.4 Un dato sbagliato ha attraversato tre versioni

«63 campioni fino a −1,5 m» proveniva dal PUT. I verbali di campionamento dicono **65 campioni da
0 a −1 m**. L'errore e' rimasto in Analisi v01, v02, v03 e negli elaborati `_Elaborati CEA` di
agosto, corretto solo il 10/09.

Stessa dinamica per l'argomento **«variazione n. 8 imposta da SNAM»**: **falso** — la tecnica
l'ha proposta il D.L. con PEC del 17/07/2025 — eppure ha retto **due versioni dell'Atto 1 e due
dell'Analisi**. Il documento che lo smentiva stava dentro uno dei **64 contenitori chiusi**
(`.p7m`, zip e rar annidati) aperti in quattro giri.

### 3.5 Altri residui rilevati dallo stesso HANDOFF

- **148 `OCR_POVERO`** su 749 PDF unici (517 integri, 84 `OCR_OK`, 0 irrecuperabili).
- **108 schede su 457 da verificare** all'ancoraggio (349 ancorate).
- **Gli allegati dei `.msg` non vengono aperti dal plugin.** Il verbale di campionamento del
  cavidotto (10/10/2023) esiste **solo** dentro `postacert.eml (841 MB).msg`: estratto a mano il
  10/09, non ancora in fascicolo.
- **`_inventario` finisce nell'indice** (7 documenti): il plugin indicizza i propri registri.
- 5 documenti indicizzati solo in parte; 15 censiti ma non in indice.
- `D.D.G. 78/2022` ha il layer testo cifrato: il cancello di ancoraggio lo segnala tutto come
  «NON TROVATO» — falso positivo atteso.

---

## 4. Il filo comune: il criterio di completamento

I quattro errori sono lo stesso errore quattro volte, ed e' gia' stato nominato nel §14 dello
HANDOFF:

> **«Il silenzio non e' una fine.»** *Un timeout scambiato per convergenza, un giro scaduto con
> codice 0, due giri falliti letti come «niente da fare».*
> **Il criterio di completamento deve verificare il risultato atteso, non l'assenza di attivita'.**

Ogni conteggio del plugin misura la cosa sbagliata:

| Oggi conta | Dovrebbe contare |
|---|---|
| atti (781) | **pagine** (16.402) |
| giri eseguiti | **risultato atteso** |
| cio' che il lettore dichiara | cio' che e' **verificato** |

Non e' la lettura a essere lenta. **Sono le verifiche che il cancello dovrebbe fare da solo e che
finiscono per essere rifatte a mano** — tardi, quando l'errore e' gia' dentro tre versioni del
documento.

---

## 5. Il lavoro buono non viene capitalizzato

Gli strumenti che risolvono due dei quattro errori **esistono gia'**, scritti durante le sessioni
di Caltagirone:

| Script | Cosa fa | Dove vive oggi |
|---|---|---|
| `parziali_confronto.py` | confronta sui 5-grammi le pagine dichiarate «gia' lette» — smaschera §3.2 | **scratchpad di sessione** |
| `indicizza2.py` | verifica l'indice per cartella di primo livello — smaschera §3.3 | **scratchpad di sessione** |
| `md2doc.py` | produzione DOCX/PDF | percorso temporaneo, da ricopiare a mano ogni volta |

**Lo scratchpad e' per sessione: evapora.** Nello stesso HANDOFF ci si annota il percorso
temporaneo di `md2doc.py` con l'istruzione di ricopiarlo.

Si risolve il problema, si scrive lo strumento giusto, e poi lo strumento sparisce. La sessione
dopo ricomincia da zero. **Questa e' la risposta piu' onesta alla domanda «perche' non riusciamo a
farlo in maniera piu' semplice».**

Lo stesso vale per il plugin: l'audit rilevava che `commessa-forense` risulta **assente dal
deposito sorgente e dal deposito runtime** — esiste solo nel marketplace.

---

## 6. Piano di intervento

Ordinato per rapporto fra beneficio e sforzo. Nessuno di questi e' un plugin nuovo.

| # | Intervento | Chiude | Sforzo |
|---|---|---|---|
| **1** | **Copertura in pagine oltre che in atti.** `781/781` diventa anche `3.155/16.402`, con l'elenco delle pagine saltate e la motivazione dichiarata | §3.1 | medio |
| **2** | **`parziali_confronto.py` dentro il cancello di copertura.** Ogni «gia' letto» verificato dalla macchina, subito, non a mano a fine lavoro | §3.2 | basso — lo script esiste |
| **3** | **`indicizza2.py` come criterio di fine indicizzazione**, per cartella di primo livello. Mai «nessun documento nuovo» | §3.3 | basso — lo script esiste |
| **4** | **Divieto di `--max-seconds`** scritto nel `SKILL.md`, con la ragione | §3.3 | minimo |
| **5** | **Ramo di lettura dell'inventario nei quattro plugin consumatori** (`ufficio-legale-amministrativo`, `ufficio-verifiche-progettuali`, `ufficio-put`, `ufficio-progettazione`). Non e' codice nuovo: `ufficio-claims` ce l'ha gia' e funziona — si copia | §2 | medio, ripetuto 4 volte |
| **6** | **Regola D alla fonte**: una scheda che non riferisce nulla di usabile non incrementa la copertura | audit §4 | basso |
| **7** | **Apertura degli allegati `.msg`** in fase di acquisizione | §3.5 | medio |
| **8** | **Escludere `_inventario` dall'indicizzazione** e vietarne lettura e citazione nei prompt dei lettori | §3.5 | minimo |
| **9** | **Mettere il plugin nei depositi giusti**, sorgente compreso, e gli script fuori dallo scratchpad | §5 | basso |

**Gli interventi 2, 3, 4 e 9 sono quasi gratuiti** e chiudono due dei quattro errori di
Caltagirone piu' la dispersione degli strumenti. Da li' conviene partire.

### Decisione che spetta all'utente

L'intervento **1** e' quello che cambia di piu' la percezione: **il giorno che la copertura si
misura in pagine, il 100% di oggi diventa onestamente un 19%**. Non e' un peggioramento del
lavoro — e' la fine di un dato che rassicurava senza fondamento. Va deciso consapevolmente.

---

## 7. Cosa NON fare

- **Non ricostruire il plugin da capo.** Vedi §1.
- **Non sostituire `commessa-rag`.** Nessun prodotto commerciale offre insieme citazione
  `fonte:pagina` verificata e cancello `verify` sui virgolettati. Vedi il documento di stamattina.
- **Non aggiungere cancelli nuovi prima di aver reso riusabile l'inventario** (§2): finche' i
  consumatori catalogano per nome, migliorare la lettura non produce effetti a valle.

---

## 8. Da verificare al PC

1. `copertura.py` conta gia' le pagine da qualche parte, o il dato `3.155/16.402` e' calcolato
   altrove? Determina se l'intervento 1 e' una modifica o un'aggiunta.
2. `parziali_confronto.py` e `indicizza2.py` sono ancora recuperabili, o lo scratchpad che li
   conteneva e' gia' stato ripulito?
3. La copia viva del plugin: marketplace, PC, o zip `commessa-forense-v0.10.0.zip` su Drive?
4. Le **tre regole d'uso per fascicoli voluminosi** in corso di stesura: quali sono, per non
   duplicare il lavoro.
