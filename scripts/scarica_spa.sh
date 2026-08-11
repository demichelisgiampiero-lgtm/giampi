#!/usr/bin/env bash
#
# Scarica gli Studi Preliminari Ambientali (SPA) elencati in spa/urls.txt
# dal portale VIAVAS della Regione Campania.
#
# Uso:
#   ./scripts/scarica_spa.sh [file_urls] [cartella_destinazione]
#
# Default: spa/urls.txt -> spa/pdf/
#
# Ogni riga utile di file_urls ha la forma:
#   <nome_file_destinazione>  <URL>
# Righe vuote e righe che iniziano con # sono ignorate.

set -uo pipefail

URLS_FILE="${1:-spa/urls.txt}"
DEST_DIR="${2:-spa/pdf}"
MAX_RETRY=4

if [[ ! -f "$URLS_FILE" ]]; then
  echo "ERRORE: file elenco non trovato: $URLS_FILE" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"

ok=0
ko=0
skip=0
falliti=()

while read -r nome url; do
  # salta commenti e righe vuote
  [[ -z "${nome:-}" ]] && continue
  [[ "$nome" == \#* ]] && continue
  [[ -z "${url:-}" ]] && continue

  dest="$DEST_DIR/$nome"

  if [[ -s "$dest" ]]; then
    echo "= gia' presente, salto: $nome"
    skip=$((skip + 1))
    continue
  fi

  echo "-> $nome"
  attempt=1
  wait=2
  scaricato=0
  while (( attempt <= MAX_RETRY )); do
    if curl -fsSL --retry 0 --connect-timeout 20 --max-time 600 \
            -A "Mozilla/5.0 (compatible; ricerca-documentale)" \
            -o "$dest.part" "$url"; then
      mv "$dest.part" "$dest"
      scaricato=1
      break
    fi
    echo "   tentativo $attempt fallito, riprovo tra ${wait}s..." >&2
    sleep "$wait"
    attempt=$((attempt + 1))
    wait=$((wait * 2))
  done

  rm -f "$dest.part"

  if (( scaricato == 1 )); then
    # verifica che sia davvero un PDF e non una pagina di errore HTML
    if head -c 5 "$dest" | grep -q '%PDF'; then
      dim=$(wc -c < "$dest" | tr -d ' ')
      echo "   OK (${dim} byte)"
      ok=$((ok + 1))
    else
      echo "   ATTENZIONE: il contenuto non e' un PDF (probabile pagina di errore)" >&2
      mv "$dest" "$dest.non-pdf"
      ko=$((ko + 1))
      falliti+=("$nome (contenuto non PDF)")
    fi
  else
    echo "   FALLITO dopo $MAX_RETRY tentativi" >&2
    ko=$((ko + 1))
    falliti+=("$nome (download fallito)")
  fi
done < "$URLS_FILE"

echo
echo "=============================="
echo "Scaricati:      $ok"
echo "Gia' presenti:  $skip"
echo "Falliti:        $ko"
if (( ko > 0 )); then
  echo
  echo "Elenco falliti:"
  for f in "${falliti[@]}"; do
    echo "  - $f"
  done
fi
echo "Destinazione:   $DEST_DIR"

(( ko == 0 ))
