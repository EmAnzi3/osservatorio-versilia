# Consolidamento Osservatorio Versilia — handoff operativo



## Sedi scolastiche a.s. 2026/27 e farmacie (12 novembre 2026)

- **Definizione ricostruita.** `schoolSites` pubblicato (anno «2025») coincide 7/7 con i codici scuola
  univoci dell'anagrafe MIM delle **scuole statali** a.s. 2025/26 (`SCUANAGRAFESTAT20252620250901.csv`):
  Massarosa 22, Viareggio 49, Camaiore 24, Pietrasanta 24, Seravezza 13, Forte dei Marmi 8, Stazzema 6.
  Le paritarie sono escluse. È la riconciliazione che `a3-benchmark-residual-evidence.json` dava come
  `AMBIGUOUS_OR_MISMATCH` sul 2024/25 statali+paritarie.
- Nuovo aggiornatore `update_source_data.py mim-schools --year AAAA` (richiesta `"mimSchools"`): trova
  nel catalogo MIM il file statale dell'a.s. AAAA/AA+1, conta i codici univoci per Comune (REGIONE,
  PROVINCIA, DESCRIZIONECOMUNE), Toscana e Italia, aggiorna valori, rapporto ogni 1.000 residenti al
  1° gennaio 2026, metodo e scrive `mim-school-sites-AAAA.json` con impronta del file. Rifiuta a.s.
  precedenti, righe di altri anni, codici con attributi diversi e Comuni senza sedi. Aggiunto al giro
  mensile (`NEXT_YEAR`).
- a.s. 2026/27 (dati al 01/09/2026), verificato dal browser sul file MIM: cambia solo Viareggio 49 → 48.
- **Farmacie**: nessun aggiornamento. `pharmaciesPer1000` è la fotografia annuale al 31/12/2025 del file
  ministeriale `FRM_FARMA_5_20251231.csv`; i file mensili 2026 non la sostituiscono (scelta dichiarata
  nello snapshot). Il prossimo dato è al 31/12/2026.

## Radar: il bando aperto assorbe le schede «in arrivo» dello stesso bando (12 novembre 2026)

- Dopo #581 il sito mostrava «Fondo investimenti stradali nei piccoli Comuni 2026» aperto (ANCI Toscana,
  30/11) e, accanto, due schede «in arrivo» dello stesso fondo (MIT senza scadenza; rilancio ANCI Lombardia).
- `opportunity_qualifier.absorb_announcements`: una scheda `upcoming`/`announced_upcoming` esce quando
  un bando aperto ha almeno 4 parole distintive del titolo in comune (80% del titolo più corto,
  prime 5 lettere, escluse parole generiche come avviso/bando/comuni), gli stessi anni e, se annunciata,
  la stessa scadenza. Le schede assorbite sono in `absorbedAnnouncements` con il bando che le sostituisce.
- Chiamata dopo `_apply_publication_exclusions` nel run e nella preparazione pubblica; le schede assorbite
  vanno in `archive` con `archive_reason: superseded_by_open_call`, così la riconciliazione finale della
  continuità le riconosce (senza archivio il primo dry-run dava `continuityHold=1` sul rilancio ANCI Lombardia).

## Radar: fonte ANCI nazionale rimossa (12 novembre 2026)

- `anci-nazionale` non era leggibile dalla CI: tutti gli endpoint `anci.it` e `sistemacomunidigitali.anci.it`
  vanno in timeout o rispondono 403 (WAF) / errore TLS in IPv4; restava solo il mirror ANCI Piemonte,
  supplementare, le cui segnalazioni non potevano essere verificate sulla fonte primaria.
- Rimossa da `opportunity-discovery-v044.json` (override e registro copertura), `opportunity-sources-v03.json`,
  `opportunity-source-coverage-v03.json`, dalla diagnosi rotte di `opportunity_transport_smoke.py` e dalle
  fonti di copertura del GSE in `COVERED_WHEN_BLOCKED` (resta `mase-bandi` + `anci-toscana`).
- Test: eliminati i due casi che leggevano la configurazione reale di `anci-nazionale`; il caso sui
  successi supplementari usa ora `pcm-politiche-mare` (stesso meccanismo); il caso sintetico sul mirror resta.
- I rilanci ANCI arrivano da `anci-toscana`. La #583 (endpoint di ricerca ANCI) è chiusa senza merge.

## Radar: coda delle segnalazioni, quote separate e decisioni verificabili (11 novembre 2026)

- Stato 10/11: `discoveryQueue` 350 segnalazioni; il qualificatore ne legge al massimo 120 per run,
  ma 97 posti andavano ai topic Funding & Tenders (dati strutturati, nessuno scaricamento): restavano
  ~23 letture in rete per run e 180 segnalazioni non erano mai state lette.
- Ora i dati strutturati si decidono tutti fuori quota; le 120 letture in rete restano per le pagine.
- Il qualificatore usa un `TransportBudget` proprio (`MAX_SECONDS` + 60 s, journal
  `opportunity-qualifier-progress.jsonl`) e restituisce il tempo speso alla scadenza della scansione.
- `autoQualificationCache` conserva il motivo della decisione; le voci senza motivo (cache precedente)
  si rileggono una volta. Il run live stampa `QUALIFICA: esito · fonte · titolo · motivo`.
- `pcm-famiglia` legge anche la sottosezione `finanziamenti-avvisi-e-bandi/avvisi-e-bandi/`.
- Revisione dei 107 `QUALIFICA` non F&T del dry-run (regole generali, nessuna correzione per bando):
  - «Non possono partecipare i Comuni che hanno già ottenuto…» non è più un'esclusione dei Comuni:
    `PUBLIC_EXCLUDED` ignora l'esclusione seguita da una relativa o un requisito (che, già, con…).
    Era il motivo del rifiuto di «Fondo investimenti stradali nei piccoli Comuni 2026».
  - Limiti di popolazione nella voce dei destinatari («popolazione massima di 5.000 abitanti»,
    «fino a 50.000 abitanti», «superiore a…»): i Comuni fuori limite diventano `not_eligible`
    con i residenti Istat dell'indicatore `population` di `site-data.json`; se nessuno dei sette
    rientra la segnalazione è respinta. Le soglie sotto 500 e le età non contano.
  - Richiedenti limitati agli enti in dissesto o in riequilibrio (anche «gestione liquidatoria»,
    «organo straordinario di liquidazione»): respinti (es. comunicato DAIT
    del 10/11 sull'anticipazione del Fondo di rotazione, prima qualificato).
  - «per la formazione della graduatoria» nel titolo non è più letto come esito.
  - «dovranno essere completate entro…» è un termine di esecuzione (`EXECUTION_CUE` + completat/eseguit):
    l'avviso MIM 79378 (candidature fino al 14/10) risultava aperto per la data 31/12/2028 delle verifiche.
  - Scaduti confermati: «Fabbrica Spazi Civici» (04/11), «Prevenzione Sismica Edifici Pubblici» (01/08).
- Il job `daily production dry-run` passa da 40 a 55 minuti: con il qualificatore la scansione dura
  ~25 minuti e la build statica ~14; il run del 11/11 si è fermato al termine della build.
- Ancora da fare: fonti mancanti Pari opportunità «L'Italia delle donne» (pagina avvisi non raggiungibile
  dal container, da verificare l'URL), ANCI spazi under 35, MUSE DHC.

## Radar: rilettura quotidiana delle pagine ufficiali e `verified_at` onesto (10 novembre 2026)

Correzione sistemica dell'audit sul Radar (bandi fermi alle date dei corpora statici).

- Nuovo `scripts/opportunity_official_recheck.py`, eseguito in ogni refresh live prima
  dell'archiviazione delle scadute (hook `PRE_EXPIRY_HOOK` in `opportunity_matrix_promotions.py`,
  impostato da `opportunity_daily_refresh_audit_fixed.py`): rilegge la pagina ufficiale di ogni
  scheda pubblica, più le pagine equivalenti già registrate (`_OFFICIAL_ALTERNATE_URLS`,
  `_OFFICIAL_EVIDENCE_SETS`) e un eventuale `official_urls`.
- La rilettura usa un `TransportBudget` proprio (`RECHECK_SCAN_SECONDS` = 420 s, journal
  `opportunity-official-recheck-progress.jsonl`) tramite `run_with_own_budget`; il tempo speso è
  restituito alla scadenza della scansione. Senza isolamento consumava i 1200 s della scansione e il
  qualificatore finiva con `scan budget exhausted` → `coverageAudit=fail` (run PR dell'11/11).
- `COVERAGE AUDIT FAIL` nel log riporta anche budget di scansione, storiche non monitorate e
  copertura residua.
- Regola unica, senza correzioni per bando: il ruolo di ogni data è deciso dalla parola chiave più
  vicina che la precede (proroga, scadenza, apertura) o da un intervallo «dal … al …»/«from … to …».
  Una proroga successiva sostituisce la scadenza; una scadenza ritrovata è confermata; senza
  scadenza la scheda prende l'unica scadenza futura della pagina; una scadenza esistente non
  ritrovata cambia solo con una proroga esplicita (altrimenti scheda invariata e «non confermata»:
  il run dell'11/11 spostava «Assistenti sociali» dall'11/11 al 5/02/2027, data di un'altra fase). Apertura passata con scadenza futura → aperta; apertura futura → in arrivo.
  Una scheda già scaduta torna aperta solo con una proroga esplicita (nel run di prova la regola
  senza questo vincolo riapriva Erasmus KA120 e BETTERRENO con date di altri cicli). Le proroghe si
  leggono anche dalla pagina di sezione del sito (host + primo segmento), ma solo se il contesto
  della data nomina la scheda: così i due SAI che puntano all'avviso originale ricevono la proroga
  pubblicata sul portale.
  Sulle pagine reali: SAI prorogato al 10/12 ore 18:00, EUCF 8ª call aperta 26/10–21/12 ore 17:00,
  C3 entro il 13/11.
  Run live sulla PR: 105 schede rilette, 32 confermate, 42 aggiornate, 23 non confermate,
  8 non raggiungibili (Erasmus+ giovani, ESC, Marchio patrimonio europeo, Conto Termico/GSE con WAF).
- `verified_at` è la data dell'ultima lettura riuscita della fonte ufficiale. Se oggi la pagina non
  risponde restano i fatti e la data dell'ultima lettura (campo `official_recheck` nello snapshot);
  una scheda dei corpora statici mai riletta ha `verified_at` nullo. Il rapporto del run ha la
  sezione «Rilettura delle pagine ufficiali» con modifiche e pagine non raggiungibili.
- Le icone delle fonti nuove non bloccano più la build: un dominio senza icona registrata riceve un
  badge tipografico locale (`local-source-mark-auto`). Il run delle 14:50 del 10/11 era fallito
  per `dait.interno.gov.it`.
- Pages: un secondo tentativo di deploy dopo 90 secondi se il primo fallisce.
- Budget: scan 38 minuti (prima 30), job 113 (prima 105).
- Resta da fare (PR successiva): promozione automatica dei lead in revisione e fonti mancate
  (famiglia.governo.it «avvisi-e-bandi», ANCI, MUSE DHC, «L'Italia delle donne»).

## Deploy del sito: dipendenze prima del catalogo (10 novembre 2026)

Il deploy di `main` dopo #576 è fallito nel job `build` di `pages.yml`: lo step «Select verified
source monitor runtime state» esegue `materialize_source_monitor_snapshot.py`, che ora valida anche
la fotografia ACI in XLSX (`openpyxl`), ma girava prima di «Install build dependencies». Lo step di
installazione è stato anticipato. Stesso difetto in «Controllo frequente fonti»
(`source-monitor-light.yml`), che non installava dipendenze: ora installa `requirements-ci.txt`.
`test_source_monitor_runtime_snapshot.py` controlla l'ordine in entrambi.

## Quotazioni OMI 1° semestre 2026 (10 novembre 2026)

`omiResidential` passa dal 2° semestre 2025 al 1° semestre 2026.

- Nuovo aggiornatore `update_source_data.py omi-residential --semester AAAA-SN [--correction …]`
  (richiesta `"omiResidential"`, correzioni in `"omiResidentialCorrections"`): interroga la
  consultazione pubblica OMI (provincia LU, Comuni riconosciuti dal codice catastale), rigioca il
  semestre pubblicato e scrive il nuovo solo se il replay coincide. Regola confermata dalla fonte:
  punto medio min/max della riga «Abitazioni civili NORMALE» (vendita e locazione; la locazione del
  catalogo può essere esatta o arrotondata al decimo); zone senza quella riga escluse (Viareggio R3).
- Il replay ha trovato tre errori del catalogo, accettati come correzioni esplicite e registrati in
  `catalogCorrections` della fotografia: Viareggio D2, Seravezza E3 e la zonizzazione di Stazzema
  (fonte: B1, E7, R2; catalogo: 11 zone non più esistenti). L'aggiornatore rifiuta correzioni
  mancanti o superflue.
- Fotografia `data/source-snapshots/omi-residential-2026-S1.json` con intervalli e tutte le righe
  della fonte per entrambi i semestri. Zone 38 (prima 46).
- Versilia 1° semestre 2026: vendita media 2.393 €/m², affitto 7,34 €/m² al mese. Forte dei Marmi
  5.580 e 15,31; Stazzema 837 e 3,07.
- Adattatore e test al `2026-S1` (`2025-S2` rifiutato), note e letture in `limits-it.mjs`, pin
  `omi#1` e `road#3` (impronta del catalogo) ripinnati, 63 domande verificate aggiornate più 3
  rifiuti di `2025-S2`, dossier rigenerati. Il test dell'aggiornatore ora usa i semestri relativi
  al catalogo corrente.

## Consumo di suolo e parco veicolare 2025 (10 novembre 2026)

`landUse`, `landUseChange`, `motorization` e `pollutingCars` passano al 2025.

- Nuova sonda generica `update_source_data.py source-probe --name --url [--follow]` (richiesta
  `"sourceProbe"`): salva in `data/source-probes/` la struttura di pagine, fogli e archivi di una fonte
  raggiungibile solo dai runner GitHub. Usata per ISPRA e ACI prima di scrivere gli aggiornatori.
- `ispra-soil --year AAAA` (`"ispraSoil"`): legge dalla libreria ISPRA l'edizione completa
  `consumo_suolo_AAAA+1_Com_Prov_Reg_Naz` e ricostruisce `landUse`/`landUseChange` in
  `territorio-v137-official.json` per tutti gli anni (l'edizione 2026 rivede anche gli anni precedenti,
  di pochi centesimi di ettaro), più `a3-ispra-soil-benchmark-AAAA.json` dalle righe ufficiali
  Toscana/Italia. I fogli `_rev` non sono usati: il flusso 2025 è misurato da ISPRA sulla carta 2024
  rivista e non coincide con la differenza tra gli stock pubblicati (dichiarato nel metodo). Dove
  ISPRA ha cambiato la superficie comunale di un anno, la riga porta `municipalAreaHa`; l'adattatore
  la usa nel controllo stock/quota, senza allargare la tolleranza. Riesecuzione sullo stesso anno
  ammessa (idempotente, verificata dal bot), anno precedente rifiutato.
- Versilia 2025: 5.571,35 ha consumati, 15,63% del territorio; consumo netto 2024–25 5,31 ha
  (Massarosa −0,19 ha). Toscana 6,22% e 467,76 ha; Italia 7,19% e 9.496,95 ha.
- `aci-vehicles --year AAAA` (`"aciVehicles"`): trova l'archivio «Parco veicolare» nella pagina
  Autoritratto, ricostruisce il pannello nativo del foglio «4 AV per Comune » (stesso parser che
  riproduce esattamente l'impronta 2024) e scrive catalogo e `a3-aci-vehicle-benchmark-AAAA.json`
  con il workbook congelato. Il 2024 resta vincolato all'archivio originale.
- Versilia 2025: 703,9 autovetture ogni 1.000 residenti (denominatore sempre al 1° gennaio 2026),
  quota Euro 0–3 18,2%. Toscana 753,7 e 16,2%; Italia 709,1 e 22,6%.
- Adattatori suolo e veicoli, fan-in, materializzatore territorio e verificatore seguono l'ultima
  edizione; pin soil#2, vehicle#1–2, road#3, road_network#1/#3 ripinnati; domande verificate
  aggiornate (7 suolo, 94 veicoli; i rifiuti «anno non congelato» passano al 2026); test di
  riferimento suolo e veicoli rigenerati dalle edizioni nuove; dossier rigenerati.
- Per gli anni ACI dopo il 2024 la validazione rilegge il workbook congelato con `openpyxl`, quindi
  anche «Controllo mensile dati» (`monthly-data-refresh.yml`) ora installa `requirements-ci.txt`.

## Capacità ricettiva Istat 2025 (9 novembre 2026)

`tourismBeds`, `tourismBedsPer1000` e `tourismStructuresPer1000` passano al 2025, su decisione di Ema
(9/11/2026) nonostante il cambio di perimetro.

- Nuovo aggiornatore `update_source_data.py istat-tourism --year AAAA`: scarica l'archivio Istat
  «Capacità comunale», ricostruisce il pannello nativo dell'anno (province e Italia riconciliate,
  273 Comuni toscani) e scrive catalogo e `a3-istat-tourism-capacity-benchmark-AAAA.json`.
  Rifiuta un anno precedente al pubblicato. In PR con `"istatTourism": [AAAA]`. Il 2024 resta
  vincolato ai suoi conteggi (7.899 Comuni, Italia 5.498.773 posti letto).
- Dal 2025 Istat include gli alloggi privati non imprenditoriali: valori non confrontabili con il
  2024. Niente serie né variazioni; la serie storica dei posti letto 2002–2024 non è più esposta.
  Nell'audit A3 la coppia `tourismBeds`/`serie_storica` passa da ACQUIRED ad AVAILABLE_MISSING.
- Versilia 2025: 69.031 posti letto (34.703 nel 2024), 435,5 ogni 1.000 residenti (218,9), 42,9
  strutture ogni 1.000 residenti (5,7). Toscana 937.066 posti letto; Italia 7.687.036.
- Adattatore A6 turismo e fan-in dei benchmark sullo snapshot più recente; impronte `tourism#3–4` e
  `road#3` ripinnate; 41 domande verificate aggiornate (la serie posti letto ora è un rifiuto
  atteso); dossier rigenerati.

## TARI e IMU 2026 (9 novembre 2026)

Terzo lotto dei periodi nuovi del controllo mensile. `tariStandardHousehold` e
`municipalImuStandard` passano al 2026; `municipalIrpef` resta al 2025.

- Nuova sonda `update_source_data.py mef-fiscal-probe --year AAAA` (`scripts/probe_mef_fiscal.py`):
  sui runner GitHub scarica pagine, elenco atti e testo dei PDF IMU/TARI e il file aliquote
  IRPEF dal Portale del federalismo fiscale, in `data/source-probes/mef-fiscal-AAAA.json`. Non
  tocca il catalogo. In PR con `"mefFiscalProbe": [AAAA]` in `ci/source-update-request.json`.
- `data/source-snapshots/costi-fiscalita-2026.json`: tariffe TARI e aliquote IMU 2026 trascritte
  dai documenti, con atto e PDF per Comune; `scripts/materialize_local_taxes_2026.py` le porta nel
  catalogo (serie 2025–2026).
- TARI 2026 (3 persone, 100 m², TEFA 5%, ARERA 7,60 €): Camaiore 427,43 €, Forte dei Marmi
  480,13 €, Massarosa 544,85 €, Pietrasanta 357,43 €, Seravezza 515,61 €, Stazzema 368,82 €,
  Viareggio 430,16 €. Media 446,35 € (440,38 € nel 2025).
- IMU 2026: aliquote invariate (1,06% Forte dei Marmi, Massarosa, Pietrasanta, Stazzema; 1,14%
  Camaiore, Seravezza, Viareggio). Prospetti 2026 per 4/7; Camaiore, Massarosa e Viareggio senza
  prospetto 2026 entro il 28 ottobre: aliquote 2025 per legge (art. 1, c. 767, L. 160/2019).
- IRPEF 2026 non aggiornata: il file MEF 2026 ha la sola riga di Forte dei Marmi (conferma); le
  delibere possono essere pubblicate fino al 20 dicembre. Da rifare con la sonda dopo quella data.
- Adattatore A6 fiscalità: periodo per indicatore (2026 TARI/IMU, 2025 IRPEF); impronte
  `municipal_tax#5–6` nuove e `road#3` ripinnata; 74 domande verificate TARI/IMU al 2026;
  dossier rigenerati.

## AGCOM FTTH al 5 ottobre 2026 (8 novembre 2026)

I 4 indicatori FTTH (`ftthCoverageDesi`, `ftthCoverage20m`, `ftthReachedHouseholds`,
`ftthUnreachedHouseholds`) passano all'edizione «Consistenze rilevate al 05/10/2026 (rev. del
12/10/2026)» della Broadband Map.

- Nuovo aggiornatore `update_source_data.py agcom-ftth`: legge il catalogo datato
  `geo.agcom.it/reportistica/report.js`, prende l'edizione più recente con CSV comunale e
  valida il CSV (≥ 7.000 Comuni, 7/7 Versilia, 273 Toscana). Scrive catalogo e due snapshot per
  edizione: `agcom-ftth-AAAA-MM-GG.json` (record comunali del CSV primario) e
  `a3-agcom-benchmark-AAAA-MM-GG.json` (Toscana e Italia, media delle percentuali comunali
  ponderata per famiglie). Rifiuta un'edizione più vecchia di quella pubblicata. I conteggi
  mancanti restano mancanti (Forte dei Marmi, 6/7). Nel giro mensile; in PR con
  `"agcomFtth": true` in `ci/source-update-request.json`.
- `scripts/agcom_sources.py` sceglie l'edizione più recente; fan-in dei benchmark e adattatore
  A6 connettività ricavano periodo, etichetta, URL del CSV e copertura dei conteggi dallo snapshot.
- Valori Versilia: copertura DESI 70,9% (era 71,1%), entro 20 m 61,2% (61,4%), 46.368
  famiglie raggiunte (46.521) e 16.341 non raggiunte (16.188). Toscana 72,0% e 63,9%;
  Italia 82,9% e 74,7%. Famiglie residenti AGCOM invariate; la copertura DESI cala alla fonte a
  Camaiore, Massarosa, Pietrasanta e Seravezza.
- Domande verificate FTTH (56) al 5/10/2026; dossier rigenerati; impronte `connectivity#1–4` e
  `road#3` ripinnate.
- Ritirato il workflow «Aggiorna imprese, ATECO e banda larga» (`refresh-agid-indicators.yml`):
  rileggeva ASIA da Cruscotto Italia (fermo al 2023) e FTTH dagli shard AgID. Gli script
  `update_agid_indicators*.py` e i loro test offline restano. Il dettaglio ATECO a 2 cifre
  resta quello pubblicato (2023): un suo aggiornamento va fatto con una fonte Istat diretta.

## ASIA-UL 2024 (8 novembre 2026)

Primo periodo nuovo segnalato dal controllo mensile completo. I 6 indicatori ASIA
(`localUnits`, `localEmployees`, `employeesPerLocalUnit`, `localUnitsChange`,
`localEmployeesChange`, `microUnits`) passano al 2024 (variazioni 2018–2024). Storico
2018–2023 invariato alla fonte (verificato 7/7).

- Nuovo aggiornatore `update_source_data.py istat-asia --year AAAA`: legge il servizio SDMX
  Istat (CSV), non più Cruscotto Italia (fermo al 2023). Scrive catalogo e tre snapshot per
  anno: `istat-asia-ul-AAAA.json` (serie comunali), `a3-istat-business-benchmark-AAAA.json`
  (Toscana e Italia come somme comunali) e `a3-istat-micro-units-benchmark-AAAA.json`
  (classi dimensionali, query per area e pannello nazionale). Test offline ricostruiti dalle
  serie pubblicate. Nel giro mensile per l'anno pubblicato e il successivo; richiedibile in PR
  con `istatAsia` in `ci/source-update-request.json`.
- `scripts/asia_sources.py` sceglie lo snapshot più recente di ogni famiglia: fan-in dei
  benchmark, companion A3.5 e adattatore A6 imprese non hanno più anni scritti nel codice;
  il validatore delle micro unità prende l'anno dallo snapshot.
- Valori 2024 Versilia: 18.019 unità locali, 55.474,02 addetti, 3,08 addetti/UL,
  +8,5% unità locali e +13,0% addetti sul 2018, 94,5% micro unità. Toscana 366.076 UL.
- Domande verificate ASIA al 2024; l'associazione addetti/occupazione femminile fissa i
  periodi al 2023. Dossier Massarosa lavoro rigenerato; impronta `road#3` ripinnata.
- Il workflow «Aggiorna imprese, ATECO e banda larga» rileggeva ASIA da Cruscotto Italia
  (2018–2023): ritirato con il lotto AGCOM FTTH (sezione sopra).

## Controllo mensile completo: 225/225 (8 novembre 2026)

Il «Controllo mensile dati» ora verifica alla fonte tutti i 225 indicatori. 60 hanno un
probe dedicato che confronta periodo e valori (OpenBDAP, ARS, demografia Istat, SIOPE, RGS);
i restanti 165 hanno una verifica **del solo periodo**: `source_period` in
`scripts/release_period_probes.py`, con 73 regole in `sourceChecks` di
`ci/release-probe-coverage.json`. Il rapporto lo dichiara riga per riga («verifica del solo
periodo»): un periodo uguale non garantisce valori identici alla fonte.

- Modi: `latest` (periodo più recente nella pagina o nel file, con `sourceOffset`, `graceDays`
  per le date, `baseline` quando il periodo pubblicato non è confrontabile), `next` (esiste
  l'edizione successiva?), `absent` (la fonte ha dati dopo il periodo pubblicato?), `snapshot`
  (registri continui; con `kind: year` istantanea annuale, es. PUN ricarica).
- `scripts/source_period_survey.py` resta come strumento di collaudo: scarica le pagine delle
  regole come la verifica e stampa anni e catture. Non è più nel workflow.
- Primo giro completo (8/11): 194 correnti, 28 con periodo nuovo alla fonte (vanno pubblicati
  con PR dedicate), 3 da verificare. **Carburanti MIMIT** non è raggiungibile dai runner GitHub
  (timeout costanti, dal browser si apre): la verifica resta manuale, il rapporto dà il CSV e
  l'archivio trimestrale. Il catalogo MIT delle concessioni (HTTP 500) e ARPAT balneazione
  (403 in un giro) sono intermittenti.
- Taratura con riscontri manuali di Ema: ospedali dalla pagina «strutture di ricovero pubbliche
  e equiparate» (l'edizione file 2025-01 contiene dati 2022), Banca dati imprese dalle serie
  storiche RT (ultimo anno di confronto + 1), UNCEM dalla ricerca del sito (rapporto 6/6/2026).

## Aggiornatori nel giro mensile (7 novembre 2026)

Il workflow «Aggiorna dati dalla fonte» ora gira anche ogni mese (giorno 6, 06:41 UTC, il
giorno dopo il «Controllo mensile dati») e a mano (`workflow_dispatch`), su main.
`scripts/source_update_monthly.py` esegue tutti gli aggiornatori di
`scripts/update_source_data.py`: i 7 indicatori ARS legacy e la mobilità Istat P2 per l'anno
pubblicato e per il successivo. Per ognuno scrive l'esito: aggiornato, invariato o rifiutato,
con il motivo e cosa fare (periodo nuovo → PR dedicata; anno non ancora pubblicato → nessuna
azione; fonte non raggiungibile → rilancio o `--file`; forma cambiata → verifica).

- Se i dati cambiano apre (o aggiorna) la PR in bozza `data/aggiornamento-auto-AAAA-MM`. La CI
  non parte da sola su una PR del bot: serve un commit umano, cioè il ripin A6, i dossier e le
  domande verificate, elencati nel corpo della PR.
- L'esito va nel riepilogo del run e, sul giro programmato, come commento nel «Registro controlli
  dati AAAA» con menzione.
- Il modo PR (`ci/source-update-request.json`) resta com'era.
- Test offline `scripts/test_source_update_monthly.py` nei quickChecks.

## Radar: sospensione di continuità GRANFEST (6 novembre 2026)

Dal 5 novembre ogni run del Radar si fermava su `continuityHold=1`: «Bando GRANFEST. Grandi Festival
2027» (Fondazione CR Lucca, identità `rule:coverage:auto-1a33f9260edbbf41`) era nel run precedente
ma non più qualificato. La pagina ufficiale è viva e il bando è aperto fino al 20 novembre, ma
riserva la partecipazione ai soli soggetti privati ed esclude espressamente i Comuni (rinviati a
«FUORI LUOGO – Territori in scena»); il Comune è citato solo come possibile cofinanziatore. La
prima qualificazione automatica era quindi errata e la nuova rilettura la scarta correttamente.
Risolto con una `publicationExclusions` motivata in `data/opportunity-audit-fixes-v1.json`
(`outside_municipal_call`), che toglie la scheda anche dalla continuità.

## Controllo mensile completo, lotto 3: RGS/OpenBDAP/SIOPE (6 novembre 2026)

Branch `feature/check-mensile-lotto3`. Copertura 50/225 (era 19). Nuove famiglie in
`scripts/release_period_probes.py`, tutte con confronto generico `evaluate()` (periodo, valori dei 7
Comuni, storico) e istruzioni manuali dedicate:

- `openbdap_rendiconto`: archivi Rendiconto Toscana dell'anno pubblicato, valori ricalcolati con le
  funzioni dei materializzatori; rilascio successivo = archivio `anno+1` presente (404 = non uscito).
  Famiglie: `v160` (14 indicatori, `build_bilanci_snapshot.build_year/compute_values`), `v139` (6,
  `materialize_bilanci_v139.extract_year`), `mission03` (Missione 03 / popolazione del catalogo),
  `debt_d1` (`financialDebtProfile`, misura principale PDI 10.4: voce D1 dello Stato patrimoniale
  passivo / popolazione; le parti 6.1 e 10.3 non sono ricalcolate).
- `siope_cumulative`: pacchetti BDAP cercati per titolo esatto (`package_search` con frase tra
  virgolette; `datastore_search` non disponibile), dicembre cumulato, CSV cp1252; 5 indicatori di
  cassa + `fiscalRecoveryActivity` (righe «verifica e controllo», popolazione Istat del dataset).
  Rilascio = dicembre dell'anno successivo presente per i 7 Comuni. Nota: `build_siope_history.py`
  nel repo non legge più il formato attuale dei dump (codice comune a 3 cifre, tipologia BDAP).
- `rgs_conto_annuale`: CSV `export/csv/{anno}---Dipendenti-Pubblici---…`; personale per 1.000,
  quota 55+ e turnover netto (causali «passaggi» escluse).

Prova dal vivo (5–6 novembre): tutti `current` tranne `availableAdministrationResultPerResident` di
Seravezza: OpenBDAP ha ripubblicato il Rendiconto 2025 il 3 novembre e il valore passa da 139,02 a
141,47 € per abitante (`same_period_values_differ`). Restano nel lotto 3 `publicWorks` (BDAP-MOP,
nessuno script di acquisizione nel repo) e `municipalStaffTraining` (pagina RGS HTML).

## Registro unico delle impronte A6 (6 novembre 2026)

Branch `feature/a6-registro-impronte` (sopra il lotto 1). Approvato da Ema.

- Le 201 impronte SHA-256 scritte in 40 adattatori `semantic_query_*_adapters.py` sono ora in
  `ci/a6-source-pins.json` (chiave `<adattatore>#<n>`) e lette come `a6_pins.Pin`, una stringa
  che in uso normale si confronta come prima: stessi rifiuti, stessi codici d'errore.
- `A6_REPIN=1` (solo tramite `scripts/a6_repin.py`): ogni confronto con un `Pin` annota il valore
  osservato e passa. Lo script esegue compare/series/trend/benchmark_gap/weighted_ratio su
  ogni indicatore e dimensione del catalogo effettivo; senza `--write` è una prova a secco, con
  `--write --allow modulo,...` scrive solo se cambiano impronte degli adattatori dichiarati.
  Impronte alternative (più valori ammessi): `a6_pins.matches_any`.
- Prova a secco sul catalogo attuale: 26.872 richieste, 194/201 impronte esercitate, 0 cambiate.
  Non esercitate: alternative già soddisfatte (`hospital#1`, `pnrr#3`, `pnrr#7`), `mef#3`,
  `mef#4`, `water_quality#1-2`.
- `scripts/test_a6_pins.py` (quickCheck): nessuna impronta nel codice, registro e codice
  allineati, semantica normale e di ri-registrazione.
- Restano congelati nel codice i **periodi** (es. `'2024'` strade, data RTCave): vanno trattati
  famiglia per famiglia insieme ai lotti del controllo mensile.

## Controllo mensile completo, lotto 1: ARS (5 novembre 2026)

Branch `feature/check-mensile-completo` (sopra `feature/aggiorna-cave-ars`). Obiettivo deciso da
Ema: ogni mese **tutti** i 225 indicatori devono avere una verifica del periodo alla fonte; lo
stato «fonte controllata, periodo non confermabile» non è un esito accettabile. Il merge resta
sempre di Ema.

- `ci/release-probe-coverage.json`: una voce per ognuno dei 225 indicatori, con `probe` (come si
  legge il periodo) oppure `pendingLot` (lotto che lo introdurrà). `maxPending` può solo scendere.
  Lotti: 1 ARS (19, fatto), 2 Istat (71), 3 OpenBDAP/RGS/SIOPE (33), 4 Regione Toscana e
  regionali (48), 5 MEF/MIM/INVALSI (23), 6 altre fonti (31).
- `scripts/release_period_probes.py`: per ogni indicatore coperto scarica la fonte (ARS: 300 s,
  3 tentativi, un download per export), legge l'ultimo periodo comune ai 7 Comuni e confronta
  periodo, valori pubblicati (Comuni + Versilia) e storico. Esiti: `current`,
  `release_detected`, `verification_required` con motivo (`source_unreachable`,
  `structure_changed`, `same_period_values_differ`, `history_revised`, …). Se la fonte non si
  scarica, l'esito porta `manualAction` con link, cosa salvare, dove caricarlo e il comando
  `--metric … --file …` che chiude il controllo.
- `monthly_data_check_status.py` esegue i probe nel run live, applica gli esiti allo stato
  dell'indicatore (prevalgono sulla sola raggiungibilità) e aggiunge al resoconto le sezioni
  «Verifica dei periodi alla fonte», «Azioni manuali» e «Revisioni dello storico».
- `scripts/test_release_period_probes.py` (quickCheck): copertura 225/225 delle voci, ratchet di
  `maxPending` e casi sintetici per tutti gli esiti.

Prossimo: lotto trasversale (adattatori A6 congelati → controlli sul contenuto; domande
verificate rigenerate dall'aggiornatore), poi lotti 2–6.

## Aggiornamento dati dalla verifica dei periodi (6 novembre 2026)

Branch `data/aggiornamento-2026-11`. Tre casi trovati dalla verifica dei periodi alla fonte
(lotto 2, #563):

- **Seravezza, parte disponibile 2025** (voce 0502, OpenBDAP ripubblicato il 3/11):
  1.721.163,36 → 1.751.574,45 € (139,02 → 141,47 €/ab.; Versilia 108,07 → 108,26). Unica voce
  2025 cambiata ricalcolando tutto il rendiconto con `build_bilanci_snapshot.build_year`.
- **Ricoveri ARS 1332, 2021–2025**: ARS ha completato l'ultimo periodo (ricoveri fuori Toscana);
  periodi precedenti identici. Applicato da `update_source_data.py ars-legacy`. Per 1.000:
  Massarosa 62,64 → 63,28, Viareggio 63,98 → 64,60, Camaiore 63,34 → 63,93, Pietrasanta
  62,66 → 63,47, Seravezza 63,41 → 64,15, Forte dei Marmi 59,67 → 61,08, Stazzema
  62,65 → 63,12, Zona Versilia 62,63 → 63,31, Toscana 61,07 → 61,80.
- **Mobilità residenziale 2025** (Istat P2 Comuni): anno successivo al 2024 pubblicato.
  Applicato da `update_source_data.py istat-mobility`; benchmark in
  `a3-istat-demography-mobility-benchmark-2025.json`; l'adattatore demografia legge l'anno
  dallo snapshot invece del 2024 scritto nel codice. Saldi 2025 per 1.000 (interno / estero /
  totale): Versilia 3,24 / 2,36 / 5,60; Toscana 0,87 / 6,03 / 6,90; Italia 0 / 5,02 / 5,02.
  Tassi ricontrollati sulla popolazione media P02 già congelata.
- **Domande verificate**: i tre saldi dei trasferimenti passano al 2025 (Massarosa
  73/63/136 eventi su media 21.794). Il rifiuto «cittadinanza vs trasferimenti» ora fissa i
  periodi (stock 2025, eventi 2024): con la stessa etichetta 2025 il motore calcolerebbe
  l'associazione con avvertenze, ma questo allargherebbe il perimetro A7 degli incroci e
  richiede una revisione esplicita, non fatta qui.
- **Gate Salute v1.40**: `canonical-quick` (25) e `preview` (30), che eseguono entrambi il preflight
  rapido, passano a 60 minuti. Il preflight rapido sui
  runner GitHub ora richiede circa 40 minuti (38 in Pages, 41 nel gate Bilanci sullo stesso
  commit), e il limite a 25 lo annullava anche su PR già fuse. Nessun controllo è cambiato.
  Arrivato finalmente al `preview`, il gate falliva su un'asserzione rimasta a «Aggiornato 14
  settembre 2026»: dal 25 ottobre (c9736bd) la homepage scrive «Catalogo al 14 settembre 2026».
  L'asserzione ora controlla il testo attuale, con la stessa data esatta.
  `canonical-full` (preflight completo) è stato annullato due volte di fila al limite di 60
  minuti (prima finiva in 48–54). I tre job che eseguono un preflight (`canonical-quick`,
  `canonical-full`, `preview`) passano quindi a 120 minuti. Nessun controllo è cambiato.

Nuovo `scripts/update_source_data.py` (aggiornatori con `--file`/`--dry-run`, test offline
`test_update_source_data.py` nei quickChecks) e workflow «Aggiorna dati dalla fonte»
(`source-data-update.yml`): su PR verso main esegue gli aggiornatori elencati in
`ci/source-update-request.json` sui runner GitHub e committa solo sul ramo della PR. I push del
bot non avviano la CI: dopo il suo commit va fatto un push (impronta `road#3` con
`a6_repin.py --allow road --write`, dossier rigenerati, preflight).

## Aggiornamento dati RTCave e ARS (5 novembre 2026)

Branch `feature/aggiorna-cave-ars`, sopra `fix/data-check-2026-11` (#555). File sorgente scaricati a
mano il 5 novembre, impronte identiche alla sonda mensile.

- **RTCave**: nuovo `scripts/update_rtcave_public.py` (solo `rtcave` e la scheda
  `extractiveSites`; verifica che la scheda pubblicata coincida con lo snapshot prima di
  scrivere). Snapshot `attivita-estrattive-v128.json` con `rtcave.retrievedAt`
  2026-11-05 (produzione e PRC invariati), 667 record regionali, 90 in Versilia; attivi 16,
  sospesi 4. Adattatore A6 `semantic_query_extractive_adapters.py` riallineato (data, SHA, 667).
- **ARS mortalità** (1438, 1499, 1327, 1606): periodo 2014–2023 aggiunto in coda, storico
  2002–2011 … 2013–2022 invariato (verificato). `materialize_salute_v140.py` ora espone
  `indicator_from_csv`; `EXPECTED_SHA`/`EXPECTED_PERIODS` aggiornati. Mortalità complessiva:
  catalogo, benchmark Toscana 829,96 e serie legacy A3.5.
- **ARS speranza di vita** (1290): serie 2008–2023; l'export rivede alcuni valori 2014–2020
  (Stazzema fino a +0,78 anni, maschi 2016), adottati. Il nome del file snapshot resta
  `ars-life-expectancy-1290-2008-2022.json` per non toccare il workflow dedicato.
  Materializzatore parametrico (`YEARS`, `--zip`, `--retrieved`).
- Snapshot demografico ARS rigenerato per i cinque indicatori.
- `semantic_query_road_adapters.py`: `CANONICAL_HASH` è l'impronta dell'intero
  `data/site-data.json`; va aggiornato a ogni modifica del catalogo.
- Domande verificate `ars_mortality_window_gap`/`ars_mortality_endpoint_refused` portate al
  2014–2023 (108,203); resoconti del programma dossier rigenerati (solo impronte).

## Controllo dati 2026-11: verifiche manuali RTCave e ARS (5 novembre 2026)

Branch `fix/data-check-2026-11`, costruito sulla PR automatica #552 (stato del monitor e
`reports/data-checks/2026-11.md`). La #552 da sola rompeva `test_attivita_estrattive_v128.py`:
RTCave aveva cambiato contenuto e il controllo metteva `extractiveSites` in
`verification_required` senza verifica registrata. Verifiche fatte su file scaricati a mano
(impronte identiche a quelle della sonda mensile):

- RTCave: 667 record regionali (erano 666), 90 in Versilia; un solo record versiliese cambiato,
  `id_cava` 402 «La Noce del Cardoso» (Stazzema) da Sospesa ad Attiva;
- ARS, 11 export: nessuna revisione dei valori pubblicati; periodo nuovo per `mortalityAll`,
  `mortalityCancer`, `mortalityCirculatory`, `mortalityRespiratory` (2014–2023) e
  `lifeExpectancy` (2023); gli altri 6 invariati per il perimetro pubblicato.

In `data/source-monitor-state.json` i sei indicatori passano a `release_detected` con
`releaseEvidence`/`verificationEvidence` (fonte, impronta, metodo, esito); il prossimo controllo
li conserva finché il periodo pubblicato resta lo stesso. Nessun valore pubblicato cambia.
Aggiornare i dati richiede una PR separata: per le cave la fotografia
`attivita-estrattive-v128.json` è vincolata dall’adattatore A6
`semantic_query_extractive_adapters.py` (SHA RTCave, 666 record, data 2 settembre 2026), che non
va toccato senza decisione esplicita.

## Dossier «Partecipazione e cultura in Versilia» (5 novembre 2026)

Branch `feature/dossier-partecipazione`, diciassettesimo dossier in forma di relazione (slug
`partecipazione`, tema comunita), scheda `partecipazione` di
`ci/territorial-dossier-program.json`, con tutti i sette `metricRefs`; completa il programma
dei dossier. Sei capitoli:

1. quanto si vota: `voterTurnout` `family:*|nativeRatio` per l’ultima elezione di ciascuna
   famiglia (politiche Camera, europee, regionali, referendum), Versilia ponderata;
2. il voto nel tempo: per ogni elezione politica ed europea della serie, un `weighted_ratio`
   Versilia con `periods` esplicito (riquadro con tabella), nessuna variazione calcolata;
3. biblioteche: prestiti per abitante, utenti ogni 100 abitanti e ore di apertura con Toscana
   (`allowPartial`: Massarosa e Stazzema non pubblicati);
4. spesa per cultura, sport e giovani 2025 con Versilia (nessun benchmark nel motore);
5. associazioni: `thirdSector` come nel dossier welfare;
6. percorsi: `slowMobilityRoutes`, solo Comuni.

`period_label` legge i periodi elettorali («elezioni europee del 9 giugno 2024»). Nuove fonti
con nome pubblico: Eligendo in `SOURCE_NAMES`, monitoraggio regionale delle biblioteche in
`SOURCE_BY_METRIC` (l’URL di dati.toscana.it avrebbe dato un nome sbagliato).

## Dossier «Personale e servizi digitali dei Comuni» (5 novembre 2026)

Branch `feature/dossier-capacita`, sedicesimo dossier in forma di relazione (slug `capacita`,
tema bilanci), scheda `capacita` di `ci/territorial-dossier-program.json`, con tutti i sei
`metricRefs` più `ftthCoverage20m`. Sei capitoli:

1. dipendenti: `municipalEmployeesPer1000` ogni 1.000 abitanti con Toscana e Versilia, e numero;
2. età: `municipalStaffAgeStructure` 55 anni e più e sotto i 40, Versilia ponderata;
3. assunzioni e uscite: `municipalStaffTurnover` saldo % con Versilia, assunzioni e cessazioni;
4. formazione: `municipalStaffTraining` media per dipendente con la media Versilia pubblicata
   dalla RGS (scope `versilia`) e giornate totali; nuova unità `daysPerEmployee`;
5. servizi online: `municipalOnlineServicesAdvanced` 2022 con Toscana;
6. fibra: `ftthCoverageDesi` e `ftthCoverage20m` con Toscana e Italia (il motore non aggrega
   le percentuali arrotondate AGCOM, quindi niente Versilia).

Nome della fonte corretto: i CSV BDAP «Dipendenti Pubblici» sono il conto annuale del
personale, non i rendiconti dei Comuni. La nuova voce in `SOURCE_NAMES` vale anche per il
dossier bilanci, che usa le stesse metriche. Nessun giudizio su produttività o qualità del
lavoro dai tassi.

## Dossier «Energia e transizione in Versilia» (5 novembre 2026)

Branch `feature/dossier-energia`, quindicesimo dossier in forma di relazione (slug `energia`,
tema ambiente), scheda `energia` di `ci/territorial-dossier-program.json`. Dossier breve
concordato con Ema: la scheda ha tre `metricRefs` e la domanda su edifici, rinnovabili e CER è
`not_determinable`. Quattro capitoli:

1. carburanti: `fuelPrices` `fuel:benzina` e `fuel:gasolio` al 10 ottobre 2026
   (`allowPartial`: Stazzema non ha distributori attivi), più le serie `monthly:*` per Comune
   da gennaio 2022: il testo riporta valori pubblicati di gennaio e settembre 2026 e il mese
   più caro della serie, senza variazioni calcolate (il motore rifiuta `relative_change`);
   nuova unità `eurliter`, nome pubblico MIMIT in `SOURCE_NAMES`;
2. colonnine: `evPoints` 2026, solo Comuni (pooling non rivisto);
3. auto: `motorization` e `pollutingCars` `nativeRatio` con Toscana, Italia e Versilia;
4. redditi bassi: `incomeDistribution` `macro:0` e `band:0to10k`, come contesto e non come
   misura di povertà energetica.

Colonnine e auto sono anche nel dossier mobilità e i redditi nel dossier redditi; qui servono
come contesto della transizione. «Cosa non sappiamo» elenca consumi, bollette, produzione
rinnovabile, classi energetiche, povertà energetica e dati per le CER.

## Dossier «Suolo, boschi e agricoltura in Versilia» (5 novembre 2026)

Branch `feature/dossier-suolo`, quattordicesimo dossier in forma di relazione (slug `suolo`,
tema ambiente), scheda `suolo` di `ci/territorial-dossier-program.json`, con tutti i nove
`metricRefs` più `agriculturalFarms` e `averageAgriculturalFarmSize`. Sette capitoli:

1. suolo consumato: `landUse` 2024 in % con Toscana, Italia e Versilia, e `view:sqmPerResident`
   (nuova unità `sqm`);
2. consumo dell’ultimo anno: `landUseChange` lordo e netto 2024 in ettari (nuova unità
   `hectares`), solo Comuni: il motore non aggrega i flussi;
3. com’è fatto il territorio: `landCoverProfile` UCS 2019, macroclassi artificiali, agricole,
   boschi e seminaturali, zone umide e acque, mai sommate fra loro;
4. boschi: `forestCoverIndex` (Foreste in Comune, CFI 2020 aggiornata 2024), % e ettari;
5. aree protette: `protectedNaturalAreas` totale (unione geometrica) e Natura 2000;
6. agricoltura: SAU sulla superficie (`view:normalized`), ettari, aziende, dimensione media con
   Toscana e Italia (nuova unità `haPerFarm`), seminativi, olivi da olio, prati e pascoli
   (`VINEY` escluso: copertura parziale);
7. chi guida le aziende: capi azienda fino a 40 anni e conduttrici donne con Versilia
   ponderata, biologico 2024 con Toscana (nessun aggregato Versilia).

Fonti con nome pubblico per metrica in `SOURCE_BY_METRIC`, perché gli URL regionali generici
corrisponderebbero a fonti sbagliate. Suolo consumato ISPRA, UCS e carta forestale sono fonti
distinte e il testo non le confronta; superficie tutelata non misura lo stato della biodiversità.

Nello stesso branch: `scripts/build_static.py` apre una scheda nuova ogni 25 rotte nel
prerender (`PRERENDER_PAGE_BATCH`). Con una sola scheda per tutte le 198 rotte Chromium
superava i 5,5 GB e veniva terminato dal kernel nei container con limite di 5,8 GB (due
preflight falliti su pagine diverse). Ogni rotta era già una navigazione completa, quindi
l’HTML prerenderizzato non cambia.

## Dossier «Il welfare in Versilia» (4 novembre 2026)

Branch `feature/dossier-welfare`, tredicesimo dossier in forma di relazione (slug `welfare`,
tema comunita), scheda `welfare` di `ci/territorial-dossier-program.json`, con tutti i sei
`metricRefs`. Sei capitoli, 593 risposte del motore in tutto il generatore:

1. fragilità: `municipalFragility` (decili IFC 2022 e classi 2018-2021). È ordinale e il motore
   ammette solo `compare` e `series` (una richiesta per Comune): nuovi `Engine.ordinal` e
   `Engine.ordinal_history`, unità `decile`, grafico `decile_chart` su scala fissa 1-10 in
   ordine alfabetico, senza graduatoria, medie né variazioni;
2. spesa sociale: `socialSpendingPerResident` 2022 con Toscana e Italia (niente valore
   Versilia: denominatori nativi non disponibili);
3. a chi va: `socialSpendingByUserArea` per famiglie e minori, disabilità, anziani, povertà;
   immigrati, dipendenze e multiutenza restano fuori dai grafici (quote piccole o nulle);
4. disabilità: `disability064Per1000` 2024 con Toscana, nuova unità `per1000young`;
5. stranieri: `foreignResidents` 2025 con Toscana, Italia e Versilia ponderata, più i conteggi;
6. Terzo settore: `thirdSector` `nativeRatio` (Versilia ponderata) e `registeredEntities`,
   nuova unità `per1000dec`; sedi legali, non servizi erogati.

Nuove fonti con nome pubblico: RUNTS in `SOURCE_NAMES`; IFC e indicatori regionali della
disabilità in `SOURCE_BY_METRIC`. Seguendo la scheda: nessuna graduatoria politica dalla
fragilità o dalla spesa, e la spesa non misura bisogno né qualità dei servizi.

## Dossier «I redditi in Versilia» (4 novembre 2026)

Branch `feature/dossier-redditi`, dodicesimo dossier in forma di relazione (slug `redditi`,
tema economia), scheda `redditi` di `ci/territorial-dossier-program.json`. Sette capitoli,
tutti su dati MEF del periodo d’imposta 2024:

1. quanto si dichiara: reddito imponibile medio con Toscana e Italia (il motore non
   calcola un `weighted_ratio` Versilia per `income`, quindi nessun valore Versilia);
2. redditi e prezzi: `incomeVsInflation` 2016-2024 con Toscana e Italia (NIC nazionale);
3. redditi bassi: `incomeDistribution` `macro:0` (fino a 15.000 €) e `band:0to10k`, Versilia
   ponderata;
4. redditi alti: `macro:3` (oltre 55.000 €); la fascia centrale è il complemento a 100 delle
   due macro-fasce esclusive, dichiarato nel testo;
5. fonti: `incomeSourceProfile` lavoro dipendente (unica fonte con benchmark), autonomo e
   fabbricati; le medie valgono per chi dichiara quella fonte e non si sommano;
6. pensioni: `pensionIncomeShare` con Toscana e Italia e pensione media dichiarata;
7. contribuenti: `taxpayersAdultPopulationRate` (periodo ibrido MEF 2024 · residenti 2026),
   nuova unità `per100adult` («ogni 100 residenti maggiorenni» nel CSV).

Le fasce oltre 120.000 € e l’impresa in contabilità ordinaria hanno celle MEF vuote in alcuni
Comuni e restano fuori. Seguendo la scheda: il reddito dichiarato non è il reddito
disponibile della famiglia e un reddito basso non prova un bisogno.

## Dossier «La salute in Versilia» (4 novembre 2026)

Branch `feature/dossier-salute`, undicesimo dossier in forma di relazione (slug `salute`,
tema salute), scheda `sanita` di `ci/territorial-dossier-program.json`. Sette capitoli,
517 risposte del motore in tutto il generatore:

1. quanto si vive: speranza di vita 2022 e mortalità per tutte le cause 2013-2022
   (tassi standardizzati ARS), con Toscana e zona Versilia ARS;
2. cause: mortalità per tumori e per malattie del sistema circolatorio 2013-2022;
3. malattie croniche: almeno una cronicità (solo zona Versilia: il motore non certifica
   il benchmark Toscana per `chronicTotal`), diabete e ipertensione 2025;
4. pronto soccorso e ricoveri: accessi 2025 e residenti ricoverati 2021-2025 (solo zona
   Versilia per i ricoveri, stessa ragione);
5. 118: 75° percentile 2024 con la sola Toscana, nessun valore Versilia (la mediana dei
   sette Comuni non è ufficiale);
6. visite ed esami: visite delle sette specialità PSR e diagnostica per immagini 2025;
7. servizi: strutture di ricovero e RSA accreditate 2025 (somma dei sette Comuni, solo
   nel testo), farmacie ogni 1.000 abitanti con Toscana e Italia, minuti dal polo IFC 2019.

Per le misure ARS il valore «Versilia» è il benchmark ufficiale della zona (scope
`versilia` di `benchmark_gap`), non un `weighted_ratio`: il metodo lo dichiara. Nuove unità
`per100k`, `per100res` (accessi ogni 100 abitanti, distinta da `per100` che nel CSV vale
«ogni 100 persone di 15-64 anni») e `minutes`. `SOURCE_BY_METRIC` dà un nome pubblico a
118, strutture di ricovero, RSA accreditate e accessibilità IFC: il nome per URL
assegnava alle RSA la fonte del movimento turistico e al 118 quella sull’ICT.
Seguendo la scheda: utilizzo non è accessibilità, una struttura censita non è capacità,
nessuna lettura clinica né causale.

## Dossier «Investimenti e opere in Versilia» (4 novembre 2026)

Branch `feature/dossier-investimenti`, decimo dossier in forma di relazione (slug
`investimenti`, tema comunità), ultimo della terna ambiente-demografia-investimenti.
Cinque capitoli, 460 risposte del motore in tutto il generatore:

1. PNRR: fondi dei progetti con il Comune soggetto attuatore (fotografia Regione
   Toscana 25 settembre 2026), per abitante (`nativeRatio`, valore Versilia) e in euro;
2. avanzamento: quota e numero dei progetti in fase ReGiS «conclusione» (stato
   amministrativo, non collaudo né apertura);
3. opere: valore delle opere monitorate BDAP-MOP per abitante (stock, non spesa annua);
4. bilanci: impegni del titolo 2 e pagamenti SIOPE in conto capitale 2025, rimando al
   dossier bilanci;
5. fossi e canali: PAB 2026 del Consorzio 1 Toscana Nord (interventi e valore
   programmati) e quota registrata come conclusa nel portale al 31 agosto 2026; nessuna
   somma fra Comuni, rimando al dossier ambiente.

Nessun confronto con Toscana o Italia: il motore non ne certifica per questi indicatori.
Seguendo `ci/territorial-dossier-program.json` (scheda investimenti): finanziato,
impegnato, pagato e concluso restano distinti e non si sommano; nessun effetto attribuito
alle opere. Nuovo `SOURCE_BY_METRIC`: `publicWorks` condivide l’URL OpenBDAP con le misure
di rendiconto, quindi il nome pubblico della fonte segue l’indicatore. Il nome della fonte
dei pagamenti in conto capitale diventa «SIOPE — Pagamenti dei Comuni (open data BDAP)»
anche nel dossier bilanci.

## Dossier «Chi vive in Versilia» (4 novembre 2026)

Branch `feature/dossier-demografia`, nono dossier in forma di relazione (slug
`demografia`, tema popolazione), dopo ambiente; poi investimenti. Sei capitoli, 431
risposte del motore in tutto il generatore:

1. quanti siamo: residenti 2026 (totale Versilia = somma dei sette Comuni, dichiarata
   nel metodo) e variazione 2019-2026 con Toscana e Italia;
2. nascite: nati e morti ogni 1.000 abitanti 2025 (provvisori) e saldo naturale, con
   rimando al dossier anziani che usa lo stesso saldo;
3. chi arriva e chi parte: saldo dei trasferimenti 2024 totale, con l’Italia e con
   l’estero; arrivati e partiti interni solo nel testo (eccezione Forte dei Marmi);
4. stranieri: quota e numero dei residenti con cittadinanza straniera 2025;
5. giovani: quote 0-14 e 20-34 anni 2026;
6. famiglie: componenti medi e famiglie unipersonali 2023 (censimento permanente;
   nessun valore Versilia, il motore non lo calcola), rimando al dossier casa.

Seguendo `ci/territorial-dossier-program.json` (scheda demografia): saldo naturale e
mobilità restano flussi distinti, in periodi propri, mai sommati né usati per previsioni;
la cittadinanza non è descritta come luogo di nascita. Unità `rate1000` per nati e morti
(senza segno), `per1000s` per i saldi.

## Dossier «Ambiente e rischi in Versilia» (3 novembre 2026)

Branch `feature/dossier-ambiente`, ottavo dossier in forma di relazione, scelto dal
proprietario come primo dopo bilanci e mobilità (poi demografia e investimenti).
Sette capitoli, 361 risposte del motore in tutto il generatore:

1. alluvioni: residenti in pericolosità media (P2) ed elevata (P3), mappa ISPRA 2020,
   censimento 2011; scenari annidati, non sommati;
2. frane: residenti e territorio in pericolosità elevata e molto elevata (P3+P4),
   mappa 2024, censimento 2021;
3. clima: temperatura e pioggia 2025, delta OLS 1975-2025 (LaMMA/ERA5-Land); nessun
   valore Versilia né confronto con Toscana, che il motore rifiuta;
4. costa: dinamica della riva 2006-2020 e costa protetta da opere rigide (quattro
   Comuni costieri, `partial=True`; confronto con Toscana e Italia solo per le opere);
5. mare: aree di balneazione eccellenti 2022-2025, campioni di routine fuori limite
   2025 (non i campioni suppletivi, mirati), Bandiere Blu 2026 solo nel testo;
6. rifiuti e acqua: raccolta differenziata e rifiuti per abitante 2024, perdite
   idriche 2018; rimando al dossier bilanci per costo del servizio e TARI;
7. bonifiche: procedimenti SISBON aperti e totali.

Seguendo `ci/territorial-dossier-program.json` (scheda ambiente): pericolosità ed
esposizione distinte dal rischio, nessuna previsione per edificio, protezione rigida e
procedimento chiuso non descritti come efficacia o risanamento. Consumo di suolo e
agricoltura restano per il dossier «suolo».

Altre modifiche:
- `SOURCE_NAMES`: le voci specifiche (IdroGEO, LaMMA, ISPRA coste, ARPAT
  balneazione, FEE, catasto rifiuti per la produzione, censimento Istat delle
  acque, SISBON) stanno in testa, perché vince la prima corrispondenza;
- unità `celsius`, `celsiusdelta`, `mm`, `kg`; funzione `sul()` per «sull’87,8%»;
- frasi che citano montagna e quota solo se i valori estremi sono di Stazzema o
  Seravezza;
- `ci/content-contract.json`: `dossier/ambiente/index.html`; indice dei dossier
  aggiornato.

## Radar 2.0 — le schede automatiche si rileggono quando cambiano le regole (3 novembre 2026)

Branch `fix/radar-rilettura-schede-auto`: dopo il merge della #536 il run del 3/11 ha tenuto pubblicata GranFest (Fondazione CR Lucca), qualificata il 2/11 con le regole precedenti su una frase che cita il Comune solo come possibile finanziatore. Causa: `apply()` riportava le schede `auto_qualified` dei giorni precedenti fino alla scadenza senza rileggerle. Ora `VERSION` del qualificatore è `1.1` e una scheda con `auto_qualification_version` diversa torna in lettura per prima, anche se scartata di recente: se le regole attuali la qualificano viene ricostruita, se la respingono o è scaduta esce (conteggio `withdrawn`, «ritirate perché non superano più le regole» nel rapporto del run), se la pagina non si legge in quel run resta com'era. Ogni futura modifica alle regole di ammissibilità deve alzare `VERSION`. Test: `test_cards_from_older_rules_are_reread` (fallisce senza la correzione).


## Radar 2.0 — icone fonte per tutti i domini ufficiali (2 novembre 2026)

Branch `fix/radar-icona-anci-abruzzo`: il Radar del 2/11 su main non si pubblicava (`build_static_brand.py`: «Icone fonte incomplete: 161/162», scheda ANCI Abruzzo «Avviso MIM vulnerabilità sismica»). `materialize_opportunity_release_favicons.py` copre ora tutti i domini di `OFFICIAL_SUFFIXES` del qualificatore: alias ai favicon versionati (Sviluppo Toscana, Fondazione CR Lucca, GSE) e source-mark locali (ANCI, ANCI Toscana, ANCI Abruzzo, Invitalia, CDP, Italia Domani, Interreg Europe, URBACT, Interreg Marittimo). Il test `test_every_official_qualifier_host_has_a_source_icon` fallisce se si aggiunge un dominio ufficiale senza icona.
## Dossier «I conti dei Comuni» (2 novembre 2026)

Branch `feature/dossier-bilanci`, settimo dossier in forma di relazione e ultimo dei
due prioritari (dopo la mobilità). Sette capitoli dai rendiconti 2025 (OpenBDAP),
da SIOPE, dalle delibere MEF 2025 su addizionale IRPEF e TARI, dal costo ISPRA dei
rifiuti 2024, dal Conto annuale RGS 2024 e dall'indicatore regionale sui servizi
online (Istat ICT 2022):

1. entrate e riscossione;
2. spesa corrente, sociale e scuola;
3. investimenti impegnati e pagati;
4. risultato disponibile e spese rigide;
5. debito e interessi;
6. IRPEF e TARI su casi tipo, costo dei rifiuti;
7. personale e servizi online.

Gli aggregati Versilia sono quelli che il motore calcola (`weighted_ratio`).
Per spese rigide, risultato del Piano degli indicatori, TARI e IRPEF il motore non
ammette aggregati, quindi il testo cita solo i valori comunali. Toscana compare solo
dove il motore ha il confronto: dipendenti, servizi online, costo dei rifiuti.

Seguendo `ci/territorial-dossier-program.json` (scheda bilanci), il testo:
- non calcola margini disponibili;
- non equipara la spesa ai servizi ricevuti;
- avverte che i valori per residente dei Comuni turistici sono gonfiati da chi non
  vi risiede.

Altre modifiche:
- nuova funzione `money()` e unità `eurc`, per gli euro con i centesimi solo quando
  servono (IRPEF di Camaiore 144,50);
- l'articolo si apostrofa anche davanti a 1 («l'1,7%»);
- nuovi nomi di fonte: SIOPE, Conto annuale, BDAP open data, delibere MEF, ISPRA,
  indicatori comunali regionali.

## Abitare in terracotta (2 novembre 2026)

Branch `feature/abitare-terracotta`, su richiesta del proprietario. Il viola di
Abitare (#6d5ca6) era quasi identico a quello di Istruzione (#7357a8, distanza
percettiva ΔE 6). Nuova palette DS2 di Abitare: accento #8e5a46, scuro #734637,
fondo #fbf4f1, linea #e6d3ca. Contrasto sul bianco 5,7:1; ΔE minimo dagli altri
temi 23 (Sicurezza). Una terracotta più accesa (#b5653f) sarebbe finita a ΔE 8
da Sicurezza e 15 da Demografia ed è stata scartata. File toccati: fidelity.css
(tema, pillole del contesto, pilota municipale), dossier-report.css,
secondary-pages-ui.css (card della home, ora coerente col marrone delle icone).
Le baseline visive (golden lock tematico e municipale, visual-regression
themes) si aggiornano in una PR successiva secondo docs/A5_GOLDEN_MASTERS.md.

## Dossier «Muoversi in Versilia» e icone dei temi (1° novembre 2026)

Branch `feature/dossier-mobilita`, su richiesta del proprietario (proseguire con
gli altri dossier; alla pubblicazione icone e colori dei temi del sito). Sesto
dossier in forma di relazione, primo dei due prioritari rimasti (poi bilanci e
servizi): occupati che lavorano fuori Comune e pendolari in uscita e in entrata,
corse di autobus e treni, ampiezza della giornata di servizio e fermate (GTFS,
un giorno feriale d’estate), automobili ed Euro 0-3, punti di ricarica, fibra
fino all’edificio (AGCOM), percorsi a piedi e in bici. Saldo e autocontenimento
restano nel dossier lavoro, con rimando. Nessun aggregato Versilia dove il
motore lo rifiuta (TPL, veicoli, ricarica, fibra, percorsi). Le date dei periodi
(`AAAA-MM-GG`) sono scritte per esteso; lo zero prende l’articolo «lo»; la fonte
GTFS ha un nome proprio prima della regola generica `dati.toscana.it`, che
l’avrebbe chiamata «servizi per la prima infanzia».

Icone e colori: ogni dossier e ogni scheda dell’indice portano l’icona del tema
del sito (tracciati letti da `themeSvgPaths` in `assets/app-parts/00.txt`, non
duplicati) e la palette DS2 delle pagine tematiche (`--ds-theme-accent`); il
turismo usa il colore di Economia con un’icona propria (ombrellone). Barre,
riquadri e numeri del dossier prendono il colore del tema.

## Workflow superati — primo lotto (1° novembre 2026)

Branch `chore/retire-obsolete-workflows`, su decisione del proprietario (pulizia
caso per caso). Ritirati `invalsi-v138-preview` e `biometria-comune-preview`:
anteprime di rilasci già in produzione, ultimo run il 13/9 fallito. I loro gate
di sorgente (`test_invalsi_v138.py`, `test_biometria_comune_release.py`, offline,
meno di un secondo) passano ora nei quickChecks canonici, quindi la copertura
non cala. Restano attivi, con motivazione: le acquisizioni
`meteo-poc`, `climate-minmax-extend` e `probe-istat-lavoro-istruzione` sono
l'unica via documentata per rigenerare quei dati; lo shadow
`opportunity-radar-daily-v2-shadow` esce con la fase 2 del Radar insieme a
`opportunity-radar-v044-ci`, che ne esegue il test.

## Radar 2.0 — coda interna letta dal qualificatore (2 novembre 2026)

- Origine: audit indipendente del 2 novembre. FUORILUOGO (Fondazione CR Lucca, Comuni richiedenti diretti, scadenza 11/12/2026) era stato trovato ma restava in `reviewQueue` con «Manca una regola documentale v0.2.1»: il qualificatore automatico leggeva solo `discoveryQueue`.
- Ora `opportunity_qualifier.apply` legge anche le schede in `reviewQueue` delle fonti primarie (`review_candidates`), con le stesse regole generali e l'etichetta «Requisiti da confermare»; le schede pubblicate escono dalla coda interna. Escluse le prefetture (`REVIEW_EXCLUDED_SOURCES`), che hanno filtri dedicati.
- Nessun doppione delle schede curate con titolo diverso: se almeno l'80% delle parole significative del titolo in coda compare in un titolo pubblicato della stessa fonte, la scheda è saltata (caso BELLA LÌ).
- Prova sul vivo dalla coda del 2/11: oltre a FUORILUOGO si sblocca «Contributi agli enti locali per lo sviluppo di progettualità sui dati» (Regione Toscana, Comuni toscani, a sportello dal 22/10). Concorsi, selezioni di personale e bandi per imprese restano scartati.
- Due correzioni emerse dalla prova: «beni comuni», «spazi comuni» e simili non valgono come Comuni richiedenti; le sezioni «Varianti/Esecutivi» non sono avvisi.
- SRA31: nessun difetto, la proroga al 13/11 era già nello snapshot del 2/11 ore 07:36; l'audit aveva letto la pagina del 30/10.
- GSE: resta «bloccata e coperta» (firewall sui server della CI); nessuna modifica in questa PR.
- Correzione dopo il primo giro reale (#533): GranFest 2027 era pubblicato come partnership, ma la scheda dice «riservata a soli soggetti privati» (il Comune compariva solo fra i possibili finanziatori). Il bando regionale sui dati era già pubblicato con altro titolo e il controllo dei doppioni lo ha saltato correttamente.

## Radar 2.0 — chi può candidarsi si legge nella voce dei destinatari (2 novembre 2026)

- Decisione del proprietario: la voce dei destinatari del bando è l'unica base per stabilire se il Comune può candidarsi. Niente più ricerca della parola «Comune» in tutta la pagina.
- `find_beneficiaries` legge prima la scheda, poi i documenti: voci «Beneficiari», «Soggetti ammessi/beneficiari/richiedenti…», «Chi può partecipare», «Possono presentare domanda…», «Domanda presentata da», «Requisiti di ammissibilità», «Eligible applicants». Decide la prima voce sui richiedenti; «Destinatari» da solo può indicare il pubblico delle attività (cittadini, scuole) e quindi include ma non esclude.
- Prevalgono sempre «riservata a soli soggetti privati» e l'esclusione espressa degli enti pubblici. Il Comune come finanziatore, patrocinatore o luogo del progetto non è un richiedente. Contano anche «enti pubblici», «soggetti pubblici o privati», «enti di diritto pubblico» e l'etichetta regionale «Destinatari: Enti».
- Nessuna voce trovata: la scheda resta in coda, non si pubblica. La scheda pubblicata cita la voce.
- I topic UE (`strict_municipal`) mantengono le regole dedicate EU_LEAD/EU_PARTNER.
- Seconda decisione del proprietario: resta fuori solo il bando in cui il Comune non c'entra in alcun modo. Se può partecipare in qualsiasi forma (richiedente, partner, consorzio, associazione, collaborazione con accordo) il bando va bene. Nel qualificatore la prima frase della voce decide chi presenta; le frasi successive contano se ammettono il Comune (`LATER_ADMISSION`, `LIST_ITEM_PUBLIC`) o lo fanno collaborare (`MUNICIPAL_AS_COLLABORATOR`, ruolo partner); patrocinio, sostegno, parere o nulla osta del Comune non sono partecipazione (`MUNICIPAL_AS_SUPPORTER`). Le schede curate Pro Loco (Comune partner con accordo formalizzato) e Spreco alimentare (Comune partner operativo) restano quindi valide.
- Prova sulla coda live del 2/11 (282 segnalazioni lette): escono servizio civile regionale (destinatari: giovani 18-29 anni) e una pagina indice «Avvisi pubblici e premi»; entra Sport e Salute «Fabbrica Spazi Civici» come partnership («al partenariato possono aggiungersi anche enti pubblici»). Sui 58 pubblicati nessun cambio.

## Lancio di «Chiedi» e «Dossier» (31 ottobre 2026)

Branch `feature/launch-chiedi-dossier`, su decisione del proprietario: nel menu
principale «Dossier» e «Chiedi» dopo «Comuni» (contratto `HEADER_LINK_LABELS`,
coerenza, fixture e browser test aggiornati; voce attiva calcolata dal percorso);
in home un riquadro dopo i Temi con i link a `/dossier/` e `/chiedi/`. Dossier e
indice senza `noindex` e registrati nella sitemap da `build_dossier_reports.py`;
`/chiedi/` era già indicizzabile. `materialize_opportunity_public_shell.py`
riconosce la voce Opportunità già materializzata anche con le nuove voci. Su
mobile, sotto 440 px, l’header mostra solo il marchio OV senza la scritta
(prima sotto 380 px), così «Opportunità» resta visibile nel menu; fra 701 e
940 px il menu scorre in orizzontale come su mobile (con 8 voci l’header
sforava di ~60 px a 768). `test_site_chrome_browser.py` verifica la scritta
nascosta sotto 440 px invece di misurarne la geometria.

## Radar 2.0 — fonti bloccate ma coperte (31 ottobre 2026)

Branch `fix/radar-gse-blocked-covered`: il GSE blocca la CI con il firewall;
se MASE, ANCI o ANCI Toscana rispondono, il rapporto lo elenca fra le «Fonti
bloccate ma coperte» invece che fra quelle da riparare (`COVERED_WHEN_BLOCKED`
in `opportunity_qualifier.py`). Dettagli in `docs/RADAR_2.md`.

## Radar 2.0 — correzioni del qualificatore (31 ottobre 2026)

Branch `fix/radar-qualifier-eu-topics`: il primo run di produzione del
qualificatore non ha pubblicato nulla. L'anno nel codice di un topic UE non lo
scarta più se la scadenza strutturata è futura; un'autorità pubblica locale nel
consorzio come beneficiaria vale come partecipazione da partner. Dettagli in
`docs/RADAR_2.md`. Fase 2 (pipeline unica) ancora da fare.

## Radar 2.0 — qualificazione automatica (31 ottobre 2026)

Branch `feature/radar-discovery-overhaul`, presa in carico su richiesta del
proprietario dopo l’issue #511 (CERV-DAPHNE aperti a luglio, rilevati a fine
ottobre). Diagnosi e piano in `docs/RADAR_2.md`. Questa fase: qualificazione
automatica delle segnalazioni con etichetta «Requisiti da confermare»
(`opportunity_qualifier.py`), fonte UE dall’interfaccia ufficiale Funding &
Tenders (`opportunity_eu_calls.py`), fonti da riparare, ritardo di rilevazione nel
rapporto e rapporto come commento sulle PR del Radar. Fase 2: pipeline unica al
posto dei sette strati.

## A7.5.6 — riorganizzazione di «Chiedi» (30 ottobre 2026)

Branch `feature/a7-chiedi-reorg`. Su decisione del proprietario `/chiedi/` non
pubblica più le domande guidate del pilota (offerta educativa, percorsi
Massarosa): la pagina è hero, esploratore e rimando a `/dossier/`.
`build_a7_public_page.py` genera la pagina senza rilascio del pilota;
`validate_public_site.py` richiede esploratore e link ai dossier; ritirati
`a7_public_release.py`, `a7_education_editorial.py`,
`test_a7_education_editorial.py` e `verify_public_page`. Il pilota resta
verificato come esperimento. Dopo la revisione dell’anteprima resta il lancio.

## A7.5.5 — riuso dei risultati di «Chiedi» (30 ottobre 2026)

Branch `feature/a7-reuse-export`. Ogni risultato dell’esploratore offre: «Copia
il link» (indicatore, dettaglio, domanda, Comune e riferimento nel frammento
`#esplora&…`, letto una sola volta e poi rimosso dall’indirizzo), «Scarica i dati
(CSV)» con i valori esatti delle risposte A6 (separatore `;`, virgola decimale) e
la riga del risultato nativo, «Stampa o salva in PDF» con una copia del solo
risultato. Nessun nuovo calcolo nel browser. Restano A7.5.6 (riorganizzazione
della pagina) e il lancio di «Chiedi» e «Dossier» in navigazione.

## Dossier — pagina indice (29 ottobre 2026)

`dist/dossier/index.html`: una scheda per dossier con tema, presentazione, primo
dato della sintesi, link a pagina, PDF e CSV; il percorso di ogni dossier porta
all’indice. Tutte le pagine restano `noindex` e fuori da menu e sitemap: il
lancio (menu, home, indicizzazione) insieme a «Chiedi» richiede l’approvazione
del proprietario.

## Dossier come relazione — «Crescere in Versilia» (29 ottobre 2026)

Quinto dossier `dist/dossier/scuola/`: posti nei servizi per la prima infanzia,
tempo pieno e alunni per classe, età degli edifici e mense, INVALSI di quinta
primaria (copertura parziale dichiarata: Stazzema non pubblicato), adulti con
almeno il diploma, spesa comunale per l’istruzione. Il generatore accetta misure
a copertura parziale (`allowPartial`), con nota nel grafico e frase per Comune.
Restano la pagina indice `/dossier/` e il lancio.

## Dossier come relazione — «Invecchiare in Versilia» (29 ottobre 2026)

Quarto dossier `dist/dossier/anziani/`: indice di vecchiaia e sua variazione,
anziani per 100 persone in età da lavoro, grandi anziani (85+), saldo naturale e
variazione della popolazione, speranza di vita (ARS), assistenza domiciliare e
farmacie, spesa sociale dei Comuni. Costruito sopra il ramo del turismo (#501).

## Dossier come relazione — «La Versilia dei turisti» (29 ottobre 2026)

Terzo dossier `dist/dossier/turismo/`: presenze e intensità turistica,
variazione delle presenze fra il primo e l’ultimo anno disponibili (una
`relative_change` A6 per Comune), permanenza e turisti residenti all’estero,
stagionalità, posti letto e strutture, spesa comunale per il turismo. Il
generatore aggiunge le misure di variazione per Comune e i nomi pubblici di
Regione Toscana e OpenBDAP; il gate abbina ogni grafico alla sua misura.

## Dossier come relazione — «Lavorare in Versilia» (28 ottobre 2026)

Formato approvato dal proprietario con la #495 (casa). Secondo dossier
`dist/dossier/lavoro/`: occupazione e disoccupazione 25-64 anni, giovani e donne,
addetti e dimensione delle imprese, pendolari 2021, retribuzioni e valore
aggiunto, redditi da lavoro e pensioni. Il generatore ora gestisce valori negativi
(saldo pendolare), nomi delle fonti per tipo di rilevazione e articoli italiani
davanti alle cifre. Chiuse su decisione del proprietario le PR superate #494, #443,
#338 e #117. Pagine ancora `noindex` e fuori dal menu; manca una pagina indice
`/dossier/` prima del lancio.

## Dossier come relazione — prototipo «Abitare in Versilia» (27 ottobre 2026)

Il proprietario ha respinto i dossier come elenco di evidenze (#494, in pausa):
un dossier deve dare valore al dato, in forma di relazione divulgativa
(riferimenti Openpolis, ONS, Dove vanno i nostri soldi), senza rimandi a
GitHub né JSON scaricabili. Scelte: tema «Casa e affitti», punto di vista
«Versilia + scegli il tuo Comune», tono divulgativo. Branch
`feature/dossier-report-casa`: `scripts/build_dossier_reports.py` genera
`dist/dossier/casa/` (sintesi, sei capitoli con domanda, grafici, «Perché
conta», versione per Comune, «Cosa non sappiamo», fonti e note), un PDF della
versione Versilia e un CSV per Excel. Ogni cifra viene da una risposta calcolata
dal motore A6; le frasi sono modelli fissi senza cause. Pagina `noindex` e fuori
dalla navigazione fino all’approvazione. Gate `test_dossier_reports.py`. Prossimo
passo: revisione del proprietario, poi estensione agli altri temi.

## A7 — perimetro della prima versione e valori fuori scala (26 ottobre 2026)

Decisione del proprietario: la prima versione guidata di «Chiedi» comprende le
domande su una misura, il riuso delle analisi (CSV/PDF) e il consolidamento; gli
incroci (A7.5.4) sono rinviati. Il lancio in navigazione avviene solo a
perimetro completo. Branch `feature/a7-outlier-values`, base main #489: espone
l’operazione A6 `anomaly` come «Valori fuori scala fra i sette Comuni»
(profilo `outliers`, regola di Tukey, interfaccia v8). 515 viste ammesse, 503
calcolate. Metodo `A7_OUTLIER_VALUES.md`. Con questo incremento tutte le
operazioni su una misura ammesse da A6 sono presentate, salvo 9 viste con
riferimento «Versilia», escluse per scelta. Restano A7.5.5 riuso e A7.5.6
consolidamento.

## A7.5.4 — perimetro degli incroci misurato e rivisto (26 ottobre 2026)

Branch `feature/a7-association-perimeter`, base main #488. Delle 202
associazioni fra le domande verificate A6, 6 sono calcolate e 196 rifiutate
(175 per coppia non rivista congiuntamente). Il costo non è il vincolo: 32
componenti aggiungono +0,10% di gzip al runtime pubblico completo. Decisione del
proprietario: perimetro = le 6 associazioni calcolabili, con motivi in italiano
come nuove richieste esatte dai risultati invariati. Piano
`ci/a7-association-perimeter.json`, gate `test_a7_association_perimeter.py` nei
controlli sul catalogo effettivo, metodo `A7_ASSOCIATION_PERIMETER.md`.
Nessun rollout: il divieto `public=True, associations=True` resta invariato.
Prossimo passo, da approvare: rollout pubblico del solo piano rivisto.

## Main verificata il 24 ottobre 2026 — #476 integrata e pubblicata

Merge del proprietario `d5c8fc2870869a23b3fe0640428e682931503655`, albero
`4c1c060d5328b5b17ebf1164bd56f7ce12582473`, identico alla head #476
`cb5af9084f9435f695d96be4bf308c571f552d52`. Nessun merge/deploy dell’assistente.
Pubblicazione: Pages push `40092635164` (#4238) SUCCESS, reporter live
`40094663950` SUCCESS. Questa verifica legge soltanto gli esiti pubblici dei run:
log, job Quick→Full della PR e A3 non sono stati riletti in questa sessione e
non vengono attestati qui. L’anteprima degli incroci resta opt-in e isolata.

Prossimo incremento A7.5.4: misura e revisione del perimetro preparato degli
incroci prima di qualunque rollout pubblico. La misura richiede la build
pubblica completa (`public_dist_required`) e quindi Chromium: va eseguita con
Quick/Full locali ordinari, non stimata. Restano invariati i divieti
`public=True, associations=True`, whitelist di domande e coppie scelte dal
coefficiente.

## Main precedente — #474 integrata e pubblicata

Merge del proprietario `c5386a38f4a5c490b0e10e0bfa1ca50d20c77a1c`, albero
`7a2afdac9b425cf6b52686325a3a226ae1510a1b`, identico alla head #474
`7c766b417215da9a41deb6aa157e12ffbe8425be`. Nessun merge/deploy dell’assistente.
CI Quick→Full effettivo nello stesso run `40032825527`, job `120685009917`
e `120698490944`, SUCCESS; A3 `40032825514`, job `120685007265`, SUCCESS.
Checkout effettivo `6d24726c` con il medesimo albero. Quick e Full locali
ordinari eseguiti PASS; il Full termina il 23 ottobre alle 23:34 UTC.
La conservazione del suo log è incompleta: ricevuta e rapporti disponibili,
quattro log completi su cinque. Non è un’attestazione archivistica completa;
limite e tentativi distinti nella #474, senza trasferimento di verdi.
Evidenze #474 `A7_EXPLICIT_ASSOCIATIONS_e6d52b0_evidenze.zip`, SHA256
`958c9cfeb9f8e706b92db512c7b80eb39cf39aceed345e99230ce64cdb2324c9`.

Pubblicazione verificata separatamente: Pages push `40070233147`, build
`120801890630` e deploy `120806424596` SUCCESS. Reporter `40071753266`, job
`120806501424` SUCCESS; checkout effettivo del merge nei log build/live.
Integrità Chiedi asset/hash, `ov-public-routes` e `ov-pages-live` PASS;
log live SHA256 `b9e998ad7e2d6a69e02c03cb5dbca3e34ed5044b2a65d537ce8b0200b7e26cec`.
Quick/Full skipped del push non sono nuovi gate. Il reporter è un campione
live di disponibilità/integrità, non certifica tutte le richieste numeriche.

A6 DONE: 225/225 adapter, 3.727 casi indipendenti, 35 letture e due riepiloghi,
Atlante 20.325 unità locali native, 40 golden e Camaiore congelata. A7
IN_PROGRESS. La #473 espone la tendenza nativa; la #474 integra il trasporto
opzionale dei piani di associazione, senza abilitarli nella build pubblica.
Ultima misura approvata dei profili pubblici: 50.523 richieste,
28.422 computed / 22.101 rifiuti, 127.146.205 byte gzip. Misura di trasporto,
non nuovi casi numerici indipendenti. Nessuna promozione in navigazione.

## Incremento integrato con la #476 — anteprima degli incroci guidati

Branch `feature/a7-guided-pair-selection`, base main #474. A7.5.4 resta aperta.
`build_a7_explorer_preview.py --associations` aggiunge nella stessa pagina due
variabili, asse, metodo, motivo/copertura, risultato e coppie originali A6.
Selezioni derivate dal piano ancorato, nomi/unità dal catalogo canonico:
nessuna whitelist di domande o coppia scelta dal coefficiente. Il grafico
proietta soltanto le coppie native; tabelle e fonti conservano periodi e unità.
Nessun coefficiente sostitutivo nei rifiuti, consenso esplicito e revoca dei
risultati superati durante il fetch. Metodo `A7_GUIDED_ASSOCIATION_PREVIEW.md`.

È un’opzione isolata: `public=True, associations=True` è vietato. Default,
materializzatore pubblico e interfaccia v6 restano invariati; soltanto questa
anteprima usa v7 e i due nuovi asset. Prima del rollout restano misura e
revisione del perimetro preparato. Non è interrogabilità universale né un
ampliamento automatico del runtime. Il motivo non viene riscritto: una modifica
richiede un’altra richiesta esatta e la sua materializzazione originale A6.

Il gate di trasporto esistente verifica anche la UI sulla shell canonica,
1440/390/320 px, parità nativa, selettori invertiti, rifiuto temporale A6,
testo ostile, consenso, cache, guasti/ripresa e selezione superata. Gli otto
casi originali del lettore conservano il proprio budget; tredici casi UI in
runtime separato, comprese omissioni di asse/metodo in gruppi sparsi e
allineamento delle coppie agli estremi etichettati delle scale; grafico
leggibile su colonne strette con scorrimento da tastiera e caratteri effettivi
controllati dopo la scala SVG. La prova preliminare del componente non certifica la pagina
completa. Preview reale, Quick/Full locali ordinari e CI Quick→Full/A3 richiesti
sul nuovo candidato; nessun verde della #474 trasferito. Evidenze nella PR.

Restano incroci pubblici, perimetro generale, riuso/CSV/PDF e consolidamento.
Dossier e Radar separati; nessuna acquisizione, modifica di adapter/dati/golden,
modello esterno, backend o costo ricorrente. Merge e deploy restano del proprietario.
