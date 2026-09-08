# Radar Opportunità · Wave 12 · sweep full-corpus indipendente

**Data:** 8 settembre 2026  
**PR:** #161  
**Tipo sweep:** `independent_full_corpus`  
**Stato:** `open_not_saturated`  
**Implementazione:** congelata  
**Sweep puliti consecutivi validi:** **0/2**

## Esito

Lo sweep full-corpus indipendente **non è pulito**.

La ricerca non è partita dall'elenco dei gap delle Wave precedenti. Sono stati interrogati prima oracle istituzionali separati — Commissione/programmi/missioni, CINEA/EISMEA/EACEA, EIT, EUI, Covenant, Interreg, cascade/FSTP, canali nazionali e Regione Toscana — e soltanto dopo l'emersione di un candidato sono stati consultati lo snapshot Radar e le Wave precedenti per deduplicare e classificare.

Sono emerse **due nuove opportunità correnti azionabili**, assenti sia dallo snapshot di riferimento sia dal corpus di audit precedente:

1. **EIT Urban Mobility · RIS Education Open Call 2027**;
2. **European Urban Initiative · Permanent Call for peer reviewers**.

È inoltre emersa una **riapertura corrente della misura Toscana Nidi gratis per i Comuni**, pubblicata lo stesso giorno dello snapshot. La registriamo come problema di lifecycle/reopening, ma senza attribuirla retroattivamente a un miss del motore perché non è stata accertata l'ora di pubblicazione rispetto alla generazione dello snapshot.

Di conseguenza il gate resta **0/2**.

---

## 1. Nuovo falso negativo · EIT Urban Mobility · RIS Education Open Call 2027

Fonte ufficiale EIT:

https://www.eit.europa.eu/our-activities/opportunities/ris-education-open-call-2027

Fonte EIT Urban Mobility:

https://www.eiturbanmobility.eu/call-for-proposals/ris-education-open-call-2027/

La call è aperta dal **1 giugno 2026** e chiude **8 settembre 2026 alle 17:00 CEST**.

Caratteristiche:

- budget EIT indicativo complessivo: circa **2,6 milioni di euro**;
- `RISE1` e `RISE2`: fino a **300.000 euro per progetto**;
- `RISE3`: fino a 180.000 euro;
- `RISE4`: fino a 140.000 euro;
- `RISE5`: fino a 70.000 euro;
- sono ammesse proposte multi-beneficiario e mono-beneficiario;
- fra i soggetti che possono candidarsi la call cita esplicitamente le **cities**;
- per la route mono-beneficiario il soggetto deve provenire da un Paese RIS;
- l'Italia è esplicitamente tra i Paesi ammissibili EIT RIS nel 2026.

Fonte RIS:

https://www.eiturbanmobility.eu/our-community/our-ris-hubs/

Il fatto che le città siano formalmente ammesse non significa promozione indiscriminata dei sette Comuni: il candidato deve dimostrare esperienza precedente e competenze nel capacity building su mobilità urbana e/o innovazione e imprenditorialità.

**Stato Radar:** assente dallo snapshot di riferimento.  
**Classificazione:** `current_conditional_beneficiary_false_negative`.  
**Severità:** `critical`.  
**Root cause:** `EIT_action_level_source_gap`.

Questo finding è particolarmente significativo perché non deriva da una famiglia già in chiusura nelle Wave 9–11: è emerso da un nuovo oracle EIT durante lo sweep full-corpus.

---

## 2. Nuovo rolling structural gap · EUI Permanent Call for peer reviewers

Fonte ufficiale:

https://www.urban-initiative.eu/capacity-building/peer-reviews/ongoing-call-peer-reviews

La **Permanent Call for peer reviewers** è aperta dal **19 novembre 2025** e resta **continuamente aperta**.

Il ruolo è distinto da quello di `city under review` già auditato nelle call periodiche EUI:

- il peer reviewer si candida come individuo;
- può rappresentare **qualsiasi urban authority dell'UE**;
- deve avere esperienza pertinente nella progettazione e attuazione di strategie integrate e place-based;
- la candidatura richiede l'endorsement dell'autorità urbana rappresentata;
- l'attività è capacity building / benchmarking / peer learning, non un normale contributo cash comunale.

Lo snapshot non contiene una scheda corrispondente alla call permanente.

**Classificazione:** `rolling_structural_gap`.  
**Severità:** `high`.  
**Municipality role:** `individual_municipal_representative_endorsed_by_any_EU_urban_authority`.  
**Root cause:** `rolling_capacity_building_opportunity_gap`.

La distinzione lifecycle è essenziale: la call autunnale 2026 per le città sotto revisione apre solo il 1 ottobre, ma la call permanente per peer reviewers è già aperta oggi.

---

## 3. Regione Toscana · Nidi gratis · riapertura candidature dei Comuni

Fonte ufficiale:

https://www.regione.toscana.it/-/bando-nidi-gratis-2026-2027-per-i-servizi-educativi-rivolto-ai-comuni

La Regione Toscana ha pubblicato il **7 settembre 2026** la riapertura delle candidature comunali alla misura Nidi gratis 2026-2027:

- nuovi Comuni non ancora candidati: richiesta delle credenziali entro **25 settembre 2026**;
- Comuni già candidati: invio della documentazione necessaria via PEC entro **6 ottobre 2026**.

Lo snapshot Radar del 7 settembre contiene come controllo soltanto il bando `Nidi gratis` rivolto alle **famiglie**, classificato non operativo per il Comune. Non contiene la nuova finestra comunale.

Tuttavia lo snapshot è stato generato il **7 settembre alle 09:35 UTC** e la pagina regionale espone soltanto la data, non l'ora di pubblicazione. Non è quindi metodologicamente corretto dichiarare che questa riapertura fosse necessariamente disponibile prima dello snapshot.

**Classificazione:** `current_reopened_window_gap_timing_unresolved`.  
**Severità:** `high`.  
**Root cause da presidiare:** `lifecycle_reopening_watch`.

Questo caso dimostra comunque che il Radar deve riconoscere non soltanto `open → closed`, ma anche **riaperture e nuove finestre della stessa misura**.

---

## 4. Mission Adaptation 2026 · chiusura indipendente della matrice residua

Fonte ufficiale Mission Adaptation:

https://research-and-innovation.ec.europa.eu/funding/funding-opportunities/funding-programmes-and-open-calls/horizon-europe/eu-missions-horizon-europe/adaptation-climate-change_en

La call apre il 4 febbraio e chiude il **23 settembre 2026**. Lo sweep indipendente ha verificato anche i topic non già chiusi puntualmente dalle Wave precedenti.

### CLIMA-01 · National Adaptation Hubs

`HORIZON-MISS-2026-01-CLIMA-01`

Il topic costruisce hub nazionali che collegano livello nazionale, regioni e attori locali e può usare Financial Support to Third Parties. Non è corretto trasformarlo in una scheda di candidatura diretta generica per ciascun Comune.

**Classificazione:** `cascade_prospective_gap_national_hub_watch`.

### CLIMA-02 · Facilitating implementation of actionable solutions

`HORIZON-MISS-2026-01-CLIMA-02`

Le autorità regionali e locali sono il target principale delle soluzioni, ma il Work Programme specifica che **non sono attese nel consorzio principale**.

**Classificazione:** `end_user_no_auto_promotion`.

### CLIMA-03 · Climate services

`HORIZON-MISS-2026-01-CLIMA-03`

Possibile ruolo di end-user/stakeholder, ma nessun requisito comunale come beneficiario stabilito.

**Classificazione:** `end_user_scope_no_auto_promotion`.

### CLIMA-04 · DRM + climate adaptation

`HORIZON-MISS-2026-01-CLIMA-04`

Le autorità regionali/locali sono destinatari delle linee guida, raccomandazioni e capacità di resilienza sviluppate dal progetto. Nessun requisito universale di Comune beneficiario.

**Classificazione:** `end_user_policy_target_no_auto_promotion`.

### CLIMA-05 e CLIMA-07

Entrambi sono stati riscoperti dall'oracle indipendente ma erano già nel corpus:

- `CLIMA-05`: già `current_topic_level_promotion_gap`;
- `CLIMA-07`: già `cascade_prospective_gap` per future sovvenzioni FSTP alle amministrazioni locali/regionali.

Sono quindi controlli positivi di rediscovery, non finding nuovi.

### CLIMA-06

La resilienza di vie navigabili interne e infrastrutture correlate non è automaticamente applicabile ai sette Comuni senza un asset/ruolo pertinente.

**Classificazione:** `correctly_not_auto_promoted_for_versilia`.

---

## 5. CEF Energy · CB RES status 2026

Fonte CINEA:

https://cinea.ec.europa.eu/news-events/news/cef-energy-6th-call-cross-border-renewable-energy-projects-obtain-status-launched-2026-06-29_en

La sesta e ultima call 2021-2027 per ottenere lo status **Cross-Border Renewable Energy Project** è aperta fino al **6 ottobre 2026**.

Lo status è prerequisito per poter concorrere successivamente al finanziamento CEF Energy per studi e lavori. Tuttavia la candidatura riguarda promotori di veri progetti FER transfrontalieri con requisiti e cooperazione internazionale specifici.

**Classificazione:** `scope_review_conditional_project_promoter`.

Non va quindi aggiunta indiscriminatamente ai sette Comuni.

---

## 6. Controlli che NON generano nuovi gap correnti

### EIT Citizens on the Move 2026

Opportunità pertinente anche a civil servants delle città e con supporto RIS, ma i due round 2026 si sono chiusi il **13 maggio** e l'**8 luglio**.

**Classificazione:** `historical_current_year_sentinel`.

### I3 Capacity Building 2026 · CAP2b

L'oracle EISMEA l'ha fatto emergere indipendentemente, ma la call è chiusa dal **19 marzo 2026**.

**Classificazione:** `historical_prelaunch_sentinel`.

### Covenant Peer Review Programme 2026

Destinato a Covenant Coordinators/Supporters e chiuso a maggio 2026, non a tutti i Comuni firmatari in modo generico.

**Classificazione:** `historical_closed_and_scope_limited`.

### Interreg Italia-Croazia · 4th Call

Call corrente, ma la Provincia di Lucca/Toscana non rientra nell'area italiana ammissibile.

**Classificazione:** `correctly_excluded_geography`.

### TRUNSPORT, SUNDANSE, SPACE4Cities, I3 INV1/INV2a, IUCN Rapid-Response Fund

Sono stati tutti riscoperti attraverso oracle indipendenti ma risultano già documentati nelle Wave precedenti. Servono quindi come **positive controls** sulla qualità dello sweep, non come nuovi finding.

### Mission Ocean downstream community assistance

La procedura a monte è già nota. Il contractor dovrà selezionare almeno 50 comunità tra regioni, città, autorità fluviali/idriche e autorità portuali. La futura EOI per le comunità resta `downstream_EOI_expected` e non è stata trovata come pubblicata al momento dello sweep.

---

## 7. Sentinelle future

### Fondo Carnevali Storici 2026

La finestra prevista è **15 settembre – 15 ottobre 2026**. Non è ancora aperta l'8 settembre. L'eleggibilità include enti che organizzano carnevali storici qualificati; per Viareggio occorre distinguere Comune e Fondazione Carnevale di Viareggio come soggetto organizzatore/candidato.

**Classificazione:** `announced_upcoming_conditional_affiliated_entity`.

### CERV Remembrance 2026

Il calendario è stato spostato rispetto alle precedenti indicazioni. La call non è trattata come runtime miss corrente all'8 settembre.

**Classificazione:** `announced_upcoming_calendar_sentinel`.

---

## Conclusione

La prima vera passata full-corpus indipendente **fallisce il clean gate** perché individua due opportunità correnti realmente nuove:

- `eit-urban-mobility-ris-education-2027`;
- `eui-permanent-peer-reviewers`.

La riapertura Nidi gratis aggiunge un terzo finding lifecycle, con cautela temporale.

**Gate dopo Wave 12: `0/2`.**

L'hardening del motore resta congelato. Il prossimo sweep indipendente dovrà partire da oracle diversi o da percorsi diversi dentro gli stessi ecosistemi, non dalla checklist di Wave 12. Soltanto un passaggio full-corpus senza nuovi current actionable gap potrà portare il contatore a `1/2`.

Nessun file del motore, configurazione discovery o output pubblico è stato modificato in questa Wave.
