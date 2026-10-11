# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 11 ottobre 2026

- Baseline #401 mergiata dal proprietario: main `ecd70b974f5459e56abe5c85e094331d54e9ec26`, comprende anche Radar #398. ERP v42: 207/225 effettivi, 151/181 sorgente, 18 residui e 2.235 domande PASS; Quick/Full locali e CI della PR verdi, build/deploy post-merge `38134850469` SUCCESS. Evidenze sul merge effettivo tenute separate da quelle dell'albero PR.
- Catalogo effettivo invariato: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-real-income-adapter`. A6.1–A6.3 pubblicate, A6.4 parziale; A6.5–A6.6 aperte alla revisione metodologica, A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

Redditi vs inflazione v43: un carrier 7/7, nove anni d'imposta 2016–2024, viste reale/nominale con base 2016. Reddito imponibile medio comunale distinto da reddito familiare disponibile; NIC nazionale distinto dai prezzi locali. Pannelli MEF normalizzati degli estremi riconciliati, anni intermedi dal catalogo pubblico; archivi originali non rigiocati. Gap Toscana/Italia solo reali 2024, da rapporti delle medie aggregate. Pooling, variazioni/trend, benchmark nominali/storici, anomalie e coppie non revisionate rifiutati. Metodo `docs/A6_REAL_INCOME_ADAPTERS.md`.

126 celle pubbliche fisse, 28 componenti degli estremi, quattro totali, 14 gap, nove indici NIC e prove avversarie in cache; replay distinto dei 15.876 record normalizzati. 192 nuove domande e 2.235 precedenti invariate; suite 2.427 PASS (1.398 calcoli/letture, 1.029 rifiuti). Copertura derivata 208/225 effettivi, 152/181 sorgente, 17 residui. Report `reports/a6-real-income/`; gate canonici da concludere sul medesimo albero.

## Prossima azione

Quick canonico locale prima di ogni push. Full completo locale in clone freddo e CI Quick→Full sul medesimo albero prima della prontezza. Conservare log finali/ricevute, aggiornare prove e PR. Merge riservato al proprietario. Dopo merge manuale scegliere dal residuo derivato; chiusura metodologica distinta dal conteggio adapter.

## Manutenzioni e monitor separati

Manutenzione separata autorizzata 11 ottobre: branch `fix/source-data-sisbon-mimit-20261011`, base main #403 `0fc9af7`, include Radar #402 pubblicato. SISBON 2.0 CSV pubblico integralmente acquisito, 154 codici (58 attivi/96 chiusi), adapter aggiornato con replay raw e rifiuti invariati; MIMIT 10 ottobre, storico puntuale conservato e mensili fino a settembre invariati. PNRR 25 settembre invariato. RUNTS Excel 11 ottobre acquisito in sola lettura (465 sedi comunali), fotografia candidata corrente distinta dai tassi 2025 non riconciliati. Esiti Quick/Full e monitor live nella PR dedicata; nessun merge/deploy di questo lotto. #338 conserva il rapporto mensile, #329 ASIA/AGCOM e #117 watchdog restano separati; #306 archiviata.
