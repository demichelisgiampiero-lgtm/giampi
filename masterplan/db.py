"""
Strato dati di Masterplan.

Usa SQLite (incluso in Python, nessuna installazione). Gestisce:
- società della rete
- richieste in arrivo (gara / lavoro / consulenza)
- assegnazioni delle richieste alle società (con risposta entro 24h)
- registro eventi (tracciabilità del flusso)

Tutto il carico di lavoro viene calcolato a partire dalle assegnazioni
accettate o in corso, così da non sovraccaricare le società.
"""

import os
import sqlite3
from datetime import datetime, timedelta

# Il database è un singolo file accanto al codice: facile da copiare/salvare.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "masterplan.db")

# Quante ore ha una società per rispondere a una richiesta.
ORE_PER_RISPOSTA = 24


# --------------------------------------------------------------------------- #
# Connessione
# --------------------------------------------------------------------------- #
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # accesso alle colonne per nome
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def now_iso():
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #
SCHEMA = """
CREATE TABLE IF NOT EXISTS societa (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT NOT NULL,
    referente TEXT,
    email     TEXT,
    -- Capacità massima espressa in "punti carico" (es. progetti-uomo
    -- contemporanei sostenibili). Serve per calcolare la saturazione.
    capacita  REAL NOT NULL DEFAULT 10,
    attiva    INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS richieste (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    codice        TEXT,
    oggetto       TEXT NOT NULL,
    -- GARA | LAVORO | CONSULENZA
    tipo          TEXT NOT NULL,
    cliente       TEXT,
    descrizione   TEXT,
    -- RICEVUTA | INVIATA | ACCETTATA | IN_CORSO | COMPLETATA | CHIUSA_NEGATIVA
    stato         TEXT NOT NULL DEFAULT 'RICEVUTA',
    data_arrivo   TEXT NOT NULL,
    scadenza_lavoro TEXT,
    -- Project manager (persona) e società capofila, definiti dal manager di rete
    pm_nome       TEXT,
    pm_societa_id INTEGER REFERENCES societa(id),
    note          TEXT
);

CREATE TABLE IF NOT EXISTS assegnazioni (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    richiesta_id  INTEGER NOT NULL REFERENCES richieste(id) ON DELETE CASCADE,
    societa_id    INTEGER NOT NULL REFERENCES societa(id),
    -- INVIATA | ACCETTATA | RIFIUTATA | SCADUTA
    stato         TEXT NOT NULL DEFAULT 'INVIATA',
    -- CAPOFILA | PARTNER
    ruolo         TEXT NOT NULL DEFAULT 'PARTNER',
    -- Peso stimato del carico che questo lavoro porta alla società.
    peso          REAL NOT NULL DEFAULT 1,
    data_invio    TEXT NOT NULL,
    scadenza_risposta TEXT NOT NULL,
    data_risposta TEXT,
    motivo_rifiuto TEXT,
    UNIQUE (richiesta_id, societa_id)
);

CREATE TABLE IF NOT EXISTS eventi (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    richiesta_id INTEGER NOT NULL REFERENCES richieste(id) ON DELETE CASCADE,
    quando       TEXT NOT NULL,
    chi          TEXT,
    testo        TEXT NOT NULL
);
"""


def init_db():
    """Crea le tabelle se non esistono e inserisce le 9 società iniziali."""
    nuovo = not os.path.exists(DB_PATH)
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    if nuovo or conn.execute("SELECT COUNT(*) FROM societa").fetchone()[0] == 0:
        _seed_societa(conn)
    conn.close()


def _seed_societa(conn):
    societa = [
        ("Alfa Engineering",      "Ing. Rossi",    "rossi@alfa.it",    12),
        ("Beta Progetti",         "Ing. Bianchi",  "bianchi@beta.it",  10),
        ("Gamma Strutture",       "Ing. Verdi",    "verdi@gamma.it",    8),
        ("Delta Impianti",        "Ing. Neri",     "neri@delta.it",    10),
        ("Epsilon Infrastrutture","Ing. Gallo",    "gallo@epsilon.it", 14),
        ("Zeta Ambiente",         "Ing. Conti",    "conti@zeta.it",     6),
        ("Eta Architettura",      "Arch. Ferri",   "ferri@eta.it",      8),
        ("Theta Geotecnica",      "Ing. Marini",   "marini@theta.it",   6),
        ("Iota Consulting",       "Ing. De Luca",  "deluca@iota.it",    9),
    ]
    conn.executemany(
        "INSERT INTO societa (nome, referente, email, capacita) VALUES (?,?,?,?)",
        societa,
    )
    conn.commit()


# --------------------------------------------------------------------------- #
# Eventi (registro/tracciabilità)
# --------------------------------------------------------------------------- #
def log_evento(conn, richiesta_id, testo, chi="Sistema"):
    conn.execute(
        "INSERT INTO eventi (richiesta_id, quando, chi, testo) VALUES (?,?,?,?)",
        (richiesta_id, now_iso(), chi, testo),
    )


# --------------------------------------------------------------------------- #
# Società
# --------------------------------------------------------------------------- #
def lista_societa(solo_attive=False):
    conn = get_conn()
    q = "SELECT * FROM societa"
    if solo_attive:
        q += " WHERE attiva = 1"
    q += " ORDER BY nome"
    rows = conn.execute(q).fetchall()
    conn.close()
    return rows


def aggiungi_societa(nome, referente, email, capacita):
    conn = get_conn()
    conn.execute(
        "INSERT INTO societa (nome, referente, email, capacita) VALUES (?,?,?,?)",
        (nome, referente, email, float(capacita or 10)),
    )
    conn.commit()
    conn.close()


def carico_societa():
    """
    Ritorna, per ogni società, il carico attivo e la % di saturazione.

    Il carico = somma dei pesi delle assegnazioni ACCETTATA su richieste
    non ancora completate/chiuse.
    """
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT s.id, s.nome, s.referente, s.email, s.capacita, s.attiva,
               COALESCE(SUM(CASE
                   WHEN a.stato = 'ACCETTATA'
                    AND r.stato IN ('ACCETTATA','IN_CORSO')
                   THEN a.peso ELSE 0 END), 0) AS carico,
               COUNT(CASE
                   WHEN a.stato = 'ACCETTATA'
                    AND r.stato IN ('ACCETTATA','IN_CORSO')
                   THEN 1 END) AS lavori_attivi
        FROM societa s
        LEFT JOIN assegnazioni a ON a.societa_id = s.id
        LEFT JOIN richieste r    ON r.id = a.richiesta_id
        GROUP BY s.id
        ORDER BY s.nome
        """
    ).fetchall()
    conn.close()
    risultato = []
    for r in rows:
        capacita = r["capacita"] or 1
        saturazione = round(100 * r["carico"] / capacita)
        risultato.append({**dict(r), "saturazione": saturazione})
    return risultato


# --------------------------------------------------------------------------- #
# Richieste
# --------------------------------------------------------------------------- #
def crea_richiesta(oggetto, tipo, cliente, descrizione, scadenza_lavoro, chi):
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO richieste
           (oggetto, tipo, cliente, descrizione, scadenza_lavoro,
            stato, data_arrivo)
           VALUES (?,?,?,?,?, 'RICEVUTA', ?)""",
        (oggetto, tipo, cliente, descrizione, scadenza_lavoro or None, now_iso()),
    )
    rid = cur.lastrowid
    # Codice leggibile tipo R-2026-0007
    codice = "R-%s-%04d" % (datetime.now().year, rid)
    conn.execute("UPDATE richieste SET codice=? WHERE id=?", (codice, rid))
    log_evento(conn, rid, "Richiesta registrata dalla segreteria (%s)." % tipo, chi)
    conn.commit()
    conn.close()
    return rid


def lista_richieste(stato=None):
    conn = get_conn()
    q = """SELECT r.*, ps.nome AS pm_societa_nome
           FROM richieste r
           LEFT JOIN societa ps ON ps.id = r.pm_societa_id"""
    params = ()
    if stato:
        q += " WHERE r.stato = ?"
        params = (stato,)
    q += " ORDER BY r.data_arrivo DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows


def get_richiesta(rid):
    conn = get_conn()
    r = conn.execute(
        """SELECT r.*, ps.nome AS pm_societa_nome
           FROM richieste r
           LEFT JOIN societa ps ON ps.id = r.pm_societa_id
           WHERE r.id = ?""",
        (rid,),
    ).fetchone()
    if not r:
        conn.close()
        return None, [], []
    assegnazioni = conn.execute(
        """SELECT a.*, s.nome AS societa_nome, s.referente, s.email
           FROM assegnazioni a JOIN societa s ON s.id = a.societa_id
           WHERE a.richiesta_id = ?
           ORDER BY a.ruolo DESC, s.nome""",
        (rid,),
    ).fetchall()
    eventi = conn.execute(
        "SELECT * FROM eventi WHERE richiesta_id=? ORDER BY id",
        (rid,),
    ).fetchall()
    conn.close()
    return r, assegnazioni, eventi


def assegna_societa(rid, societa_pesi, chi):
    """
    Il manager di rete individua le società; la segreteria invia la richiesta.

    societa_pesi: lista di (societa_id, peso). Crea le assegnazioni con
    scadenza risposta a 24h e porta la richiesta in stato INVIATA.
    """
    conn = get_conn()
    scadenza = (datetime.now() + timedelta(hours=ORE_PER_RISPOSTA)) \
        .replace(microsecond=0).isoformat(sep=" ")
    nomi = []
    for societa_id, peso in societa_pesi:
        try:
            conn.execute(
                """INSERT INTO assegnazioni
                   (richiesta_id, societa_id, stato, peso,
                    data_invio, scadenza_risposta)
                   VALUES (?,?, 'INVIATA', ?, ?, ?)""",
                (rid, societa_id, float(peso or 1), now_iso(), scadenza),
            )
            nome = conn.execute(
                "SELECT nome FROM societa WHERE id=?", (societa_id,)
            ).fetchone()["nome"]
            nomi.append(nome)
        except sqlite3.IntegrityError:
            # Società già assegnata a questa richiesta: la ignoriamo.
            continue
    if nomi:
        conn.execute("UPDATE richieste SET stato='INVIATA' WHERE id=?", (rid,))
        log_evento(
            conn, rid,
            "Richiesta inviata a: %s. Risposta attesa entro 24h (%s)."
            % (", ".join(nomi), scadenza),
            chi,
        )
    conn.commit()
    conn.close()


def rispondi_assegnazione(assegnazione_id, accetta, motivo, chi):
    """Una società accetta o rifiuta. Aggiorna anche lo stato della richiesta."""
    conn = get_conn()
    a = conn.execute(
        "SELECT * FROM assegnazioni WHERE id=?", (assegnazione_id,)
    ).fetchone()
    if not a:
        conn.close()
        return
    rid = a["richiesta_id"]
    societa = conn.execute(
        "SELECT nome FROM societa WHERE id=?", (a["societa_id"],)
    ).fetchone()["nome"]

    if accetta:
        conn.execute(
            "UPDATE assegnazioni SET stato='ACCETTATA', data_risposta=? WHERE id=?",
            (now_iso(), assegnazione_id),
        )
        log_evento(conn, rid, "%s ha ACCETTATO il lavoro." % societa, chi)
        # Se la richiesta era ancora solo "INVIATA", passa ad ACCETTATA.
        r = conn.execute("SELECT stato FROM richieste WHERE id=?", (rid,)).fetchone()
        if r["stato"] in ("INVIATA", "RICEVUTA"):
            conn.execute("UPDATE richieste SET stato='ACCETTATA' WHERE id=?", (rid,))
    else:
        conn.execute(
            """UPDATE assegnazioni
               SET stato='RIFIUTATA', data_risposta=?, motivo_rifiuto=?
               WHERE id=?""",
            (now_iso(), motivo or None, assegnazione_id),
        )
        log_evento(
            conn, rid,
            "%s ha RIFIUTATO%s." % (societa, (" — " + motivo) if motivo else ""),
            chi,
        )
        _ricalcola_stato_negativo(conn, rid)
    conn.commit()
    conn.close()


def _ricalcola_stato_negativo(conn, rid):
    """Se tutte le società hanno rifiutato/scaduto, segna la richiesta come chiusa negativa."""
    righe = conn.execute(
        "SELECT stato FROM assegnazioni WHERE richiesta_id=?", (rid,)
    ).fetchall()
    if righe and all(x["stato"] in ("RIFIUTATA", "SCADUTA") for x in righe):
        r = conn.execute("SELECT stato FROM richieste WHERE id=?", (rid,)).fetchone()
        if r["stato"] in ("INVIATA", "RICEVUTA"):
            conn.execute(
                "UPDATE richieste SET stato='CHIUSA_NEGATIVA' WHERE id=?", (rid,)
            )
            log_evento(
                conn, rid,
                "Nessuna società disponibile: richiesta chiusa con esito negativo.",
            )


def definisci_gruppo(rid, pm_nome, pm_societa_id, chi):
    """Il manager di rete definisce il project manager e avvia il lavoro."""
    conn = get_conn()
    conn.execute(
        "UPDATE richieste SET pm_nome=?, pm_societa_id=?, stato='IN_CORSO' WHERE id=?",
        (pm_nome, pm_societa_id or None, rid),
    )
    # La società del PM diventa capofila tra le assegnazioni accettate.
    if pm_societa_id:
        conn.execute(
            "UPDATE assegnazioni SET ruolo='CAPOFILA' WHERE richiesta_id=? AND societa_id=?",
            (rid, pm_societa_id),
        )
    nome_soc = ""
    if pm_societa_id:
        row = conn.execute("SELECT nome FROM societa WHERE id=?", (pm_societa_id,)).fetchone()
        if row:
            nome_soc = " (%s)" % row["nome"]
    log_evento(
        conn, rid,
        "Gruppo di lavoro avviato. Project Manager: %s%s." % (pm_nome or "—", nome_soc),
        chi,
    )
    conn.commit()
    conn.close()


def completa_richiesta(rid, chi):
    conn = get_conn()
    conn.execute("UPDATE richieste SET stato='COMPLETATA' WHERE id=?", (rid,))
    log_evento(conn, rid, "Lavoro completato e archiviato.", chi)
    conn.commit()
    conn.close()


def scadute_aggiorna():
    """
    Segna come SCADUTE le assegnazioni 'INVIATA' oltre le 24h senza risposta.
    Va chiamata a ogni caricamento pagina: tiene il quadro sempre aggiornato.
    """
    conn = get_conn()
    adesso = now_iso()
    scadute = conn.execute(
        "SELECT id, richiesta_id FROM assegnazioni "
        "WHERE stato='INVIATA' AND scadenza_risposta < ?",
        (adesso,),
    ).fetchall()
    for a in scadute:
        conn.execute("UPDATE assegnazioni SET stato='SCADUTA' WHERE id=?", (a["id"],))
        log_evento(
            conn, a["richiesta_id"],
            "Termine di 24h scaduto senza risposta da una società.",
        )
        _ricalcola_stato_negativo(conn, a["richiesta_id"])
    if scadute:
        conn.commit()
    conn.close()


def statistiche():
    """Numeri per la dashboard."""
    conn = get_conn()
    per_stato = {
        row["stato"]: row["n"]
        for row in conn.execute(
            "SELECT stato, COUNT(*) n FROM richieste GROUP BY stato"
        ).fetchall()
    }
    # Risposte in scadenza (entro 24h, ancora da rispondere)
    in_attesa = conn.execute(
        "SELECT COUNT(*) n FROM assegnazioni WHERE stato='INVIATA'"
    ).fetchone()["n"]
    conn.close()
    return {"per_stato": per_stato, "in_attesa": in_attesa}
