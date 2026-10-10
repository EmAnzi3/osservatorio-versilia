# Osservatorio Versilia — roadmap di consolidamento

Questa roadmap governa il lavoro di consolidamento dell'Osservatorio dopo la fase di forte espansione del catalogo dati.

## Obiettivo

Portare il progetto da raccolta ricca di indicatori a prodotto dati governato, verificabile, coerente e interrogabile.

Il principio guida è:

> ogni dato pubblicato deve essere derivabile dalle fonti canoniche, censito, monitorato, documentato, verificato e rappresentato secondo contratti comuni.

## Regole di tracking

- Ogni workstream ha un ID stabile (`A0`, `A1`, ...).
- Gli step usano ID gerarchici (`A1.1`, `A1.2`, ...).
- Stati ammessi: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `DONE`.
- `docs/CONSOLIDATION_HANDOFF.md` contiene esclusivamente lo stato operativo corrente e deve essere aggiornato in ogni PR che avanza questa roadmap.
- La cronologia resta in Git e nelle PR: non si mantiene un secondo diario append-only.
- Una nuova chat/sessione deve leggere prima `AGENTS.md`, questa roadmap e `docs/CONSOLIDATION_HANDOFF.md`.
- Nessun workstream può indebolire i contratti esistenti per far passare una modifica.
- `data/site-data.json` resta la fonte canonica del catalogo. Non va introdotto un secondo inventario canonico parallelo.

## Baseline iniziale

- Data di avvio consolidamento: 2026-09-14
- Baseline `main`: `f7c132eb5262ff2fcf028bfb3c5fecb339c95e2f`
- Catalogo dichiarato dalla baseline: 225 indicatori
- Evidenza già emersa: conteggi e stato del progetto possono divergere tra README, sito/Stato dati e output materializzati; il consolidamento deve eliminare strutturalmente queste divergenze.

---

## A0 — Governance del programma e handoff

**Stato:** `DONE`

Scopo: rendere il lavoro multi-sessione ripetibile e trasferibile senza dipendere dalla memoria della chat.

- [x] **A0.1** Definire roadmap con ID e stati stabili.
- [x] **A0.2** Introdurre handoff operativo breve e aggiornabile.
- [x] **A0.3** Rendere obbligatoria la lettura di roadmap/handoff per le sessioni di consolidamento tramite `AGENTS.md`.
- [x] **A0.4** Aprire PR di fondazione e registrarla nell'handoff.
- [x] **A0.5** Merge solo dopo approvazione esplicita del proprietario.

**Definition of done:** una nuova sessione può capire in pochi minuti cosa è stato completato, cosa è in corso, cosa resta da fare e quale sia la prossima azione esatta.

---

## A1 — Data Governance Foundation

**Stato:** `DONE`

Scopo: eliminare le molteplici “verità” sullo stato del progetto senza duplicare il catalogo canonico.

- [x] **A1.1** Audit del percorso canonico `site-data.json` → materializzatori → output pubblicato; documentare esattamente quali trasformazioni possono modificare/arricchire il catalogo visibile.
- [x] **A1.2** Definire una vista derivata e riproducibile del catalogo effettivamente pubblicato, senza introdurre un nuovo inventario canonico.
- [x] **A1.3** Introdurre invarianti automatiche sugli ID: `pubblicati = censiti = monitorati = rappresentati nello Stato dati`, salvo eccezioni dichiarate e motivate.
- [x] **A1.4** Generare automaticamente i blocchi di stato del README a partire dalle fonti canoniche/derivate.
- [x] **A1.5** Generare automaticamente lo Stato dati dalla stessa pipeline di verità.
- [x] **A1.6** Riconciliare versioni, conteggi, date di aggiornamento e copertura tra README, homepage, Stato dati e pipeline.
- [x] **A1.7** Inserire i gate nel preflight generale, evitando test release-specifici.
- [x] **A1.8** Documentare data lineage minimo: fonte → acquisizione/raw → trasformazione/materializzatore → indicatore → visualizzazione.

Nota A1.3: in questo workstream “monitorati” significa che ogni ID pubblicato risolve una policy fonte strutturalmente valida. Freschezza, ultimo controllo riuscito e copertura operativa del monitor sono responsabilità di `A2`.

Nota chiusura A1: la PR `#193` è stata mergiata su `main` dopo Quick e Full GitHub verdi. Il deploy Pages post-merge `#3219` e il successivo controllo live-status sono verdi. La release pubblica è governata sul perimetro di 225 indicatori.

**Definition of done:** non è possibile pubblicare o materializzare un indicatore senza che documentazione, Stato dati e controlli di copertura ne conoscano lo stesso ID.

---

## A2 — Full Coverage Source Monitor

**Stato:** `DONE`

Scopo: avere prova periodica che tutti gli indicatori pubblicati siano controllati per aggiornamenti delle rispettive fonti.

- [x] **A2.1** Audit della copertura reale dell'attuale source registry/monitor rispetto al catalogo effettivamente pubblicato.
- [x] **A2.2** Eliminare conteggi attesi hard-coded quando derivabili dal catalogo canonico.
- [x] **A2.3** Separare controllo leggero frequente e controllo profondo periodico.
- [x] **A2.4** Definire per ogni fonte frequenza attesa, modalità di rilevazione cambiamenti e ultimo controllo riuscito.
- [x] **A2.5** Produrre report leggibile con almeno: coperti/totali, aggiornamenti disponibili, nuove release, fonti irraggiungibili, cambi di schema, dati invariati.
- [x] **A2.6** Rendere evidente l'esito tramite GitHub Actions/issue o altro canale già coerente con l'architettura della repo.
- [x] **A2.7** Fallire chiaramente se esistono indicatori pubblicati privi di monitoraggio applicabile.

Nota A2.1: l'audit è documentato in `docs/A2_SOURCE_MONITOR_AUDIT.md`. Il workflow mensile usava il catalogo sorgente e un registry con conteggi attesi `181/177/4`, mentre l'Effective Public Catalog contiene 225 indicatori.

Nota A2.2: `materialize_source_monitor_snapshot.py` riusa la stessa catena di materializzazione della release e si arresta prima del prerender. Il monitor opera così sul catalogo pubblico derivato: la verifica GitHub ha restituito `225` indicatori, `122` fonti, `0` errori strutturali. Nessuna nuova costante `225` è stata introdotta come fonte di verità.

Nota A2.3: il controllo profondo resta mensile e conserva hash/verifiche semantiche; `source-monitor-light.yml` introduce un controllo frequente read-only sullo stesso perimetro pubblico, senza hash dei contenuti né verifiche semantiche PNRR/MIMIT. Il workflow light non modifica baseline, issue o PR e produce un artifact diagnostico separato.

Nota chiusura A2: la PR `#194` ha implementato A2.4–A2.7 e ha chiuso il perimetro operativo a 225 indicatori / 122 fonti con Quick, Full, monitor light e deep verdi. I successivi interventi di hardening sulla pipeline di refresh hanno preservato questi contratti e rimosso regressioni legacy senza introdurre un secondo inventario canonico.

**Definition of done:** ogni indicatore pubblicato ha una strategia di monitoraggio verificabile oppure un'eccezione esplicita; ogni run produce un responso comprensibile.

---

## A3 — Enrichment Audit globale

**Stato:** `DONE`

Scopo: verificare sistematicamente se stiamo sfruttando tutto ciò che le fonti offrono, invece di scoprire gli arricchimenti per caso.

- [x] **A3.1** Definire le dimensioni comuni di enrichment: serie storica, sesso, età, dettaglio territoriale, benchmark Toscana/Italia, assoluto/normalizzato, frequenza infra-annuale, numeratore/denominatore, categorie specifiche.
- [x] **A3.2** Classificare ogni coppia indicatore/dimensione come `ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`.
- [x] **A3.3** Eseguire audit fonte per fonte sul catalogo completo.
- [x] **A3.4** Trasformare `AVAILABLE_MISSING` in backlog ordinato per valore informativo e costo di acquisizione.
- [x] **A3.5** Integrare nuove dimensioni in lotti controllati con QA e fonte dichiarata.
- [x] **A3.6** Introdurre un indicatore interno di copertura enrichment, derivato e non autocelebrativo.

Nota perimetro benchmark — 03-10-2026: il proprietario limita questa fase ai valori Toscana/Italia ufficiali direttamente fruibili e agli storici già disponibili. Le ricostruzioni di pannelli territoriali, il recupero oneroso di fotografie storiche e il calcolo di aggregati mancanti non rientrano nel lavoro residuo. La fase può concludersi con confronti mancanti esplicitamente documentati: le coppie mantengono la classificazione reale della matrice e non diventano ACQUIRED o SOURCE_UNAVAILABLE per una scelta di priorità. Il residual audit continua a descrivere la copertura completa delle fonti; il suo closureReady=false non richiede ulteriori acquisizioni fuori da questo perimetro. Approvazione e merge restano necessari per la chiusura formale.

Nota A3.1: la tassonomia e la semantica dei quattro stati sono definite in `docs/A3_ENRICHMENT_AUDIT.md`. Il documento è metodologico e non introduce un secondo catalogo o una matrice manuale di indicatori.

Nota A3.2: la chiusura è governata dalla matrice strict derivata dall'Effective Public Catalog: 225 indicatori × 9 dimensioni = 2.025 coppie, con `unclassifiedPairCount = 0`. Il gate A3 verifica inoltre le evidenze strutturali e tutte le classificazioni esplicite; nessun `ACQUIRED` è dichiarato manualmente.

Nota A3.3: l'audit fonte-per-fonte è derivato dalla matrice A3 strict e dal source registry. Il gate verifica tutti i source profile effettivamente usati dal catalogo, la copertura esatta metriche × 9 dimensioni, i metadati operativi della fonte e i conteggi per stato; produce artifact JSON/Markdown senza introdurre un inventario canonico parallelo.

Nota A3.4: il backlog è derivato da tutte le coppie `AVAILABLE_MISSING` e le raggruppa in pacchetti `sourceProfileId × dimensione`. L'ordinamento usa una policy esplicita e versionata di valore informativo e un proxy di costo 1..5 basato su riuso della stessa dimensione, livello dell'evidenza e frammentazione dei riferimenti fonte. Il gate verifica copertura 1:1 delle opportunità e pubblica artifact JSON/Markdown; nessun dato viene ancora acquisito.

Nota A3.5 — lotto 1: la prima acquisizione controllata integra la dimensione `sesso` per `population`, `dependencyIndices` e `foreignResidents` riusando esclusivamente snapshot Istat POSAS/RCS già versionati e governati. Il materializzatore riconcilia 7/7 Comuni e aggregato Versilia, ricalcola gli indici di dipendenza per sesso e dichiara anno/unità/fonte nel nuovo `sexDimension`. Le tre coppie passano da `AVAILABLE_MISSING` a `ACQUIRED` per evidenza strutturale; A3.5 resta `IN_PROGRESS` dopo questo lotto.

Nota A3.5 — lotto 2: il backlog A3.4 post-#260 contiene 869 coppie `AVAILABLE_MISSING`. Il lotto acquisisce 16 coppie del pacchetto `openbdap-annual × numeratore_denominatore`, scelto dalla graduatoria governata dopo aver verificato la disponibilità reale dei componenti. Per 14 indicatori di rendiconto usa esclusivamente `data/source-snapshots/bilanci-v1.6.0.json`; per `cashReceiptsPerResident` e `cashBalancePerResident` usa `data/source-snapshots/siope-history-v1.6.0.json`. Ogni riga comunale espone `ratioComponents` con numeratore, denominatore, scala, anno, fonte e snapshot, e il QA riconcilia la formula con il valore già pubblicato. Le altre 8 coppie dello stesso pacchetto restano `AVAILABLE_MISSING` perché gli snapshot correnti non congelano entrambi i componenti necessari: nessuna retro-derivazione dal rapporto pubblicato è ammessa. Effetto atteso del lotto: 869 → 853 `AVAILABLE_MISSING`; A3.5 resta `IN_PROGRESS`.

Nota A3.5 — lotto 3: dal backlog A3.4 post-#261 di 853 coppie `AVAILABLE_MISSING` viene integrato un lotto coerente sul profilo `istat-business-annual`, riusando esclusivamente gli snapshot Frame SBS Territoriale Istat v1.34.0 già versionati. Per gli 8 indicatori di Economia prodotta il lotto acquisisce 8 coppie `categorie_specifiche` tramite i perimetri `Totale / Industria / Servizi`, 8 coppie `assoluto_normalizzato` tramite componenti economiche/occupazionali coerenti e 4 coppie `numeratore_denominatore` per produttività, fatturato per addetto, valore aggiunto sul fatturato e retribuzione media per dipendente. Il QA riconcilia le formule con i valori pubblici e ammette soltanto tolleranze motivate dall'arrotondamento delle tavole Istat; nessun nuovo numero esterno o benchmark viene introdotto. Effetto atteso: 853 → 833 `AVAILABLE_MISSING`; A3.5 resta `IN_PROGRESS`.

Nota A3.5 — lotto 4: dal backlog A3.4 post-#262 di 833 coppie AVAILABLE_MISSING vengono riusati esclusivamente i componenti grezzi 2023 già congelati nello snapshot Istat delle sezioni di censimento v1.8.0. Per femaleEmploymentRate, maleEmploymentRate, housingStockPer1000, nonOccupiedHomesPer1000, vacantHomes e singleHouseholds il lotto espone numeratore e denominatore verificabili, riconcilia le formule con i valori pubblici e acquisisce 6 coppie numeratore_denominatore + 6 coppie assoluto_normalizzato. Nessun valore pubblico, benchmark o elemento UI viene modificato. Effetto atteso: 833 → 821 AVAILABLE_MISSING; A3.5 resta IN_PROGRESS.

Nota A3.5 — lotto 5: dal backlog post-lotto 4 di 821 coppie `AVAILABLE_MISSING` viene integrato un lotto esclusivamente strutturale, senza nuovi valori pubblici. Il lotto riusa i `ratioComponents` OpenBDAP già acquisiti nel lotto 2 per esporre 16 companion assoluto/normalizzato; usa componenti Istat già versionati per `cohabitingHouseholds`, `oldAgeIndex`, tre indicatori agricoli e cinque indicatori business, dopo riconciliazione formula-per-formula sui 7 Comuni. Per `localEmployeesChange` e `localUnitsChange` il companion assoluto è la variazione in unità 2023−2018, mentre i livelli 2023 e 2018 restano rispettivamente numeratore e denominatore della formula percentuale. `householdSize` resta escluso perché i componenti candidati non riconciliano abbastanza precisamente il valore ufficiale pubblicato. Totale: 34 nuove coppie strutturalmente `ACQUIRED`; effetto atteso 821 → 787 `AVAILABLE_MISSING`. Nessun campo aggiunto dal lotto è consumato dal renderer; A3.5 resta `IN_PROGRESS`.

Nota A3.5 — lotto 6: dal backlog post-#264 di 787 coppie `AVAILABLE_MISSING` vengono materializzate esclusivamente strutture già ricostruibili dagli snapshot versionati: 6 serie storiche (`industryValueAddedShare`, `industryWorkerShare`, `localEmployeesChange`, `localUnitsChange`, `populationChange`, `rigidExpenditureShare`), 2 breakdown industria/servizi Frame SBS e 5 companion MEF per `incomeSourceProfile`, `pensionIncomeShare` e `municipalIrpef`. Le serie di variazione ASIA restano ancorate alla baseline 2018; `populationChange` alla baseline 2019. `cohabitingHouseholds` e `householdSize` restano esclusi dallo storico perché gli snapshot disponibili non consentono una riconciliazione 7/7 omogenea. Totale: 13 nuove coppie strutturalmente `ACQUIRED`; effetto atteso 787 → 774 `AVAILABLE_MISSING`. Nessun valore pubblico o renderer viene modificato; A3.5 resta `IN_PROGRESS`.

Nota A3.5 — lotto 7: dal backlog post-#265 di 774 coppie `AVAILABLE_MISSING` vengono acquisite 7 serie storiche del profilo `ars-toscana-mixed` per `chronicTotal`, `dementia`, `diabetes`, `elderlyHomeCare`, `emergencyAccess`, `hospitalizedAll` e `mortalityAll`. I numeri derivano dagli export ZIP/CSV ufficiali ARS, vengono congelati nello snapshot `data/source-snapshots/ars-a3-5-legacy-history.json` con SHA-256 del file sorgente e riconciliati 7/7 con il valore pubblico corrente e con l'aggregato ufficiale Zona Versilia. Le serie comprendono da 9 a 16 periodi; per `mortalityAll` la fonte espone già 2014–2023, ma il catalogo pubblico resta 2013–2022 e il lotto congela la serie soltanto fino a quel periodo, senza anticipare il normale refresh del dato. Totale: 7 nuove coppie strutturalmente `ACQUIRED`; effetto atteso 774 → 767 `AVAILABLE_MISSING`. Nessun valore, testo o renderer pubblico viene modificato; A3.5 resta `IN_PROGRESS`.

Nota A3.5 — lotto 8: dal backlog post-#266 di 767 coppie `AVAILABLE_MISSING` viene integrato un lotto esclusivamente strutturale da numeri ufficiali già versionati. Il lotto acquisisce 8 coppie Istat lavoro (`sesso`, `eta` e categorie occupati/in cerca/inattivi dove semanticamente applicabili) usando il dettaglio 2024, senza alterare le serie pubbliche 2023; 4 coppie MIM per `studentsPerClass` e `primaryFullTimeShare`, esponendo numeratore/denominatore e companion assoluto/normalizzato direttamente dai conteggi 2024/25 già congelati; 3 coppie RGS su turnover del personale e formazione per sesso. Il candidato AGCOM viene escluso dal lotto perché per Forte dei Marmi il CSV ufficiale espone percentuali ma non i conteggi assoluti FTTH: in coerenza con la policy della repository nessun conteggio viene retro-derivato. Totale atteso: 15 nuove coppie strutturalmente `ACQUIRED`; effetto atteso 767 → 752 `AVAILABLE_MISSING`. Nessun valore, testo o renderer pubblico viene modificato; A3.5 resta `IN_PROGRESS`.

Nota chiusura A3.5: il consolidamento non richiede l'azzeramento del backlog `AVAILABLE_MISSING`. Otto lotti controllati (#260–#267) hanno dimostrato end-to-end il percorso `AVAILABLE_MISSING → ACQUIRED` su più famiglie di fonte e dimensioni, con 120 nuove coppie strutturalmente acquisite e nessun override manuale `ACQUIRED`. Il residuo passa da 872 a 752 coppie e resta integralmente nel backlog A3.4 come roadmap di espansione dati futura, senza essere riclassificato artificialmente.

Nota A3.6: `scripts/enrichment_coverage.py` deriva dalla matrice strict la copertura `ACQUIRED / (ACQUIRED + AVAILABLE_MISSING)`, globale, per dimensione e per source profile, ed esclude dal denominatore `SOURCE_UNAVAILABLE` e `NOT_APPLICABLE`. La baseline post-#267 è 544 / 1.296 opportunità acquisibili = 42,0%, con 752 opportunità residue. Il valore è diagnostico e non costituisce un punteggio di qualità né un target implicito del 100%.

Nota chiusura A3: tassonomia, matrice strict, audit fonte-per-fonte, backlog prioritizzato, percorso di acquisizione controllato e copertura enrichment sono tutti derivati dalle fonti canoniche e verificati automaticamente. Le future acquisizioni del backlog A3.4 sono miglioramenti di prodotto e non riaprono il workstream salvo modifica della metodologia o dei contratti.

Nota pubblicazione A3 — 04-10-2026: i lotti disponibili e approvati sono stati incorporati nella #322 e pubblicati; i successivi #327/#328 aggiornano fonti e MIMIT. Il checkpoint corrente espone 225 indicatori, 124 storici e 137 confronti verificati dal Quick. Il backlog oneroso resta escluso dal perimetro autorizzato, con classificazioni reali conservate. Le vecchie PR stacked sono state archiviate; non rappresentano lavori ancora da mergiare.

**Definition of done:** per ogni indicatore sappiamo quali dimensioni la fonte rende disponibili, quali abbiamo acquisito e quali mancano ancora.

---

## A4 — Visualization & Content Contract

**Stato:** `DONE`

Scopo: trasformare le attuali regole di coerenza da linee guida distribuite a invarianti globali testabili.

- [x] **A4.1** Consolidare le regole esistenti di UI, scale, tooltip, unità, medie, benchmark e dati mancanti.
- [x] **A4.2** Definire metadati/contratti derivabili che evitino duplicazioni per unità, precisione, semantica colore e formato tooltip.
- [x] **A4.3** Testare coerenza tra dato, testo, asse, tooltip, legenda e unità.
- [x] **A4.4** Testare esplicitamente media semplice vs ponderata e denominatori quando applicabili.
- [x] **A4.5** Introdurre visual regression su un campione rappresentativo per famiglia di grafici/temi, non screenshot indiscriminati dell'intero sito.
- [x] **A4.6** Portare i nuovi gate nel preflight generale.

Nota A4.1–A4.2: `docs/A4_VISUALIZATION_CONTENT_CONTRACT.md` consolida le regole già operative per unità/precisione, scale, confronti, benchmark, dati mancanti, polarità e tooltip. `ci/visualization-content-contract.json` ne definisce il vocabolario machine-readable senza enumerare indicatori; `scripts/visualization_content_contract.py` lo valida sia sul catalogo sorgente sia sull'Effective Public Catalog dopo la build. Baseline effettiva post-#268: 225 indicatori, 1.547 righe, 84 riferimenti aggregati espliciti, 141 fallback alla media semplice, 22 righe `n.d.` e 24 `n.a.`. A4 resta `IN_PROGRESS`: A4.3–A4.4 devono verificare semantica e aggregazioni prima della visual regression.

Nota A4.3–A4.4: il contratto governa ora anche unità di parti composite/normalizzate, coerenza formatter/tooltip/accessibilità e aggregazioni con `ratioComponents`. Il gate ricostruisce 16 rapporti ponderati (112 righe comunali) come `sum(numeratore) / sum(denominatore) × scala`, verifica denominatori e aggregato territoriale e richiede il riferimento esplicito all'aggregato. L'audit ha corretto tre casi OpenBDAP (`ownRevenueShare`, `currentCollectionCapacity`, `currentPaymentCapacity`) che avevano già l'aggregato ponderato corretto ma il renderer usava ancora la media semplice. Baseline attesa: 87 riferimenti aggregati espliciti e 138 fallback.

Nota A4.5–A4.6: la PR #271 introduce un gate di regressione visuale rappresentativo derivato dall'Effective Public Catalog. Il bootstrap copre 40 superfici: 11 temi, 3 famiglie generiche, 22 `compositeType`, 2 varianti storiche e 2 stati comunali. Le baseline sono fingerprint compatti versionati; gli screenshot vengono prodotti soltanto come diagnostica. Il gate è Full-only nel preflight generale e il workflow Pages pubblica l'artifact diagnostico anche quando il confronto fallisce. Nessuna modifica UI pubblica è introdotta. La chiusura di A4 diventa effettiva su `main` con il merge esplicito di #271 dopo Quick e Full verdi.

**Definition of done:** una regressione semantica o visiva rilevante viene intercettata prima del merge senza affidarsi soltanto al controllo manuale.

---

## A5 — Design System 2.0

**Stato:** `DONE`

Scopo: migliorare gerarchia e leggibilità riducendo la predominanza del beige senza perdere l'identità del progetto.

- [x] **A5.1** Audit quantitativo/visivo di superfici, contrasto, densità e gerarchia.
- [x] **A5.2** Definire ruoli cromatici: canvas neutro, superfici analitiche chiare, colore tematico usato come informazione.
- [x] **A5.3** Definire token comuni per background, card, bordi, testo, stati e temi.
- [x] **A5.4** Applicare il nuovo sistema a una pagina pilota e verificarlo desktop/mobile.

Nota chiusura A5.4: il golden master tematico `confronta/demografia/` e il golden master comunale sono stati consolidati nella PR #280. Viareggio/Demografia è stato approvato visivamente su desktop/mobile; Massarosa è stata poi portata sullo stesso shell e sulle stesse famiglie grafiche come prova di generalizzazione, senza clone/fetch prototipali né hard-code strutturali su Viareggio. Il gate browser verifica 10/10 indicatori Demografia su entrambi i Comuni, famiglie grafiche, tooltip/riferimenti, controlli condivisi, KPI/label, benchmark, Metodo/Scala e responsive 768/390 px. Il commit di chiusura A5.4 è `7eadda666118f2450290a3b1c6edb93f061b7c7b`; Quick e release gate pertinenti sono verdi. A5.5 è stato successivamente avviato e completato nella stessa PR con rollout controllato e golden lock dedicati.
- [x] **A5.5** Estendere progressivamente senza modifiche massive non verificabili.

Nota A5.5 — lotto 1 DONE: `confronta/economia/` usa lo shell A5 parametrico; geometria, accenti, desktop/mobile e 7/7 card comunali sono stati verificati automaticamente e il lotto è stato approvato visivamente. L’Atlante attività economiche e le schede comunali Economia sono rimasti fuori dal lotto.

Nota A5.5 — lotto 2 DONE: `confronta/lavoro/` usa lo shell A5 condiviso; tutti gli indicatori Lavoro, incluse le superfici età/sesso, hanno superato i gate desktop/mobile e il lotto è stato approvato visivamente.

Nota A5.5 — bulk tematico DONE: il rollout DS2 è stato esteso a tutti gli 11 temi standard delle route `confronta/<tema>/`. Il gate attraversa tutti gli indicatori tramite i controlli reali della sidebar e verifica shell, geometria, accento, chart non vuoto, overflow e superfici speciali a 1440 px e 390 px.

Nota A5.5 — rollout comunale DONE: lo standard parametrico è esteso alle 7 schede comunali sui temi applicabili. Camaiore resta congelata al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; Viareggio/Massarosa Demografia restano protette dal golden lock storico. Il cohort municipale verifica valori, unità, scale, toolbar, storico, benchmark, ordine dei contenuti, overflow e responsive. La navigazione dei Comuni e la sezione Home “Esplora per territorio” sono ordinate alfabeticamente: Camaiore, Forte dei Marmi, Massarosa, Pietrasanta, Seravezza, Stazzema, Viareggio.

Nota A5.5 — route speciali: `confronta/meteo-clima/`, `confronta/economia/atlante-attivita-economiche/` e `confronta/comunita/affluenza/` restano eccezioni intenzionali, non regressioni DS2. Meteo/clima mantiene il workspace analitico specializzato ed è coperto dai gate clima e dalla shell canonica; l’Atlante mantiene il web component autonomo e il browser contract dedicato desktop/tablet/mobile; Affluenza mantiene il proprio archivio/event selector ma riusa token e componenti canonici con adattamenti responsive dedicati.

Nota chiusura A5.5: il checkpoint UI approvato è `bc9e5086aa796637828e1a5ae6e9952873024ef7`. La PR #280 è stata approvata visivamente e mergiata su `main` il 30/09/2026 con merge commit `a98b89995e01cd12f2ab8422a0a6ed6aa81b5578`; Quick, Full, rollout comunali e golden lock sono risultati verdi sullo stesso head finale `ab9743821bd60fa99c346e824968b30f6e6c3d5d`. A5 è quindi `DONE`.

Nota A5.1–A5.3: `docs/A5_DESIGN_SYSTEM_AUDIT.md` misura il sistema corrente e definisce la fondazione DS2 senza modificare la UI. La baseline CSS contiene 246 colori HEX distinti; `--paper` e `--surface` hanno contrasto 1,11:1; `--muted` su `--paper` è 4,37:1; 177/288 dichiarazioni `font-size` in px sono <= 11 px. L'audit rileva inoltre due sistemi tematici sovrapposti e copertura cromatica esplicita per 9 temi su 11. A5.2 separa canvas, superfici, testo, bordi, stati e tema; A5.3 converge `--theme-color` / `--theme-accent` in un solo vocabolario DS2. La prima modifica visuale è A5.4 e deve restare Draft fino ad approvazione desktop/mobile.

**Definition of done:** i dati emergono visivamente dal layout, i temi restano riconoscibili e contrasto/leggibilità migliorano in modo misurabile.

---

## A6 — Semantic Data Layer e interrogazione deterministica

**Stato:** `IN_PROGRESS`

Scopo: permettere di interrogare e mettere in relazione i dati senza introdurre conclusioni causali non supportate.

- [x] **A6.1** Definire modello semantico minimo: comune, indicatore, tema, periodo, dimensione, fonte, benchmark.

Nota A6 — 05-10-2026: #342 pubblicata, main `29f11f28`, deploy `37361574176` e verifica live `37362454243` SUCCESS. Censimento v7: 56/225 con adapter, 69 domande. Lotto finanza v8 in corso: 25 carrier aggiuntivi, copertura effettiva 81/225, 84 domande (52 calcoli/32 rifiuti); Rendiconto/SIOPE e date dei denominatori distinti, rapporti da componenti congelati, revisioni e limiti delle estrazioni normalizzate espliciti. Metodo `docs/A6_FINANCE_ADAPTERS.md`; audit, mappa e baseline separata. Nessuna acquisizione/modifica dati/UI/golden. A6.4–A6.6 aperte; A7 non avviata.
- [x] **A6.2** Definire operazioni deterministiche: confronto, serie, trend, variazione, scostamento, rango, correlazione, anomalia.
- [x] **A6.3** Stabilire regole di comparabilità temporale, territoriale e metodologica.
- [ ] **A6.4** Implementare un motore che restituisca sempre indicatori usati, periodi, unità, metodo e fonti.
- [ ] **A6.5** Produrre prime letture territoriali riproducibili e verificabili.
- [ ] **A6.6** Inserire avvertenze metodologiche esplicite per correlazione vs causalità.

**Definition of done:** domande analitiche multi-indicatore possono essere risolte con operazioni riproducibili, citando esattamente dati e metodo.

---

Nota A6.4 — v9: lotto carrier distinti debito, opere monitorate, Missione 03 e recupero fiscale; 85/225 con adapter. Componenti D1/interessi e recupero locale riconciliati; PDI 10.3 senza ponderazione retro-derivata, stock opere e missione normalizzati senza falsa prova raw. DAIT assegnazione 2025/riscossioni erariali 2024 separati. Continuità ordinario/OSL Massarosa non attestata: serie leggibili, trend/cambi rifiutati. 103 domande con aspettative indipendenti; A6.4 rimane parziale, A6.5–A6.6 aperte, A7 non avviata. Metodo `docs/A6_DISTINCT_FINANCE_ADAPTERS.md`; gate obbligatori prima della revisione per merge.


Nota A6.4 — v10 dopo #344 pubblicata: 16 adapter demografia e MIM già acquisiti; 101/225 effettivi, 68/181 sorgente, 130 domande (81 calcoli/49 rifiuti). Periodi nativi, cittadinanza/eventi, denominatori e risposte non definite espliciti. Metodo `docs/A6_DEMOGRAPHY_SCHOOL_ADAPTERS.md`; audit, collegamenti e baseline separata. Nessuna nuova acquisizione o modifica dati/UI/golden/workflow. A6.4 resta parziale, A6.5–A6.6 aperte; gate obbligatori prima del merge.

Nota A6.4 — v11 dopo #346 pubblicata: sette carrier di pendolarismo per lavoro Istat 2021, 108/225 effettivi e 75/181 sorgente; 148 domande (94 calcoli/54 rifiuti). Componenti, basi dei denominatori 2021/2026, precisione e margini comunali espliciti; nessuna ricostruzione della matrice origine-destinazione, autocontenimento territoriale o mobilità per studio. Metodo `docs/A6_COMMUTING_ADAPTERS.md`; audit, mappa e baseline separata. Dati/UI/golden/workflow preservati. Manutenzione della prontezza browser separata. A6.4–A6.6 aperte; gate obbligatori prima del merge.

## A7 — “Chiedi alla Versilia”

**Stato:** `NOT_STARTED`

Scopo: aggiungere linguaggio naturale solo sopra un layer semantico già governato.

- [ ] **A7.1** Tradurre la domanda utente in operazioni consentite dal motore semantico.
- [ ] **A7.2** Vietare risposte che inventino metriche, periodi o relazioni assenti.
- [ ] **A7.3** Restituire sempre evidenze, fonti, periodo e indicatori utilizzati.
- [ ] **A7.4** Testare domande ambigue, confronti impropri e richieste causali.
- [ ] **A7.5** Integrare UI solo dopo validazione metodologica del motore.

**Definition of done:** il linguaggio naturale facilita l'accesso ai dati ma non diventa una fonte autonoma di numeri o interpretazioni.

---

## Gate tra i workstream

Ordine raccomandato:

`A0 → A1 → A2 → A3 → A4 → A5 → A6 → A7`

Sono ammesse sovrapposizioni solo quando non cambiano contemporaneamente fonte di verità, pipeline dati e UI sullo stesso perimetro.

Prima di iniziare A5 deve essere stabile almeno A1. Prima di iniziare A6 devono essere stabili A1 e A3. A7 non parte prima della chiusura metodologica di A6.

## Criterio generale di chiusura

Un workstream passa a `DONE` soltanto quando:

1. il codice/documentazione prevista è presente;
2. i test pertinenti sono verdi;
3. il risultato è verificabile e non dipende da conteggi copiati manualmente;
4. l'handoff è aggiornato;
5. la PR è stata approvata e mergiata esplicitamente dal proprietario.

Nota A6.5 — estensione dopo gli adapter v11 della #349: il generatore esistente produce cinque percorsi × sette comuni e due riepiloghi da componenti sommate. Pendolarismo 2021 e scuola 2024/25 conservano universi e periodi propri; associazione descrittiva ecologica fra sette comuni, rifiuti temporali, ipotesi e proposte non approvate distinti. Copertura adapter e suite generale invariate. Report e metodo `docs/A6_TERRITORIAL_READINGS.md`; nessuna nuova UI o acquisizione. A6.5–A6.6 restano aperte per revisione metodologica; A7 non avviata.

Nota A6.4 — lotto ambientale v12: cinque adapter su carrier congelati, 113/225 effettivi e 80/181 sorgente; suite 166 domande. Rapporti idrici da volumi, rifiuti alla precisione pubblicata, costi CTOTab e benchmark con scopi espliciti. Serie rifiuti consultabili senza autorizzare confronti temporali non attestati. Metodo `docs/A6_ENVIRONMENT_ADAPTERS.md`. Restano 47 indicatori ambientali senza adapter e revisione metodologica A6.5–A6.6; nessuna chiusura di A6 o avvio A7.

Nota A6.4 — lotto agricolo v13 dopo #353 mergiata: cinque carrier Istat 2020 con ambiti centro aziendale/localizzazione distinti; 118/225 effettivi e 85/181 sorgente. Tre rapporti da componenti native, colture mancanti non imputate, nessuno storico inventato; 182 domande verificate. Metodo `docs/A6_AGRICULTURE_ADAPTERS.md`. Restano 42 indicatori ambientali senza adapter; A6.4 parziale e revisione A6.5–A6.6 aperta.

Nota A6.4 — v14 dopo #356 pubblicata: quattro carrier geografici/forestali materializzati, 122/225 effettivi e 85/181 sorgente. Densità 2026/2021 con componenti POSAS e superficie Istat; altimetria 2021 preserva sintesi arrotondata e otto fasce senza ettari retro-derivati; CFI nominale 2020 aggiornata 2024 distinta dal rapporto 2026. 197 domande (125 calcoli/72 rifiuti), 118 osservazioni indipendenti, 103 residui di cui 38 ambientali. Metodo `docs/A6_GEOGRAPHY_FOREST_ADAPTERS.md`; dati/UI/golden/workflow invariati. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.

Nota A6.4 — v15 dopo #358 pubblicata: stock e incremento suolo ISPRA, copertura UCS Toscana; 125/225 effettivi e 85/181 sorgente. Rapporti nativi con precisione pubblicata distinta, denominatori propri, categorie annidate non sommate, netto negativo e annualità mancanti preservati. Serie consultabili; continuità metodologica non attestata per trend/variazioni e associazioni temporali. 214 domande, 100 residui di cui 35 ambientali. Metodo `docs/A6_SOIL_LAND_COVER_ADAPTERS.md`; dati/UI/golden/workflow invariati. A6.4 parziale; revisione A6.5–A6.6 aperta, A7 non avviata.

Nota A6.4 — v16 dopo #359 pubblicata: aree protette, reticolo idrografico e feature censite di opere idrauliche regionali; 128/225 effettivi, 97 residui di cui 32 ambientali. Unione e categorie sovrapposte distinte; densità da km/area nativi, nessuna somma di presenze per contare feature uniche. Riferimenti di fonte/consultazione/confini distinti; niente serie inventate o gap rispetto al totale regionale censito. 230 domande, 161 osservazioni indipendenti con alias, 41 collegamenti tipizzati. Metodo `docs/A6_TERRITORY_ADAPTERS.md`; dati/UI/golden/workflow invariati. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.

Nota A6.4 — v17 dopo #360 pubblicata: esposizione ISPRA ad alluvioni e frane, 130/225 effettivi e 86/181 sorgente; 95 residui di cui 30 ambientali. Riferimenti mappe 2020/2024, confini 2024 e residenti censiti 2011/2021 separati. Componenti native e percentuali pubblicate distinte, scenari alluvionali annidati non sommati, campo ufficiale P3+P4 preservato. Storico areale frane 2017/2020/2024 leggibile a due decimali, senza dedurre residenti né trend/variazioni non attestati. 248 domande, 294 osservazioni fisse con alias e ripetizioni; 42 collegamenti tipizzati. Metodo `docs/A6_HAZARD_EXPOSURE_ADAPTERS.md`; dati/UI/golden/workflow invariati. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.

Nota A6.4 — v18 dopo #363 mergiata: IFC decili/ventili consultabili senza aritmetica cardinale; accessibilità effettiva 2019 distinta dalla release 2022, mediane comunali native Toscana/Italia. 133/225 effettivi, 86/181 sorgente; 92 residui, 28 ambientali. Suite 278 domande, 105 verifiche fisse nel lotto, 44 collegamenti tipizzati e 43 carichi. Metodo `docs/A6_FRAGILITY_ADAPTERS.md`; nessuna modifica a dati/UI/golden/workflow/Radar. A6.4 parziale e revisione A6.5–A6.6 aperta; A7 non avviata.

Nota A6.4 — v19 dopo #364 mergiata: linea statistica Istat 2021, protezione rigida ISPRA 2020 e dinamica litoranea 2006–2020 con universi e denominatori distinti. Quattro litoranei/tre n.a., chilometri nativi per quote aggregate, benchmark ISPRA percentuali ammessi; totali Istat, storico annuale e correlazioni automatiche rifiutati. 136/225 effettivi, 88/181 sorgente, 89 residui di cui 25 ambientali. Suite 308 domande, 56 verifiche fisse effettive/52 sorgente nel lotto, 46 collegamenti e 46 carichi. Metodo `docs/A6_COAST_ADAPTERS.md`. Dati/UI/golden/workflow/Radar invariati; A6.4 parziale, revisione A6.5–A6.6 aperta e A7 non avviata.

Nota A6.4 — v20 dopo #365 mergiata: classificazione ARPAT 2025 su 2022–2025, campioni 2025 per tipo e località FEE 2019–2026. Quattro costieri/tre n.a., quote aggregate da aree/km/campioni nativi distinti; supplettivi mirati e riconoscimenti multicriterio non equivalenti alla qualità microbiologica. Totali FEE non usati come medie comunali; zero 2021 di Pietrasanta conservato, serie leggibili senza trend/variazioni non revisionati. 139/225 effettivi, 91/181 sorgente, 86 residui di cui 22 ambientali; 342 domande, 152 verifiche fisse con alias e 32 conteggi storici per catalogo, 48 collegamenti e 49 carichi. Metodo `docs/A6_BATHING_ADAPTERS.md`; dati/UI/golden/workflow/Radar invariati. A6.4 parziale, revisione A6.5–A6.6 aperta; A7 non avviata.

Nota A6.4 — v21 dopo #366 mergiata: titoli SID e canoni annuali dovuti 2026 sullo snapshot agosto 2026; quattro costieri/tre n.a., attribuzione territoriale congelata di titoli comunali/portuali/Capitaneria. Quote e medie da componenti nativi, mediane non additive; nessuna equivalenza titoli–stabilimenti o dovuto–incassato/gettito comunale. Geometrie incomplete e storici non armonizzati non autorizzano nuove misure o variazioni. 141/225 effettivi, 93/181 sorgente, 84 residui di cui 20 ambientali; 383 domande, 48 verifiche fisse correnti per catalogo nel lotto, 50 collegamenti e 52 carichi. Metodo `docs/A6_MARITIME_ADAPTERS.md`; dati/UI/golden/workflow/Radar invariati. A6.4 parziale, revisione A6.5–A6.6 aperta; A7 non avviata.

Nota A6.4 — v22 dopo #367 mergiata: RTCave snapshot settembre 2026, produzione PRC 2019–2025 con copertura 2/7 e quadro PRC variante 2025 distinti. 90 record locali e componenti riconciliati, zero diverso da n.d.; record non necessariamente cave fisiche. Percentuali GIS native separate da tre rapporti ricostruiti da aree arrotondate, categorie G/GP/ACC non sommate né interpretate come escavato/autorizzato; SED non esaustivo. Storici di produzione leggibili senza variazioni/trend non revisionati; benchmark e correlazioni automatiche rifiutati. 144/225 effettivi, 96/181 sorgente, 81 residui di cui 17 ambientali; 435 domande, 226 verifiche nel lotto incluse alias e 14 storiche, 52 collegamenti, 55 carichi. Metodo `docs/A6_EXTRACTIVE_ADAPTERS.md`; dati/UI/golden/workflow/Radar invariati. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.

Avanzamento A6 v25 dopo #370 — clima: 156/225 adapter effettivi, 108/181 sorgente; 69 residui e cinque ambientali. Valori annui 2025 e delta OLS 1975–2025 distinti; metadati legacy espliciti. Min/max ERA5-Land continuo con offset costante, media/pioggia LaMMA + rianalisi calibrata. Serie 76/51 anni; pendenze/variazioni arbitrarie solo min/max omogenei, nessuna percentuale Celsius o aggregazione areale senza componenti. 63 riferimenti fissi indipendenti e replay distinto di 1.778 celle annue; 555 domande (268 calcoli, 287 rifiuti), 56 collegamenti e 64 carichi descrittivi. Raster/calibrazione/SIR congelati, non rigiocati. Metodo `docs/A6_CLIMATE_ADAPTERS.md`; report `reports/a6-climate/`. Dati, UI, asset, golden, workflow, Radar, Camaiore, 35 letture e due riepiloghi conservati. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata. Gate canonici prima del merge del proprietario.

Avanzamento A6 v26 dopo #372 — profili agricoli: 159/225 adapter effettivi, 109/181 sorgente, 66 residui di cui due ambientali. Cinque rapporti censuari 2020 con universi 959/957/944 e componenti native distinti; alias primari senza nuove osservazioni, zero ufficiale conservato, caratteristiche sovrapposte non sommate. SAU biologica regionale 2018–2024 leggibile e gap Toscana 2024 ufficiale; nessuna quota territoriale senza ettari o variazione/trend non revisionati. 622 domande (285 calcoli/337 rifiuti), 56 riferimenti correnti inclusi alias, 14 rapporti aggregati, 49 valori annui e sette gap nel lotto; 58 collegamenti e 67 carichi descrittivi. Microdati non riacquisiti né deduplicati. Metodo `docs/A6_AGRICULTURE_PROFILES_ADAPTERS.md`; report `reports/a6-agriculture-profiles/`. Dati, UI, golden, workflow, Radar e letture conservati; A6.4 parziale, A6.5–A6.6 aperte e A7 non avviata. Gate obbligatori prima del merge del proprietario.

Avanzamento A6 v27 dopo #375 — classificazioni territoriali: 160/225 adapter effettivi, 109/181 sorgente; 65 residui, uno ambientale (qualità acqua GAIA, non il conteggio delle località). DEGURBA e appartenenze litoranea/costiera consultabili al riferimento 2021, pubblicazione 2026 distinta; codici categoriali con etichette/booleani conservati, nessuna aritmetica o associazione automatica. 689 domande (313 letture/calcoli, 376 rifiuti), 28 osservazioni fisse inclusi alias, 59 collegamenti e 69 carichi descrittivi. Snapshot e cache riconciliati, nessuna nuova validazione di geometrie/microdati. Metodo `docs/A6_CLASSIFICATION_ADAPTERS.md`; dati, UI, golden, workflow, Radar e letture conservati. A6.4 parziale, A6.5–A6.6 aperte, A7 non avviata; gate canonici prima del merge del proprietario.

Avanzamento A6 v28 dopo #376, riallineato alla #377 Radar già mergiata — GAIA: 161/225 adapter effettivi e 110/181 sorgente, 64 residui e zero ambientali senza adapter. Consultazione esplicita per località/parametro del 2° semestre 2025, 70 × 17 stringhe con unità, qualificatori e riferimenti nativi; nessuna media comunale, censurato sostituito o valutazione di potabilità. `lookup` governato separatamente dai calcoli numerici, senza indebolire guardie o minimi dei confronti. 24 celle fisse, sette conteggi, replay distinto di 1.190 celle; 736 domande (344 consultazioni/calcoli, 392 rifiuti), 58 collegamenti e 72 carichi descrittivi. Metodo `docs/A6_WATER_QUALITY_ADAPTERS.md`; dati/UI/golden/workflow/Radar e letture conservati. A6.4 resta parziale e A6.5–A6.6 aperte; A7 non avviata. Gate canonici prima del merge del proprietario.

Avanzamento A6 v29 dopo #378 — quattro carrier MEF: distribuzioni con basi note/totale distinte, sette medie per fonte, quota pensionistica economica e contribuenti 2024/adulti 2026. Componenti native, null/zero e periodo ibrido espliciti; frequenze fra fonti non additive. Serie fonti/pensioni 2023–2024 dove disponibili; benchmark geografici solo dimensioni revisionate. Variazioni, trend, anomalie e coppie non certificate rifiutate. 165/225 effettivi, 114/181 sorgente, 60 residui; 802 domande (380 consultazioni/calcoli, 422 rifiuti), 161 osservazioni correnti fisse con alias/null e replay distinto 124 storiche con alias. Metodo `docs/A6_MEF_ADAPTERS.md`, report `reports/a6-mef/`; dati/UI/golden/workflow/Radar e letture conservati. Attese browser Demografia/Percorsi limitate senza abbassare le asserzioni. A6.4 parziale, A6.5–A6.6 aperte, A7 non avviata; gate canonici prima del merge del proprietario.

Avanzamento A6 v30 dopo #379 — RGS: quattro carrier del personale comunale, identità del datore e componenti stock/residenti/età/saldo netto distinti. Stock 31 dicembre vs residenti 1 gennaio 2024, Unioni e trasferimenti esclusi. Medie formazione pubblicate RGS, giornate e genere distinti; nessuna ponderazione o denominatore retro-derivato. Benchmark Toscana organico 273/273 con due zero PIAO espliciti e formazione Versilia dalla selezione congiunta ufficiale. 169/225 effettivi, 118/181 sorgente, 56 residui; 872 domande (415 consultazioni/calcoli, 457 rifiuti), 126 osservazioni fisse con alias, cinque rapporti aggregati, otto riferimenti pubblicati. Metodo `docs/A6_RGS_ADAPTERS.md`, report `reports/a6-rgs/`; dati/UI/golden/workflow/Radar e letture conservati. Serie/variazioni/trend/anomalie/correlazioni non certificate rifiutate. A6.4 parziale, A6.5–A6.6 aperte, A7 non avviata; gate canonici prima del merge del proprietario.

Avanzamento A6 v31 dopo #380 — turismo: sei nuovi carrier e presenze già governate rafforzate, 175/225 effettivi, 124/181 sorgente, 50 residui. Movimento 2023–2025 al netto delle locazioni; capacità 2024/residenti stimati 1 gennaio 2026 distinti, perimetro Istat 7.899 Comuni e ampliamento 2025 escluso. Quota pubblica estera arrotondata e rapporto nativo separati, nessun denominatore retro-derivato. Storico posti letto 2002–2024 leggibile; operazioni presenze già ammesse preservate, nuove analisi temporali/coppie non revisionate rifiutate per gli altri carrier. 960 domande (449 consultazioni/calcoli, 511 rifiuti), 56 osservazioni fisse, quattro rapporti territoriali, dieci benchmark e replay distinto di 245 celle storiche. 58 collegamenti tipizzati, 29 companion e 81 carichi descrittivi. Metodo `docs/A6_TOURISM_ADAPTERS.md`; dati/UI/golden/workflow/Radar e letture conservati. A6.4 parziale, A6.5–A6.6 aperte, A7 non avviata; gate canonici obbligatori prima del merge del proprietario.

Avanzamento A6 v32 dopo #381 — sei carrier regionali, SAU biologica già governata esclusa. Fonte comunale pubblicata, formule e universi espliciti, conteggi/denominatori numerici e distribuzione 118 non congelati. P75 distinto dalla media; disabilità amministrativa 0–64, nascita estera distinta da cittadinanza, innovazione classificata Ateco distinta da produzione innovativa. Servizi online definitivo 2022 con paniere 2018/2022 diverso; giovani 2020 assente. Serie consultabili e gap Toscana correnti, nessuna ponderazione retro-derivata o continuità temporale/coppia non revisionata. 181/225 effettivi, 130/181 sorgente, 44 residui; suite 1.053 domande (473 consultazioni/calcoli, 580 rifiuti), 42 celle correnti fisse, sei benchmark, 36 celle storiche fisse e replay distinto 252 celle. 58 collegamenti, 29 companion e 84 carichi descrittivi. Metodo `docs/A6_REGIONAL_ADAPTERS.md`; dati/UI/golden/workflow/Radar e letture conservati. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata. Gate canonici obbligatori prima della prontezza per il merge manuale.

Avanzamento A6 v33 dopo #382 — tre carrier biblioteche: indici ufficiali arrotondati, riferimento 2024 con copertura 5/7. Massarosa non alimentata e Stazzema assente distinti, nessuna imputazione o riporto storico. Serie prestiti/utenti 1998–2024 con lacune esplicite, ore soltanto 2022–2024; benchmark Toscana corrente. Pooling, variazioni/trend, anomalie e coppie non revisionate rifiutati. 21 celle correnti, tre benchmark, 57 celle storiche fisse e replay distinto 399 celle incluse null; 58 nuove domande. Metodo `docs/A6_LIBRARY_ADAPTERS.md`; 184/225 effettivi, 133/181 sorgente, 41 residui; 1.111 domande PASS (485 consultazioni/calcoli, 626 rifiuti), 58 collegamenti, 29 companion e 87 carichi descrittivi. Report `reports/a6-library/`; gate canonici da verificare nella PR prima della prontezza al merge manuale. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.

Avanzamento A6 v34 dopo #384 — quattro carrier INVALSI, 32 viste grado/prova e 46 categorie correnti. Comune plesso distinto da residenza; Totale ufficiale e benchmark Toscana/Italia per la stessa annata/vista, null e gap 2019–20 conservati. Periodi scolastici espliciti, livelli solo correnti; nessun pooling da percentuali di partecipazione/copertura o continuità temporale/coppia inferita. 28 celle correnti, 21 storiche, otto benchmark e due QCER fissi; replay distinto di 1.442 celle storiche, 412 benchmark e 322 categorie. Metodo `docs/A6_INVALSI_ADAPTERS.md`; 188/225 effettivi, 133/181 sorgente, 37 residui; 1.295 domande PASS (631 consultazioni/calcoli, 664 rifiuti), 58 collegamenti, 29 companion e 91 carichi descrittivi. Report `reports/a6-invalsi/`; gate canonici da verificare nella PR. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.

Avanzamento A6 v35 dopo #385 — due indicatori spesa sociale Istat: €/abitante nominali inclusivi 2014–2022, benchmark Toscana/Italia solo 2022 e sette quote native per area solo 2022. Arrotondamento pubblico e provenienza espliciti; zeri validi, alias iniziale e summary in unità distinte. Medie comunali descrittive, nessun pooling o denominatore ricostruito, operazioni temporali/coppie non revisionate rifiutate. Metodo `docs/A6_SOCIAL_SPENDING_ADAPTERS.md`; 190/225 effettivi, 135/181 sorgente, 35 residui; 1.350 domande PASS (650 consultazioni/calcoli, 700 rifiuti), 58 collegamenti, 29 companion e 94 carichi descrittivi. Report `reports/a6-social-spending/`; gate canonici da verificare nella PR. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.

Avanzamento A6 v36 dopo #386 — due carrier farmacie/RSA: sedi valide e accreditamento 31 dicembre 2025, denominatore farmacie POSAS stimato 1 gennaio 2026 distinto. Arrotondamento pubblico a due decimali, benchmark farmacie non arrotondato; RSA assolute regionali non equiparate a un tasso comunale. 14 celle fisse, sette conteggi/denominatori indipendenti e 14 gap; zeri, pari merito e deduplicazione governati. Metodo `docs/A6_HEALTH_FACILITIES_ADAPTERS.md`; 192/225 effettivi, 136/181 sorgente e 33 residui. Suite 1.402 domande PASS (680 consultazioni/calcoli, 722 rifiuti); 58 collegamenti, 29 companion e 97 carichi descrittivi. Report `reports/a6-health-facilities/`; gate canonici da verificare nella PR. Nessun nuovo dato/UI/golden/workflow/Radar; A6.4 parziale, A6.5–A6.6 aperte, A7 non avviata.
