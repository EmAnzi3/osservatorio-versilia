# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 6 ottobre 2026

- Baseline pubblicata verificata per questo lotto: `3545f1c88ce39bf90528cd3b27a2f161cf82887b` (#348); deploy `37490896493` e status `ov-pages-live` SUCCESS. #349 e #347 seguono i gate del loro albero nella rispettiva PR; non dedurre la pubblicazione da un verde PR. Catalogo effettivo: 225 indicatori, 124 storici e 137 confronti verificati dal Quick; conteggi sempre derivati.
- A0–A5 DONE. A5 chiusa con #280; UI approvate e correzioni #313–315/#322 preservate. Camaiore resta protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; golden e altri lock restano attivi.
- Workstream attivo: **A6**, step **A6.4 e letture pilota A6.5**, issue **#330**, branch `feat/a6-commuting-adapters`. A6.2–A6.3: contratto e guardie pubblicati con #331 (merge manuale del proprietario). A6.1 chiusa con merge autorizzato di #301. Specifica `docs/A6_SEMANTIC_MODEL.md`, contratto `ci/semantic-model-contract.json`, validatore e regressione integrati nel Quick per sorgente ed Effective Public Catalog.
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

Il proprietario ha autorizzato il 6 ottobre integrazione e pubblicazione di #348/#349, chiarimento del gate locale #347 e correzione Radar/live prima di riprendere A6. #348 mergiata su main `3545f1c88ce39bf90528cd3b27a2f161cf82887b`; #349 riallineata conservando helper browser e adapter/letture. Gate del nuovo albero registrati nella PR. Il precedente head #349 `f29d3398` aveva Full locale e CI verdi. Non riprendere lo sviluppo A6 prima del resoconto al proprietario.

Questo lotto estende la #349 in un commit distinto e amplia il generatore A6.5 esistente a cinque percorsi × sette comuni: invecchiamento/assistenza, lavoro/infanzia, turismo/servizi, pendolarismo e organizzazione scolastica. Due riepiloghi di gruppo usano sei rapporti da componenti sommate; periodi, universi, scopi geografici e associazioni ecologiche espliciti. Null e coperture incomplete non diventano zero: le letture comunali valide restano disponibili e i riepiloghi incompleti vengono rifiutati. Nessuna politica, effetto, graduatoria o fabbisogno di trasporto dedotto automaticamente.

Metodo `docs/A6_TERRITORIAL_READINGS.md`; report riproducibile in `reports/a6-territorial-readings.md`. Catalogo, adapter v11, 108/225 effettivi, 75/181 sorgente e suite di 148 domande invariati. Nessuna acquisizione o modifica a dati, pagine, asset, renderer, golden o workflow. Gate locali/CI obbligatori prima del merge; evidenze del singolo head nella PR. Revisione metodologica delle letture e delle domande aperte ancora necessaria: A6.4 parziale, A6.5–A6.6 aperte, A7 non avviata.

## Gate operativo Radar prima di riprendere A6

Il proprietario ha autorizzato il 6 ottobre merge e pubblicazione #348/#349, chiarimento del Full locale #347 e correzione dell'automazione Radar/live. Il follow-up #347 riunisce nello stesso lotto le rotte ufficiali, i ruoli listing/supplementary (mirror, FAQ, singoli avvisi), la riconciliazione della memoria con i ruoli correnti e il checksum CSS Leaflet corretto. Metodo e URL residui `docs/RADAR_DISCOVERY_RECOVERY.md`.

Automazione nello stesso candidato: budget finiti scan 30/build 20/job 60 minuti, concorrenza PR separata dalla produzione, context `ov-radar-refresh`, `ov-public-routes` e `ov-pages-live` indipendenti. Un deploy saltato non cancella l'evidenza precedente; HTTP/errori conservati nei log con massimo tre verifiche route. Diagnosi `docs/RADAR_RUNTIME_LIVE_STATUS.md`. Gate locali isolati e CI sul nuovo albero nella PR; dati, contenuti, layout e golden conservati, nessuna soglia ridotta. Unica modifica HTML: il checksum del CSS Leaflet approvato nella mappa Percorsi, senza ridisegno.

Dopo merge/deploy: un solo refresh produttivo completo; verificare persistenza, pubblicazione e context. Riferire al proprietario prima di riprendere A6. Le 35 letture restano soggette a revisione metodologica; prossimo backlog ambientale derivato, senza acquisizioni onerose. A7 non avviata.
