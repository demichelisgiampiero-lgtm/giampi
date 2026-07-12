# memory/ — La memoria persistente

Questa cartella è il cuore del second brain. Tutto qui dentro è pensato per
essere letto sia da te (Giampiero) sia da Claude all'inizio di ogni sessione.

| File / cartella | A cosa serve |
|---|---|
| `profile.md` | Chi sei: preferenze, contesto stabile, progetti, obiettivi. Cambia di rado. |
| `decisions.md` | Log cronologico delle decisioni importanti, con motivazione. |
| `journal/` | Il diario: una voce per giorno (`AAAA-MM-GG.md`). È il registro di cosa succede. |
| `knowledge/` | Approfondimenti per argomento (opzionale, si riempie col tempo). |

## Il principio

> Il container di Claude è effimero. Solo ciò che è committato in git
> sopravvive. Quindi **scrivere qui = ricordare; non scrivere = dimenticare.**

Ogni volta che chiudiamo una sessione di lavoro, la memoria viene committata.
Alla sessione dopo, l'hook di avvio la ricarica e si riparte da dove eravamo.
