# A3.2 — Residual Closure Audit post-#223

## Scopo

Audit diagnostico delle **351 coppie indicatore × dimensione** rimaste non classificate dopo il Full della PR #223.

Baseline verificata:
- catalogo pubblico: **225 indicatori**
- matrice: **2.025 coppie**
- classificate: **1.674**
- residue: **351**
- Full #223: run `35241061878`, job `105271718007`
- main post-merge #223: `474462da3227077a2a6948e218d50c30d10c409f`

Questo audit **non modifica** `data/site-data.json`, `data/source-registry.json`, le evidenze A3.2 o lo stato finale di alcuna coppia. Assegna soltanto una *closure route* diagnostica.

## Quattro contenitori

| Bucket | Significato | Coppie | % residuo |
|---|---|---:|---:|
| A | Falso residuo strutturale: dato già materializzato ma detector incompleto | 22 | 6,3% |
| B | Cross-source / companion metric: chiusura richiede contratto esplicito tra fonti/metriche | 20 | 5,7% |
| C | Semanticamente N/A ad alta confidenza: candidato `NOT_APPLICABLE` metric-specific | 37 | 10,5% |
| D | Vera verifica fonte: decidere `AVAILABLE_MISSING` vs `SOURCE_UNAVAILABLE` su fonte ufficiale | 272 | 77,5% |

**Risultato operativo:** 79 coppie (**22,5%**) possono essere instradate senza una nuova ricerca fonte-per-fonte. Le restanti 272 richiedono audit della fonte ufficiale.

## Distribuzione per dimensione

| Dimensione | A | B | C | D | Totale |
|---|---:|---:|---:|---:|---:|
| `serie_storica` | 3 | 0 | 0 | 24 | 27 |
| `sesso` | 0 | 0 | 10 | 25 | 35 |
| `eta` | 0 | 7 | 10 | 39 | 56 |
| `dettaglio_territoriale` | 2 | 0 | 0 | 4 | 6 |
| `benchmark_toscana_italia` | 1 | 0 | 0 | 6 | 7 |
| `assoluto_normalizzato` | 4 | 6 | 10 | 63 | 83 |
| `frequenza_infra_annuale` | 0 | 0 | 0 | 45 | 45 |
| `numeratore_denominatore` | 7 | 7 | 7 | 31 | 52 |
| `categorie_specifiche` | 5 | 0 | 0 | 35 | 40 |

## A — falsi residui strutturali

Entrano in A soltanto coppie per cui il dato è già nel payload pubblico verificato o nella route speciale canonica associata alla stessa metrica, ma il detector non riconosce la forma.

Casi principali:
- `landCoverProfile`: serie 2007–2019, ettari + quote %, categorie UCS;
- `economyActivityAtlas`: storico, dettaglio comunale, riferimento Toscana e tassonomia ATECO nella route speciale;
- `voterTurnout`: archivio storico, dettaglio comunale, votanti/elettori e tipologia di consultazione nella route speciale;
- `foreignResidents`: `count` + `population` già nelle righe;
- `taxpayersAdultPopulationRate`: `taxpayers` + `adultPopulation2026`;
- `municipalEmployeesPer1000`: `staffAt31Dec` + `residentPopulation`;
- `municipalStaffTurnover`: componenti assunzioni/cessazioni/headcount;
- `earlyChildhoodPotentialCapacityRate`: `potentialCapacity` + `children3to36Months`;
- `forestCoverIndex`: `forestAreaHa`, `municipalityAreaHa`, `forestCoverPct`;
- `landUse` e `managedReticulumLength`: categorie già nei `parts`.

**Chiusura:** detector-only, con regressioni positive e negative. Nessuna annotazione manuale; le coppie devono emergere automaticamente come `ACQUIRED`.

## B — cross-source / companion

La misura pubblicata necessita di un'altra metrica o di una seconda fonte governata per completare la dimensione.

Casi principali:
- età per `population`, `populationChange`, `naturalDemographicDynamics`, mobilità residenziale e residenti stranieri: la scomposizione vive in dataset/metriche companion demografiche;
- `evPoints`, `publicWorks`, `roadFinesPerResident`, `tourismBedsPer1000`, `tourismStructuresPer1000`, `tourismIntensity`, `pharmaciesPer1000`: numeratore dalla fonte tematica, denominatore demografico da altra fonte governata;
- `protectedNaturalAreas`: la normalizzazione richiede una base territoriale distinta.

**Chiusura:** definire un contratto cross-source/companion riusabile con lineage esplicita. Non usare `NOT_APPLICABLE` e non dichiarare la dimensione assente guardando soltanto la fonte primaria.

## C — semanticamente N/A

Solo casi ad alta confidenza in cui la dimensione non descrive l'oggetto della metrica o non esiste un equivalente semanticamente coerente.

Esempi:
- sesso/età su misure puramente fisiche, territoriali o finanziarie come copertura forestale, uso del suolo, cave, opere/stock e pagamenti;
- `numeratore_denominatore` per importi SIOPE e altre misure dirette non definite come rapporto;
- `assoluto_normalizzato` per aliquote/tariffe standard e trend climatici dove non esiste un equivalente “assoluto” omologo;
- sesso/età su superfici agricole, dimensione media aziendale e profili colturali quando la metrica misura superficie/composizione, non persone.

**Chiusura:** revisione metric-specific e `NOT_APPLICABLE`. Nessuna regola N/A a livello source profile.

## D — vera verifica della fonte

Le altre **272 coppie** non vengono forzate. Il payload corrente non basta a stabilire se la dimensione sia disponibile ma non acquisita oppure assente dalla fonte.

Profili prioritari per numero di coppie D:

| Source profile | D |
|---|---:|
| `ars-toscana-mixed` | 64 |
| `regione-toscana-indicatori-comunali` | 35 |
| `istat-demography-annual` | 32 |
| `istat-commuting-irregular` | 11 |
| `istat-business-annual` | 10 |
| `regione-toscana-biblioteche-annual` | 9 |
| `cb1-pmo-status-2026` | 8 |
| `istat-tourism-annual` | 8 |
| `istat-road-annual` | 7 |
| `mef-istat-real-income-annual` | 7 |
| `erp-lucca-annual-balance-sheet` | 6 |
| `regione-toscana-tourism-annual` | 5 |
| `rgs-conto-annuale-annual` | 5 |
| `mim-school-year` | 5 |
| `dait-eligendo-irregular` | 5 |
| `percorsi-curated` | 5 |

Per ogni coppia D:
1. verificare la fonte ufficiale e l'esatta metrica;
2. se la dimensione è pubblicata in modo compatibile → `AVAILABLE_MISSING`;
3. se la fonte ufficiale non pubblica la dimensione compatibile → `SOURCE_UNAVAILABLE`;
4. se emerge dato già materializzato o dipendenza companion/cross-source → spostare in A/B, senza annotazione artificiale;
5. `NOT_APPLICABLE` soltanto se la verifica semantica lo dimostra per la singola metrica.

## Ordine di chiusura

1. **A — detector closure:** 22 coppie.
2. **B — cross-source contract:** 20 coppie.
3. **C — semantic closure:** 37 coppie.
4. **D — source evidence:** 272 coppie, iniziando da ARS Toscana, indicatori comunali Toscana e demografia Istat.

Questo ordine elimina prima la coda artificiale e semantica e concentra poi la ricerca solo sulle coppie che dipendono davvero dalla fonte.

## Vincoli invariati

- nessun `ACQUIRED` manuale;
- nessun secondo catalogo manuale;
- `AVAILABLE_MISSING` / `SOURCE_UNAVAILABLE` solo con evidenza ufficiale verificabile;
- `NOT_APPLICABLE` solo metric-specific;
- A3.2 chiusa soltanto con `unclassifiedPairCount = 0`;
- nessun passaggio ad A3.3 prima dello zero.
