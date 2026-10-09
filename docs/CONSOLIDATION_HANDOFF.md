# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 9 ottobre 2026

- Baseline main: `5ed97e3b740909ac749707ed72e8e637dac13d7a`, merge #372; albero `08df5ffd4464721d3e6b1b15ad4c56354a775cce`. Quick/Full CI `37915145216` e Full locale isolato #372 verdi sullo stesso albero. Catalogo effettivo: 225 indicatori, 124 storici e 137 confronti; conteggi derivati.
- A0–A5 DONE. A5 chiusa con #280; UI approvate e correzioni #313–315/#322 preservate. Camaiore resta protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; golden e altri lock restano attivi.
- Workstream attivo: **A6**, step **A6.4 e letture pilota A6.5**, issue **#330**, branch `feat/a6-agriculture-profiles`. A6.2–A6.3: contratto e guardie pubblicati con #331 (merge manuale del proprietario). A6.1 chiusa con merge autorizzato di #301. Specifica `docs/A6_SEMANTIC_MODEL.md`, contratto `ci/semantic-model-contract.json`, validatore e regressione integrati nel Quick per sorgente ed Effective Public Catalog.
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

Baseline #372 verificata: main `5ed97e3b740909ac749707ed72e8e637dac13d7a`, albero `08df5ffd4464721d3e6b1b15ad4c56354a775cce`. Quick/Full CI `37915145216` e Full locale isolato exit 0 sullo stesso albero; evidenza `PR372_Full_locale_isolato_20261009.zip`, inclusi i tentativi precedenti. Guardia mobile Percorsi con attese limitate conservata.

Lotto corrente agricolo v26: ricambio/conduzione e diversificazione/modernizzazione Istat 2020 con cinque rapporti e universi 959/957/944 distinti; nessun indice, somma di sottocategorie sovrapposte o equivalenza conduttore/capo azienda. Aggregazioni dalle componenti native della stessa lettura, zero ufficiale Forte dei Marmi conservato; microdati SDMX non riacquisiti. Quota SAU biologica regionale 2024 e serie 2018–2024 leggibili, gap Toscana 2024 dalla riga ufficiale; niente ponderazione senza ettari, benchmark retrodatato o variazioni/trend non revisionati. Metodo `docs/A6_AGRICULTURE_PROFILES_ADAPTERS.md`; report `reports/a6-agriculture-profiles/`.

Copertura 159/225 effettivi, 109/181 sorgente; 66 residui e due ambientali (acqua potabile per località/parametro e classificazioni territoriali). Suite 622 domande, 285 calcoli e 337 rifiuti; 56 riferimenti correnti con alias, 14 rapporti aggregati, 49 annualità fisse e sette gap ufficiali nel lotto. 58 collegamenti e 67 carichi descrittivi. Dati/UI/asset/golden/workflow/Radar/Camaiore e 35 letture + due riepiloghi conservati. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata. Quick/Full locali e CI sul candidato prima del merge del proprietario; Radar nell’altra chat.
