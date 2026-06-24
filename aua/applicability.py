"""Motore di applicabilita dei titoli AUA (Sezione 7 di WORKFLOW_AUA.md).

Valuta i flag della checklist e determina, per ciascuno dei 7 titoli sostituibili
dall'AUA (art. 3 DPR 59/2013), se il titolo e applicabile e se e gia implementato
(template disponibile nell'MVP). Solo logica pura: nessun I/O.
"""

from __future__ import annotations

from typing import Any


# Catalogo dei 7 titoli sostituibili dall'AUA (art. 3 DPR 59/2013).
# Per ogni titolo: codice (A..G), nome, riferimento normativo, flag implementato.
# Implementati subito nell'MVP: A, C, D, G. Solo rilevati (da produrre a parte): B, E, F.
CATALOGO_TITOLI: list[dict[str, Any]] = [
    {
        "codice": "A",
        "nome": "Autorizzazione agli scarichi di acque reflue",
        "riferimento": "art. 124 D.Lgs. 152/2006",
        "implementato": True,
    },
    {
        "codice": "B",
        "nome": "Comunicazione per l'utilizzazione agronomica di effluenti, "
                "acque di vegetazione, acque reflue",
        "riferimento": "art. 112 D.Lgs. 152/2006",
        "implementato": False,
    },
    {
        "codice": "C",
        "nome": "Autorizzazione alle emissioni in atmosfera (in via ordinaria)",
        "riferimento": "art. 269 D.Lgs. 152/2006",
        "implementato": True,
    },
    {
        "codice": "D",
        "nome": "Autorizzazione di carattere generale alle emissioni in atmosfera",
        "riferimento": "art. 272 c. 2 D.Lgs. 152/2006",
        "implementato": True,
    },
    {
        "codice": "E",
        "nome": "Comunicazione/documentazione di impatto acustico",
        "riferimento": "L. 447/1995",
        "implementato": False,
    },
    {
        "codice": "F",
        "nome": "Autorizzazione all'utilizzo dei fanghi di depurazione in agricoltura",
        "riferimento": "D.Lgs. 99/1992",
        "implementato": False,
    },
    {
        "codice": "G",
        "nome": "Comunicazioni per il recupero di rifiuti in procedura semplificata",
        "riferimento": "artt. 215-216 D.Lgs. 152/2006",
        "implementato": True,
    },
]


def _emissioni_regime(dati: dict[str, Any]) -> tuple[bool, str]:
    """Restituisce (presenti, regime) per le emissioni in atmosfera.

    Usa .get() per gestire senza errori le chiavi mancanti; il regime e
    normalizzato (minuscolo, senza spazi) per i confronti.
    """
    emissioni = dati.get("emissioni_atmosfera") or {}
    presenti = bool(emissioni.get("presenti"))
    regime = str(emissioni.get("regime") or "").strip().lower()
    return presenti, regime


def _valuta_titolo(codice: str, dati: dict[str, Any]) -> tuple[bool, str]:
    """Applica la regola di applicabilita del singolo titolo (Sezione 7).

    Restituisce (applicabile, motivazione). Tutte le letture usano .get() per
    tollerare sezioni/chiavi assenti nella checklist.
    """
    scarichi = dati.get("scarichi") or {}
    rifiuti = dati.get("rifiuti_recupero") or {}
    altri = dati.get("altri_titoli") or {}
    presenti_emissioni, regime = _emissioni_regime(dati)

    if codice == "A":
        if bool(scarichi.get("presenti")):
            return True, "Sono presenti scarichi di acque reflue (scarichi.presenti = true)."
        return False, "Nessuno scarico di acque reflue dichiarato (scarichi.presenti = false)."

    if codice == "B":
        if bool(altri.get("utilizzo_agronomico_effluenti")):
            return True, ("Dichiarata utilizzazione agronomica di effluenti "
                          "(altri_titoli.utilizzo_agronomico_effluenti = true).")
        return False, "Nessuna utilizzazione agronomica di effluenti dichiarata."

    if codice == "C":
        if presenti_emissioni and regime == "ordinaria":
            return True, ("Emissioni in atmosfera in regime ordinario "
                          "(emissioni_atmosfera.regime = 'ordinaria').")
        if presenti_emissioni:
            return False, (f"Emissioni presenti ma in regime '{regime or 'non indicato'}', "
                           "non ordinario.")
        return False, "Nessuna emissione in atmosfera dichiarata."

    if codice == "D":
        if presenti_emissioni and regime == "generale":
            return True, ("Emissioni in atmosfera in regime generale "
                          "(emissioni_atmosfera.regime = 'generale').")
        if presenti_emissioni:
            return False, (f"Emissioni presenti ma in regime '{regime or 'non indicato'}', "
                           "non generale.")
        return False, "Nessuna emissione in atmosfera dichiarata."

    if codice == "E":
        if bool(altri.get("impatto_acustico")):
            return True, "Dichiarato impatto acustico (altri_titoli.impatto_acustico = true)."
        return False, "Nessun impatto acustico dichiarato."

    if codice == "F":
        if bool(altri.get("fanghi_in_agricoltura")):
            return True, ("Dichiarato utilizzo di fanghi in agricoltura "
                          "(altri_titoli.fanghi_in_agricoltura = true).")
        return False, "Nessun utilizzo di fanghi in agricoltura dichiarato."

    if codice == "G":
        if bool(rifiuti.get("presente")):
            return True, ("Previsto recupero di rifiuti in procedura semplificata "
                          "(rifiuti_recupero.presente = true).")
        return False, "Nessun recupero di rifiuti in procedura semplificata dichiarato."

    # Codice non previsto: non applicabile per sicurezza.
    return False, f"Titolo con codice '{codice}' non riconosciuto."


def valuta_applicabilita(dati: dict[str, Any]) -> list[dict[str, Any]]:
    """Valuta l'applicabilita di tutti i titoli AUA secondo le regole della Sezione 7.

    Per ogni titolo del catalogo restituisce un dizionario con:
    {codice, nome, riferimento, applicabile, implementato, motivazione}.
    Le chiavi mancanti nella checklist sono gestite senza errori (.get()).
    """
    if not isinstance(dati, dict):
        dati = {}

    esiti: list[dict[str, Any]] = []
    for titolo in CATALOGO_TITOLI:
        codice = titolo["codice"]
        applicabile, motivazione = _valuta_titolo(codice, dati)
        esiti.append({
            "codice": codice,
            "nome": titolo["nome"],
            "riferimento": titolo["riferimento"],
            "applicabile": applicabile,
            "implementato": titolo["implementato"],
            "motivazione": motivazione,
        })
    return esiti


def riepilogo(esiti: list[dict[str, Any]]) -> str:
    """Produce una sintesi testuale degli esiti di applicabilita.

    Esempio:
    "Titoli da includere: A, C, G - generati: A, C, G - da produrre a parte: (nessuno)"
    """
    da_includere = [e["codice"] for e in esiti if e.get("applicabile")]
    generati = [e["codice"] for e in esiti if e.get("applicabile") and e.get("implementato")]
    da_produrre = [
        e["codice"] for e in esiti if e.get("applicabile") and not e.get("implementato")
    ]

    def _elenco(codici: list[str]) -> str:
        return ", ".join(codici) if codici else "(nessuno)"

    return (
        f"Titoli da includere: {_elenco(da_includere)} "
        f"— generati: {_elenco(generati)} "
        f"— da produrre a parte: {_elenco(da_produrre)}"
    )
