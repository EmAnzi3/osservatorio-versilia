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

**Stato:** `IN_PROGRESS`

Scopo: verificare sistematicamente se stiamo sfruttando tutto ciò che le fonti offrono, invece di scoprire gli arricchimenti per caso.

- [x] **A3.1** Definire le dimensioni comuni di enrichment: serie storica, sesso, età, dettaglio territoriale, benchmark Toscana/Italia, assoluto/normalizzato, frequenza infra-annuale, numeratore/denominatore, categorie specifiche.
- [x] **A3.2** Classificare ogni coppia indicatore/dimensione come `ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`.
- [ ] **A3.3** Eseguire audit fonte per fonte sul catalogo completo.
- [ ] **A3.4** Trasformare `AVAILABLE_MISSING` in backlog ordinato per valore informativo e costo di acquisizione.
- [ ] **A3.5** Integrare nuove dimensioni in lotti controllati con QA e fonte dichiarata.
- [ ] **A3.6** Introdurre un indicatore interno di copertura enrichment, derivato e non autocelebrativo.

Nota A3.1: la tassonomia e la semantica dei quattro stati sono definite in `docs/A3_ENRICHMENT_AUDIT.md`. Il documento è metodologico e non introduce un secondo catalogo o una matrice manuale di indicatori.

Nota A3.2: la chiusura è governata dalla matrice strict derivata dall'Effective Public Catalog: 225 indicatori × 9 dimensioni = 2.025 coppie, con `unclassifiedPairCount = 0`. Il gate A3 verifica inoltre le evidenze strutturali e tutte le classificazioni esplicite; nessun `ACQUIRED` è dichiarato manualmente.

**Definition of done:** per ogni indicatore sappiamo quali dimensioni la fonte rende disponibili, quali abbiamo acquisito e quali mancano ancora.

---

## A4 — Visualization & Content Contract

**Stato:** `NOT_STARTED`

Scopo: trasformare le attuali regole di coerenza da linee guida distribuite a invarianti globali testabili.

- [ ] **A4.1** Consolidare le regole esistenti di UI, scale, tooltip, unità, medie, benchmark e dati mancanti.
- [ ] **A4.2** Definire metadati/contratti derivabili che evitino duplicazioni per unità, precisione, semantica colore e formato tooltip.
- [ ] **A4.3** Testare coerenza tra dato, testo, asse, tooltip, legenda e unità.
- [ ] **A4.4** Testare esplicitamente media semplice vs ponderata e denominatori quando applicabili.
- [ ] **A4.5** Introdurre visual regression su un campione rappresentativo per famiglia di grafici/temi, non screenshot indiscriminati dell'intero sito.
- [ ] **A4.6** Portare i nuovi gate nel preflight generale.

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
