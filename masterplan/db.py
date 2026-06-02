"""
Strato dati di Masterplan.

Usa SQLite (incluso in Python, nessuna installazione). Gestisce:
- società della rete
- utenti e ruoli (segreteria / manager di rete / società)
- richieste in arrivo (gara / lavoro / consulenza)
- assegnazioni delle richieste alle società (con risposta entro 24h)
- registro eventi (tracciabilità del flusso)
- posta inviata (outbox) con notifiche automatiche
- promemoria automatici allo scadere delle 24h

Tutto il carico di lavoro viene calcolato a partire dalle assegnazioni
accettate o in corso, così da non sovraccaricare le società.
"""

import os
import sqlite3
from datetime import datetime, timedelta

import notifications as notif
import security

# Il database è un singolo file accanto al codice: facile da copiare/salvare.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "masterplan.db")

# Quante ore ha una società per rispondere a una richiesta.
ORE_PER_RISPOSTA = 24
# Quante ore prima della scadenza inviare il sollecito automatico.
ORE_SOLLECITO = 6

# Ruoli utente
RUOLO_SEGRETERIA = "SEGRETERIA"
RUOLO_MANAGER = "MANAGER"
RUOLO_SOCIETA = "SOCIETA"


# --------------------------------------------------------------------------- #
# Connessione / tempo
# --------------------------------------------------------------------------- #
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def now_dt():
    return datetime.now().replace(microsecond=0)


def now_iso():
    return now_dt().isoformat(sep=" ")


def _parse(iso):
    try:
        return datetime.fromisoformat(iso)
    except (ValueError, TypeError):
        return None


# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #
SCHEMA = """
CREATE TABLE IF NOT EXISTS societa (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT NOT NULL,
    referente TEXT,
    email     TEXT,
    capacita  REAL NOT NULL DEFAULT 10,
    attiva    INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS utenti (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT NOT NULL UNIQUE,
    nome       TEXT NOT NULL,
    email      TEXT,
    -- SEGRETERIA | MANAGER | SOCIETA
    ruolo      TEXT NOT NULL,
    societa_id INTEGER REFERENCES societa(id),
    password   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS richieste (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    codice        TEXT,
    oggetto       TEXT NOT NULL,
    tipo          TEXT NOT NULL,
    cliente       TEXT,
    descrizione   TEXT,
    stato         TEXT NOT NULL DEFAULT 'RICEVUTA',
    data_arrivo   TEXT NOT NULL,
    scadenza_lavoro TEXT,
    pm_nome       TEXT,
    pm_societa_id INTEGER REFERENCES societa(id),
    note          TEXT
);

CREATE TABLE IF NOT EXISTS assegnazioni (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    richiesta_id  INTEGER NOT NULL REFERENCES richieste(id) ON DELETE CASCADE,
    societa_id    INTEGER NOT NULL REFERENCES societa(id),
    stato         TEXT NOT NULL DEFAULT 'INVIATA',
    ruolo         TEXT NOT NULL DEFAULT 'PARTNER',
    peso          REAL NOT NULL DEFAULT 1,
    data_invio    TEXT NOT NULL,
    scadenza_risposta TEXT NOT NULL,
    data_risposta TEXT,
    motivo_rifiuto TEXT,
    promemoria    INTEGER NOT NULL DEFAULT 0,
    UNIQUE (richiesta_id, societa_id)
);

CREATE TABLE IF NOT EXISTS eventi (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    richiesta_id INTEGER NOT NULL REFERENCES richieste(id) ON DELETE CASCADE,
    quando       TEXT NOT NULL,
    chi          TEXT,
    testo        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS outbox (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    quando             TEXT NOT NULL,
    destinatario       TEXT,
    destinatario_email TEXT,
    oggetto            TEXT,
    corpo              TEXT,
    richiesta_id       INTEGER,
    tipo               TEXT,
    inviata_smtp       INTEGER NOT NULL DEFAULT 0
);
"""


def init_db():
    """Crea le tabelle se non esistono e popola dati iniziali."""
    nuovo = not os.path.exists(DB_PATH)
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    if nuovo or conn.execute("SELECT COUNT(*) FROM societa").fetchone()[0] == 0:
        _seed_societa(conn)
    if conn.execute("SELECT COUNT(*) FROM utenti").fetchone()[0] == 0:
        _seed_utenti(conn)
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


def _seed_utenti(conn):
    """Crea gli utenti iniziali. Password = username (solo per il prototipo!)."""
    base = [
        ("segreteria", "Segreteria di rete", "segreteria@masterplan.it",
         RUOLO_SEGRETERIA, None),
        ("manager", "Manager di rete", "manager@masterplan.it",
         RUOLO_MANAGER, None),
    ]
    for username, nome, email, ruolo, sid in base:
        conn.execute(
            "INSERT INTO utenti (username, nome, email, ruolo, societa_id, password) "
            "VALUES (?,?,?,?,?,?)",
            (username, nome, email, ruolo, sid, security.hash_password(username)),
        )
    # Un utente per ogni società (il referente), username = prima parola del nome.
    for s in conn.execute("SELECT * FROM societa").fetchall():
        username = s["nome"].split()[0].lower()
        conn.execute(
            "INSERT INTO utenti (username, nome, email, ruolo, societa_id, password) "
            "VALUES (?,?,?,?,?,?)",
            (username, s["referente"] or s["nome"], s["email"],
             RUOLO_SOCIETA, s["id"], security.hash_password(username)),
        )
    conn.commit()


# --------------------------------------------------------------------------- #
# Utenti / autenticazione
# --------------------------------------------------------------------------- #
def utente_per_username(username):
    conn = get_conn()
    u = conn.execute(
        "SELECT * FROM utenti WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return u


def lista_credenziali_demo():
    """Per mostrare gli accessi di prova nella pagina di login."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT username, nome, ruolo FROM utenti ORDER BY "
        "CASE ruolo WHEN 'SEGRETERIA' THEN 0 WHEN 'MANAGER' THEN 1 ELSE 2 END, "
        "username"
    ).fetchall()
    conn.close()
    return rows


def _email_per_ruolo(conn, ruolo):
    return conn.execute(
        "SELECT nome, email FROM utenti WHERE ruolo=? AND email IS NOT NULL",
        (ruolo,),
    ).fetchall()


def _notifica_staff(conn, ruolo, oggetto, corpo, rid, tipo):
    for u in _email_per_ruolo(conn, ruolo):
        notif.invia(conn, u["nome"], u["email"], oggetto, corpo, rid, tipo)


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
    cur = conn.execute(
        "INSERT INTO societa (nome, referente, email, capacita) VALUES (?,?,?,?)",
        (nome, referente, email, float(capacita or 10)),
    )
    sid = cur.lastrowid
    # Crea anche l'utente referente della nuova società.
    username = nome.split()[0].lower() if nome.split() else ("societa%d" % sid)
    if not conn.execute("SELECT 1 FROM utenti WHERE username=?", (username,)).fetchone():
        conn.execute(
            "INSERT INTO utenti (username, nome, email, ruolo, societa_id, password) "
            "VALUES (?,?,?,?,?,?)",
            (username, referente or nome, email, RUOLO_SOCIETA, sid,
             security.hash_password(username)),
        )
    conn.commit()
    conn.close()


def carico_societa():
    """Per ogni società: carico attivo, % di saturazione, lavori attivi."""
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
    codice = "R-%s-%04d" % (datetime.now().year, rid)
    conn.execute("UPDATE richieste SET codice=? WHERE id=?", (codice, rid))
    log_evento(conn, rid, "Richiesta registrata dalla segreteria (%s)." % tipo, chi)
    # Notifica al manager di rete: c'è una nuova richiesta da smistare.
    _notifica_staff(
        conn, RUOLO_MANAGER,
        "[Masterplan] Nuova richiesta da smistare: %s" % codice,
        "È arrivata una nuova richiesta (%s) da \"%s\":\n\n%s\n\n%s\n\n"
        "Accedi a Masterplan per individuare le società da coinvolgere."
        % (tipo, cliente or "—", oggetto, descrizione or ""),
        rid, "nuova_richiesta",
    )
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
    """Il manager individua le società; la segreteria invia (notifica + 24h)."""
    conn = get_conn()
    r = conn.execute("SELECT * FROM richieste WHERE id=?", (rid,)).fetchone()
    scadenza = (now_dt() + timedelta(hours=ORE_PER_RISPOSTA)).isoformat(sep=" ")
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
            s = conn.execute(
                "SELECT nome, referente, email FROM societa WHERE id=?",
                (societa_id,),
            ).fetchone()
            nomi.append(s["nome"])
            # Notifica alla società coinvolta: deve rispondere entro 24h.
            notif.invia(
                conn, s["referente"] or s["nome"], s["email"],
                "[Masterplan] Richiesta di partecipazione: %s" % (r["codice"] or rid),
                "Gentile %s,\nla rete Masterplan vi propone il seguente lavoro (%s):\n\n"
                "%s\nCliente: %s\n\nVi chiediamo di confermare la disponibilità "
                "ENTRO 24 ORE (scadenza %s) accedendo a Masterplan.\n\n"
                "Cordiali saluti,\nSegreteria di rete"
                % (s["referente"] or s["nome"], r["tipo"], r["oggetto"],
                   r["cliente"] or "—", scadenza),
                rid, "invio_societa",
            )
        except sqlite3.IntegrityError:
            continue
    if nomi:
        conn.execute("UPDATE richieste SET stato='INVIATA' WHERE id=?", (rid,))
        log_evento(
            conn, rid,
            "Richiesta inviata a: %s. Risposta attesa entro 24h (%s)."
            % (", ".join(nomi), scadenza),
            chi,
        )
        _notifica_staff(
            conn, RUOLO_SEGRETERIA,
            "[Masterplan] Inviata richiesta %s" % (r["codice"] or rid),
            "La richiesta %s è stata inviata a: %s. Attesa risposta entro 24h."
            % (r["codice"] or rid, ", ".join(nomi)),
            rid, "invio_societa",
        )
    conn.commit()
    conn.close()


def rispondi_assegnazione(assegnazione_id, accetta, motivo, chi):
    """Una società accetta o rifiuta. Aggiorna stato e notifica lo staff."""
    conn = get_conn()
    a = conn.execute(
        "SELECT * FROM assegnazioni WHERE id=?", (assegnazione_id,)
    ).fetchone()
    if not a:
        conn.close()
        return
    rid = a["richiesta_id"]
    cod = conn.execute("SELECT codice FROM richieste WHERE id=?", (rid,)).fetchone()["codice"]
    societa = conn.execute(
        "SELECT nome FROM societa WHERE id=?", (a["societa_id"],)
    ).fetchone()["nome"]

    if accetta:
        conn.execute(
            "UPDATE assegnazioni SET stato='ACCETTATA', data_risposta=? WHERE id=?",
            (now_iso(), assegnazione_id),
        )
        log_evento(conn, rid, "%s ha ACCETTATO il lavoro." % societa, chi)
        r = conn.execute("SELECT stato FROM richieste WHERE id=?", (rid,)).fetchone()
        if r["stato"] in ("INVIATA", "RICEVUTA"):
            conn.execute("UPDATE richieste SET stato='ACCETTATA' WHERE id=?", (rid,))
        esito = "ha ACCETTATO"
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
        esito = "ha RIFIUTATO" + ((" (%s)" % motivo) if motivo else "")

    # Notifica a segreteria e manager dell'esito.
    for ruolo in (RUOLO_SEGRETERIA, RUOLO_MANAGER):
        _notifica_staff(
            conn, ruolo,
            "[Masterplan] %s: risposta da %s" % (cod, societa),
            "Per la richiesta %s, la società %s %s." % (cod, societa, esito),
            rid, "risposta_societa",
        )
    conn.commit()
    conn.close()


def _ricalcola_stato_negativo(conn, rid):
    righe = conn.execute(
        "SELECT stato FROM assegnazioni WHERE richiesta_id=?", (rid,)
    ).fetchall()
    if righe and all(x["stato"] in ("RIFIUTATA", "SCADUTA") for x in righe):
        r = conn.execute("SELECT stato, codice FROM richieste WHERE id=?", (rid,)).fetchone()
        if r["stato"] in ("INVIATA", "RICEVUTA"):
            conn.execute(
                "UPDATE richieste SET stato='CHIUSA_NEGATIVA' WHERE id=?", (rid,)
            )
            log_evento(
                conn, rid,
                "Nessuna società disponibile: richiesta chiusa con esito negativo.",
            )
            _notifica_staff(
                conn, RUOLO_MANAGER,
                "[Masterplan] %s chiusa senza disponibilità" % r["codice"],
                "Nessuna società ha dato disponibilità per la richiesta %s. "
                "Valutare un nuovo smistamento." % r["codice"],
                rid, "chiusa_negativa",
            )


def definisci_gruppo(rid, pm_nome, pm_societa_id, chi):
    """Il manager definisce il project manager e avvia il lavoro."""
    conn = get_conn()
    conn.execute(
        "UPDATE richieste SET pm_nome=?, pm_societa_id=?, stato='IN_CORSO' WHERE id=?",
        (pm_nome, pm_societa_id or None, rid),
    )
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
    cod = conn.execute("SELECT codice FROM richieste WHERE id=?", (rid,)).fetchone()["codice"]
    # Notifica al gruppo di lavoro (società che hanno accettato).
    membri = conn.execute(
        """SELECT s.nome, s.referente, s.email
           FROM assegnazioni a JOIN societa s ON s.id=a.societa_id
           WHERE a.richiesta_id=? AND a.stato='ACCETTATA'""",
        (rid,),
    ).fetchall()
    for m in membri:
        notif.invia(
            conn, m["referente"] or m["nome"], m["email"],
            "[Masterplan] %s: gruppo di lavoro avviato" % cod,
            "Il lavoro %s è stato avviato. Project Manager: %s%s.\n"
            "La vostra società fa parte del gruppo di lavoro."
            % (cod, pm_nome or "—", nome_soc),
            rid, "gruppo_avviato",
        )
    conn.commit()
    conn.close()


def completa_richiesta(rid, chi):
    conn = get_conn()
    conn.execute("UPDATE richieste SET stato='COMPLETATA' WHERE id=?", (rid,))
    log_evento(conn, rid, "Lavoro completato e archiviato.", chi)
    cod = conn.execute("SELECT codice FROM richieste WHERE id=?", (rid,)).fetchone()["codice"]
    _notifica_staff(
        conn, RUOLO_MANAGER,
        "[Masterplan] %s completata" % cod,
        "Il lavoro %s è stato completato e archiviato." % cod,
        rid, "completata",
    )
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------- #
# Scadenze e promemoria automatici (24h)
# --------------------------------------------------------------------------- #
def scadute_aggiorna():
    """Segna come SCADUTE le assegnazioni 'INVIATA' oltre le 24h e avvisa il manager."""
    conn = get_conn()
    adesso = now_iso()
    scadute = conn.execute(
        """SELECT a.id, a.richiesta_id, s.nome AS societa_nome, r.codice
           FROM assegnazioni a
           JOIN societa s ON s.id=a.societa_id
           JOIN richieste r ON r.id=a.richiesta_id
           WHERE a.stato='INVIATA' AND a.scadenza_risposta < ?""",
        (adesso,),
    ).fetchall()
    for a in scadute:
        conn.execute("UPDATE assegnazioni SET stato='SCADUTA' WHERE id=?", (a["id"],))
        log_evento(
            conn, a["richiesta_id"],
            "Termine di 24h scaduto senza risposta da %s." % a["societa_nome"],
        )
        _notifica_staff(
            conn, RUOLO_MANAGER,
            "[Masterplan] %s: termine 24h scaduto (%s)" % (a["codice"], a["societa_nome"]),
            "La società %s non ha risposto entro 24h per la richiesta %s."
            % (a["societa_nome"], a["codice"]),
            a["richiesta_id"], "scadenza",
        )
        _ricalcola_stato_negativo(conn, a["richiesta_id"])
    if scadute:
        conn.commit()
    conn.close()


def promemoria_aggiorna():
    """Invia un sollecito alle società quando mancano <= ORE_SOLLECITO alla scadenza."""
    conn = get_conn()
    limite = (now_dt() + timedelta(hours=ORE_SOLLECITO)).isoformat(sep=" ")
    adesso = now_iso()
    da_sollecitare = conn.execute(
        """SELECT a.id, a.richiesta_id, a.scadenza_risposta,
                  s.nome AS societa_nome, s.referente, s.email, r.codice, r.oggetto
           FROM assegnazioni a
           JOIN societa s ON s.id=a.societa_id
           JOIN richieste r ON r.id=a.richiesta_id
           WHERE a.stato='INVIATA' AND a.promemoria=0
             AND a.scadenza_risposta <= ? AND a.scadenza_risposta > ?""",
        (limite, adesso),
    ).fetchall()
    for a in da_sollecitare:
        conn.execute("UPDATE assegnazioni SET promemoria=1 WHERE id=?", (a["id"],))
        notif.invia(
            conn, a["referente"] or a["societa_nome"], a["email"],
            "[Masterplan] SOLLECITO — risposta in scadenza: %s" % a["codice"],
            "Gentile %s,\nvi ricordiamo che la richiesta %s (\"%s\") è in scadenza "
            "(%s). Vi chiediamo di confermare disponibilità o rifiuto al più presto.\n\n"
            "Segreteria di rete"
            % (a["referente"] or a["societa_nome"], a["codice"], a["oggetto"],
               a["scadenza_risposta"]),
            a["richiesta_id"], "sollecito",
        )
        log_evento(
            conn, a["richiesta_id"],
            "Sollecito automatico inviato a %s (scadenza vicina)." % a["societa_nome"],
        )
    if da_sollecitare:
        conn.commit()
    conn.close()


# --------------------------------------------------------------------------- #
# Outbox (posta inviata)
# --------------------------------------------------------------------------- #
def lista_outbox(limite=100):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM outbox ORDER BY id DESC LIMIT ?", (limite,)
    ).fetchall()
    conn.close()
    return rows


# --------------------------------------------------------------------------- #
# Statistiche / Report
# --------------------------------------------------------------------------- #
def statistiche():
    conn = get_conn()
    per_stato = {
        row["stato"]: row["n"]
        for row in conn.execute(
            "SELECT stato, COUNT(*) n FROM richieste GROUP BY stato"
        ).fetchall()
    }
    in_attesa = conn.execute(
        "SELECT COUNT(*) n FROM assegnazioni WHERE stato='INVIATA'"
    ).fetchone()["n"]
    conn.close()
    return {"per_stato": per_stato, "in_attesa": in_attesa}


def report():
    """Aggregati per la pagina Report e statistiche."""
    conn = get_conn()

    per_stato = conn.execute(
        "SELECT stato, COUNT(*) n FROM richieste GROUP BY stato"
    ).fetchall()
    per_tipo = conn.execute(
        "SELECT tipo, COUNT(*) n FROM richieste GROUP BY tipo ORDER BY n DESC"
    ).fetchall()
    per_cliente = conn.execute(
        "SELECT COALESCE(cliente,'(non indicato)') cliente, COUNT(*) n "
        "FROM richieste GROUP BY cliente ORDER BY n DESC LIMIT 10"
    ).fetchall()

    # Statistiche per società: invii, accettazioni, rifiuti, scadute, tempo medio.
    ass = conn.execute(
        """SELECT s.id, s.nome,
                  SUM(CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END) inviate,
                  SUM(CASE WHEN a.stato='ACCETTATA' THEN 1 ELSE 0 END) accettate,
                  SUM(CASE WHEN a.stato='RIFIUTATA' THEN 1 ELSE 0 END) rifiutate,
                  SUM(CASE WHEN a.stato='SCADUTA'   THEN 1 ELSE 0 END) scadute
           FROM societa s
           LEFT JOIN assegnazioni a ON a.societa_id=s.id
           GROUP BY s.id ORDER BY s.nome"""
    ).fetchall()

    # Tempo medio di risposta per società (in ore), calcolato in Python.
    tempi = {}
    rows = conn.execute(
        "SELECT societa_id, data_invio, data_risposta FROM assegnazioni "
        "WHERE data_risposta IS NOT NULL"
    ).fetchall()
    for r in rows:
        d0, d1 = _parse(r["data_invio"]), _parse(r["data_risposta"])
        if d0 and d1:
            ore = (d1 - d0).total_seconds() / 3600.0
            tempi.setdefault(r["societa_id"], []).append(ore)

    societa_stats = []
    tot_ore, tot_n = 0.0, 0
    for r in ass:
        lista = tempi.get(r["id"], [])
        medio = round(sum(lista) / len(lista), 1) if lista else None
        tot_ore += sum(lista)
        tot_n += len(lista)
        inviate = r["inviate"] or 0
        accettate = r["accettate"] or 0
        risposte = accettate + (r["rifiutate"] or 0)
        tasso = round(100 * accettate / risposte) if risposte else None
        societa_stats.append({
            "nome": r["nome"], "inviate": inviate, "accettate": accettate,
            "rifiutate": r["rifiutate"] or 0, "scadute": r["scadute"] or 0,
            "tasso": tasso, "tempo_medio": medio,
        })

    tempo_medio_globale = round(tot_ore / tot_n, 1) if tot_n else None
    totale_richieste = conn.execute("SELECT COUNT(*) n FROM richieste").fetchone()["n"]
    completate = conn.execute(
        "SELECT COUNT(*) n FROM richieste WHERE stato='COMPLETATA'"
    ).fetchone()["n"]
    conn.close()

    return {
        "per_stato": per_stato,
        "per_tipo": per_tipo,
        "per_cliente": per_cliente,
        "societa_stats": societa_stats,
        "tempo_medio_globale": tempo_medio_globale,
        "totale_richieste": totale_richieste,
        "completate": completate,
    }
