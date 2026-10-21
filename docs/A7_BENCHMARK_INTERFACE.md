# A7 — confronto guidato con Toscana e Italia

Incremento A7.5.2: porta nell’esploratore le richieste selettive `benchmark_gap`
introdotte dalla #462. A6 resta DONE e immutata. Nessuna nuova acquisizione,
backend o servizio; nessuna promozione nella navigazione.

## Interazione e risultati

Scegliere tema, indicatore e vista, poi «Confronto con Toscana o Italia».
Il riferimento richiede una scelta esplicita: il menu contiene soltanto Toscana
e/o Italia dichiarati da A6 per quella vista, se il relativo shard è presente.
Un’operazione dichiarata ma non trasportata resta disabilitata; un confronto
non ammesso non viene inventato. Comune e riferimento sono selezioni distinte.

La richiesta conserva il periodo nativo e non aggiunge `allowPartial`. Il lettore
originale restituisce esclusivamente la richiesta esatta materializzata. Un
rifiuto resta tale; le eventuali osservazioni con copertura incompleta richiedono
consenso e non producono una scheda di scostamento. Cambiare riferimento revoca
risultati, consenso e risposte tardive, come le altre selezioni.

Solo per risposte `computed` la sintesi mostra `municipalValue`, `benchmarkValue`
e `value` restituiti da A6. Nessuna sottrazione o conversione percentuale nel
browser. Le prime due unità provengono dalle rispettive osservazioni; l’unità
dello scostamento proviene dal risultato. `percentage_points` è presentato come
«punti percentuali», distinto dai valori percentuali delle due osservazioni.
Un segno positivo non implica un giudizio favorevole o sfavorevole.

Periodi del risultato e, dove presenti, di numeratore/denominatore sono esposti.
La tabella conserva le due osservazioni, i rispettivi periodi, fonti, definizioni
e metodi, anche quando la sintesi è già visibile. Toscana/Italia hanno etichette
leggibili. Il payload originale resta intatto nel dettaglio di verifica.
La sintesi arrotonda per leggibilità a due decimali, o tre cifre significative
per valori non nulli inferiori a 0,01; lo dichiara accanto ai valori. La tabella
conserva la precisione di presentazione originale. Nessun dato persistito viene
arrotondato e nessuno scostamento viene ricostruito dai valori visualizzati. Grafici soltanto secondo le
guardie già esistenti per osservazioni complete e omogenee.

## Pacchetto pubblico candidato

Il generatore mantiene `DEFAULT_PROFILES` invariato. Soltanto il materializzatore
pubblico sceglie esplicitamente `current`, `comparison`, `history`, `benchmark`.
Il ranking resta opzionale e non viene aggiunto al prodotto pubblico. Un pacchetto
senza benchmark continua a funzionare con l’operazione non consultabile.

La ricevuta del grafo dichiara `interfaceVersion: 2`, legata all’integrità della
pagina. La matrice considera i benchmark presentati soltanto in artefatti con
questa interazione e relativo shard, mantenendo distinta la UI versione 1.
Il report offline non prova la pubblicazione: il controllo live resta separato.

L’intero pacchetto segue staging, verifica di tutti gli hash, ancora indipendente
e artifact Pages unico già approvati. File mancanti/incompatibili bloccano la
consultazione senza fallback ad altre release. Nessuna modifica a budget,
consenso, service worker, adapter, dati, aspettative numeriche o golden.

## Verifica e limiti

Il gate esistente `test_a7_query_runtime.py` comprende selezioni native benchmark
in browser desktop/mobile: richiesta/risposta identiche ad A6, riferimenti
espliciti, unità dello scostamento, periodi dei componenti, rifiuti senza scheda,
revoca al cambio riferimento e regressioni delle altre operazioni. I controlli
di corruzione, recupero, offline e rollback restano attivi. Nessun nuovo workflow.

La misura combinata e la matrice vanno prodotte sul catalogo effettivo. Non sono
nuove prove numeriche indipendenti. Prima della prontezza: preview/browser,
Quick/Full locali ordinari, CI Quick→Full effettivo e audit A3 sul medesimo albero.
Nessun merge o deploy dell’assistente. A7 resta IN_PROGRESS.
