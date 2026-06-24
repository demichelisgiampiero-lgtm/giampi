# Generatore AUA — Regione Campania

Software (MVP a riga di comando) che, a partire da una **checklist compilata dal
cliente**, redige una bozza di pratica **AUA — Autorizzazione Unica Ambientale**
(DPR 59/2013) pronta da rifinire e presentare al SUAP.

## 👉 Punto di partenza

**Tutto il piano di lavoro è in [`WORKFLOW_AUA.md`](./WORKFLOW_AUA.md).**
È un documento autosufficiente: aprilo in Claude Code desktop e segui la
**Sezione 9 (Piano di build)**, fase per fase, fino ad avere il software funzionante.

## Stato attuale

- ✅ **Fase 0 (setup)**: `requirements.txt`, `aua/__init__.py`, `aua/intake.py`
- ⬜ Fasi 1–6: da eseguire domani seguendo il workflow

## Ambito MVP

Titoli AUA generati subito: **emissioni in atmosfera** (art. 269/272),
**scarichi di acque reflue** (art. 124), **recupero rifiuti in procedura
semplificata** (artt. 215-216). Gli altri titoli (B, E, F) vengono rilevati e
segnalati per lo sviluppo successivo.

## Uso previsto (al termine del build)

```bash
# quali titoli servono per questo cliente?
python -m aua.cli applicabilita checklist/checklist_AUA.yaml

# genera il pacchetto Word della pratica
python -m aua.cli genera checklist/checklist_AUA.yaml -o output/cliente_x
```

## ⚠️ Avvertenza

Produce **bozze tecniche** a supporto del professionista. Prima della presentazione
reale va sempre verificata la modulistica AUA vigente di Regione Campania / Provincia
competente. Vedi Sezione 13 del workflow.
