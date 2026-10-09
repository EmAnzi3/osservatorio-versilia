# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 9 ottobre 2026

- Baseline main: #379 `c953f1275e5a896387a3eec8b09a7607b75b87ad`, albero `4468fd8377b31c51ab19fafc9830bbf780469ddc`; head MEF `bfb58d791caeea7434d65f7b9483068c3c27a83c`, Quick/Full CI `37976227645` SUCCESS. Catalogo effettivo: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, A6.4 e letture pilota A6.5, issue #330; branch `feat/a6-rgs-staff`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte alla revisione metodologica. A7 non avviata. Specifica `docs/A6_SEMANTIC_MODEL.md`, contratti semantici e gate canonici governano il lavoro.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; UI, golden, workflow, Radar, 35 letture territoriali e due riepiloghi conservati.

## Lotto in verifica

RGS v30: quattro adapter per organico/residenti, classi d’età, formazione e turnover netto. Componenti congelate, identità datore/comune, stock 31 dicembre vs residenti 1 gennaio 2024 espliciti; Unioni escluse. Rapporto aggregato per organico, età e saldo netto; nessuna ponderazione delle medie RGS formazione. Gap Toscana organico dal pannello 273/273, due zero PIAO espliciti; gap formazione dalla selezione congiunta API Versilia, senza media dei Comuni. Italia, serie, variazioni, trend, anomalie e correlazioni non certificate rifiutate. Metodo `docs/A6_RGS_ADAPTERS.md`, report `reports/a6-rgs/`.

Copertura derivata 169/225 effettivi, 118/181 sorgente, 56 residui e zero ambientali senza adapter. Suite 872 domande (415 consultazioni/calcoli, 457 rifiuti); 126 osservazioni fisse con alias, cinque rapporti aggregati e otto riferimenti pubblicati con alias. 58 collegamenti tipizzati e 29 link companion conservati; 78 carichi descrittivi senza promessa di prestazioni. Nessuna nuova acquisizione o modifica a dati/UI/rendering/golden/workflow/Radar.

La baseline recuperata coincide byte per byte con l’albero mergiato #379. Il Full locale MEF interrotto non ha una ricevuta finale recuperabile; il verde CI resta un’evidenza distinta. Nessun Full locale precedente viene riutilizzato. Le attese Demografia/Percorsi della #379 sono conservate, con asserzioni e soglie invariate. Nuovo Quick/Full locale canonico su checkout isolato del candidato RGS; CI sul medesimo albero prima della revisione per merge manuale del proprietario.

## Prossima azione

Completare Quick/Full locali e CI del lotto RGS e consegnare l’evidenza isolata. Dopo merge, proseguire con turismo (sette carrier) e regionali (sei), previa verifica dei componenti e universi. La stima 40–50 ulteriori adapter post-GAIA resta preliminare, non una promessa. A6.4 parziale, revisione metodologica e validazione delle 35 letture/due riepiloghi A6.5–A6.6 aperte; A7 non avviata.

## Manutenzioni e monitor separati

Radar nell'altra chat; #377 incorporata nella baseline, nessuna ulteriore modifica in A6. Monitor leggero/profondo, snapshot mensile e Stati dati conservati; nessuna pubblicazione automatica di nuovi numeri. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Errori di rete non attestano indisponibilità della fonte né cancellano ultime evidenze valide. RUNTS estrazione comunale non acquisita; ACI/Eligendo da verificare con harvester pertinenti. SISBON mappa pubblica distinta dall'export autenticato. #329 refresh ASIA/AGCOM no-op/metadati, #306 diagnostica Radar e #117 watchdog restano fuori dal lotto.
