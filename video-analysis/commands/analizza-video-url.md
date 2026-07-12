---
description: Scarica un video da un URL (YouTube, ecc.) e lo analizza (metadati, fotogrammi, audio/trascrizione)
argument-hint: <url-del-video> [cosa cercare]
allowed-tools: Bash(yt-dlp:*), Bash(ffprobe:*), Bash(ffmpeg:*), Bash(ls:*), Bash(file:*), Bash(mkdir:*), Bash(rm:*), Bash(du:*), Read, Glob, Write
---

## Compito

Scarica il video dall'URL indicato e produci un'analisi chiara e strutturata **in italiano**.

- **URL del video:** `$1`
- **Focus richiesto (facoltativo):** $2

Se `$1` è vuoto, chiedi all'utente l'URL del video prima di procedere.

## Prerequisiti

Verifica che gli strumenti necessari siano disponibili:

```
command -v yt-dlp ffprobe ffmpeg
```

- Se `yt-dlp` non è installato, avvisa l'utente e proponi come installarlo (es. `pip install -U yt-dlp` oppure `brew install yt-dlp`), poi fermati.
- Se `ffprobe`/`ffmpeg` non sono installati, proponi `apt-get install ffmpeg` o `brew install ffmpeg`, poi fermati.

## Procedura

1. **Scaricamento del video**
   - Crea una cartella di lavoro (es. `/tmp/video_dl`).
   - Prima ispeziona i metadati remoti senza scaricare, per confermare titolo/durata:
     ```
     yt-dlp --no-warnings --print "%(title)s | %(duration)s s | %(resolution)s" "$1"
     ```
   - Se la durata supera ~20 minuti, avvisa l'utente che il download potrebbe essere pesante e chiedi conferma prima di procedere.
   - Scarica in una risoluzione contenuta per velocizzare l'analisi:
     ```
     yt-dlp -f "best[height<=720]/best" -o "/tmp/video_dl/video.%(ext)s" "$1"
     ```
   - Individua il file scaricato con `ls /tmp/video_dl/`.

2. **Analisi del file**
   Applica al file scaricato la stessa procedura del comando `/analizza-video`:
   - **Metadati tecnici** con `ffprobe -v error -show_format -show_streams ...`.
   - **Fotogrammi** campionati (~1 ogni 10s, max ~12), ridimensionati, poi descritti con `Read`.
   - **Audio/trascrizione**: estrai l'audio e trascrivilo se è disponibile uno strumento tipo `whisper`; altrimenti indica solo la presenza/assenza di parlato.

3. **Sintesi finale**
   Produci un riepilogo strutturato con:
   - **Panoramica** — di cosa tratta il video in 2-3 frasi.
   - **Origine** — titolo, autore/canale e URL.
   - **Dettagli tecnici** — tabella con durata, risoluzione, fps, codec, dimensione.
   - **Contenuto visivo** — descrizione cronologica delle scene.
   - **Contenuto audio** — sintesi o trascrizione, se disponibile.
   - **Focus richiesto** — se l'utente ha indicato qualcosa in `$2`, rispondi specificamente a quella domanda.
   - **Note / anomalie** — problemi riscontrati (download fallito, geo-blocco, tracce mancanti, ecc.).

4. **Pulizia**
   - Rimuovi la cartella di lavoro e i file temporanei creati (`/tmp/video_dl`, `/tmp/frames_*.jpg`, `/tmp/audio.wav`) al termine.

Rispetta il copyright: scarica solo contenuti che l'utente è autorizzato a usare. Mantieni le risposte concise: mostra i risultati dell'analisi, non ogni comando eseguito.
