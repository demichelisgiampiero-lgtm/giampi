# Handoff — stato del lavoro al 2 settembre 2026

Documento di passaggio di consegne. È scritto per **una sessione che non sa
nulla** di come è nato questo progetto: contiene lo stato, le decisioni prese e
il perché, cosa è verificato e cosa no, e cosa conviene fare dopo.

- **Repository:** `https://github.com/demichelisgiampiero-lgtm/giampi`
- **Branch:** `claude/read-all-files-folders-lvlsi0`
- **Progetto del workflow, consultabile:** https://claude.ai/code/artifact/b24781fe-f9c3-4bd2-9644-289afd494fc4

---

## Da dove nasce

L'utente ha segnalato un problema ricorrente: chiedendo di *«analizzare tutti i
documenti nella cartella e nelle sottocartelle»*, l'analisi risultava
incompleta — alcuni file non venivano letti, **senza che nulla lo segnalasse**.

La diagnosi è che l'esplorazione è discrezionale: si aprono i file che dal nome
sembrano rilevanti e ci si ferma quando si ritiene di aver capito abbastanza.
Non esiste un momento in cui qualcuno conta i documenti presenti e verifica che
il numero letto coincida. Il guasto è silenzioso: non produce un errore, produce
una relazione che **sembra** finita.

Il rimedio non è un prompt più insistente. È togliere la discrezionalità con
controlli automatici che si oppongono alla consegna.

---

## Come ripartire domani

```bash
git clone -b claude/read-all-files-folders-lvlsi0 \
  https://github.com/demichelisgiampiero-lgtm/giampi.git
cd giampi
python3 plugins/commessa-forense/scripts/ricognizione.py
```

La ricognizione dice cosa manca sulla macchina e stampa i comandi di
installazione giusti per Windows, macOS o Linux. **Esce con codice 1** finché
qualcosa di bloccante non è risolto.

Poi, per eseguire un'analisi: apri Claude Code nella cartella del repository e
digli *«Segui `WORKFLOW.md` sulla cartella `<percorso della commessa>`»*.

Per continuare lo sviluppo: leggi prima questo file, poi `WORKFLOW.md`.

---

## Mappa dei file

### Il plugin — è questo che si usa

| File | Cosa fa |
|---|---|
| `plugins/commessa-forense/scripts/ricognizione.py` | Verifica l'ambiente prima di cominciare. Le librerie di `rag.py` non le cerca su disco: **prova a importarle davvero** in un processo separato, perché una libreria con estensioni native mal compilate è presente e fallisce comunque all'uso. |
| `plugins/commessa-forense/scripts/integrita.py` | Controlla ogni PDF **pagina per pagina**, passa all'OCR le scansioni scrivendo un PDF ricercabile *accanto* all'originale, e **misura la resa dell'OCR** sulla quota di parole italiane riconosciute. |
| `plugins/commessa-forense/scripts/copertura.py` | Censimento e cancello. Fa quadrare tre numeri: documenti **censiti**, **indicizzati**, **letti uno per uno**. |
| `plugins/commessa-forense/scripts/qualita.py` | Controllo di qualità sulla lettura: cerca nel documento ogni dato dichiarato nelle schede, e sceglie chi rileggere a campione. |
| `plugins/commessa-forense/agents/*.md` | Tre agenti: acquisizione, lettura (parallelizzabile), verifica di consegna. |
| `plugins/commessa-forense/skills/analisi-commessa/SKILL.md` | L'orchestratore. |
| `WORKFLOW.md` | Le istruzioni operative complete, autosufficienti. |

### Superata, ma ancora nel repo

`.claude/skills/inventario-documenti/` è la **prima versione**, poi superata
quando si è deciso di orchestrare `commessa-rag` invece di duplicarlo.

Attenzione però: **contiene ancora qualcosa che il plugin non ha.** Il suo
`scripts/estrai.py` (798 righe) ha l'integrazione con **Docling** e i lettori
per `.docx`/`.xlsx`/`.eml` in libreria standard. Il plugin cerca Docling nella
ricognizione ma **nessuno script del plugin lo usa**: il lavoro su Docling è di
fatto orfano.

Va deciso: recuperare la parte Docling dentro `integrita.py`, oppure cancellare
la vecchia skill. Lasciare due catene di estrazione contraddice la decisione
presa (vedi sotto) e prima o poi produce due verità sullo stesso documento.

---

## Le decisioni prese, e perché

**Orchestrare le skill esistenti, non inglobarle.** `commessa-rag`, `cme-claims`
e `cme-plugin` restano installate e aggiornabili per conto loro. Il motivo non è
la comodità: `commessa-rag` produce **citazioni**, e una copia congelata
finirebbe prima o poi per indicizzare lo stesso fascicolo in modo diverso,
dando due citazioni `file:pagina` divergenti sullo stesso atto. In un contenzioso
due verità sono un problema, non una ridondanza. Per lo stesso motivo è stato
scartato l'ibrido con copia interna di riserva.

**Ridurre il nostro codice a ciò che manca agli altri.** Estrazione e indice li
fa `rag.py`, che è collaudato. Restano nostri solo l'integrità pagina per pagina
e i controlli sulla lettura.

**Tre cancelli, che presidiano guasti diversi.** Non avere il documento; non
averlo guardato; aver scritto cose che non ci sono. Nessuno copre gli altri.

**Tutto in locale.** Gli atti di un contenzioso non escono dalla macchina. Vale
anche per l'OCR: niente servizi cloud, benché più accurati.

**Solo strumenti gratuiti** per l'OCR (scelta dell'utente): `ocrmypdf` /
`tesseract`, con la misura di resa a segnalare i pochi documenti da riprendere a
mano.

---

## Cosa è verificato e cosa no

Questa tabella è la parte più importante del documento. **Non dare per buono
ciò che è nella colonna di destra.**

| Verificato eseguendo | Mai eseguito |
|---|---|
| Il **PDF misto** passa il cancello di `rag.py`: registro di 5 pagine con 2 scansionate → `status='indexed'`, chunk ricercabili solo su `[1,2,5]`. Provato due volte: sulla funzione `index_pdf` isolata e poi end-to-end su un fascicolo ben formato. | **L'OCR.** Sulla macchina di sviluppo non c'era alcun motore installato: tutto il percorso che produce il PDF ricercabile è scritto e mai eseguito. È la parte più importante e la meno provata. |
| La **misura di qualità dell'OCR** separa 63% (prosa italiana vera) da 6% (stessa pagina mal riconosciuta). Soglia a 12%. | **Docling** con il pacchetto vero: non si installava (guasto di build su `antlr4`). Provato solo contro un'imitazione della sua interfaccia. |
| Il **riconoscimento del formato dai byte**: un `.xls` che è un `.xlsx` viene letto lo stesso e la discrepanza segnalata. | **Il plugin come plugin.** Mai caricato con `claude --plugin-dir`. Gli agenti non hanno mai girato, né in sequenza né in parallelo. |
| Il **controllo di qualità** su errori piantati apposta: riconosciuti un importo inventato, una data sbagliata e una scheda generica, senza falsi allarmi. | **Una commessa reale.** Tutto è stato provato su un fascicolo sintetico costruito da me. |
| Le **intestazioni Word non entrano nell'indice**: `extract_docx` di `rag.py` legge paragrafi e tabelle, non header e footer — dove stanno protocollo e data. `Prot. 4471 del 14/03/2024` è nel file e assente dall'indice. | Il **cancello 3** (`verify` sui virgolettati) su una bozza vera. |

---

## Tre errori che ho commesso, perché non si ripetano

**1. Ho costruito prima di far approvare il progetto.** L'utente aveva detto
«possiamo *pensare* a un plugin»; sono passato a costruirlo saltando la
validazione del workflow. Il documento di progetto è arrivato dopo, e contiene
nove decisioni che sono ancora mie assunzioni.

**2. Il banco di prova sintetico mi ha ingannato due volte.**
I PDF che generavo avevano la tabella `xref` troncata: `pdfplumber` li rifiutava
e io ho attribuito la cosa a *librerie mancanti*, sbagliando diagnosi e
scrivendola nel documento. Poi i `.docx` sintetici dichiaravano content-type
errati e `python-docx` li rifiutava: seconda diagnosi sbagliata. Entrambi
riparati, ma **i file finti sono rotti in modi in cui i file veri non lo sono**.
Non fidarsi del corpus sintetico per conclusioni sugli strumenti.

**3. Ho parlato di `commessa-rag` prima di leggerlo.** Ho costruito un cancello
di copertura senza accorgermi che `rag.py` ne aveva già uno (`gate`,
`needs_ocr`, `attest`). Metà del primo lavoro era ridondante. **Leggere gli
strumenti esistenti prima di scrivere codice.**

---

## Le nove decisioni che aspettano l'utente

Sono nel documento consultabile, ciascuna con la proposta attuale. In sintesi:

1. **Perimetro** — oltre ~300 documenti, perimetro ristretto concordato?
2. **Soglia OCR** — 12% di parole italiane riconosciute: giusta? blocca o segnala?
3. **Lettura mirata** — oltre ~80 pagine si legge in modo mirato: soglia giusta?
4. **Esclusioni** — le decide sempre l'utente, o sopra un certo numero d'ufficio?
5. **Duplicati** — stesso contenuto in due cartelle: un documento o due?
6. **Versioni** — chi stabilisce quale `Capitolato_revN` è il contrattuale?
7. **PDF da OCR** — accanto all'originale o in sottocartella separata?
8. **Quota di rilettura** — oggi 15% più i segnalati e i primi 5 per importo.
9. **Dati fuori indice** — bloccano la consegna o solo segnalano? (oggi: segnalano)

Finché non risponde, valgono le proposte, che sono scritte in `WORKFLOW.md`
nella tabella «Convenzioni adottate».

---

## Prossimi passi, in ordine

1. **Ricognizione sul PC** e installazione di quello che manca. Senza OCR il
   flusso è monco su qualsiasi fascicolo reale.
2. **Prima esecuzione su una commessa vera**, possibilmente piccola. È il primo
   test che conta davvero: tutto il resto è stato provato su file finti.
   Aspettarsi che qualcosa si rompa, e raccogliere l'errore invece di aggirarlo.
3. **Decidere sulla skill superata**: recuperare Docling dentro `integrita.py`
   oppure cancellare `.claude/skills/inventario-documenti/`.
4. **Rispondere alle nove decisioni** e allineare `WORKFLOW.md`.
5. **Le intestazioni Word**: valutare se estenderle nell'indice, dato che
   protocollo e data sono riferimenti su cui si fondano le affermazioni.

---

## Nota di metodo per chi riprende

Il senso di questo lavoro è che gli strumenti **si oppongano alla fretta di
consegnare**. Se un cancello non passa, il rimedio non è aggirarlo: è capire
perché e dirlo all'utente. Un'analisi dichiarata incompleta è onesta; una
dichiarata completa e non lo è, in un contenzioso, è un danno.
