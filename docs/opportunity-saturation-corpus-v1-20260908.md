# Radar Opportunità · corpus di saturazione v1

**Congelato:** 8 settembre 2026  
**Scopo:** rendere finalmente misurabile il gate dei due sweep puliti consecutivi senza abbassare la soglia di qualità.

## Perché serve

Le Wave 1–18 hanno continuato a trovare nuove opportunità, ma hanno anche dimostrato un problema metodologico: il perimetro di ricerca si ampliava mentre veniva misurato. Dopo grant e bandi sono entrati progressivamente assistenza tecnica, FSTP, premi, project finance, asset transfer, reti con servizi, banche multilaterali, matchmaking e altre forme.

Un gate aperto a «qualsiasi nuova forma utile a un Comune» non può raggiungere una saturazione falsificabile.

Il corpus v1 congela quindi **oracle e classi di opportunità**. Non elimina le forme emerse finora: le include quando hanno una route operativa documentata. Impedisce soltanto che una nuova categoria inventata dopo il freeze modifichi retroattivamente il denominatore.

## Regola del gate v1

Servono **2 full-corpus sweep indipendenti consecutivi** sullo stesso corpus v1 senza nuovi `current actionable gap`.

- Wave 19 sarà il primo sweep che può portare il counter a `1/2`.
- Wave 20, se indipendente e ancora pulita, può portarlo a `2/2`.
- Se una delle due trova un nuovo gap **dentro il corpus v1**, il counter torna `0/2`.
- Una famiglia realmente nuova ma esterna al corpus viene registrata come `out_of_corpus_candidate_for_v2`; non azzera il counter v1 salvo decisione esplicita di versionare un corpus nuovo.

## Cosa conta come nuovo current actionable gap

Devono essere vere **tutte** le condizioni seguenti:

1. una fonte ufficiale primaria conferma che la misura è **aperta o rolling** alla data dello sweep;
2. almeno uno dei sette Comuni è formalmente ammissibile come applicant, borrower, requester, required beneficiary, public procurer o partner di consorzio con ruolo concreto;
3. esiste un beneficio operativo: grant/contributo, finanza agevolata o diretta, trasferimento di asset, TA, capacity building, expert support, accesso a infrastrutture, premio/label, matchmaking progetto-investitore, FSTP/replicator o procurement innovativo;
4. esiste una route documentata di domanda, richiesta, submission o partecipazione;
5. prima di dichiarare l'assenza vengono controllati snapshot completo, `municipality_eligibility`, coverage rule, `internal_review`/`auditReview` e Wave 1–18;
6. il caso non è già un gap noto nel corpus audit.

Un vero `promotion_gap` o `rolling_structural_gap` conta.

## Classi incluse

Il corpus v1 comprende:

- grant, contributi e sovvenzioni;
- prestiti agevolati e prodotti di finanza pubblica con route comunale;
- finanziamento da istituzioni multilaterali quando l'accesso dell'autorità locale è esplicito e operativo;
- assistenza tecnica e project preparation;
- capacity building / peer learning / expert support con candidatura o richiesta;
- premi, label e competition;
- cascade, FSTP, replicator e associated-region support;
- PCP/PPI quando il Comune può essere realmente public procurer;
- portali di matchmaking solo se prevedono una submission formale del progetto;
- trasferimenti patrimoniali o altri benefici non-cash con richiesta formale;
- servizi rolling;
- procedure nazionali/shared-management in cui il Comune è beneficiario o origine della richiesta;
- partner di consorzio condizionale solo quando il ruolo comunale è concreto e documentato.

## Cosa non azzera il gate v1

Restano fuori:

- membership generica di network senza beneficio operativo discreto;
- knowledge platform, newsletter o directory senza request route;
- survey, consultazioni e questionari;
- eventi, webinar e conferenze;
- procurement lato fornitore;
- pagine generiche di banche/finanziatori senza accesso comunale documentato;
- semplice ruolo di stakeholder/end-user;
- beneficiari predeterminati che escludono tutti i sette Comuni;
- programmi geograficamente non eleggibili;
- call già chiuse e replay storici;
- call annunciate ma non ancora aperte;
- nuove famiglie/oracle introdotte dopo il freeze senza una decisione esplicita di creare `corpus_v2`.

## Oracle congelati

### UE istituzionale

Funding & Tenders, CINEA, EISMEA, EACEA, EIT, EUI, URBACT, Interreg Euro-MED, Interreg NEXT MED, Interreg Italy-Croatia come controllo geografico, Mission Adaptation/MIP4Adapt, Mission Ocean, NetZeroCities, Covenant of Mayors, Smart Cities Marketplace, EIB Advisory, InvestEU Portal, eeef, Council of Europe Development Bank e le famiglie Commissione di award/label già emerse nel corpus.

### Open call / cascade di progetti UE

SUNDANSE, SPACE4Cities, LDT4SSC, DS4SSCC, TRUNSPORT, SMART ERA, CO-WATERS, IRISCC, Mission Ocean Associated Regions e European Invasive Alien Species Rapid-Response Fund.

### Italia

Ministero Interno/DAIT, FNAsilo-SAI, FAMI, Funzione Pubblica/InPA/PA Digitale, Dipartimenti PCM Famiglia/Sport/Giovani-SCU/Politiche del Mare, MiC general/DG Cinema/DG Spettacolo/DG Creatività, MIT, MASE, MIM, Infratel, ICSC, CDP, Agenzia del Demanio, Ministero del Turismo e Pelagos.

### Toscana / locale

Regione Toscana bandi aperti e tutti i bandi, PR FESR, PR FSE+, Sviluppo Toscana, ANCI Toscana come discovery oracle secondario e Fondazione Cassa di Risparmio di Lucca per il perimetro territoriale già presente nel Radar.

Il dettaglio machine-readable degli oracle è in `data/opportunity-saturation-corpus-v1-20260908.json`.

## Indipendenza degli sweep

- **Wave 19:** source/oracle-first; si raccolgono candidati dai directory/programme pages e solo dopo si consulta il corpus precedente.
- **Wave 20:** ordine diverso; si parte dalle classi di opportunità, lifecycle e ruolo comunale, e si risale alle fonti.

Entrambe devono usare esattamente lo stesso corpus v1.

## Implementazione

Il motore resta congelato. Il freeze riguarda esclusivamente il **perimetro dell'audit**.
