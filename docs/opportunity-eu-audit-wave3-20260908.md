# Radar Opportunità · audit UE Wave 3

**Data audit:** 8 settembre 2026  
**PR:** #161  
**Branch:** `audit/opportunity-eu-120d-20260907`  
**Implementazione motore:** congelata  
**Stato gate:** `OPEN / NOT SATURATED`  
**Sweep puliti consecutivi:** **0/2**

## Decisione

La Wave 3 non consente ancora di passare all'implementazione. Ha trovato ulteriori opportunità correnti e azionabili assenti dallo snapshot Radar, oltre a nuovi pattern strutturali: topic-level discovery insufficiente, cascade calls, qualificazioni rolling, opportunità EU-funded pubblicate da implementer terzi e programmi a gestione indiretta.

Il criterio di saturazione resta quindi invariato: servono **due sweep indipendenti consecutivi senza nuovi current actionable gap**.

## Correzione LIFE CET

Una verifica diretta del branch corregge una classificazione intermedia dell'audit: le seguenti quattro call LIFE CET sono **già captured e pubbliche** nel v0.4.4:

- `LIFE-2026-CET-HEATCOOLPLAN`
- `LIFE-2026-CET-PDA`
- `LIFE-2026-CET-ENERCOM`
- `LIFE-2026-CET-EMPOWER`

Sono state pubblicate il **21 aprile 2026** e hanno `first_seen_at = 2026-08-24`: detection lag **125 giorni**. Il problema è quindi la latenza di scoperta, non la loro assenza attuale.

`EMPOWER` richiede inoltre una revisione del lifecycle: la call principale seleziona il soggetto che gestirà successive cascade call; per le autorità locali il valore operativo principale può arrivare proprio da queste sotto-call. Il Radar deve quindi conservare una sentinella prospettica anche dopo aver catturato la call madre.

## Nuovi gap LIFE non-CET

Le call seguenti sono aperte dal **21 aprile** al **22 settembre 2026** e non compaiono nello snapshot pubblico di riferimento del 7 settembre:

| Topic | Ruolo comunale | Esito audit |
| --- | --- | --- |
| `LIFE-2026-CLIMA-SAP-CCA` | ente pubblico, ruolo diretto/partner condizionato; adattamento locale e city councils esplicitamente pertinenti | **current promotion gap · critical** |
| `LIFE-2026-SAP-CLIMA-GOV` | autorità locali/regionali nella governance multilivello clima-energia | **current promotion gap · high** |
| `LIFE-2026-SAP-ENV-ENVIRONMENT` | ente pubblico; acqua, drenaggio urbano, servizi idrici e GPP sono aree municipali dirette | **current promotion gap · critical** |
| `LIFE-2026-SAP-ENV-GOV` | ente pubblico, governance/compliance/partecipazione | **promotion + scope gap · high** |
| `LIFE-2026-SAP-NAT-NATURE` | ente pubblico; progetto natura/restoration/Natura 2000 condizionato | **promotion + scope gap · high** |
| `LIFE-2026-SAP-NAT-GOV` | ente pubblico, governance/informazione natura | **promotion + scope gap · high** |
| `LIFE-2026-PLP-ENER-GOV` | autorità locali parte del dialogo multilivello, ma call di scala ampia | **scope review high** |
| `LIFE-2026-TA-PP-CLIMA-SIP` | ente pubblico formalmente ammissibile, ma scala SIP da risolvere | **scope review** |

Per le sei SAP il lag minimo misurabile allo snapshot del 7 settembre è **139 giorni**.

Fonti primarie: CINEA · LIFE Calls 2026 e pagine ufficiali dei singoli topic.

## Horizon Missions · programma configurato, topic persi

Il Radar dispone già del source generico `eu-horizon`, ma nello snapshot non compaiono gli identificatori dei topic qui verificati.

### Cities Mission 2026

Call aperta dal **4 febbraio** all'**8 ottobre 2026**, budget indicativo **85,5 M€**:

- `HORIZON-MISS-2026-04-CIT-01`
- `HORIZON-MISS-2026-04-CIT-02`
- `HORIZON-MISS-2026-04-CIT-NEB-B4P-CCRI-03`

Il terzo topic richiede dimostrazioni in almeno tre città di Paesi diversi, con le città come beneficiari e almeno una Mission City. L'assenza dei topic dallo snapshot, a fronte del source Horizon configurato, è un **topic-level promotion/detail gap**. Lag minimo al 7 settembre: **215 giorni dall'apertura**.

### Mission Adaptation 2026

- `CLIMA-05` — patrimonio culturale e resilienza climatica: autorità regionali/locali coinvolte nei territori dimostratori, con possibile ruolo beneficiary/associated partner. **Current scope/promotion gap**.
- `CLIMA-07` — finanziamento di azioni locali di adattamento mediante FSTP. **Cascade prospective gap**: il Radar deve seguire anche le successive sotto-call.

### Mission Ocean 2026

Scadenza **23 settembre 2026**.

- `OCEAN-01` — supporto alle public authorities per mapping habitat marini e Nature Restoration Regulation; route anche tramite associated regions.
- `OCEAN-02` — autorità nazionali, regionali e locali sono esplicitamente tra i soggetti cui rendere disponibili soluzioni contro inquinamento e perdita di biodiversità; anche qui esistono componenti di replicazione/associated regions.

Entrambi sono assenti dallo snapshot: **topic-level scope/promotion gap**.

## New European Bauhaus Facility 2026

La Facility Horizon/NEB è aperta fino al **1 dicembre 2026**. Il source Horizon generico non basta: nessun `HORIZON-NEB-2026` compare nello snapshot.

La matrice preliminare distingue almeno:

- **alta rilevanza municipale:** `BUSINESS-03`, `PARTICIPATION-02`, `REGEN-01`, `REGEN-02`, `BUSINESS-01`;
- **ruolo prevalentemente end-user / non promuovere automaticamente:** `PARTICIPATION-03`;
- altri topic ancora da risolvere puntualmente.

Classificazione: **current topic-matrix promotion gap**, non nuovo source programmatico da aggiungere alla cieca.

## Erasmus+ · source presente, action-level coverage assente

L'Agenzia Italiana per la Gioventù conferma un secondo round al **1° ottobre 2026, ore 12:00 Bruxelles** per:

- `KA152` · Scambi di giovani
- `KA153` · Mobilità degli animatori socioeducativi
- `KA154` · Attività di partecipazione dei giovani
- `KA155` · DiscoverEU inclusion
- `KA182` · Mobilità del personale sportivo

Nessuna di queste azioni compare nello snapshot.

`KA182` è il caso più netto: la Guida Erasmus+ ammette una **local public authority** attiva nello sport/attività fisica e nel grassroots sport come applicant. È quindi un **current direct-applicant false negative**.

### Accreditamento KA120

Scadenza **29 settembre 2026, ore 12:00 Bruxelles**. La Guida Erasmus+ ammette autorità pubbliche locali/regionali con un ruolo nei settori VET, scuola o educazione degli adulti. L'accreditamento semplifica l'accesso futuro ai finanziamenti KA1.

Classificazione: **qualification/access gap**. Il Radar deve modellare anche opportunità che non sono un grant immediato ma aprono un canale stabile di finanziamento.

## European Solidarity Corps

In Italia i progetti di volontariato hanno una seconda scadenza al **1° ottobre 2026**. Per candidarsi è necessario il **Quality Label**, richiedibile continuativamente durante l'anno.

Né `ESC51` né `Quality Label` compaiono nello snapshot.

Classificazione: **current conditional false negative + rolling qualification gap**.

## Nuovo gap third-party: European Invasive Alien Species Rapid-Response Fund

**Fonte:** IUCN Save Our Species, iniziativa cofinanziata dall'UE.  
**Stato:** aperta.  
**Scadenza:** **10 febbraio 2027, ore 14:00**.  
**Grant:** **10.000–50.000 €**.  
**Durata:** fino a 12 mesi.  
**Applicant:** conservation organisations, research institutions e **public authorities** nell'UE.

Finanzia interventi rapidi su nuove o emergenti invasioni di specie aliene, dalla pianificazione alla rapida eradicazione e al monitoraggio.

Non compare nello snapshot Radar.

**Classificazione:** `current_false_negative_third_party_editorial_gap` · **critical**.

Questo caso è strutturalmente importante: il finanziamento è europeo, ma la call è pubblicata e gestita da un implementer terzo. Un Radar che controlla solo Commissione, Funding & Tenders e agenzie esecutive continuerà a perdere questa classe di opportunità.

## Horizon Mission Prizes · sentinella di calendario

Il Work Programme Horizon 2026-2027 annuncia quattro premi per local public authorities:

- Mission Anchoring Prize
- Mission Citizen Engagement Prize
- Mission Ecosystem Prize
- Mission Knowledge Valorisation Prize

Per ciascun premio sono previsti **1,5 M€**, ripartiti in 450k / 390k / 330k / 330k. Il lancio è indicato nel **Q3 2026**.

Al momento dell'audit non è stata trovata una pagina definitiva di contest aperto. Non vengono quindi classificati come false negative correnti.

**Classificazione:** `announced_upcoming / launch-overdue-review`.

Il caso dimostra la necessità di una sentinella che fallisca quando una finestra di lancio annunciata trascorre senza che il Radar abbia trovato una call definitiva o registrato una variazione di calendario.

## CERV Remembrance · non forzare una falsa classificazione

Il planning CERV è stato aggiornato nel corso del 2026 e le fonti consultate non restituiscono una finestra perfettamente coerente con il calendario iniziale. Non viene classificato come current false negative fino alla verifica della call definitiva sul Funding & Tenders.

**Classificazione:** `calendar_change / announced_upcoming review`.

## CEF Transport · controllo positivo

La call CEF Transport 2026 è già presente nel corpus come sentinella `r03` in `audit_review`.

È corretto non pubblicarla genericamente ai sette Comuni: l'ammissibilità formale dei public bodies non basta; servono topic/TEN-T, asset e progetto pertinenti e, dove previsto, accordo dello Stato membro.

**Classificazione:** `correctly_held_scope_review`.

## AMIF · Integration at Local Level

DG HOME conferma:

- budget indicativo **77 M€**;
- città, Comuni, autorità regionali e agenzie locali tra i beneficiari eleggibili;
- selezione dei progetti affidata alla **Managing Authority AMIF nazionale**;
- scadenza Commissione per le Managing Authorities: **2 ottobre 2026**.

Nelle ricerche effettuate sulle fonti FAMI/Ministero dell'Interno non è stato individuato un avviso italiano inequivocabilmente riferito a questa Specific Action. Questo **non dimostra che non esista**: la route italiana resta da risolvere.

Classificazione: **indirect-route gap / national selection unresolved**.

## Diagnosi strutturale aggiornata

La Wave 3 rafforza sette difetti distinti:

1. `program configured != topic coverage`;
2. family coverage e editorial-channel coverage vanno separati;
3. cascade/open calls di progetti UE richiedono discovery dedicata;
4. implementer terzi EU-funded richiedono un oracle separato;
5. qualification/access instruments e rolling support devono essere lifecycle di prima classe;
6. le call annunciate devono avere launch-window sentinels;
7. shared management richiede tracciamento UE → Managing Authority nazionale/regionale.

## Prossimo gate

Non si implementa ancora.

La prossima tornata deve:

1. completare i residui LIFE CET (`ENERPOV`, `POLICY`, `RENEWHC`, `BETTERRENO`, `OSS` + negative controls);
2. chiudere la matrice municipality-level di Cities, Adaptation e Ocean per tutti e sette i Comuni;
3. chiudere tutti i 9 topic NEB Facility;
4. risolvere Erasmus+ rispetto alle funzioni effettive dell'ente locale e alle definizioni delle Agenzie nazionali italiane;
5. fare un nuovo sweep indipendente specifico su **cascade calls / associated regions / third-party implementers**;
6. ripetere Commission Cities Portal + DG-by-DG dopo l'aggiornamento del corpus.

Solo dopo **due sweep consecutivi a zero nuovi current actionable** sarà ragionevole proporre l'hardening del motore nella stessa PR #161.
