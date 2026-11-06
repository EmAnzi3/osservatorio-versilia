# Consolidamento Osservatorio Versilia — handoff operativo

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
