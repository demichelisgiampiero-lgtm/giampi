# SPA di screening — Regione Campania (portale VIA-VAS)

Raccolta di **Studi Preliminari Ambientali** (art. 19 D.Lgs. 152/2006, verifica
di assoggettabilità a VIA) estratti dal portale VIA-VAS della Regione Campania,
da esaminare e usare come esempio.

## Stato

| Passo | Stato |
|---|---|
| Individuazione fonti sul portale VIA-VAS | fatto (vedi sotto) |
| Griglia normativa di lettura | fatto → [`struttura-spa.md`](struttura-spa.md) |
| Primo esemplare acquisito | fatto (caricamento manuale) → `esempi/` |
| Analisi critica del primo esemplare | fatto → [`analisi-cava-mugnano-2018.md`](analisi-cava-mugnano-2018.md) |
| Download degli altri PDF dal portale | **bloccato** — egress di rete chiuso |

## Esemplari

| File | Oggetto | Analisi |
|---|---|---|
| `esempi/19881843-Studio_preliminare_ambientale_1.pdf` | Cava di sabbia in loc. Pianaiello, Mugnano del Cardinale (AV) — screening integrato da Valutazione di Incidenza (SIC IT8040017 "Pietra Maula"), 94 pp., 2018 | [`analisi-cava-mugnano-2018.md`](analisi-cava-mugnano-2018.md) |
| `esempi/SPA_ExCavaVentrone_art19_20260806_v17_BOZZA.docx` | Ex Cava Ventrone, San Felice a Cancello (CE) — recupero ambientale mediante ritombamento, screening ex art. 19 integrato da VIncA (ZSC IT8040006), bozza di lavoro 2026 | [`revisione-ex-cava-ventrone-2026.md`](revisione-ex-cava-ventrone-2026.md) |

### Perché il download è bloccato

L'ambiente di esecuzione applica una network policy di livello *Trusted*: il
proxy risponde `403` al CONNECT verso qualunque host non pre-allowlistato,
inclusi i domini della Regione Campania.

```
viavas.regione.campania.it:443 → gateway answered 403 to CONNECT (policy denial)
www.regione.campania.it:443    → gateway answered 403 to CONNECT (policy denial)
```

**Sblocco:** in claude.ai/code → Environments → ambiente in uso → *Network
access* → livello **Custom**, aggiungendo `viavas.regione.campania.it`,
`www.regione.campania.it`, `servizi-digitali.regione.campania.it`. La policy
viene applicata all'avvio del container, quindi occorre **avviare una sessione
nuova** dopo il salvataggio.

In alternativa: scaricare i PDF manualmente e allegarli alla sessione.

## Fonti da scaricare

Documenti pubblici già individuati sul portale, con URL diretto:

- `.../allegati/Rizzotto/8264/Studio_preliminare_ambientale.pdf`
- `.../allegati/Rizzotto/8263/ALLEGATO_7-STUDIO_PRELIMINARE_AMBIENTALE.pdf`
- `.../allegati/Rizzotto/8722/STUDIO_PRELIMINARE_AMBIENTALE.pdf`
- `.../allegati/D_Alterio/8180/V00_STUDIO_PRELIMINARE_AMBIENTALE.pdf`
- `.../allegati/D_Alterio/8238/Studio_Preliminare_Ambientale_Integrato.pdf`

Prefisso comune:
`https://viavas.regione.campania.it/opencms/export/sites/default/VIAVAS/download/`

Portali di riferimento:

- Home VIA-VAS — <https://viavas.regione.campania.it/opencms/opencms/VIAVAS>
- Area VIA — <https://viavas.regione.campania.it/opencms/opencms/VIAVAS/VIA>
- Modulistica — <https://viavas.regione.campania.it/opencms/opencms/VIAVAS/Modulistica>
- Istanze digitali VIA — <https://servizi-digitali.regione.campania.it/via>

I PDF scaricati vanno collocati in `docs/spa-screening/esempi/`.

## Avvertenza terminologica

**SPA** designa due documenti distinti, da non confondere:

- **Studio Preliminare Ambientale** — art. 19 D.Lgs. 152/2006, contenuti da
  Allegato IV-bis. È il documento dello *screening*, ed è quello trattato qui.
- **Studio di Prefattibilità Ambientale** — ex art. 20 DPR 207/2010, elaborato
  del progetto preliminare, oggi assorbito nel PFTE. Si reperisce negli atti di
  gara, non sul portale VIA-VAS.
