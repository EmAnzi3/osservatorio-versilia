# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 9 ottobre 2026

- Baseline main: #378 `1df5a9aec027b143355fc6e05e5b8de276bb61a1`, albero `6d8886d7c5c19504945ac7a707840d94533ef073`; head GAIA `5eebaaaa411a25838c12814e64d433db98722929`, Quick/Full CI `37963389495` SUCCESS. Catalogo effettivo: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, A6.4 e letture pilota A6.5, issue #330; branch `feat/a6-mef-income`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte alla revisione metodologica. A7 non avviata. Specifica `docs/A6_SEMANTIC_MODEL.md`, contratti semantici e gate canonici governano il lavoro.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; UI, golden, workflow, Radar, 35 letture territoriali e due riepiloghi conservati.

## Lotto in verifica

MEF v29: quattro adapter `incomeDistribution`, `incomeSourceProfile`, `pensionIncomeShare`, `taxpayersAdultPopulationRate`, da snapshot congelati. Otto fasce native vs quattro macrofasce con denominatori distinti; sette fonti con importi/frequenze sovrapposte fra fonti; quota economica pensionistica distinta dalla quota pensionati; contribuenti 2024 / adulti 2026 con periodo ibrido esplicito. Null e zero distinti. Medie/quote aggregate da componenti sommate della stessa dimensione, nessuna somma di persone tra fonti. Serie disponibili 2023–2024 per fonti e pensioni; benchmark Toscana/Italia limitati a lavoro dipendente, pensioni e rapporto contribuenti/adulti. Variazioni/trend/anomalie/correlazioni non revisionate rifiutate. Metodo `docs/A6_MEF_ADAPTERS.md`, report `reports/a6-mef/`.

Copertura derivata 165/225 effettivi, 114/181 sorgente, 60 residui e zero ambientali senza adapter. Suite 802 domande (380 consultazioni/calcoli, 422 rifiuti); 161 osservazioni correnti fisse con alias/null, replay storico distinto 124 con alias, tre rapporti aggregati e sei riferimenti geografici fissi. Nessuna nuova acquisizione o modifica a dati/UI/rendering. Conteggi e risultati vanno letti insieme ai limiti delle operazioni; non attestano completezza A6.

Due attese browser ancora locali dopo il merge GAIA vengono integrate nel nuovo candidato: Demografia aspetta metrica, label e superficie coerente; Percorsi mobile aspetta metrica attiva e richiamo visibile. Timeout limitati 15/10 s, asserzioni/soglie/golden conservati. I gate mirati erano PASS; il Full locale GAIA sul candidato diverso dal head mergiato non ha una ricevuta finale recuperabile, quindi non è attestato verde e non viene riutilizzato. Nuovo Quick/Full locale isolato richiesto su MEF prima della revisione per merge; CI sul medesimo albero. Merge manuale del proprietario.

## Prossima azione

Completare i gate del lotto MEF, aprire la PR e consegnare evidenza Full locale isolato. Dopo merge, proseguire per famiglie RGS (quattro carrier), turismo (sette) e regionali (sei), con verifiche dei componenti e universi. La stima 40–50 ulteriori adapter era una previsione preliminare sul backlog post-GAIA, non una promessa di copertura completa. Restano revisione metodologica, validazione delle letture e avvertenze A6.5–A6.6 prima di A7.

## Manutenzioni e monitor separati

Radar nell'altra chat; #377 incorporata nella baseline, nessuna ulteriore modifica in A6. Monitor leggero/profondo, snapshot mensile e Stati dati conservati; nessuna pubblicazione automatica di nuovi numeri. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Errori di rete non attestano indisponibilità della fonte né cancellano ultime evidenze valide. RUNTS estrazione comunale non acquisita; ACI/Eligendo da verificare con harvester pertinenti. SISBON mappa pubblica distinta dall'export autenticato. #329 refresh ASIA/AGCOM no-op/metadati, #306 diagnostica Radar e #117 watchdog restano fuori dal lotto.
