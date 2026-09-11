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
| ~~1~~ | ❌ **GIA' IMPLEMENTATO IN SORGENTE — v. §6-quater.** ~~Copertura in pagine oltre che in atti.~~ `781/781` diventa anche `3.155/16.402`, con l'elenco delle pagine saltate e la motivazione dichiarata. **Specifica al §6-bis** | §3.1 | medio |
| **2** | **`parziali_confronto.py` dentro il cancello di copertura.** Ogni «gia' letto» verificato dalla macchina, subito, non a mano a fine lavoro | §3.2 | basso — lo script esiste |
| **3** | **`indicizza2.py` come criterio di fine indicizzazione**, per cartella di primo livello. Mai «nessun documento nuovo» | §3.3 | basso — lo script esiste |
| **4** | **Divieto di `--max-seconds`** scritto nel `SKILL.md`, con la ragione | §3.3 | minimo |
| **5** | **Ramo di lettura dell'inventario nei quattro plugin consumatori** (`ufficio-legale-amministrativo`, `ufficio-verifiche-progettuali`, `ufficio-put`, `ufficio-progettazione`). Non e' codice nuovo: `ufficio-claims` ce l'ha gia' e funziona — si copia | §2 | medio, ripetuto 4 volte |
| **6** | **Regola D alla fonte**: una scheda che non riferisce nulla di usabile non incrementa la copertura | audit §4 | basso |
| **7** | **Apertura degli allegati `.msg`** in fase di acquisizione | §3.5 | medio |
| **8** | **Escludere `_inventario` dall'indicizzazione** e vietarne lettura e citazione nei prompt dei lettori | §3.5 | minimo |
| **9** | ⬆️ **SALITO IN CIMA** — **`commessa-forense` nel repository `giampi`**, versionato, con caricamento del plugin solo da li'. Piu' gli script fuori dallo scratchpad. Motivo al §6-ter.1-2 | §5, §6-ter | basso |

**Gli interventi 2, 3, 4 e 9 sono quasi gratuiti** e chiudono due dei quattro errori di
Caltagirone piu' la dispersione degli strumenti. Da li' conviene partire.

### Decisione che spetta all'utente

L'intervento **1** e' quello che cambia di piu' la percezione: **il giorno che la copertura si
misura in pagine, il 100% di oggi diventa onestamente un 19%**. Non e' un peggioramento del
lavoro — e' la fine di un dato che rassicurava senza fondamento.

**Deciso l'11/09/2026: si procede.** Specifica al §6-bis.

> ⚠️ **Superato lo stesso giorno.** La lettura del codice sorgente ha mostrato che la
> copertura in pagine **e' gia' implementata** dal 7 settembre, in forma piu' completa della
> specifica. **Leggere il §6-quater**: il §6-bis resta solo come documentazione di cosa si
> era chiesto, non come lavoro da fare.

---

## 6-bis. DECISO — l'intervento 1: copertura in pagine

Decisione dell'utente dell'11/09/2026: **la copertura si misura in pagine.**

### Il dato esiste gia'

L'HANDOFF riporta `3.155/16.402 pagine (19,2%)` e distingue `570 integrali, 175 parziali con
pagine`. Il conteggio per pagina e' quindi **gia' calcolato**: la scheda di una lettura parziale
registra quali pagine sono state aperte.

**Non e' un dato da aggiungere: e' un dato da portare dentro il cancello.** Oggi esiste nel report
e non incide su nulla.

### I tre cambiamenti

**1 — `copertura.py report`: entrambi i numeri affiancati, mai uno solo.**

```
Atti letti:     781/781        (100%)
Pagine lette:   3.155/16.402   (19,2%)
```

Sotto, l'elenco degli atti con pagine scoperte e la motivazione dichiarata. E' la tabella che va
in testa alla relazione: chi legge deve vedere **su quanta carta** si fonda l'analisi, non solo su
quanti atti.

**2 — `copertura.py stato`: un atto parziale non si chiude.**

Oggi il cancello esce 1 finche' restano documenti non letti, assenti dall'indice o indicizzati
solo in parte. Deve esporre anche il conteggio delle pagine e **tenere esplicite le pagine
scoperte** di ogni atto letto in parte, invece di considerarlo concluso.

**3 — La motivazione della lettura parziale diventa un campo tipizzato.**

Oggi il lettore scrive prosa libera (*"riproduce il 627, gia' letto"*), che nessuno puo'
controllare. Deve invece dichiarare una causa presa da un elenco chiuso:

| Causa | Significato | Controllo |
|---|---|---|
| `MIRATA` | lettura mirata deliberata (calcoli, datasheet, schemi, certificati) | nessuno — e' una scelta legittima, ma resta visibile nell'elenco |
| `RIPRODUCE` | il contenuto e' gia' stato letto in un altro atto | **verificata da `parziali_confronto.py`**; se il confronto fallisce, l'atto torna da leggere |
| `ILLEGGIBILE` | pagine non estraibili | rimanda al cancello di integrita' |

### Il criterio di blocco — proporzionato

**Il cancello NON deve bloccare sulla percentuale di pagine.** Pretendere il 100% delle pagine
sarebbe assurdo: nessuno legge 123 pagine di studio idraulico per ricavarne una portata, e la
lettura mirata e' tecnica corretta.

Sulle pagine il cancello **informa**: mostra il numero, elenca gli atti scoperti, lascia la
decisione all'operatore.

**Blocca invece sulle `RIPRODUCE` non verificate**, perche' quelle non sono scelte: sono
affermazioni, e finche' non sono provate sono affermazioni non verificate. E' esattamente il caso
del D.D.G. 3 (§3.2).

### Effetto atteso, da mettere in conto

Il giorno in cui la modifica entra in servizio, **la copertura di Caltagirone passa da `100%` a
`19,2%`**. Il lavoro non peggiora di un millimetro: finisce soltanto un numero che rassicurava
senza averne titolo.

---

## 6-ter. ATTENZIONE — due copie divergenti di `commessa-forense`

Rilevato su Drive l'11/09, **prima di toccare il codice**:

| | `plugins/commessa-forense/` | `commessa-forense_marketplace/` |
|---|---|---|
| `scripts/copertura.py` | **105.602 byte** | 73.295 byte |
| `scripts/qualita.py` | **120.324 byte** | 87.667 byte |
| ultima modifica | **7 settembre** | 6 settembre |
| cartella `prove/` | **presente** | assente |
| `plugin.json` | da verificare | v0.10.0 |

**Il deposito marketplace e' indietro di oltre 30 KB su entrambi gli script**, piu' la cartella
dei test: circa il 30% del codice.

E' la stessa classe di problema segnalata al §6 dell'audit del 05-09 (*"la sorgente e' indietro:
si rischia di ripartire da li'"*), qui a parti invertite.

**Prima di qualsiasi modifica va stabilito quale copia e' quella viva**, altrimenti si patcha il
ramo sbagliato e si perde il lavoro dell'altro. E' anche la ragione per cui il punto 9 del piano
(rimettere il plugin in un deposito unico e versionato) non e' burocrazia: e' cio' che impedisce
che questo succeda di nuovo.

### 6-ter.1 — La copia che gira e' un caricamento manuale (rilevato l'11/09)

Il plugin installato risulta:

```
Commessa forense — di local-desktop-app-uploads · 0.10.0 · 1 competenza · aggiornato 6 giorni fa
```

`local-desktop-app-uploads` significa **caricato a mano dall'app desktop**: la sorgente vive sul
PC, e la copia installata e' una **fotografia congelata al momento del caricamento**.
«6 giorni fa» rispetto all'11/09 = **5 settembre**.

Incrociando con Drive:

| Copia | Ultima modifica | `copertura.py` |
|---|---|---|
| **installata (in esercizio)** | **5 settembre** | ? |
| `plugins/commessa-forense/` | **7 settembre** | 105.602 byte |
| `commessa-forense_marketplace/` | 6 settembre (copia in blocco) | 73.295 byte |

Le date di `plugins/` sono sfalsate (`copertura.py` 16:22, `qualita.py` 17:08): sembrano
lavorazioni reali, non una copia in blocco.

**Ipotesi da verificare, non ancora confermata:** su Caltagirone (9-10 settembre) potrebbe essere
girata la versione del **5 settembre**, priva delle modifiche del 7. Se cosi' fosse, parte dei
difetti rilevati potrebbe essere **gia' corretta in sorgente e mai entrata in esercizio**.

**Controllo che chiude la questione**, sulla cartella sorgente del plugin al PC:

```powershell
Get-Item .\scripts\copertura.py, .\scripts\qualita.py | Select-Object Name, Length, LastWriteTime
```

Confronto: **105.602 / 120.324** (ramo `plugins/`) contro **73.295 / 87.667** (ramo marketplace).

### 6-ter.2 — Il problema e' il meccanismo, non la singola versione

Con il caricamento manuale, **ogni modifica fatta sul PC non ha effetto finche' non si ricarica il
plugin**. Il codice che si modifica e il codice che gira sono due cose distinte, e nulla lo
ricorda all'operatore.

E' questo che genera i disallineamenti che l'audit del 05-09 rincorreva a mano. Non e' disordine:
**e' l'assenza di una fonte unica.**

**Conseguenza sul piano: il punto 9 sale in cima.** Mettere `commessa-forense` nel repository
`giampi`, versionarlo, e caricare il plugin sempre e solo da li'. Una fonte, una storia, e
`git log` al posto del confronto fra le dimensioni dei file.

Ogni modifica al codice — a partire dall'intervento 1 — va seguita da un **ricaricamento
esplicito**, altrimenti non entra in esercizio.

---

## 6-quater. CORREZIONE — l'intervento 1 e' gia' implementato in sorgente

Letto `copertura.py` della copia viva (105.602 byte, 7 settembre; confermata dall'utente come
quella sul PC). **La copertura in pagine c'e' gia', ed e' piu' completa della specifica del
§6-bis.**

### Cosa fa gia' `cmd_stato`

```
COPERTURA DI LETTURA: 781/781 = 100.0%  (documenti)
COPERTURA IN PAGINE : 3155/16402 = 19.2%  <- quanto fascicolo e' stato guardato
  Le due misure rispondono a domande diverse: la prima dice quanti
  atti sono stati aperti, la seconda quanta carta e' stata letta.
```

| Funzione | Riga | Cosa fa |
|---|---|---|
| `conta_pagine()` | 701 | interpreta `"1-5,32,40"`; `-1` se la dicitura non si legge |
| `copertura_in_pagine()` | 730 | somma le pagine; restituisce anche gli atti **senza dichiarazione** |
| `pagine_da_indice()` | 767 | prende `{percorso: n_pagine}` dall'indice di `commessa-rag` |
| `cmd_parziale` | 1535 | **`--pagine` obbligatorio**, con validazione del formato |
| `cmd_pagine` | 1556 | dichiarazione **retroattiva** per i fascicoli lavorati prima dell'obbligo |

Piu': il marcatore **`(MINIMO)`** quando qualche parziale non dichiara le pagine (*«e' un rilievo
e non uno zero»*), il blocco **BLOCCANTE** sulle parziali senza pagine, e la gestione delle buste
`.p7m` nel denominatore (*«misurato il 6 settembre 2026 su Bottegone»*).

### Il §3.1 di questo documento era sbagliato nella premessa

Il `781/781` non nascondeva nulla: lo strumento stampava gia' entrambe le misure, e l'HANDOFF le
citava entrambe. La riga dell'HANDOFF e' stata letta come se fosse l'esito del cancello, e non lo
era. **Nessuna patch da scrivere sulla copertura in pagine.**

Resta valido il §3.1 come descrizione del fenomeno (100% di atti != 100% di carta); cade la parte
che lo dava per non implementato.

### Cio' che invece NON e' implementato — ed e' il difetto che ha prodotto il danno

Su `cmd_parziale`, **`--motivo` e' obbligatorio ma non viene mai verificato**. Ricerca su tutto
`copertura.py`: nessun controllo sul contenuto del motivo, nessun richiamo a un confronto di testo.

Quindi questa registrazione passa senza rilievi:

```
--motivo "riproduce il parere 627, gia' letto"  --pagine "1-8,34-39"
```

Le pagine dichiarate entrano nel conteggio, il cancello e' soddisfatto, e **le 21 pagine del
D.D.G. 3 contenenti i pareri CTS 350/2023 e 526/2023 restano fuori senza che nulla lo segnali.**

**Il difetto §3.2 e' l'unico dei quattro rimasto intatto, ed e' quello che e' costato caro su
Caltagirone.** Lo strumento che lo chiuderebbe, `parziali_confronto.py`, e' ancora nello
scratchpad (§5).

### Piano rivisto

| Ordine | Intervento | Stato |
|---|---|---|
| 1 | Verificare quale versione e' **in esercizio** (caricamento del 5 vs sorgente del 7) e, se serve, ricaricare | da fare, costo nullo |
| 2 | **`--motivo` tipizzato e verificato**: causa `RIPRODUCE` → esegue `parziali_confronto.py`; se il confronto non regge, l'atto torna da leggere | **il vero intervento** |
| 3 | Ramo di lettura dell'inventario nei quattro plugin consumatori (§2) | la richiesta originaria |
| 4 | Plugin nel repository, script fuori dallo scratchpad | §6-ter.2 |

~~Intervento 1 del §6~~ — **gia' implementato, cancellato dal piano.**

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
3. **Quale copia del plugin e' quella viva** — v. §6-ter: le due su Drive divergono di oltre
   30 KB per script. **Da chiarire prima di scrivere una riga di codice.**
4. Le **tre regole d'uso per fascicoli voluminosi** in corso di stesura: quali sono, per non
   duplicare il lavoro.
