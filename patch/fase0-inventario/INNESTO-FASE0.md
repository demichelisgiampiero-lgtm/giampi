## MODALITA FORENSE — il fascicolo e' gia' stato letto

**Controllare per primo.** Se nella cartella esiste `_inventario/copertura.json` con un
`censito_il` valorizzato, il fascicolo e' gia' stato letto da `commessa-forense`: c'e' un registro
di ogni atto, con classe, esito di lettura e sintesi, e un indice ragionato in
`_inventario/schede.rpt`.

```bash
test -f "<cartella>/_inventario/copertura.json" && echo "MODALITA FORENSE"
```

In quel caso:

1. **Leggere `_inventario/schede.rpt` PRIMA di cercare.** Dice cosa c'e' in ogni atto, compresi
   quelli che nessuna query avrebbe pescato. La ricerca serve dopo, per la citazione.
2. **Prendere il perimetro dal registro, non dai nomi dei file.** Si lavora sui record con
   `classe: ATTO`; `DUPLICATO`, `DERIVATO`, `SERVIZIO` e `PROPRIO` non si ricontano.
3. **Non ricensire e non rilanciare l'OCR.** Un `_inventario/` valido ha gia' superato il cancello
   di integrita': l'OCR a monte e' fatto, e il `gate` di `commessa-rag` non si bloccera' sui
   `needs_ocr`. Rifarlo su un PDF nativo peggiora il testo.
4. **Prima di promettere un'analisi completa**, eseguire `copertura.py stato "<cartella>"`: esce
   **1** finche' restano atti non letti o indicizzati solo in parte. Se esce 1, l'analisi non e'
   completa e va detto.

### Le tre regole che non si saltano

🔴 **L'indice non e' la fonte.** Dalla scheda si prende il *dove guardare*; da un documento si
prende *cosa affermare*. Nessun dato che entri in un elaborato si cita dal registro: si rilegge
dalla pagina che il registro indica. Vale soprattutto per i numeri — un errore di soglia nasce da
un numero preso di seconda mano.

🔴 **Le due coperture sono due cose diverse.** `781/781 = 100% (documenti)` e
`3.155/16.402 = 19,2% (pagine)` convivono: un atto risulta letto anche se se ne sono aperte 3
pagine su 123. Leggere entrambe le righe, e riportare la tabella di copertura **in testa** alla
relazione, non in appendice.

🔴 **Una lettura parziale non provata e' un'affermazione.** Se un record `PARZIALE` ha una
motivazione che sostiene che il resto sta altrove (*riproduce*, *gia' letto*, *ripetitivo*,
*struttura standard gia' riscontrata*) **e il campo `riproduce` e' assente**, quell'affermazione
non e' mai stata verificata da nessuno. Elencarle con
`parziali_confronto.py "<cartella>" --rassegna` e non concludere nulla su quelle pagine — in
particolare, non scrivere che un fatto «non risulta agli atti».

> Protocollo completo, con i cinque presidi e i moventi misurati:
> `reference/inventario-forense.md`.

**Se `_inventario/` non c'e'**, si procede con le modalita' ordinarie previste qui sotto,
**dichiarandolo**: un'analisi senza inventario forense non ha superato nessuno dei tre cancelli, e
la relazione deve dirlo.
