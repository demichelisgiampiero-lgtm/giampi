# Log delle decisioni

> Decisioni importanti, in ordine cronologico (le più recenti in alto).
> Formato: **data** — decisione — *motivazione*.

---

## 2026-05-31

- **Creato il second brain markdown versionato in git** come memoria persistente
  di Claude. — *Il container di Claude Code sul web è effimero; solo ciò che è
  committato sopravvive. Il markdown è leggibile, portabile e mio per sempre.*
- **Scelto il formato "diario/log giornaliero"** (una voce per data in
  `memory/journal/`). — *Preferenza di Giampiero: registro cronologico di cosa
  succede.*
- **Mantenuto anche il plugin `claude-mem`** come memoria automatica di supporto,
  accanto al diario markdown. — *Due livelli: il diario esplicito e leggibile +
  la cattura automatica del plugin.*
- **Hook SessionStart sincrono** che inietta la memoria nel contesto all'avvio.
  — *Il caricamento è istantaneo (legge solo file locali), quindi non serve la
  modalità async.*
