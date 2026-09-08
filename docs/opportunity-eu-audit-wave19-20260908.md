# Radar Opportunità · Wave 19 · primo sweep pulito sul corpus v1

**Data:** 8 settembre 2026  
**Corpus:** `data/opportunity-saturation-corpus-v1-20260908.json`

## Esito

**Wave 19 è pulita.**

Il counter di saturazione passa finalmente a:

**1/2**

È il primo sweep che conta sul gate nuovo perché è stato eseguito dopo il freeze del corpus v1, senza introdurre nuovi oracle o nuove classi di opportunità durante la ricerca.

L'implementazione resta congelata: serve ancora un secondo sweep indipendente sullo stesso identico corpus.

## Metodo

Wave 19 è stata eseguita `oracle-first`:

1. raccolta dei candidati esclusivamente dagli oracle congelati;
2. nessuna Wave precedente usata come seed di discovery;
3. per ogni candidato emerso: confronto con snapshot completo, `municipality_eligibility`, coverage rule, `internal_review` / `auditReview` e corpus Wave 1–18;
4. solo un caso aperto/rolling, concretamente azionabile e realmente nuovo avrebbe azzerato il counter.

## Risultato

**Nuovi current actionable gap: 0.**

### Controlli che hanno evitato falsi positivi

**Fondazione CR Lucca · Progettare per il futuro – opere pubbliche**

È aperto fino all'11 settembre ed è perfettamente pertinente agli enti locali della provincia di Lucca, ma il controllo dello snapshot ha trovato la scheda canonica `opp-9cba2129173b22` con rule `fcrl-opere-pubbliche-2026`.

→ `captured`, non gap.

**CERV Gender Equality 2026**

La call è chiusa dal 28 aprile 2026.

→ controllo storico, non current gap.

**CERV European Remembrance 2026**

La vecchia pianificazione indicativa Commissione e gli aggiornamenti più recenti dei punti di contatto non sono allineati. I contact point aggiornati collocano pubblicazione/apertura in ottobre e non è stata stabilita la pubblicazione della documentazione completa corrente sul Funding & Tenders Portal all'8 settembre.

Secondo il contratto v1, un calendario indicativo non basta per inventare una call corrente.

→ `lifecycle_conflict_no_confirmed_current_open_gap`.

**EISMEA · Net-Zero AI4Permitting**

Call molto pertinente alle local permitting authorities, ma chiusa il 9 giugno 2026.

→ replay/closed control.

**I3 2026 INV1 / INV2a**

Le call sono correnti fino al 12 novembre e includono public authorities negli ecosistemi interregionali, ma la famiglia era già documentata nelle Wave precedenti.

→ known current conditional-partner family, non nuovo gap.

**Agenzia del Demanio · Piano Città degli immobili pubblici**

È un reale processo di pianificazione e collaborazione con gli Enti territoriali, ma nello sweep non è stata individuata una finestra standard aperta di application/request per un Comune. Non soddisfa quindi tutte le condizioni di actionability v1.

→ non azzera il counter.

**Regione Toscana / Sviluppo Toscana / FCR Lucca**

Gli open municipal-facing emersi sono risultati già canonici o già noti: Mercati rionali, Nidi gratis, Sistemi museali e i due bandi FCR Lucca già presenti nello snapshot.

→ nessun nuovo gap.

## Candidati fuori corpus

Durante la ricerca sono emersi due filoni della Sustainable Blue Economy Partnership attraverso oracle Atlantic/SBEP non congelati nel corpus v1:

- Rolling Access Call to Marine and Maritime Research Infrastructures;
- Regional Portfolios · Call for Interest.

Sono registrati come `out_of_corpus_candidate_for_v2` e **non** modificano il counter v1. Saranno eventualmente studiati dopo il gate, senza spostare di nuovo il traguardo durante la misurazione.

## Gate

- Wave 19 clean: **sì**
- counter: **1/2**
- motore/config/discovery: **ancora congelati**
- prossimo passo: Wave 20, indipendente, sullo stesso corpus v1 ma partendo da classi/lifecycle/ruolo comunale invece che dagli oracle

Nessuna modifica di implementazione è stata effettuata.
