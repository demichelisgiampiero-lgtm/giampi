"""
Autenticazione e sessioni per Masterplan (solo libreria standard).

Sessioni tenute in memoria (un dizionario token -> utente): semplici e
sufficienti per il prototipo. Al riavvio del server gli utenti dovranno
rifare l'accesso. Le password sono verificate con il modulo `security`.
"""

import secrets

import db
import security

COOKIE = "mp_session"

# token -> dict utente { id, username, nome, ruolo, societa_id }
_sessioni = {}


def login(username, password):
    """Verifica le credenziali e crea una sessione. Ritorna il token o None."""
    u = db.utente_per_username((username or "").strip().lower())
    if not u or not security.verifica_password(password or "", u["password"]):
        return None
    token = secrets.token_hex(24)
    _sessioni[token] = {
        "id": u["id"], "username": u["username"], "nome": u["nome"],
        "ruolo": u["ruolo"], "societa_id": u["societa_id"],
    }
    return token


def logout(token):
    _sessioni.pop(token, None)


def utente_da_token(token):
    return _sessioni.get(token) if token else None


# Helper sui ruoli ---------------------------------------------------------- #
def is_staff(utente):
    """Segreteria o manager (chi gestisce il flusso lato rete)."""
    return bool(utente) and utente["ruolo"] in (db.RUOLO_SEGRETERIA, db.RUOLO_MANAGER)


def is_manager(utente):
    return bool(utente) and utente["ruolo"] == db.RUOLO_MANAGER


def is_segreteria(utente):
    return bool(utente) and utente["ruolo"] == db.RUOLO_SEGRETERIA


def is_societa(utente):
    return bool(utente) and utente["ruolo"] == db.RUOLO_SOCIETA


def puo_rispondere(utente, assegnazione_societa_id):
    """Una società può rispondere solo alle proprie assegnazioni; lo staff a tutte."""
    if is_staff(utente):
        return True
    return is_societa(utente) and utente["societa_id"] == assegnazione_societa_id
