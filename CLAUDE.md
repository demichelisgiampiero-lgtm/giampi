# Second Brain di Giampiero 🧠

Questo repository è il **"second brain"** di Giampiero: una memoria persistente
che sopravvive tra una sessione di Claude e l'altra. Il container in cui giro è
effimero — tutto ciò che non è committato in git viene perso. Quindi **questi
file markdown SONO la mia memoria a lungo termine**.

> Ispirato all'idea di Karpathy: tenere un "diario" leggibile dall'umano e
> dall'AI, versionato in git, che cresce nel tempo.

## Come funziona

1. **All'avvio di ogni sessione** un hook (`.claude/hooks/session-start.sh`)
   carica automaticamente nel mio contesto: il profilo, le decisioni e le
   ultime voci di diario. Così riparto sempre sapendo chi sei e cosa stavamo
   facendo.
2. **Durante la sessione** aggiorno i file di memoria man mano che emergono
   fatti, decisioni o eventi degni di nota.
3. **A fine sessione** committo le modifiche, così la memoria persiste.

## Struttura

```
CLAUDE.md                  ← questo file (istruzioni che leggo sempre)
memory/
  profile.md               ← chi sei, preferenze, contesto stabile
  decisions.md             ← log delle decisioni importanti
  journal/
    AAAA-MM-GG.md          ← una voce di diario per giorno/sessione
    _template.md           ← modello per le nuove voci
  knowledge/               ← conoscenza organizzata per argomento (opzionale)
.claude/
  hooks/session-start.sh   ← carica la memoria all'avvio
  settings.json            ← registra l'hook
```

## Regole per me (Claude)

Quando lavoro in questo repository devo:

- **Scrivere sempre in italiano** nei file di memoria.
- **Aggiornare il diario**: a ogni sessione di lavoro aggiungo/aggiorno la voce
  del giorno in `memory/journal/AAAA-MM-GG.md`. Una voce per data.
- **Registrare le decisioni** importanti in `memory/decisions.md` (cosa, perché,
  quando).
- **Tenere aggiornato `memory/profile.md`** quando emergono nuove informazioni
  stabili su Giampiero (preferenze, progetti, persone, obiettivi).
- **Committare la memoria** al termine del lavoro con un messaggio chiaro, così
  nulla va perso (la repo è l'unica cosa che sopravvive al container effimero).
- Essere **conciso e fattuale**: il diario è una memoria, non un romanzo.
- **Mantenere il vault navigabile in Obsidian**: ogni nota nuova va collegata da
  `[[index]]` con un `[[wikilink]]` e taggata (es. `#progetto`, `#diario`,
  `#idea`). Così il grafo resta utile man mano che cresce. Vedi
  `memory/guida-obsidian.md`.

## Comando rapido

Se Giampiero dice "aggiorna la memoria" o "salva nel second brain", aggiorno i
file pertinenti, faccio un commit descrittivo e un push sul branch corrente.
