# Workflow di costruzione — Software generatore AUA (Regione Campania)

> **Scopo di questo documento.** È il piano di lavoro completo e autosufficiente
> per costruire un software che, a partire dai dati di un cliente raccolti tramite
> una checklist, rediga una pratica **AUA — Autorizzazione Unica Ambientale**
> (DPR 13 marzo 2013, n. 59) pronta per la presentazione al SUAP in Regione Campania.
>
> **Come si usa domani.** Apri questa cartella in **Claude Code desktop** e segui
> la **Sezione 9 (Piano di build)**: ogni fase ha un prompt già pronto da incollare.
> Le fasi sono ordinate; eseguile in sequenza. Alla fine avrai uno script funzionante
> e, se vuoi, un eseguibile `.exe` autonomo.

---

## 1. Obiettivo

Realizzare un **MVP a riga di comando** (script Python + template editabili) che:

1. riceva in input una **checklist compilata** dal cliente (file `YAML`);
2. determini automaticamente **quali titoli ambientali** devono confluire nell'AUA;
3. generi i **documenti Word editabili** della pratica (Modello Unico + relazioni tecniche);
4. produca una **checklist degli allegati** e dei controlli finali prima dell'invio al SUAP.

L'obiettivo NON è sostituire il tecnico, ma **azzerare il lavoro ripetitivo** di
compilazione e produrre una bozza coerente e completa da rifinire.

---

## 2. Inquadramento normativo (sintesi operativa)

**AUA — DPR 59/2013.** Titolo unico che, su domanda, **sostituisce e coordina**
fino a 7 atti di comunicazione, notifica e autorizzazione in materia ambientale.
Si rivolge a PMI e a impianti **non soggetti ad AIA**. Durata: **15 anni**.

**Presentazione.** L'istanza si presenta in via telematica al **SUAP** (Sportello
Unico Attività Produttive) del Comune, che la trasmette all'**autorità competente**.
In Campania l'autorità competente al rilascio è di norma la **Provincia / Città
Metropolitana di Napoli**; il SUAP resta l'unico punto di accesso.

**I 7 titoli sostituibili (art. 3 DPR 59/2013):**

| Cod. | Titolo | Riferimento |
|------|--------|-------------|
| A | Autorizzazione agli scarichi di acque reflue | art. 124 D.Lgs. 152/2006 |
| B | Comunicazione per l'utilizzazione agronomica di effluenti, acque di vegetazione, acque reflue | art. 112 D.Lgs. 152/2006 |
| C | Autorizzazione alle emissioni in atmosfera (in via ordinaria) | art. 269 D.Lgs. 152/2006 |
| D | Autorizzazione di carattere generale alle emissioni in atmosfera | art. 272 c. 2 D.Lgs. 152/2006 |
| E | Comunicazione/documentazione di impatto acustico | L. 447/1995 |
| F | Autorizzazione all'utilizzo dei fanghi di depurazione in agricoltura | D.Lgs. 99/1992 |
| G | Comunicazioni per il recupero di rifiuti in procedura semplificata | artt. 215-216 D.Lgs. 152/2006 |

> ⚠️ **Modulistica.** Il "Modello Unico AUA" e gli allegati sono adottati a livello
> nazionale e recepiti/adattati a livello regionale. Prima della presentazione
> reale **va sempre verificata la modulistica AUA vigente** pubblicata da Regione
> Campania / Provincia competente / portale SUAP, perché numeri di protocollo,
> allegati e dettagli possono variare. I template di questo software sono **scheletri
> professionali con segnaposto**, non moduli ufficiali.

---

## 3. Ambito dell'MVP

Titoli **implementati subito** (i più frequenti per attività edili/produttive/estrattive):

- **C / D — Emissioni in atmosfera** (art. 269 ordinaria oppure art. 272 c. 2 generale)
- **A — Scarichi di acque reflue** (art. 124)
- **G — Recupero rifiuti in procedura semplificata** (artt. 215-216)

Titoli **rilevati ma non ancora generati** (il software segnala che servono, con
rinvio a sviluppo successivo): **B, E, F**.

---

## 4. Architettura

```
checklist.yaml ──▶ intake (lettura+validazione) ──▶ dati
                                                      │
                                                      ▼
                                          applicabilità (motore di regole)
                                                      │
                              ┌───────────────────────┼───────────────────────┐
                              ▼                        ▼                       ▼
                     elenco titoli AUA        template .md.j2           checklist allegati
                              │                  (Jinja2)                       │
                              └──────────────▶ render (Markdown→DOCX) ◀─────────┘
                                                      │
                                                      ▼
                                        pacchetto/ (file .docx editabili)
```

**Principi:**
- **Contenuto separato dal codice.** Il testo legale/tecnico sta in template
  `*.md.j2` (Markdown + Jinja2), modificabili dal tecnico senza toccare il codice.
- **Output editabile.** Si generano `.docx` (Word), non PDF: il tecnico rifinisce.
- **Deterministico e versionabile.** Stesso input → stesso output.

**Stack:** Python 3.11+, `python-docx`, `Jinja2`, `PyYAML`. Packaging opzionale
in `.exe` con `PyInstaller`.

---

## 5. Struttura del repository

```
giampi/
├── WORKFLOW_AUA.md              # questo documento (la guida)
├── README.md                    # istruzioni d'uso sintetiche
├── requirements.txt             # ✅ FATTO (Fase 0)
├── aua/
│   ├── __init__.py              # ✅ FATTO (Fase 0)
│   ├── intake.py                # ✅ FATTO (Fase 0) — lettura/validazione checklist
│   ├── applicability.py         # ⬜ DA FARE (Fase 2) — motore di regole
│   ├── render.py                # ⬜ DA FARE (Fase 3) — Markdown→DOCX + Jinja2
│   ├── cli.py                   # ⬜ DA FARE (Fase 4) — entrypoint a riga di comando
│   └── templates/
│       ├── modello_unico_aua.md.j2     # ⬜ DA FARE (Fase 3)
│       ├── relazione_emissioni.md.j2   # ⬜ DA FARE (Fase 3)
│       ├── relazione_scarichi.md.j2    # ⬜ DA FARE (Fase 3)
│       └── relazione_rifiuti.md.j2     # ⬜ DA FARE (Fase 3)
├── checklist/
│   ├── checklist_AUA.yaml              # ⬜ DA FARE (Fase 1) — modello da compilare
│   └── Checklist_AUA_Cliente.md        # ⬜ DA FARE (Fase 1) — versione leggibile per il cliente
├── examples/
│   └── esempio_officina_meccanica.yaml # ⬜ DA FARE (Fase 1) — esempio compilato per i test
└── output/                             # cartella di destinazione dei pacchetti generati
```

---

## 6. Modello dati — schema della checklist (`checklist_AUA.yaml`)

Schema completo che la Fase 1 deve realizzare. I commenti guidano la compilazione.

```yaml
# ============ ANAGRAFICA GESTORE ============
gestore:
  ragione_sociale: ""            # OBBLIGATORIO
  forma_giuridica: ""            # es. S.r.l., S.p.A., ditta individuale
  codice_fiscale: ""             # OBBLIGATORIO
  partita_iva: ""
  sede_legale:                   # OBBLIGATORIO
    indirizzo: ""
    comune: ""
    provincia: ""                # sigla, es. CE
    cap: ""
  legale_rappresentante:
    nome: ""
    cognome: ""
    codice_fiscale: ""
    pec: ""                      # necessaria per invio SUAP
  referente_tecnico:
    nome: ""
    cognome: ""
    email: ""
    telefono: ""

# ============ IMPIANTO / INSEDIAMENTO ============
impianto:
  denominazione: ""              # OBBLIGATORIO
  indirizzo: ""
  comune: ""                     # OBBLIGATORIO
  provincia: ""                  # OBBLIGATORIO — atteso: AV/BN/CE/NA/SA
  cap: ""
  foglio: ""                     # dati catastali
  particella: ""
  codice_ateco: ""
  descrizione_attivita: ""       # descrizione sintetica del ciclo produttivo
  superficie_mq:                 # numero
  numero_addetti:                # numero

# ============ TITOLO C/D — EMISSIONI IN ATMOSFERA ============
emissioni_atmosfera:
  presenti: false                # true se ci sono emissioni in atmosfera
  regime: ""                     # "ordinaria" (art.269) | "generale" (art.272 c.2)
  attivita_in_deroga: ""         # se generale: attività dell'Allegato (parte II) richiamato dall'art.272
  punti_emissione:               # elenco dei punti
    - sigla: ""                  # es. E1
      provenienza: ""            # fase/macchinario
      inquinanti: []             # es. [polveri, COV]
      portata_nmc_h:             # numero
      altezza_m:                 # numero
      impianto_abbattimento: ""  # es. filtro a maniche / nessuno

# ============ TITOLO A — SCARICHI DI ACQUE REFLUE ============
scarichi:
  presenti: false
  tipologie: []                  # tra: industriali, domestiche, meteoriche_dilavamento
  recapito: ""                   # "fognatura" | "acque_superficiali" | "suolo"
  corpo_recettore: ""            # denominazione del corpo idrico / gestore fognatura
  portata_mc_anno:               # numero
  presenza_sostanze_pericolose: false   # tab.3/A o 5 All.5 Parte III
  punti_scarico:
    - sigla: ""                  # es. S1
      origine: ""                # processo che genera il refluo
      trattamento: ""            # es. fossa Imhoff / disoleatore / depuratore

# ============ TITOLO G — RECUPERO RIFIUTI (PROCEDURA SEMPLIFICATA) ============
rifiuti_recupero:
  presente: false
  pericolosita: ""               # "non_pericolosi" (DM 5/2/1998) | "pericolosi" (DM 161/2002)
  operazioni: []                 # codici R: es. [R3, R4, R5, R13]
  codici_eer: []                 # es. ["170504", "170302"]
  quantita_annua_t:              # numero (t/anno)
  messa_in_riserva_R13: false    # true se previsto stoccaggio R13

# ============ ALTRI TITOLI (solo rilevazione nell'MVP) ============
altri_titoli:
  utilizzo_agronomico_effluenti: false   # Titolo B (art.112)
  impatto_acustico: false                # Titolo E (L.447/1995)
  fanghi_in_agricoltura: false           # Titolo F (D.Lgs.99/1992)
```

---

## 7. Motore di applicabilità — regole

`applicability.py` valuta i flag della checklist e produce, per ciascun titolo,
un esito: `applicabile` (sì/no), `implementato` (template disponibile?), `motivazione`.

| Cod. | Titolo | Condizione di applicabilità | Implementato |
|------|--------|------------------------------|:------------:|
| A | Scarichi acque reflue | `scarichi.presenti == true` | ✅ |
| B | Utilizzazione agronomica | `altri_titoli.utilizzo_agronomico_effluenti == true` | ❌ |
| C | Emissioni — ordinaria | `emissioni_atmosfera.presenti` e `regime == "ordinaria"` | ✅ |
| D | Emissioni — generale | `emissioni_atmosfera.presenti` e `regime == "generale"` | ✅ |
| E | Impatto acustico | `altri_titoli.impatto_acustico == true` | ❌ |
| F | Fanghi in agricoltura | `altri_titoli.fanghi_in_agricoltura == true` | ❌ |
| G | Recupero rifiuti semplificato | `rifiuti_recupero.presente == true` | ✅ |

**Output del motore:** una lista ordinata di esiti + un riepilogo testuale
("Titoli da includere nell'AUA: A, C, G — di cui generati: A, C, G").
Per i titoli `applicabile == true` ma `implementato == false`, la generazione
deve **avvisare** chiaramente che il relativo allegato va prodotto a parte.

---

## 8. Template documentali

Ogni template è un file `*.md.j2`: **Markdown** (titoli `#`, tabelle `|`, elenchi
`-`, grassetto `**`) con segnaposto **Jinja2** (`{{ gestore.ragione_sociale }}`,
`{% if ... %}`). Il `render.py` li trasforma in `.docx`.

**8.1 `modello_unico_aua.md.j2`** — l'istanza AUA. Contiene:
- intestazione al SUAP del Comune competente;
- dati del gestore e del legale rappresentante;
- dati dell'impianto/insediamento (ubicazione, catasto, ATECO, attività);
- **elenco dei titoli richiesti** (generato dal motore di applicabilità);
- dichiarazioni sostitutive (DPR 445/2000), bollo, durata 15 anni;
- spazio firma digitale del legale rappresentante.

**8.2 `relazione_emissioni.md.j2`** — relazione tecnica emissioni: descrizione
del ciclo, tabella dei punti di emissione (sigla, provenienza, inquinanti, portata,
altezza, abbattimento), regime (ordinaria/generale) e valori limite di riferimento.

**8.3 `relazione_scarichi.md.j2`** — relazione tecnica scarichi: tipologia reflui,
schema di trattamento, recapito e corpo recettore, tabella punti di scarico,
richiamo ai limiti della Tab. 3 All. 5 Parte III D.Lgs. 152/2006.

**8.4 `relazione_rifiuti.md.j2`** — relazione recupero rifiuti: codici EER,
operazioni R, quantità annue, eventuale messa in riserva R13, richiamo al
DM 5/2/1998 (non pericolosi) o DM 161/2002 (pericolosi).

Tutti i template devono usare **segnaposto evidenti** del tipo
`[DA COMPLETARE: ...]` dove il dato non è in checklist, così la bozza segnala
da sé cosa manca.

---

## 9. Piano di build (fasi/prompt per domani in Claude Code desktop)

> Esegui le fasi **in ordine**. Dopo ogni fase, lancia la verifica indicata.
> I prompt sono pensati per essere incollati così come sono.

### Fase 0 — Setup (già fatto)
`requirements.txt`, `aua/__init__.py`, `aua/intake.py` sono già nel repo.
Crea l'ambiente e installa le dipendenze:
```
python -m venv .venv
.venv\Scripts\activate          # Windows  (su Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

### Fase 1 — Checklist ed esempio
**Prompt da incollare:**
> «Leggi `WORKFLOW_AUA.md` sezione 6. Crea `checklist/checklist_AUA.yaml` esattamente
> con quello schema e quei commenti (vuoto, da compilare). Crea poi
> `checklist/Checklist_AUA_Cliente.md`, versione leggibile della stessa checklist
> pensata per il cliente, raggruppata per sezioni con spiegazioni in linguaggio
> semplice. Infine crea `examples/esempio_officina_meccanica.yaml`: lo stesso schema
> ma **compilato** con un caso realistico di officina meccanica con cabina di
> verniciatura (emissioni regime generale art.272, scarichi domestici in fognatura,
> recupero rifiuti non pericolosi R13/R4 su rottami metallici).»

**Verifica:** `python -c "import yaml,glob; [yaml.safe_load(open(f)) for f in glob.glob('checklist/*.yaml')+glob.glob('examples/*.yaml')]"` non dà errori.

### Fase 2 — Motore di applicabilità
**Prompt:**
> «Crea `aua/applicability.py` secondo la sezione 7 di `WORKFLOW_AUA.md`. Definisci
> il catalogo dei 7 titoli (codice, nome, riferimento normativo, implementato) e una
> funzione `valuta_applicabilita(dati: dict) -> list[dict]` che applica le regole
> della tabella e restituisce per ogni titolo `{codice, nome, riferimento, applicabile,
> implementato, motivazione}`. Aggiungi `riepilogo(esiti) -> str`. Solo logica pura,
> nessun I/O.»

**Verifica:** `python -c "from aua.applicability import valuta_applicabilita; print(valuta_applicabilita({'scarichi':{'presenti':True}}))"`.

### Fase 3 — Render e template
**Prompt:**
> «Crea `aua/render.py` con: (1) un mini-convertitore `markdown_to_docx(testo, percorso)`
> basato su `python-docx` che gestisce titoli `#`/`##`/`###`, paragrafi, elenchi `-`,
> tabelle `|...|` (saltando la riga separatrice `|---|`) e grassetto inline `**...**`;
> (2) `renderizza_template(nome_template, contesto) -> str` con Jinja2 (loader sulla
> cartella `aua/templates`). Poi crea i 4 template `*.md.j2` descritti nella sezione 8,
> con contenuti professionali e segnaposto `[DA COMPLETARE: ...]`.»

**Verifica:** rendering di un template con un contesto fittizio produce un `.docx` apribile.

### Fase 4 — CLI e orchestrazione
**Prompt:**
> «Crea `aua/cli.py` con `argparse` e due comandi:
> `applicabilita <checklist.yaml>` (stampa il riepilogo dei titoli) e
> `genera <checklist.yaml> -o <cartella>` che: carica e valida la checklist (intake),
> valuta l'applicabilità, renderizza il Modello Unico e le relazioni dei soli titoli
> applicabili+implementati, converte tutto in `.docx` dentro la cartella di output,
> scrive un `Checklist_Allegati.md` con l'elenco dei documenti prodotti, dei titoli
> applicabili non ancora implementati e dei `[DA COMPLETARE]` residui. Stampa a video
> avvisi e percorso del pacchetto. Aggiungi il blocco `if __name__ == '__main__'`.»

**Verifica (test end-to-end):**
```
python -m aua.cli genera examples/esempio_officina_meccanica.yaml -o output/test
```
Devono comparire i `.docx` in `output/test/` e nessuna eccezione.

### Fase 5 — README e rifinitura
**Prompt:**
> «Aggiorna `README.md` con: descrizione, installazione, come compilare la checklist,
> come lanciare `genera`, dove trovare l'output, e il disclaimer legale (sezione 13 del
> workflow). Aggiungi `output/` a `.gitignore`.»

### Fase 6 (opzionale) — Eseguibile autonomo
Per distribuire senza installare Python:
```
pip install pyinstaller
pyinstaller --onefile --name aua-campania --add-data "aua/templates;aua/templates" aua/cli.py
```
(su Mac/Linux il separatore in `--add-data` è `:` invece di `;`).
L'eseguibile finisce in `dist/`.

---

## 10. Esecuzione e packaging — riepilogo comandi

```bash
# generazione pacchetto AUA da una checklist compilata
python -m aua.cli genera percorso/della/checklist.yaml -o output/cliente_x

# solo verifica di quali titoli servono
python -m aua.cli applicabilita percorso/della/checklist.yaml
```

---

## 11. Test e validazione

- **Test del motore:** casi con 0, 1 e più titoli attivi → esiti attesi.
- **Test end-to-end:** l'esempio officina genera 4 file (Modello Unico + 3 relazioni)
  senza eccezioni e i `.docx` si aprono in Word.
- **Controllo qualità documenti:** ogni `[DA COMPLETARE]` residuo deve finire nella
  `Checklist_Allegati.md` per non sfuggire al tecnico.

---

## 12. Roadmap estensioni (dopo l'MVP)

1. Titoli **B, E, F** (template + regole già predisposte).
2. Allegati cartografici/planimetrie e gestione marche da bollo.
3. **Modulo web** (form guidato con campi condizionali) sopra lo stesso motore.
4. Esportazione **PDF/A** e fascicolo unico firmabile.
5. Pre-compilazione da **visura camerale** e da banche dati ATECO.

---

## 13. Avvertenze legali

Questo software produce **bozze tecniche** a supporto del professionista. Non
costituisce parere legale né garantisce la conformità alla modulistica vigente.
Prima di ogni presentazione reale al SUAP è onere del tecnico incaricato:
- verificare la **modulistica AUA aggiornata** di Regione Campania / Provincia competente;
- validare valori limite, allegati obbligatori, bolli e dichiarazioni;
- assumersi la responsabilità tecnica dei contenuti.
