# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 6 ottobre 2026

- Main pubblicato: `d4f04e77374c98756548f2a5fe48c764e9623a39` (#343); deploy `37416342215` e status `ov-pages-live` SUCCESS. Catalogo effettivo: 225 indicatori, 124 storici e 137 confronti verificati dal Quick; conteggi sempre derivati.
- A0–A5 DONE. A5 chiusa con #280; UI approvate e correzioni #313–315/#322 preservate. Camaiore resta protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; golden e altri lock restano attivi.
- Workstream attivo: **A6**, step **A6.4 e prototipo A6.5**, issue **#330**, branch `feat/a6-distinct-finance-carriers`. A6.2–A6.3: contratto e guardie pubblicati con #331 (merge manuale del proprietario). A6.1 chiusa con merge autorizzato di #301. Specifica `docs/A6_SEMANTIC_MODEL.md`, contratto `ci/semantic-model-contract.json`, validatore e regressione integrati nel Quick per sorgente ed Effective Public Catalog.
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

#343 mergiata manualmente il 6 ottobre, main `d4f04e77374c98756548f2a5fe48c764e9623a39`, deploy #37416342215 SUCCESS e `ov-pages-live` SUCCESS. Quick/Full locali con Chromium 151 e CI GREEN; falsi negativi hover/sticky corretti nei test, soglie/golden/UI invariati.

Lotto v9 su `feat/a6-distinct-finance-carriers`: debito, opere monitorate, Missione 03 e recupero fiscale. 85/225 con adapter, 103 domande (63 calcoli/40 rifiuti). Componenti D1/interessi/recupero locale verificati; PDI 10.3 senza ponderazioni implicite; stock opere e missione leggibili come carrier normalizzati, non prova raw. DAIT 2025/riscossioni 2024 e popolazione SIOPE senza data attestata restano distinti. Metodo `A6_DISTINCT_FINANCE_ADAPTERS.md`; mappa e baseline separata. Regressioni mirate e suite domande PASS; gli esiti finali Quick/Full locali e CI sono registrati nella PR del branch. Tutti i gate devono passare prima della revisione per merge. Nessuna modifica dati/UI/asset/golden/workflow o nuova acquisizione. A6.4 parziale, A6.5–A6.6 aperte, A7 non avviata. Dopo questo lotto: demografia/MIM già acquisiti e revisione delle letture, senza manutenzioni separate. Merge solo su istruzione specifica.
