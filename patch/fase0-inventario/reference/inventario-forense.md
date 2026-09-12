# L'inventario forense — protocollo di lettura

Da mettere in `reference/` di ogni plugin che legge un fascicolo di commessa.
Descrive come usare cio' che `commessa-forense` ha gia' prodotto, e i cinque presidi che
impediscono di usarlo male.

Scritto il 12 settembre 2026, dopo il collaudo su Caltagirone. Sostituisce e amplia la
correzione del 5 settembre.

---

## 1. Perche' esiste

`commessa-forense` legge un fascicolo una volta: apre i contenitori, passa all'OCR cio' che serve,
censisce, fa leggere ogni atto e ne scrive una scheda. Il risultato sta in `_inventario/`.

**Un plugin che cataloga per nome file butta via tutto quel lavoro e ricomincia a indovinare.**
Non legge male: non legge affatto.

E' il difetto censito come **A** nell'audit del 5 settembre 2026:

> l'entry point non cerca `_inventario\copertura.json` / `schede.rpt` e cataloga per nome

---

## 2. Cosa c'e' dentro `_inventario/`

| File | Contenuto |
|---|---|
| `copertura.json` | il registro: un record per file, con classe, esito di lettura, sintesi, pagine lette |
| `schede.rpt` | l'indice ragionato leggibile: **cosa c'e'** in ogni atto |
| `copertura.rpt` | la tabella di copertura, da mettere in testa alla relazione |

Campi del registro che servono a chi legge:

| Campo | Significato |
|---|---|
| `classe` | `ATTO` · `DERIVATO` · `DUPLICATO` · `SERVIZIO` · `PROPRIO` — **si lavora sugli ATTO** |
| `lettura` | `LETTO` · `PARZIALE` · `ESCLUSO` · `SENZA_TESTO` |
| `pagine_lette` | su una `PARZIALE`: quali pagine, come `"1-5,32,40"` |
| `causa_parziale` | `MIRATA` · `RIPRODUCE` · `ILLEGGIBILE` — **assente = mai dichiarata** |
| `riproduce` | l'atto di cui e' copia, **verificato dal confronto**. Assente = non provato |
| `versione_ocr` | il PDF estratto da una busta firmata: il testo sta li' |
| `censito_il` | (in testa al file) quando il censimento e' stato fatto |

---

## 3. FASE 0 — la modalita' forense

### Come riconoscerla

Nella cartella indicata esiste `_inventario/copertura.json` con un `censito_il` valorizzato.

### Cosa comporta

Un `_inventario/` valido **ha gia' superato il cancello di integrita' di `commessa-forense`**.
Quindi l'OCR a monte e' fatto, e il `gate` di `commessa-rag` **non si bloccera' sui `needs_ocr`**:
non serve rifare nulla di quella fase.

### Come si usa

1. **Leggere `schede.rpt` PRIMA di cercare.** Dice cosa c'e' in ogni atto, compresi quelli che
   nessuna query avrebbe mai pescato. La ricerca serve dopo, per la citazione.
2. **Prendere il perimetro dal registro**, non dai nomi dei file: gli `ATTO` sono gli atti; i
   `DUPLICATO`, `DERIVATO`, `SERVIZIO` e `PROPRIO` non si ricontano.
3. **Verificare lo stato prima di promettere un'analisi completa:**
   ```
   copertura.py stato "<cartella>"
   ```
   Esce **1** finche' restano documenti non letti, assenti dall'indice o indicizzati solo in
   parte. Se esce 1, l'analisi **non e' completa**, e va detto.
4. **Per la citazione, `commessa-rag`.** Le schede dicono *dove guardare*; la citazione
   `fonte:pagina` si prende dal motore e si verifica con `verify`.

### Cosa NON fare

- **Non ricensire** e non ricatalogare per nome: il registro c'e' gia'.
- **Non rilanciare l'OCR**: e' gia' stato fatto, e rifarlo su un PDF nativo peggiora il testo.
- **Non citare dal registro.** Vedi il presidio 1.

---

## 4. I cinque presidi

### 🔴 1 — L'indice non e' la fonte

**Dalla scheda si prende il DOVE GUARDARE; da un documento si prende COSA AFFERMARE.**

Nessun dato che finisca in un elaborato si cita dal registro: si rilegge dalla pagina che il
registro indica, e si cita quella.

Vale in particolare per i **numeri**. Un valore dimensionale, una quantita', un importo, una data
che si confronta con una soglia di legge: si rileggono dall'atto. *Un errore di soglia nasce da un
numero preso di seconda mano.*

> Misurato il 10 settembre 2026 su Caltagirone: un lettore aveva dato per errato il protocollo di
> un'autorizzazione paesaggistica. Era giusto — aveva letto il numero dell'istanza. Chi avesse
> corretto l'atto sulla parola della scheda avrebbe introdotto l'errore, non tolto.

### 🔴 2 — Una scheda che si dichiara illeggibile non e' una lettura

**Non dichiarare alcun documento «illeggibile» o «non disponibile» prima di averlo letto.**

Un documento il cui testo non si estrae non e' un documento perduto: e' un documento **da
OCRizzare**. La formula ammessa e' *«non risulta dal testo estratto»*, che descrive lo strumento;
*«non citabile»* qualifica l'atto, ed e' vietata.

Gli estratti con `origine: ocr` o su file marcati `OCR_POVERO` sono citabili ma **il virgolettato
va riscontrato sull'originale prima della firma**, e va detto nella relazione.

> Movente (commessa Cava Luserta): due allegati furono catalogati «illeggibili» e contenevano il
> materiale piu' rilevante dell'intero dossier — 139 e 260 pagine. Erano soltanto non OCRizzati.

### 🔴 3 — Il 100% degli atti non e' il 100% delle pagine

`copertura.py stato` stampa **due misure**, e vanno lette entrambe:

```
COPERTURA DI LETTURA: 781/781 = 100.0%  (documenti)
COPERTURA IN PAGINE : 3155/16402 = 19.2%  <- quanto fascicolo e' stato guardato
```

Un atto risulta «letto» anche se ne sono state aperte 3 pagine su 123. **La prima riga dice quanti
atti sono stati aperti; la seconda dice quanta carta e' stata letta.**

La lettura mirata e' tecnica corretta — nessuno legge 123 pagine di studio idraulico per ricavarne
una portata. Ma **chi scrive deve sapere quante pagine sono rimaste fuori**, e chi legge la
relazione anche: la tabella di copertura va in testa, non in appendice.

Se accanto alla percentuale compare **`(MINIMO)`**, alcune letture parziali non dichiarano le
pagine e li' contano zero: la copertura vera e' piu' alta di quel numero e non e' calcolabile.

### 🔴 4 — Una lettura parziale non provata e' un'affermazione, non un dato

Una `PARZIALE` la cui motivazione sostiene che il resto sta altrove — *«riproduce…»*, *«gia'
letto»*, *«struttura standard gia' riscontrata»*, *«ripetitivo»* — sta facendo un'**affermazione
sul contenuto delle pagine che non ha letto**.

Se il campo `riproduce` e' **assente**, quell'affermazione **non e' mai stata verificata**.

```
parziali_confronto.py "<cartella>" --rassegna
```

elenca tutte quelle in questo stato. Finche' non sono provate, **non si puo' concludere nulla su
quelle pagine**, e in particolare non si puo' scrivere che un fatto «non risulta agli atti».

> Misurato l'11 settembre 2026 su Caltagirone: **40 letture parziali su 175** affermavano una
> riproduzione mai verificata, per **2.803 pagine**. Il caso a monte e' il D.D.G. 3/2024, dato
> per copia di un parere gia' letto: le 21 pagine saltate contenevano due pareri CTS che non
> esistono in nessun altro punto del fascicolo.

### 🔴 5 — Un rimando «id NNN» dentro una nota e' un riferimento pendente

Gli id del registro **cambiano a ogni ricensimento**. Un id scritto in prosa dentro una
motivazione resta indietro, in silenzio, e continua a sembrare valido.

**Prima di seguire un rimando `id NNN`, risolverlo e guardare su cosa cade davvero.**

> Misurato l'11 settembre 2026: cinque relazioni di calcolo rimandavano a «POD1 (id 678)». Dopo un
> ricensimento l'id 678 era la Relazione Tecnico Agronomica; POD1 era diventato il 687. Gli id
> erano slittati di +9 e tutti e cinque i rimandi erano sbagliati.

E' anche il motivo per cui il campo `riproduce` contiene un **percorso** e non un id: un percorso
sopravvive a un ricensimento.

---

## 5. Comandi

```bash
copertura.py stato   "<cartella>"          # esce 1 se l'analisi non e' completa
copertura.py report  "<cartella>"          # la tabella da mettere in testa alla relazione
copertura.py da-leggere "<cartella>"       # cosa manca
parziali_confronto.py "<cartella>" --rassegna   # le affermazioni non provate
```

---

## 6. Quando l'inventario NON c'e'

Si procede come prima — censimento proprio, `commessa-rag`, catalogazione — **dichiarandolo**:
un'analisi senza inventario forense non ha superato nessuno dei tre cancelli, e la relazione deve
dirlo. Non e' un divieto: e' un'avvertenza che deve arrivare a chi legge.
