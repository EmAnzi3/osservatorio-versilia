# Radar Opportunità · audit · Wave 14

**Data:** 8 settembre 2026  
**PR:** #161  
**Tipo sweep:** `independent_full_corpus`  
**Stato:** `open_not_saturated`  
**Implementazione:** congelata  
**Sweep puliti consecutivi validi:** **0/2**

## Esito

Wave 14 è un nuovo **full-corpus independent sweep** e **non è pulito**.

La discovery è partita da oracle esterni istituzionali e progettuali, non dall'elenco delle opportunità già note. Solo dopo l'emersione dei candidati sono stati consultati lo snapshot Radar del 7 settembre 2026, `internal_review`, le regole canoniche e le Wave 1-13 per deduplicazione, classificazione e controllo dell'applicabilità ai sette Comuni.

Lo sweep ha trovato **cinque nuovi gap correnti o strutturali** assenti dal corpus precedente:

1. Dipartimento della Funzione Pubblica · **Tirocini InPA 2026**;
2. Dipartimento della Funzione Pubblica · **Dottorati InPA 2026**;
3. MiC · **Progetti speciali per il cinema e l'audiovisivo 2026**;
4. ICSC · **Sport Missione Comune 2026**;
5. CINEA · **Green Assist Project Advisory**.

Qualunque singolo nuovo current actionable gap azzera il clean-sweep counter. Di conseguenza il gate resta **0/2**.

---

## 1. Tirocini InPA 2026

Fonti ufficiali:

- https://www.inpa.gov.it/dipartimento-della-funzione-pubblica-della-presidenza-del-consiglio-dei-ministri-avvisi-rivolti-alle-pubbliche-amministrazioni-di-cui-allart-1-comma-2-d-lgs-165-2001/
- https://www.funzionepubblica.pcm.gov.it/it/il-dipartimento/notizie-del-dipartimento/al-via-la-terza-edizione-delliniziativa-tirocini-inpa-e-dottorati-inpa/

L'avviso è stato pubblicato il **5 agosto 2026** e chiude il **20 settembre 2026**.

È rivolto alle pubbliche amministrazioni di cui all'art. 1, comma 2, del D.Lgs. 165/2001. I Comuni rientrano formalmente in questo perimetro.

Il programma sostiene **190 tirocini curriculari**. L'avviso 2026 prevede un sostegno complessivo di **3.800 euro per tirocinio**: 3.600 euro di indennità al tirocinante e 200 euro all'Università, secondo le condizioni dell'avviso.

Per il Comune l'azione è diretta ma condizionata alla presentazione di un progetto ammissibile e al necessario rapporto/convenzione con l'Università.

**Stato Radar:** assente dallo snapshot e dalla ricerca repository.  
**Classificazione:** `current_false_negative`.  
**Severità:** `high`.  
**Root cause:** `national_central_pa_capacity_building_source_gap`.

Formalmente tutti e sette i Comuni rientrano nella classe di amministrazioni potenzialmente candidate; l'effettiva actionability resta legata al progetto e all'accordo universitario.

---

## 2. Dottorati InPA 2026

Fonti ufficiali:

- https://www.inpa.gov.it/dipartimento-della-funzione-pubblica-della-presidenza-del-consiglio-dei-ministri-avvisi-rivolti-alle-pubbliche-amministrazioni-di-cui-allart-1-comma-2-d-lgs-165-2001/
- https://www.funzionepubblica.pcm.gov.it/it/il-dipartimento/notizie-del-dipartimento/al-via-la-terza-edizione-delliniziativa-tirocini-inpa-e-dottorati-inpa/

Anche questo avviso è rivolto alle PA ex art. 1, comma 2, D.Lgs. 165/2001 e chiude il **20 settembre 2026**.

Il programma finanzia **13 contratti di apprendistato di alta formazione e ricerca finalizzati al conseguimento del dottorato**, con importo lordo annuo indicato nell'avviso pari a **30.000 euro per contratto per tre anni**, secondo le condizioni previste.

L'amministrazione deve presentare un progetto qualificante e attivare il protocollo richiesto con una Università accreditata.

**Stato Radar:** assente.  
**Classificazione:** `current_false_negative`.  
**Severità:** `high`.  
**Root cause:** `national_central_pa_capacity_building_source_gap`.

### Nota di evidenza

Nel PDF allegato al bando Dottorati compare un apparente refuso con riferimento al **20 settembre 2025**. Le pagine ufficiali DFP/InPA e l'intero lifecycle della terza edizione 2026 indicano invece la scadenza **20 settembre 2026**. Per l'audit prevale il lifecycle ufficiale 2026.

---

## 3. MiC · Progetti speciali per il cinema e l'audiovisivo 2026

Fonti ufficiali:

- https://cinema.cultura.gov.it/cosa-facciamo/sostegni-economici/linee-di-sostegno/promozione/progetti-speciali/
- https://cinema.cultura.gov.it/avvisi/proroga-per-la-presentazione-delle-domande-afferenti-al-bando-per-la-concessione-di-contributi-a-progetti-speciali-per-il-cinema-e-laudiovisivo-anno-2026/
- https://cinema.cultura.gov.it/comunicazione/bandi-aperti-e-prossime-scadenze/

La call 2026 è stata pubblicata il **24 luglio 2026**, con apertura delle domande il **31 luglio 2026**. La scadenza, dopo proroga, è **14 settembre 2026 alle 23:59**.

La DG Cinema indica esplicitamente gli **enti pubblici** tra i beneficiari. Il bando sostiene iniziative e progetti annuali o pluriennali di particolare rilevanza nazionale o internazionale e con forte vocazione culturale, sociale e/o economica nel cinema e nell'audiovisivo.

Dotazione 2026: **4 milioni di euro**. Il contributo è a fondo perduto e può coprire fino all'80% dei costi ammissibili entro le regole annuali.

**Stato Radar:** assente.  
**Classificazione:** `current_conditional_beneficiary_false_negative`.  
**Severità:** `high`.  
**Root cause:** `sectoral_ministry_subdirectorate_source_gap`.

Tutti i sette Comuni rientrano formalmente nella classe `ente pubblico`, ma non devono essere promossi indiscriminatamente: serve un progetto realmente conforme al profilo di particolare rilevanza richiesto dal bando.

---

## 4. ICSC · Sport Missione Comune 2026

Fonti ufficiali:

- https://www.creditosportivo.it/sport-missione-comune-2026/
- https://www.creditosportivo.it/cliente-enti-territoriali/
- https://www.creditosportivo.it/fondi-speciali-bandi-sport-2026/

La misura 2026 è corrente e chiude il **30 settembre 2026**.

Destinatari diretti sono **Comuni e altri Enti territoriali**. L'iniziativa mette a disposizione oltre **250 milioni di euro di finanziamenti a tasso fisso** e **42 milioni di euro di contributi in conto interessi**.

Sono finanziabili, secondo le condizioni ICSC, interventi su impianti sportivi pubblici — realizzazione, ampliamento, riqualificazione, efficientamento energetico, messa a norma e completamento — oltre a strutture sportive scolastiche, acquisizioni ammissibili e ciclovie.

**Stato Radar:** assente.  
**Classificazione:** `current_false_negative`.  
**Severità:** `critical`.  
**Root cause:** `public_finance_product_family_source_gap`.

Tutti e sette i Comuni sono formalmente nel perimetro dei potenziali beneficiari, ferma restando la necessità di un investimento ammissibile e della documentazione richiesta, compreso il parere CONI quando previsto.

Questo finding è distinto da **Cultura Missione Comune 2026**, già emerso in precedenza: la copertura del prodotto culturale non equivale a copertura della famiglia ICSC per gli enti territoriali.

---

## 5. CINEA · Green Assist Project Advisory

Fonti ufficiali:

- https://cinea.ec.europa.eu/green-assist-project-advisory_en
- https://cinea.ec.europa.eu/system/files/2023-10/GREEN%20ASSIST%20-%20FAQ%20experts-%2028Sept%20Clean.pdf

Green Assist è un servizio di **advisory gratuito** per promotori di investimenti green, pubblici e privati. Non è un grant monetario.

La richiesta passa normalmente attraverso l'**InvestEU Central Entry Point**. Il servizio ha però una propria logica operativa, criteri e proposta di supporto e non è quindi equivalente a una generica scheda `InvestEU Advisory Hub`.

Il focus ordinario è su programmi d'investimento plausibili di almeno **2,5 milioni di euro**; investimenti inferiori possono essere considerati se replicabili.

**Stato Radar:** assente dallo snapshot e dal corpus Wave 1-13.  
**Classificazione:** `rolling_structural_gap`.  
**Severità:** `high`.  
**Root cause:** `rolling_technical_assistance_named_service_gap`.

Un Comune è pertinente quando agisce come project promoter di un investimento green sufficientemente strutturato. Non va presentato come sostegno automaticamente utile a ogni amministrazione in assenza di un progetto.

---

## 6. Correzione dell'audit · Celebrazioni storiche Toscana

Durante Wave 14 la ricerca testuale nel repository aveva inizialmente fatto emergere come possibile gap:

**Regione Toscana · Sostegno a progetti dedicati a San Francesco, Collodi e Alluvione di Firenze**.

Il controllo diretto del completo `data/opportunity-daily-public.json` ha però trovato la scheda canonica:

- `opp-aad71fb1d25308`;
- `rule_id = rt-celebrazioni-2026`;
- ruolo `direct_applicant`;
- deadline corrente;
- matrice di eleggibilità comunale.

**Classificazione corretta:** `captured`.

Questo caso non è un gap Wave 14 e ribadisce una regola metodologica ormai vincolante: **la mancata corrispondenza di titolo nella code search non dimostra l'assenza dal Radar**. Prima di classificare un finding vanno sempre controllati snapshot, scheda canonica, regola, `municipality_eligibility` e duplicati `internal_review`.

---

## 7. Controlli e riscoperta di casi già noti

Lo sweep ha riscoperto indipendentemente diversi casi già presenti nel corpus, che non vengono ricontati:

- SPACE4Cities · Replicator Cities;
- EUI Permanent Call for peer reviewers;
- MIP4Adapt Citizen Engagement Hotline;
- Mercati rionali Toscana;
- Amianto edifici pubblici;
- Toscana Diffusa · strutture di servizio pubbliche.

Sono controlli positivi della qualità del full-corpus sweep, non nuovi finding.

### Interreg Euro-MED · ETU

`ETU Open Call 1` è stata mantenuta come `scope_review_participation_solution_showcase`: può coinvolgere anche public authorities con soluzioni già testate, ma non è stato stabilito un beneficio operativo assimilabile a grant/TA abbastanza forte da giustificare la promozione automatica nel Radar.

La prevista **ETU Open Call 2**, annunciata per ottobre 2026 e rivolta direttamente ad autorità locali/regionali per testare soluzioni con supporto dedicato, resta invece una sentinella futura da seguire.

### AMIF Integration at Local Level

Resta `national_route_watch`. Non è stata individuata una procedura italiana ufficiale inequivocabilmente riferibile alla Specific Action `AMIF/2026/SA/2.4.2`. Gli altri avvisi FAMI correnti non devono essere confusi con questa misura solo per coincidenza di importi o finalità generiche.

### Altri lifecycle control

- `Sport e Periferie 2026`: già replay storico nel corpus, non nuova opportunità corrente;
- `Nidi Gratis 2026-2027`: resta la correzione Wave 13, senza nuovo gap azionabile confermato per il perimetro Versilia;
- `Bando parcheggi Toscana 2026`: finestra non ancora aperta alla data dello sweep, quindi sentinella/upcoming e non current false negative;
- rinegoziazione mutui CDP 2026: finestra terminata ad aprile, quindi controllo storico e non current gap.

---

## Copertura dello sweep

Sono stati interrogati, con ricerca da oracle esterni prima del confronto con il corpus:

### UE

Funding & Tenders e programmi Commissione, CINEA, EISMEA, EACEA, EIT, EUI, URBACT, Interreg, Mission platforms, Covenant/Smart Cities/EIB advisory, premi e label, PCP/PPI, cascade/FSTP/replicator/associated regions e supporto tecnico rolling.

### Italia

Funzione Pubblica/InPA, Ministero Interno/DAIT/FAMI, PCM e Dipartimenti, MiC/DG Cinema, MIT, MASE, MIM, Dipartimento Sport, Infratel e prodotti finanziari/advisory per Enti Locali di ICSC/CDP.

### Toscana

Regione Toscana, PR FESR, PR FSE+, Sviluppo Toscana e ANCI Toscana come discovery oracle, con controllo separato di lifecycle e applicabilità comunale.

---

## Effetto sul gate

Wave 14 è un full-corpus independent sweep valido ai fini del gate, ma è **non pulito** perché ha prodotto cinque nuovi finding correnti/strutturali.

Nuovi gap Wave 14:

1. `dfp-tirocini-inpa-2026`;
2. `dfp-dottorati-inpa-2026`;
3. `mic-cinema-progetti-speciali-2026`;
4. `icsc-sport-missione-comune-2026`;
5. `cinea-green-assist-project-advisory`.

**Gate di saturazione: 0/2.**

L'hardening del motore resta congelato. Per iniziare a guadagnare credito verso il gate serve un nuovo full-corpus sweep indipendente con **zero** nuovi current actionable gap. Solo allora il counter potrà passare a `1/2`; servirà poi un secondo sweep indipendente consecutivo pulito per arrivare a `2/2`.

Nessuna modifica a motore/config/discovery. Nessun merge e nessuna pubblicazione.