# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 11 ottobre 2026

- Baseline #397 mergiata manualmente: main `019142abcb816a2edf63b159c065de3e62bf3ca0`, albero `e914c5e4bb1c46df8be11fd6ba3a9ff3f82b4d67`. Fiscalità v40: 203/225 effettivi, 147/181 sorgente, 22 residui e 2.010 domande PASS; Quick/Full locali e CI verdi, evidenze archiviate.
- Catalogo effettivo invariato: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-tpl-adapters`. A6.1–A6.3 pubblicate, A6.4 parziale; A6.5–A6.6 aperte alla revisione metodologica, A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

TPL v41: tre carrier, 7/7, giornata programmata 26 agosto 2026. Corse assolute e per residenti, punti GTFS assoluti e per residenti, ampiezza oraria in secondi GTFS con ore oltre 24 conservate. Universo trip-comune diverso dalle corse territoriali uniche; coppie feed/stop_id diverse dalle fermate fisiche; finestra diversa dalla frequenza. Denominatori al 1 gennaio 2026 espliciti. Nessuna misura di affidabilità, passeggeri o accessibilità pedonale. Confronto/rango ammessi; pooling, storia, trend, anomalie, benchmark e coppie non revisionate rifiutati. Snapshot normalizzato riconciliato, calendari/feed/geometrie originari non rigiocati. Metodo `docs/A6_TPL_ADAPTERS.md`.

35 celle pubbliche fisse, 14 componenti bus/ferrovia, 14 orari in secondi e prove avversarie. 101 nuove domande e 2.010 precedenti invariate; suite 2.111 PASS (1.127 letture/calcoli, 984 rifiuti). Copertura derivata 206/225 effettivi, 150/181 sorgente, 19 residui. Report `reports/a6-tpl/`; gate canonici da concludere sul medesimo albero.

## Prossima azione

Quick canonico locale prima di ogni push. Full completo locale in clone freddo e CI Quick→Full sul medesimo albero prima della prontezza. Conservare log finali/ricevute, aggiornare prove e PR. Merge riservato al proprietario. Dopo merge manuale scegliere dal residuo derivato; chiusura metodologica distinta dal conteggio adapter.

## Manutenzioni e monitor separati

Radar #395 conservato; monitor e snapshot mensile invariati. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Nessuna acquisizione onerosa; RUNTS non acquisito. #329 refresh ASIA/AGCOM, #306 diagnostica Radar e #117 watchdog fuori dal lotto.

**Definition of done:** il linguaggio naturale facilita l’accesso ai dati ma non diventa una fonte autonoma di numeri o interpretazioni.
