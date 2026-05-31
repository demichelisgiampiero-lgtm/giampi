---
tags: [idea, knowledge]
---

# Il "second brain" alla Karpathy

> Nota di conoscenza: l'idea di fondo dietro a questo intero vault.
> Collegata a → [[index]] · [[decisions]] · [[profile]]

## L'idea

Andrej Karpathy ha reso popolare l'idea di tenere un **diario leggibile sia
dall'umano sia dall'AI**, versionato in git, che cresce nel tempo. Invece di
affidarsi alla memoria volatile del modello, si scrive ciò che conta in file di
testo semplici che **persistono** e si **rileggono** all'inizio di ogni sessione.

## Perché funziona

- Il contesto di un'AI è **effimero**: finita la sessione, sparisce.
- I file markdown in git **sopravvivono** e sono portabili ovunque.
- Sono leggibili da chiunque, senza lock-in: oggi Claude, domani un altro
  strumento, sempre gli stessi `.md`.

## Come lo applichiamo qui

Questo è esattamente ciò che fa il nostro [[index|second brain]]:
- [[profile]] tiene il contesto stabile,
- [[decisions]] traccia il "perché" delle scelte,
- il diario (es. [[2026-05-31]]) registra il "cosa è successo".

Lo stesso set di file è leggibile **da Claude** (via hook) e **da te** in
Obsidian. Vedi [[guida-obsidian]] per collegare i due mondi.

## Collegamenti

- Decisione fondante: [[decisions]] → *"Creato il second brain markdown..."*
- Strumento umano: [[guida-obsidian]]
