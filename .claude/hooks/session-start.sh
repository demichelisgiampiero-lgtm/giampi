#!/bin/bash
# SessionStart hook — carica il "second brain" nel contesto di Claude.
# Stampa su stdout: profilo, decisioni e le ultime voci di diario.
# Tutto ciò che viene stampato qui viene iniettato nel contesto di Claude
# all'avvio della sessione, così riparte sempre con la memoria caricata.
set -euo pipefail

# Radice del progetto (fallback alla posizione dello script se la var manca).
ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
MEM="$ROOT/memory"

# Se non c'è la cartella memory non facciamo nulla.
[ -d "$MEM" ] || exit 0

echo "=========================================="
echo " 🧠 SECOND BRAIN — memoria caricata"
echo "=========================================="
echo
echo "Questi sono i ricordi persistenti di Giampiero. Leggili prima di iniziare."
echo "A fine sessione, aggiorna il diario in memory/journal/ e committa."
echo

if [ -f "$MEM/profile.md" ]; then
  echo "----- PROFILO (memory/profile.md) -----"
  cat "$MEM/profile.md"
  echo
fi

if [ -f "$MEM/decisions.md" ]; then
  echo "----- DECISIONI (memory/decisions.md) -----"
  cat "$MEM/decisions.md"
  echo
fi

# Ultime 3 voci di diario (per data decrescente), escluso il template.
if [ -d "$MEM/journal" ]; then
  echo "----- ULTIME VOCI DI DIARIO (memory/journal/) -----"
  # Elenca i file AAAA-MM-GG.md, ordina decrescente, prendi i primi 3.
  mapfile -t entries < <(find "$MEM/journal" -maxdepth 1 -type f -name '[0-9]*.md' -printf '%f\n' 2>/dev/null | sort -r | head -n 3)
  if [ "${#entries[@]}" -eq 0 ]; then
    echo "(nessuna voce di diario ancora)"
  else
    for f in "${entries[@]}"; do
      echo
      echo ">>> $f"
      cat "$MEM/journal/$f"
    done
  fi
  echo
fi

# Indice degli approfondimenti, se presenti.
if [ -d "$MEM/knowledge" ]; then
  kfiles=$(find "$MEM/knowledge" -maxdepth 1 -type f -name '*.md' ! -name 'README.md' -printf ' - knowledge/%f\n' 2>/dev/null | sort)
  if [ -n "$kfiles" ]; then
    echo "----- APPROFONDIMENTI DISPONIBILI (memory/knowledge/) -----"
    echo "$kfiles"
    echo
  fi
fi

echo "=========================================="
echo " Fine memoria. Buon lavoro."
echo "=========================================="
