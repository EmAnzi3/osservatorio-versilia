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

**Stato:** `NOT_STARTED`

Scopo: migliorare gerarchia e leggibilità riducendo la predominanza del beige senza perdere l'identità del progetto.

- [ ] **A5.1** Audit quantitativo/visivo di superfici, contrasto, densità e gerarchia.
- [ ] **A5.2** Definire ruoli cromatici: canvas neutro, superfici analitiche chiare, colore tematico usato come informazione.
- [ ] **A5.3** Definire token comuni per background, card, bordi, testo, stati e temi.
- [ ] **A5.4** Applicare il nuovo sistema a una pagina pilota e verificarlo desktop/mobile.
- [ ] **A5.5** Estendere progressivamente senza modifiche massive non verificabili.

**Definition of done:** i dati emergono visivamente dal layout, i temi restano riconoscibili e contrasto/leggibilità migliorano in modo misurabile.

---

## A6 — Semantic Data Layer e interrogazione deterministica

**Stato:** `NOT_STARTED`

Scopo: permettere di interrogare e mettere in relazione i dati senza introdurre conclusioni causali non supportate.

- [ ] **A6.1** Definire modello semantico minimo: comune, indicatore, tema, periodo, dimensione, fonte, benchmark.
- [ ] **A6.2** Definire operazioni deterministiche: confronto, serie, trend, variazione, scostamento, rango, correlazione, anomalia.
- [ ] **A6.3** Stabilire regole di comparabilità temporale, territoriale e metodologica.
- [ ] **A6.4** Implementare un motore che restituisca sempre indicatori usati, periodi, unità, metodo e fonti.
- [ ] **A6.5** Produrre prime letture territoriali riproducibili e verificabili.
- [ ] **A6.6** Inserire avvertenze metodologiche esplicite per correlazione vs causalità.

**Definition of done:** domande analitiche multi-indicatore possono essere risolte con operazioni riproducibili, citando esattamente dati e metodo.

---

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
