# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 9 ottobre 2026

- Baseline main: `d91ba11b25d7cf044abfc3d2f9ed6c3a2b0f0924`, merge #370; albero `7beb0204453f05e22661a728a757e6ba37e62740`. Quick/Full CI `37895073572` e Full locale isolato #370 verdi sullo stesso albero. Catalogo effettivo: 225 indicatori, 124 storici e 137 confronti; conteggi derivati.
- A0–A5 DONE. A5 chiusa con #280; UI approvate e correzioni #313–315/#322 preservate. Camaiore resta protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; golden e altri lock restano attivi.
- Workstream attivo: **A6**, step **A6.4 e letture pilota A6.5**, issue **#330**, branch `feat/a6-climate-adapters`. A6.2–A6.3: contratto e guardie pubblicati con #331 (merge manuale del proprietario). A6.1 chiusa con merge autorizzato di #301. Specifica `docs/A6_SEMANTIC_MODEL.md`, contratto `ci/semantic-model-contract.json`, validatore e regressione integrati nel Quick per sorgente ed Effective Public Catalog.
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

Baseline verificata: #370 mergiata, main `d91ba11b25d7cf044abfc3d2f9ed6c3a2b0f0924`, albero `7beb0204453f05e22661a728a757e6ba37e62740`. Quick/Full CI `37895073572` e Full locale isolato #370 verdi; evidenza `PR370_Full_locale_isolato_20261009.zip`.

Lotto corrente clima v25: quattro carrier esterni, valori annuali e delta OLS 1975–2025 distinti. `total` usa il valore annuo corrente 2025 come il runtime; la vecchia etichetta catalogo resta esplicita. Minime/massime: ERA5-Land continuo con offset costante LaMMA, non il vecchio stitching del caveat catalogo. Serie 76/51 anni; variazioni assolute e pendenze arbitrarie solo per Tmin/Tmax omogenei. Percentuale solo della retta delle precipitazioni; nessuna percentuale Celsius, media territoriale non verificata, benchmark geografico, anomalia, correlazione o causalità. Raster/calibrazione/SIR non riacquisiti né rigiocati. Metodo `docs/A6_CLIMATE_ADAPTERS.md`; report `reports/a6-climate/`.

Copertura 156/225 effettivi, 108/181 sorgente; 69 residui e cinque ambientali. Suite 555 domande; 63 riferimenti numerici indipendenti, replay distinto di 1.778 celle annue congelate. 56 collegamenti e 64 carichi descrittivi. Restano agricoltura (tre), acqua potabile per località/parametro e classificazione territoriale. Le 35 letture e due riepiloghi conservano perimetro e revisione aperta. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata. Quick/Full locali e CI sul candidato prima del merge del proprietario. Radar prosegue nell’altra chat.

Guardia browser mobile Percorsi: attesa esplicita massima di 10 secondi sul controllo e sul grafico già verificati, dopo `networkidle`; nessuna asserzione, soglia o golden modificato. Il controllo precedente era fallito nel Quick e passato isolatamente; l’attesa certifica il completamento della selezione asincrona prima della misura.
