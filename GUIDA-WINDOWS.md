# 🪟 Guida rapida per Windows

Come installare e usare il **Giornale dei Lavori** sul tuo PC Windows.
Pensata per chi non è pratico di programmazione: bastano pochi click.

---

## 1. Installa Node.js (una volta sola)

Node.js è il "motore" che fa funzionare l'app.

1. Vai su **https://nodejs.org**
2. Clicca il pulsante verde con scritto **LTS**.
3. Apri il file scaricato (`node-...msi`) e clicca **Next / Avanti**
   fino a **Install**. Non serve cambiare nulla.

> Lo installi una volta sola; non dovrai più rifarlo.

---

## 2. Scarica l'app (una volta sola)

1. Apri questa pagina nel browser:
   **https://github.com/demichelisgiampiero-lgtm/giampi/tree/claude/workflow-aElIb**
2. Clicca il pulsante verde **Code** → **Download ZIP**.
3. Vai nella cartella **Download**, fai **tasto destro** sul file `giampi-...zip`
   → **Estrai tutto…** → scegli per esempio il **Desktop** → **Estrai**.

Ora hai una cartella `giampi-claude-workflow-aElIb` (o simile) sul Desktop.

---

## 3. Avvia l'app (ogni volta che ti serve)

1. Apri la cartella che hai estratto.
2. Fai **doppio click** sul file **`Avvia-Giornale-Windows.bat`**.
3. Si apre una finestra nera: la **prima volta** prepara tutto da sola
   (serve internet, ci mette un minuto). Le volte successive parte subito.
4. Dopo qualche secondo l'app si apre **da sola nel browser**.
   Se non si aprisse, apri il browser e vai su: **http://localhost:3000**

> ⚠️ Windows potrebbe mostrare un avviso "PC protetto da Windows" o del
> firewall la prima volta: clicca **"Ulteriori informazioni" → "Esegui
> comunque"** e **"Consenti accesso"**. È normale per i programmi locali.

---

## 4. Spegnere l'app

Chiudi la **finestra nera** (quella del comando). L'app si arresta.
I tuoi dati restano salvati e li ritrovi al prossimo avvio.

---

## Dove finiscono i dati

Tutto ciò che inserisci (cantieri, voci CME, giornaliere) viene salvato in un
file sul tuo computer, dentro la cartella dell'app:

```
giampi\data\giornale.db
```

💡 **Consiglio:** ogni tanto fai una copia di questo file (es. su una chiavetta
o su Drive) per avere un backup. Per ripartire da zero, basta eliminarlo.

---

## Problemi comuni

| Problema | Soluzione |
|---|---|
| "Node.js non risulta installato" | Rifai il **Passo 1** e riavvia il PC. |
| Il browser non si apre da solo | Aprilo a mano e vai su `http://localhost:3000`. |
| "Porta già in uso" | C'è già un'altra finestra dell'app aperta: chiudila. |
| Voglio usarla da tablet/telefono | Serve la pubblicazione online: chiedi a Claude l'opzione "hosting". |

---

Per i dettagli tecnici completi vedi il file **`README.md`**.
