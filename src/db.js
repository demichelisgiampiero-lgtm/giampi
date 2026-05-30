// Gestione del database SQLite tramite il modulo integrato di Node (node:sqlite).
// Nessuna dipendenza nativa da compilare: funziona out-of-the-box con Node >= 22.5.
import { DatabaseSync } from 'node:sqlite';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { mkdirSync } from 'node:fs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const DATA_DIR = join(__dirname, '..', 'data');
const DB_PATH = process.env.DB_PATH || join(DATA_DIR, 'giornale.db');

// Assicura l'esistenza della cartella dati prima di aprire il database.
mkdirSync(DATA_DIR, { recursive: true });

const db = new DatabaseSync(DB_PATH);

// Abilita il rispetto delle foreign key (disattivate di default in SQLite).
db.exec('PRAGMA foreign_keys = ON;');

// ---------------------------------------------------------------------------
// Schema del giornale dei lavori (predisposto per l'impresa).
//
//   cantieri      = commessa/appalto (dati di contratto e CSA)
//   voci_computo  = schede di cantiere derivate dal CME (voce, UM, qta, prezzo)
//   giornaliere   = registrazione giornaliera del personale di cantiere
//   avanzamenti   = quantità eseguita nella giornata, agganciata a una voce CME
//
// La contabilità e lo SAL si ricavano sommando gli avanzamenti per voce.
// ---------------------------------------------------------------------------
db.exec(`
  CREATE TABLE IF NOT EXISTS cantieri (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    nome                 TEXT NOT NULL,
    codice_commessa      TEXT,
    committente          TEXT,
    importo_contrattuale REAL,
    rif_contratto        TEXT,
    rif_csa              TEXT,
    data_consegna        TEXT,
    data_inizio          TEXT,
    data_fine_prevista   TEXT,
    note                 TEXT,
    created_at           TEXT NOT NULL DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS voci_computo (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    cantiere_id       INTEGER NOT NULL REFERENCES cantieri(id) ON DELETE CASCADE,
    codice            TEXT,
    descrizione       TEXT NOT NULL,
    categoria         TEXT,
    unita_misura      TEXT,
    quantita_progetto REAL NOT NULL DEFAULT 0,
    prezzo_unitario   REAL NOT NULL DEFAULT 0,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS giornaliere (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    cantiere_id            INTEGER NOT NULL REFERENCES cantieri(id) ON DELETE CASCADE,
    data                   TEXT NOT NULL,
    meteo                  TEXT,
    temperatura            TEXT,
    maestranze_numero      INTEGER,
    maestranze_descrizione TEXT,
    mezzi                  TEXT,
    materiali              TEXT,
    note                   TEXT,
    created_at             TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at             TEXT NOT NULL DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS avanzamenti (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    giornaliera_id    INTEGER NOT NULL REFERENCES giornaliere(id) ON DELETE CASCADE,
    voce_computo_id   INTEGER NOT NULL REFERENCES voci_computo(id) ON DELETE CASCADE,
    quantita_eseguita REAL NOT NULL DEFAULT 0,
    note              TEXT
  );

  CREATE INDEX IF NOT EXISTS idx_voci_cantiere   ON voci_computo(cantiere_id);
  CREATE INDEX IF NOT EXISTS idx_giorn_cantiere  ON giornaliere(cantiere_id);
  CREATE INDEX IF NOT EXISTS idx_giorn_data      ON giornaliere(data);
  CREATE INDEX IF NOT EXISTS idx_avanz_giorn     ON avanzamenti(giornaliera_id);
  CREATE INDEX IF NOT EXISTS idx_avanz_voce      ON avanzamenti(voce_computo_id);
`);

/**
 * Esegue `fn` dentro una transazione (node:sqlite non offre db.transaction()).
 * Effettua il rollback e ripropaga l'errore in caso di fallimento.
 */
export function transazione(fn) {
  db.exec('BEGIN');
  try {
    const risultato = fn();
    db.exec('COMMIT');
    return risultato;
  } catch (err) {
    db.exec('ROLLBACK');
    throw err;
  }
}

/** Chiude la connessione al database (utile nei test e alla chiusura dell'app). */
export function chiudiDb() {
  try { db.close(); } catch { /* già chiuso */ }
}

export default db;
export { DB_PATH };
