# Valutazione Recall e diagnosi della ricerca documentale di commessa

**Data:** 11 settembre 2026
**Branch:** `claude/recall-software-evaluation-llmvtv`
**Scopo:** documento di passaggio di consegne. Raccoglie la valutazione del software Recall e,
soprattutto, la diagnosi dei problemi di precisione della ricerca sugli atti di commessa, con il
piano di intervento. Da leggere prima della sessione di lavoro al PC.

---

## AVVERTENZA IMPORTANTE SULLA PORTATA DI QUESTA DIAGNOSI

L'analisi qui sotto è stata condotta su **`commessa-rag` v2**, la versione sincronizzata nel
cloud. La versione effettivamente in uso sul PC — chiamata **`commessa-forense`** — **non è stata
esaminata**: non è sincronizzata e non era accessibile dalla sessione remota.

Alcune delle debolezze elencate potrebbero quindi essere **già state risolte** in
`commessa-forense`. La prima cosa da fare al PC è confrontare i due motori, prima di intervenire.

---

## 0. In sintesi

1. **Recall: scartato.** È una knowledge base per studio personale, non dà citazione
   `fonte:pagina` verificabile. Resta valido per normativa e preparazione Envision.
2. **Il problema di precisione non è il motore di ricerca.** È lo **strato di estrazione a monte**:
   il RAG non può trovare ciò che non è mai stato estratto.
3. **Causa numero uno:** i PDF scansionati senza OCR hanno testo estratto **zero**. Sono
   invisibili al motore. Nessun reranker, nessun embedding, nessun thesaurus li recupera.
4. **Quattro debolezze verificate nel codice** di `commessa-rag` (sezione 2).
5. **Piano in quattro mosse**, ordinate per impatto (sezione 6).
6. **dtSearch valutato** (sezione 4-bis): ottimo strumento, ma **non fa OCR** — non risolve
   la causa principale. ~249 USD perpetui per il Desktop.

---

## 1. Recall (recall.it) — valutazione ed esito

**Cos'è:** app di Recall Wiki, Inc. ("Save, Summarize, Chat"). Knowledge base personale che salva
e riassume articoli, video YouTube, podcast, PDF e note, con knowledge graph automatico.
Disponibile su web, iOS, Android ed estensioni browser.

**Dati tecnici rilevati:**

| Aspetto | Dato |
|---|---|
| Integrazione con Claude | **Sì**, tramite server MCP (sola lettura, scope `kb:read`, 4 strumenti) |
| Piano richiesto per MCP/API | **Solo Max**: ~38 $/mese annuale (~456 $/anno), 48 $/mese mensile |
| Dove stanno i dati | Local-first sul dispositivo; backup e sync su Google Cloud **Belgio** (europe-west1) |
| Limite upload PDF | 100 MB |
| Import massivo | Fino a 10.000 file markdown |

**Esito: NON adatto al lavoro forense di commessa.**

- Non produce citazione `fonte:pagina` verificabile: restituisce "card" a chunk deduplicati.
- Riassume, e su un capitolato o una perizia il riassunto è esattamente ciò che non è utilizzabile
  come fonte.
- Non indicizza cartelle locali e non legge Excel: i CME restano fuori.
- L'MCP è in sola lettura, quindi non è nemmeno un archivio su cui scrivere.

**Dove invece ha senso:** normativa, linee guida ANAC, sentenze, dottrina, articoli e video
tecnici, e in particolare la **preparazione della certificazione Envision** (riassunti, flashcard,
quiz, ripetizione spaziata). Per questo uso il piano gratuito o Plus basta: il Max non serve
finché non si vuole far leggere la base a Claude.

---

## 2. Diagnosi di `commessa-rag` — cosa funziona e cosa no

### 2.1 Cosa NON va buttato

L'impianto forense è solido e **non esiste prodotto commerciale equivalente**:

- citazione `fonte:pagina` con verifica;
- cancello di consegna `verify` sui virgolettati (`rag.py:1831`), con esiti
  `OK` / `APPROSSIMATO` / `DA CORREGGERE` / `SENZA_CITAZIONE` ed exit code 1 in `--strict`;
- regola "cita o taci";
- `gate` che blocca l'analisi finché il corpus non è pronto;
- eval harness con recall@k, precision@k, MRR e nDCG@k (`rag.py:1482`);
- ricerca a scaletta (frase esatta → AND → AND espanso → OR) con fusione RRF multi-query;
- `timeline` per la cronologia degli atti.

NotebookLM, ChatPDF e Humata non sono difendibili in giudizio. Harvey, Luminance e Kira sono
enterprise, cloud e tarati sul common law. **Sostituire il motore significherebbe perdere proprio
la parte che vale.**

### 2.2 Le quattro debolezze (verificate nel codice)

**A. Estrazione PDF che distrugge le tabelle** — `rag.py:221`, `extract_pdf_native()`

Usa `pdfplumber.extract_text()` con fallback su `pypdf`. Entrambi **linearizzano** la pagina: le
tabelle diventano testo corrente e le colonne si mescolano. Su CME, SAL e computi — dove la
precisione è numerica (voce, quantità, prezzo unitario, importo) — è il punto di rottura.

**B. Estrazione Excel appiattita** — `rag.py:258`, `extract_xlsx()`

Ogni riga diventa `" | ".join(cells)`. Si perdono intestazioni, gerarchia delle voci, celle unite
e struttura delle colonne. Aggravante: per XLSX, DOCX, EML, MSG e TXT **l'intero file vale come
"pagina 1"**, quindi la citazione `CME.xlsx:1` da sola non localizza nulla.

**C. Chunking a lunghezza fissa** — `rag.py:126-127`

```
CHUNK_TARGET  = 900   # caratteri
CHUNK_OVERLAP = 150
```

Taglio cieco a 900 caratteri: spezza a metà le voci di computo e gli articoli di capitolato.
Per documenti strutturati serve un chunking **strutturale** (per articolo, per voce), non metrico.

**D. Nessun reranker vero**

Quello che la skill chiama "rerank" (FASE B, punto 3 di `SKILL.md`) è il modello che rilegge i
candidati. Non c'è **cross-encoder** nel codice. È tipicamente l'intervento con il miglior
rapporto tra sforzo e precisione guadagnata, e manca.

### 2.3 Due leve già presenti ma probabilmente spente

**Thesaurus sottodimensionato** — `scripts/thesaurus.json` contiene **38 gruppi di termini**.
Per un lessico di appalti e contenzioso è pochissimo. La skill stessa dichiara che aggiornarlo è
*"il modo più diretto e auditabile per alzare la recall"*.

**Layer denso opzionale e da attivare a mano** — richiede `pip install fastembed`, le variabili
`RAG_EMBED_BACKEND` / `RAG_EMBED_MODEL` e il comando `embed` (`rag.py:1068`). Senza, la ricerca è
**solo per parole chiave**. Su linguaggio giuridico-tecnico italiano, dove lo stesso concetto si
scrive in cinque modi diversi, la differenza è sostanziale.

> **Da verificare al PC:** se `embed` non è mai stato lanciato, questa singola omissione spiega
> una fetta importante dei documenti persi.

---

## 3. La causa principale: i documenti a testo zero

I PDF scansionati **senza OCR** risultano in stato `needs_ocr`: testo estratto **zero**.
`commessa-rag` delega esplicitamente l'OCR a monte ("OCR esterno, es. ABBYY FineReader").

Non sono documenti ordinati male in coda ai risultati: **non esistono per il motore**. Questo
spiega da solo il sintomo "perde documenti e informazioni", e spiega perché migliorare la ricerca
non ha prodotto effetti — il problema è a monte.

**Primo comando da lanciare al PC:**

```bash
python3 "<percorso>/rag.py" gate --folder "<CARTELLA-COMMESSA>"
```

Il numero di file in `needs_ocr` è la quota di commessa oggi invisibile. Da annotare: è la
baseline dell'intervento.

Da guardare anche gli altri due elenchi restituiti dal `gate`:
- `file_con_testo_ocr` — citabili, ma il virgolettato va verificato sull'originale;
- `file_a_paginazione_logica` — la "pagina" è un blocco, va citato anche il campo `posizione`.

---

## 4. Lo strato mancante: parsing documentale moderno

L'estrazione di `commessa-rag` è di generazione 2022. Nel 2026 layout, OCR e riconoscimento
tabelle sono confluiti in modelli vision-language, ed è lì che sta il salto di precisione.

| Strumento | Dove vince | Dati | Note |
|---|---|---|---|
| **Docling** (IBM, open source) | **Struttura tabellare: il migliore.** Modello TableFormer dedicato: righe, colonne, celle unite, intestazioni | 97,9% su DocLayNet (IBM Research); 50,3% su olmOCR-bench a 2,1 pag/s | Il pezzo giusto per **CME, computi, SAL**. Ha anche una pipeline VLM (`granite-docling-258M`) |
| **Marker 2** (datalab, motore Surya 2) | **OCR generale: il migliore.** 90+ lingue, batte Tesseract sulla gran parte dei benchmark | 76,0% su olmOCR-bench, 83,5% sui PDF nativi, 2,9 pag/s su GPU B200 | Il pezzo giusto per le **scansioni**. Vuole GPU per andare veloce |
| **OCRmyPDF + Tesseract** | Gratis, leggero, batch, gira ovunque | — | La via rapida per azzerare i `needs_ocr` fin da subito |
| **pdfmux** | Tabelle, in crescita | 0,911 TEDS contro 0,887 di Docling (maggio 2026) | Da tenere d'occhio |

Tutti girano **in locale**: gli atti non escono dalla macchina e il principio forense della skill
resta intatto.

**Alternative cloud** (Azure Document Intelligence, Mistral OCR, LlamaParse): più forti su alcune
tabelle, ma i documenti escono dalla macchina. **Non consigliate su documentazione di contenzioso**,
anche a fronte di disponibilità dichiarata all'uso del cloud.

---

## 4-bis. dtSearch — valutazione

**Cos'è:** motore di full-text retrieval commerciale, standard de facto in eDiscovery e computer
forensics. Indicizza terabyte, oltre 25 modalità di ricerca (booleana, di prossimità, fuzzy,
fonetica, regex, sinonimi, intervalli numerici), parser propri per centinaia di formati.
Gira **in locale** su Windows.

**Punto di forza reale per il contenzioso:** evidenzia gli hit **dentro il documento originale**
con il riferimento di pagina. Per il riscontro manuale di un virgolettato è ottimo.

### LIMITE DECISIVO: dtSearch non fa OCR

Verificato sulla documentazione di supporto dtSearch: raccomanda di passare le scansioni a un OCR
esterno (citano Acrobat) e si limita a **identificare i PDF immagine come "da OCR-izzare"**.

È **lo stesso identico comportamento** dello stato `needs_ocr` di `commessa-rag`. Su un corpus con
scansioni non trattate, dtSearch trova esattamente quanto si trova oggi: **la causa principale dei
documenti persi resta intatta**.

### Corrispondenza con i sintomi rilevati

| Sintomo | Risolto da dtSearch? |
|---|---|
| Atti non trovati — scansioni senza OCR | **No.** Stesso limite |
| Atti non trovati — sinonimi e formulazioni diverse | **In parte.** Fuzzy, fonetica e anelli di sinonimi: stessa famiglia di soluzione del thesaurus già presente. Nessun embedding, nessuna ricerca semantica |
| Errori su numeri e tabelle (CME) | **No.** Indicizza testo: la struttura voce/quantità/prezzo/importo si perde ugualmente |
| Troppi risultati irrilevanti | **In parte.** La ricerca di prossimità aiuta; manca il reranking semantico |
| Citazione verificata | **Diversamente.** Nessun cancello `verify` sui virgolettati, ma l'evidenziazione nell'originale è ottima per il controllo manuale |

**Non è un RAG.** Non sintetizza, non redige, non si integra con Claude (l'unica via sarebbe
l'SDK Engine, a partire da 12.500 USD). È uno strumento di **istruttoria manuale**, complementare
al motore esistente, non sostitutivo.

### Prezzi

> Rilevati da rivenditori e listini indicizzati: `dtsearch.com` era bloccato dal proxy di rete.
> **Da riverificare sul sito prima dell'acquisto.**

| Prodotto | Prezzo | Note |
|---|---|---|
| **Desktop, utente singolo** | **~249 USD** | Licenza **perpetua**; una persona, fino a 2 computer |
| Licenza annuale "investigative" | non verificato | Dedicata a forensics ed eDiscovery |
| Network | da ~200 USD/postazione (5-24) a 55 USD/postazione (20.000+) | |
| Engine (SDK) | minimo **12.500 USD** per 25 server | Unica via per l'integrazione in un programma |

### Conclusione

A **249 USD perpetui** è un acquisto difendibile come strumento di istruttoria manuale su corpus
grandi: software serio, con trent'anni di storia, e la cifra è modesta.

**Ma non risolve il problema di precisione diagnosticato.** L'ordine corretto resta:

> **L'OCR viene prima di qualunque motore di ricerca.** Che sia `commessa-rag`,
> `commessa-forense` o dtSearch, un PDF immagine senza OCR è testo zero per tutti e tre.

Quindi: **prima l'OCR** (OCRmyPDF, gratuito), **poi** misurare quanto problema residuo resta.
Se dopo l'OCR la ricerca funziona, l'acquisto è evitato. Se non funziona, dtSearch si valuta
sapendo esattamente cosa si sta comprando.

---

## 5. Il reranker

Per il sintomo "troppi risultati irrilevanti" serve un **cross-encoder** in coda al recupero:

- **`bge-reranker-v2-m3`** — locale, multilingue, buone prestazioni sull'italiano.
- Alternative cloud: Cohere Rerank, Jina Reranker (i testi escono: sconsigliate sul contenzioso).

Schema: recupero ampio (`--k 30`) → il cross-encoder riordina → si tengono i 5 migliori.

---

## 6. Piano di intervento, ordinato per impatto

| # | Intervento | Sintomo che risolve | Sforzo |
|---|---|---|---|
| 1 | **OCR su tutti i `needs_ocr`** (OCRmyPDF come primo passo, Marker 2 per la qualità) | "Non trova atti che ci sono" | Basso, ma richiede tempo macchina |
| 2 | **Attivare il layer denso** (`fastembed` + `embed`), se spento | Recall bassa, sinonimi non colti | Molto basso |
| 3 | **Docling per PDF tabellari ed Excel**, con chunking strutturale per voce | "Sbaglia su numeri e tabelle"; citazione imprecisa | Medio-alto: tocca l'ingest |
| 4 | **Cross-encoder in coda alla ricerca** | "Troppi risultati irrilevanti" | Medio |
| 5 | **Ampliare `thesaurus.json`** oltre i 38 gruppi attuali | Recall bassa | Basso, incrementale |

L'ordine non è arbitrario: gli interventi 1 e 2 sono a basso costo e agiscono sulla causa
principale. Gli interventi 3 e 4 vanno affrontati **dopo** aver misurato la baseline, altrimenti
non si distingue il miglioramento dal rumore.

---

## 7. Metodo: misurare, non indovinare

I sintomi riportati sono **quattro insieme** (documenti mancanti, errori su tabelle, citazioni
imprecise, risultati irrilevanti). Con quadri così ampi, procedere a intuito porta a girare a
vuoto. Il motore ha già l'eval harness: va usato.

```bash
# 1) generare il modello di golden set
python3 "$SCRIPT" eval --template golden.json --folder "<CARTELLA>"

# 2) baseline PRIMA di qualunque modifica
python3 "$SCRIPT" eval --folder "<CARTELLA>" --golden golden.json --k 8

# 3) confronto senza thesaurus e senza stemming (per isolare il contributo)
python3 "$SCRIPT" eval --folder "<CARTELLA>" --golden golden.json --k 8 --no-thesaurus --no-stem
```

**Regola:** una modifica si accetta solo se recall@k, precision@k, MRR e nDCG@k **non peggiorano**.

Il golden set va costruito sui casi reali: query effettivamente usate in commessa, con le
`file:pagina` che dovrebbero uscire. Una ventina di casi ben scelti valgono più di cento generici.

---

## 8. Da preparare per la sessione al PC

1. **Output del `gate`** su una commessa vera, con il conteggio dei `needs_ocr`.
2. **Percorso di `commessa-forense`** e di una cartella di commessa rappresentativa (PDF nativi,
   scansioni, CME, Word insieme).
3. **Verificare se `embed` è mai stato lanciato** (esiste un indice denso?).
4. **Un caso di fallimento concreto e ripetibile**: un documento che si sa essere agli atti, la
   query usata, e la conferma che non esce. **Questo vale più di tutto il resto messo insieme**:
   da un caso riproducibile si risale alla causa in mezz'ora.

## 9. Domande aperte

- `commessa-forense` quali delle quattro debolezze ha già risolto?
- Quanti file sono in `needs_ocr`, in percentuale sul corpus?
- Le scansioni già OCR-izzate con quale motore sono state trattate? (se l'OCR è scadente, il testo
  è corrotto e la ricerca fallisce anche se formalmente il testo "c'è")
- C'è una GPU disponibile sul PC? Determina se Marker 2 è praticabile o se conviene OCRmyPDF.

---

## 10. Fonti

- [Marker 2 vs MinerU, Docling e Liteparse — benchmark](https://www.marktechpost.com/2026/07/24/datalab-marker-v2-vs-mineru-docling-and-liteparse-benchmark-breakdown/)
- [PDF parsing per RAG 2026: MinerU vs Docling vs Marker](https://builderai.tools/blog/pdf-parsing-for-rag-mineru-docling-marker-compared)
- [Benchmark accuratezza parsing: Docling vs Unstructured](https://www.ertas.ai/blog/pdf-parsing-accuracy-benchmark-docling-unstructured)
- [Marker su GitHub](https://github.com/datalab-to/marker)
- [Migliori strumenti OCR open source 2026](https://unstract.com/blog/best-opensource-ocr-tools/)
- [dtSearch — come usare l'output OCR con i prodotti dtSearch](https://support.dtsearch.com/faq/dts0167.htm)
- [dtSearch — funzionalità per la forensics](https://www.dtsearch.com/PLF_forensics_2.html)
- [dtSearch — store e listino](https://www.dtsearch.com/dtStore.html)
- [dtSearch Desktop, licenza singolo utente (rivenditore)](https://www.provantage.com/dtsearch-desktop~7DTSO177.htm)
- [Recall — prezzi](https://www.recall.it/pricing)
- [Recall — documentazione MCP](https://docs.recall.it/developer/mcp)
- [Recall su Google Play](https://play.google.com/store/apps/details?id=com.recall.wiki)
