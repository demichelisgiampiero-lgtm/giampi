"""
Strato di notifica email di Masterplan (solo libreria standard).

Ogni messaggio viene SEMPRE registrato nella tabella `outbox` (la "Posta
inviata", consultabile dall'interfaccia). Se è configurato un server SMTP
tramite variabili d'ambiente, il messaggio viene anche spedito davvero.

Variabili d'ambiente per l'invio reale (tutte opzionali):
    MP_SMTP_HOST   host del server SMTP (se assente -> solo simulazione)
    MP_SMTP_PORT   porta (default 587)
    MP_SMTP_USER   utente
    MP_SMTP_PASS   password
    MP_SMTP_FROM   mittente (default "Masterplan <noreply@masterplan.it>")
    MP_SMTP_TLS    "1" per usare STARTTLS (default "1")

Il modulo è isolato: riceve una connessione DB e non importa db/auth.
"""

import os
import smtplib
from datetime import datetime
from email.message import EmailMessage


def _now():
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def smtp_configurato() -> bool:
    return bool(os.environ.get("MP_SMTP_HOST"))


def _invia_smtp(email_dest: str, oggetto: str, corpo: str) -> bool:
    """Invio reale via SMTP. Ritorna True se spedito, False altrimenti."""
    host = os.environ.get("MP_SMTP_HOST")
    if not host or not email_dest:
        return False
    porta = int(os.environ.get("MP_SMTP_PORT", "587"))
    mittente = os.environ.get("MP_SMTP_FROM", "Masterplan <noreply@masterplan.it>")
    msg = EmailMessage()
    msg["From"] = mittente
    msg["To"] = email_dest
    msg["Subject"] = oggetto
    msg.set_content(corpo)
    try:
        with smtplib.SMTP(host, porta, timeout=15) as s:
            if os.environ.get("MP_SMTP_TLS", "1") == "1":
                s.starttls()
            utente = os.environ.get("MP_SMTP_USER")
            if utente:
                s.login(utente, os.environ.get("MP_SMTP_PASS", ""))
            s.send_message(msg)
        return True
    except Exception as exc:  # in un prototipo non vogliamo bloccare il flusso
        print("[notifiche] invio SMTP fallito:", exc)
        return False


def invia(conn, destinatario_nome, destinatario_email, oggetto, corpo,
          richiesta_id=None, tipo="generico"):
    """
    Registra il messaggio nella outbox e prova l'invio SMTP se configurato.
    """
    inviata = _invia_smtp(destinatario_email, oggetto, corpo)
    conn.execute(
        """INSERT INTO outbox
           (quando, destinatario, destinatario_email, oggetto, corpo,
            richiesta_id, tipo, inviata_smtp)
           VALUES (?,?,?,?,?,?,?,?)""",
        (_now(), destinatario_nome, destinatario_email, oggetto, corpo,
         richiesta_id, tipo, 1 if inviata else 0),
    )
