# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 6 ottobre 2026

- Main pubblicato: `93647a10780f6afd683833a1111758a5a5d57b63` (#346); deploy `37443730287` e status `ov-pages-live` SUCCESS. Catalogo effettivo: 225 indicatori, 124 storici e 137 confronti verificati dal Quick; conteggi sempre derivati.
- A0–A5 DONE. A5 chiusa con #280; UI approvate e correzioni #313–315/#322 preservate. Camaiore resta protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; golden e altri lock restano attivi.
- Workstream attivo: **A6**, step **A6.4 e prototipo A6.5**, issue **#330**, branch di manutenzione `fix/a6-browser-view-readiness`. A6.2–A6.3: contratto e guardie pubblicati con #331 (merge manuale del proprietario). A6.1 chiusa con merge autorizzato di #301. Specifica `docs/A6_SEMANTIC_MODEL.md`, contratto `ci/semantic-model-contract.json`, validatore e regressione integrati nel Quick per sorgente ed Effective Public Catalog.
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

#344 pubblicata manualmente il 6 ottobre: main `0118a1ad532cc2ffe39b01cd8b7fd2bfcbd4b474`, deploy `37425250340`, live `37426041154` e `ov-pages-live` SUCCESS. CI Quick/Full verdi su head #344. Catalogo pubblico verificato HTTP 200: SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`, 225 indicatori. Il Full locale v9 non era concluso: timeout di prontezza browser legati ad attese globali di rete; due correzioni ERP/PNRR rimaste locali sono recuperate nel lotto v10. Il Quick v10 ha inoltre mostrato un timeout intermittente della grammatica visiva; attesa di rendering client/indicatore/font corretta e test completo PASS su candidato e baseline. UI, richieste, asserzioni e soglie preservate.

Lotto v10: 16 adapter demografia/MIM già acquisiti; 101/225 effettivi, 68/181 sorgente. 130 domande (81 calcoli/49 rifiuti); 1.379 osservazioni native verificate. Stock, eventi, cittadinanza, intervalli cumulati e anni scolastici distinti; edifici sulle risposte definite, missing espliciti. Metodo `docs/A6_DEMOGRAPHY_SCHOOL_ADAPTERS.md`, audit/mappa/domande e baseline in `reports/a6-demography-school/`. Gate locali e CI finali registrati nella PR del branch prima della revisione per merge. Nessuna acquisizione, modifica dati/UI/asset/golden/workflow. A6.4 parziale, A6.5–A6.6 aperte, A7 non avviata. Proseguire dal backlog derivato con componenti già disponibili e letture territoriali verificate; nessuna manutenzione separata. Merge solo su istruzione specifica.

#346 mergiata manualmente e pubblicata: main `93647a10780f6afd683833a1111758a5a5d57b63`, deploy `37443730287` e live `37444683014` SUCCESS. Head `63f80f4f4c1525d06194938a4c28c7ebe2e2cc29`: CI Quick/Full (`37439887403`) e A3 (`37439887367`) verdi. Full locale v10 non verde: timeout A4; la correzione aggiuntiva viene separata dal lotto già pubblicato. Helper condiviso: 40/40 golden e grammatica visuale PASS su candidato e baseline. Un ulteriore Full è stato interrotto dalla policy dell’ambiente verso `https://thumb.wikimedia.org:443` (fotografie, nessun indicatore); verifica locale senza connessioni esterne e CI del nuovo head registrate nella PR di manutenzione. Nessuna simulazione dei dati, baseline aggiornata o soglia ridotta.

Successivo lotto funzionale: pendolarismo per lavoro Istat 2021, con componenti e matrice già versionate; distinguere flussi interni al gruppo e verso l’esterno, denominatori e anno. La matrice del lavoro non misura gli spostamenti per studio. Nessuna manutenzione separata incorporata.
