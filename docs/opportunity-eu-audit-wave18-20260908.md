# Radar Opportunità · audit Wave 18 · 8 settembre 2026

## Esito

Wave 18 è **non pulita** e chiude il metodo di audit a perimetro aperto.

Il contatore legacy resta **0/2** perché è emersa una nuova route strutturale corrente: il finanziamento della **Council of Europe Development Bank (CEB)** alle autorità locali/regionali.

Questa wave è però l'ultima nella quale una nuova famiglia di opportunità può entrare automaticamente nel gate. Dalla Wave 19 il conteggio usa un **corpus di saturazione v1 congelato**, con oracle e criteri di actionability definiti ex ante.

## Nuovo finding corrente

### Council of Europe Development Bank · financing for local/regional authorities

**Classificazione:** `rolling_structural_gap`

La CEB non è stata conteggiata perché è genericamente una banca, ma perché offre una route operativa documentata:

- le autorità locali/regionali sono esplicitamente tra i potenziali borrower;
- la domanda viene preparata congiuntamente da CEB e borrower;
- segue appraisal finanziario, tecnico e sociale;
- l'approvazione conduce a un Framework Loan Agreement;
- gli strumenti includono Project Loans, Programme Loans, European Co-finance Facility, Public Sector Financing Facility e Cross-Sectoral Loans.

La concreta applicabilità ai sette Comuni resta condizionata a investimento sociale ammissibile, dimensione/struttura dell'operazione, capacità finanziaria dell'ente e appraisal CEB.

L'operatività per Comuni italiani non è teorica: la CEB documenta direttamente, tra gli altri, finanziamenti al Comune di Genova e al Comune di Reggio Emilia.

Fonti primarie:

- https://coebank.org/en/project-financing/how-access-ceb-financing/
- https://coebank.org/en/project-financing/projects-approved-administrative-council/building-resilience-genoa-rrf-co-financing-facility/
- https://coebank.org/en/project-financing/projects-approved-administrative-council/social-and-affordable-housing-and-urban-regeneration-reggio-emilia/

## Replay storico

### PA Digitale 2026 · SUAP/SUE

Il 1° luglio 2026 il Dipartimento della Funzione Pubblica ha annunciato sei nuovi avvisi PA Digitale 2026, con circa **33 milioni di euro** PNRR aggiuntivi, rivolti anche ai Comuni singoli o associati per aggiornamento e interoperabilità delle piattaforme SUAP/SUE.

La finestra si è chiusa il 27 luglio 2026, prima dell'operatività pubblica del Radar.

**Classificazione:** `historical_pre_launch_gap`

Non incide sul gate corrente, ma conferma la necessità di mantenere il replay nazionale nei test del futuro motore.

Fonte primaria:

- https://www.funzionepubblica.gov.it/it/il-dipartimento/notizie-del-dipartimento/digitalizzazione-suap-e-sue-ulteriori-33-milioni-di-risorse-pnrr-per-l-aggiornamento-delle-piattaforme-tecnologiche/

## Cambio metodologico

Le Wave 1–18 hanno mostrato che un gate formulato come «qualsiasi nuova forma di opportunità utile a un Comune» è aperto per definizione: ogni ampliamento verso nuove banche, portali, reti, servizi o strumenti patrimoniali crea un nuovo universo di ricerca.

Dalla Wave 19 il gate viene quindi valutato su un corpus v1 finito. Questo **non abbassa la soglia di qualità**: impedisce soltanto di modificare il denominatore mentre si misura la saturazione.

Una nuova famiglia esterna al corpus v1 potrà essere registrata come proposta per `corpus_v2`, ma non azzererà retroattivamente il counter v1 senza una decisione esplicita di revisione del perimetro.

## Gate

- Wave 18 clean: **no**
- counter legacy dopo Wave 18: **0/2**
- implementazione: **congelata**
- prossimo passo: congelare corpus v1 e avviare Wave 19 sul solo perimetro fissato

Nessuna modifica a motore/config/discovery in questa wave.
