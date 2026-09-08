# Radar Opportunità · audit UE · Wave 7

**Data:** 8 settembre 2026  
**PR:** #161  
**Stato:** `open_not_saturated`  
**Implementazione:** congelata  
**Sweep puliti consecutivi:** **0/2**

## Esito

La Wave 7 **non è uno sweep pulito**. Risolve un `scope_review` rimasto aperto dalla Wave 2 e conferma un'ulteriore famiglia di gap di partecipazione nel Cluster 3 Horizon:

1. **Urban Mobility Explained (UMX)** non è soltanto una call rivolta all'ecosistema cittadino: EIT Urban Mobility dichiara esplicitamente che le **cities sono legal entities ammissibili**, anche in proposta mono-partecipante. Il secondo cut-off è il 29 settembre 2026 e il contributo EIT può arrivare a **700.000 euro per proposta**. Nel reference snapshot non compare.
2. `HORIZON-CL3-2026-01-SSRI-02` e `SSRI-03` sono strumenti di **innovation procurement** che richiedono buyer group/procurers pubblici come beneficiari. Per un Comune la partecipazione è condizionale all'esistenza di un bisogno e di una funzione di procurement di sicurezza civile, ma non si tratta di semplice stakeholder engagement.

Il contatore di saturazione resta quindi **0/2**.

## 1. EIT Urban Mobility · UMX

### Urban Mobility Explained (UMX) Open Call · secondo cut-off

Call aperta dal 2 luglio 2025; secondo cut-off **29 settembre 2026, ore 17:00 CEST**.

La pagina ufficiale EIT Urban Mobility chiarisce definitivamente il punto lasciato in `scope_review` nella Wave 2:

- sono ammesse tutte le persone giuridiche stabilite in UE o Paesi associati a Horizon Europe;
- tra gli esempi espliciti figurano **cities**, oltre a PMI, università, RTO e grandi imprese;
- sono ammesse proposte **mono-participant** e **multi-participant**;
- budget indicativo della call: circa **2–4 milioni di euro**;
- contributo EIT massimo per proposta: **700.000 euro**.

Il fit comunale resta tematico: la proposta deve sviluppare o scalare formazione professionale e servizi di supporto sull'urban mobility, con dimensione europea e sostenibilità dell'offerta. Non ogni Comune è quindi un candidato materialmente forte, ma il Comune è un applicant giuridicamente ammissibile.

**Classificazione:** `current_conditional_applicant_false_negative`.  
**Severità:** `high`.

Fonte ufficiale:  
https://www.eiturbanmobility.eu/call-for-proposals/urban-mobility-explained-umx-open-call-2/

## 2. Cluster 3 · innovation procurement

### HORIZON-CL3-2026-01-SSRI-02 · Demand-led innovation in security

Apertura **6 maggio 2026** · scadenza **5 novembre 2026**. Tipo di azione: **Pre-Commercial Procurement (PCP)**.

La composizione minima richiede:

- almeno **3 practitioners**;
- almeno **3 procurers**;
- provenienza da almeno **3 Stati membri/Paesi associati**;
- almeno **2 procurers** devono essere public procurers indipendenti.

Una stessa organizzazione può coprire il ruolo di practitioner e procurer. Per un Comune il fit dipende quindi da un effettivo ruolo di civil-security practitioner/procurer e dalla capacità di entrare in un buyer group transnazionale.

**Classificazione:** `conditional_partner`.  
**Famiglia:** `innovation_procurement / buyer_group`.  
**Radar:** codice esatto assente dal reference snapshot.

### HORIZON-CL3-2026-01-SSRI-03 · Public procurement of innovation for security

Apertura **6 maggio 2026** · scadenza **5 novembre 2026**. Tipo di azione: **Public Procurement of Innovative Solutions (PPI)**.

Il topic richiede come beneficiari almeno:

- **3 practitioners**;
- **3 public procurers**;
- da almeno **3 Paesi**;
- almeno **2 public procurers indipendenti**, in Paesi diversi, con almeno uno stabilito in uno Stato membro UE.

Anche qui la forma dell'opportunità è diversa dal grant ordinario: il valore per il Radar è intercettare il ruolo possibile dell'ente come **buyer/procurer**, senza promuovere indiscriminatamente qualunque topic security.

**Classificazione:** `conditional_partner`.  
**Famiglia:** `innovation_procurement / buyer_group`.  
**Radar:** codice esatto assente dal reference snapshot.

Fonti di verifica:

- https://rea.ec.europa.eu/funding-and-grants/horizon-europe-cluster-3-civil-security-society_en
- Funding & Tenders / topic `HORIZON-CL3-2026-01-SSRI-02`
- Funding & Tenders / topic `HORIZON-CL3-2026-01-SSRI-03`

## 3. Cluster 3 · INFRA-02

`HORIZON-CL3-2026-01-INFRA-02` — **Security challenges of the green transition in urban and peri-urban areas** — resta un caso di `scope_review` / possibile `conditional_partner`.

Il topic è direttamente costruito su rischi generati dall'adozione urbana e periurbana di tecnologie della transizione verde — fotovoltaico, storage, ricarica EV, smart sensors, green roofs/walls, infrastrutture sostenibili — e mira a fornire metodologie a **authorities e critical infrastructure operators**. In questa passata non è stata però dimostrata una condizione di eleggibilità che imponga una municipalità come beneficiario.

Non lo trasformo quindi in falso negativo automatico.

## 4. CEF Energy · 6th CB RES status call

La sesta e ultima call del MFF 2021–2027 per ottenere lo status **Cross-Border Renewable Energy (CB RES)** è aperta dal 29 giugno al **6 ottobre 2026, ore 17:00**.

Lo status è prerequisito per accedere ai successivi finanziamenti CEF per studi e lavori. Tuttavia un progetto deve:

- essere basato su un meccanismo di cooperazione della Renewable Energy Directive;
- coinvolgere cooperazione tra Stati;
- disporre dell'accordo o del supporto formale degli Stati partecipanti;
- dimostrare benefici socio-economici cross-border.

Non è quindi una call comunale generalista. Un ente locale può eventualmente stare dietro a un progetto/promotore compatibile, ma per i sette Comuni non esiste applicabilità automatica.

**Classificazione:** `scope_review`, non `current_false_negative`.

Fonte ufficiale CINEA:  
https://cinea.ec.europa.eu/news-events/news/cef-energy-6th-call-cross-border-renewable-energy-projects-obtain-status-launched-2026-06-29_en

## 5. Cascade / Associated Regions · controlli

### SUNDANSE Open Call 2

Confermata ancora aperta fino al **30 settembre 2026, ore 17:00 CET**, con contributo fino a **100.000 euro** per autorità locale/regionale e Italia eleggibile. È già presente nel corpus audit dalla Wave 2: nessun nuovo finding, ma resta un ottimo sentinel della famiglia `cascade/FSTP/associated_region`.

### SPACE4Cities · Replicator Cities

Confermata ancora aperta fino al **15 settembre 2026, ore 17:00 CEST**. Possono applicare municipalità, città, regioni e public agencies; il supporto comprende pilot gratuito, copertura dei costi del pilot e **2.500 euro** per travel/engagement. Anche questo caso è già nel corpus precedente: nessun nuovo finding.

### Mission Ocean · directory Associated Regions

La directory ufficiale Commissione conferma la famiglia editoriale, ma le call Associated Regions esaminate in questa passata risultano chiuse. Non emerge da quella directory un nuovo current false negative oltre ai casi già repertoriati.

### LDT4SSC

Le tre open call risultano ora tutte **closed**; la terza è scaduta il 13 luglio 2026. Va mantenuta come replay/historical sentinel, non come gap corrente all'8 settembre.

## 6. Correzione metadata · Natura 2000 Award

La pagina ufficiale della Commissione indica ora una **proroga della scadenza al 16 ottobre 2026, ore 12:00 CEST**.

Il corpus precedente riportava ancora 30 settembre. Il caso è già stato identificato dal Radar audit; quindi non è un nuovo gap di discovery, ma una **correzione di freshness/metadata** importante: il futuro motore deve essere capace di aggiornare deadline estese senza lasciare una scheda prematuramente scaduta.

**Classificazione:** `captured_metadata_correction`.

Fonte ufficiale:  
https://environment.ec.europa.eu/topics/nature-and-biodiversity/natura-2000-award/application-process_en

## 7. Low-value participation control

Il Covenant of Mayors espone anche il **Strategic Review 2026 survey**, aperto a tutti i Comuni fino al 30 settembre 2026. È una vera possibilità di partecipazione istituzionale, ma non offre grant, premio, TA strutturata o capacity building.

**Classificazione:** `scope_review_low_value_participation`.

Questo è un controllo utile per impedire che l'aumento del recall degradi il Radar in un aggregatore di qualunque survey europea.

## Decisione

**Audit ancora non saturo. Implementazione congelata. Sweep puliti: 0/2.**

La Wave 7 aggiunge due lezioni strutturali alla futura correzione del Radar:

1. l'eleggibilità deve essere risolta anche quando una call non è semanticamente “per Comuni” ma include le **cities come applicant** (`UMX`);
2. il discovery deve riconoscere gli strumenti di **PCP/PPI buyer-group**, dove il ruolo dell'ente pubblico è procurer/practitioner e non il classico beneficiario di un grant (`SSRI-02`, `SSRI-03`).

Prossimo sweep, ancora audit-only:

1. completare i restanti Cluster 3 `INFRA` e procurement/practitioner topic;
2. proseguire l'asse Commission/Covenant/city-facing eliminando survey e input a basso segnale;
3. chiudere, se possibile, la route italiana AMIF;
4. confrontare UMX e le famiglie procurement con `internal_review` depurato dai duplicati;
5. avviare un nuovo sweep indipendente di saturazione soltanto dopo questi controlli.

Solo un intero sweep senza nuovi gap correnti azionabili potrà portare il contatore a **1/2**.
