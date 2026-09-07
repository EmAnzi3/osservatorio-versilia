# Radar Opportunità · audit UE 120 giorni · Wave 2

**Data:** 7 settembre 2026  
**Stato:** audit aperto, implementazione congelata  
**Obiettivo:** aumentare il recall prima dell'hardening, cercando opportunità indipendentemente dalle fonti già configurate nel Radar.

## Perché una seconda wave

La prima wave aveva già dimostrato falsi negativi reali (C4T, Natura 2000, Euro-MED, ELENA, NetZeroCities). Un secondo sweep, impostato non per fonte già nota ma per **forma dell'opportunità** e **canale editoriale indipendente**, ha trovato ulteriori casi correnti. Questo dimostra che il corpus non è ancora saturo e che sarebbe prematuro implementare l'hardening attorno ai soli finding iniziali.

Il principio per questa fase è quindi: **prima congelare un corpus sufficientemente ampio e indipendente, poi implementare**.

## Nuovi finding correnti ad alta confidenza

| Opportunità | Apertura/pubblicazione | Scadenza | Ruolo comunale | Stato rispetto al Radar | Classificazione audit |
| --- | --- | --- | --- | --- | --- |
| European Digital Connectivity Awards 2026 | 26/06/2026 | 09/09/2026 | progetto pubblico/locale ammissibile se avanzato e con impatto tangibile | assente | **current_false_negative · critical** |
| #BeActive EU Sport Awards 2026 | 25/06/2026; open 30/06 | 17/09/2026 17:00 CEST | organizzazione eleggibile; va verificata la forma giuridica/ruolo del singolo Comune sul regolamento | assente | **current_scope_review_high** |
| European Capitals of Small Retail 2027 | 11/05/2026 | 09/10/2026 12:00 CET | candidatura diretta dell'amministrazione cittadina; endorsement del Sindaco; popolazione >=5.000 | assente | **current_false_negative · critical** |
| SUNDANSE Open Call 2 · Freshwater Ecosystems | 08/07/2026 | 30/09/2026 17:00 CET | autorità locali/regionali e corpi pubblici analoghi; Italia eleggibile | assente | **current_false_negative · critical** |
| Citizen Energy Advisory Hub · Technical Assistance Call 2 | 01/09/2026 | 02/10/2026 23:59 CEST | autorità pubbliche locali esplicitamente eleggibili se coinvolte in un progetto citizen energy | assente | **current_false_negative · critical** |
| Interreg NEXT MED · 3rd Call · Sustainable Tourism Capitalisation | 01/07/2026 | 29/10/2026 13:00 | autorità locali ammissibili; partenariato e riuso di output MMM richiesti | assente | **current_false_negative · critical** |
| AMIF Specific Action · Integration at Local Level | 21/05/2026 | 02/10/2026 | città/Comuni beneficiari; candidatura veicolata dalla Managing Authority nazionale | assente | **current_indirect_route_gap · high** |
| TRUNSPORT Open Call 1 | 30/07/2026 | 30/10/2026 | enti pubblici ammessi; occorre un caso d'uso cybersecurity nel trasporto | assente | **current_scope_review_high** |
| Smart Cities Marketplace · Matchmaking Services | rolling | rolling | città o consorzi con almeno una città; focus preferenziale <100k | assente | **rolling_structural_gap · high** |
| EIB ADAPT | rolling | rolling | città, autorità locali e altre PA; advisory su investimenti di adattamento climatico | assente | **rolling_structural_gap · high** |
| EIB Circular City Centre · C3 | rolling | rolling | advisory gratuito per città e promotori pubblici; CCA/CPA | assente | **rolling_structural_gap · high** |

### Evidenze ufficiali principali

- European Digital Connectivity Awards: https://digital-strategy.ec.europa.eu/en/news/apply-european-digital-connectivity-awards-2026-9-september
- #BeActive EU Sport Awards: https://sport.ec.europa.eu/fr/node/1094
- European Capitals of Small Retail: https://single-market-economy.ec.europa.eu/single-market/services/retail/european-capitals-small-retail-ecosr/how-apply_en
- SUNDANSE Open Call 2: https://sundanseproject.eu/sundanse-open-call-2/
- Citizen Energy Advisory Hub TA: https://citizens-energy.ec.europa.eu/receive-support/ceah-technical-assistance-call-proposals_en
- Interreg NEXT MED 3rd Call: https://www.regione.sardegna.it/atti-bandi-archivi/atti-amministrativi/bandi/178290330373360
- AMIF Integration at Local Level: https://home-affairs.ec.europa.eu/news/integration-local-level-eur-77-million-under-amif-specific-action-2026-05-21_en
- TRUNSPORT Open Call: https://trunsport.eu/open-calls/ (da riconfermare sul documento primario; evidenza istituzionale italiana disponibile via Lazio Innova)
- Smart Cities Marketplace Matchmaking: https://smart-cities-marketplace.ec.europa.eu/matchmaking/call-for-application
- EIB ADAPT: https://advisory.eib.org/about/adapt
- EIB C3: https://advisory.eib.org/about/circular-city-centre.htm

## Nuovo promotion gap: LIFE oltre il solo Clean Energy Transition

La configurazione corrente presidia soprattutto LIFE/CINEA topic-by-topic sul sotto-programma **Clean Energy Transition**. Lo sweep indipendente mostra invece che al 7 settembre sono ancora aperte fino al **22 settembre 2026** diverse call LIFE 2026 fuori dal perimetro CET, e il programma ammette in generale persone giuridiche pubbliche dell'UE.

Casi da sottoporre a verifica topic-by-topic, senza promozione indiscriminata:

- LIFE-2026-CLIMA-SAP-CCM · Climate Change Mitigation;
- LIFE-2026-SAP-CLIMA-GOV · Climate Governance and Information;
- LIFE-2026-SAP-ENV-ENVIRONMENT · Circular Economy and Zero Pollution;
- LIFE-2026-SAP-NAT-NATURE · Nature and Biodiversity;
- LIFE-2026-SAP-NAT-GOV · Nature/Biodiversity Governance and Information;
- LIFE-2026-PLP-NAT-ENV · Legislative and Policy Priorities;
- LIFE-2026-TA-PP-CLIMA-SIP · Technical Assistance for preparation of climate SIPs.

Fonte generale: https://cinea.ec.europa.eu/life-calls-proposals-2026_en  
Ammissibilità generale: https://cinea.ec.europa.eu/programmes/life/life-support-applicants_en

**Finding:** il presidio `cinea-life` non può essere considerato esaustivo soltanto perché quattro topic CET risultano pubblici. Serve una matrice completa `topic -> ruolo comunale -> geografia -> stato Radar` per l'intera call LIFE 2026.

## Cycle/version gap: New European Bauhaus

Il Radar contiene `eu-co-create-neb-2026`, ma la call corrente ufficiale è **Connect NEB & Co-create NEB 2027**, aperta dal 15 luglio al 30 settembre 2026. Non va trattata automaticamente come un nuovo falso negativo: prima va verificato se la scheda pubblica esistente rappresenta la stessa call con titolo/ciclo obsoleto oppure una call precedente.

Fonte: https://www.eit.europa.eu/our-activities/opportunities/connect-neb-co-create-neb

Classificazione: **cycle_version_revalidation**.

## Nuovo scope review: EIT Urban Mobility

La call **Urban Mobility Explained (UMX)** ha secondo cut-off il 29 settembre 2026. La fonte ufficiale la presenta come call per soggetti giuridici che sviluppano e scalano formazione professionale sull'urban mobility; il programma EIT 2026 è rivolto anche a ecosistemi cittadini. Prima di promuoverla serve verificare nel manuale se il Comune può essere applicant utile e non soltanto destinatario/partner.

Fonte: https://www.eiturbanmobility.eu/call-for-proposals/urban-mobility-explained-umx-open-call-2/

Classificazione: **scope_review**, non falso negativo finché il ruolo non è risolto.

## Missioni UE: altro punto cieco da aprire

La pagina ufficiale della **Mission Adaptation to Climate Change** indica call 2026 aperte fino al **23 settembre 2026** ed è esplicitamente orientata anche a autorità regionali e locali. Il Radar ha un presidio Horizon generico, ma non basta a dimostrare che i singoli topic Mission siano stati valutati.

Fonte: https://research-and-innovation.ec.europa.eu/funding/funding-opportunities/funding-programmes-and-open-calls/horizon-europe/eu-missions-horizon-europe/adaptation-climate-change_en

Azione audit: enumerare tutti i topic 2026 Mission Adaptation e Cities, risolvere applicant/partner/geografia per ciascuno e confrontare con snapshot/discovery interno.

## Casi storici/replay aggiuntivi

Lo sweep continua a confermare che premi e call cittadine annuali devono essere trattati come **sentinelle di calendario**, non trovati casualmente quando sono già in scadenza. Oltre ai casi della Wave 1, entrano nel replay:

- Access City Award 2027 · 18/06–04/09/2026; requisito città >50.000 abitanti;
- European Green Capital / Green Leaf 2028 · call chiusa 01/04/2026, fuori dalla finestra 120 giorni ma utile come sentinella annuale;
- European Capitals of Inclusion and Diversity · quinta edizione annunciata per autunno 2026, da monitorare prima dell'apertura.

## Nuovo oracle indipendente

La ricerca non deve dipendere unicamente dai programmi già configurati. La **Commissione europea mantiene pagine trasversali rivolte a enti pubblici e città** che possono funzionare come oracle indipendente per il prospective audit. In particolare:

- Funding opportunities for public bodies: https://commission.europa.eu/funding-and-tenders/how-apply/eligibility-who-can-get-funding/funding-opportunities-public-bodies_en
- Commission / city-facing support pages e directory di advisory;
- EIT opportunities: https://www.eit.europa.eu/our-activities/opportunities
- EIB Advisory catalogue: https://advisory.eib.org/

Questi canali non devono necessariamente pubblicare direttamente nel Radar: devono però produrre un **campione indipendente di controllo**, utile a verificare cosa il Radar non sta vedendo.

## Metodo di saturazione prima dell'implementazione

L'implementazione resta congelata finché non sono completati questi sweep indipendenti:

1. **Forma dell'opportunità:** grant/call, premi, FSTP/cascade funding, technical assistance, rolling facilities, shared/indirect management, capacity building, strumenti di matchmaking/advisory.
2. **Canali istituzionali:** Commission DG per DG, agenzie esecutive, CINEA, EIT, EIB, Missioni UE, Covenant, EUI, URBACT, Interreg rilevanti per Toscana.
3. **Progetti finanziati UE con open call:** cascade funding e associated regions che non compaiono sui portali programmatici generici.
4. **Promotion audit:** riesame dei candidati `internal_review` del Radar per identificare opportunity già viste ma non promosse.
5. **Matrice comunale:** per ogni finding, verifica puntuale dei sette Comuni e delle condizioni (popolazione, geografia, progetto, partenariato, ruolo).
6. **Replay storico:** sentinelle per call annuali e casi già scaduti.

### Criterio di freeze del corpus

Il corpus UE non viene dichiarato saturo finché **due sweep completi e indipendenti consecutivi non producono nuove opportunità correnti azionabili**. Ogni caso del corpus deve inoltre avere uno stato esplicito tra:

- `captured`;
- `current_false_negative`;
- `historical_prelaunch_gap`;
- `cycle_version_revalidation`;
- `indirect_route_gap`;
- `scope_review`;
- `scope_excluded`;
- `rolling_structural_gap`;
- `announced_upcoming`.

L'obiettivo non è dichiarare il Radar “infallibile”, cosa non dimostrabile, ma portarlo a **copertura ad alta saturazione con falsi negativi misurabili e auditabili**.

## Stato Wave 2

**NON CHIUSA.** Il fatto che questa seconda ricerca abbia aggiunto opportunità correnti che la Wave 1 non conteneva dimostra che serve continuare. Nessun hardening va implementato sulla base del corpus attuale.