# Radar Opportunità · audit · Wave 16

**Data:** 8 settembre 2026  
**PR:** #161  
**Tipo:** `independent_full_corpus`  
**Stato:** `open_not_saturated`  
**Implementazione:** congelata  
**Sweep puliti consecutivi:** **0/2**

## Metodo

Wave 16 è un nuovo full-corpus sweep indipendente con ordine degli oracle diverso dalle Wave 14-15: prima canali nazionali e regionali, poi strumenti UE a livello di progetto, infrastrutture di ricerca, Mission Ocean, Interreg e forme di supporto non monetario.

Il corpus precedente e lo snapshot `data/opportunity-daily-public.json` sono stati consultati soltanto dopo l'emersione dei candidati, per deduplicazione, verifica della scheda canonica, `municipality_eligibility`, coverage rule e lifecycle.

## 1. Nuovo gap corrente · IRISCC 4th Open Call for Access

La quarta call IRISCC è aperta dal **20 luglio 2026** al **15 ottobre 2026**.

IRISCC invita esplicitamente anche le **public authorities** a richiedere accesso sponsorizzato alle infrastrutture europee di ricerca sui rischi climatici. Il supporto può comprendere:

- laboratori, field stations e strumentazione;
- dataset e servizi digitali;
- supporto tecnico/scientifico degli esperti IRISCC;
- per proposte on-site o ibride approvate, sostegno a viaggio/sussistenza fino a **2.000 euro**, secondo le regole della call.

Non è un grant comunale generalista: l'azione è concretamente utile quando il Comune dispone di un caso d'uso credibile su hazard, esposizione, vulnerabilità, adattamento o valutazione del rischio climatico.

**Radar:** assente dallo snapshot e dal corpus Wave 1-15.  
**Classificazione:** `current_conditional_applicant_false_negative`.  
**Detection lag al reference snapshot:** **49 giorni**.  
**Root cause:** `EU_project_research_infrastructure_access_call_gap`.

Fonti ufficiali:

- https://www.iriscc.eu/
- https://www.iriscc.eu/sponsored-access

---

## 2. Nuovo gap strutturale · CO-WATERS Coalition

La Coalition CO-WATERS, avviata nel marzo 2026 nell'ambito della Mission Ocean, è una struttura corrente rivolta a waterfront authorities e partner locali, inclusi città e regioni.

I servizi comprendono:

- networking e peer learning;
- capacity building e training;
- supporto al coinvolgimento di cittadini e stakeholder;
- funding advice;
- accompagnamento all'implementazione di obiettivi Mission Ocean e iniziative locali sull'acqua.

È distinta dalle future EOI di assistenza tecnica già tracciate nel corpus Mission Ocean: la Coalition è un canale operativo permanente di supporto e collaborazione.

**Radar:** assente dallo snapshot e dal corpus Wave 1-15.  
**Classificazione:** `rolling_structural_gap`.  
**Root cause:** `Mission_Ocean_coalition_capacity_building_gap`.

Fonti ufficiali:

- https://co-waters.eu/
- portale Commissione europea · Mission Restore our Ocean and Waters

---

## 3. Nuovo gap corrente · CO-WATERS Blue Climathons 2026

Il **31 agosto 2026** CO-WATERS ha aperto una call specifica per organizzare fino a **20 Blue Climathons**.

Possono candidarsi membri della Coalition — città, regioni, isole, porti e altri soggetti pertinenti — che dispongano di una concreta sfida locale legata all'acqua.

La scadenza è il **27 settembre 2026**.

Il supporto non consiste in un contributo ai costi dell'evento, ma in assistenza gratuita per:

- definizione della challenge;
- struttura e facilitazione dell'evento;
- mobilitazione dei partecipanti;
- comunicazione e promozione;
- approcci di fundraising;
- accompagnamento continuo da parte degli esperti e della community degli organizzatori.

Per il perimetro Versilia il fit più immediato riguarda i Comuni costieri; per gli altri Comuni deve essere dimostrata una challenge waterfront/acqua coerente e l'adesione alla Coalition.

**Radar:** assente dallo snapshot e dal corpus Wave 1-15.  
**Classificazione:** `current_conditional_beneficiary_false_negative`.  
**Detection lag al reference snapshot:** **7 giorni**.  
**Root cause:** `EU_project_city_support_open_call_gap`.

Fonte ufficiale:

- https://co-waters.eu/

---

## 4. Correzione lifecycle · SAI 2026

Il primo controllo degli avvisi SAI poteva far pensare a tre call già aperte. La verifica della fonte istituzionale completa corregge questa interpretazione.

Le tre procedure finanziano complessivamente **3.202 nuovi posti**:

- 2.402 posti ordinari;
- 500 posti per MSNA;
- 300 posti per persone con disagio mentale o sanitario.

Gli Enti locali possono presentare progetti singolarmente o in forma associata, ma la presentazione delle domande decorre dal **15 settembre 2026** e termina il **10 novembre 2026 alle 18:00**.

Alla data dell'audit, **8 settembre 2026**, le tre procedure sono quindi:

`announced_upcoming`

non `current_false_negative`.

Non incidono sul counter di saturazione Wave 16.

---

## 5. Replay storico · Fondo per minori allontanati dalla famiglia

Il Ministero dell'Interno ha attivato nel 2026 un fondo nazionale da **250 milioni di euro** destinato ai Comuni che sostengono spese per l'assistenza a minori allontanati dal nucleo familiare con provvedimento dell'autorità giudiziaria.

L'accesso richiedeva una dichiarazione telematica comunale entro 30 giorni dalla pubblicazione del decreto in Gazzetta Ufficiale nell'aprile 2026.

La finestra era quindi già chiusa prima dell'avvio pubblico del Radar.

**Classificazione:** `historical_pre_launch_gap`.

Non modifica il gate corrente ma deve entrare nel replay e nelle sentinelle di ciclo future.

Fonte ufficiale:

- https://dait.interno.gov.it/finanza-locale/notizie/comunicato-del-14-aprile-2026

---

## 6. Correzione dell'audit · Bando parcheggi 2026

Wave 15 aveva registrato il **Bando parcheggi 2026** come `announced_upcoming`, assumendo erroneamente una futura apertura della finestra.

Il controllo diretto sullo snapshot completo mostra invece la scheda canonica:

- `opp-7fbab3d295ee2d`;
- `rule_id = rt-parcheggi-2026`;
- stato `open`;
- pubblicazione 12 agosto 2026;
- scadenza 30 novembre 2026;
- Comuni toscani come beneficiari diretti.

La classificazione corretta è quindi:

`captured`

La correzione non incide sul gate; elimina soltanto un errore di lifecycle dell'audit.

---

## 7. Controlli negativi e di perimetro

### Interreg Italy-Croatia · 4th Call 2026

La call è corrente e consente la partecipazione di autorità locali, ma il programme area italiano non include la Toscana/Versilia.

**Classificazione:** `correctly_excluded_geography`.

### MIT · Fondo investimenti stradali piccoli Comuni 2026

La nuova annualità è stata annunciata, ma il Radar dispone già della coverage `mit-fondo-piccoli-comuni-2026` in lifecycle `announced_upcoming`.

**Classificazione:** `captured_announced_upcoming`.

### CEF Transport 2026

Già presente nell'`auditReview` dello snapshot. La partecipazione di un Comune richiede un progetto TEN-T/CEF qualificante e la necessaria route nazionale.

**Classificazione:** `scope_review_project_promoter_control`.

### Mission Ocean · Associated Regions

Il directory ufficiale è stato ricontrollato. Le recenti call Associated Regions individuate risultano chiuse; non è emersa una nuova call corrente per il perimetro Versilia oltre alle famiglie già presenti nel corpus.

### Servizio Civile Universale 2026

La finestra è già trattenuta nell'`auditReview` del Radar. La presentazione dipende dall'accreditamento/iscrizione all'Albo SCU e non è stata acquisita nuova evidenza di accreditamento dei sette Comuni.

**Classificazione:** `scope_review_conditional_accreditation_route`.

---

## Effetto sul gate

Wave 16 è un **full-corpus independent sweep valido ma non pulito**.

Nuovi finding correnti/strutturali:

1. IRISCC · 4th Open Call for Access;
2. CO-WATERS · Coalition;
3. CO-WATERS · Blue Climathons 2026.

La presenza di uno solo di questi casi sarebbe sufficiente a interrompere una sequenza pulita.

**Gate: 0/2.**

L'implementazione resta congelata.

Il prossimo passo è un nuovo full-corpus sweep indipendente, Wave 17, con seed e ordine degli oracle nuovamente diversi. Se Wave 17 fosse pulita, il counter salirebbe soltanto a **1/2**; servirebbe ancora un secondo sweep indipendente consecutivo pulito prima di iniziare l'hardening.

Nessuna modifica a motore, configurazione o discovery. Nessun merge e nessuna pubblicazione.
