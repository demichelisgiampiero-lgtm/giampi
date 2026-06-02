#!/usr/bin/env python3
"""
Masterplan — gestione della rete di società di ingegneria.

Avvio:
    python3 app.py
poi apri il browser su  http://localhost:8000

Nessuna libreria esterna: usa solo Python 3 (http.server + sqlite3).
"""

import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import db
import views

PORT = 8000


class Handler(BaseHTTPRequestHandler):
    # --- utilità di risposta ------------------------------------------------ #
    def _html(self, contenuto, codice=200):
        body = contenuto.encode("utf-8")
        self.send_response(codice)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, dove):
        self.send_response(303)
        self.send_header("Location", dove)
        self.end_headers()

    def _post_data(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        # parse_qs ritorna liste; teniamo anche la versione "primo valore".
        multi = parse_qs(raw, keep_blank_values=True)
        single = {k: v[0] for k, v in multi.items()}
        return single, multi

    def log_message(self, *args):
        pass  # silenzia il log di default

    # --- GET ---------------------------------------------------------------- #
    def do_GET(self):
        db.scadute_aggiorna()  # tiene aggiornate le scadenze 24h a ogni pagina
        path = urlparse(self.path).path

        if path == "/":
            stats = db.statistiche()
            carichi = db.carico_societa()
            ultime = db.lista_richieste()[:8]
            return self._html(views.pagina_dashboard(stats, carichi, ultime))

        if path == "/richieste":
            return self._html(views.pagina_lista_richieste(db.lista_richieste()))

        if path == "/richieste/nuova":
            return self._html(views.pagina_nuova_richiesta())

        m = re.fullmatch(r"/richieste/(\d+)", path)
        if m:
            rid = int(m.group(1))
            r, ass, ev = db.get_richiesta(rid)
            if not r:
                return self._html(views.layout("Non trovata",
                    "<div class='card'>Richiesta non trovata.</div>"), 404)
            return self._html(
                views.pagina_dettaglio_richiesta(r, ass, ev, db.carico_societa()))

        if path == "/societa":
            return self._html(views.pagina_societa(db.carico_societa()))

        return self._html(views.layout("404",
            "<div class='card'>Pagina non trovata.</div>"), 404)

    # --- POST --------------------------------------------------------------- #
    def do_POST(self):
        path = urlparse(self.path).path
        single, multi = self._post_data()

        if path == "/richieste/nuova":
            rid = db.crea_richiesta(
                single.get("oggetto", "").strip(),
                single.get("tipo", "LAVORO"),
                single.get("cliente", "").strip(),
                single.get("descrizione", "").strip(),
                single.get("scadenza_lavoro", "").strip(),
                single.get("chi", "Segreteria"),
            )
            return self._redirect("/richieste/%d" % rid)

        m = re.fullmatch(r"/richieste/(\d+)/assegna", path)
        if m:
            rid = int(m.group(1))
            ids = multi.get("societa", [])
            societa_pesi = [
                (int(sid), single.get("peso_%s" % sid, "1")) for sid in ids
            ]
            if societa_pesi:
                db.assegna_societa(rid, societa_pesi, single.get("chi", "Segreteria"))
            return self._redirect("/richieste/%d" % rid)

        m = re.fullmatch(r"/assegnazioni/(\d+)/rispondi", path)
        if m:
            aid = int(m.group(1))
            accetta = single.get("esito") == "accetta"
            db.rispondi_assegnazione(
                aid, accetta, single.get("motivo", "").strip(),
                single.get("chi", "Società"))
            return self._redirect("/richieste/%s" % single.get("ric", ""))

        m = re.fullmatch(r"/richieste/(\d+)/gruppo", path)
        if m:
            rid = int(m.group(1))
            pm_soc = single.get("pm_societa_id")
            db.definisci_gruppo(
                rid, single.get("pm_nome", "").strip(),
                int(pm_soc) if pm_soc else None,
                single.get("chi", "Manager di rete"))
            return self._redirect("/richieste/%d" % rid)

        m = re.fullmatch(r"/richieste/(\d+)/completa", path)
        if m:
            rid = int(m.group(1))
            db.completa_richiesta(rid, single.get("chi", "Project Manager"))
            return self._redirect("/richieste/%d" % rid)

        if path == "/societa/nuova":
            nome = single.get("nome", "").strip()
            if nome:
                db.aggiungi_societa(
                    nome, single.get("referente", "").strip(),
                    single.get("email", "").strip(),
                    single.get("capacita", "10"))
            return self._redirect("/societa")

        return self._html("Not found", 404)


def main():
    db.init_db()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("Masterplan avviato su  http://localhost:%d" % PORT)
    print("Premi Ctrl+C per fermare.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArresto.")
        server.shutdown()


if __name__ == "__main__":
    main()
