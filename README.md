# 📒 Giornale dei Lavori

Web app per la gestione del **giornale dei lavori** di cantiere, predisposta
**per l'impresa**. Segue il flusso reale della contabilità di cantiere:

```
Progetto esecutivo + CME + Contratto/CSA
        │
        ▼
SCHEDE DI CANTIERE   ── voci di computo (codice, UM, quantità di progetto, prezzo)
        │
        ▼  (compilate giornalmente dal personale di cantiere)
GIORNALIERE          ── meteo, maestranze, mezzi, materiali + QUANTITÀ ESEGUITE per voce
        │
        ▼  (raccolte e raggruppate)
CONTABILITÀ          ── avanzamento per voce e totali
        │
        ▼  (in base a Contratto + CSA)
SAL                  ── importo progressivo e % di avanzamento
```

## Funzionalità (v1)

- **Cantieri / commesse**: dati di appalto (committente, importo contrattuale,
  riferimenti a contratto e Capitolato Speciale d'Appalto, date).
- **Schede di cantiere (CME)**: voci di computo con codice, descrizione,
  categoria, unità di misura, quantità di progetto e prezzo unitario.
  Inserimento **manuale** oppure **import da CSV** (anche in formato Excel
  italiano: separatore `;` e virgola decimale).
- **Giornaliere**: registrazione per data con meteo, temperatura, maestranze,
  mezzi, materiali, note e **righe di avanzamento** (quantità eseguita
  agganciata alle voci CME).
- **Contabilità e SAL**: riepilogo per voce (quantità eseguita, % avanzamento,
  importo eseguito, residuo) e **calcolo dello Stato Avanzamento Lavori** —
  importo progressivo e percentuale rispetto al contratto, con filtro
  "SAL alla data".

> Non ancora incluso (fase 2): workflow di approvazione della Direzione Lavori
> (stati bozza → inviato → approvato), export PDF, gestione utenti.

## Requisiti

- **Node.js >= 22.5** (usa il modulo integrato `node:sqlite`, nessuna
  dipendenza nativa da compilare).

## App desktop per Windows (consigliata)

L'app è disponibile come **vero programma desktop** (Electron): un'icona sul
Desktop, finestra propria, nessun browser e nessun comando. I dati restano
salvati sul PC e l'installer include già tutto (anche Node.js).

- **Per gli utenti:** scarica l'installer `Giornale dei Lavori Setup x.y.z.exe`
  e installalo. Vedi la guida **[`GUIDA-WINDOWS.md`](GUIDA-WINDOWS.md)**.
  L'installer viene compilato automaticamente da GitHub Actions
  (workflow *Build app desktop Windows*): lo trovi tra gli **Artifacts** della
  run, oppure tra gli allegati di una **Release** se è stato creato un tag `vX.Y.Z`.
- **Per chi sviluppa:**
  ```bash
  npm install
  npm run electron     # avvia l'app desktop in locale
  npm run dist         # genera l'installer Windows in dist/  (richiede Windows)
  ```

> L'app desktop salva il database in `%APPDATA%\Giornale dei Lavori\giornale.db`.

### Alternativa senza installazione (launcher .bat)

In assenza dell'installer puoi usare `Avvia-Giornale-Windows.bat`: richiede
Node.js installato, parte col doppio click e apre l'app nel browser.

## Avvio

```bash
npm install      # installa Express
npm start        # avvia il server su http://localhost:3000
```

Poi apri **http://localhost:3000** nel browser (anche da tablet/telefono sulla
stessa rete). Per cambiare porta: `PORT=8080 npm start`.

Per lo sviluppo con ricarica automatica:

```bash
npm run dev
```

## Dati

I dati sono salvati in un file SQLite locale: `data/giornale.db` (creato
automaticamente, escluso dal versionamento). Per usare un percorso diverso:

```bash
DB_PATH=/percorso/mio.db npm start
```

Per ripartire da zero è sufficiente eliminare il file `data/giornale.db`.

## Import del CME da CSV

Dalla scheda **Schede di cantiere → Importa CSV**. Intestazioni riconosciute
(sinonimi accettati, maiuscole/minuscole indifferenti):

| Campo            | Intestazioni accettate                          |
|------------------|-------------------------------------------------|
| codice           | `codice`, `cod`, `art`, `n.`, `numero`          |
| descrizione *    | `descrizione`, `lavorazione`, `designazione`    |
| categoria        | `categoria`, `capitolo`, `gruppo`               |
| unità di misura  | `um`, `u.m.`, `unità`, `misura`                 |
| quantità         | `quantità`, `qta`, `q.tà`                       |
| prezzo unitario  | `prezzo`, `p.u.`, `prezzo unit.`                |

\* unico campo obbligatorio. Esempio:

```csv
codice;descrizione;um;quantità;prezzo
01;Scavo di sbancamento;m3;100;10,50
02;Calcestruzzo Rck30;m3;50;120,00
```

## Test

```bash
npm test
```

I test (`node:test`) verificano il flusso completo CME → giornaliera →
contabilità/SAL e le validazioni di base, usando un database temporaneo isolato.

## Struttura del progetto

```
src/
  server.js   API Express (cantieri, voci, giornaliere, contabilità/SAL)
  db.js       Schema e connessione SQLite (node:sqlite)
  csv.js      Parser CSV del computo (formato italiano)
public/
  index.html  Interfaccia a schede
  style.css   Stile
  app.js      Logica frontend (vanilla JS)
test/
  api.test.js Test end-to-end dell'API
```

## API principali

| Metodo | Endpoint                              | Descrizione                       |
|--------|---------------------------------------|-----------------------------------|
| GET/POST | `/api/cantieri`                     | Elenco / creazione cantieri       |
| PUT/DELETE | `/api/cantieri/:id`               | Modifica / eliminazione cantiere  |
| GET/POST | `/api/cantieri/:id/voci`            | Voci di computo del cantiere      |
| POST   | `/api/cantieri/:id/voci/import`       | Import CME da CSV                  |
| PUT/DELETE | `/api/voci/:id`                   | Modifica / eliminazione voce      |
| GET/POST | `/api/cantieri/:id/giornaliere`     | Giornaliere (filtro `from`/`to`)  |
| GET/PUT/DELETE | `/api/giornaliere/:id`        | Dettaglio / modifica / eliminazione |
| GET    | `/api/cantieri/:id/contabilita`       | Contabilità e SAL (filtro `alla_data`) |
