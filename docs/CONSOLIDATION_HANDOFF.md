# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 9 ottobre 2026

- Baseline main: #381 `eb40123c6b9a65dac4d9f3f08e21cb19719819ba`, albero `3fab1045fe6688f6f4b5ebc787f9005effaa9c42`. Merge manuale del proprietario distinto dai gate: Full Linux freddo canonico exit 0 (09/10, 21:54:50–22:36:27 UTC), 40 golden, 578 controlli browser e Lighthouse verdi, checkout pulito; CI Quick/Full `37995764220` SUCCESS sul head `d33b419f3f21f4d55b1c4feadba7557060e295f8`. Ricevuta/log completi consegnati in `A6_Turismo_Full_locale_isolato_20261009.zip`. Tentativo Windows fallito nel Quick per separatori path, distinto dal Linux; primo Full Linux in checkout riusato dopo Quick fallito per output Atlas residui, conservato separatamente. Deploy main `37999080864` e live `37999964536` SUCCESS.
- Catalogo effettivo: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-regional-indicators`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte alla revisione metodologica; A7 non avviata. Specifica `docs/A6_SEMANTIC_MODEL.md` e gate canonici governano il lavoro.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; UI, golden, workflow, Radar, 35 letture territoriali e due riepiloghi conservati.

## Lotto in verifica

Indicatori comunali regionali v32: sei nuovi carrier, SAU biologica già coperta esclusa dal conteggio. Percentuali, tasso di disabilità 0–64 e P75 118 pubblicati; formule/universi espliciti, conteggi e distribuzioni native assenti. Servizi online al definitivo 2022, paniere 2018/2022 diverso; giovani 2020 assente. Serie leggibili e gap Toscana ufficiali al solo riferimento corrente; nessuna ponderazione, componente retro-derivata, continuità temporale o coppia automatica. Metodo `docs/A6_REGIONAL_ADAPTERS.md`, report `reports/a6-regional/`.

Copertura derivata 181/225 effettivi, 130/181 sorgente, 44 residui, zero ambientali senza adapter. Suite 1.053 domande (473 consultazioni/calcoli, 580 rifiuti); 42 osservazioni fisse correnti, sei benchmark e 36 celle storiche fisse; replay separato 252 celle congelate. 58 collegamenti e 29 companion conservati; 84 carichi descrittivi. Dati/UI/golden/workflow/Radar/letture conservati. Quick/Full locali e CI del candidato da completare prima della prontezza per il merge.

## Prossima azione

Completare i gate canonici regionali in checkout isolati distinti, consegnare PR tecnica ed evidenza completa. Nessun merge/deploy automatico. Dopo merge manuale, scegliere il successivo lotto dal residuo derivato, senza ricontare carrier coperti. Revisione metodologica A6.4–A6.6 separata dal numero di adapter; A7 non avviata.

## Manutenzioni e monitor separati

Radar nell'altra chat; #377 incorporata nella baseline, nessuna modifica in A6. Monitor leggero/profondo, snapshot mensile e Stato dati conservati; nessuna pubblicazione automatica di nuovi numeri. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Errori di rete non attestano indisponibilità della fonte né cancellano ultime evidenze valide. RUNTS estrazione comunale non acquisita; ACI/Eligendo da verificare con harvester pertinenti. SISBON mappa pubblica distinta dall'export autenticato. #329 refresh ASIA/AGCOM no-op/metadati, #306 diagnostica Radar e #117 watchdog fuori dal lotto.
