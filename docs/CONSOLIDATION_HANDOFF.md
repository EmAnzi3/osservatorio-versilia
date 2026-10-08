# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 8 ottobre 2026

- Baseline main: `b7ea02eec7025e36b2b794612a31e74a4d239af0`, merge #358. Quick/Full CI `37748491323` e Full locale isolato verdi; albero `0387f42fa5248a7e87804e412915302a816b8aec`. Build/deploy `37753657990` e live `37754638963` SUCCESS. Catalogo effettivo: 225 indicatori, 124 storici e 137 confronti; conteggi derivati.
- A0–A5 DONE. A5 chiusa con #280; UI approvate e correzioni #313–315/#322 preservate. Camaiore resta protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; golden e altri lock restano attivi.
- Workstream attivo: **A6**, step **A6.4 e letture pilota A6.5**, issue **#330**, branch `feat/a6-soil-land-cover-adapters`. A6.2–A6.3: contratto e guardie pubblicati con #331 (merge manuale del proprietario). A6.1 chiusa con merge autorizzato di #301. Specifica `docs/A6_SEMANTIC_MODEL.md`, contratto `ci/semantic-model-contract.json`, validatore e regressione integrati nel Quick per sorgente ed Effective Public Catalog.
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

#358 ha pubblicato il lotto geografia/foreste v14. Fonti e date distinte, rapporti nativi, nessun trend da fotografie. Lotto chiuso, senza estendere la revisione delle letture.

Lotto suolo v15: stock consumato/incremento lordo-netto ISPRA 2006–2024 e UCS Toscana 2007–2019. Percentuali e m²/residente pubblicati conservati separatamente dai rapporti nativi; denominatori della stessa fonte/anno. Macroclassi e dettagli UCS annidati, superfici UCS/ISPRA/Istat/CFI distinte; netto negativo preservato. Serie consultabili, variazioni/trend e associazioni temporali rifiutati senza prova di continuità. Metodo `docs/A6_SOIL_LAND_COVER_ADAPTERS.md`, report `reports/a6-soil/`.

Copertura derivata: 125/225 effettivi, 85/181 sorgente; 100 senza adapter, di cui 35 ambientali. Suite 214 domande (136 calcoli, 78 rifiuti), 1.456 celle correnti/storiche interrogate contro riferimenti fissi (conteggio include alias e ripetizioni); 40 collegamenti tipizzati. Le 35 letture e due riepiloghi conservano perimetro e revisione metodologica aperta. Quick/Full locali e CI sul singolo albero prima della revisione per merge; approvazione esplicita richiesta. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.
