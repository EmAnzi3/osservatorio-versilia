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

Radar #402 conservato; monitor e snapshot mensile invariati. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Nessuna acquisizione onerosa; RUNTS non acquisito. #329 refresh ASIA/AGCOM, #306 diagnostica Radar e #117 watchdog fuori dal lotto.
