# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 9 ottobre 2026

- Baseline main: `9865ba4c79344f81d6c37a0e26f57f1620d5e3ab`, merge #369; albero `ebcc50dbeb3a9d77b2ffb88a08970fa5442a0112`. Quick/Full CI `37863716188` e Full locale isolato #369 verdi sullo stesso albero. Catalogo effettivo: 225 indicatori, 124 storici e 137 confronti; conteggi derivati.
- A0–A5 DONE. A5 chiusa con #280; UI approvate e correzioni #313–315/#322 preservate. Camaiore resta protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; golden e altri lock restano attivi.
- Workstream attivo: **A6**, step **A6.4 e letture pilota A6.5**, issue **#330**, branch `feat/a6-pab-adapters`. A6.2–A6.3: contratto e guardie pubblicati con #331 (merge manuale del proprietario). A6.1 chiusa con merge autorizzato di #301. Specifica `docs/A6_SEMANTIC_MODEL.md`, contratto `ci/semantic-model-contract.json`, validatore e regressione integrati nel Quick per sorgente ed Effective Public Catalog.
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

Baseline verificata: #369 mergiata, main `9865ba4c79344f81d6c37a0e26f57f1620d5e3ab`, albero `ebcc50dbeb3a9d77b2ffb88a08970fa5442a0112`. Quick/Full CI `37863716188` e Full locale isolato #369 verdi; evidenza `PR369_Full_locale_isolato_20261009.zip`.

Lotto corrente PAB v24: sette carrier, A-1 approvato / km-intervento degli export / stato operativo WFS separati. 1.259 codici A-1, 1.265 feature operative; quote in corso e completate esclusivamente sullo stesso inventario operativo al 31 agosto, nessuna falsa percentuale di esecuzione del piano. Importi operativi non spesa pagata o budget approvato; km-intervento non reticolo fisico unico. Ledger A-1 verificato; matching WFS attestato nel vecchio snapshot aggregato, ID/date individuali non rigiocati. Serie, benchmark, anomalie e correlazioni automatiche rifiutati. Metodo `docs/A6_PAB_ADAPTERS.md`; report `reports/a6-pab/`.

Copertura 152/225 effettivi, 104/181 sorgente; 73 residui, nove ambientali. Suite 518 domande (253 calcoli, 265 rifiuti); 63 riferimenti numerici per catalogo e quattro quote aggregate nel lotto. 54 collegamenti e 61 carichi descrittivi. Restano clima (quattro), agricoltura (tre), acqua potabile per località/parametro e classificazione territoriale. Le 35 letture e due riepiloghi conservano perimetro e revisione aperta. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata. Quick/Full locali e CI sul candidato prima del merge del proprietario. Radar prosegue nell’altra chat.
