"""
Funzioni di sicurezza per le password (solo libreria standard).

Le password non vengono mai salvate in chiaro: usiamo PBKDF2-HMAC-SHA256 con
sale casuale. Modulo volutamente isolato (non importa db né auth) per evitare
dipendenze circolari.
"""

import hashlib
import hmac
import os

_ITERAZIONI = 120_000


def hash_password(password: str) -> str:
    """Ritorna una stringa 'sale$hash' da salvare nel database."""
    sale = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sale, _ITERAZIONI)
    return "%s$%s" % (sale.hex(), dk.hex())


def verifica_password(password: str, salvato: str) -> bool:
    """Verifica una password contro il valore 'sale$hash' salvato."""
    try:
        sale_hex, hash_hex = salvato.split("$", 1)
        sale = bytes.fromhex(sale_hex)
        atteso = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sale, _ITERAZIONI)
    return hmac.compare_digest(dk, atteso)
