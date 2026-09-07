# Radar Opportunità · audit UE 120 giorni

**Data audit:** 7 settembre 2026  
**Finestra:** 10 maggio – 7 settembre 2026  
**Baseline pubblica:** Radar online dal 24 agosto 2026; snapshot corrente 29 opportunità.

## Esito

C4T GROUNDWORK **non è un caso isolato**. L'audit trova gap reali nella discovery UE: il contratto attuale può dichiarare coperta una famiglia tematica pur non presidiando tutti i canali editoriali ufficiali da cui escono opportunità direttamente utilizzabili dai Comuni.

La distinzione è importante:

- **runtime miss**: opportunità ancora aperta quando il Radar era già operativo e non intercettata;
- **historical pre-launch gap**: call scaduta prima del 24 agosto, quindi non imputabile al refresh giornaliero, ma assente dal replay storico;
- **promotion gap**: il discovery interno vede la call ma non la porta al pubblico;
- **scope review**: opportunità reale, ma il ruolo comunale va verificato prima di considerarla un falso negativo.

## Finding critici runtime

| Opportunità | Apertura/pubblicazione | Scadenza | Stato Radar al 7/9 | Finding |
| --- | --- | --- | --- | --- |
| C4T GROUNDWORK | 03/07/2026 | 11/09/2026 | recuperata il 07/09 | **Late: 66 gg dalla pubblicazione; almeno 14 gg di gap con Radar pubblico** |
| European Natura 2000 Award · Towns & cities | 21/05/2026 | 30/09/2026 | assente | **Falso negativo corrente** |
| Interreg Euro-MED Call 7 · MMM | 01/09/2026 | 30/09/2026 | assente | **Falso negativo corrente, già 6 giorni di lag** |
| ELENA · European Local ENergy Assistance | rolling | rolling | assente | **Falso negativo strutturale** |
| NetZeroCities · Technical Helpdesk for Mission-minded cities | n.d. | 04/09/2026 | assente anche il giorno della scadenza | **Falso negativo runtime appena scaduto** |

### C4T GROUNDWORK

La call è stata pubblicata da ManagEnergy/CINEA il 3 luglio e scade l'11 settembre. Lo snapshot del 25 agosto non contiene C4T; nemmeno quello del 4 settembre. È stata recuperata soltanto il 7 settembre dopo l'audit indipendente.

**Diagnosi:** il canale ManagEnergy/C4T non era presidiato. Il fix del 7 settembre ha aggiunto per la prima volta una source dedicata.

### European Natura 2000 Award

L'8ª edizione è aperta dal 21 maggio al 30 settembre. La Commissione ammette enti pubblici e ha introdotto una categoria specifica **Towns & cities** per iniziative in siti Natura 2000 urbani/periurbani.

È assente dagli snapshot del 25 agosto, 4 settembre e 7 settembre.

**Classificazione proposta:** `conditional`, perché il Comune deve avere un'attività/realizzazione pertinente collegata esplicitamente a uno o più siti Natura 2000.

### Interreg Euro-MED · Call 7

La call è aperta dal 1° al 30 settembre 2026 e riguarda il trasferimento/capitalizzazione di risultati sul turismo sostenibile. La Toscana rientra nell'area di cooperazione e le autorità pubbliche locali sono soggetti potenzialmente partecipanti; resta la condizione specifica di basarsi su almeno un output sviluppato in un altro programma MMM.

È assente dallo snapshot del 4 settembre e da quello corrente.

**Classificazione proposta:** `conditional`.

### ELENA

ELENA è una facility EIB/Commissione a sportello. Le autorità regionali, locali e municipali sono esplicitamente ammissibili; la TA può coprire fino al 90% dei costi di preparazione. Per i filoni energia/residenziale/trasporto, il programma di investimenti è normalmente superiore a 30 milioni di euro.

Non compare nel Radar.

**Classificazione proposta:** `rolling_open`, condizionata alla dimensione e struttura del programma di investimento.

### NetZeroCities Technical Helpdesk

La Mission Platform offriva assistenza tecnica gratuita a tutte le città "Mission-minded", anche oltre le 112 Mission Cities, con supporto su energia, mobilità, ambiente costruito, circolarità e adattamento. Scadenza 4 settembre 2026.

Non compare nello snapshot del 25 agosto né in quello del 4 settembre.

**Conclusione:** opportunità operativa persa mentre il Radar era già in produzione.

## Gap storici precedenti al lancio pubblico

Questi casi **non sono runtime miss**, perché la loro scadenza precede il 24 agosto, ma mostrano che il replay storico non era sufficiente:

| Opportunità | Scadenza | Evidenza |
| --- | --- | --- |
| Better Homes Partnerships · EOI | 21/08/2026 | autorità pubbliche locali esplicitamente incluse |
| Citizen Energy Panel | 14/08/2026 | call rivolta direttamente ai Comuni UE |
| EUI Innovative Actions Call 4 | 15/06/2026 | 60 M€ ERDF, call per autorità urbane; nel Radar resta solo evidenza storica di copertura |
| URBACT Action Networks 2026 | 17/06/2026 | call per amministrazioni cittadine; nel Radar resta solo evidenza storica di copertura |

Queste call devono entrare nel corpus di backtest anche se ormai scadute: servono per impedire che lo stesso tipo di opportunità venga perso in futuro.

## Promotion / scope review

### EUI Peer Reviews · autumn 2026

La call aprirà il 1° ottobre e chiuderà il 12 novembre. Il Radar la intercetta già come `discovery_only/internal_review`, ma non la pubblica.

Non viene classificata ancora come falso negativo: serve risolvere la matrice Article 11 per i sette Comuni. È però un esempio utile di **promotion gap da presidiare prima dell'apertura**, non a ridosso della scadenza.

### 6th CB RES status call

È aperta fino al 6 ottobre, ma il candidato deve essere promotore di un progetto rinnovabile transfrontaliero conforme alle regole CB RES. Non va pubblicata indiscriminatamente per tutti i Comuni. Resta in `scope_review` finché non è dimostrato un ruolo azionabile per almeno uno dei sette enti.

## Controlli positivi

L'audit ha verificato anche casi correttamente intercettati, per evitare di selezionare solo errori:

- **European City Facility · 8ª call**: presente come `announced_upcoming`; pubblicata il 17 agosto, `first_seen_at` 25 agosto.
- **EUI City-to-City Exchanges**: presente come `rolling_open`.
- **LIFE 2026 CET**: risultano pubbliche almeno le call PDA, Energy Communities, Heating & Cooling Plans e EMPOWER.

Questo dimostra che il problema non è "l'UE non viene letta": è **copertura incompleta dei canali e assenza di una misura prospettica del detection lag**.

## Causa radice

Il contratto `opportunity-coverage-contract-v04.json` valida famiglie minime. Per esempio:

- `energy-climate-environment` = GSE + MASE + CINEA LIFE;
- `eu-direct` = CINEA LIFE + NEB + Funding & Tenders + CERV.

Una famiglia può quindi risultare coperta anche se un canale diverso — ManagEnergy, Covenant of Mayors Calls, DG Environment, NetZeroCities, EIB ELENA, Interreg Euro-MED — pubblica una call che nessuna source configurata intercetta.

Inoltre il generic listing `https://eu-mayors.ec.europa.eu/en/calls` oggi viene già raggiunto dal transport del source C4T, ma con filtri C4T-specifici: il sistema riesce a scaricare la pagina e tuttavia ignora le altre call presenti sulla stessa pagina. È un difetto di **source scoping**, non di rete.

## Correzioni richieste

1. **EU Covenant of Mayors Calls come source generica autonoma**, con discovery ampia e dedup verso le fonti primarie.
2. **Interreg Euro-MED** come source esplicita.
3. **EIB ELENA** come rolling source.
4. Presidi espliciti per **DG Environment/Natura 2000** e **NetZeroCities/Cities Mission**.
5. **Historical replay 120 giorni** automatico quando entra un nuovo canale.
6. **Prospective audit settimanale** con opportunità ufficiali esterne al canonico.
7. **Detection lag misurato**, target <= 3 giorni; oltre soglia il finding deve risultare rosso anche se la call viene poi recuperata.
8. Separare nei gate **family coverage** e **editorial-channel coverage**.
9. Conservare sentinelle delle call scadute per misurare falsi negativi e lag senza dipendere dal solo snapshot corrente.

## Decisione sul KPI

Non viene dichiarato un nuovo "capture rate" in questa fase: il campione è un audit mirato di canali ad alto valore e il Radar pubblico esiste solo dal 24 agosto. Prima di pubblicare un KPI servono un corpus prospettico congelato e almeno un ciclo di osservazione reale.

Il dato già sufficiente per il gate è più semplice: **esistono falsi negativi correnti e runtime verificati. Il gate discovery non può quindi essere considerato chiuso.**
