"""Lettura e validazione della checklist compilata dal cliente (file YAML)."""

from __future__ import annotations

import pathlib
from typing import Any

import yaml


class ErroreChecklist(Exception):
    """Errore bloccante nella lettura della checklist."""


# Sezioni che devono sempre essere presenti nella checklist.
SEZIONI_OBBLIGATORIE = ("gestore", "impianto")

# Campi anagrafici minimi richiesti per poter compilare il Modello Unico.
CAMPI_GESTORE_OBBLIGATORI = (
    "ragione_sociale",
    "codice_fiscale",
    "sede_legale",
)
CAMPI_IMPIANTO_OBBLIGATORI = (
    "denominazione",
    "comune",
    "provincia",
)

# Province della Regione Campania (sigle ammesse).
PROVINCE_CAMPANIA = {"AV", "BN", "CE", "NA", "SA"}


def carica_checklist(percorso: str | pathlib.Path) -> dict[str, Any]:
    """Carica la checklist YAML e restituisce il dizionario dei dati."""
    percorso = pathlib.Path(percorso)
    if not percorso.exists():
        raise ErroreChecklist(f"File checklist non trovato: {percorso}")
    try:
        with percorso.open("r", encoding="utf-8") as f:
            dati = yaml.safe_load(f)
    except yaml.YAMLError as exc:  # pragma: no cover - dipende dall'input
        raise ErroreChecklist(f"Errore di sintassi YAML in {percorso}: {exc}") from exc
    if not isinstance(dati, dict):
        raise ErroreChecklist("La checklist deve contenere un dizionario di sezioni.")
    return dati


def valida(dati: dict[str, Any]) -> list[str]:
    """Verifica i requisiti minimi. Restituisce la lista di avvisi non bloccanti.

    Solleva ErroreChecklist per problemi che impediscono la generazione.
    """
    avvisi: list[str] = []

    for sezione in SEZIONI_OBBLIGATORIE:
        if sezione not in dati or not isinstance(dati[sezione], dict):
            raise ErroreChecklist(f"Sezione obbligatoria mancante o non valida: '{sezione}'.")

    gestore = dati["gestore"]
    for campo in CAMPI_GESTORE_OBBLIGATORI:
        if not gestore.get(campo):
            raise ErroreChecklist(f"Campo obbligatorio mancante: gestore.{campo}")

    impianto = dati["impianto"]
    for campo in CAMPI_IMPIANTO_OBBLIGATORI:
        if not impianto.get(campo):
            raise ErroreChecklist(f"Campo obbligatorio mancante: impianto.{campo}")

    provincia = str(impianto.get("provincia", "")).upper().strip()
    if provincia not in PROVINCE_CAMPANIA:
        avvisi.append(
            f"La provincia dell'impianto ('{provincia or 'non indicata'}') non risulta tra "
            f"quelle della Regione Campania ({', '.join(sorted(PROVINCE_CAMPANIA))}). "
            "Verificare la competenza territoriale del SUAP/autorità competente."
        )

    if not gestore.get("legale_rappresentante"):
        avvisi.append("Manca il legale rappresentante (gestore.legale_rappresentante): "
                      "necessario per la sottoscrizione dell'istanza.")

    pec = (gestore.get("legale_rappresentante") or {}).get("pec")
    if not pec:
        avvisi.append("Manca la PEC del legale rappresentante: l'invio al SUAP avviene via PEC.")

    return avvisi
