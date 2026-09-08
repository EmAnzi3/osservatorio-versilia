# Radar Opportunità · audit · Wave 17

**Data:** 8 settembre 2026  
**PR:** #161  
**Tipo:** `independent_full_corpus`  
**Stato:** `open_not_saturated`  
**Implementazione:** congelata  
**Sweep puliti consecutivi:** **0/2**

## Metodo

Wave 17 ha cambiato nuovamente il seed rispetto alle Wave precedenti: prima strumenti UE orizzontali di riforma, finanza energetica, project-development e matchmaking degli investimenti; poi canali nazionali specializzati e Regione Toscana.

Il corpus Wave 1-16 e lo snapshot di riferimento sono stati usati solo dopo l'emersione dei candidati per controllare titolo alternativo, scheda canonica, coverage rule, `internal_review/auditReview` e lifecycle.

## 1. Nuovo gap corrente instradato · Technical Support Instrument 2027

La Commissione ha aperto il ciclo **TSI 2027** il **12 giugno 2026**. La scadenza è il **31 ottobre 2026**.

La call stabilisce espressamente che possono formulare richieste:

- autorità nazionali;
- autorità regionali;
- **autorità locali**.

Il supporto può coprire l'intero ciclo della riforma: progettazione, analisi, implementazione, change management e valutazione.

La route non è però un grant comunale diretto. Le beneficiary authorities possono preparare e gestire la richiesta nel portale, ma soltanto la **National Coordinating Authority** dello Stato membro può inviarla formalmente alla Commissione. La lista corrente della Commissione identifica per l'Italia l'Autorità nazionale di coordinamento presso il **Ministero per il Sud**.

Per i sette Comuni l'ammissibilità formale come autorità locali è quindi generale, mentre l'azione concreta dipende da:

- presenza di una riforma o fabbisogno di assistenza coerente;
- qualità della proposta;
- coordinamento e prioritizzazione nazionale.

**Radar:** assente dallo snapshot e dal corpus Wave 1-16.  
**Classificazione:** `current_national_route_technical_support_false_negative`.  
**Severità:** `critical`.  
**Detection lag al reference snapshot:** **87 giorni**.  
**Root cause:** `EU_routed_reform_technical_support_family_gap`.

Fonti ufficiali:

- https://reforms-investments.ec.europa.eu/technical-support-instrument-2027-call_en
- https://reforms-investments.ec.europa.eu/technical-support-instrument-0/tsi-how-it-works_en
- https://commission.europa.eu/funding-and-tenders/find-funding/eu-funding-programmes/technical-support-instrument/tsi-national-coordinating-authorities-contacts_en
- https://www.politicheeuropee.gov.it/it/attivita/strumento-di-supporto-tecnico-alle-riforme/

---

## 2. Nuovo gap strutturale · European Energy Efficiency Fund · direct financing

Il **European Energy Efficiency Fund (eeef)** è un veicolo europeo di finanziamento per:

- efficienza energetica;
- rinnovabili di piccola scala;
- trasporto urbano pulito.

La pagina ufficiale identifica espressamente come beneficiari finali le **autorità municipali, locali e regionali**.

Gli investimenti diretti si collocano normalmente nella fascia **5-25 milioni di euro** e possono utilizzare, secondo il progetto, debito senior, strumenti mezzanine, leasing e altre strutture finanziarie.

Non è un contributo a fondo perduto: serve un investimento economicamente sostenibile e coerente con i criteri del Fondo.

**Radar:** assente dallo snapshot e dal corpus precedente.  
**Classificazione:** `rolling_financing_structural_gap`.  
**Severità:** `high`.  
**Root cause:** `rolling_public_energy_finance_product_gap`.

Fonte ufficiale:

- https://www.eeef.lu/eligible-investments.html

---

## 3. Nuovo gap strutturale · eeef Technical Assistance Facility

Separatamente dal finanziamento, eeef mantiene una **Technical Assistance Facility** direttamente accessibile ai soggetti pubblici.

La pagina corrente indica tra gli eligible applicants:

- Regions;
- **City Councils**;
- Universities;
- public hospitals;
- altri enti pubblici UE.

Il supporto riguarda la preparazione di programmi di investimento in efficienza energetica, piccole rinnovabili e trasporto pubblico urbano e può comprendere:

- studi di fattibilità e audit energetici;
- verifica della sostenibilità economica;
- strutturazione di gare ESCO/PPP;
- supporto legale;
- costi del personale del beneficiario ammessi secondo le condizioni del programma.

Criteri principali:

- programma di investimento superiore a **5 milioni di euro**;
- leverage >20;
- almeno **30%** di risparmio di energia primaria/CO2.

La call è **senza scadenza**, first-come-first-served, subordinata alla disponibilità delle risorse e al fit del progetto.

La facility è oggi co-supportata attraverso un contratto EIB ELENA, ma rimane una **route applicativa distinta**, con propri criteri, application form, valutazione e award process. Per questo la generica copertura ELENA non è sufficiente a considerarla catturata.

**Radar:** assente.  
**Classificazione:** `rolling_structural_gap`.  
**Severità:** `critical`.  
**Root cause:** `named_project_development_service_gap`.

Fonte ufficiale:

- https://www.eeef.lu/eeef-ta-facility.html

---

## 4. Nuovo gap strutturale · InvestEU Portal

L'**InvestEU Portal** è una componente distinta del programma InvestEU, insieme al Fund e all'Advisory Hub.

È un marketplace europeo che consente ai project promoter di pubblicare gratuitamente progetti d'investimento per ottenere visibilità presso investitori internazionali.

Possono essere pubblicati progetti promossi da una **persona giuridica pubblica o privata** in regola e conformi ai criteri di ammissione.

La Commissione può inoltre trasmettere i progetti:

- agli implementing partners InvestEU;
- all'InvestEU Advisory Hub, quando pertinente e richiesto.

Non garantisce finanziamento e non è un grant, ma è una route operativa continuativa di **investment matchmaking**. È quindi distinta dal già noto InvestEU Advisory Hub.

**Radar:** assente.  
**Classificazione:** `rolling_structural_gap`.  
**Severità:** `medium`.  
**Root cause:** `investment_matchmaking_named_service_gap`.

Fonti ufficiali:

- https://investeu.europa.eu/investeu-programme/investeu-portal_en
- https://investeu.europa.eu/investeu-programme/investeu-portal/frequently-asked-questions-about-investeu-portal_en

---

## 5. Controlli di perimetro

### InvestEU Fund

Il Fund può finanziare final recipients pubblici attraverso implementing partners. In questa wave non viene però trasformato in una scheda comunale generica: vanno auditati i singoli prodotti degli implementing partners quando hanno un percorso concreto per Enti territoriali.

**Classificazione:** `scope_review_generic_financing_framework`.

### LSU · Comuni sotto 5.000 abitanti

Gli avvisi correnti del Ministero del Lavoro riguardano pagamenti 2026 verso Comuni già inseriti negli elenchi per la stabilizzazione di LSU, non una nuova finestra competitiva.

**Classificazione:** `predetermined_or_payment_lifecycle_control`.

### Rottamazione enti territoriali 2026

La procedura riguarda l'adesione dei debitori alla definizione agevolata di carichi degli enti territoriali. Non è un'opportunità di finanziamento/supporto con il Comune come beneficiario Radar.

**Classificazione:** `correctly_excluded_non_municipal_applicant_opportunity`.

### Regione Toscana

Il nuovo controllo su bandi aperti e PR FSE+ ha restituito opportunità comunali già presenti nel corpus: Nidi gratis, Toscana Diffusa, Mercati rionali, Buoni scuola, Amianto e Parcheggi.

Non è emerso un nuovo current actionable gap regionale.

### Suvignano · Consulta

La procedura corrente è rivolta a soggetti rappresentativi del Terzo Settore, non ai Comuni.

**Classificazione:** `correctly_excluded_eligibility`.

### Apprendistato duale

La struttura del soggetto proponente richiede partnership formativa con lead e soggetti accreditati specifici; non è stato stabilito un ruolo comunale diretto.

**Classificazione:** `correctly_not_auto_promoted_municipality`.

---

## Effetto sul gate

Wave 17 è un **full-corpus independent sweep valido ma non pulito**.

Nuovi finding:

1. Technical Support Instrument 2027;
2. eeef direct financing;
3. eeef Technical Assistance Facility;
4. InvestEU Portal.

**Gate: 0/2.**

L'implementazione resta congelata.

Il prossimo passaggio è Wave 18, con ordine degli oracle ancora diverso. Se Wave 18 fosse pulita, produrrebbe soltanto il primo credito verso il gate (`1/2`). Servirebbe comunque un'ulteriore Wave indipendente consecutiva pulita per iniziare l'hardening.

Nessuna modifica a motore/config/discovery. Nessun merge e nessuna pubblicazione.
