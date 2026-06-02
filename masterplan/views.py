"""
Rendering HTML per Masterplan (nessun motore di template esterno).

Ogni funzione restituisce una stringa HTML. Il layout di base contiene il CSS
in linea, così non serve servire file statici.
"""

import html

# Etichette leggibili e colori per gli stati delle richieste.
STATI_RICHIESTA = {
    "RICEVUTA":        ("Ricevuta",        "#6c757d"),
    "INVIATA":         ("Inviata (attesa risposta)", "#0d6efd"),
    "ACCETTATA":       ("Accettata",       "#198754"),
    "IN_CORSO":        ("In corso",        "#6610f2"),
    "COMPLETATA":      ("Completata",      "#20c997"),
    "CHIUSA_NEGATIVA": ("Chiusa negativa", "#dc3545"),
}
STATI_ASSEGNAZIONE = {
    "INVIATA":   ("In attesa", "#0d6efd"),
    "ACCETTATA": ("Accettata", "#198754"),
    "RIFIUTATA": ("Rifiutata", "#dc3545"),
    "SCADUTA":   ("Scaduta",   "#fd7e14"),
}
TIPI = {"GARA": "Gara", "LAVORO": "Lavoro specifico", "CONSULENZA": "Consulenza"}


def e(s):
    return html.escape(str(s if s is not None else ""))


def badge(testo, colore):
    return (
        '<span style="background:%s;color:#fff;padding:2px 9px;border-radius:12px;'
        'font-size:12px;white-space:nowrap">%s</span>' % (colore, e(testo))
    )


def badge_stato_richiesta(stato):
    etichetta, colore = STATI_RICHIESTA.get(stato, (stato, "#6c757d"))
    return badge(etichetta, colore)


def badge_stato_assegnazione(stato):
    etichetta, colore = STATI_ASSEGNAZIONE.get(stato, (stato, "#6c757d"))
    return badge(etichetta, colore)


def barra_saturazione(perc):
    if perc < 70:
        colore = "#198754"
    elif perc < 100:
        colore = "#fd7e14"
    else:
        colore = "#dc3545"
    larghezza = min(perc, 100)
    return (
        '<div class="bar"><div class="bar-fill" style="width:%d%%;background:%s">'
        '</div></div><span class="bar-label">%d%%</span>' % (larghezza, colore, perc)
    )


CSS = """
* { box-sizing: border-box; }
body { font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
       margin: 0; background: #f4f6f9; color: #1f2733; }
header { background: #0b2545; color: #fff; padding: 14px 26px;
         display: flex; align-items: center; gap: 26px; }
header h1 { font-size: 20px; margin: 0; letter-spacing: .5px; }
header nav a { color: #cfe0ff; text-decoration: none; margin-right: 18px; font-size: 15px; }
header nav a:hover { color: #fff; }
.container { max-width: 1100px; margin: 26px auto; padding: 0 20px; }
.card { background: #fff; border-radius: 10px; padding: 20px 22px; margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,.08); }
h2 { margin-top: 0; font-size: 19px; }
h3 { font-size: 16px; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 9px 10px; border-bottom: 1px solid #eef1f5; font-size: 14px; vertical-align: top; }
th { color: #6b7686; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: .4px; }
tr:hover td { background: #fafbfc; }
a { color: #0d6efd; }
.btn { display: inline-block; background: #0d6efd; color: #fff; border: none; padding: 9px 16px;
       border-radius: 7px; cursor: pointer; text-decoration: none; font-size: 14px; }
.btn:hover { background: #0b5ed7; }
.btn-secondary { background: #e9eef5; color: #1f2733; }
.btn-secondary:hover { background: #dde4ee; }
.btn-success { background: #198754; } .btn-success:hover { background: #157347; }
.btn-danger { background: #dc3545; } .btn-danger:hover { background: #bb2d3b; }
.btn-sm { padding: 5px 10px; font-size: 13px; }
input, select, textarea { width: 100%; padding: 9px 10px; border: 1px solid #cfd6e0;
       border-radius: 7px; font-size: 14px; font-family: inherit; }
label { display: block; font-size: 13px; font-weight: 600; margin: 12px 0 5px; color: #46505f; }
.row { display: flex; gap: 16px; flex-wrap: wrap; }
.row > div { flex: 1; min-width: 200px; }
.stat-grid { display: flex; gap: 16px; flex-wrap: wrap; }
.stat { background: #fff; border-radius: 10px; padding: 16px 20px; flex: 1; min-width: 140px;
        box-shadow: 0 1px 3px rgba(0,0,0,.08); }
.stat .num { font-size: 30px; font-weight: 700; }
.stat .lbl { color: #6b7686; font-size: 13px; }
.bar { display: inline-block; width: 120px; height: 10px; background: #eef1f5;
       border-radius: 6px; overflow: hidden; vertical-align: middle; }
.bar-fill { height: 100%; }
.bar-label { font-size: 13px; margin-left: 8px; color: #46505f; }
.muted { color: #8a94a3; font-size: 13px; }
.timeline { list-style: none; padding-left: 0; }
.timeline li { padding: 7px 0 7px 16px; border-left: 2px solid #dfe5ec; margin-left: 6px; position: relative; }
.timeline li::before { content:''; position:absolute; left:-6px; top:12px; width:10px; height:10px;
       background:#0d6efd; border-radius:50%; }
.flash { background:#d1e7dd; border:1px solid #a3cfbb; color:#0f5132; padding:12px 16px;
       border-radius:8px; margin-bottom:18px; }
.checkrow { display:flex; align-items:center; gap:10px; padding:7px 0; border-bottom:1px solid #f0f2f5; }
.checkrow input[type=checkbox] { width:auto; }
.checkrow .peso { width:90px; }
.pill { background:#eef1f5; padding:2px 9px; border-radius:10px; font-size:12px; }
"""


def layout(titolo, contenuto, flash=None):
    flash_html = ('<div class="flash">%s</div>' % e(flash)) if flash else ""
    return """<!doctype html>
<html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titolo} · Masterplan</title><style>{css}</style></head>
<body>
<header>
  <h1>🛰️ MASTERPLAN</h1>
  <nav>
    <a href="/">Cruscotto</a>
    <a href="/richieste">Richieste</a>
    <a href="/richieste/nuova">+ Nuova richiesta</a>
    <a href="/societa">Società della rete</a>
  </nav>
</header>
<div class="container">{flash}{contenuto}</div>
</body></html>""".format(
        titolo=e(titolo), css=CSS, flash=flash_html, contenuto=contenuto
    )


# --------------------------------------------------------------------------- #
# Pagine
# --------------------------------------------------------------------------- #
def pagina_dashboard(stats, carichi, ultime):
    ps = stats["per_stato"]
    aperte = ps.get("RICEVUTA", 0) + ps.get("INVIATA", 0) + \
        ps.get("ACCETTATA", 0) + ps.get("IN_CORSO", 0)
    cards = """
    <div class="stat-grid">
      <div class="stat"><div class="num">%d</div><div class="lbl">Richieste aperte</div></div>
      <div class="stat"><div class="num" style="color:#0d6efd">%d</div><div class="lbl">In attesa risposta (24h)</div></div>
      <div class="stat"><div class="num" style="color:#6610f2">%d</div><div class="lbl">Lavori in corso</div></div>
      <div class="stat"><div class="num" style="color:#20c997">%d</div><div class="lbl">Completate</div></div>
    </div>
    """ % (aperte, stats["in_attesa"], ps.get("IN_CORSO", 0), ps.get("COMPLETATA", 0))

    # Tabella carico società
    righe_carico = ""
    for c in carichi:
        righe_carico += (
            "<tr><td><a href='/societa'>%s</a></td><td>%.0f / %.0f</td>"
            "<td>%s</td><td>%d</td></tr>"
            % (e(c["nome"]), c["carico"], c["capacita"],
               barra_saturazione(c["saturazione"]), c["lavori_attivi"])
        )
    tab_carico = """
    <div class="card"><h2>Carico di lavoro della rete</h2>
    <table><tr><th>Società</th><th>Carico</th><th>Saturazione</th><th>Lavori attivi</th></tr>
    %s</table></div>""" % righe_carico

    # Ultime richieste
    righe_ult = ""
    for r in ultime:
        righe_ult += (
            "<tr><td><a href='/richieste/%d'>%s</a></td><td>%s</td>"
            "<td>%s</td><td>%s</td><td>%s</td></tr>"
            % (r["id"], e(r["codice"] or r["id"]), e(r["oggetto"]),
               e(TIPI.get(r["tipo"], r["tipo"])), badge_stato_richiesta(r["stato"]),
               e(r["data_arrivo"]))
        )
    if not righe_ult:
        righe_ult = "<tr><td colspan='5' class='muted'>Nessuna richiesta. Inizia da “Nuova richiesta”.</td></tr>"
    tab_ult = """
    <div class="card"><h2>Ultime richieste</h2>
    <table><tr><th>Codice</th><th>Oggetto</th><th>Tipo</th><th>Stato</th><th>Arrivo</th></tr>
    %s</table></div>""" % righe_ult

    contenuto = '<div class="card">%s</div>%s%s' % (cards, tab_carico, tab_ult)
    return layout("Cruscotto", contenuto)


def pagina_lista_richieste(richieste):
    righe = ""
    for r in richieste:
        righe += (
            "<tr><td><a href='/richieste/%d'>%s</a></td><td>%s</td><td>%s</td>"
            "<td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (r["id"], e(r["codice"] or r["id"]), e(r["oggetto"]),
               e(TIPI.get(r["tipo"], r["tipo"])), e(r["cliente"] or "—"),
               badge_stato_richiesta(r["stato"]),
               e(r["pm_nome"] or "—"), e(r["data_arrivo"]))
        )
    if not righe:
        righe = "<tr><td colspan='7' class='muted'>Nessuna richiesta.</td></tr>"
    contenuto = """
    <div class="card">
      <h2>Richieste <a class="btn btn-sm" style="float:right" href="/richieste/nuova">+ Nuova</a></h2>
      <table>
        <tr><th>Codice</th><th>Oggetto</th><th>Tipo</th><th>Cliente</th>
            <th>Stato</th><th>Project Manager</th><th>Arrivo</th></tr>
        %s
      </table>
    </div>""" % righe
    return layout("Richieste", contenuto)


def pagina_nuova_richiesta():
    opzioni_tipo = "".join(
        '<option value="%s">%s</option>' % (k, v) for k, v in TIPI.items()
    )
    contenuto = """
    <div class="card">
      <h2>Nuova richiesta (registrazione segreteria)</h2>
      <form method="post" action="/richieste/nuova">
        <label>Oggetto della richiesta *</label>
        <input name="oggetto" required placeholder="Es. Progettazione ponte ciclopedonale">
        <div class="row">
          <div><label>Tipo *</label><select name="tipo">%s</select></div>
          <div><label>Cliente / Ente richiedente</label><input name="cliente"></div>
          <div><label>Scadenza del lavoro</label><input type="date" name="scadenza_lavoro"></div>
        </div>
        <label>Descrizione / dettagli</label>
        <textarea name="descrizione" rows="4" placeholder="Riferimenti email, importo, requisiti..."></textarea>
        <label>Registrata da</label>
        <input name="chi" value="Segreteria di rete">
        <p style="margin-top:18px">
          <button class="btn" type="submit">Registra richiesta</button>
          <a class="btn btn-secondary" href="/richieste">Annulla</a>
        </p>
      </form>
    </div>""" % opzioni_tipo
    return layout("Nuova richiesta", contenuto)


def _box_assegna(r, societa_carichi, assegnate_ids):
    """Form con cui il manager di rete individua le società."""
    righe = ""
    for c in societa_carichi:
        if c["id"] in assegnate_ids or not c["attiva"]:
            continue
        righe += """
        <div class="checkrow">
          <input type="checkbox" name="societa" value="%d" id="s%d">
          <label for="s%d" style="margin:0;flex:1">%s
            <span class="muted">— carico %.0f/%.0f (%d%%)</span></label>
          <input class="peso" type="number" step="0.5" min="0.5" name="peso_%d"
                 value="1" title="Peso/carico stimato">
        </div>""" % (c["id"], c["id"], c["id"], e(c["nome"]),
                     c["carico"], c["capacita"], c["saturazione"], c["id"])
    if not righe:
        righe = "<p class='muted'>Tutte le società attive sono già state coinvolte.</p>"
    return """
    <div class="card">
      <h3>Assegna a società (decisione manager di rete)</h3>
      <p class="muted">Seleziona le società da coinvolgere e il peso stimato del lavoro.
         La segreteria invia la richiesta: avranno 24h per rispondere.</p>
      <form method="post" action="/richieste/%d/assegna">
        %s
        <label>Inviata da</label>
        <input name="chi" value="Segreteria di rete">
        <p style="margin-top:14px"><button class="btn" type="submit">Invia alle società selezionate</button></p>
      </form>
    </div>""" % (r["id"], righe)


def _box_gruppo(r, assegnazioni):
    """Form per definire il project manager (solo se c'è almeno un'accettazione)."""
    accettate = [a for a in assegnazioni if a["stato"] == "ACCETTATA"]
    if not accettate:
        return ""
    opzioni = "".join(
        '<option value="%d">%s</option>' % (a["societa_id"], e(a["societa_nome"]))
        for a in accettate
    )
    return """
    <div class="card">
      <h3>Definisci gruppo di lavoro e Project Manager</h3>
      <form method="post" action="/richieste/%d/gruppo">
        <div class="row">
          <div><label>Nome Project Manager</label><input name="pm_nome" placeholder="Es. Ing. Rossi"></div>
          <div><label>Società del PM (capofila)</label><select name="pm_societa_id">%s</select></div>
        </div>
        <label>Definito da</label>
        <input name="chi" value="Manager di rete">
        <p style="margin-top:14px"><button class="btn btn-success" type="submit">Avvia il lavoro</button></p>
      </form>
    </div>""" % (r["id"], opzioni)


def pagina_dettaglio_richiesta(r, assegnazioni, eventi, societa_carichi):
    assegnate_ids = {a["societa_id"] for a in assegnazioni}

    # Riepilogo assegnazioni con azioni di risposta
    righe_ass = ""
    for a in assegnazioni:
        azioni = ""
        if a["stato"] == "INVIATA":
            azioni = """
            <form method="post" action="/assegnazioni/%d/rispondi" style="display:flex;gap:6px;align-items:center">
              <input type="hidden" name="ric" value="%d">
              <input name="motivo" placeholder="motivo (se rifiuto)" style="width:160px">
              <button class="btn btn-success btn-sm" name="esito" value="accetta">Accetta</button>
              <button class="btn btn-danger btn-sm" name="esito" value="rifiuta">Rifiuta</button>
            </form>""" % (a["id"], r["id"])
        elif a["stato"] == "RIFIUTATA" and a["motivo_rifiuto"]:
            azioni = "<span class='muted'>%s</span>" % e(a["motivo_rifiuto"])
        ruolo = badge("Capofila", "#0b2545") if a["ruolo"] == "CAPOFILA" else \
            "<span class='pill'>Partner</span>"
        righe_ass += (
            "<tr><td>%s %s</td><td>%s</td><td>%.1f</td><td>%s</td>"
            "<td class='muted'>%s</td><td>%s</td></tr>"
            % (e(a["societa_nome"]), ruolo, badge_stato_assegnazione(a["stato"]),
               a["peso"], e(a["scadenza_risposta"]),
               e(a["data_risposta"] or "—"), azioni)
        )
    box_assegnazioni = ""
    if righe_ass:
        box_assegnazioni = """
        <div class="card"><h3>Società coinvolte</h3>
        <table><tr><th>Società</th><th>Stato</th><th>Peso</th><th>Scadenza 24h</th>
        <th>Risposta</th><th>Azione</th></tr>%s</table></div>""" % righe_ass

    # Box assegnazione (se ancora in fase di smistamento)
    box_assegna = ""
    if r["stato"] in ("RICEVUTA", "INVIATA"):
        box_assegna = _box_assegna(r, societa_carichi, assegnate_ids)

    box_gruppo = _box_gruppo(r, assegnazioni) if r["stato"] == "ACCETTATA" else ""

    # Azione completamento
    box_completa = ""
    if r["stato"] == "IN_CORSO":
        box_completa = """
        <div class="card"><form method="post" action="/richieste/%d/completa">
          <input name="chi" type="hidden" value="Project Manager">
          <button class="btn btn-secondary">✓ Segna come completata</button>
        </form></div>""" % r["id"]

    # Timeline eventi
    eventi_html = "".join(
        "<li><strong>%s</strong> — %s <span class='muted'>(%s)</span></li>"
        % (e(ev["quando"]), e(ev["testo"]), e(ev["chi"])) for ev in eventi
    )
    box_eventi = """
    <div class="card"><h3>Tracciabilità (storia della richiesta)</h3>
    <ul class="timeline">%s</ul></div>""" % eventi_html

    pm = "—"
    if r["pm_nome"] or r["pm_societa_nome"]:
        pm = e(r["pm_nome"] or "") + (
            " (%s)" % e(r["pm_societa_nome"]) if r["pm_societa_nome"] else "")

    intestazione = """
    <div class="card">
      <h2>%s &nbsp; %s</h2>
      <p class="muted">%s</p>
      <div class="row">
        <div><strong>Tipo:</strong> %s</div>
        <div><strong>Cliente:</strong> %s</div>
        <div><strong>Arrivo:</strong> %s</div>
        <div><strong>Scadenza lavoro:</strong> %s</div>
        <div><strong>Project Manager:</strong> %s</div>
      </div>
      %s
    </div>""" % (
        e(r["codice"] or r["id"]), badge_stato_richiesta(r["stato"]),
        e(r["oggetto"]),
        e(TIPI.get(r["tipo"], r["tipo"])), e(r["cliente"] or "—"),
        e(r["data_arrivo"]), e(r["scadenza_lavoro"] or "—"), pm,
        ("<p style='margin-top:14px'>%s</p>" % e(r["descrizione"])) if r["descrizione"] else "",
    )

    contenuto = (intestazione + box_assegna + box_assegnazioni +
                 box_gruppo + box_completa + box_eventi)
    return layout("Richiesta %s" % (r["codice"] or r["id"]), contenuto)


def pagina_societa(carichi):
    righe = ""
    for c in carichi:
        stato = "attiva" if c["attiva"] else "non attiva"
        righe += (
            "<tr><td><strong>%s</strong></td><td>%s</td><td>%s</td>"
            "<td>%.0f</td><td>%s</td><td>%d</td></tr>"
            % (e(c["nome"]), e(c["referente"] or "—"), e(c["email"] or "—"),
               c["capacita"], barra_saturazione(c["saturazione"]), c["lavori_attivi"])
        )
    contenuto = """
    <div class="card">
      <h2>Società della rete</h2>
      <table>
        <tr><th>Società</th><th>Referente</th><th>Email</th>
            <th>Capacità</th><th>Saturazione</th><th>Lavori attivi</th></tr>
        %s
      </table>
    </div>
    <div class="card">
      <h3>Aggiungi società</h3>
      <form method="post" action="/societa/nuova">
        <div class="row">
          <div><label>Nome *</label><input name="nome" required></div>
          <div><label>Referente</label><input name="referente"></div>
          <div><label>Email</label><input name="email" type="email"></div>
          <div><label>Capacità (punti)</label><input name="capacita" type="number" step="1" value="10"></div>
        </div>
        <p style="margin-top:14px"><button class="btn" type="submit">Aggiungi</button></p>
      </form>
    </div>""" % righe
    return layout("Società", contenuto)
