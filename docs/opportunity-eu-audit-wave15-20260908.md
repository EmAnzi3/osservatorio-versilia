# Radar Opportunità · audit · Wave 15

**Data:** 8 settembre 2026  
**PR:** #161  
**Tipo sweep:** `independent_full_corpus`  
**Stato:** `open_not_saturated`  
**Implementazione:** congelata  
**Sweep puliti consecutivi validi:** **0/2**

## Esito

Wave 15 è un **full-corpus independent sweep valido**, ma **non è pulito**.

La discovery è ripartita da oracle esterni, con un ordine diverso rispetto a Wave 14. Le Wave precedenti e lo snapshot Radar sono stati consultati solo dopo l'emersione dei candidati, per verificare scheda canonica, `municipality_eligibility`, `internal_review`/`auditReview`, duplicati, lifecycle e reale applicabilità ai sette Comuni.

Sono emersi **due nuovi gap strutturali correnti**:

1. **Agenzia del Demanio · trasferimento gratuito di immobili dello Stato agli Enti territoriali**;
2. **EU Mission Adaptation · Mission Community / Roster of Experts**.

Sono inoltre emersi due replay storici forti — **Pelagos 2026-2028** e **Fondo attività socio-educative a favore dei minori 2026 / centri estivi** — e un controllo storico di scope su **Best Tourism Villages 2026**.

Poiché Wave 15 contiene nuovi current actionable gap, il gate resta **0/2**.

---

## 1. Agenzia del Demanio · trasferimento gratuito di immobili dello Stato

Fonte ufficiale primaria:

https://www.agenziademanio.it/it/in-evidenza/trasferimentoimmobiliEETT/

L'Agenzia del Demanio presenta esplicitamente la procedura come **“una opportunità per gli Enti Territoriali”**.

L'art. 15-bis del D.L. 13/2023 consente a:

- Regioni;
- **Comuni**;
- Province;
- Città metropolitane

di richiedere il trasferimento **in proprietà e a titolo gratuito** di determinate categorie di immobili statali.

La procedura riguarda immobili appartenenti al demanio storico-artistico o al patrimonio disponibile dello Stato gestito dall'Agenzia, quando interessati da progetti di riqualificazione per scopi istituzionali o sociali finanziati o candidati a finanziamento, anche parziale, tramite:

- PNRR;
- PNC;
- PNIEC.

Sono previste esclusioni normative, tra cui beni già destinati a finalità statali o coinvolti in procedure di valorizzazione/dismissione.

Le richieste motivate devono essere inviate via PEC alla Direzione territoriale competente entro **31 dicembre 2026**.

**Stato Radar:** assente dallo snapshot e dal corpus Wave 1-14.  
**Classificazione:** `rolling_structural_gap`.  
**Severità:** `high`.  
**Municipality role:** `direct_municipality_requester_for_free_state_asset_transfer`.  
**Root cause:** `state_property_transfer_instrument_gap`.

Tutti e sette i Comuni rientrano formalmente nella classe ammessa. L'opportunità non deve però essere presentata come automaticamente azionabile: serve individuare un bene statale trasferibile e un progetto di riqualificazione coerente con i requisiti della norma.

Non è un grant cash, ma è un beneficio patrimoniale diretto e potenzialmente rilevante per un ente locale; rientra quindi nel perimetro Radar allo stesso modo in cui l'audit ha già incluso assistenza tecnica, strumenti finanziari e altri supporti non cash direttamente azionabili.

---

## 2. EU Mission Adaptation · Mission Community / Roster of Experts

Fonti ufficiali:

- https://mission-adaptation-portal.ec.europa.eu/news-events/news/eu-mission-adaptation-launches-call-experts-join-new-roster-experts-2026-06-15_en
- https://mission-adaptation-portal.ec.europa.eu/mission-community_en

Il **Roster of Experts** è stato annunciato il **15 giugno 2026** come strumento della Mission on Adaptation per rafforzare knowledge exchange, collaborazione e supporto all'implementazione.

La pagina ufficiale spiega che il Roster collega:

- Regional and Local Authorities;
- Mission Projects;
- altri membri della Mission Community

con esperti selezionati su temi di adattamento climatico.

Una volta operativo, il soggetto che cerca supporto può presentare una breve richiesta e MIP4Adapt facilita l'introduzione con gli esperti pertinenti.

La pagina corrente della **EU Mission Adaptation Community** conferma che la Community è aperta a qualsiasi organizzazione impegnata nello sviluppo della resilienza climatica e che i membri possono:

- richiedere il collegamento con un membro del Roster of Experts;
- partecipare a thematic working groups;
- accedere ad attività di capacity building e matchmaking;
- costruire alleanze e partnership per nuovi progetti;
- partecipare a spazi strutturati di coordinamento e scambio.

**Stato Radar:** assente dallo snapshot e dal corpus Wave 1-14.  
**Classificazione:** `rolling_structural_gap`.  
**Severità:** `high`.  
**Municipality role:** `direct_local_authority_community_member_requesting_expert_connection_or_using_structured_capacity_building`.  
**Root cause:** `Mission_Adaptation_community_and_expert_matchmaking_gap`.

### Distinzione dalla Citizen Engagement Hotline

Questo finding **non duplica** la Wave 13.

La `Citizen Engagement Hotline` offre coaching specialistico sul coinvolgimento di cittadini e stakeholder ed è aperta a tutte le autorità regionali/locali europee.

La `Mission Community / Roster of Experts` è invece un canale più ampio di expert matchmaking, capacity building, working groups, networking e costruzione di partnership.

### Lifecycle caveat

L'annuncio del 15 giugno indicava il lancio iniziale del Roster genericamente in **settembre 2026**, senza giorno preciso. Per questo Wave 15 non calcola un detection lag puntuale. La current actionability è invece sostenuta dalla pagina corrente della Mission Community, che indica espressamente la possibilità per i membri di richiedere una connessione con un membro del Roster.

---

## 3. Replay storico · Pelagos 2026-2028

Fonti ufficiali:

- https://pelagos-sanctuary.org/it/bando-per-il-finanziamento-di-progetti-nellambito-della-carta-di-partenariato-dellaccordo-pelagos-2026-2028/
- https://www.statocitta.pcm.gov.it/home/notizie-e-comunicati/2026/bando-pelagos-2026-2028-aperte-le-candidature-dei-comuni/

Il bando MASE/DG Tutela della Biodiversità e del Mare era rivolto ai **Comuni aderenti alla Carta di Partenariato dell'Accordo Pelagos** in regola con il rinnovo oppure a nuovi aderenti con delibera comunale e successivo parere favorevole della DG competente.

Scadenza: **18 agosto 2026 alle 23:59**.

È quindi chiuso prima della messa online operativa del Radar pubblico e non è un current runtime gap dell'8 settembre.

**Classificazione:** `historical_pre_launch_gap`.

### Applicabilità Versilia

Per **Viareggio** l'applicabilità è dimostrata direttamente da un atto ufficiale del Comune di Vecchiano: la delibera di Giunta n. 128 del 17 agosto 2026 approva una candidatura congiunta con il **Comune di Viareggio** per il progetto `WISPO Viareggio/Vecchiano`.

Fonte comunale:

https://www.halleyegov.it/c050037/zf/index.php/atti-amministrativi/delibere/dettaglio/atto/G5WpVd0TEUT0-A

Per Pietrasanta è stata trovata evidenza di rinnovo del partenariato, ma in questa Wave non è stato dimostrato il definitivo parere MASE utile alla data di scadenza. Non viene quindi dichiarata eleggibilità certa.

---

## 4. Replay storico · Fondo attività socio-educative a favore dei minori 2026

Fonti ufficiali PCM/Dipartimento Politiche per la famiglia:

- https://famiglia.governo.it/it/politiche-e-attivita/comunicazione/notizie/avviso-finanziamento-ai-comuni-per-attivita-socio-educative-a-favore-dei-minori-annualita-2026/
- https://www.famiglia.governo.it/it/politiche-e-attivita/finanziamenti-avvisi-e-bandi/fondo-per-le-attivita-socio-educative-a-favore-dei-minori-anno-2026/introduzione/

La legge di bilancio 2026 ha istituito un Fondo da **60 milioni di euro annui** destinato a iniziative comunali per:

- centri estivi;
- servizi socio-educativi territoriali;
- centri con funzione educativa e ricreativa per minori.

I Comuni interessati dovevano manifestare l'interesse sulla piattaforma dedicata tra **8 e 28 maggio 2026**.

Il perimetro comprendeva i Comuni italiani, con esclusione dei territori delle Province autonome di Trento e Bolzano. Le attività finanziate devono svolgersi dal 1° giugno al 31 dicembre 2026.

Lo snapshot Radar contiene solo un vecchio frammento discovery relativo ai **centri estivi 2022**, non l'opportunità comunale 2026.

**Classificazione:** `historical_pre_launch_gap`.  
**Municipality role:** `direct_municipality_manifestation_of_interest`.

Tutti e sette i Comuni Versilia ricadevano formalmente nel perimetro geografico nazionale della misura durante la finestra di candidatura.

---

## 5. Replay storico · Best Tourism Villages 2026

Fonte ufficiale Ministero del Turismo:

https://www.ministeroturismo.gov.it/un-tourism-al-via-la-6a-edizione-di-best-tourism-villages/

La procedura italiana della sesta edizione di `Best Tourism Villages` è stata pubblicata l'**11 maggio 2026** e chiudeva il **25 maggio 2026**.

Potevano essere candidati Comuni, borghi o destinazioni con:

- popolazione inferiore a 15.000 abitanti;
- requisiti di sostenibilità, valorizzazione del patrimonio e sviluppo turistico locale.

La route italiana prevedeva prima la manifestazione di interesse attraverso la Regione e poi la candidatura nazionale da parte del Ministero, entro il limite UN Tourism di otto candidature per Paese.

Fra i benefici figurano visibilità internazionale e partecipazione al network; le destinazioni ad alto potenziale possono accedere all'`Upgrade Programme` con supporto tecnico.

**Classificazione prudente:** `historical_scope_review`.

Almeno Stazzema è già documentato nelle Wave precedenti come Comune sotto 5.000 abitanti e quindi supera certamente il requisito demografico, ma questa Wave non ha ri-validato per i sette Comuni tutti i criteri qualitativi della destinazione. Non viene quindi contato come falso negativo comunale definitivo.

---

## 6. Controlli canonici e di scope

### Buoni scuola Toscana 2026

Un oracle esterno aveva fatto riemergere il bando con deadline **25 settembre 2026**.

Il controllo sul completo `opportunity-daily-public.json` ha però trovato la scheda canonica:

- `opp-f167a60a4b3c05`;
- `rule_id = rt-buoni-scuola-2026`;
- Comune/Unione come soggetto proponente.

**Classificazione:** `captured`.

Non è un nuovo gap Wave 15.

### Emergenza abitativa Toscana

Anche la manifestazione per il reperimento di patrimonio immobiliare da destinare a emergenza abitativa/ERS è già canonica:

- `opp-c83615a316d655`;
- `rule_id = rt-emergenza-abitativa-2026`;
- `municipality_role = direct_applicant`.

**Classificazione:** `captured`.

### Servizio Civile Universale · programmi e progetti 2026

La finestra è corrente, ma la candidatura è riservata agli enti iscritti/accreditati all'Albo SCU.

Lo snapshot contiene già il caso in `auditReview/internal_review`, con l'eleggibilità dei sette Comuni da risolvere.

**Classificazione:** `scope_review_conditional_accreditation_route`.  
**Non conta come nuovo current gap.**

### CEF Transport 2026

Anche CEF Transport è già presente in `auditReview`.

L'ammissibilità di un ente pubblico non basta: servono un progetto coerente con TEN-T/CEF, ruolo di promotore e, dove previsto, supporto nazionale.

**Classificazione:** `scope_review_project_promoter_control`.

### Bando parcheggi Toscana 2026

La pagina regionale può apparire come `Aperto`, ma la finestra effettiva parte il **14 settembre 2026**.

Alla data Wave 15, 8 settembre, resta:

`announced_upcoming`.

### MASE · supporto città a emissioni zero

La misura riguarda il gruppo delle nove città italiane con Mission Label. Nessuno dei sette Comuni Versilia appartiene al gruppo.

**Classificazione:** `correctly_excluded_eligibility`.

---

## Effetto sul gate

Wave 15 è un full-corpus independent sweep valido ma **dirty**.

Nuovi gap correnti/strutturali:

1. `agenzia-demanio-free-transfer-15bis-2026`;
2. `mip4adapt-mission-community-roster-experts`.

Replay storici aggiuntivi:

- `mase-pelagos-2026-2028`;
- `pcm-famiglia-attivita-socio-educative-minori-2026`.

Controllo storico di scope:

- `ministero-turismo-best-tourism-villages-2026`.

**Gate di saturazione: 0/2.**

L'implementazione e l'hardening restano congelati.

Per poter iniziare l'hardening servono ancora **due full-corpus sweep indipendenti consecutivi puliti**. Il prossimo sweep, se privo di nuovi current actionable gap, porterà il counter soltanto a `1/2`; servirà comunque un secondo sweep indipendente pulito consecutivo per arrivare a `2/2`.

Nessuna modifica a motore/config/discovery. Nessun merge e nessuna pubblicazione.
