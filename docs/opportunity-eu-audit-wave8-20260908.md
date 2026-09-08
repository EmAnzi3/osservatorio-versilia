# Radar Opportunità · audit UE/nazionale · Wave 8

**Data:** 8 settembre 2026  
**PR:** #161  
**Stato:** `open_not_saturated`  
**Implementazione:** congelata  
**Sweep puliti consecutivi:** **0/2**

## Esito

La Wave 8 non è uno sweep pulito. Il controllo dei residui Cluster 3, della coda `internal_review` e di un oracle istituzionale nazionale ha prodotto nuovi gap correnti e, soprattutto, ha evidenziato un problema distinto dalla discovery: il Radar può catturare correttamente una misura ma attribuirla a tutti i sette Comuni anche quando il requisito territoriale o demografico ne ammette solo alcuni.

I nuovi finding principali sono:

1. tre topic Horizon Cluster 3 `INFRA` con possibile ruolo del Comune come **beneficiario practitioner di protezione civile**;
2. un vero **promotion gap** nel `internal_review`: Marchio del patrimonio europeo 2027;
3. un nuovo **rolling structural gap** nazionale: SINFI 2026 · Supporto ai Comuni;
4. un nuovo **current false negative** nazionale: Cultura Missione Comune 2026;
5. due errori correnti di applicabilità comunale: `Crescere nei piccoli comuni 2026` e `Capitale italiana del mare 2027`.

Di conseguenza il contatore di saturazione resta **0/2**.

---

## 1. Cluster 3 · INFRA-01, INFRA-02 e INFRA-03

La call `HORIZON-CL3-2026-01` è aperta dal **6 maggio 2026** al **5 novembre 2026, ore 17:00 Bruxelles**.

Fonte ufficiale:

https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/wp-call/2026-2027/wp-6-civil-security-for-society_horizon-2026-2027_en.pdf

### HORIZON-CL3-2026-01-INFRA-01

**Tools and processes to support stress tests of critical infrastructure**

- Innovation Action;
- budget topic: **9,67 milioni di euro**;
- contributo atteso: circa **4,835 milioni per progetto**;
- almeno **3 practitioner pertinenti devono essere beneficiari**;
- i portfolio ammessi includono espressamente una **civil protection authority**.

Il codice esatto non compare nello snapshot di riferimento.

In Italia il nesso comunale non è teorico: il Codice della protezione civile qualifica i Sindaci come autorità territoriali di protezione civile e attribuisce ai Comuni funzioni di protezione civile.

Fonte nazionale:

https://www.protezionecivile.gov.it/it/normativa/decreto-legislativo-n1-del-2-gennaio-2018-codice-della-protezione-civile/

**Classificazione:** `current_conditional_beneficiary_false_negative`.  
Il Comune non va promosso indiscriminatamente: il ruolo è reale quando il progetto richiede il suo coinvolgimento come practitioner di protezione civile o altra autorità pertinente.

### HORIZON-CL3-2026-01-INFRA-02

**Security challenges of the green transition in urban and peri-urban areas**

- Research and Innovation Action;
- budget topic: **4 milioni di euro**;
- circa **4 milioni per progetto**;
- almeno **3 practitioner come beneficiari**;
- i portfolio includono `civil protection authority` e `safety or security first responders`.

La Wave 7 lo aveva prudenzialmente lasciato in `scope_review`. L'evidenza completa di eleggibilità impone una correzione verso l'alto.

**Nuova classificazione:** `current_conditional_beneficiary_false_negative`.

### HORIZON-CL3-2026-01-INFRA-03

**Targeted innovative capabilities for the resilience of critical entities to natural and human-induced disasters, including hybrid scenarios**

- Innovation Action;
- budget topic: **9 milioni di euro**;
- circa **4,5 milioni per progetto**;
- almeno **3 practitioner come beneficiari**;
- portfolio ammessi: critical infrastructure operator, authority for critical-infrastructure resilience, **civil protection authority**, first responders, authority managing NaTech events, law enforcement/security providers.

**Classificazione:** `current_conditional_beneficiary_false_negative`.

### Controlli negativi Cluster 3

Lo stesso criterio non deve trasformarsi in una promozione indiscriminata di tutto Cluster 3.

- `DRS-03`: richiede first responders e medical emergency authorities; un Comune non è automaticamente uno di questi soggetti;
- `DRS-04`: la condizione sugli enti responsabili del disaster risk è definita nel Work Programme con riferimento a public bodies operanti a livello nazionale; le autorità locali sono stakeholder di uptake, non automaticamente beneficiari richiesti;
- `SSRI-04`: richiede first-responder organisations; pertinenza territoriale non equivale a eleggibilità automatica del Comune;
- il residuo FCT/BM verificato in questa passata resta prevalentemente legato a Police Authorities, Border/Coast Guard, Customs e practitioner specializzati.

Questa distinzione deve diventare una regola del successivo hardening: **ruolo documentato sì, keyword locale no**.

---

## 2. `internal_review` · vero promotion gap: Marchio del patrimonio europeo 2027

La coda interna contiene la pagina ufficiale MiC:

**Bando per la preselezione dei siti italiani da candidarsi al Marchio del patrimonio europeo nell'ambito della selezione 2027**.

Il bando è corrente:

- pubblicazione: **23 giugno 2026**;
- scadenza candidature: **4 novembre 2026**;
- due progetti italiani saranno preselezionati;
- trasmissione alla Commissione entro il 1° marzo 2027.

Fonte ufficiale:

https://cultura.gov.it/comunicato/29136

Il modello del Marchio distingue il soggetto proponente dalla `autorità di gestione` del sito. Un Comune può quindi avere un ruolo diretto quando propone o gestisce un sito eleggibile.

Non è un grant monetario: è una **opportunità di riconoscimento/label**, categoria che il Radar deve comunque saper presidiare insieme a premi e riconoscimenti.

Sant'Anna di Stazzema è già tra i siti italiani insigniti del Marchio: quel sito specifico non costituisce quindi una nuova candidatura 2027. Questo non elimina la rilevanza generale della call per enti locali che propongano o gestiscano altri siti eleggibili.

**Stato Radar:** scoperto, ma solo `internal_review`.  
**Classificazione:** `promotion_gap`.  
**Severità:** `high`.

La coda `internal_review` non è quindi soltanto rumore: dopo dedup e filtri contiene almeno un'altra opportunità corrente realmente trattenuta.

---

## 3. Nuovo gap nazionale · SINFI 2026

### Supporto ai Comuni fino a 50.000 abitanti

Infratel Italia ha avviato il progetto SINFI 2026 rivolto ai **Comuni fino a 50.000 abitanti**.

Il servizio consente gratuitamente:

- raccolta dati infrastrutturali;
- rilievo in campo di reti e infrastrutture;
- digitalizzazione delle informazioni;
- adeguamento agli standard SINFI;
- caricamento dei dati sulla piattaforma nazionale.

Le richieste sono possibili dal **8 giugno 2026** e vengono gestite **FIFO fino a esaurimento delle risorse**.

Fonte ufficiale:

https://www.infratelitalia.it/archivio-news/notizie/progetto-sinfi-2026-i-comuni-fino-50000-abitanti-infratel-italia-apre

Non è un contributo cash al Comune, ma un servizio tecnico gratuito finanziato con risorse pubbliche e direttamente richiedibile dall'amministrazione.

Il caso non compare nello snapshot di riferimento.

**Classificazione:** `rolling_structural_gap`.  
**Severità:** `high`.

Questo finding conferma che il Radar deve presidiare anche il perimetro **supporto tecnico nazionale / servizi gratuiti / richieste fino a esaurimento risorse**, non soltanto i bandi con una data di scadenza.

---

## 4. Nuovo falso negativo nazionale · Cultura Missione Comune 2026

L'Istituto per il Credito Sportivo e Culturale ha aperto **Cultura Missione Comune 2026**.

Caratteristiche principali:

- plafond complessivo **50 milioni di euro**;
- mutui a tasso fisso con **integrale abbattimento del tasso di interesse**;
- destinatari: **Enti Locali, Province e Regioni**;
- interventi su patrimonio culturale pubblico, restauro, efficientamento, accessibilità, acquisto di beni culturali, cofinanziamenti, digitalizzazione e maggiori costi ammissibili;
- fino a **2 milioni** per Comuni <=5.000 abitanti;
- fino a **4 milioni** per Comuni tra 5.000 e 100.000 abitanti;
- domanda entro **30 settembre 2026**.

Fonte ufficiale:

https://www.creditosportivo.it/cliente-enti-territoriali/

Il titolo non compare nello snapshot di riferimento.

**Classificazione:** `current_false_negative`.  
**Severità:** `critical`.

È un finding importante perché amplia la tassonomia delle opportunità oltre `grant`: un finanziamento agevolato a interesse integralmente abbattuto è chiaramente operativo per un Comune e non deve essere ignorato dal Radar.

---

## 5. Nuovo root cause · applicabilità comunale troppo larga

Il confronto non si limita più a `presente/assente`. Due schede già pubbliche dimostrano che il Radar può conoscere correttamente il requisito ma poi associare comunque l'opportunità a **tutti e sette i Comuni**.

### 5.1 Crescere nei piccoli comuni 2026

La scheda pubblica del Radar riporta correttamente:

> Comune con popolazione residente fino a 5.000 abitanti.

Ma sotto `Comuni della Versilia` visualizza:

- Camaiore;
- Forte dei Marmi;
- Massarosa;
- Pietrasanta;
- Seravezza;
- Stazzema;
- Viareggio.

La fonte PCM limita invece l'avviso ai Comuni fino a **5.000 abitanti**.

L'Allegato 1 ufficiale costituisce l'elenco dei Comuni <=5.000 sulla base della popolazione al 1° gennaio 2025. Tra i sette Comuni del Radar compare **solo Stazzema**, con popolazione 2.892; gli altri sei non compaiono nell'elenco.

Fonti:

- https://famiglia.governo.it/it/politiche-e-attivita/finanziamenti-avvisi-e-bandi/avvisi-e-bandi/avviso-crescere-nei-piccoli-comuni-2026-stanziati-50-milioni-di-euro-per-le-famiglie/
- https://famiglia.governo.it/media/pfzlra1b/allegato-1-avviso-piccoli-comuni.pdf

**Classificazione:** `captured_with_eligibility_overbreadth`.  
**Severità:** `critical`.

Errore effettivo: **6 Comuni su 7 visualizzati come pertinenti senza esserlo**.

### 5.2 Capitale italiana del mare 2027

La scheda pubblica dichiara correttamente:

> Comune costiero italiano.

Ma anche qui il Radar visualizza tutti e sette i Comuni.

La procedura ufficiale è riservata ai **Comuni costieri** e assegna al vincitore un contributo di **1 milione di euro**.

Fonte:

https://www.dipartimentopolitichemare.gov.it/it/bandi-e-avvisi/capitale-italiana-del-mare/procedura-di-selezione-anno-2027/

Nel perimetro Versilia i Comuni costieri sono:

- Camaiore;
- Forte dei Marmi;
- Pietrasanta;
- Viareggio.

Massarosa, Seravezza e Stazzema non soddisfano il requisito costiero.

**Classificazione:** `captured_with_eligibility_overbreadth`.  
**Severità:** `high`.

### Root cause

I due casi convergono su una stessa famiglia:

`municipality_scope_fanout_without_condition_evaluation`

Il problema non è la discovery né la verifica della scheda: è la fase finale che propaga la scheda a tutti i Comuni senza valutare la condizione specifica.

Questo deve essere auditato sistematicamente su:

- soglie demografiche;
- Comune costiero/non costiero;
- geografie Toscana Diffusa/montane;
- qualifiche territoriali;
- proprietà/disponibilità di asset;
- appartenenza a reti o sistemi;
- condizioni programme-specific.

---

## 6. `internal_review` · pulizia della coda

La revisione conferma che una quota importante dei **40** elementi `reviewInternal` non è costituita da opportunità pubblicabili autonome.

### Valorizzazione Centri Commerciali Naturali 2026

È una misura corrente toscana, ma i richiedenti sono gli **organismi di gestione dei CCN costituiti principalmente tra imprese del commercio**. Il Comune non è il richiedente diretto.

Fonte:

https://www.sviluppo.toscana.it/bando/bando-centri-commerciali-naturali-2026/

**Classificazione:** `correctly_excluded_eligibility`.

### Fondo attività socio-educative minori 2026

La misura è reale e comunale, ma la fase di adesione/assegnazione è già avvenuta e l'elenco 2026 dei beneficiari è stato determinato. Non è una nuova finestra di candidatura corrente all'8 settembre.

**Classificazione:** `historical_or_allocated_lifecycle_control`.

### EUCF 8th call

Il record ufficiale upcoming è già pubblico nel Radar; il frammento della pagina ManagEnergy rimasto in `internal_review` è duplicazione/queue noise.

**Classificazione:** `captured`.

### Digital Europe CYBER

Le call aperte richiedono verifica topic-specific su soggetti cyber/NIS2. I sette Comuni non devono essere promossi automaticamente in assenza di una base di eleggibilità documentata.

**Classificazione:** `scope_review`.

### Conclusione sulla coda

La coda contiene almeno due fenomeni diversi:

1. **queue noise / duplicati / indici / storici**;
2. **veri promotion gap**, come Co-create NEB e ora Marchio del patrimonio europeo 2027.

La futura correzione non deve semplicemente abbassare la soglia di promozione: deve prima separare semanticamente questi due gruppi.

---

## 7. AMIF · route italiana ancora non risolta

La Specific Action **Integration at Local Level** resta confermata dalla Commissione:

- budget indicativo: **77 milioni di euro**;
- beneficiari possibili: città, Comuni, autorità regionali e agenzie locali;
- contributo per progetto: **0,8-7,5 milioni di euro**;
- cofinanziamento UE fino al **90%**;
- selezione dei progetti affidata alle Managing Authorities nazionali;
- scadenza della candidatura nazionale alla Commissione: **2 ottobre 2026**.

Fonte:

https://home-affairs.ec.europa.eu/news/integration-local-level-eur-77-million-under-amif-specific-action-2026-05-21_en

Anche in questa passata non è stato confermato un avviso ufficiale italiano dedicato che mappi senza ambiguità la Specific Action al percorso di selezione dei Comuni.

Le ricerche sul sito del Ministero dell'Interno restituiscono anche trasferimenti nazionali da **77 milioni**, ma riguardano altre misure, ad esempio i servizi sociali comunali di Sicilia e Sardegna. Non devono essere confusi con la Specific Action AMIF.

**Classificazione:** `national_route_watch / unresolved_Italian_selection_mechanism`.

---

## 8. Spiagge Sicure 2026 · controllo da completare

Il Ministero dell'Interno ha destinato **1,5 milioni di euro** a **60 Comuni costieri pre-identificati**, con contributo di **25.000 euro** ciascuno.

La misura è assente dallo snapshot, ma il semplice requisito `Comune costiero <=50.000` non basta: il finanziamento è riservato all'elenco ufficiale dei 60 Comuni e include ulteriori condizioni legate alle annualità precedenti.

Fonte:

https://www.interno.gov.it/it/amministrazione-trasparente/disposizioni-generali/atti-generali/atti-amministrativi-generali/circolari/circolare-24-giugno-2026-prevenzione-e-contrasto-dellabusivismo-commerciale-e-vendita-prodotti-contraffatti-spiagge-sicure-estate-2026-finanziamento

**Classificazione provvisoria:** `scope_review_predetermined_beneficiary_list`.

Non viene contato come falso negativo finché l'elenco ufficiale non è confrontato con i sette Comuni.

---

## 9. Root cause aggiornate

Dopo otto wave il corpus distingue ormai almeno sei problemi strutturali differenti:

1. `topic_level_discovery_gap`;
2. `promotion_after_discovery_gap`;
3. `rolling_technical_support_source_gap`;
4. `financial_instrument_source_gap`;
5. `municipality_scope_fanout_without_condition_evaluation`;
6. `internal_review_queue_noise`.

Questo è il motivo per cui implementare prima della saturazione sarebbe stato prematuro: un unico aumento di recall non risolverebbe tutti questi fenomeni.

---

## Decisione

**Audit ancora non saturo. Implementazione congelata. Sweep puliti: 0/2.**

La Wave 8 aggiunge finding correnti sufficienti a respingere qualsiasi ipotesi di chiusura del gate.

### Prossimo sweep, ancora solo audit

1. completare una **matrice sistematica dei sette Comuni** sulle opportunità pubbliche correnti, verificando soglie demografiche, geografia e requisiti condizionali;
2. chiudere l'elenco **Spiagge Sicure 2026** contro i sette Comuni;
3. continuare la route italiana **AMIF**;
4. completare `internal_review` dopo dedup canonico;
5. solo a quel punto eseguire un nuovo sweep indipendente di saturazione.

Solo un'intera passata senza nuovi gap correnti azionabili farà avanzare il contatore a **1/2**.
