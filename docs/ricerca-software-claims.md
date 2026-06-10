# Ricerca di mercato — software per riserve/claims negli appalti

Verifica dei software, in Italia e all'estero, che svolgono (in tutto o in
parte) il lavoro della skill **Ufficio Riserve**: analizzare la documentazione
di un appalto di opere civili e costruire/gestire le riserve dell'appaltatore e
i claims. Per ciascuno: cosa fa, cosa possiamo imparare.

> Nota: nessuno strumento sul mercato fa esattamente ciò che fa la skill
> (analisi documentale automatica → redazione di riserve inattaccabili). I
> prodotti coprono **pezzi** del processo: contabilità lavori (IT),
> document/claim control e delay analysis (estero). La skill può integrarne le
> idee migliori.

---

## A. Italia — contabilità lavori e gestione riserve

In Italia il presidio è normativo (D.Lgs. 36/2023, Allegato II.14). I software
di **contabilità lavori** generano gli atti dove le riserve vivono (registro di
contabilità, SAL, libretto misure) ma **non costruiscono la riserva**: lasciano
all'utente il contenuto giuridico.

| Software | Casa | Cosa fa | Spunti per noi |
|---|---|---|---|
| **Pitagora / Contabilità** | Blumatica | Contabilità lavori, registro di contabilità, SAL, gestione riserve come record contabile, conformità All. II.14 | Strutturare la riserva come **record collegato all'atto contabile e alla data** (tempestività tracciata dal software) |
| **PriMus / contabilità** | ACCA software | Computo, contabilità, SAL, libretto misure | Collegamento **misure↔SAL↔importi**: base per il quantum tracciabile |
| **STR Vision CPM** | TeamSystem/STR | Contabilità e gestione commessa, controllo costi | **Controllo costi di commessa** = base dati per i maggiori oneri |
| **Namirial / contabilità** | Namirial | Contabilità lavori e atti | Dematerializzazione e **firma/protocollo** degli atti |

**Lezione dall'Italia**: il valore aggiunto della nostra skill non è
contabilizzare (lo fanno già), ma **qualificare giuridicamente** il fatto,
**verificare la decadenza** e **redigere** la riserva blindata — area scoperta
da questi gestionali.

---

## B. Estero — claims, delay analysis, document control

All'estero il mercato è maturo su **claim management**, **delay/disruption** e
**document control**, dove c'è molto da imparare sul metodo probatorio.

| Software / metodo | Origine | Cosa fa | Spunti per noi |
|---|---|---|---|
| **Primavera P6** (Oracle) | USA | Schedulazione, baseline, as-planned vs as-built | Motore della **delay analysis** (Fase 6): confronto programma vs reale |
| **Microsoft Project** | USA | Schedulazione di progetto | Baseline e windows analysis per i ritardi |
| **SCL Delay & Disruption Protocol** | UK (metodo) | Standard su ritardi e improduttività | **Contemporaneous records**, metodi di delay, *measured mile* |
| **AACE 29R-03 / RP claim** | USA (metodo) | Forensic schedule analysis, change/claim | Struttura **entitlement→causation→quantum**, scelta del metodo |
| **FIDIC suite** | Internazionale (contratto) | Clausole claim con notice/particulars/DAAB | **Notice tempestiva a pena di decadenza**, organo di dispute avoidance (≈ CCT) |
| **Document control / claim platforms** | varie | Registro protocolli, correlazione evento↔documento, audit trail | **Correlazione automatica** fatto↔documento↔data per il dossier probatorio |

**Lezione dall'estero**: il claim si vince con **prova contemporanea** e
**metodo dichiarato** (delay/disruption). Importiamo il rigore
*entitlement→causation→quantum* e la disciplina dei *contemporaneous records*.

---

## C. Software affini (gestione attività venatoria) — NON pertinenti

Durante una prima ricerca su "riserve" erano emersi software per la **gestione
delle riserve di caccia** (TosCaccia, Dafne Caccia, XCaccia, Infocaccia,
HuntScrape, HuntStand, HAMS, DeerMapper). **Dominio diverso**: registrati qui
solo per chiarire che NON sono concorrenti della skill (riguardano tesserini e
capi abbattuti, non i claims d'appalto).

---

## D. Conclusioni operative per l'upgrade della skill

1. **Posizionamento unico**: nessun prodotto fa analisi documentale →
   redazione di riserve. È il nostro vantaggio: presidiamo la parte
   **giuridico-redazionale** che i gestionali italiani non coprono.
2. **Da importare dall'Italia**: collegamento riserva ↔ atto contabile ↔ data
   (tempestività verificabile), quantum tracciabile dalle misure.
3. **Da importare dall'estero**: contemporaneous records, struttura
   entitlement→causation→quantum, metodi di delay/disruption dichiarati,
   document control con audit trail.
4. **Tradotto nel workflow**: già recepito nelle Fasi 1 (document control),
   4 (decadenze), 5-6 (quantum e delay), 7-8 (redazione + checklist). Vedi
   `.claude/skills/ufficio-riserve/reference/best-practice-internazionali.md`.

## Fonti
- Riserve nel D.Lgs. 36/2023 — guide e dottrina:
  [Studio Moscarini](https://www.studiomoscarini.it/2025/07/18/riserve-negli-appalti-pubblici-guida-dlgs-36-2023/),
  [ANCE AIES Salerno](https://www.anceaies.it/dl-36-2023_-le-riserve-nel-nuovo-codice-dei-contratti-pubblici/),
  [FareAppalti](https://www.fareappalti.it/2023/05/11/d-lgs-36-2023-le-riserve-dellappaltatore/),
  [Avvocato di cantiere — 12 regole](https://avvocatodicantiere.it/le-12-regole-generali-in-materia-di-riserve-nel-codice-36-2023/),
  [Appalti e Contratti](https://www.appaltiecontratti.it/note-sulla-disciplina-delle-riserve-nel-codice-dei-contratti-pubblici/),
  [LavoriPubblici](https://www.lavoripubblici.it/news/lavori-pubblici-iscrizione-riserve-atti-contabili-28119).
- Contabilità/SAL: [BibLus ACCA — SAL](https://biblus.acca.it/stato-avanzamento-lavori/),
  [Ingenio — SAL guida](https://www.ingenio-web.it/articoli/stato-avanzamento-lavori-s-a-l-guida-pratica-alla-contabilita-lavori-per-tecnici-e-imprese/),
  [Codice Appalti — art. 115](https://www.codiceappalti.it/DLGS_36_2023/Articolo_115__Controllo_tecnico_contabile_e_amministrativo_/12736).
- Claims/estero: [SCL Protocol — delay & disruption (panoramica)](https://www.lexology.com/library/detail.aspx?g=e26df642-6112-459b-bb38-f452b7a8164d),
  [Global Arbitration Review — delay & quantum](https://globalarbitrationreview.com/guide/the-guide-construction-arbitration/fifth-edition/article/delays-in-quantum-and-financial-methods-computing-costs-and-damages),
  [Equitas — claims & delay experts](https://www.equitas-consulting.com/).
