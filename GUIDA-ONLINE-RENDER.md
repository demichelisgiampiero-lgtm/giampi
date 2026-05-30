# 🌐 Pubblicare il Giornale dei Lavori online (Render)

Questa guida mette l'app **online**, così la usi dal **telefono, tablet o PC**
tramite un indirizzo web — con **gli stessi dati ovunque** e protetta da
**password**. Da fare una volta sola; richiede ~10 minuti.

> Useremo **Render.com**: ha un piano adatto con disco persistente (i dati
> restano salvati anche dopo riavvii e aggiornamenti).

---

## 1. Crea un account Render

1. Vai su **https://render.com** → **Get Started** / **Sign Up**.
2. Registrati con **GitHub** (è il più semplice: collega lo stesso account
   dove c'è il progetto `giampi`).

## 2. Crea il servizio dal progetto (Blueprint)

Il progetto contiene già il file di configurazione `render.yaml`: Render lo
legge e imposta quasi tutto da solo.

1. Nel cruscotto Render clicca **New +** → **Blueprint**.
2. Seleziona il repository **`giampi`** (se richiesto, autorizza Render ad
   accedervi).
3. Render rileva `render.yaml` e mostra il servizio **giornale-dei-lavori**.
4. Ti chiederà di inserire il valore di **`APP_PASSWORD`**: scegli qui la
   **password** con cui accederai all'app (annotala!). L'utente predefinito
   è `cieffe` (modificabile con la variabile `APP_USER`).
5. Clicca **Apply** / **Create**. Render scarica il codice, installa e avvia
   l'app (qualche minuto la prima volta).

## 3. Apri l'app

1. Al termine, Render mostra un indirizzo tipo
   **`https://giornale-dei-lavori.onrender.com`**.
2. Aprilo nel browser (telefono, tablet o PC): comparirà la richiesta di
   **utente e password** → inserisci `cieffe` e la password scelta al punto 2.4.
3. Sei dentro! Da qui in poi PC e telefono usano **lo stesso archivio**.

> 📲 **Sul telefono:** apri l'indirizzo in Chrome/Safari, poi
> "Aggiungi a schermata Home" per avere un'icona come una app.

---

## Dati condivisi tra PC e telefono

- L'app online è la **fonte unica** dei dati: ciò che inserisci dal telefono
  in cantiere lo ritrovi dal PC in ufficio (e viceversa), aprendo lo stesso
  indirizzo nel browser.
- Il database è salvato sul **disco persistente** di Render (`/data`), quindi
  non si perde con riavvii o aggiornamenti.
- L'app desktop installata sul PC resta utile come comodità **offline**, ma ha
  un suo archivio separato. Per lavorare sui dati condivisi, dal PC usa il
  browser sull'indirizzo online.

## Aggiornamenti

Ad ogni miglioria del codice (push sul branch), Render **riaggiorna l'app da
solo**. Non devi rifare nulla.

## Costi

Il piano con disco persistente di Render è a pagamento (qualche dollaro al
mese). Esiste un piano gratuito, ma **non** mantiene i dati nel tempo e
"si addormenta" quando inattivo: per un uso reale di cantiere è sconsigliato.

## Sicurezza

- L'accesso è protetto da password (variabile `APP_PASSWORD`).
- La connessione è cifrata (Render fornisce `https://` automaticamente).
- 💡 Cambia la password periodicamente dal cruscotto Render
  (**Environment** → `APP_PASSWORD` → salva: l'app si riavvia da sola).
