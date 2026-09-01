#!/usr/bin/env bash
# Prepara l'ambiente per l'estrazione degli elaborati.
#
# Crea un venv locale perche' il python di sistema di alcune immagini ha il
# modulo cryptography rotto (_cffi_backend mancante), che fa fallire l'import
# di pypdf e di chi lo usa. Il venv evita del tutto il problema.
set -u

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${RIAMB_VENV:-$DIR/.venv}"

echo "==> venv in $VENV"
python3 -m venv "$VENV" 2>/dev/null || true
"$VENV/bin/pip" install --quiet --upgrade pip 2>/dev/null

echo "==> librerie di estrazione"
"$VENV/bin/pip" install --quiet pdfplumber python-docx pypdfium2 defusedxml lxml || {
    echo "!! installazione fallita: PyPI raggiungibile?" >&2
    exit 1
}

if ! command -v tesseract >/dev/null 2>&1; then
    echo "==> tesseract assente, provo a installarlo (serve solo per i PDF scansionati)"
    if command -v apt-get >/dev/null 2>&1; then
        apt-get install -y tesseract-ocr tesseract-ocr-ita >/dev/null 2>&1 \
            && echo "   tesseract installato" \
            || echo "   !! non installato: i PDF scansionati non saranno leggibili via OCR"
    else
        echo "   !! apt-get non disponibile: installa tesseract-ocr e la lingua ita a mano"
    fi
else
    echo "==> tesseract gia' presente"
fi

echo
echo "Pronto. Usa:"
echo "  $VENV/bin/python $DIR/estrai.py <file> --out <dir>"
