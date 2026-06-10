# Ufficio Riserve — pacchetto skill (upgrade)

Skill per analizzare la documentazione di un appalto di opere civili e costruire
le **riserve dell'appaltatore "inattaccabili"** ai sensi del **D.Lgs. 36/2023**.

## Contenuto
- `SKILL.md` — definizione della skill e workflow in 8 fasi.
- `reference/normativa-riserve.md` — quadro normativo e termini/decadenze.
- `reference/checklist-inattaccabilita.md` — gate finale di validazione.
- `reference/template-riserva.md` — modello + esempio compilato.
- `reference/tassonomia-riserve.md` — catalogo dei fatti pregiudizievoli.
- `reference/documenti-input.md` — documenti da acquisire (Fase 1).
- `reference/best-practice-internazionali.md` — SCL/AACE/FIDIC, delay & quantum.

## Cosa cambia rispetto alla versione precedente (upgrade)
1. **Gate anti-decadenza**: fase dedicata a tempestività e scadenze (15 gg) con
   semaforo, per evitare il vizio che più spesso fa respingere le riserve.
2. **Checklist di inattaccabilità** come blocco finale: nessun output se un
   requisito manca.
3. **Struttura entitlement → causation → quantum** importata dai claims
   internazionali (SCL/AACE/FIDIC).
4. **Quantum tracciabile** e **delay/disruption** con metodo dichiarato.
5. **Dossier probatorio** trattato come parte della riserva (contemporaneous
   records), non come allegato eventuale.
6. **Tassonomia** dei fatti pregiudizievoli per non perdere riserve.

## Come aggiornare la skill su Claude (desktop)
1. Comprimi la cartella `ufficio-riserve/` in uno zip.
2. Su Claude desktop → Impostazioni → Skills (Capabilities) → carica/aggiorna la
   skill sostituendo la versione esistente.
3. In alternativa, copia la cartella in `~/.claude/skills/ufficio-riserve/` se
   usi Claude Code.

## Avvertenza
Strumento di supporto tecnico-giuridico. Le riserve con effetti decadenziali
vanno **validate da un legale** prima dell'iscrizione. Termini, soglie e
articoli vanno verificati sul testo vigente e sul CSA del singolo appalto.

## Merge con la tua versione attuale
Se mi fornisci il `SKILL.md` della versione in uso sul desktop, allineo questa
alle tue convenzioni di input/output invece di sostituirla.
