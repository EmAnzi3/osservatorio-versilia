# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 7 ottobre 2026

- Baseline main: `9d7baa837970a19c723de219b174fa741a7e394e`, merge #353. Quick/Full CI verdi sul candidato; albero `a14442cacfffdfa7fe038e783f615f7d3475f269` identico al Full locale isolato verde. Pubblicazione da verificare sul run main, distinta dal verde PR. Catalogo effettivo: 225 indicatori, 124 storici e 137 confronti; conteggi derivati.
- A0–A5 DONE. A5 chiusa con #280; UI approvate e correzioni #313–315/#322 preservate. Camaiore resta protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; golden e altri lock restano attivi.
- Workstream attivo: **A6**, step **A6.4 e letture pilota A6.5**, issue **#330**, branch `feat/a6-agriculture-adapters`. A6.2–A6.3: contratto e guardie pubblicati con #331 (merge manuale del proprietario). A6.1 chiusa con merge autorizzato di #301. Specifica `docs/A6_SEMANTIC_MODEL.md`, contratto `ci/semantic-model-contract.json`, validatore e regressione integrati nel Quick per sorgente ed Effective Public Catalog.
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

Il proprietario ha confermato #347 mergiata/pubblicata e autorizzato la ripresa di A6 il 6 ottobre. Il completamento Radar/live prosegue in un'altra chat: non incorporarlo né usarlo come blocco di A6.

Lotto agricolo v13: cinque carrier Istat 2020, aziende, SAU localizzata, dimensione media, colture, superficie irrigata. Centro aziendale distinto dalla localizzazione dei terreni; rapporti da componenti native, mancanti delle colture conservati. Nessuno storico o condizione corrente 2026 inventato. Solo la dimensione media ha benchmark comparabili; ettari comunali e totali regionali non diventano misure equivalenti. Metodo `docs/A6_AGRICULTURE_ADAPTERS.md`, report `reports/a6-agriculture/`.

Copertura derivata: 118/225 effettivi, 85/181 sorgente; 107 senza adapter, di cui 42 ambientali. Suite cumulativa 182 domande (116 calcoli, 66 rifiuti), 86 osservazioni agricole indipendenti incluse quattro celle mancanti; 37 collegamenti tipizzati. Le 35 letture territoriali e due riepiloghi conservano perimetro e revisione metodologica aperta. Gate Quick/Full locali e CI sul singolo albero prima del merge, approvazione esplicita del proprietario richiesta. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.
