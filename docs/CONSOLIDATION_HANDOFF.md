# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 11 ottobre 2026

- Baseline dopo il merge manuale #403: main `0fc9af79e097c8abcbe66a63bf8d290f0072b5c8`, comprende Radar #402. Redditi v43: 208/225 effettivi, 152/181 sorgente, 17 residui, 2.427 domande PASS. Quick/Full locali e CI della PR verdi; Full completo sul merge effettivo GREEN, build/deploy post-merge `38141187066` SUCCESS. Alberi ed evidenze distinti.
- Catalogo effettivo invariato: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-hospital-adapter`. A6.1–A6.3 pubblicate, A6.4 parziale; A6.5–A6.6 aperte, A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

Strutture ospedaliere v44: un carrier 7/7, due viste 2025. Presidi localizzati distinti dai posti letto ogni 10.000 residenti. Confronto/ordinamento numerico di valori pubblici, non accessibilità, qualità o priorità politica. Replay del catalogo, non dei record ministeriali; data esatta dello stock, componenti e data del denominatore del tasso non congelati separatamente. Nessuna retro-derivazione, pooling, benchmark geografico, storia o coppia non revisionata. Metodo `docs/A6_HOSPITAL_ADAPTERS.md`.

14 riferimenti pubblici indipendenti, zeri/pari merito, puntatori e prove ostili dopo cache. 49 nuove domande e 2.427 precedenti invariate; suite 2.476 PASS (1.414 letture/calcoli, 1.062 rifiuti). Copertura derivata 209/225 effettivi, 153/181 sorgente, 16 residui; collegamenti derivati in `reports/a6-hospitals/`; gate canonici da concludere sul medesimo albero.

## Prossima azione

Quick canonico locale prima di ogni push. Full completo locale in clone freddo e CI Quick→Full sul medesimo albero prima della prontezza. Conservare log finali/ricevute, aggiornare prove e PR. Merge riservato al proprietario. Dopo merge manuale scegliere dal residuo derivato; chiusura metodologica distinta dal conteggio adapter.

## Manutenzioni e monitor separati

Manutenzione separata autorizzata 11 ottobre: branch `fix/source-data-sisbon-mimit-20261011`, riallineata a main #406 `63dace2`, include Radar #402 pubblicato. SISBON 2.0 CSV pubblico integralmente acquisito, 154 codici (58 attivi/96 chiusi), adapter aggiornato con replay raw e rifiuti invariati; MIMIT 10 ottobre, storico puntuale conservato e mensili fino a settembre invariati. PNRR 25 settembre invariato. RUNTS Excel 11 ottobre acquisito in sola lettura (465 sedi comunali), fotografia candidata corrente distinta dai tassi 2025 non riconciliati. Monitor ARS: 120 secondi per richiesta sia light sia deep; ZIP 255 fornito dal proprietario integro, 88 osservazioni comunali/Versilia 2015–2025 invariate. Esiti Quick/Full e monitor live nella PR #407; nessun merge/deploy di questo lotto. #338 conserva il rapporto mensile, #329 ASIA/AGCOM e #117 watchdog restano separati; #306 archiviata.
