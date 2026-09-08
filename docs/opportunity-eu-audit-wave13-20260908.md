# Radar Opportunità · audit · Wave 13

**Data:** 8 settembre 2026  
**PR:** #161  
**Tipo:** `post_wave12_evidence_correction_and_oracle_addendum`  
**Stato:** `open_not_saturated`  
**Implementazione:** congelata  
**Sweep puliti consecutivi:** **0/2**

## Scopo

La Wave 13 non è un nuovo sweep indipendente e non può produrre credito verso il gate `2/2`. Serve a preservare la tracciabilità della Wave 12 senza riscriverne retroattivamente l'evidenza: corregge due interpretazioni emerse dopo il commit e aggiunge un ulteriore gap corrente individuato da un oracle Mission Adaptation consultato dopo la chiusura del full-corpus sweep.

## 1. Correzione · EIT Urban Mobility RIS Education Open Call 2027

La Wave 12 classificava correttamente la call come nuovo `current_conditional_beneficiary_false_negative`, ma registrava la scadenza dell'8 settembre 2026.

Il dettaglio ufficiale EIT Urban Mobility indica invece:

- apertura: **1 giugno 2026**;
- scadenza: **16 settembre 2026, ore 17:00 CEST**;
- cities esplicitamente tra i soggetti che possono candidarsi;
- Italia inclusa nei Paesi EIT RIS 2026;
- proposte mono- o multi-beneficiario secondo la linea;
- contributo massimo fino a **300.000 euro** per alcune linee.

Una pagina-directory EIT riportava 8 settembre; ai fini dell'audit prevale la pagina dettagliata della call.

Fonti ufficiali:

- https://www.eiturbanmobility.eu/call-for-proposals/ris-education-open-call-2027/
- https://www.eit.europa.eu/our-activities/opportunities/ris-education-open-call-2027

**Correzione:** `deadlineAt = 2026-09-16T17:00:00+02:00`.

La classificazione di gap corrente **non cambia**.

---

## 2. Correzione · Nidi gratis 2026-2027 · riapertura candidature dei Comuni

La riapertura regionale è reale:

- nuovi Comuni non ancora candidati: richiesta credenziali entro **25 settembre 2026**;
- Comuni già ammessi: documentazione entro **6 ottobre 2026**.

Tuttavia il successivo controllo sull'elenco ufficiale degli enti ammessi ha verificato che sono già presenti:

- Camaiore;
- Forte dei Marmi;
- Massarosa;
- Pietrasanta;
- Seravezza;
- Viareggio.

Stazzema non è stato individuato nell'elenco recuperato e, in questa audit wave, non è stata acquisita evidenza di un servizio 0-3 ammissibile che renda la finestra riaperta concretamente azionabile per il Comune.

Di conseguenza non è corretto contare la riapertura come nuovo gap azionabile del perimetro Versilia.

Fonte ufficiale:

https://www.regione.toscana.it/-/bando-nidi-gratis-2026-2027-per-i-servizi-educativi-rivolto-ai-comuni

**Nuova classificazione:** `lifecycle_reopening_control_no_confirmed_new_versilia_opportunity`.

---

## 3. Nuovo gap corrente · MIP4Adapt Citizen Engagement Hotline

Un oracle indipendente della **EU Mission on Adaptation to Climate Change** ha fatto emergere dopo la chiusura della Wave 12 una forma di supporto non presente nel Radar:

**MIP4Adapt · Citizen Engagement Hotline**.

La Commissione/Mission Adaptation ha annunciato il 17 giugno 2026 che il servizio è disponibile a **tutte le autorità regionali e locali europee**.

Il supporto comprende:

- coaching personalizzato;
- assistenza nella progettazione e gestione di attività di coinvolgimento di cittadini e stakeholder;
- accesso a un pool multilingue di specialisti;
- richiesta on-demand attraverso l'Helpdesk MIP4Adapt.

Non è un grant monetario, ma una opportunità operativa di **technical/capacity-building support** direttamente richiedibile dall'autorità locale. Va distinta dalla Technical Assistance MIP4Adapt principale: quest'ultima ha una diversa struttura di eleggibilità e la call corrente risulta chiusa.

Fonti ufficiali:

- https://mission-adaptation-portal.ec.europa.eu/news-events/news/citizen-engagement-hotline-now-available-all-regional-and-local-authorities-2026-06-17_en
- https://mission-adaptation-portal.ec.europa.eu/mission-knowledge-and-data/mission-support/mip4adapt-technical-assistance_en

**Stato Radar:** assente dallo snapshot e dalla ricerca repository.  
**Classificazione:** `rolling_structural_gap`.  
**Severità:** `high`.  
**Root cause:** `Mission_Adaptation_rolling_support_gap`.

---

## 4. Controlli di perimetro

### Fondo Carnevali Storici 2026 · Viareggio

Il bando ammette Comuni, Fondazioni e Associazioni, ma richiede che il richiedente sia l'organizzatore qualificato del carnevale. Per Viareggio l'organizzatore è la **Fondazione Carnevale di Viareggio**. Il bando non deve quindi essere associato automaticamente al Comune solo per territorialità.

**Classificazione:** `conditional_nonmunicipal_local_control`.

### CEF Energy · 6th CB RES status call

La call è corrente, ma serve un progetto transfrontaliero FER qualificabile, un project promoter e cooperazione tra Stati membri. Non è stata stabilita un'opportunità diretta per uno dei sette Comuni.

**Classificazione:** `scope_review_project_promoter_control`.

---

## Effetto sul gate

La Wave 12 resta un **full-corpus independent sweep non pulito**. La correzione su Nidi gratis elimina un finding sovrastimato, ma non cambia il risultato perché la Wave 12 conserva quattro nuovi casi correnti definitivi:

1. EIT Urban Mobility · RIS Education Open Call 2027;
2. EUI Permanent Call for peer reviewers;
3. EIT Culture & Creativity · NEB Academy | Skills Infrastructure;
4. EIT Culture & Creativity · Delegate Cities & Regions Network.

A questi si aggiunge ora la **MIP4Adapt Citizen Engagement Hotline**.

**Gate: 0/2.**

La Wave 13 non è un nuovo sweep indipendente e non modifica il contatore. Prima dell'hardening restano necessari due full-corpus sweep indipendenti consecutivi senza nuovi gap correnti azionabili.

Nessuna modifica a motore, configurazione o discovery. Nessun merge e nessuna pubblicazione.
