"""Interfaccia a riga di comando dell'AUA (Fase 4 di WORKFLOW_AUA.md).

Espone due sottocomandi tramite ``argparse``:

- ``applicabilita <checklist.yaml>``: carica e valida la checklist, poi stampa
  gli avvisi e il riepilogo dei titoli ambientali determinati dal motore.
- ``genera <checklist.yaml> -o <cartella>``: orchestra l'intero flusso (intake →
  applicabilita → render → DOCX), produce il Modello Unico e le relazioni dei
  soli titoli applicabili e implementati, e scrive ``Checklist_Allegati.md``.

L'output (Word ``.docx``) e' editabile dal tecnico, secondo i principi della
Sezione 4 del workflow.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
from typing import Any

from jinja2 import TemplateError, TemplateNotFound

from aua.applicability import riepilogo, valuta_applicabilita
from aua.intake import ErroreChecklist, carica_checklist, valida
from aua.render import markdown_to_docx, renderizza_template


# Associazione fra codice del titolo, template *.md.j2 e nome-base del file di output.
# Sono mappati solo i titoli implementati nell'MVP (A, C, D, G). Il numero iniziale
# (00, 01, ...) determina l'ordine dei documenti nel pacchetto.
TEMPLATE_PER_TITOLO: dict[str, dict[str, str]] = {
    "C": {
        "template": "relazione_emissioni.md.j2",
        "nome_file": "Relazione_Emissioni",
    },
    "D": {
        "template": "relazione_emissioni.md.j2",
        "nome_file": "Relazione_Emissioni",
    },
    "A": {
        "template": "relazione_scarichi.md.j2",
        "nome_file": "Relazione_Scarichi",
    },
    "G": {
        "template": "relazione_rifiuti.md.j2",
        "nome_file": "Relazione_Rifiuti",
    },
}

# Ordine di presentazione delle relazioni nel pacchetto (dopo il Modello Unico).
ORDINE_RELAZIONI = ["C", "D", "A", "G"]

# Riconosce i segnaposto residui nei documenti, tipo "[DA COMPLETARE: ...]".
_RE_SEGNAPOSTO = re.compile(r"\[DA COMPLETARE[^\]]*\]")


def _costruisci_contesto(dati: dict[str, Any], esiti: list[dict[str, Any]]) -> dict[str, Any]:
    """Costruisce il contesto Jinja2 a partire dai dati della checklist e dagli esiti.

    Il contesto contiene le sezioni della checklist piu' la lista ``titoli`` dei
    soli titoli applicabili (per popolare l'elenco del Modello Unico).
    """
    titoli_applicabili = [
        {
            "codice": e["codice"],
            "nome": e["nome"],
            "riferimento": e["riferimento"],
        }
        for e in esiti
        if e.get("applicabile")
    ]
    contesto = dict(dati)
    contesto["titoli"] = titoli_applicabili
    return contesto


def _segnaposto_residui(markdown: str) -> list[str]:
    """Restituisce l'elenco (ordinato e senza duplicati) dei segnaposto in un testo."""
    trovati = _RE_SEGNAPOSTO.findall(markdown)
    # Si rimuovono i duplicati preservando l'ordine di prima comparsa.
    visti: list[str] = []
    for s in trovati:
        if s not in visti:
            visti.append(s)
    return visti


def _comando_applicabilita(percorso_checklist: str) -> int:
    """Esegue il sottocomando ``applicabilita``: stampa avvisi e riepilogo dei titoli."""
    try:
        dati = carica_checklist(percorso_checklist)
        avvisi = valida(dati)
    except ErroreChecklist as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 1

    esiti = valuta_applicabilita(dati)

    if avvisi:
        print("Avvisi:")
        for avviso in avvisi:
            print(f"  - {avviso}")
        print()

    print(riepilogo(esiti))
    print()
    print("Dettaglio titoli:")
    for e in esiti:
        stato = "APPLICABILE" if e["applicabile"] else "non applicabile"
        impl = "generabile" if e["implementato"] else "da produrre a parte"
        print(f"  [{e['codice']}] {e['nome']} — {stato} ({impl})")
        print(f"       {e['motivazione']}")

    return 0


def _comando_genera(percorso_checklist: str, cartella_output: str) -> int:
    """Esegue il sottocomando ``genera``: produce il pacchetto AUA in ``cartella_output``."""
    try:
        dati = carica_checklist(percorso_checklist)
        avvisi = valida(dati)
    except ErroreChecklist as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 1

    esiti = valuta_applicabilita(dati)
    contesto = _costruisci_contesto(dati, esiti)

    cartella = pathlib.Path(cartella_output)
    cartella.mkdir(parents=True, exist_ok=True)

    # Tracciamento dei documenti prodotti e dei segnaposto residui per documento.
    documenti_prodotti: list[str] = []
    segnaposto_per_documento: dict[str, list[str]] = {}

    def _produci(template: str, nome_file: str) -> None:
        """Renderizza un template e lo converte nel relativo .docx, tracciando i segnaposto.

        In caso di template assente o di errore di sintassi Jinja2, oppure di errore
        di scrittura del file, solleva ``ErroreChecklist`` con un messaggio chiaro
        invece di lasciar emergere un'eccezione grezza con stack trace.
        """
        try:
            markdown = renderizza_template(template, contesto)
        except TemplateNotFound as exc:
            raise ErroreChecklist(
                f"Template non trovato: '{template}' (cartella aua/templates)."
            ) from exc
        except TemplateError as exc:
            raise ErroreChecklist(
                f"Errore nel template '{template}': {exc}"
            ) from exc
        percorso_docx = cartella / f"{nome_file}.docx"
        try:
            markdown_to_docx(markdown, str(percorso_docx))
        except OSError as exc:
            raise ErroreChecklist(
                f"Impossibile scrivere il documento '{percorso_docx}': {exc}"
            ) from exc
        documenti_prodotti.append(percorso_docx.name)
        residui = _segnaposto_residui(markdown)
        if residui:
            segnaposto_per_documento[percorso_docx.name] = residui

    # Tracciamento dei titoli da produrre a parte (B, E, F e fallback).
    esiti_per_codice = {e["codice"]: e for e in esiti}
    file_prodotti_set: set[str] = set()
    titoli_da_produrre_a_parte: list[dict[str, Any]] = []

    try:
        # 1) Modello Unico AUA: sempre prodotto.
        _produci("modello_unico_aua.md.j2", "00_Modello_Unico_AUA")

        # 2) Relazioni dei soli titoli applicabili E implementati, in ordine.
        #    Si evita di duplicare la relazione emissioni se sia C sia D risultassero
        #    applicabili (stesso template/file): si tiene traccia dei file gia' prodotti.
        numero = 1
        for codice in ORDINE_RELAZIONI:
            esito = esiti_per_codice.get(codice)
            if not esito or not esito.get("applicabile"):
                continue
            if not esito.get("implementato"):
                titoli_da_produrre_a_parte.append(esito)
                continue
            # Difesa contro l'incoerenza catalogo/mappa: se un titolo risulta
            # "implementato" ma non ha un template associato in TEMPLATE_PER_TITOLO,
            # non si va in crash: lo si tratta come "da produrre a parte" e si avvisa.
            info = TEMPLATE_PER_TITOLO.get(codice)
            if info is None:
                titoli_da_produrre_a_parte.append(esito)
                print(
                    f"AVVISO: il titolo {codice} risulta implementato ma manca il "
                    "template associato; verra' elencato tra quelli da produrre a parte.",
                    file=sys.stderr,
                )
                continue
            if info["nome_file"] in file_prodotti_set:
                # Relazione gia' generata da un titolo equivalente (es. C e D).
                continue
            nome_file = f"{numero:02d}_{info['nome_file']}"
            _produci(info["template"], nome_file)
            file_prodotti_set.add(info["nome_file"])
            numero += 1
    except ErroreChecklist as exc:
        print(f"ERRORE: {exc}", file=sys.stderr)
        return 1

    # Titoli applicabili ma non implementati che non rientrano nelle relazioni
    # gestite sopra (B, E, F): vanno comunque elencati come "da produrre a parte".
    for e in esiti:
        if e.get("applicabile") and not e.get("implementato") and e not in titoli_da_produrre_a_parte:
            titoli_da_produrre_a_parte.append(e)

    # 3) Checklist degli allegati e dei controlli finali.
    percorso_checklist_allegati = cartella / "Checklist_Allegati.md"
    _scrivi_checklist_allegati(
        percorso_checklist_allegati,
        documenti_prodotti,
        titoli_da_produrre_a_parte,
        segnaposto_per_documento,
        avvisi,
    )

    # Stampa a video di avvisi e percorso del pacchetto.
    if avvisi:
        print("Avvisi:")
        for avviso in avvisi:
            print(f"  - {avviso}")
        print()

    print(riepilogo(esiti))
    print()
    print("Documenti prodotti:")
    for nome in documenti_prodotti:
        print(f"  - {nome}")
    print(f"  - {percorso_checklist_allegati.name}")
    print()
    print(f"Pacchetto generato in: {cartella.resolve()}")

    return 0


def _scrivi_checklist_allegati(
    percorso: pathlib.Path,
    documenti_prodotti: list[str],
    titoli_da_produrre_a_parte: list[dict[str, Any]],
    segnaposto_per_documento: dict[str, list[str]],
    avvisi: list[str],
) -> None:
    """Scrive ``Checklist_Allegati.md`` con documenti, titoli mancanti e segnaposto residui."""
    righe: list[str] = []
    righe.append("# Checklist degli allegati e controlli finali — AUA")
    righe.append("")
    righe.append("Documento di servizio generato automaticamente: riepiloga i documenti")
    righe.append("prodotti, i titoli ancora da redigere e i punti `[DA COMPLETARE]` da")
    righe.append("rifinire prima della presentazione al SUAP.")
    righe.append("")

    # 1) Documenti prodotti.
    righe.append("## 1. Documenti prodotti")
    righe.append("")
    for nome in documenti_prodotti:
        righe.append(f"- [ ] {nome}")
    righe.append("")

    # 2) Titoli applicabili ma non ancora implementati.
    righe.append("## 2. Titoli applicabili da produrre a parte")
    righe.append("")
    if titoli_da_produrre_a_parte:
        righe.append("I seguenti titoli risultano applicabili ma non sono ancora generati")
        righe.append("automaticamente dall'MVP: il relativo allegato va prodotto a parte.")
        righe.append("")
        for e in titoli_da_produrre_a_parte:
            righe.append(f"- [ ] **[{e['codice']}] {e['nome']}** ({e['riferimento']})")
    else:
        righe.append("Nessun titolo applicabile resta da produrre a parte.")
    righe.append("")

    # 3) Segnaposto residui per documento.
    righe.append("## 3. Segnaposto `[DA COMPLETARE]` residui")
    righe.append("")
    if segnaposto_per_documento:
        righe.append("Punti da completare manualmente nei documenti prodotti:")
        righe.append("")
        for nome, segnaposto in segnaposto_per_documento.items():
            righe.append(f"### {nome}")
            righe.append("")
            for s in segnaposto:
                righe.append(f"- [ ] {s}")
            righe.append("")
    else:
        righe.append("Nessun segnaposto residuo nei documenti prodotti.")
        righe.append("")

    # 4) Avvisi residui dall'intake.
    righe.append("## 4. Avvisi e controlli")
    righe.append("")
    if avvisi:
        for avviso in avvisi:
            righe.append(f"- [ ] {avviso}")
    else:
        righe.append("Nessun avviso dall'intake della checklist.")
    righe.append("")

    percorso.write_text("\n".join(righe), encoding="utf-8")


def _costruisci_parser() -> argparse.ArgumentParser:
    """Costruisce il parser argparse con i due sottocomandi."""
    parser = argparse.ArgumentParser(
        prog="aua",
        description="Generatore di pratiche AUA (DPR 59/2013) per la Regione Campania.",
    )
    sottocomandi = parser.add_subparsers(dest="comando", required=True)

    p_app = sottocomandi.add_parser(
        "applicabilita",
        help="Valuta e stampa i titoli AUA applicabili a partire dalla checklist.",
    )
    p_app.add_argument("checklist", help="Percorso del file checklist YAML.")

    p_gen = sottocomandi.add_parser(
        "genera",
        help="Genera il pacchetto AUA (.docx + Checklist_Allegati.md) dalla checklist.",
    )
    p_gen.add_argument("checklist", help="Percorso del file checklist YAML.")
    p_gen.add_argument(
        "-o",
        "--output",
        required=True,
        help="Cartella di destinazione del pacchetto generato.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Punto d'ingresso della CLI. Restituisce il codice di uscita."""
    parser = _costruisci_parser()
    args = parser.parse_args(argv)

    if args.comando == "applicabilita":
        return _comando_applicabilita(args.checklist)
    if args.comando == "genera":
        return _comando_genera(args.checklist, args.output)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
