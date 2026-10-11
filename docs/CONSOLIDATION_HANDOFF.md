# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 11 ottobre 2026

- Baseline dopo merge manuale #406: main `63dace2c810bb9b13223fb1c360b282aa6a770c9`, albero `6fdf52029a1918c424b1f13e17f356b7963dd5e7`, identico al lotto ospedali verificato. Quick/Full completi locali e CI della #406 verdi; evidenze del merge distinte dalle identità di commit della PR. Copertura 209/225 effettivi, 153/181 sorgente, 16 residui, 2.476 domande PASS.
- Catalogo effettivo invariato: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-tourism-seasonality-adapter`. A6.1–A6.3 pubblicate, A6.4 parziale; A6.5–A6.6 aperte, A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

Concentrazione turistica v45: quota annuale 2025 dei tre mesi con più presenze, 7/7 Comuni; confronto, rango e scostamento Toscana in punti percentuali. Mesi selezionati per geografia, non trimestre estivo fisso; concentrazione distinta da volume/performance. Replay dei valori pubblici e risultato A3, non del pannello mensile originario assente. Vietate retro-derivazione, pooling dei numeratori locali, storico/mesi, benchmark Italia/Versilia, anomalie e coppie non revisionate. Metodo `docs/A6_SEASONALITY_ADAPTERS.md`.

Sette quote e sette gap fissi indipendenti; puntatori, cache ostile e controesempio sulla selezione dei massimi. 34 nuove domande e 2.476 precedenti invariate; suite 2.510 PASS (1.429 letture/calcoli, 1.081 rifiuti). Copertura derivata 210/225 effettivi, 154/181 sorgente, 15 residui. Report in `reports/a6-seasonality/`; gate canonici da concludere sul medesimo albero.

## Prossima azione

Quick canonico locale prima di ogni push. Pubblicare la PR tecnica dopo Quick GREEN; completare Full locale in clone freddo e CI Quick→Full prima della prontezza. Conservare ricevute/log, verificare identità di alberi e aggiornare PR. Merge riservato al proprietario. Dopo merge scegliere dal residuo derivato; chiusura metodologica distinta dal conteggio adapter.

## Manutenzioni e monitor separati

Manutenzione separata autorizzata 11 ottobre: branch `fix/source-data-sisbon-mimit-20261011`, riallineata a main #408 `042a827`, include Radar #402 pubblicato. SISBON 2.0 CSV pubblico integralmente acquisito, 154 codici (58 attivi/96 chiusi), adapter aggiornato con replay raw e rifiuti invariati; MIMIT 10 ottobre, storico puntuale conservato e mensili fino a settembre invariati. PNRR 25 settembre invariato. RUNTS Excel 11 ottobre acquisito in sola lettura (465 sedi comunali), fotografia candidata corrente distinta dai tassi 2025 non riconciliati. Monitor ARS: 120 secondi per richiesta sull’intero dominio, anche per le rotte derivate dagli snapshot, sia light sia deep; ZIP 255 fornito dal proprietario integro, 88 osservazioni comunali/Versilia 2015–2025 invariate. Stato dati distingue il periodo pubblicato dalle prove storiche del monitor: un periodo cambiato richiede nuova verifica senza inventare date o rilasci. Esiti Quick/Full e monitor live nella PR #407; nessun merge/deploy di questo lotto. #338 conserva il rapporto mensile, #329 ASIA/AGCOM e #117 watchdog restano separati; #306 archiviata.
