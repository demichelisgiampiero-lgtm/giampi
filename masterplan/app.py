#!/usr/bin/env python3
"""
Masterplan — gestione della rete di società di ingegneria.

Avvio:
    python3 app.py
poi apri il browser su  http://localhost:8000

Funzioni: registrazione richieste, smistamento del manager di rete, invio alle
società con risposta entro 24h, gruppo di lavoro e project manager, controllo
del carico, login per ruoli, notifiche email, promemoria automatici e report.

Nessuna libreria esterna: solo Python 3 (http.server + sqlite3 + smtplib).
Per inviare email reali configura le variabili d'ambiente MP_SMTP_* (vedi README).
"""

import re
import threading
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import auth
import db
import notifications
import views

PORT = 8000
# Ogni quanti secondi il processo in background controlla scadenze e solleciti.
INTERVALLO_CONTROLLO = 60

# Percorsi accessibili senza login.
PUBBLICI = {"/login"}


class Handler(BaseHTTPRequestHandler):
    # --- utilità di risposta ------------------------------------------------ #
    def _html(self, contenuto, codice=200, set_cookie=None):
        body = contenuto.encode("utf-8")
        self.send_response(codice)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, dove, set_cookie=None):
        self.send_response(303)
        self.send_header("Location", dove)
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.end_headers()

    def _nega(self):
        self._html(views.layout(
            "Accesso negato",
            "<div class='card'><h2>Operazione non consentita</h2>"
            "<p class='muted'>Il tuo ruolo non permette questa azione.</p>"
            "<a class='btn btn-secondary' href='/'>Torna al cruscotto</a></div>",
            utente=self.utente), 403)

    def _post_data(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        multi = parse_qs(raw, keep_blank_values=True)
        single = {k: v[0] for k, v in multi.items()}
        return single, multi

    def _token(self):
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        morsel = cookie.get(auth.COOKIE)
        return morsel.value if morsel else None

    def _autentica(self):
        """Imposta self.utente. Ritorna True se la richiesta può proseguire."""
        self.utente = auth.utente_da_token(self._token())
        return self.utente is not None

    def log_message(self, *args):
        pass

    # --- GET ---------------------------------------------------------------- #
    def do_GET(self):
        path = urlparse(self.path).path
        loggato = self._autentica()

        if path == "/login":
            if loggato:
                return self._redirect("/")
            return self._html(views.pagina_login(db.lista_credenziali_demo()))

        if path == "/logout":
            auth.logout(self._token())
            scaduto = "%s=; Path=/; Max-Age=0" % auth.COOKIE
            return self._redirect("/login", set_cookie=scaduto)

        if not loggato:
            return self._redirect("/login")

        # Da qui in poi l'utente è autenticato. Aggiorna scadenze/solleciti.
        db.scadute_aggiorna()
        db.promemoria_aggiorna()

        if path == "/":
            return self._html(views.pagina_dashboard(
                db.statistiche(), db.carico_societa(),
                db.lista_richieste()[:8], self.utente))

        if path == "/richieste":
            return self._html(views.pagina_lista_richieste(
                db.lista_richieste(), self.utente))

        if path == "/richieste/nuova":
            if not auth.is_staff(self.utente):
                return self._nega()
            return self._html(views.pagina_nuova_richiesta(self.utente))

        m = re.fullmatch(r"/richieste/(\d+)", path)
        if m:
            rid = int(m.group(1))
            r, ass, ev = db.get_richiesta(rid)
            if not r:
                return self._html(views.layout("Non trovata",
                    "<div class='card'>Richiesta non trovata.</div>",
                    utente=self.utente), 404)
            return self._html(views.pagina_dettaglio_richiesta(
                r, ass, ev, db.carico_societa(), self.utente))

        if path == "/societa":
            return self._html(views.pagina_societa(db.carico_societa(), self.utente))

        if path == "/report":
            if not auth.is_staff(self.utente):
                return self._nega()
            return self._html(views.pagina_report(db.report(), self.utente))

        if path == "/outbox":
            if not auth.is_staff(self.utente):
                return self._nega()
            return self._html(views.pagina_outbox(
                db.lista_outbox(), notifications.smtp_configurato(), self.utente))

        return self._html(views.layout("404",
            "<div class='card'>Pagina non trovata.</div>", utente=self.utente), 404)

    # --- POST --------------------------------------------------------------- #
    def do_POST(self):
        path = urlparse(self.path).path
        single, multi = self._post_data()

        if path == "/login":
            token = auth.login(single.get("username", ""), single.get("password", ""))
            if not token:
                return self._html(views.pagina_login(
                    db.lista_credenziali_demo(),
                    "Nome utente o password non validi."), 401)
            cookie = "%s=%s; Path=/; HttpOnly; SameSite=Lax" % (auth.COOKIE, token)
            return self._redirect("/", set_cookie=cookie)

        if not self._autentica():
            return self._redirect("/login")

        if path == "/richieste/nuova":
            if not auth.is_staff(self.utente):
                return self._nega()
            rid = db.crea_richiesta(
                single.get("oggetto", "").strip(),
                single.get("tipo", "LAVORO"),
                single.get("cliente", "").strip(),
                single.get("descrizione", "").strip(),
                single.get("scadenza_lavoro", "").strip(),
                self.utente["nome"])
            return self._redirect("/richieste/%d" % rid)

        m = re.fullmatch(r"/richieste/(\d+)/assegna", path)
        if m:
            if not auth.is_staff(self.utente):
                return self._nega()
            rid = int(m.group(1))
            ids = multi.get("societa", [])
            societa_pesi = [
                (int(sid), single.get("peso_%s" % sid, "1")) for sid in ids
            ]
            if societa_pesi:
                db.assegna_societa(rid, societa_pesi, self.utente["nome"])
            return self._redirect("/richieste/%d" % rid)

        m = re.fullmatch(r"/assegnazioni/(\d+)/rispondi", path)
        if m:
            aid = int(m.group(1))
            # Verifica che l'utente possa rispondere a QUESTA assegnazione.
            societa_id = db.get_conn().execute(
                "SELECT societa_id FROM assegnazioni WHERE id=?", (aid,)
            ).fetchone()
            if societa_id is None or not auth.puo_rispondere(
                    self.utente, societa_id["societa_id"]):
                return self._nega()
            accetta = single.get("esito") == "accetta"
            db.rispondi_assegnazione(
                aid, accetta, single.get("motivo", "").strip(), self.utente["nome"])
            return self._redirect("/richieste/%s" % single.get("ric", ""))

        m = re.fullmatch(r"/richieste/(\d+)/gruppo", path)
        if m:
            if not auth.is_manager(self.utente):
                return self._nega()
            rid = int(m.group(1))
            pm_soc = single.get("pm_societa_id")
            db.definisci_gruppo(
                rid, single.get("pm_nome", "").strip(),
                int(pm_soc) if pm_soc else None, self.utente["nome"])
            return self._redirect("/richieste/%d" % rid)

        m = re.fullmatch(r"/richieste/(\d+)/completa", path)
        if m:
            if not auth.is_staff(self.utente):
                return self._nega()
            rid = int(m.group(1))
            db.completa_richiesta(rid, self.utente["nome"])
            return self._redirect("/richieste/%d" % rid)

        if path == "/societa/nuova":
            if not auth.is_staff(self.utente):
                return self._nega()
            nome = single.get("nome", "").strip()
            if nome:
                db.aggiungi_societa(
                    nome, single.get("referente", "").strip(),
                    single.get("email", "").strip(),
                    single.get("capacita", "10"))
            return self._redirect("/societa")

        return self._html("Not found", 404)


def _controllo_periodico():
    """Thread in background: solleciti e scadenze 24h anche senza traffico web."""
    while True:
        time.sleep(INTERVALLO_CONTROLLO)
        try:
            db.scadute_aggiorna()
            db.promemoria_aggiorna()
        except Exception as exc:
            print("[promemoria] errore:", exc)


def main():
    db.init_db()
    threading.Thread(target=_controllo_periodico, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    modo = "INVIO REALE (SMTP)" if notifications.smtp_configurato() else "SIMULAZIONE email"
    print("Masterplan avviato su  http://localhost:%d" % PORT)
    print("Notifiche:", modo, "— vedi pagina 'Posta inviata'.")
    print("Accessi di prova: segreteria/segreteria · manager/manager · alfa/alfa ...")
    print("Premi Ctrl+C per fermare.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArresto.")
        server.shutdown()


if __name__ == "__main__":
    main()
