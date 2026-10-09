# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 9 ottobre 2026

- Baseline main: `5d91c38663a1de1662afec6fc6cd477b963c0391`, merge #368; albero `8aabad0296443197e05122db54a08b64f4f38baf`. Quick/Full CI `37856914614` e Full locale isolato #368 verdi sullo stesso albero. Catalogo effettivo: 225 indicatori, 124 storici e 137 confronti; conteggi derivati.
- A0–A5 DONE. A5 chiusa con #280; UI approvate e correzioni #313–315/#322 preservate. Camaiore resta protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; golden e altri lock restano attivi.
- Workstream attivo: **A6**, step **A6.4 e letture pilota A6.5**, issue **#330**, branch `feat/a6-remediation-adapter`. A6.2–A6.3: contratto e guardie pubblicati con #331 (merge manuale del proprietario). A6.1 chiusa con merge autorizzato di #301. Specifica `docs/A6_SEMANTIC_MODEL.md`, contratto `ci/semantic-model-contract.json`, validatore e regressione integrati nel Quick per sorgente ed Effective Public Catalog.
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

#367 ha integrato il demanio v21; Quick/Full CI e Full locale isolato verdi, 40 golden, 578 controlli browser, Lighthouse. Evidenza `PR367_Full_locale_isolato_20261009.zip`. Radar resta manutenzione separata.

Lotto estrattivo v22: record RTCave al 2 settembre 2026, produzione PRC 2019–2025 e pianificazione PRC variante 2025 distinti. Novanta record locali rideduplicati per codice_rt/id_cava, anagrafiche e conteggi riconciliati; record non necessariamente cave fisiche. Produzione documentata per due comuni, altri cinque n.d. con opt-in; serie leggibile, continuità per variazioni/trend non revisionata. Superfici G/GP/ACC non sommabili né assimilate a escavato/autorizzato. Percentuali GIS pubblicate distinte dai rapporti da componenti arrotondati; tre quote ricostruite aggregate, precisione esplicita. SED non esaustivo; benchmark e correlazioni automatiche rifiutati. Metodo `docs/A6_EXTRACTIVE_ADAPTERS.md`, report `reports/a6-extractive/`.

Copertura derivata: 145/225 effettivi, 97/181 sorgente; 80 residui, di cui 16 ambientali. Suite 449 domande (242 calcoli, 207 rifiuti), 35 verifiche numeriche per catalogo nel lotto SISBON, alias inclusi; 52 collegamenti tipizzati, 58 carichi. Le 35 letture e due riepiloghi conservano perimetro e revisione metodologica aperta. Quick/Full locali e CI sullo stesso albero prima della revisione per merge del proprietario. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.

### Lotto SISBON v23

Baseline #368 mergiata, Quick e Full CI verdi (run 37856914614); evidenza Full locale `PR368_Full_locale_isolato_20261009.zip`. Adapter amministrativo `remediationProceedings`: attivi, chiusi, tutti e quota attivi/all da 152 codici distinti. 56 attivi, 96 chiusi; stato amministrativo distinto da contaminazione attuale, rischio e completamento bonifica. Nessuno storico, benchmark o correlazione automatica. Metodo in `docs/A6_REMEDIATION_ADAPTER.md`, report in `reports/a6-remediation/`. Gate canonici sul candidato richiesti prima del merge del proprietario; Radar resta nell’altra chat.
