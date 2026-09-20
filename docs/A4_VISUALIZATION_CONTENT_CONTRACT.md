# A4 — Visualization & Content Contract

Questo documento consolida le regole visuali e semantiche già presenti nel prodotto e definisce il perimetro del contratto machine-readable introdotto in A4.2.

Non è un secondo catalogo di indicatori: le metriche restano derivate esclusivamente da `data/site-data.json` e dall'Effective Public Catalog materializzato dalla build.

## A4.1 — Audit delle regole esistenti

La baseline verificata è il catalogo effettivo della build post-#268:

- 225 indicatori;
- 1.547 righe comunali;
- 72 indicatori composite;
- 26 indicatori con benchmark Toscana/Italia dichiarato;
- 46 righe con valore principale nullo, di cui 24 esplicitamente `notApplicable` e 22 realmente `n.d.`;
- 84 indicatori con `meta.comparisonReference = "aggregate"`;
- 141 indicatori che nel layer visuale generico ricadono sul fallback della media semplice dei Comuni con dato disponibile.

### Formattazione dei valori

Il prodotto usa formatter italiani con separatore delle migliaia e precisione dipendente dall'unità.

La baseline contiene più alias semanticamente equivalenti, tra cui:

- conteggi: `number`, `count`;
- percentuali: `percent`, `%`, `percent2`;
- valuta: `currency`, `currency2`;
- densità/tassi: `per100`, `per1000`, `per10k`, `per100k`;
- unità territoriali e tecniche dedicate.

Prima di A4 le regole erano duplicate soprattutto tra `assets/app-bundle.js` e `assets/visual-grammar.js`, con differenze possibili di precisione e alias. A4.2 introduce un unico vocabolario dichiarativo per rendere queste differenze verificabili.

### Scale

Il comportamento corrente del layer visuale generico è:

- percentuali non negative: asse da zero; 0–100 solo quando il massimo osservato occupa una parte significativa della scala, altrimenti massimo adattivo leggibile;
- grandezze non negative: asse da zero;
- grandezze interamente negative: zero come estremo superiore;
- grandezze con segni opposti: scala simmetrica attorno allo zero;
- prezzo carburante `eurliter`: scala focalizzata con padding dedicato.

A4 non cambia queste regole in questa fase: le rende prima esplicite e testabili.

### Confronti con la Versilia

Il layer visuale distingue due casi:

1. `meta.comparisonReference = "aggregate"`: usa l'aggregato dichiarato nel catalogo;
2. campo assente: calcola una media semplice dei Comuni con dato disponibile.

I modi di differenza espliciti già presenti sono:

- `percentagePoints`;
- `absolute`;
- `shareOfAggregate`.

In assenza di un modo esplicito, il confronto numerico ordinario è relativo in percentuale.

Il fatto che tutti i 225 indicatori abbiano un `aggregate` ma soltanto 84 dichiarino esplicitamente di usarlo nel confronto è un punto da verificare in A4.4, non da correggere automaticamente: totale, media ponderata, rapporto e media semplice non sono intercambiabili.

### Benchmark Toscana/Italia

Quando `meta.benchmark` è presente, il benchmark deve mantenere almeno:

- periodo/anno;
- fonte;
- URL della fonte;
- nota metodologica;
- almeno un valore numerico tra Toscana e Italia.

La presenza di un benchmark non autorizza a sostituire il riferimento Versilia usato nei confronti comunali.

### Dati mancanti e non applicabili

Le due situazioni sono semanticamente distinte:

- valore assente: `n.d.` / “Dato non disponibile”;
- fenomeno non applicabile al territorio: `n.a.` / “Non applicabile”, governato da `row.notApplicable`.

Una riga `notApplicable` non deve contenere un valore numerico principale.

### Polarità, ordine e colore

Le polarità ammesse sono `neutral`, `positive`, `negative`.

L'ordinamento delle barre resta numerico decrescente. La polarità serve a spiegare come leggere l'indicatore e non trasforma automaticamente il primo valore nel “migliore”.

Il colore conserva significato tematico/informativo e non deve diventare un semaforo implicito di qualità territoriale.

### Tooltip e accessibilità

Il valore mostrato nel tooltip, nella label hover e nell'`aria-label` deve usare la stessa semantica di formato della superficie visibile.

`n.d.` e `n.a.` devono restare distinguibili anche nei testi accessibili.

## A4.2 — Contratto dichiarativo

`ci/visualization-content-contract.json` definisce senza enumerare metriche:

- vocabolario delle unità e precisione;
- distinzione tra dato mancante e non applicabile;
- polarità ammesse e semantica non valutativa del colore;
- riferimento di confronto e fallback corrente;
- modi di differenza ammessi;
- requisiti minimi dei benchmark;
- regole di scala già applicate dal layer generico;
- vincolo di coerenza tra valore visibile e tooltip/accessibilità.

`scripts/visualization_content_contract.py` valida il contratto sia sul catalogo sorgente sia sul catalogo effettivo materializzato dalla build.

Il validator è deliberatamente generico: nessun ID indicatore è copiato nel contratto.

## A4.3 — Coerenza semantica delle superfici

Il contratto valida ora anche le unità presenti nelle parti composite e nei valori normalizzati, e verifica che l'unità della riga normalizzata coincida con quella dichiarata dalla metrica.

Il gate blocca inoltre la grammatica runtime comune su invarianti non legati a singoli indicatori:

- hover e `aria-label` usano lo stesso formatter del valore;
- la legenda usa il riferimento di confronto risolto;
- `n.d.` / “Dato non disponibile” e `n.a.` / “Non applicabile” restano distinti.

La regressione browser deriva dal catalogo effettivo i rapporti strutturati e verifica su famiglie di unità rappresentative che legenda, asse, hover e testo accessibile espongano lo stesso riferimento e la stessa unità.

## A4.4 — Media semplice, rapporti e denominatori

Il contratto di aggregazione non assume che `aggregate.value` sia automaticamente il riferimento corretto. Quando `comparisonReference` è assente, il renderer continua a usare la media semplice dei Comuni con dato disponibile.

Quando però il catalogo effettivo espone `ratioComponents`, il gate ricostruisce sia ogni valore comunale sia l'aggregato territoriale con la formula:

`sum(numeratore) / sum(denominatore) × scala`

e richiede:

- denominatori comunali e aggregato non nulli;
- scala uniforme;
- riconciliazione del valore comunale;
- riconciliazione dell'aggregato ponderato;
- `comparisonReference = "aggregate"`, perché la media semplice dei rapporti non è semanticamente equivalente al rapporto sui totali.

L'audit post-#269 individua 16 indicatori / 112 righe con componenti numeratore-denominatore. Tre indicatori OpenBDAP erano numericamente corretti nell'aggregato ma ricadevano ancora nel fallback della media semplice: `ownRevenueShare`, `currentCollectionCapacity` e `currentPaymentCapacity`. A4.4 li riallinea al valore ponderato Versilia già presente nel catalogo, senza modificare i dati sorgente.

Dopo la correzione il catalogo effettivo atteso contiene 87 riferimenti aggregati espliciti e 138 fallback alla media semplice. Gli altri fallback non vengono riclassificati automaticamente: somme, totali, compositi e aggregati speciali restano distinti dalla semantica del confronto.

## A4.5 — Visual regression rappresentativa

`ci/visual-regression-contract.json` governa un campione visuale derivato dall'Effective Public Catalog, senza introdurre un inventario manuale di indicatori.

Il bootstrap effettivo contiene 40 superfici rappresentative:

- 11 pannelli, uno per ogni tema;
- 3 famiglie generiche risolte dal `data-viz` renderizzato: `lollipop`, `percent-dotplot`, `signed-dotplot`;
- 22 famiglie composite derivate dai `meta.compositeType` presenti nel catalogo effettivo;
- 2 varianti dello storico: serie a due punti e serie lunga;
- 2 stati della scheda comunale: vista corrente e storico.

La selezione della metrica resta algoritmica: primo indicatore canonico pertinente alla famiglia richiesta. Il contratto non contiene ID di metriche.

Le baseline versionate in `ci/visual-regression-baselines/*.json` sono fingerprint visuali compatti, non screenshot binari. Ogni fingerprint conserva dimensioni, average hash, difference hash e una griglia colore quantizzata 8×8. Il confronto tollera esclusivamente piccoli delta di rasterizzazione; una variazione oltre soglia fallisce il gate.

I PNG reali vengono prodotti soltanto come diagnostica in `reports/visual-regression/` quando manca una baseline, si registra intenzionalmente una nuova baseline o viene rilevato un mismatch. Le baseline iniziali derivano dal run GitHub Actions `35522525947` sullo SHA `3c31b452c333ff5df94e58eb070293fdce586995`, dopo che tutte le regressioni preesistenti erano risultate verdi e le 40 candidate erano state verificate visivamente.

## A4.6 — Integrazione nel preflight generale

`scripts/test_visual_regression.py` è parte del Full preflight canonico tramite `scripts/preflight.py` ed è incluso nel manifest di compilazione CI. Il Quick resta il gate semantico/build rapido; la regressione visuale resta Full-only insieme agli altri controlli browser.

Il workflow Pages conserva sempre `reports/visual-regression/` come artifact diagnostico del Full, anche in caso di failure del gate. Non è stato introdotto un workflow release-specifico.

Per una modifica visuale intenzionale:

1. il rendering deve essere verificato esplicitamente;
2. si rigenerano i fingerprint solo dopo l'approvazione del nuovo aspetto;
3. le soglie non vanno allargate per far passare una regressione;
4. gli screenshot di mismatch restano diagnostica temporanea, non una seconda fonte di verità.

Il lotto A4.5–A4.6 non modifica il rendering o i dati pubblici del sito.
