---
tags: [knowledge, guida]
---

# Guida: usare questo second brain con Obsidian

> Lo stesso set di file `.md` è **memoria di Claude** (via git + hook) **e**
> **vault Obsidian** per te. Questa nota spiega come collegare i due mondi.
> Torna all'[[index]].

## 1. Aprire la repo come vault

1. Clona la repo sul tuo computer:
   `git clone <url-della-repo> giampi`
2. In Obsidian: **Apri cartella come vault** → scegli la cartella `giampi`.
3. Fatto: tutte le note (`index`, `profile`, `decisions`, il diario, la
   conoscenza) appaiono nel vault, con grafo e link già funzionanti.

## 2. Convenzioni che usiamo

- **Wikilink**: `[[nome-nota]]` collega due note (cliccabile + visibile nel
  grafo). Es. da [[index]] a [[profile]].
- **Tag**: `#progetto`, `#decisione`, `#diario`, `#idea`, `#persona` per
  filtrare e raggruppare.
- **Frontmatter**: il blocco `---` in cima a ogni nota contiene i `tags:`.
- **Nota indice**: [[index]] è la homepage (MOC) da cui parte tutto.

## 3. Sincronizzazione automatica (plugin Obsidian Git)

Così le tue modifiche in Obsidian e quelle di Claude restano allineate:

1. In Obsidian: **Impostazioni → Plugin della community → Sfoglia** → installa
   **Obsidian Git** → abilitalo.
2. Configura l'auto-commit/pull (es. ogni 10 minuti) e il push automatico.
3. Risultato:
   - Tu scrivi in Obsidian → Obsidian Git fa **commit + push**.
   - Alla sessione dopo, **Claude** legge le tue modifiche (l'hook ricarica).
   - Claude aggiorna le note e fa push → tu fai **pull** e le vedi in Obsidian.

```
Tu in Obsidian  ──scrivi/navighi──┐
                                   ├──►  stessi file .md  ──► git ──► Claude
Claude in sessione ──aggiorna──────┘
```

## 4. Buone abitudini

- Quando crei una nota nuova, **collegala** da [[index]] con un `[[wikilink]]`.
- Per una voce di diario nuova, parti da `memory/journal/_template.md`.
- Le decisioni importanti vanno sempre anche in [[decisions]].
