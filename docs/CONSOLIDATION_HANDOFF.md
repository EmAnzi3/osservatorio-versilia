# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 11 ottobre 2026

- Baseline #393 mergiata manualmente: main `3ad69bb15e078667ce6e1974856b382e36c799ef`, albero `c3defe4152165051227544b2ca96fb0f790dd8cb`. ACI v39: 200/225 effettivi, 144/181 sorgente, 25 residui, 1.850 domande PASS; Quick/Full locali e CI verdi sulla base #395, evidenze archiviate.
- Catalogo effettivo invariato: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-municipal-tax-adapters`. A6.1–A6.3 pubblicate, A6.4 parziale; A6.5–A6.6 aperte alla revisione metodologica, A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

Fiscalità comunale v40: tre carrier 2025 TARI, IMU e addizionale IRPEF, 7/7. TARI residente 3 persone/100 m² include TEFA e ARERA, Stazzema base ufficiale distinta. IMU su base imponibile 100.000 €, aliquota separata. IRPEF scenari 20/30/50 mila €, alias iniziale e companion effettivo 20 mila distinti; esenzione non franchigia, Seravezza conferma comunale e soglie null esplicite. Solo scenari congelati, nessuna bolletta personale, gettito, qualità servizio o pooling. Serie/trend/anomalie/benchmark/coppie non revisionati rifiutati. Snapshot normalizzati riconciliati, documenti originari non rigiocati. Metodo `docs/A6_MUNICIPAL_TAX_ADAPTERS.md`.

56 celle fisse e prove avversarie; 160 nuove domande, le 1.850 precedenti invariate. Copertura derivata 203/225 effettivi, 147/181 sorgente, 22 residui. Suite 2.010 PASS (1.082 letture/calcoli, 928 rifiuti), audit 203/225 verificato. Report `reports/a6-municipal-tax/`; gate ancora da completare sul medesimo albero.

## Prossima azione

Quick canonico locale prima di ogni push. Full completo locale in clone freddo e CI Quick→Full sul medesimo albero prima della prontezza. Conservare log finali/ricevute, aggiornare prove e PR. Merge riservato al proprietario. Dopo merge manuale scegliere dal residuo derivato; chiusura metodologica distinta dal conteggio adapter.

## Manutenzioni e monitor separati

Radar #395 conservato; monitor e snapshot mensile invariati. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Nessuna acquisizione onerosa; RUNTS non acquisito. #329 refresh ASIA/AGCOM, #306 diagnostica Radar e #117 watchdog fuori dal lotto.

**Definition of done:** il linguaggio naturale facilita l’accesso ai dati ma non diventa una fonte autonoma di numeri o interpretazioni.
