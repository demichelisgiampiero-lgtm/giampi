# Patch per `commessa-forense` — verifica delle letture parziali

**Data:** 11 settembre 2026
**Si applica a:** `commessa-forense` v0.10.0, ramo con `scripts/copertura.py` da **105.602 byte**
(quello del 7 settembre; **non** la copia marketplace da 73.295 byte).

---

## Il difetto che chiude

Su `copertura.py parziale`, il campo `--motivo` è obbligatorio ma **non viene verificato da
nulla**. Una lettura parziale può quindi affermare che il resto dell'atto sta altrove, e nessuno
lo controlla.

**Caltagirone, D.D.G. n. 3/2024.** Registrato con motivo *«riproduce il parere 627, già letto»*:
ventuno pagine restarono fuori. Contenevano i pareri CTS **350/2023** e **526/2023**, che non
esistono in nessun altro punto del fascicolo, e da lì è uscito il riscontro sulla **CA 4 lett. i)**.
Il difetto fu trovato il 10/09 a mano, non da uno strumento.

---

## Cosa contiene

| File | Cosa fa |
|---|---|
| `scripts/parziali_confronto.py` | **nuovo modulo.** Verifica che le pagine non lette si ritrovino davvero nell'atto dichiarato riprodotto, confrontando i 5-grammi di parole presi dall'indice di `commessa-rag`. Usabile anche da riga di comando |
| `copertura.py.patch` | innesta la verifica dentro `cmd_parziale` (151 righe di diff) |

---

## Come si applica

```bash
cd <radice del plugin commessa-forense>
cp <questa cartella>/scripts/parziali_confronto.py scripts/
patch -p0 scripts/copertura.py < <questa cartella>/copertura.py.patch
python3 -c "import py_compile; py_compile.compile('scripts/copertura.py', doraise=True)"
```

Poi **ricaricare il plugin**: la sorgente modificata non entra in esercizio da sola.

I fine riga sono **CRLF**, come gli altri script del plugin, e la patch li preserva.

---

## Cosa cambia nel comportamento

`parziale` guadagna due argomenti:

- **`--causa {MIRATA,RIPRODUCE,ILLEGGIBILE}`** — perché il resto non è stato letto;
- **`--riproduce PERCORSO`** — l'atto già letto di cui questo sarebbe copia (ripetibile).

Tre regole:

1. **`--causa MIRATA`** (il valore predefinito) non afferma nulla sul resto: nessun controllo.
   La lettura mirata resta una tecnica legittima.
2. **`--causa RIPRODUCE`** esige `--riproduce` ed **esegue il confronto**. Se una sola pagina non
   si ritrova nel riferimento, **la registrazione viene rifiutata** e l'errore elenca le pagine.
3. **Se `--causa` è omessa ma il motivo afferma una riproduzione** (*«riproduce…»*, *«già letto»*,
   *«è copia di…»*, *«identico a…»*, *«duplicato…»*), la registrazione **viene rifiutata** finché
   non la si dichiara in forma verificabile. È il caso del D.D.G. 3: non si può più scivolare in
   prosa.

**Retrocompatibile:** i comandi esistenti che non usano `--causa` continuano a funzionare, a meno
che il motivo non affermi una riproduzione — cioè esattamente il caso che deve fermarsi.

**Se `parziali_confronto.py` manca, `RIPRODUCE` viene rifiutata**, non lasciata passare: un
verificatore assente non è un lasciapassare.

### Campi nuovi nel registro

- `causa_parziale` — `MIRATA` / `RIPRODUCE` / `ILLEGGIBILE`
- `riproduce` — l'elenco degli atti di riferimento, solo per `RIPRODUCE`

---

## Sui fascicoli già lavorati

```bash
python3 scripts/parziali_confronto.py "<cartella commessa>" --rassegna
```

Elenca le letture parziali che **affermano una riproduzione senza averla provata**. Non può
verificarle da sola — la motivazione è prosa e non dice in forma utilizzabile *quale* atto sarebbe
riprodotto — ma dà l'elenco, che è ciò che su Caltagirone nessuno aveva.

Esce **1** se ne trova, **0** se il fascicolo è pulito.

**Da lanciare subito su Caltagirone**, dove le letture parziali sono 175.

---

## Verifica di una singola lettura

```bash
python3 scripts/parziali_confronto.py "<cartella>" \
    --atto "Autorizzazioni/PAUR/DDG_3_2024.pdf" \
    --pagine "1-8" \
    --riproduce "Autorizzazioni/parere_627.pdf"
```

Esce **0** se la riproduzione regge, **1** se restano pagine scoperte, **2** se il confronto non è
eseguibile (indice assente, atto non indicizzato, riferimento senza testo).

---

## Come decide

- Estrae i **5-grammi di parole** di ogni pagina non dichiarata letta. Cinque perché quattro li fa
  combaciare il lessico burocratico (*«ai sensi dell'articolo»* ricorre ovunque) e sei rendono il
  confronto fragile a una virgola.
- Confronta con i 5-grammi dell'atto di riferimento, normalizzando come fa l'indice (minuscole,
  senza diacritici — `commessa-rag` indicizza con `remove_diacritics`).
- Una pagina è **riprodotta** se ne ritrova almeno il **90%**. Non il 100%, perché due tirature
  dello stesso testo differiscono per intestazioni, numerazione e sillabazione.
- Una pagina con **meno di 8 cinque-grammi** è **indecidibile**, non promossa: di una tavola
  grafica nessuno può affermare che «riproduce» un altro atto. Le indecidibili **bloccano**, perché
  sotto `RIPRODUCE` si sta facendo un'affermazione anche su di loro.

Soglie in testa al modulo: `SOGLIA_COPERTURA`, `MIN_GRAMMI`, `N_GRAMMA`.

---

## Prove eseguite

Ricostruito in laboratorio il caso del D.D.G. 3 (indice SQLite con un atto le cui prime 8 pagine
copiano un altro atto e le ultime 4 sono uniche):

| Prova | Atteso | Esito |
|---|---|---|
| atto che dichiara di riprodurre ma ha 4 pagine uniche | rifiuto, elenco `9-12` | **rifiutato**, pagine 9-12, «0% del testo si ritrova» |
| atto che riproduce davvero | passa | **passato** |
| 13 motivazioni che affermano riproduzione (con e senza apostrofo, con `'` e `’`) | tutte intercettate | **13 su 13** |
| 6 motivazioni di lettura mirata | nessuna intercettata | **0 falsi positivi** |
| rassegna su registro con 4 parziali | 2 sospette, salta la mirata e la già verificata | **corretto** |

> Durante la prova è emerso che `«già letto»` scritto con l'apostrofo — `gia' letto`, la forma che
> i lettori usano perché il plugin vieta le lettere accentate — **non veniva intercettato**.
> Corretto normalizzando via gli apostrofi prima del confronto.
