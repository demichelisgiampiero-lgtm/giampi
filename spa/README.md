# Studi Preliminari Ambientali (SPA) — Regione Campania

Materiale per il confronto comparato tra Studi Preliminari Ambientali presentati
nell'ambito delle procedure di verifica di assoggettabilità a VIA (art. 19
D.lgs. 152/2006) presso la Regione Campania.

## Dove si trovano gli SPA

| Risorsa | URL |
|---|---|
| Elenco Regionale Progetti (accesso pubblico) | https://servizi-digitali.regione.campania.it/Public/AccessoPubblico/ViaVas/ElencoProgetti?Tipo=via |
| Area VIA — Verifica di assoggettabilità | https://viavas.regione.campania.it/opencms/opencms/VIAVAS/VIA_Verifica_Ass_NP |
| Portale VIAVAS (home) | https://viavas.regione.campania.it/opencms/opencms/VIAVAS |
| Presentazione istanze (dal 17/03/2025, con SPID/CIE/CNS) | https://servizi-digitali.regione.campania.it/via |

Gli allegati dei singoli procedimenti seguono il pattern:

```
http://viavas.regione.campania.it/opencms/export/sites/default/VIAVAS/download/allegati/<ISTRUTTORE>/<ID_PROCEDIMENTO>/<NOME_FILE>.pdf
```

dove `<ISTRUTTORE>` è la cartella del funzionario istruttore (es. `Rizzotto`,
`D_Alterio`, `Del_Piano`) e `<ID_PROCEDIMENTO>` il numero del procedimento.

## Come scaricare

```bash
./scripts/scarica_spa.sh                    # usa spa/urls.txt -> spa/pdf/
./scripts/scarica_spa.sh altro_elenco.txt   # elenco alternativo
```

Lo script:

- salta i file già scaricati (ripartenza sicura);
- riprova fino a 4 volte con backoff esponenziale (2s, 4s, 8s, 16s);
- verifica che il file scaricato sia realmente un PDF e non una pagina di
  errore HTML (in tal caso lo rinomina `.non-pdf` e lo segnala);
- stampa un riepilogo finale con l'elenco dei download falliti.

I PDF finiscono in `spa/pdf/`, che è escluso dal versionamento
(vedi `.gitignore`).

## Stato: download non eseguito in sessione remota

Nella sessione Claude Code remota **la policy di rete blocca tutto l'egress
verso host esterni**: ogni richiesta a `viavas.regione.campania.it` e
`servizi-digitali.regione.campania.it` riceve `403 CONNECT tunnel failed` dal
proxy (il blocco riguarda qualsiasi dominio non in allowlist, verificato anche
su `example.com`). Lo script è stato testato ed è funzionante: fallisce solo
sul blocco di rete.

Per completare il download servono una di queste opzioni:

1. eseguire `./scripts/scarica_spa.sh` in locale;
2. modificare la policy di rete dell'ambiente remoto per consentire i due
   domini — vedi https://code.claude.com/docs/en/claude-code-on-the-web

## Riferimento metodologico per il confronto

Gli "Indirizzi per la predisposizione dello Studio Preliminare Ambientale"
(DD n. 3 del 10/01/2022, allegato alla DGR 613/2021) definiscono la struttura
attesa di un SPA e sono la griglia naturale per il confronto comparato:

http://viavas.regione.campania.it/opencms/export/sites/default/VIAVAS/download/DGR_613_28122021/INDIRIZZI_SPA_Gennaio2022_rev01.pdf
