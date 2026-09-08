# Radar Opportunità · Wave 20 · secondo sweep pulito e chiusura gate

**Data:** 8 settembre 2026  
**Corpus:** `data/opportunity-saturation-corpus-v1-20260908.json`

## Esito

**Wave 20 è pulita.**

Dopo Wave 19 pulita, questo è il secondo full-corpus sweep indipendente consecutivo sullo stesso perimetro congelato.

Il counter raggiunge:

# **2/2 — GATE DI SATURAZIONE RAGGIUNTO**

Il requisito che teneva congelata l'implementazione è quindi soddisfatto.

In questa wave **non è stata effettuata alcuna modifica al motore, alle source o alla configurazione di discovery**. Il risultato autorizza metodologicamente l'avvio dell'hardening come fase successiva; non equivale a merge o pubblicazione.

## Perché Wave 20 è indipendente da Wave 19

Wave 19 era `oracle-first`: directory e pagine programma prima, classificazione dopo.

Wave 20 ha usato l'ordine inverso. La ricerca è partita da:

- grant/contributo;
- assistenza tecnica / project preparation;
- finanza comunale;
- asset transfer;
- award/label;
- cascade/FSTP/replicator;
- PCP/PPI e public procurer;
- borrower/requester;
- required local-authority beneficiary;
- conditional municipal consortium partner.

Solo dopo ogni candidato è stato ricondotto allo scope di uno degli oracle congelati e confrontato con il canonico.

## Nuovi current actionable gap

**Zero.**

## Controlli principali

### Access City Award 2027

Il premio è autenticamente city-facing, con candidatura diretta e premio monetario, ma il termine era il **4 settembre 2026**.

→ `closed_control`, non current gap.

### SPACE4Cities · Replicator Cities

Call ancora aperta fino al 15 settembre, con Comuni/città/regioni direttamente ammessi e pilot gratuito più supporto economico.

→ reale e current, ma **già gap noto** nel corpus.

### SUNDANSE Open Call 2

Route current per autorità locali su ecosistemi d'acqua dolce e resilienza, deadline 30 settembre.

→ già gap noto.

### eeef

La ricerca per forma finanziaria ha ritrovato sia il finanziamento diretto sia la Technical Assistance Facility per autorità municipali/locali/regionali.

→ già Wave 17.

### Regione Toscana · Sistemi museali 2026

Il controllo snapshot trova la scheda canonica `opp-04739a44581e08`, rule `rt-sistemi-museali-2026`.

→ `captured`.

### Mercati rionali / Nidi gratis

Entrambi current, entrambi già risolti nel corpus e nel canonico/lifecycle audit.

→ nessun nuovo gap.

### ICSC · Sport Missione Comune / Cultura Missione Comune

Entrambi restano current fino al 30 settembre e direttamente comunali.

→ già documentati prima del freeze.

### Agenzia del Demanio · trasferimento gratuito art. 15-bis

La ricerca per asset transfer lo ritrova, ma è già finding Wave 15.

→ known structural gap.

### CERV / PCP-PPI

Le ricerche per ruolo comunale e public procurer non hanno prodotto nuovi casi v1: i current rilevanti sono già nel corpus (Town Twinning, Charter, Daphne, Horizon procurement e SPACE4Cities) oppure risultano chiusi/upcoming/non-actionable alla data dell'audit.

## Candidati da non usare per spostare di nuovo il traguardo

### EIB · general public-sector financing

La EIB dispone anche di prodotti generali di lending per autorità regionali/locali con project cycle documentato. È un tema reale, ma nel corpus v1 l'oracle EIB è stato congelato esplicitamente nello scope `eib-advisory` (ELENA, ADAPT, C3, JASPERS, InvestEU Advisory Hub).

Estenderlo ora alla general lending significherebbe cambiare il corpus dopo Wave 19.

→ `out_of_corpus_candidate_for_v2`, nessun effetto sul gate v1.

### Agenzia del Demanio · Piano Città

Strumento reale di collaborazione e pianificazione integrata, ma non è stata stabilita una application/request window aperta e standardizzata conforme al contratto v1.

→ eventuale product-design/v2 review, non gap del gate.

## Conclusione

Il corpus v1 non pretende di rappresentare «ogni cosa che possa mai essere utile a un Comune europeo».

Pretende invece — e ora dimostra — di essere sufficientemente saturo rispetto a un perimetro esplicito, ampio e riproducibile:

- Wave 19: **0 nuovi gap**;
- Wave 20: **0 nuovi gap**;
- stesso corpus;
- due strategie di discovery materialmente diverse.

## Gate

- counter: **2/2**
- saturation gate: **MET**
- PR #161: deve restare draft/non merged fino ad autorizzazione
- merge/pubblicazione: **non eseguiti**
- modifiche motore/config: **nessuna**
- prossima fase ammessa: **hardening del Radar sulla base del corpus audit Wave 1–20**
