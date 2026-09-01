# Insidie dell'ambiente

Da leggere solo quando qualcosa fallisce. Sono problemi incontrati davvero, con
la soluzione che ha funzionato.

## `ModuleNotFoundError: No module named '_cffi_backend'`

Il `cryptography` di sistema è rotto in alcune immagini e fa esplodere l'import
di `pypdf` (che lo carica per i provider di cifratura). Non tentare di ripararlo:
usa un venv, come fa `scripts/setup.sh`. In alternativa `pdfplumber` non ha
questa dipendenza.

## LibreOffice: `Error: source file could not be loaded`

`soffice --convert-to pdf` può fallire su qualunque file, anche integro — si
verifica anche sull'originale non modificato. Significa che **il rendering non è
disponibile**, non che il file sia corrotto.

Conseguenza pratica: dopo aver modificato un `.docx` non puoi guardarlo. Verifica
per altra via — validazione strutturale e confronto paragrafo per paragrafo — e
**dichiara al committente che il controllo visivo non è stato fatto**, invitandolo
ad aprirlo. Non spacciare per verificato ciò che non hai visto.

## `pdftoppm is not installed`

Poppler può mancare, e senza di esso lo strumento di lettura non riesce a
rasterizzare i PDF. Rimedio senza dipendenze di sistema: `pypdfium2`, che
installa da PyPI e rasterizza in puro Python.

```python
import pypdfium2 as pdfium
pdf = pdfium.PdfDocument(src)
pdf[i].render(scale=2.2).to_pil().save("p.png")
```

Scala 2.2 è un buon compromesso per l'OCR di testo giuridico; sotto 1.5 la resa
peggiora sensibilmente.

## PDF che estrae zero caratteri

È una scansione. Verifica prima di concludere che il file sia vuoto: conta i
caratteri per pagina e le immagini per pagina. Poi rasterizza e passa a
tesseract:

```bash
tesseract p01.png - -l ita --psm 6
```

`--psm 6` (blocco uniforme di testo) funziona bene sui testi normativi
impaginati a colonna singola. La lingua `ita` è necessaria: senza, gli accenti e
le parole giuridiche degradano molto.

Attenzione: l'OCR sbaglia sistematicamente i numeri di legge e la punteggiatura
(«legge 171 novembre 2014», «n, 152»). **Non citare un numero d'articolo letto
solo da OCR senza averlo riscontrato sull'immagine della pagina.**

## Rete chiusa

L'egress può essere bloccato verso i domini esterni (403 al CONNECT del proxy)
mentre **PyPI e i repository APT restano raggiungibili**: `pip install` e
`apt-get install` funzionano anche quando non si riesce a scaricare un PDF da un
portale pubblico.

Se serve un documento dal web e la rete è chiusa: non aggirare la policy. Chiedi
al committente di allegarlo, oppure di aprire l'allowlist dell'ambiente — che si
applica all'avvio del container, quindi richiede una sessione nuova.

## Contesto effimero

Il filesystem e la memoria non sopravvivono alla sessione, e il repository viene
clonato da capo. Tutto ciò che serve alla sessione successiva va **committato**:
elaborati archiviati, trascrizioni OCR, rapporti, diario.
