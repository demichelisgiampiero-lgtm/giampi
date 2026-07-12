---
description: Analizza un file video (metadati, fotogrammi, audio/trascrizione) e produce un riepilogo
argument-hint: <percorso-del-video> [cosa cercare]
allowed-tools: Bash(ffprobe:*), Bash(ffmpeg:*), Bash(ls:*), Bash(file:*), Bash(mkdir:*), Bash(du:*), Read, Glob, Write
---

## Compito

Analizza il video indicato dall'utente e produci un'analisi chiara e strutturata **in italiano**.

- **Percorso del video:** `$1`
- **Focus richiesto (facoltativo):** $2

Se `$1` è vuoto, chiedi all'utente il percorso del file video prima di procedere.

## Prerequisiti

Verifica che gli strumenti necessari siano disponibili. Se `ffprobe`/`ffmpeg` non sono installati, avvisa l'utente e proponi come installarli (es. `apt-get install ffmpeg` o `brew install ffmpeg`), poi fermati.

```
command -v ffprobe ffmpeg
```

## Procedura

1. **Esistenza e dimensione del file**
   - Controlla che il file esista (`ls -lh "$1"`, `du -h "$1"`, `file "$1"`).
   - Se non esiste, segnalalo e fermati.

2. **Metadati tecnici** con `ffprobe`:
   ```
   ffprobe -v error -show_format -show_streams -of default=noprint_wrappers=1 "$1"
   ```
   Riporta in modo leggibile: durata, risoluzione, frame rate, codec video/audio, bitrate, numero di tracce audio/sottotitoli, container.

3. **Campionamento dei fotogrammi**
   - Crea una cartella temporanea per i frame.
   - Estrai alcuni fotogrammi rappresentativi (circa 1 ogni 10 secondi, massimo ~12 immagini) ridimensionati per essere leggeri:
     ```
     ffmpeg -i "$1" -vf "fps=1/10,scale=640:-1" -frames:v 12 -q:v 3 /tmp/frames_%03d.jpg
     ```
   - Usa `Read` su ciascun frame estratto per **descrivere visivamente** il contenuto (scene, persone/oggetti, testo a schermo, cambi di scena).

4. **Audio / trascrizione**
   - Se è presente una traccia audio, estraila:
     ```
     ffmpeg -i "$1" -vn -ac 1 -ar 16000 /tmp/audio.wav
     ```
   - Se nel progetto o nell'ambiente è disponibile uno strumento di trascrizione (es. `whisper`), usalo per trascrivere. Altrimenti indica che la trascrizione automatica non è disponibile e descrivi solo la presenza/assenza di audio e parlato.

5. **Sintesi finale**
   Produci un riepilogo strutturato con queste sezioni:
   - **Panoramica** — di cosa tratta il video in 2-3 frasi.
   - **Dettagli tecnici** — tabella con durata, risoluzione, fps, codec, dimensione.
   - **Contenuto visivo** — descrizione cronologica delle scene basata sui frame.
   - **Contenuto audio** — sintesi o trascrizione, se disponibile.
   - **Focus richiesto** — se l'utente ha indicato qualcosa in `$2`, rispondi specificamente a quella domanda.
   - **Note / anomalie** — problemi riscontrati (video corrotto, tracce mancanti, ecc.).

6. **Pulizia**
   - Rimuovi i file temporanei creati (`/tmp/frames_*.jpg`, `/tmp/audio.wav`) al termine.

Mantieni le risposte concise e vai dritto al punto. Non descrivere ogni singolo comando che esegui: mostra i risultati dell'analisi.
