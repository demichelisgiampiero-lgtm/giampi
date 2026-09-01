# Diario di lavoro — commessa SPA / ex Cava Ventrone

Registro cronologico delle sessioni, delle decisioni e del metodo emerso.
Serve a due scopi: continuità fra sessioni (il container è effimero, la memoria
non persiste) e materiale grezzo per la trasformazione in skill.

---

## Sessione 1 — 11 agosto / 1 settembre 2026

### Cronologia

| # | Attività | Esito |
|---|---|---|
| 1 | Ricognizione SPA sul portale VIA-VAS Regione Campania | **Bloccata** — egress di rete chiuso (403 al CONNECT). Individuati per via di ricerca 5 URL di SPA pubblici |
| 2 | Griglia normativa dell'Allegato IV-bis + checklist Allegato V | `struttura-spa.md` |
| 3 | Analisi SPA Mugnano del Cardinale 2018 (94 pp., PDF nativo) | `analisi-cava-mugnano-2018.md` |
| 4 | Revisione bozza SPA ex Cava Ventrone v17 (456 par., 46 tab.) | `revisione-ex-cava-ventrone-2026.md` — 6 rilievi sostanziali, 7 formali |
| 5 | Riscontro Relazione Tecnica Generale rivista | `relazione-generale-ventrone-riscontro.md` — 3 discordanze chiuse, 8 aperte, 1 peggiorata |
| 6 | Riscrittura cap. 9 in regime esclusivo di sottoprodotto | `.docx` modificato + `cap9-riscritto-testo.md` |
| 7 | Riscontro del cap. 9 sul D.P.R. 120/2017 (scansione, via OCR) | Riferimenti numerati; rilevata la questione abrogativa |

### Decisioni prese

- **Terminologia.** «SPA» designa due documenti distinti: Studio *Preliminare*
  Ambientale (art. 19, screening) e Studio di *Prefattibilità* Ambientale (ex
  art. 20 DPR 207/2010). La commessa riguarda il primo.
- **Nessuna modifica allo SPA.** A oggi lo SPA v17 è archiviato intatto; gli
  interventi sono stati fatti sulla sola Relazione generale, e su copia.
- **Colonna A non derogabile** per le CSC, ancorata all'art. 20 co. 1 D.P.R.
  120/2017 (destinazione urbanistica del sito di destinazione).
- **Criterio più restrittivo della norma** sui riporti antropici: esclusi del
  tutto, a fronte del 20% ammesso dall'art. 4 co. 3, per la collocazione del
  sito nel Piano Regionale di Bonifica.

### Questioni aperte

1. **Vigenza del D.P.R. 120/2017.** Il testo consolidato reca l'AGGIORNAMENTO (1):
   il D.L. 24 febbraio 2023, n. 13, art. 48 comma 3, ne dispone l'abrogazione *a
   partire dalla data di entrata in vigore del decreto di cui al comma 1* del
   medesimo D.L. Da verificare se quel decreto sia entrato in vigore: l'intero
   impianto del cap. 9 e dell'Appendice B.1 dello SPA vi si fonda.
2. **Termine annuale di utilizzo** (art. 21 co. 1): le partite da cantieri di
   piccole dimensioni vanno utilizzate entro un anno dalla produzione, salvo
   termine di esecuzione superiore dell'opera. I conferimenti durano ~15,8 mesi.
3. Le dodici modifiche allo SPA elencate in `relazione-generale-ventrone-riscontro.md`
   § 7 e in `revisione-ex-cava-ventrone-2026.md` § 4.

### Vincoli d'ambiente appresi

- **Egress chiuso** verso qualunque dominio non allowlistato (`regione.campania.it`,
  `example.com`). Un solo ambiente configurato, "Default — trusted network access";
  la policy si cambia solo da claude.ai/code → Environments, e si applica
  all'avvio del container.
- **PyPI e i repository APT sono invece raggiungibili**: `pip install` funziona
  (pdfplumber, python-docx, pypdfium2, defusedxml) e `apt-get install
  tesseract-ocr` pure. È la via per procurarsi strumenti mancanti.
- **LibreOffice non converte** in questo ambiente (`source file could not be
  loaded`, anche su file integri): niente rendering PDF dei .docx, quindi niente
  controllo visivo. Validare via `validate.py` e confronto paragrafo per paragrafo.
- **poppler/pdftoppm assenti**: per leggere un PDF scansionato, rasterizzare con
  `pypdfium2` e poi OCR con `tesseract -l ita --psm 6`.
- **La memoria non persiste** fra sessioni e il repo viene clonato fresco: ciò
  che serve alla sessione successiva va committato.

---

## Metodo emerso — candidato a diventare skill

Il procedimento si è stabilizzato in cinque passi ricorrenti, applicati due
volte (Mugnano 2018, Ventrone 2026) con esiti coerenti.

### Passo 1 — Classificare il documento prima di leggerlo

Distinguere Studio Preliminare Ambientale, Studio di Prefattibilità Ambientale,
Studio di Impatto Ambientale, Studio di Incidenza, Piano di Monitoraggio
Ambientale. Il nome del file mente: `SPACAS009_PMA_R02.pdf` è un Piano di
Monitoraggio, non uno SPA.

### Passo 2 — Misurare le proporzioni

Contare pagine, paragrafi e tabelle per capitolo. Nell'esemplare 2018 lo
screening occupava 7 pagine su 94: il rapporto ha rivelato che il documento era
uno studio di incidenza con un cappello di screening, prima ancora di leggerne
il merito.

### Passo 3 — Riscontrare sulla griglia, non sull'impressione

Allegato IV-bis per i contenuti, Allegato V per i criteri. Per ciascuna voce:
presente / parziale / assente. La ricerca testuale distingue il trattamento reale
dalla citazione di stile — se «cumulo» ricorre dieci volte e tutte nella
descrizione della metodologia, il cumulo non è stato valutato.

### Passo 4 — Verificare l'aritmetica e le citazioni

Far quadrare i numeri fra loro (volumi ÷ viaggi = capacità automezzo; conferimenti
× giorni = totale) e controllare la vigenza delle norme citate rispetto alla data
di redazione. Nell'esemplare 2018: art. 20 citato nel 2018, quando il D.Lgs.
104/2017 l'aveva già sostituito con l'art. 19.

### Passo 5 — Incrociare gli elaborati

I vizi peggiori stanno fra i documenti, non dentro. Lo SPA Ventrone assume il
sottoprodotto come regime esclusivo; la Relazione firmata lo qualificava come
eventuale. Nessuno dei due documenti, letto da solo, mostra il problema.

### Regola trasversale

**Cita o taci.** Ogni riferimento normativo o si riscontra sulla fonte o si
marca `[DA VERIFICARE]` con l'indicazione della fonte da consultare. La
convenzione è quella che lo SPA Ventrone già adotta ed è la ragione per cui è
un buon documento.
