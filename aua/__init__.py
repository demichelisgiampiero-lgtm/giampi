"""Generatore di pratiche AUA (Autorizzazione Unica Ambientale) - Regione Campania.

DPR 13 marzo 2013, n. 59.

MVP: a partire da una checklist compilata dal cliente (file YAML), il pacchetto
determina quali titoli ambientali devono confluire nell'AUA e genera la
documentazione (Modello Unico + relazioni tecniche) in formato Word editabile.

Titoli implementati in questa versione:
  - C/D: Emissioni in atmosfera (art. 269 / art. 272 c.2 D.Lgs. 152/2006)
  - A:   Scarichi di acque reflue (art. 124 D.Lgs. 152/2006)
  - G:   Recupero rifiuti in procedura semplificata (artt. 215-216 D.Lgs. 152/2006)
"""

__version__ = "0.1.0"
