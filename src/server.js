// Giornale dei Lavori — server Express.
// API REST per cantieri, schede di cantiere (CME), giornaliere con avanzamenti,
// contabilità e calcolo dello Stato Avanzamento Lavori (SAL).
import express from 'express';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import db, { transazione } from './db.js';
import { parseVociComputo } from './csv.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 3000;

// Protezione con password (HTTP Basic): attiva SOLO se è impostata la variabile
// d'ambiente APP_PASSWORD. In locale/desktop, dove non è impostata, l'accesso
// resta libero. Online (es. Render) la si imposta per proteggere i dati.
// Si può personalizzare l'utente con APP_USER (default: "cieffe").
const APP_PASSWORD = process.env.APP_PASSWORD;
const APP_USER = process.env.APP_USER || 'cieffe';
if (APP_PASSWORD) {
  app.use((req, res, next) => {
    const header = req.headers.authorization || '';
    const [schema, encoded] = header.split(' ');
    if (schema === 'Basic' && encoded) {
      const [user, pass] = Buffer.from(encoded, 'base64').toString().split(':');
      if (user === APP_USER && pass === APP_PASSWORD) return next();
    }
    res.set('WWW-Authenticate', 'Basic realm="Giornale dei Lavori", charset="UTF-8"');
    res.status(401).send('Accesso riservato. Inserisci utente e password.');
  });
}

app.use(express.json({ limit: '5mb' }));
app.use(express.text({ type: 'text/csv', limit: '10mb' }));
app.use(express.static(join(__dirname, '..', 'public')));

// --- Helper -----------------------------------------------------------------

/** Avvolge un handler async/sync inoltrando gli errori al middleware. */
const wrap = (fn) => (req, res, next) => {
  try { Promise.resolve(fn(req, res, next)).catch(next); }
  catch (err) { next(err); }
};

/** Errore HTTP con status personalizzato. */
class HttpError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

/** Converte un valore in numero o restituisce il default. */
function num(v, def = null) {
  if (v === '' || v === null || v === undefined) return def;
  const n = Number(v);
  return Number.isFinite(n) ? n : def;
}

/** Verifica che il cantiere esista, altrimenti 404. */
function getCantiereOr404(id) {
  const c = db.prepare('SELECT * FROM cantieri WHERE id = ?').get(id);
  if (!c) throw new HttpError(404, 'Cantiere non trovato.');
  return c;
}

// ===========================================================================
// CANTIERI / COMMESSE
// ===========================================================================

app.get('/api/cantieri', wrap((req, res) => {
  const rows = db.prepare('SELECT * FROM cantieri ORDER BY nome COLLATE NOCASE').all();
  res.json(rows);
}));

app.get('/api/cantieri/:id', wrap((req, res) => {
  res.json(getCantiereOr404(req.params.id));
}));

const CAMPI_CANTIERE = [
  'nome', 'codice_commessa', 'committente', 'importo_contrattuale',
  'rif_contratto', 'rif_csa', 'data_consegna', 'data_inizio',
  'data_fine_prevista', 'note',
];

app.post('/api/cantieri', wrap((req, res) => {
  const b = req.body || {};
  if (!b.nome || String(b.nome).trim() === '') {
    throw new HttpError(400, 'Il nome del cantiere è obbligatorio.');
  }
  const valori = CAMPI_CANTIERE.map((k) =>
    k === 'importo_contrattuale' ? num(b[k]) : (b[k] ?? null));
  const stmt = db.prepare(
    `INSERT INTO cantieri (${CAMPI_CANTIERE.join(',')})
     VALUES (${CAMPI_CANTIERE.map(() => '?').join(',')})`);
  const info = stmt.run(...valori);
  res.status(201).json(getCantiereOr404(info.lastInsertRowid));
}));

app.put('/api/cantieri/:id', wrap((req, res) => {
  getCantiereOr404(req.params.id);
  const b = req.body || {};
  if ('nome' in b && String(b.nome).trim() === '') {
    throw new HttpError(400, 'Il nome del cantiere non può essere vuoto.');
  }
  const valori = CAMPI_CANTIERE.map((k) =>
    k === 'importo_contrattuale' ? num(b[k]) : (b[k] ?? null));
  db.prepare(
    `UPDATE cantieri SET ${CAMPI_CANTIERE.map((k) => `${k}=?`).join(',')} WHERE id=?`
  ).run(...valori, req.params.id);
  res.json(getCantiereOr404(req.params.id));
}));

app.delete('/api/cantieri/:id', wrap((req, res) => {
  getCantiereOr404(req.params.id);
  db.prepare('DELETE FROM cantieri WHERE id = ?').run(req.params.id);
  res.status(204).end();
}));

// ===========================================================================
// VOCI DI COMPUTO (schede di cantiere derivate dal CME)
// ===========================================================================

app.get('/api/cantieri/:id/voci', wrap((req, res) => {
  getCantiereOr404(req.params.id);
  const rows = db.prepare(
    'SELECT * FROM voci_computo WHERE cantiere_id = ? ORDER BY id'
  ).all(req.params.id);
  res.json(rows);
}));

const CAMPI_VOCE = ['codice', 'descrizione', 'categoria', 'unita_misura',
  'quantita_progetto', 'prezzo_unitario'];

function validaVoce(b) {
  if (!b.descrizione || String(b.descrizione).trim() === '') {
    throw new HttpError(400, 'La descrizione della voce è obbligatoria.');
  }
}

app.post('/api/cantieri/:id/voci', wrap((req, res) => {
  getCantiereOr404(req.params.id);
  const b = req.body || {};
  validaVoce(b);
  const info = db.prepare(
    `INSERT INTO voci_computo (cantiere_id, ${CAMPI_VOCE.join(',')})
     VALUES (?, ${CAMPI_VOCE.map(() => '?').join(',')})`
  ).run(
    req.params.id, b.codice ?? null, b.descrizione, b.categoria ?? null,
    b.unita_misura ?? null, num(b.quantita_progetto, 0), num(b.prezzo_unitario, 0)
  );
  res.status(201).json(db.prepare('SELECT * FROM voci_computo WHERE id = ?').get(info.lastInsertRowid));
}));

app.put('/api/voci/:id', wrap((req, res) => {
  const voce = db.prepare('SELECT * FROM voci_computo WHERE id = ?').get(req.params.id);
  if (!voce) throw new HttpError(404, 'Voce non trovata.');
  const b = req.body || {};
  validaVoce(b);
  db.prepare(
    `UPDATE voci_computo SET ${CAMPI_VOCE.map((k) => `${k}=?`).join(',')} WHERE id=?`
  ).run(
    b.codice ?? null, b.descrizione, b.categoria ?? null, b.unita_misura ?? null,
    num(b.quantita_progetto, 0), num(b.prezzo_unitario, 0), req.params.id
  );
  res.json(db.prepare('SELECT * FROM voci_computo WHERE id = ?').get(req.params.id));
}));

app.delete('/api/voci/:id', wrap((req, res) => {
  const voce = db.prepare('SELECT * FROM voci_computo WHERE id = ?').get(req.params.id);
  if (!voce) throw new HttpError(404, 'Voce non trovata.');
  db.prepare('DELETE FROM voci_computo WHERE id = ?').run(req.params.id);
  res.status(204).end();
}));

// Import massivo del CME da CSV. Accetta sia text/csv grezzo sia { csv: "..." }.
app.post('/api/cantieri/:id/voci/import', wrap((req, res) => {
  getCantiereOr404(req.params.id);
  const testo = typeof req.body === 'string' ? req.body : (req.body && req.body.csv);
  if (!testo || String(testo).trim() === '') {
    throw new HttpError(400, 'Nessun contenuto CSV ricevuto.');
  }
  const { voci, errori } = parseVociComputo(testo);
  if (voci.length === 0) {
    throw new HttpError(400, `Nessuna voce importabile. ${errori.join(' ')}`.trim());
  }
  const stmt = db.prepare(
    `INSERT INTO voci_computo (cantiere_id, ${CAMPI_VOCE.join(',')})
     VALUES (?, ${CAMPI_VOCE.map(() => '?').join(',')})`);
  transazione(() => {
    for (const v of voci) {
      stmt.run(req.params.id, v.codice, v.descrizione, v.categoria,
        v.unita_misura, v.quantita_progetto, v.prezzo_unitario);
    }
  });
  res.status(201).json({ importate: voci.length, avvisi: errori });
}));

// ===========================================================================
// GIORNALIERE (registrazioni giornaliere del personale di cantiere)
// ===========================================================================

const CAMPI_GIORN = ['data', 'meteo', 'temperatura', 'maestranze_numero',
  'maestranze_descrizione', 'mezzi', 'materiali', 'note'];

/** Carica una giornaliera con le sue righe di avanzamento. */
function getGiornalieraCompleta(id) {
  const g = db.prepare('SELECT * FROM giornaliere WHERE id = ?').get(id);
  if (!g) return null;
  g.avanzamenti = db.prepare(
    `SELECT a.*, v.codice AS voce_codice, v.descrizione AS voce_descrizione,
            v.unita_misura, v.prezzo_unitario
     FROM avanzamenti a JOIN voci_computo v ON v.id = a.voce_computo_id
     WHERE a.giornaliera_id = ? ORDER BY a.id`
  ).all(id);
  return g;
}

app.get('/api/cantieri/:id/giornaliere', wrap((req, res) => {
  getCantiereOr404(req.params.id);
  const { from, to } = req.query;
  const clausole = ['cantiere_id = ?'];
  const args = [req.params.id];
  if (from) { clausole.push('data >= ?'); args.push(from); }
  if (to) { clausole.push('data <= ?'); args.push(to); }
  const rows = db.prepare(
    `SELECT g.*,
            (SELECT COUNT(*) FROM avanzamenti a WHERE a.giornaliera_id = g.id) AS n_avanzamenti
     FROM giornaliere g WHERE ${clausole.join(' AND ')}
     ORDER BY data DESC, g.id DESC`
  ).all(...args);
  res.json(rows);
}));

app.get('/api/giornaliere/:id', wrap((req, res) => {
  const g = getGiornalieraCompleta(req.params.id);
  if (!g) throw new HttpError(404, 'Giornaliera non trovata.');
  res.json(g);
}));

/** Valida e salva le righe di avanzamento di una giornaliera (sostituzione totale). */
function salvaAvanzamenti(giornalieraId, cantiereId, avanzamenti) {
  if (!Array.isArray(avanzamenti)) return;
  db.prepare('DELETE FROM avanzamenti WHERE giornaliera_id = ?').run(giornalieraId);
  const stmt = db.prepare(
    `INSERT INTO avanzamenti (giornaliera_id, voce_computo_id, quantita_eseguita, note)
     VALUES (?, ?, ?, ?)`);
  for (const a of avanzamenti) {
    const voceId = num(a.voce_computo_id);
    if (!voceId) continue;
    const voce = db.prepare(
      'SELECT id FROM voci_computo WHERE id = ? AND cantiere_id = ?'
    ).get(voceId, cantiereId);
    if (!voce) throw new HttpError(400, `Voce ${voceId} non appartiene al cantiere.`);
    stmt.run(giornalieraId, voceId, num(a.quantita_eseguita, 0), a.note ?? null);
  }
}

app.post('/api/cantieri/:id/giornaliere', wrap((req, res) => {
  getCantiereOr404(req.params.id);
  const b = req.body || {};
  if (!b.data || String(b.data).trim() === '') {
    throw new HttpError(400, 'La data della giornaliera è obbligatoria.');
  }
  const id = transazione(() => {
    const info = db.prepare(
      `INSERT INTO giornaliere (cantiere_id, ${CAMPI_GIORN.join(',')})
       VALUES (?, ${CAMPI_GIORN.map(() => '?').join(',')})`
    ).run(
      req.params.id, b.data, b.meteo ?? null, b.temperatura ?? null,
      num(b.maestranze_numero), b.maestranze_descrizione ?? null,
      b.mezzi ?? null, b.materiali ?? null, b.note ?? null
    );
    salvaAvanzamenti(info.lastInsertRowid, Number(req.params.id), b.avanzamenti);
    return info.lastInsertRowid;
  });
  res.status(201).json(getGiornalieraCompleta(id));
}));

app.put('/api/giornaliere/:id', wrap((req, res) => {
  const g = db.prepare('SELECT * FROM giornaliere WHERE id = ?').get(req.params.id);
  if (!g) throw new HttpError(404, 'Giornaliera non trovata.');
  const b = req.body || {};
  if ('data' in b && String(b.data).trim() === '') {
    throw new HttpError(400, 'La data non può essere vuota.');
  }
  transazione(() => {
    db.prepare(
      `UPDATE giornaliere SET ${CAMPI_GIORN.map((k) => `${k}=?`).join(',')},
       updated_at = datetime('now') WHERE id = ?`
    ).run(
      b.data ?? g.data, b.meteo ?? null, b.temperatura ?? null,
      num(b.maestranze_numero), b.maestranze_descrizione ?? null,
      b.mezzi ?? null, b.materiali ?? null, b.note ?? null, req.params.id
    );
    if ('avanzamenti' in b) {
      salvaAvanzamenti(Number(req.params.id), g.cantiere_id, b.avanzamenti);
    }
  });
  res.json(getGiornalieraCompleta(req.params.id));
}));

app.delete('/api/giornaliere/:id', wrap((req, res) => {
  const g = db.prepare('SELECT * FROM giornaliere WHERE id = ?').get(req.params.id);
  if (!g) throw new HttpError(404, 'Giornaliera non trovata.');
  db.prepare('DELETE FROM giornaliere WHERE id = ?').run(req.params.id);
  res.status(204).end();
}));

// ===========================================================================
// CONTABILITÀ e SAL (Stato Avanzamento Lavori)
// ===========================================================================
//
// Per ogni voce di computo somma le quantità eseguite (eventualmente fino a una
// data) e le valorizza al prezzo unitario. Il totale eseguito, confrontato con
// l'importo di progetto/contratto, costituisce lo SAL.

app.get('/api/cantieri/:id/contabilita', wrap((req, res) => {
  const cantiere = getCantiereOr404(req.params.id);
  const allaData = req.query.alla_data || null;

  // Somma avanzamenti per voce, con filtro opzionale sulla data della giornaliera.
  const righe = db.prepare(
    `SELECT v.id, v.codice, v.descrizione, v.categoria, v.unita_misura,
            v.quantita_progetto, v.prezzo_unitario,
            COALESCE((
              SELECT SUM(a.quantita_eseguita)
              FROM avanzamenti a
              JOIN giornaliere g ON g.id = a.giornaliera_id
              WHERE a.voce_computo_id = v.id
                AND ($alla_data IS NULL OR g.data <= $alla_data)
            ), 0) AS quantita_eseguita
     FROM voci_computo v
     WHERE v.cantiere_id = $cantiere
     ORDER BY v.id`
  ).all({ cantiere: req.params.id, alla_data: allaData });

  let importoProgetto = 0;
  let importoEseguito = 0;
  const voci = righe.map((r) => {
    const impProg = r.quantita_progetto * r.prezzo_unitario;
    const impEseg = r.quantita_eseguita * r.prezzo_unitario;
    importoProgetto += impProg;
    importoEseguito += impEseg;
    const perc = r.quantita_progetto > 0
      ? (r.quantita_eseguita / r.quantita_progetto) * 100 : null;
    return {
      ...r,
      importo_progetto: impProg,
      importo_eseguito: impEseg,
      residuo: impProg - impEseg,
      percentuale: perc,
    };
  });

  const baseSal = cantiere.importo_contrattuale || importoProgetto;
  const sal = {
    alla_data: allaData,
    importo_eseguito: importoEseguito,
    importo_progetto: importoProgetto,
    importo_contrattuale: cantiere.importo_contrattuale,
    base_calcolo: baseSal,
    percentuale_avanzamento: baseSal > 0 ? (importoEseguito / baseSal) * 100 : null,
    residuo: baseSal - importoEseguito,
  };

  res.json({ cantiere, voci, sal });
}));

// --- Frontend SPA fallback --------------------------------------------------
app.get('/', (req, res) => res.sendFile(join(__dirname, '..', 'public', 'index.html')));

// --- Gestione errori --------------------------------------------------------
app.use((err, req, res, next) => {
  const status = err.status || 500;
  if (status >= 500) console.error(err);
  res.status(status).json({ errore: err.message || 'Errore interno del server.' });
});

/**
 * Avvia il server e risolve con { server, url, port }.
 * Usato dall'app desktop (Electron). Con `port = 0` il sistema sceglie
 * una porta libera, evitando conflitti quando l'app è già avviata altrove.
 */
export function avviaServer(port = PORT) {
  return new Promise((resolve) => {
    const server = app.listen(port, '127.0.0.1', () => {
      const realPort = server.address().port;
      resolve({ server, port: realPort, url: `http://127.0.0.1:${realPort}` });
    });
  });
}

// Avvio solo quando eseguito direttamente (non durante i test né sotto Electron).
const eseguitoDirettamente =
  process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1];
if (eseguitoDirettamente) {
  app.listen(PORT, () => {
    console.log(`Giornale dei Lavori in ascolto su http://localhost:${PORT}`);
  });
}

export default app;
