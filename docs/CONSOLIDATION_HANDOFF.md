# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 11 ottobre 2026

- Baseline #400 mergiata manualmente: main `e7ba93a3a40cea80cc5063640cbdf2040565450f`. TPL v41: 206/225 effettivi, 150/181 sorgente, 19 residui e 2.111 domande PASS; Quick/Full locali e CI verdi, evidenze archiviate.
- Catalogo effettivo invariato: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-erp-adapter`. A6.1–A6.3 pubblicate, A6.4 parziale; A6.5–A6.6 aperte alla revisione metodologica, A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

ERP Lucca v42: un carrier 7/7, cinque esercizi 2020–2024. Percentuali pubbliche distinte dai rapporti nativi, pooling delle somme comunali soltanto sullo stesso esercizio. Importi cumulati per fitti/spese accessorie, non famiglie o canoni annui. Serie consultabili; variazioni/trend, anomalie, benchmark e coppie non revisionate rifiutati. Intestazione 2022 e percentuali 2023 incoerenti esplicite, emesso Massarosa 2023 conservato senza correzioni. Snapshot contabile normalizzato riconciliato; PDF originari non rigiocati. Metodo `docs/A6_ERP_ADAPTERS.md`.

35 celle pubbliche, 70 importi fissi, cinque totali/rapporti territoriali e prove avversarie. 124 nuove domande e 2.111 precedenti invariate; suite 2.235 PASS. Copertura derivata 207/225 effettivi, 151/181 sorgente, 18 residui. Report `reports/a6-erp/`; gate canonici da concludere sul medesimo albero.

## Prossima azione

Quick canonico locale prima di ogni push. Full completo locale in clone freddo e CI Quick→Full sul medesimo albero prima della prontezza. Conservare log finali/ricevute, aggiornare prove e PR. Merge riservato al proprietario. Dopo merge manuale scegliere dal residuo derivato; chiusura metodologica distinta dal conteggio adapter.

## Manutenzioni e monitor separati

Radar #395 conservato; monitor e snapshot mensile invariati. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Nessuna acquisizione onerosa; RUNTS non acquisito. #329 refresh ASIA/AGCOM, #306 diagnostica Radar e #117 watchdog fuori dal lotto.

**Definition of done:** il linguaggio naturale facilita l’accesso ai dati ma non diventa una fonte autonoma di numeri o interpretazioni.
