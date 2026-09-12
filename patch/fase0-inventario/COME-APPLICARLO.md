# Come applicare l'innesto FASE 0 ai quattro plugin

**Data:** 12 settembre 2026
**Chiude:** il difetto **A** dell'audit del 05-09-2026 — *«l'entry point non cerca
`_inventario\copertura.json` / `schede.rpt` e cataloga per nome»*.

---

## Perché riscritto e non copiato

La correzione del 5 settembre esiste in `ufficio-claims` v0.5.3 e `ufficio-valutazioni-ambientali`
v0.5.3, ma **nessuna delle due si trova**: né sul Desktop né su Drive, dove le copie più recenti
sono `ufficio-claims v0.5.0` (20 agosto) e `ufficio-valutazioni-ambientali v0.5.2` (4 settembre),
entrambe **precedenti** alla correzione.

Riscriverlo è risultato comunque preferibile: questa versione incorpora anche i tre riscontri
dell'11 settembre — le due coperture, le affermazioni non provate, i rimandi pendenti — che il
5 settembre non erano ancora noti.

---

## I due file

| File | Dove va | Fine riga |
|---|---|---|
| `INNESTO-FASE0.md` | **incollato** nell'entry point, nella fase di apertura | CRLF, come i `SKILL.md` |
| `reference/inventario-forense.md` | copiato in `reference/` del plugin | LF, come il resto di `reference/` |

Le convenzioni sui fine riga sono quelle già in uso nei plugin: `SKILL.md` in CRLF,
`reference/` in LF. I due file sono già scritti così.

---

## Dove incollarlo, plugin per plugin

| Plugin | File | Punto |
|---|---|---|
| `ufficio-legale-amministrativo` | entry point del dossier | prima del ramo `_DOSSIER_COMMESSA.json` |
| `ufficio-verifiche-progettuali` | `skills\orchestratore\SKILL.md` | **BLOCCO 1**, prima del ramo dossier |
| `ufficio-put` | entry point | nella fase di apertura del fascicolo |
| `ufficio-progettazione` | entry point (DIP) | nella fase di apertura del fascicolo |

**Regola di posizione: la modalità forense va controllata per PRIMA**, prima del ramo
`_DOSSIER_COMMESSA.json` e prima di qualunque catalogazione per nome. Se si mette dopo, il plugin
ricataloga comunque e l'innesto non serve a nulla.

---

## Ordine consigliato

1. **`ufficio-legale-amministrativo`** — è quello che serve su Cava Fusco, è già a v0.6.0 ed è
   l'unico **versionato in git** (bundle `b3788cb` dell'11/09). Si tocca con la rete di sicurezza.
2. **`ufficio-verifiche-progettuali`** — ha già il presidio 1 nella stessa formulazione, quindi
   l'innesto si salda a un testo che lo prevede già.
3. **`ufficio-put`** e **`ufficio-progettazione`** — esposizione minore.

---

## Come verificare che sia servito

Su un fascicolo con `_inventario/` presente, il plugin deve:

- **nominare il registro** all'apertura, invece di elencare i file per nome;
- **non ricensire** e non rilanciare l'OCR;
- **riportare entrambe le coperture** quando dichiara su quanto si fonda l'analisi.

Se elenca i file per nome, l'innesto è stato messo troppo in basso.
