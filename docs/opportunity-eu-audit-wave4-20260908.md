# Radar Opportunità · audit UE · Wave 4

**Data:** 8 settembre 2026  
**PR:** #161  
**Stato:** `open_not_saturated`  
**Implementazione:** congelata  
**Sweep puliti consecutivi:** **0/2**

## Esito

Il primo sweep di saturazione successivo alla Wave 3 non è pulito. Sono emersi nuovi casi correnti azionabili, ulteriori topic Horizon con ruolo comunale documentato, un nuovo replicator-city channel e due famiglie strutturali che il Radar attuale non modella bene: **innovation procurement (PCP/PPI)** e **downstream municipal EOI/cascade**.

La conclusione rimane quindi: **non passare ancora all'implementazione**.

## Nuovi casi correnti ad alta priorità

| Opportunità | Scadenza | Ruolo comunale | Classificazione |
| --- | --- | --- | --- |
| Erasmus+ KA210 VET · round 2 | 01/10/2026 | applicant/partner condizionato | `current_action_level_false_negative` |
| SPACE4Cities · Replicator Cities | 15/09/2026 | applicant diretto come città/Comune/ente pubblico | `current_false_negative_technical_capacity_support` |
| LIFE CET ENERPOV | 16/09/2026 | autorità pubblica beneficiaria/partner | `current_promotion_gap` |
| LIFE CET OSS | 16/09/2026 | applicant/partner condizionato; possibile single applicant | `current_promotion_gap` |
| HORIZON-CL6-2026-01-CIRCBIO-04 | 17/09/2026 | autorità locale/regionale **obbligatoria come beneficiary** | `current_conditional_beneficiary_false_negative` |
| HORIZON-CL5-2026-10-D6-09 | 08/10/2026 | local/regional authority, road authority, demo/partner | `current_conditional_partner_false_negative` |
| HORIZON-CL5-2026-10-D6-01 | 08/10/2026 | municipality/city/region come public player/demo partner | `current_conditional_partner_false_negative` |

### SPACE4Cities

La call per Replicator Cities seleziona dieci città/regioni per testare soluzioni space-based già acquistate dal buyers' group. Sono ammessi Comuni, città, regioni e public agencies. Il supporto comprende un pilot gratuito di tre mesi, EUR 2.500 per spese di engagement/trasferta e peer exchange.

Il caso è assente dallo snapshot pubblico del 7 settembre. È una prova diretta che le opportunità gestite da **progetti UE / public buyers** costituiscono un canale editoriale autonomo rispetto a Funding & Tenders.

### Horizon Cluster 6 · CIRCBIO-04

Il topic sui sistemi di raccolta, riuso e riparazione dei tessili a livello città/regione è uno dei casi più netti dell'intero audit: il consorzio deve includere almeno **nove autorità regionali o locali come beneficiari**, con almeno tre città/regioni dimostratrici e sei replicatrici.

Non compare nello snapshot. La presenza della source generica `eu-horizon` non costituisce quindi copertura del topic.

## Topic Horizon con ruolo partner/procurement

Sono inoltre assenti dallo snapshot:

- `HORIZON-CL6-2026-01-ZEROPOLLUTION-03`: coinvolgimento adeguato di autorità locali nel tema managed aquifer recharge / resilienza idrica;
- `HORIZON-CL5-2026-10-D6-07` CIVITAS: ruolo città/autorità locali dentro un'unica CSA di ecosistema;
- `HORIZON-CL5-2026-09-D4-04`: politiche e business model per affordable/sustainable housing, con forte rilevanza per autorità pubbliche attive sull'abitare;
- `HORIZON-CL3-2026-01-DRS-04`: uptake di disaster-risk solutions, con autorità locali tra end-user/stakeholder delle dimostrazioni;
- `HORIZON-CL3-2026-01-SSRI-03`: PPI per sicurezza civile, rilevante quando il Comune ha un concreto fabbisogno di procurement.

Questi casi non vanno tutti pubblicati come "bando per il Comune": il Radar deve distinguere applicant diretto, beneficiary richiesto, demo-site, stakeholder/end-user e buyers' group.

## Innovation procurement: nuovo lifecycle strutturale

`HORIZON-MISS-2026-04-PCP-CIT-01` dimostra che PCP/PPI richiedono una modellazione propria. Il topic finanzia consorzi di public procurers, in particolare autorità locali, per acquistare congiuntamente R&D su soluzioni net-zero. Il lead e almeno tre città devono essere Mission Cities, ma altre follower cities possono contribuire.

La stessa logica ricompare nel Cluster 3 con `SSRI-03`.

**Conseguenza per l'hardening futuro:** il ruolo `public_procurer / buyer_group / follower_city` non può essere schiacciato su `direct_applicant` o `partner`.

## NEB Facility 2026 · matrice comunale

La Facility resta assente a livello topic. La risoluzione Wave 4 separa:

### Priorità alta
- `BUSINESS-03`: outcome esplicito sulle autorità locali che identificano e riusano spazi vuoti, obsoleti o sottoutilizzati;
- `PARTICIPATION-02`: dimostrazioni di trasformazione partecipata di quartieri/spazi pubblici.

### Priorità media
- `PARTICIPATION-01`;
- `BUSINESS-01`;
- `REGEN-01`, `REGEN-02`, `REGEN-03` quando il Comune è demo-site, asset owner o partner territoriale.

### Nessuna promozione automatica
- `PARTICIPATION-03`: autorità locali soprattutto destinatari di raccomandazioni;
- `BUSINESS-02`: ruolo municipale operativo non dimostrato dalla sola pertinenza tematica.

## DUT Call 2026: partecipazione senza finanziamento italiano

La Driving Urban Transitions Call 2026 richiede almeno una urban government authority nel consorzio. Tuttavia l'Italia non figura tra le funding agencies partecipanti alla call corrente. Un Comune italiano può quindi entrare come **Cooperation Partner non finanziato**.

Questo deve essere rappresentato come `partner_only / unfunded_in_Italy`, non come grant disponibile.

## AMIF · rotta italiana

Per `AMIF Specific Action - Integration at Local Level` Comuni e città sono beneficiari eleggibili, ma la Managing Authority nazionale seleziona i progetti e presenta la proposta alla Commissione.

L'Autorità di gestione italiana è il Ministero dell'Interno. Nella ricerca sistematica sulle fonti ufficiali italiane effettuata all'8 settembre non è stato localizzato uno specifico avviso pubblico nazionale riferibile con certezza alla procedura corrente. Questo non dimostra che una procedura non esista: il caso resta `national-route watch / unresolved Italian selection mechanism`.

## Civil protection · sentinella storica UCPM

`UCPM-2026-KAPP-PVPP` è scaduta il 21 maggio, quindi non è un runtime miss del Radar pubblico. È però dentro la finestra retrospettiva ed è una sentinella eccellente: ammetteva enti pubblici e il consorzio doveva includere almeno una amministrazione pubblica di civil protection/DRM nazionale, regionale o locale.

La call va conservata nel replay storico per il canale DG ECHO/UCPM.

## Nuova sentinella downstream

La gara CINEA `CINEA/2026/OP/0018` per la seconda fase di supporto alla Mission Ocean è chiusa, ma il contractor dovrà organizzare una selezione di almeno 50 comunità — regioni, città, autorità fluviali/idriche e portuali — da assistere gratuitamente nello sviluppo di transition agendas e roadmaps.

Il Radar deve quindi poter generare una sentinella del tipo:

`upstream_contract_awarded -> downstream_city_EOI_expected`

senza aspettare che la futura EOI compaia casualmente in una fonte generica.

## Negative controls chiusi

- **SMART ERA**: correttamente esclusa per geografia. La call richiede una rural region appartenente a EUSALP/EUSBSR/EUSAIR/EUSDR; la Toscana non rientra nel perimetro italiano pertinente.
- **Just Transition PSLF 2026-2027**: call reale e aperta per il settore pubblico, ma i progetti devono ricadere nei Territorial Just Transition Plans; in Italia i territori JTF sono Taranto e Sulcis Iglesiente, quindi Versilia fuori scope.
- **Digital CYBER-11 COORDPREP**: non va promosso automaticamente ai sette Comuni; il perimetro italiano NIS2 per le amministrazioni locali comprende categorie dimensionali/istituzionali che non si applicano ai Comuni versiliesi solo in quanto Comuni.
- **Built4People D4-01**: nessuna promozione automatica senza un ruolo comunale concreto come asset/demo partner.

## Conseguenze per il gate

La Wave 4 rafforza sette requisiti per il futuro hardening:

1. coverage **topic/action-level**, non solo per programma;
2. canali dedicati a FSTP/cascade/replicator calls;
3. lifecycle `PCP/PPI` con buyers' group e procurer;
4. sentinelle downstream generate da call/contratti upstream;
5. distinzione finanziato / partner-only / unfunded;
6. negative controls geografici, regolatori e istituzionali;
7. detection lag separato dallo stato finale di capture.

## Decisione

**Audit non saturo. Implementazione ancora congelata. Sweep puliti: 0/2.**

Il prossimo sweep indipendente deve concentrarsi su Cluster 3/6 residui, UCPM, EU4Health, PCP/PPI cross-programma e ulteriori cascade/associated-region/replicator calls. Solo dopo la risoluzione di questi assi ha senso tentare il primo sweep realmente pulito.
