# Il repo, PowerShell e Claude Code — guida pratica

**Per:** Giampiero De Michelis · **Data:** 12 settembre 2026
**Taglio:** solo ciò che serve al lavoro che fai davvero. Gli esempi sono i casi veri
dell'11-12 settembre, non esempi inventati.

---

## Perché ti serve: i tre guai di questi due giorni

Nessuno dei tre era un problema tecnico difficile. Erano tutti e tre lo stesso problema.

1. **Due `copertura.py` diversi.** Uno da 105.602 byte, uno da 73.295. Per capire quale fosse
   quello vivo abbiamo confrontato le dimensioni dei file e le date di Drive. Con un repo sarebbe
   stata una riga: `git log`.

2. **`parziali_confronto.py` e `indicizza2.py` evaporati.** Scritti, usati, e persi con lo
   scratchpad di sessione. Un file dentro un repo non si perde: è registrato.

3. **Il plugin che gira non era il codice che modificavi.** L'installato era del 5 settembre, la
   sorgente del 7. Due giorni di correzioni sul disco e mai in servizio.

**Un repo è la risposta a tutti e tre.**

---

## 1. Cos'è un repo, detto come lo diresti tu

Un repo è **una cartella normale, più un registro di tutto quello che le è successo.**

Il registro sta in una sottocartella nascosta, `.git`, e non si tocca mai a mano.

> **L'analogia che funziona:** il repo sta al codice come il **registro di contabilità** sta ai
> lavori. Ogni `commit` è un SAL: dice **cosa** è cambiato, **quando**, e **perché**. E `git log`
> è la contabilità: la puoi rileggere tutta, in ordine, e nessuno può riscriverla di nascosto.

Tre parole che ti servono, e basta:

| Parola | Cos'è | Nel tuo mondo |
|---|---|---|
| **working tree** | i file come sono adesso sul disco | il cantiere com'è oggi |
| **commit** | una fotografia registrata, con data e motivazione | un SAL firmato |
| **remote** | la copia su GitHub, condivisa | l'originale depositato |

Il flusso è sempre lo stesso: **lavori sul disco → registri un commit → lo mandi al remote.**

---

## 2. I sette comandi che bastano

Git ne ha centinaia. Questi sette coprono il 95% di quello che farai.

### Guardare

```powershell
git status
```
**Cosa è cambiato e non è ancora registrato.** È il comando che lanci quando non sai a che punto
sei. Lancialo sempre, non fa mai danni.

```powershell
git diff
```
**Esattamente quali righe sono cambiate.** Le righe con `-` tolte, quelle con `+` aggiunte.
È quello che ti ho chiesto ieri per l'innesto.

```powershell
git log --oneline -10
```
**Gli ultimi dieci commit**, uno per riga. La contabilità.

### Registrare

```powershell
git add -A
git commit -m "Aggiungi la modalita' forense alla FASE 0-ter"
```
`add` dice *«queste modifiche voglio registrarle»*; `commit` le registra con la motivazione.
**La motivazione conta**: fra tre mesi sarà l'unica cosa che ti dice perché avevi toccato quel file.

Nota: sono **due** passaggi perché puoi registrare solo una parte di quello che hai cambiato.
All'inizio usa sempre `-A`, che vuol dire «tutto».

### Scambiare

```powershell
git push
```
**Manda i tuoi commit su GitHub.** Finché non fai push, esistono solo sul tuo PC.

```powershell
git pull
```
**Prende quello che c'è su GitHub e non hai.** È quello che fai per leggere ciò che ti scrivo io.

---

## 3. PowerShell — il minimo indispensabile

### Il prompt ti dice dove sei

```
PS C:\Users\HP WS>
```

Quel `C:\Users\HP WS` è la **cartella corrente**. Tutti i comandi girano lì.

**È l'errore numero uno.** `git status` lanciato fuori da un repo non trova niente; lanciato nel
repo sbagliato ti mostra l'altro progetto.

### Muoversi

```powershell
cd "C:\Users\HP WS\Desktop\Caltagirone (Catania)"
Get-Location          # dove sono adesso
```

**Le virgolette servono** quando il percorso ha spazi o parentesi — e i tuoi ce li hanno quasi
sempre: `HP WS`, `Caltagirone (Catania)`.

### I segnaposti nei miei messaggi

Quando scrivo `<plugin>` o `<repo giampi>`, **non sono da copiare così**: sono buchi da riempire
col percorso vero.

> Ieri è successo: `python <plugin>\scripts\...` è stato incollato letterale, e PowerShell ha
> risposto *«Operatore '<' riservato per utilizzi futuri»*. Non era un guasto: stava leggendo
> `<` come un suo simbolo.

Il modo comodo è metterlo una volta in una variabile e poi riusarla:

```powershell
$plugin = "C:\percorso\vero\del\plugin"
python "$plugin\scripts\copertura.py" stato "$c"
```

---

## 4. Claude Code sul repo — il vero salto

**Questo è il punto che cambia di più la tua giornata.**

Sul PC hai un agente che vede i file, apre le cartelle, modifica il testo ed esegue i comandi.
Con lui **non digiti comandi: descrivi il risultato.**

### Invece di questo

```powershell
cd <plugin>
git diff > "<repo>\patch\fase0-inventario\diff-legale.txt"
cd <repo>
git add -A ; git commit -m "diff" ; git push
```

### Digli questo

> Prendi il diff del plugin, scrivilo in `patch/fase0-inventario/diff-legale.txt` del repo
> `giampi`, poi committa e pusha.

Fa le stesse cose, e **non sbaglia i percorsi** — perché li legge invece di ricordarseli.

### Cosa gli puoi chiedere, con esempi tuoi

| Vuoi | Diglielo così |
|---|---|
| capire dove sei | *«in che repo siamo, e cosa c'è di non committato?»* |
| rivedere prima di registrare | *«fammi vedere cosa ho cambiato»* |
| registrare | *«committa con un messaggio che spiega che ho aggiunto i punti 4 e 5 alla FASE 0-ter»* |
| ritrovare | *«quando abbiamo toccato `copertura.py` l'ultima volta e perché?»* |
| tornare indietro | *«annulla le modifiche non committate a questo file»* |
| trovare roba | *«c'è da qualche parte un file che contiene MODALITA FORENSE?»* |

### La regola d'oro

**Prima di fargli committare, fatti sempre mostrare il diff.** Un commit sbagliato si corregge,
ma vederlo prima costa dieci secondi e ti insegna a leggere le modifiche.

---

## 5. Il giro di lavoro, in pratica

```
1. git pull            ← prendi quello che c'è di nuovo
2. lavori              ← tu, o Claude Code al posto tuo
3. git status          ← cosa è cambiato?
4. git diff            ← esattamente cosa?
5. git add -A
6. git commit -m "..."  ← con una motivazione vera
7. git push            ← e adesso esiste anche fuori dal tuo PC
```

Sono sempre questi sette, in quest'ordine, per qualunque cosa.

---

## 6. Tre cose che ti risparmiano i guai di ieri

### Metti `commessa-forense` nel repo

È il punto 9 del piano, ed è la cura per il guaio n. 1 e n. 3. Da quel momento:

- **quale copia è viva** lo dice `git log`, non le dimensioni dei file;
- **cosa è cambiato dal 5 settembre** lo dice `git diff`, non un confronto a mano;
- **niente si perde**, perché ogni cosa registrata resta.

### Non lasciare niente nello scratchpad

Se un file serve più di una volta, **va nel repo**. `parziali_confronto.py` era già stato scritto
una volta e perso. Adesso è in `patch/commessa-forense/scripts/` e non si perde più.

### Ricorda che modificare ≠ mettere in servizio

Il repo tiene il **sorgente**. Il plugin che gira è una **copia caricata**. Sono due cose, e dopo
ogni modifica va rifatto il caricamento, se no la correzione resta sul disco — che è esattamente
quello che era successo alle correzioni del 7 settembre.

---

## 7. Se qualcosa va storto

| Ti dice | Vuol dire | Fai |
|---|---|---|
| `not a git repository` | non sei dentro un repo | `cd` nella cartella giusta |
| `nothing to commit` | non hai cambiato niente, o hai già committato | `git status` per capire quale dei due |
| `rejected ... fetch first` | su GitHub c'è qualcosa che tu non hai | `git pull`, poi `git push` |
| `Operatore '<' riservato` | hai incollato un segnaposto letterale | sostituiscilo col percorso vero |

**Regola generale:** git è molto difficile da rompere davvero. Quasi tutto quello che è stato
committato si recupera. Le uniche cose che si perdono sono quelle che **non hai mai committato** —
motivo in più per farlo spesso.

---

## In una riga

> **Committa spesso, con motivazioni vere, e fatti mostrare il diff prima.**
> Il resto lo puoi chiedere a Claude Code.
