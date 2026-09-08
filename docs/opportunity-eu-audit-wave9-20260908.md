# Radar Opportunità · audit UE/nazionale · Wave 9

**Data:** 8 settembre 2026  
**PR:** #161  
**Stato:** `open_not_saturated`  
**Implementazione:** congelata  
**Sweep puliti consecutivi validi per il gate:** **0/2**

## Esito

La Wave 9 ha verificato un asse indipendente rispetto alle precedenti passate: **applicabilità reale ai sette Comuni, coda `internal_review` e route nazionali**.

Su questo asse non è emerso alcun nuovo gap corrente azionabile. La passata non viene tuttavia conteggiata come primo sweep pulito del gate perché il corpus complessivo non è ancora chiuso: restano famiglie note da completare (NEB Facility, LIFE CET residuo, Horizon Cluster 5/6, I3 e cascade/downstream calls).

Il risultato più importante è una **rettifica dell'audit stesso**: i due presunti errori di fan-out comunale riportati nella Wave 8 non sono bug del Radar. La Wave 8 aveva interpretato il campo top-level `municipalities` come risultato di eleggibilità, mentre la fonte canonica usa `municipality_eligibility` per la decisione puntuale.

Il gate resta quindi **0/2**, ma senza trascinare due falsi problemi nell'hardening futuro.

---

## 1. Rettifica Wave 8 · Crescere nei piccoli comuni 2026

La Wave 8 aveva classificato il caso come `captured_with_eligibility_overbreadth`, sostenendo che il Radar attribuisse la misura a tutti e sette i Comuni.

Il controllo del record canonico mostra invece che `municipality_eligibility` è già calcolato correttamente:

- Camaiore: `not_eligible`;
- Forte dei Marmi: `not_eligible`;
- Massarosa: `not_eligible`;
- Pietrasanta: `not_eligible`;
- Seravezza: `not_eligible`;
- **Stazzema: `eligible`**;
- Viareggio: `not_eligible`.

Il requisito ufficiale è la popolazione residente fino a **5.000 abitanti**.

Fonte ufficiale:

https://famiglia.governo.it/it/politiche-e-attivita/finanziamenti-avvisi-e-bandi/avvisi-e-bandi/avviso-crescere-nei-piccoli-comuni-2026-stanziati-50-milioni-di-euro-per-le-famiglie/

**Classificazione corretta:** `captured_with_correct_municipality_filter`.

**Rettifica root cause:** non è dimostrato alcun `municipality_scope_fanout_without_condition_evaluation` su questo caso.

---

## 2. Rettifica Wave 8 · Capitale italiana del mare 2027

Anche qui la Wave 8 aveva letto l'array top-level come decisione finale.

Il record canonico distingue invece correttamente:

- Camaiore: `eligible`;
- Forte dei Marmi: `eligible`;
- Massarosa: `not_eligible`;
- Pietrasanta: `eligible`;
- Seravezza: `not_eligible`;
- Stazzema: `not_eligible`;
- Viareggio: `eligible`.

Il requisito è essere **Comune costiero italiano**.

Fonte ufficiale:

https://www.dipartimentopolitichemare.gov.it/it/bandi-e-avvisi/capitale-italiana-del-mare/procedura-di-selezione-anno-2027/

**Classificazione corretta:** `captured_with_correct_municipality_filter`.

Anche questo finding della Wave 8 viene formalmente ritirato.

---

## 3. Controlli di precisione comunale

### Toscana Diffusa · strutture di servizio pubbliche

Il Radar associa correttamente:

- **Camaiore**: ammissibile come `TD*`, ma soltanto per interventi nella porzione montana del territorio;
- **Seravezza**: ammissibile `TD`;
- **Stazzema**: ammissibile `TD`;
- Forte dei Marmi, Massarosa, Pietrasanta, Viareggio: non ammissibili.

La stessa condizione `TD*` è riportata nella regola canonica.

**Classificazione:** `captured_with_correct_partial_territory_condition`.

### Conto Termico 3.0

Il Radar distingue già correttamente tra accesso generale della PA e regime rafforzato legato alla soglia dei **15.000 abitanti**:

- Forte dei Marmi, Seravezza e Stazzema: entro soglia, fermo il rispetto degli altri requisiti;
- Camaiore, Massarosa, Pietrasanta e Viareggio: accesso ordinario come PA, senza attribuzione automatica del regime al 100% per la sola soglia demografica.

**Classificazione:** `captured_with_correct_demographic_condition`.

### Bando Sistemi museali 2026

È già presente nel record canonico e la partecipazione è modellata tramite il sistema museale pertinente.

Scadenza: **25 settembre 2026, ore 23:59**.

**Classificazione:** `captured`.

### Toscanaincontemporanea 2026

È già presente nel Radar.

Scadenza: **23 settembre 2026, ore 12:00**.

**Classificazione:** `captured`.

---

## 4. `internal_review` · duplicati da non confondere con promotion gap

La Wave 9 conferma che un record in `internal_review` non può essere classificato come promotion gap prima del confronto con `opportunities` canoniche.

### Mercati rionali 2026

Il frammento ANCI Toscana “bando in arrivo” è ancora nella coda, ma il Radar possiede già la scheda canonica con regola `st-mercati-rionali-2026`.

Scadenza: **15 settembre 2026, ore 12:00**.

**Classificazione:** `captured_internal_review_duplicate_noise`.

### Bando Amianto Edifici Pubblici 2026

Anche il vecchio frammento ANCI resta in coda, ma la misura è già pubblica nel Radar con richiedenti comunali correttamente verificati.

Scadenza: **30 settembre 2026, ore 16:00**.

**Classificazione:** `captured_internal_review_duplicate_noise`.

### Eventi sportivi di rilevanza nazionale e internazionale 2026

La pagina generica del Dipartimento Sport genera frammenti `internal_review`, ma la scheda canonica è già presente e modella correttamente il Comune come richiedente condizionale quando dispone del titolo di esclusività nell'organizzazione/realizzazione dell'evento.

Scadenza massima: **1 dicembre 2026, ore 23:59**.

**Classificazione:** `captured_internal_review_duplicate_noise`.

### Metodo corretto

Nuova regola metodologica dell'audit:

`canonical_opportunity_crosscheck_required_before_promotion_gap_classification`

La coda contiene contemporaneamente:

- frammenti di navigazione e pagine indice;
- contenuti storici;
- duplicati di schede canoniche già pubbliche;
- veri promotion gap, come il Marchio del patrimonio europeo 2027 già accertato in Wave 8.

Il successivo hardening dovrà quindi migliorare anche la deduplicazione semantica della coda, non soltanto la discovery.

---

## 5. Spiagge Sicure 2026 · chiuso il perimetro Versilia

Il Ministero dell'Interno ha selezionato **60 Comuni costieri** per l'edizione 2026:

- dotazione totale: **1,5 milioni di euro**;
- contributo: **25.000 euro per Comune**;
- beneficiari predeterminati;
- progetto da presentare alla Prefettura competente;
- interventi da concludere entro il **15 ottobre 2026**.

Fonte ufficiale:

https://www.interno.gov.it/it/amministrazione-trasparente/disposizioni-generali/atti-generali/atti-amministrativi-generali/circolari/circolare-24-giugno-2026-prevenzione-e-contrasto-dellabusivismo-commerciale-e-vendita-prodotti-contraffatti-spiagge-sicure-estate-2026-finanziamento

L'elenco dei 60 beneficiari contiene per la Toscana soltanto:

- **Magliano in Toscana**;
- **Montignoso**.

Nessuno dei sette Comuni del Radar è quindi beneficiario.

**Classificazione:** `correctly_excluded_geography` / `predetermined_beneficiary_list`.

L'assenza dallo snapshot pubblico è corretta per il perimetro Versilia.

---

## 6. AMIF Integration at Local Level · route italiana ancora sotto watch

La Commissione conferma la Specific Action `AMIF/2026/SA/2.4.2`:

- budget: **77 milioni di euro**;
- città e Comuni tra i beneficiari possibili;
- progetto da **0,8 a 7,5 milioni di euro**;
- cofinanziamento UE fino al **90%**;
- selezione dei progetti demandata alla **Managing Authority nazionale**;
- deadline della procedura tra Stati membri e Commissione: **2 ottobre 2026**.

Fonte Commissione:

https://home-affairs.ec.europa.eu/news/integration-local-level-eur-77-million-under-amif-specific-action-2026-05-21_en

Sono stati verificati entrambi i canali ufficiali italiani FAMI:

- avvisi pubblici;
- altre modalità / inviti e interventi ad hoc.

Alla data dell'8 settembre 2026 non è stato individuato in tali canali un meccanismo italiano pubblicato che corrisponda inequivocabilmente a `AMIF/2026/SA/2.4.2`.

Questo **non dimostra che l'Italia non abbia una route**; significa soltanto che il meccanismo di selezione italiano non è ancora risolto con evidenza pubblica sufficiente.

**Classificazione:** `national_route_watch / unresolved_Italian_selection_mechanism`.

---

## 7. DAIT · contributo spese di progettazione annualità 2026

La coda `internal_review` intercetta il comunicato DAIT del **24 agosto 2026** relativo all'assegnazione del contributo per progettazione definitiva ed esecutiva.

La vera finestra di candidatura era però precedente:

- apertura: **24 novembre 2025**;
- chiusura: **15 gennaio 2026, ore 23:59**.

Era una misura reale per enti locali, relativa a progettazione per:

- messa in sicurezza da rischio idrogeologico;
- strade, ponti e viadotti;
- edifici pubblici e scolastici, compresi interventi di efficientamento energetico.

La finestra è quindi chiusa da mesi e precedente alla finestra di audit corrente.

**Classificazione:** `historical_pre_launch_gap`.

Va mantenuta come **sentinella annuale/replay storico**, non come falso negativo corrente.

---

## 8. Ri-generare con creatività · controllo di scope

La DG Creatività Contemporanea ha riaperto fino al **30 ottobre 2026** la raccolta di contributi ed esperienze di rigenerazione urbana a base culturale, con una traccia specifica per gli **Enti locali**.

È una partecipazione reale ma non risultano un contributo economico, una technical assistance o un premio.

**Classificazione:** `scope_review_low_value_participation`.

Il caso serve a fissare il confine qualitativo del Radar: non ogni consultazione o raccolta di esperienze rivolta ai Comuni deve diventare automaticamente una card pubblica.

---

## 9. Conclusione Wave 9

### Nuovi gap correnti azionabili

**Nessuno** su questo asse.

### Rettifiche

Due finding Wave 8 vengono ritirati:

- `Crescere nei piccoli comuni 2026`;
- `Capitale italiana del mare 2027`.

Il filtro comunale canonico è risultato corretto anche nei controlli su:

- soglia demografica;
- costa;
- Toscana Diffusa e porzione `TD*`;
- regimi differenziati per popolazione.

### Cosa resta vero dalla Wave 8

Restano pienamente validi i gap già accertati su:

- Horizon Cluster 3 `INFRA-01/02/03`;
- Marchio del patrimonio europeo 2027;
- SINFI 2026;
- Cultura Missione Comune 2026.

### Gate

La Wave 9 è **pulita sull'asse esaminato**, ma non è ancora uno sweep completo eleggibile per il conteggio di saturazione.

**Contatore: 0/2.**

L'implementazione resta congelata.

---

## Prossimi assi da chiudere

1. completare la matrice dei **9 topic NEB Facility 2026**;
2. chiudere LIFE CET residuo: `ENERPOV`, `POLICY`, `RENEWHC`, `BETTERRENO`, `OSS`;
3. chiudere Horizon Cluster 5/6, in particolare `CIRCBIO-04` e `ZEROPOLLUTION-03`;
4. approfondire I3 DG REGIO/EISMEA e ruolo effettivo di un Comune toscano;
5. continuare cascade/FSTP/associated regions/replicator e Mission Ocean downstream EOI;
6. solo dopo la chiusura di questi assi eseguire un nuovo sweep completo indipendente che possa eventualmente portare il gate da **0/2 a 1/2**.
