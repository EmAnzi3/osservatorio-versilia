# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 9 ottobre 2026

- Baseline main: `9e8c4c3c16284ca96bab1fead7225180e9d4b258`, merge #377 Radar; albero `91c3d0db9988d13c01e92bf40915658d2c1fab4e`. Quick/Full CI `37953459734` verdi. Il lotto GAIA è riallineato a questa baseline; Full locale isolato richiesto sul candidato combinato. Catalogo effettivo: 225 indicatori, 124 storici e 137 confronti; conteggi derivati.
- A0–A5 DONE. A5 chiusa con #280; UI approvate e correzioni #313–315/#322 preservate. Camaiore resta protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; golden e altri lock restano attivi.
- Workstream attivo: **A6**, step **A6.4 e letture pilota A6.5**, issue **#330**, branch `feat/a6-gaia-water-quality`. A6.2–A6.3: contratto e guardie pubblicati con #331 (merge manuale del proprietario). A6.1 chiusa con merge autorizzato di #301. Specifica `docs/A6_SEMANTIC_MODEL.md`, contratto `ci/semantic-model-contract.json`, validatore e regressione integrati nel Quick per sorgente ed Effective Public Catalog.
- A6.1 definisce invarianti e struttura; non è ancora un motore di interrogazione. A6.2 operazioni, A6.3 comparabilità e A6.4 motore devono precedere le letture A6.5 e la chiusura A6.6. A7 non parte prima della chiusura metodologica A6.
- Perimetro del lotto: motore deterministico, test e documentazione; nessuna modifica a dati, asset, renderer, homepage, temi, schede comunali o golden.

## Dati e monitor pubblicati

- #327: carburanti puntuali 3 ottobre; PNRR snapshot 25 settembre (78/101 conclusioni, finanziamenti invariati); monitor con ruoli dei percorsi ufficiali, tentativi/esiti e separazione rete/rilascio/acquisizione. Errori non cancellano dati o ultime evidenze valide.
- #328: MIMIT mensile 57 mesi gennaio 2022–settembre 2026, JSON pubblico verificato identico al candidato. Luglio 31/31, agosto 31/31, settembre 29/30; 5 settembre assente nell'archivio ufficiale, nessuna stima. Provenienza e SHA in `reports/data-checks/mimit-monthly-2026-q3.md`.
- Monitor profondo mensile il 5; schedulazione mensile il giorno 5. Snapshot e artifact del monitor alimentano Stato Dati tramite selezione canonica. Nessuna pubblicazione automatica di nuovi numeri.

## Manutenzioni separate, non bloccanti per A6

- #329: refresh ASIA/AGCOM senza nuovi dati eliminava sei `meta.benchmark`; #324 chiusa senza merge. Correggere preservazione dei metadati e rilevamento dei no-op nel suo lotto.
- #306: diagnostica Radar; #117: proposta watchdog Cloudflare. Restano aperte; non incorporarli in A6.
- SISBON mappa pubblica: `https://sisbon.regione.toscana.it/api/v1/sisbon/map_public?format=csv` HTTP 200; lo snapshot versionato non prova il live. Integrare il controllo periodico della mappa nel lotto monitor, separato dall'export autenticato `export_mosaico`.
- ARS: sette export ottenuti con attesa 33–57 secondi, hash invariati; ARPAT CSV ottenuto/hash invariato. RUNTS Excel ottenuto, estrazione comunale non acquisita. ACI ed Eligendo restano da verificare con percorsi pertinenti/harvester; gli errori 503/403 del nostro ambiente non dimostrano indisponibilità della fonte o nuovi dati.
- Pulizia conclusa: 11 PR superate chiuse e 39 issue storiche archiviate con motivazione; cronologia e branch conservati. Registro #11 e attività correnti conservati.

## Prossima azione

Checkpoint A6 #376 verificato: main `541e244ad7d1626fef126ceb6aae7085c8e897a6`, albero `3c352a60097ca70b8a2271e79aa17720c055c7a3`; Quick/Full CI `37948936878` SUCCESS. Full locale isolato #376 exit 0, 40 golden e 578 combinazioni browser, stesso albero, checkout pulito; evidenza `PR376_Full_locale_isolato_20261009.zip`. Guardia mobile Percorsi conservata.

Baseline corrente #377 `9e8c4c3c16284ca96bab1fead7225180e9d4b258`, albero `91c3d0db9988d13c01e92bf40915658d2c1fab4e`; CI `37953459734` SUCCESS. Primo Full GAIA sulla baseline #376 interrotto per riallineamento prima della fine del Quick, nessun gate riutilizzato. Nuovo Full isolato sul candidato combinato. Radar incorporato come baseline già mergiata, senza ulteriori modifiche nel lotto.

Lotto GAIA v28: consultazione `lookup` dei valori medi pubblicati per località e parametro, 70 × 17 celle del 2° semestre 2025. Identità della località subordinate al Comune canonico; unità, stringhe, qualificatori `<`/`>` e riferimenti originali conservati. Nessuna media comunale, sostituzione dei censurati, rango, associazione o giudizio di potabilità. Contratto lookup distinto dai calcoli numerici, con provenienza e riconciliazione completa snapshot/catalogo/cache. Metodo `docs/A6_WATER_QUALITY_ADAPTERS.md`, report `reports/a6-water-quality/`.

Copertura 161/225 effettivi, 110/181 sorgente; 64 residui e zero ambientali senza adapter, senza dichiarare completezza delle operazioni. Suite 736 domande (344 consultazioni/calcoli, 392 rifiuti), 24 celle fisse e sette conteggi, replay distinto di 1.190 celle; 58 collegamenti e 72 carichi descrittivi. Dati/UI/asset/golden/workflow/Radar/Camaiore e 35 letture + due riepiloghi conservati. A6.4 parziale, A6.5–A6.6 aperte e A7 non avviata. Quick/Full locali e CI canonica prima del merge del proprietario. Dopo il lotto, proseguire il censimento dei 64 residui per famiglie effettive e la revisione metodologica; Radar nell’altra chat.
