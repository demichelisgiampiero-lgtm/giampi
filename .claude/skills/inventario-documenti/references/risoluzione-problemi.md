# Quando il cancello non passa

`registro.py stato` esce con codice 1 e dice quali file sono in sospeso. Ecco
come si risolve ciascun caso — e cosa non fare.

## `RICHIEDE_OCR`

Il file e' una scansione e non abbiamo il suo contenuto.

1. Installare un motore OCR (`references/formati.md`) e rilanciare:
   `python3 scripts/estrai.py "/percorso" --solo-mancanti`
2. Se l'OCR gira ma rende poco: la scansione e' di bassa qualita' o storta.
   Provare `ocrmypdf --deskew --clean --force-ocr -l ita in.pdf out.pdf` a mano.
3. Se non si puo' installare nulla: escludere motivando, e **dirlo nel corpo
   della risposta**, non solo nella tabella. Un verbale di sospensione non letto
   puo' ribaltare la ricostruzione dei fatti.

## `MANCA_STRUMENTO`

Il messaggio nella nota dice quale programma serve. Se e' un `.msg` isolato, in
alternativa all'installazione si puo' chiedere all'utente di riesportarlo da
Outlook come `.eml`, che si legge senza dipendenze.

## `ERRORE` / `PROTETTO`

- *archivio Office corrotto o file rinominato*: capita spesso che un `.xls` sia
  in realta' un `.xlsx`, o viceversa. Verificare con `file "nome"` e correggere
  l'estensione.
- *PDF cifrato*: chiedere la password all'utente, oppure, se il PDF e' solo
  protetto in scrittura, `qpdf --decrypt in.pdf out.pdf`.
- *permesso negato*: il file e' aperto in un altro programma o appartiene a un
  altro utente.

## `ESTRATTI MA NON ANCORA LETTI`

Non e' un problema tecnico: significa che il lavoro di lettura non e' finito.
Riprendere con `registro.py da-leggere` e continuare. Questa e' precisamente la
riga che la skill esiste per far comparire, quindi non va aggirata.

## Cartelle molto grandi

Il censimento e l'estrazione scalano bene; e' la lettura che costa. Su fascicoli
oltre il migliaio di file, concordare prima con l'utente un perimetro esplicito
(per esempio: solo `01_contrattuali` e `02_contabilita`), lanciare l'inventario
solo su quello, e dichiararlo nella tabella di copertura. Un perimetro ristretto
e dichiarato e' corretto; un perimetro ristretto di fatto e taciuto e' il difetto
da evitare.

Se invece serve tutto, si puo' spezzare per sottocartella: un `_inventario`
separato per ciascuna, e le tabelle di copertura si sommano.

## Rilanciare da capo

Gli stati stanno tutti in `_inventario/manifest.json`. Per ricominciare da zero
basta cancellare la cartella `_inventario` e rifare il censimento. Per rifare
solo l'estrazione conservando le letture gia' registrate, usare `--solo-mancanti`.

## Il fascicolo e' cambiato durante il lavoro

Se l'utente aggiunge documenti a analisi iniziata, rilanciare `inventario.py`
crea un manifest nuovo e le letture registrate vanno perse. Per evitarlo,
conservare il manifest esistente e trattare i file nuovi come un secondo lotto
con un `--out` diverso, oppure — piu' semplice — completare l'analisi in corso e
poi fare un secondo giro dichiarato sui documenti sopravvenuti.
