# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 11 ottobre 2026

- Baseline dopo merge manuale #408: main `042a827eb333e5ceb5f4daed579482d6346b3cb2`, albero `dcfc963049e9d1af185b01addaf9735a56569e1a`, identico al lotto stagionalità verificato. Quick/Full completi locali, CI Quick→Full e A3 verdi. Copertura 210/225 effettivi, 154/181 sorgente, 15 residui, 2.510 domande PASS.
- Catalogo effettivo invariato: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-road-network-adapter`. A6.1–A6.3 pubblicate, A6.4 parziale; A6.5–A6.6 aperte, A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

Grafo viario v46: `roadNetworkProfile`, solo effettivo, 7/7 Comuni. Iter.Net giugno 2022 su confini Istat generalizzati gennaio 2026: periodo ibrido esplicito. Dieci parti pubbliche, alias totale e densità nativa; confronto/rango e pooling solo lunghezza/superficie nativi. Densità stampata arrotondata separatamente, classi amministrative e pavimentazione come due partizioni distinte. Elementi del grafo diversi da strade univoche, condizioni o manutenzione. Replay normalizzato, geometrie originali non rigiocate. Storia, benchmark, anomalie e coppie non revisionate rifiutati. Metodo `docs/A6_ROAD_NETWORK_ADAPTERS.md`.

84 osservazioni fisse, 14 componenti, due rapporti territoriali, puntatori/cache ostile. 202 nuove domande e 2.510 precedenti invariate; suite 2.712 casi (1.527 letture/calcoli, 1.185 rifiuti). Copertura derivata 211/225 effettivi, 154/181 sorgente, 14 residui. Report in `reports/a6-road-network/`; gate canonici da concludere sul medesimo albero.

## Prossima azione

Quick canonico locale prima di ogni push. Pubblicare la PR tecnica dopo Quick GREEN; completare Full locale in clone freddo e CI Quick→Full prima della prontezza. Conservare ricevute/log, verificare identità di alberi e aggiornare PR. Merge riservato al proprietario. Dopo merge scegliere dal residuo derivato; chiusura metodologica distinta dal conteggio adapter.

## Manutenzioni e monitor separati

Manutenzione separata autorizzata 11 ottobre: branch `fix/source-data-sisbon-mimit-20261011`, riallineata a main #408 `042a827`, include Radar #402 pubblicato. SISBON 2.0 CSV pubblico integralmente acquisito, 154 codici (58 attivi/96 chiusi), adapter aggiornato con replay raw e rifiuti invariati; MIMIT 10 ottobre, storico puntuale conservato e mensili fino a settembre invariati. PNRR 25 settembre invariato. RUNTS Excel 11 ottobre acquisito in sola lettura (465 sedi comunali), fotografia candidata corrente distinta dai tassi 2025 non riconciliati. Monitor ARS: 120 secondi per richiesta sull’intero dominio, anche per le rotte derivate dagli snapshot, sia light sia deep; ZIP 255 fornito dal proprietario integro, 88 osservazioni comunali/Versilia 2015–2025 invariate. Stato dati distingue il periodo pubblicato dalle prove storiche del monitor: un periodo cambiato richiede nuova verifica senza inventare date o rilasci. Esiti Quick/Full e monitor live nella PR #407; nessun merge/deploy di questo lotto. #338 conserva il rapporto mensile, #329 ASIA/AGCOM e #117 watchdog restano separati; #306 archiviata.

Manutenzione AGCOM/RUNTS: base main #409 `bc2debb`. RUNTS 11 ottobre verificato nuovamente contro Excel ufficiale (SHA invariato): 465 enti per sede legale, densità con popolazione Istat 1 gennaio 2026; nessuna storia retrocostruita. AGCOM: periodi validati dinamicamente e coerenti 7/7 negli shard; import primario lega il CSV al catalogo ufficiale datato. Corretta l’etichetta 2025 dei valori già congelati e dei benchmark dello stesso CSV: consistenze ufficiali 6 luglio 2026, revisione 14 luglio; date di acquisizione preservate. Solo 110 domande connettività riallineate nei riferimenti, altre 2.602 invariate. Nessun nuovo CSV acquisito: ArcGIS restituisce errore interno. Test mirati passano; Quick/Full da concludere prima della prontezza. Nessuna modifica grafica, merge riservato al proprietario.
