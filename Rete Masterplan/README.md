# Rete Masterplan — Cartella di lavoro

Raccolta ordinata del lavoro sulla Rete Masterplan: atti, normativa, analisi, gare e fascicolo di
qualificazione. Aggiornata al 15 settembre 2026.

## Struttura

| Cartella | Contenuto |
|---|---|
| `00_Atti_costitutivi/` | Contratto istitutivo di rete e documenti societari. `DA_ACQUISIRE.md` elenca quello che manca al fascicolo. |
| `01_Normativa/` | Ricognizione delle fonti europee e nazionali sulle reti di società di ingegneria negli appalti. |
| `02_Relazioni_e_analisi/` | Relazioni per le riunioni della Rete e analisi applicate al caso Masterplan. |
| `03_Gare/` | Documentazione di gara, verifiche dei requisiti, istanze di chiarimento. |
| `04_Qualificazione_Rete/` | Fascicolo permanente di qualificazione. `CHECKLIST.md` traccia lo stato dei requisiti. |
| `99_Script/` | Script che generano i documenti Word. Servono solo a rigenerarli, non contengono contenuti. |

## Documenti prodotti

**`01_Normativa/Quadro_Normativo_Reti_Ingegneria_Appalti.docx`**
Ricognizione delle fonti: direttive 2014/23, 2014/24 e 2014/25/UE e principio di neutralità della
forma giuridica; giurisprudenza della Corte di giustizia (C-631/21 Taxi Horn Tours, C-642/20
Caruter); riconoscimento delle qualifiche professionali; regolamento (UE) 2022/2560 sulle
sovvenzioni estere; disciplina nazionale del contratto di rete; artt. 65, 66 e 68 del D.Lgs.
36/2023 e Allegato II.12; Bando tipo ANAC n. 2/2026; giurisprudenza nazionale; checklist dei
criteri di partecipazione alle gare italiane; questioni aperte e argomenti difensivi.
La dimensione internazionale è rinviata a una seconda ricognizione.

**`02_Relazioni_e_analisi/Relazione_Requisiti_Gare_SIA_Rete_Masterplan.docx`**
Relazione per la riunione della Rete: quadro normativo applicato, censimento dei bandi delle
maggiori stazioni appaltanti, gap analysis del contratto sottoscritto (17 rilievi) e roadmap per
attrezzare la Rete a concorrere in proprio ai servizi di architettura e ingegneria.

## I tre punti aperti

1. **Direttore tecnico della Rete — assente.** Requisito dell'art. 37 dell'Allegato II.12, necessario
   perché l'ente-rete si qualifichi come soggetto ex art. 66, comma 1, lett. e). Va deliberato in
   assemblea.
2. **Presidente e primo Vice Presidente non figurano fra i componenti dell'Organo Comune**, mentre
   l'art. 17 del contratto li vuole nominati al suo interno. Incide sulla legittimazione di chi
   sottoscrive l'offerta.
3. **Oggetto e codice ATECO iscritti** da verificare sulla visura, per la coerenza con i servizi di
   architettura e ingegneria richiesta dai disciplinari anche all'ente-rete.

## Avvertenza

I documenti sono di lavoro interno e non costituiscono pareri legali. Norme, sentenze e dati dei
bandi sono stati riscontrati su fonti secondarie e vanno riverificati sulle fonti ufficiali prima
di qualunque uso esterno.

## Rigenerare i documenti Word

```bash
cd 99_Script
npm install
node build.js "../02_Relazioni_e_analisi/Relazione_Requisiti_Gare_SIA_Rete_Masterplan.docx"
node build_normativa.js "../01_Normativa/Quadro_Normativo_Reti_Ingegneria_Appalti.docx"
```
