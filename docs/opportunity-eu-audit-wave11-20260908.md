# Radar Opportunità · audit UE · Wave 11

**Data:** 8 settembre 2026  
**PR:** #161  
**Stato:** `open_not_saturated`  
**Implementazione:** congelata  
**Sweep globali puliti consecutivi:** **0/2**

## Esito

La Wave 11 chiude il blocco residuo **LIFE CET → Horizon Cluster 6 → Horizon Cluster 5 → I3 → cascade/FSTP**.

Il risultato del blocco è importante: **non emergono nuovi current actionable gap oltre a quelli già documentati nelle Wave 2-10**. Sono state però consolidate o corrette diverse classificazioni, aggiunti controlli negativi correnti e verificati nuovi cicli 2026/2027.

La Wave 11 **non viene conteggiata come primo sweep globale pulito**. È un audit di famiglie residue, non un nuovo sweep indipendente dell'intero corpus. Il contatore resta quindi prudentemente a **0/2**. Il prossimo passo deve essere una passata full-corpus costruita da oracle esterni e non dalla lista dei casi già noti.

---

## 1. LIFE CET 2026 residuo

Scadenza comune dei topic verificati: **16 settembre 2026, ore 17:00 CEST**.

La verifica dei topic e delle call fiche CINEA conferma la matrice della Wave 6:

- `LIFE-2026-CET-POLICY` → `scope_review`: enti pubblici pertinenti, ma nessun ruolo municipale obbligatorio documentato;
- `LIFE-2026-CET-ENERPOV` → `conditional_partner`: le autorità locali sono esplicitamente nel perimetro di governance e attuazione delle politiche contro la povertà energetica;
- `LIFE-2026-CET-OSS` → `conditional_partner`: i one-stop-shop richiedono forti partnership territoriali, incluse autorità locali/regionali, senza obbligo universale di Comune beneficiario;
- `LIFE-2026-CET-RENEWHC` → `scope_review`: focus prevalente su framework nazionali/regionali;
- `LIFE-2026-CET-BETTERRENO` → `conditional_partner`: possibile ruolo locale nel mercato e nelle politiche di ristrutturazione, senza requisito municipale obbligatorio.

Fonte generale CINEA:

https://cinea.ec.europa.eu/life-calls-proposals-2026_en

**Conclusione:** nessun nuovo falso negativo LIFE CET oltre a quelli già auditati.

---

## 2. Horizon Cluster 6

### CIRCBIO-04

Resta il caso forte già registrato in Wave 6:

`HORIZON-CL6-2026-01-CIRCBIO-04`

- scadenza: **17 settembre 2026**;
- richiede almeno **9 distinte autorità regionali/locali come beneficiari**;
- 3 città/regioni dimostratrici + 6 città/regioni replicatrici.

**Classificazione confermata:** `current_required_local_authority_false_negative`.

### ZEROPOLLUTION-03

`HORIZON-CL6-2026-01-ZEROPOLLUTION-03`

Il multi-actor approach richiede un coinvolgimento adeguato di stakeholder pertinenti, incluse autorità locali, ma non obbliga un Comune a essere beneficiario.

**Classificazione confermata:** `conditional_partner`.

### CIRCBIO-02 e topic two-stage

`CIRCBIO-02` ha rilevanza di uptake per autorità locali, ma non impone un beneficiario municipale: `end_user_or_conditional_partner_no_auto_promotion`.

I topic a due stadi che sono ora nella seconda fase non costituiscono una nuova opportunità per soggetti che non hanno superato il primo stadio: sono `historical_invite_only_control` ai fini del Radar.

Fonte Work Programme Cluster 6:

https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/wp-call/2026-2027/wp-9-food-bioeconomy-natural-resources-agriculture-and-environment_horizon-2026-2027_en.pdf

---

## 3. Horizon Cluster 5

### D6-01 · CCAM Flagship

`HORIZON-CL5-2026-10-D6-01`

Scadenza: **8 ottobre 2026**.

Il Work Programme richiede un ampio coinvolgimento degli attori pubblici e cita espressamente **municipalities, cities and regions**. Non stabilisce però che una municipalità debba essere beneficiaria.

**Correzione:** da `scope_review` a `conditional_partner`.

### D6-07 · CIVITAS

`HORIZON-CL5-2026-10-D6-07`

Scadenza: **8 ottobre 2026**.

Città e autorità locali/regionali sono centrali per capacity building, scambio, replicazione e uptake, ma non è documentato un requisito che imponga un Comune beneficiario.

**Classificazione confermata:** `conditional_partner`.

### D6-09 · sicurezza stradale e resilienza rurale

`HORIZON-CL5-2026-10-D6-09`

Scadenza: **8 ottobre 2026**.

Il topic sviluppa strumenti destinati anche alle autorità locali/regionali e valorizza il coinvolgimento delle road authorities.

**Classificazione confermata:** `conditional_partner`.

### D4-04 · affordable and sustainable housing

`HORIZON-CL5-2026-09-D4-04`

Scadenza ravvicinata: **15 settembre 2026**.

Il topic ha una chiara dimensione di housing policy, patrimonio e dimostrazione territoriale. Non emerge però un requisito universale di partecipazione municipale.

**Correzione:** da `scope_review` a `conditional_partner`.

### D4-01

`HORIZON-CL5-2026-09-D4-01`

Gli edifici pubblici possono essere demo asset, ma il Comune non è automaticamente applicant/beneficiario.

**Classificazione:** `end_user_or_demo_asset_partner_no_auto_promotion`.

### Sentinella 2027 · D6-08

`HORIZON-CL5-2027-06-D6-08`

È un ottimo sentinel per il futuro hardening: nei pilot richiede espressamente che le **autorità/amministrazioni pubbliche locali o regionali e le autorità di trasporto locali siano beneficiari**.

Non è però una call corrente 2026.

**Classificazione:** `announced_upcoming`.

Fonte Work Programme Cluster 5:

https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/wp-call/2026-2027/wp-8-climate-energy-and-mobility_horizon-2026-2027_en.pdf

---

## 4. I3 · Interregional Innovation Investments

### I3-2026-INV1

- apertura: **13 maggio 2026**;
- scadenza: **12 novembre 2026, 17:00 CET**.

Le public authorities fanno parte del target del programma, ma l'opportunità richiede un ecosistema interregionale legato a priorità S3 condivise/complementari e mantiene un forte orientamento alla deployment/market uptake.

**Classificazione confermata:** `conditional_partner`.

### I3-2026-INV2a

Stessa finestra temporale e analogo vincolo di ecosistema/S3, con particolare attenzione a regioni meno sviluppate e in transizione.

**Classificazione confermata:** `conditional_partner`.

Il Comune non va presentato come applicant standalone generico.

Fonte EISMEA:

https://eismea.ec.europa.eu/funding-opportunities/calls-proposals_en

---

## 5. Cascade / FSTP / third-party calls

### TRUNSPORT Open Call 1

Era già emersa in Wave 2 come `current_scope_review_high`. La verifica primaria odierna chiude il dubbio documentale ma non giustifica una promozione indiscriminata.

- apertura: **30 luglio 2026**;
- scadenza: **30 ottobre 2026, 17:00 CET**;
- fino a **60.000 euro** per progetto;
- finanziamento fino al **50%** del costo totale;
- road / rail / air / water;
- tra i soggetti eleggibili compaiono transport infrastructure managers e **related public sector organisations**;
- tutte le attività devono però contribuire chiaramente a cybersecurity e digital innovation nel settore dei trasporti.

Fonte primaria:

https://trunsport.eu/open-calls/

**Classificazione confermata:** `current_scope_review_high`.

Un Comune va considerato soltanto quando esiste un ruolo operativo documentabile nel sistema/infrastruttura di trasporto interessato. Non basta essere una pubblica amministrazione o proprietario generico della viabilità.

### SUNDANSE Open Call 2

Già falso negativo Wave 2:

- autorità locali/regionali direttamente ammesse;
- Italia eleggibile;
- scadenza **30 settembre 2026**.

Nessun nuovo finding.

### SPACE4Cities · Replicator Cities

Già nel corpus dei current false negative:

- target diretto: cities / municipalities / regions / public agencies;
- scadenza **15 settembre 2026**.

Nessun nuovo finding.

### European Invasive Alien Species Rapid-Response Fund

Già registrato in Wave 3 come opportunità corrente per public authorities, con scadenza **10 febbraio 2027**.

Nessun nuovo finding.

### SMART ERA Open Call 2

Una PA locale può ricoprire il ruolo di Community Activator, ma la geografia follower è circoscritta alle macrostrategie UE coperte dalla call.

La Toscana/Versilia è fuori dal perimetro.

**Classificazione confermata:** `correctly_excluded_geography`.

### RIVCircular

La cascade call è corrente fino al **17 settembre 2026**, ma i progetti devono provenire dalle sette regioni partecipanti:

- Innlandet;
- Madrid;
- Kyiv Oblast;
- Hauts-de-France;
- Extremadura;
- Vienna;
- Greece.

La Toscana non rientra nel perimetro.

**Classificazione:** `correctly_excluded_geography`.

Fonte:

https://circular-cities-and-regions.ec.europa.eu/support-materials/funding-and-financing/rivcircular-open-call-interregional-circular-economy

### NetZeroCities · Enabling City Transformation 2

Nuovo ciclo aperto il **31 agosto 2026**, deadline **3 dicembre 2026**, budget 8 milioni di euro.

È riservato alle **Mission Cities**. Nessuno dei sette Comuni del Radar appartiene alle 112 Mission Cities.

**Classificazione:** `correctly_excluded_eligibility`.

Fonti:

- https://netzerocities.eu/enabling-city-transformation/
- https://netzerocities.eu/mission-cities/

### Mission Ocean · Associated Regions

Nuovo controllo sulla directory Commissione: le recenti call SWIM e le altre associated-region disponibili risultano chiuse. Resta invece da monitorare la futura EOI destinata a città/regioni nell'ambito del contratto CINEA per i servizi alle comunità, già classificata `downstream_EOI_expected`.

Fonte:

https://projects.research-and-innovation.ec.europa.eu/en/funding/funding-opportunities/funding-programmes-and-open-calls/horizon-europe/eu-missions-horizon-europe/restore-our-ocean-and-waters/calls-proposals-associated-regions

---

## 6. Esito di saturazione del blocco

**Nuovi current actionable gap trovati in Wave 11:** `0`.

Questo non trasforma automaticamente il gate in `1/2` perché la Wave 11 è stata costruita per chiudere famiglie residue già identificate, non come sweep indipendente dell'intero universo delle opportunità.

Stato corretto:

- blocco residuo: **pulito**;
- corpus globale: **non ancora dichiarato saturo**;
- clean sweep counter globale: **0/2**;
- implementazione: **ancora congelata**.

## 7. Prossimo passo

Avviare una nuova passata **full-corpus e indipendente**, costruita da oracle esterni anziché dai topic delle Wave precedenti:

1. directory istituzionali UE e programmi delegati;
2. open call / FSTP / associated regions / replicator;
3. canali nazionali e regionali ad alta probabilità;
4. confronto finale con snapshot pubblico e `internal_review`;
5. matrice di applicabilità ai sette Comuni.

Solo se questa passata completa non produce nuovi current actionable gap il contatore potrà passare da **0/2 a 1/2**.
