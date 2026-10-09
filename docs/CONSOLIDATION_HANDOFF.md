# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 9 ottobre 2026

- Baseline main: #380 `f187b9fccfb187341ce900193a5fd6cd97a485c9`, albero `d1603659c1e7f6db6e49f7b8a64d58f4088b4006`. RGS Quick/Full CI `37986028181` SUCCESS sul head `c8f7c46909634eec2f6a4b6a33f48ffb41a17569`; nuovo Full locale isolato exit 0, 40 golden, 578 controlli browser e Lighthouse verdi, checkout pulito. Ricevuta completa consegnata in `PR380_Full_locale_isolato_20261009.zip`; nessun verde attribuito retroattivamente al Full MEF interrotto.
- Catalogo effettivo: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-tourism-adapters`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte alla revisione metodologica; A7 non avviata. Specifica `docs/A6_SEMANTIC_MODEL.md` e gate canonici governano il lavoro.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; UI, golden, workflow, Radar, 35 letture territoriali e due riepiloghi conservati.

## Lotto in verifica

Turismo v31: sei nuovi adapter più rafforzamento delle presenze già governate. Movimento 2023–2025 al netto delle locazioni; capacità Istat 2024 distinta dai residenti stimati 1 gennaio 2026. Quota estera pubblicata a un decimale e dimensione `nativeRatio` non arrotondata separate; nessuna retro-derivazione. Pannello Istat 7.899 Comuni, 273 toscani, totali provinciali/nazionale esclusi dalla somma; ampliamento del 2025 escluso. Storico posti letto 2002–2024 leggibile, nessun rapporto storico con residenti 2026 inventato. Operazioni già ammesse sulle presenze preservate; nuove variazioni/trend/anomalie/coppie non revisionate rifiutate per gli altri carrier. Metodo `docs/A6_TOURISM_ADAPTERS.md`, report `reports/a6-tourism/`.

Copertura derivata 175/225 effettivi, 124/181 sorgente, 50 residui e zero ambientali senza adapter. Suite 960 domande (449 consultazioni/calcoli, 511 rifiuti); 56 osservazioni fisse correnti, quattro rapporti territoriali e dieci benchmark; replay separato di 245 celle storiche congelate. 58 collegamenti tipizzati e 29 companion conservati; 81 carichi descrittivi senza promessa di prestazioni. Nessuna nuova acquisizione o modifica a dati/UI/rendering/golden/workflow/Radar. Quick/Full locali e CI del candidato da completare prima del merge manuale.

## Prossima azione

Completare i gate canonici del lotto turismo e consegnare l’evidenza Full isolata. Dopo merge, proseguire con i carrier regionali, previa verifica dei componenti e universi. La stima preliminare di ulteriori adapter non è una promessa; i carrier già coperti non vengono ricontati. A6.4 parziale; revisione metodologica e validazione delle letture A6.5–A6.6 aperte; A7 non avviata.

## Manutenzioni e monitor separati

Radar nell'altra chat; #377 incorporata nella baseline, nessuna modifica in A6. Monitor leggero/profondo, snapshot mensile e Stato dati conservati; nessuna pubblicazione automatica di nuovi numeri. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Errori di rete non attestano indisponibilità della fonte né cancellano ultime evidenze valide. RUNTS estrazione comunale non acquisita; ACI/Eligendo da verificare con harvester pertinenti. SISBON mappa pubblica distinta dall'export autenticato. #329 refresh ASIA/AGCOM no-op/metadati, #306 diagnostica Radar e #117 watchdog fuori dal lotto.
