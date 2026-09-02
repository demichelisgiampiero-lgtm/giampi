# Formati: come vengono trattati e cosa serve installare

Principio generale: gli script funzionano **senza installare nulla**, usando la
libreria standard di Python. Gli strumenti esterni, quando presenti, migliorano
la qualita' dell'estrazione. L'unico caso in cui manca davvero qualcosa e' l'OCR:
per una scansione non esiste ripiego, o si fa l'OCR o quel contenuto non si ha.

## Tabella di sintesi

| Formato | Metodo usato | Ripiego | Serve installare? |
|---|---|---|---|
| `.pdf` nativo | `pdftotext` (poppler) | `pypdf`, poi estrattore interno | no, ma poppler e' piu' accurato |
| `.pdf` scansionato | `ocrmypdf` | `pdftoppm` + `tesseract` | **si', altrimenti il contenuto non si acquisisce** |
| `.docx` | lettura diretta OOXML | — | no |
| `.xlsx` `.xlsm` | lettura diretta OOXML | — | no |
| `.pptx` | lettura diretta OOXML | — | no |
| `.doc` `.rtf` `.odt` | LibreOffice | — | LibreOffice |
| `.xls` `.ods` | LibreOffice → xlsx → OOXML | — | LibreOffice |
| `.eml` | modulo `email` | — | no |
| `.msg` (Outlook) | `extract-msg` | — | `pip install extract-msg` |
| `.txt` `.csv` `.md` `.xml` `.json` | diretto, con rilevamento codifica | — | no |
| `.html` | rimozione marcatori | — | no |
| immagini | `tesseract` se disponibile | marcato `NON_TESTUALE` | tesseract solo se le foto contengono testo |
| `.dwg` `.dxf` `.zip` | marcato `NON_TESTUALE` | — | — |

## Installazione

**Windows** — con [Chocolatey](https://chocolatey.org) da PowerShell come amministratore:
```powershell
choco install tesseract poppler
pip install ocrmypdf extract-msg
```
Per l'italiano serve anche il pacchetto lingua `ita` di Tesseract (l'installer
Windows lo propone tra i componenti aggiuntivi: spuntare *Additional language data → Italian*).

**macOS** — con [Homebrew](https://brew.sh):
```bash
brew install ocrmypdf tesseract-lang poppler
pip3 install extract-msg
```
`tesseract-lang` include l'italiano.

**Linux (Debian/Ubuntu)**:
```bash
sudo apt install ocrmypdf tesseract-ocr tesseract-ocr-ita poppler-utils libreoffice
pip3 install extract-msg
```

Verifica rapida di cosa e' presente:
```bash
for p in pdftotext ocrmypdf tesseract soffice; do
  command -v $p >/dev/null && echo "OK   $p" || echo "--   $p mancante"
done
```

## Note che contano nella pratica

**Il controllo di densita' sui PDF.** Un PDF si considera scansionato quando
produce meno di 100 caratteri per pagina. La soglia non e' arbitraria: una pagina
di testo reale ne produce 1500-3000, mentre una scansione ne produce zero o
pochissimi (il numero di pagina stampato dallo scanner, un timbro digitale).
La soglia si cambia in `estrai.py`, costante `SOGLIA_CARATTERI_PER_PAGINA`.
Alzarla se molte scansioni passano inosservate; abbassarla solo se il fascicolo
contiene legittimamente pagine quasi vuote (frontespizi, separatori).

**PDF misti.** Un fascicolo unico che contiene sia pagine native sia scansioni
supera il controllo di densita' grazie alle pagine native, e le scansioni
restano fuori senza segnalazione. E' il caso piu' insidioso. Se un PDF voluminoso
rende molto meno testo di quanto ci si aspetti dal numero di pagine, forzare
l'OCR su quel file:
```bash
ocrmypdf --redo-ocr --skip-text -l ita "file.pdf" "file_ocr.pdf"
```
e rilanciare l'estrazione.

**Fogli nascosti negli Excel.** Vengono estratti e marcati `[NASCOSTO]`. Nei CME
e' spesso li' che stanno le analisi prezzi intermedie: sono dati di lavoro, e in
un contenzioso possono contare parecchio.

**Intestazioni e pie' di pagina nei Word.** Vengono estratti insieme al corpo,
perche' e' li' che di norma vivono numero di protocollo e data.

**Duplicati.** Riconosciuti per impronta sha256 del contenuto, non per nome: lo
stesso atto in due cartelle viene estratto una volta sola. Attenzione al caso
opposto, che l'impronta non vede: due *versioni* dello stesso documento hanno
contenuto diverso e restano due file distinti, correttamente. Quando compaiono
`Capitolato.pdf` e `Capitolato_rev2.pdf`, stabilire quale sia il contrattuale e
dirlo nella sintesi.

**Estrattore PDF interno.** Il ripiego in libreria standard copre i PDF generati
digitalmente (che sono la maggioranza degli atti di gara e di contabilita'), ma
rende peggio di poppler su tabelle complesse e su codifiche di font non standard:
puo' perdere l'allineamento delle colonne. Quando `metodo=stdlib` compare su un
documento da cui si devono ricavare *numeri* (un libretto delle misure, un
registro di contabilita'), conviene installare poppler e rilanciare.
