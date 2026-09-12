# Aggiunta alla FASE 0-ter di `ufficio-legale-amministrativo` v0.6.0

Il difetto **A** dell'audit del 05-09 è **già chiuso** in v0.6.0: la `FASE 0-ter` controlla
`_inventario/copertura.json`, passa `_inventario/schede.rpt` agli agenti e avvisa se
`commessa-forense` non è installato. L'innesto generico sarebbe per tre quarti un doppione, e
**non va applicato a questo plugin.**

Mancano invece i tre riscontri dell'11 settembre 2026, che al momento della scrittura della
FASE 0-ter non erano noti. Sono qui sotto, già nella voce del plugin.

---

## Punti 4 e 5, da aggiungere all'elenco numerato della FASE 0-ter

*(dopo il punto 3, quello su `lib/riscontro_atti.py`)*

```markdown
4. **il cancello di copertura chiuso non vuol dire fascicolo letto.** `copertura.py stato` stampa
   due misure, e vanno lette entrambe: gli atti aperti e le pagine lette. Su Caltagirone
   (11/09/2026) erano `781/781 = 100%` di atti e `3.155/16.402 = 19,2%` di pagine — un atto
   risulta letto anche se se ne sono aperte tre pagine su centoventitré. Riporta la tabella di
   `copertura.py report` in testa al documento, non in appendice: chi legge deve sapere su quanta
   carta si fonda l'analisi prima delle conclusioni. Se accanto alla percentuale compare
   `(MINIMO)`, alcune letture parziali non dichiarano le pagine e lì contano zero;

5. **una lettura parziale non provata è un'affermazione, non un dato.** Un record `PARZIALE` la
   cui motivazione sostiene che il resto sta altrove — *riproduce*, *già letto*, *ripetitivo*,
   *struttura standard già riscontrata* — e che non ha il campo `riproduce`, non è mai stata
   verificata da nessuno:

   ```bash
   python "<percorso di commessa-forense>/scripts/parziali_confronto.py" "$CARTELLA" --rassegna
   ```

   Su Caltagirone ne risultavano **40 su 175**, per 2.803 pagine. Finché non sono provate non
   concludere nulla su quelle pagine, e in particolare non scrivere che un fatto «non risulta
   agli atti».
```

---

## Avvertenza da aggiungere in coda alla FASE 0-ter

*(dopo il capoverso «Se `commessa-forense` non è installato…»)*

```markdown
**Un rimando «id NNN» dentro una scheda non è un riferimento: gli id cambiano a ogni
ricensimento.** Su Caltagirone cinque relazioni di calcolo rimandavano a «POD1 (id 678)»: dopo un
ricensimento l'id 678 era un'altra opera e POD1 era diventato il 687, con uno slittamento di +9.
Tutti e cinque i rimandi erano sbagliati e nessuno se n'era accorto. Prima di seguire un rimando
per id, risolvilo e guarda su cosa cade davvero.
```

---

## Cosa NON aggiungere

I presidi **«l'indice non è la fonte»** e **«una scheda che si dichiara illeggibile non è una
lettura»** questo plugin li ha già, e in forma **migliore**: non come avvertenze ma come
architettura — il referto di integrità eseguito prima di leggere, il sidecar che dichiara
`NATIVO` / `OCR` / `MINIMO` / `ASSENTE`, il marcatore
`[TESTO DA OCR — NON UTILIZZABILE COME VIRGOLETTATO]`.

L'audit del 05-09 lo diceva: *«quella legale è la stessa regola in forma di stato dichiarato sul
file. La seconda è più difficile da ignorare.»* Sostituirle con le mie sarebbe un peggioramento.

---

## Dove sta il file da modificare

`skills/ufficio-legale-amministrativo/SKILL.md` — sezione `## FASE 0-ter — Il quadro dei fatti
(fascicolo voluminoso)`, intorno alla riga 179 della v0.6.0.
