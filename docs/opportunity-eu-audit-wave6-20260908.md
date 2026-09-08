# Radar Opportunità · audit UE · Wave 6

**Data:** 8 settembre 2026  
**PR:** #161  
**Stato:** `open_not_saturated`  
**Implementazione:** congelata  
**Sweep puliti consecutivi:** **0/2**

## Esito

La Wave 6 non è uno sweep pulito. Ha trovato due problemi correnti di natura diversa e ha allargato la matrice dei gap condizionali:

1. un **current false negative critico** mai entrato né nell'output pubblico né in `internal_review`: `HORIZON-CL6-2026-01-CIRCBIO-04`;
2. un **promotion gap**: `Co-create NEB`, già scoperto dal Radar ma ancora trattenuto in `internal_review` nonostante il requisito esplicito di almeno una municipalità/regione/ente affiliato nel partenariato.

Restano inoltre famiglie correnti con forte ruolo territoriale che il Radar non rappresenta a livello di topic: LIFE CET residuo, Horizon Cluster 5/6, NEB Facility e I3.

Di conseguenza il contatore di saturazione resta **0/2** e il motore rimane congelato.

## 1. Falso negativo critico · CIRCBIO-04

### HORIZON-CL6-2026-01-CIRCBIO-04

**Demonstrating and deploying innovative collection, sorting-for-reuse and repair systems for textiles at city/region level**  
Apertura 17 aprile 2026 · scadenza 17 settembre 2026.

Il Work Programme Horizon Cluster 6 impone una condizione di eleggibilità eccezionalmente netta: almeno **9 autorità regionali o locali distinte devono essere beneficiarie del consorzio**, di cui:

- almeno 3 appartenenti a città/regioni dimostratrici diverse;
- altre 6 appartenenti a città/regioni replicatrici diverse.

Budget indicativo del topic: **10 milioni di euro**; contributo atteso circa **5 milioni per progetto**.

Il codice non compare nello snapshot pubblico di riferimento e non compare nella coda `internal_review`.

**Classificazione:** `current_required_local_authority_false_negative`.  
**Severità:** `critical`.

Fonte ufficiale: Horizon Europe Work Programme 2026-2027, Cluster 6:  
https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/wp-call/2026-2027/wp-9-food-bioeconomy-natural-resources-agriculture-and-environment_horizon-2026-2027_en.pdf

Questo finding conferma che la discovery attuale può saltare interi topic anche quando il ruolo dell'ente locale è un requisito formale di eleggibilità.

## 2. Promotion gap · Co-create NEB

### Co-create NEB · Open Call 2027

Apertura luglio 2026 · scadenza **30 settembre 2026, ore 17:00**.

Il Radar ha già scoperto la pagina ufficiale UE, ma il record è ancora `internal_review` e non è nell'output pubblico.

La documentazione EIT è esplicita:

- consorzio di 2-4 partner;
- **almeno una municipalità, regione o ente affiliato**;
- grant fino a **49.300 euro**;
- cofinanziamento **8.700 euro**;
- budget totale progetto **58.000 euro**;
- trasformazione place-based di spazi pubblici con collaborazione tra comunità e municipalità.

**Classificazione:** `promotion_gap`.  
**Severità:** `high`.

Fonti ufficiali:

- https://www.eit.europa.eu/our-activities/opportunities/connect-neb-co-create-neb
- https://new-european-bauhaus.europa.eu/calls-proposals/co-create-neb_en

Il problema qui non è la discovery: è il passaggio **discovered -> verified -> promoted**.

## 3. NEB Facility 2026 · matrice completa dei 9 topic

La call `HORIZON-NEB-2026-01` è aperta dal **5 maggio 2026** al **1 dicembre 2026, ore 17:00 CET**, con budget complessivo **101,1 milioni di euro**. Il Work Programme finale contiene esattamente **9 topic**. Nessun codice `HORIZON-NEB-2026` compare nello snapshot di riferimento.

| Topic | Ruolo territoriale prudenziale | Audit |
|---|---|---|
| `PARTICIPATION-01` · homelessness / housing-led | policy e demonstration partner territoriale | `conditional_partner` |
| `PARTICIPATION-02` · spatial design of neighbourhoods | decision maker / demonstration partner | `conditional_partner` |
| `PARTICIPATION-03` · inhabitants' experiences, health and well-being | autorità locale soprattutto come policy end-user | `scope_review` |
| `REGEN-01` · thermal comfort in buildings | possibile asset/demo partner pubblico | `scope_review` |
| `REGEN-02` · maintenance and repair of existing buildings | possibile building owner/demo partner | `conditional_partner` |
| `REGEN-03` · sustainable use of vertical space | possibile planning/demo partner | `scope_review` |
| `BUSINESS-01` · homelessness, social infrastructure and services | partner su infrastrutture/servizi pubblici | `conditional_partner` |
| `BUSINESS-02` · capital market dynamics | public authority soprattutto stakeholder/end-user | `scope_review` |
| `BUSINESS-03` · reuse of vacant/obsolete/underutilised spaces | autorità locali target esplicito delle metodologie di identificazione/riuso | `conditional_partner` |

Non viene assegnato automaticamente `current_false_negative` a tutti i nove topic: l'assenza di un codice non prova da sola che un Comune debba essere beneficiario. La famiglia, però, è attualmente **non coperta a livello topic** e deve entrare nel successivo hardening con logica di ruolo.

Fonti ufficiali:

- https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/horizon-europe-eur-1011-million-under-new-european-bauhaus-facility_en
- https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/wp-call/2026-2027/wp-13-new-european-bauhaus-facility_horizon-2026-2027_en.pdf

## 4. LIFE CET · residuo 2026

I quattro casi già verificati in precedenza (`HEATCOOLPLAN`, `PDA`, `ENERCOM`, `EMPOWER`) restano **captured_with_excessive_detection_lag**, non falsi negativi.

I cinque topic residui sono invece assenti come codici esatti dallo snapshot. Tutti scadono il **16 settembre 2026, ore 17:00 CEST**.

| Topic | Valutazione comunale |
|---|---|
| `LIFE-2026-CET-ENERPOV` | `conditional_partner` · forte: autorità nazionali/regionali/locali esplicitamente nel perimetro di governance della povertà energetica |
| `LIFE-2026-CET-OSS` | `conditional_partner` · servizi territoriali one-stop-shop e partnership con attori locali/regionali |
| `LIFE-2026-CET-BETTERRENO` | `conditional_partner` · possibile ruolo su strumenti e mercati della riqualificazione, non Comune obbligatorio |
| `LIFE-2026-CET-POLICY` | `scope_review` · public authorities nel perimetro ma ruolo locale non obbligatorio |
| `LIFE-2026-CET-RENEWHC` | `scope_review` · focus soprattutto su framework nazionali/regionali |

Fonti CINEA:

- https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/alleviating-household-energy-poverty-europe-1_en
- https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/one-stop-shops-integrated-services-clean-energy-transition-private-buildings_en
- https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/energy-renovation-solutions-boosting-building-renovation-through-effective-markets-and-instruments_en
- https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/towards-effective-implementation-key-legislation-field-sustainable-energy-1_en
- https://cinea.ec.europa.eu/funding-opportunities/calls-proposals/strengthening-national-frameworks-renewable-and-efficient-heating-and-cooling-existing-buildings_en

## 5. Cluster 6 · ZEROPOLLUTION-03

`HORIZON-CL6-2026-01-ZEROPOLLUTION-03` è aperto dal **17 aprile** al **17 settembre 2026** ed è assente dallo snapshot.

Il topic richiede il multi-actor approach e l'adeguato coinvolgimento di stakeholder pertinenti, includendo espressamente **local authorities**, insieme a farmers, land managers e water-governance bodies. Richiede inoltre case study e governance model a scala locale.

Non viene però richiesta una municipalità come beneficiario obbligatorio.

**Classificazione:** `conditional_partner`, non `current_false_negative`.

Questa distinzione è importante per non trasformare il futuro hardening in un generatore di falsi positivi Horizon.

## 6. Cluster 5 · mobilità e built environment

Quattro topic prioritari verificati risultano assenti come codici esatti:

- `HORIZON-CL5-2026-10-D6-09` · Road Safety and resilience of rural areas — `conditional_partner`; forte ruolo per local/regional e road authorities, scadenza 8 ottobre;
- `HORIZON-CL5-2026-10-D6-07` · CIVITAS — `conditional_partner`; city/local-regional capacity, deployment e replication;
- `HORIZON-CL5-2026-10-D6-01` · CCAM Flagship — `scope_review`; città/regioni e policy bodies pertinenti ma nessun requisito comunale obbligatorio verificato;
- `HORIZON-CL5-2026-09-D4-04` · affordable and sustainable housing — `scope_review`; forte policy relevance locale ma nessun requisito comunale obbligatorio verificato.

Fonte ufficiale comune:  
https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/wp-call/2026-2027/wp-8-climate-energy-and-mobility_horizon-2026-2027_en.pdf

## 7. I3 · DG REGIO / EISMEA

Le call correnti `I3-2026-INV1` e `I3-2026-INV2a` sono aperte dal **13 maggio** al **12 novembre 2026** e non compaiono nello snapshot.

EISMEA include esplicitamente le **public authorities** tra i soggetti cui è rivolto l'I3 Instrument. Tuttavia l'accesso reale richiede:

- ecosistema interregionale;
- partner di più Stati/regioni;
- priorità Smart Specialisation condivise o complementari;
- investimento vicino al mercato e ruolo forte delle imprese.

La Toscana dispone di una S3 2021-2027 attiva; ciò rende la geografia potenzialmente compatibile ma non trasforma automaticamente i sette Comuni in candidati diretti.

**Classificazione:** `conditional_partner`.  
**Root cause:** `DG_REGIO_EISMEA_source_family_gap`.

Fonti:

- https://eismea.ec.europa.eu/programmes/interregional-innovation-investments-i3-instrument_en
- https://eismea.ec.europa.eu/funding-opportunities/calls-proposals/interregional-innovation-investments-strand-1-i3-2026-inv1_en
- https://eismea.ec.europa.eu/funding-opportunities/calls-proposals/interregional-innovation-investments-strand-2a-i3-2026-inv2a_en

## 8. AMIF · Integration at Local Level

La Commissione ha lanciato una Specific Action da **77 milioni di euro** che ammette espressamente **cities, municipalities, regional authorities e local agencies**. Contributo per progetto: da **0,8 a 7,5 milioni**, fino al **90%** di cofinanziamento UE.

Il percorso non è però una candidatura diretta del Comune alla Commissione: l'autorità locale deve passare dal **Managing Authority nazionale**, che seleziona i progetti e trasmette la candidatura nazionale entro il **2 ottobre 2026**.

In questo sweep non è stato confermato un avviso italiano ufficiale dedicato che mappi senza ambiguità questa Specific Action.

**Classificazione:** `national_route_watch / unresolved_Italian_selection_mechanism`.

Fonte Commissione:  
https://home-affairs.ec.europa.eu/news/integration-local-level-eur-77-million-under-amif-specific-action-2026-05-21_en

Non viene quindi né esclusa l'opportunità né dichiarata inesistente in Italia.

## 9. EUI · internal_review e lifecycle

### City-to-City Exchanges

La call è già correttamente pubblica nel Radar come `rolling_open`. Nella coda interna rimangono diversi frammenti duplicati della stessa pagina ufficiale.

Questo è **rumore/dedup**, non promotion gap.

La fonte EUI conferma che la call è aperta permanentemente alle urban authorities degli Stati membri, senza popolazione minima, con requisito DEGURBA 1/2 salvo Article 11 cities.

### Peer Reviews · autumn 2026

Il Radar ha già intercettato il riferimento in `internal_review`, ma al giorno dell'audit la call non è ancora aperta:

- apertura prevista **1 ottobre 2026**;
- chiusura **12 novembre 2026, ore 12:00 CET**;
- `city under review`: deve essere Article 11 city;
- `peer reviewer`: può rappresentare qualunque urban authority UE con esperienza pertinente.

**Classificazione al 8 settembre:** `announced_upcoming`, non runtime miss.

Fonte:  
https://www.urban-initiative.eu/capacity-building/peer-reviews/call-autumn2026

## 10. `internal_review` · lezione della Wave 6

Lo snapshot contiene **40** elementi `reviewInternal`. L'audit non deve contarli automaticamente come occasioni mancate.

Tre esempi toscani inizialmente sospetti — Amianto edifici pubblici, Mercati rionali e Toscana Diffusa — sono in realtà già pubblicati tramite la fonte canonica Regione Toscana/Sviluppo Toscana; ANCI produce duplicati discovery rimasti in coda.

Anche EUI City-to-City mostra lo stesso schema: record canonico già pubblico + frammenti della pagina in `internal_review`.

La Wave 6 distingue quindi due fenomeni:

- **promotion gap vero:** una opportunità verificabile e comunale resta solo in `internal_review` (`Co-create NEB`);
- **queue noise:** frammenti/duplicati rimangono in review mentre la stessa opportunità canonica è già pubblica.

Il successivo hardening dovrà trattare questi due problemi separatamente.

## 11. Mission Ocean downstream

Non è stata confermata, al giorno dell'audit, una EOI già aperta alle città derivante dal procurement europeo di assistenza tecnica. La sequenza resta:

`upstream contract -> downstream EOI for communities expected`.

Le future comunità destinatarie includono città, regioni, autorità fluviali/idriche e portuali.

**Classificazione:** `downstream_EOI_expected`.

## Decisione

**Audit ancora non saturo. Implementazione congelata. Sweep puliti: 0/2.**

La Wave 6 rende già più chiara la futura correzione del Radar perché separa almeno quattro root cause:

1. **discovery miss di topic** — `CIRCBIO-04`;
2. **promotion gap dopo discovery** — `Co-create NEB`;
3. **source-family/scope gap** — NEB Facility, LIFE CET residuo, Cluster 5/6, I3;
4. **rumore di coda / dedup** — duplicati ANCI ed EUI già coperti dal record canonico.

Prossimo sweep, ancora solo audit:

1. cascade/FSTP/replicator e associated-regions correnti;
2. ulteriore scan Cluster 3/5/6 per requisiti obbligatori o siti demo territoriali non ancora individuati;
3. prosecuzione della route italiana AMIF;
4. `internal_review` depurato dai duplicati canonici;
5. nuovo sweep indipendente di saturazione.

Solo uno sweep completo senza nuovi gap correnti azionabili porterà il contatore a **1/2**.
