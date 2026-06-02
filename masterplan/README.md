# Masterplan — Gestione rete di società di ingegneria

Prototipo per gestire il flusso di lavoro della rete **Masterplan**: dall'arrivo
di una richiesta (mail / telefonata) fino all'assegnazione del lavoro a una o più
società della rete, con tracciamento del carico per non sovraccaricare nessuno.

L'applicazione **non richiede alcuna installazione**: usa solo Python 3
(libreria standard) e salva i dati in un file SQLite locale.

## Avvio

```bash
cd masterplan
python3 app.py
```

Poi apri il browser su **http://localhost:8000**

Alla prima esecuzione vengono create automaticamente le **9 società** di esempio
e il database `masterplan.db`. Per ripartire da zero basta cancellare quel file.

## Il flusso gestito (i ruoli)

L'app rispecchia esattamente il processo che hai descritto:

1. **Segreteria di rete** — registra la richiesta in arrivo
   (*Nuova richiesta*): oggetto, tipo (**gara**, **lavoro specifico**,
   **consulenza**), cliente, descrizione, scadenza.
   → stato **Ricevuta**.

2. **Manager di rete** — apre la richiesta e individua a quali società inviarla,
   indicando per ciascuna un *peso* (carico stimato). La segreteria la invia.
   → stato **Inviata** e parte il **conto alla rovescia di 24h** per ogni società.

3. **Società** — entro 24h **Accetta** o **Rifiuta** (con motivo, es. "troppo
   carico"). Le richieste non risposte entro 24h diventano automaticamente
   **Scadute**. Se accetta almeno una → stato **Accettata**; se rifiutano tutte
   → **Chiusa negativa**.

4. **Manager di rete** — definisce il **gruppo di lavoro** e il **Project
   Manager** (con la sua società capofila). → stato **In corso**.

5. **Project Manager** — a fine lavoro segna **Completata**.

Ogni passaggio è registrato nella **tracciabilità** della richiesta (chi, cosa,
quando), così c'è sempre traccia di tutto come avviene oggi via mail.

## Il controllo del carico

Il **Cruscotto** e la pagina **Società della rete** mostrano per ogni società:

- il **carico attivo** (somma dei pesi dei lavori accettati/in corso);
- la **capacità** massima;
- la **% di saturazione** (verde < 70%, arancione < 100%, rosso ≥ 100%).

Quando arriva nuovo lavoro, il manager vede subito chi è scarico e chi è pieno,
evitando di sovraccaricare le società.

## File del progetto

| File        | Contenuto |
|-------------|-----------|
| `app.py`    | Web server e instradamento (solo libreria standard) |
| `db.py`     | Dati: società, richieste, assegnazioni, eventi, calcolo carico |
| `views.py`  | Pagine HTML (interfaccia in italiano) |
| `masterplan.db` | Database SQLite (creato all'avvio, non versionato) |

## Possibili sviluppi futuri

- Invio reale delle email (notifica automatica alle società e alla segreteria).
- Login per ruoli (segreteria / manager / referenti società).
- Promemoria automatici allo scadere delle 24h.
- Report e statistiche per periodo, cliente, tipo di lavoro.
- Allegati (bando di gara, documenti) sulle richieste.
