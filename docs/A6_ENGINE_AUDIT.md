# A6 — audit del motore e criteri verificabili

Questo lotto governa quattro risultati: copertura completa dell’inventario pubblico, mappa tipizzata dei collegamenti, domande con aspettative indipendenti e baseline locale delle prestazioni. Non chiude automaticamente A6.4–A6.6 e non avvia A7. Nessuna UI o acquisizione nuova.

## Copertura

`scripts/semantic_engine_audit.py` deriva ogni ID, etichetta, tema, periodo e carrier dal catalogo effettivo. Il registry viene letto accanto al catalogo: dopo build è quello materializzato, non il registry sorgente privo delle policy aggiunte dalla build. Gli hash dei due input sono distinti.

La matrice A3 strict viene riusata per tutte le nove dimensioni: ACQUIRED descrive dati acquisiti, AVAILABLE_MISSING una lacuna dati, SOURCE_UNAVAILABLE e NOT_APPLICABLE conservano la loro semantica. Non diventano certificazioni del motore. Per ogni indicatore si conservano operazioni/dimensioni dichiarate dagli adapter, query concrete, esiti e motivi. Le correlazioni richiedono una seconda variabile scelta e uno scopo: non si eseguono tutte le coppie.

Le prove correnti usano il perimetro comunale dichiarato; le prove temporali/benchmark un comune rappresentativo esplicito e i periodi realmente presenti. È un audit completo dell’inventario e dei carrier, con prove rappresentative delle operazioni: non esecuzione esaustiva di ogni combinazione di comune/anno. Il JSON conserva questa distinzione. Presenza di adapter con una query rifiutata non è contraddizione: le precondizioni restano applicabili.

Il backlog raggruppa metriche senza adapter per profilo fonte e numero di dimensioni A3 già acquisite. È un ordine diagnostico per riuso, non costo misurato o priorità di politica. Non autorizza acquisizioni onerose né riclassificazioni del backlog A3.

## Collegamenti

Tutti gli indicatori diventano nodi; gruppi tema/fonte sono derivati e non attestano comparabilità. Il contratto companion A3 esistente viene importato e le sue prove ricontrollate dal resolver esistente. Regola, dimensione, riferimenti, motivi e hash del contratto sono conservati; una prova companion non abilita automaticamente query A6 o allineamento temporale.

Le ricette analitiche esplicite riconciliano i componenti di popolazione/fasce e presenze/intensità/residenti per codice e periodo. La dipendenza matematica non costituisce evidenza statistica indipendente. I collegamenti invecchiamento/assistenza e lavoro/infanzia mantengono contesti affiancati e tentativi di correlazione rifiutati per periodi incompatibili. Nessun arco causale o calcolo automatico autorizzato dall’appartenenza a un gruppo. Questa mappa non pretende di enumerare tutte le possibili relazioni scientifiche fra i dati.

## Domande con risultati verificati

`ci/semantic-verified-questions.json` è una raccolta di casi analitici, non un catalogo duplicato o interprete linguistico. Ogni caso contiene domanda, query strutturata, esito atteso, controlli numerici/di unità/periodo, avvertenze o motivo del rifiuto e riferimento indipendente. I riferimenti numerici sono frazioni di conteggi dichiarati o record/differenze revisionabili. I due esempi censuari arrotondati dichiarano tolleranza assoluta 1e-6; gli altri riferimenti numerici usano 1e-8. Le aspettative non vengono generate dalle risposte né aggiornate automaticamente quando cambiano i dati. Un nuovo rilascio deve essere revisionato.

Il runner conserva il risultato completo e verifica anche fonte, provenienza e Pointer delle osservazioni comunali calcolate. Un rifiuto atteso è un limite correttamente verificato, non una capacità numerica aggiuntiva. Restano necessarie successive domande multidimensionali, ambigue e di politica prima dell’interprete A7.

## Prestazioni

La CLI dedicata verifica prima le domande, poi misura costruzione/validazione del motore, prima query su nuova istanza e query con cache su cinque carichi. Tempi sequenziali con perf_counter_ns; p95 interpolato alla posizione (n−1)×0,95. Le allocazioni Python vengono misurate separatamente dai tempi con tracemalloc: non RSS o memoria nativa. Ambiente, CPU visibili/quota, campioni e hash sono registrati.

Nuova istanza non significa disco a cache fredda: la cache filesystem è incontrollata. La baseline non è uno stress test concorrente, misura di rete o SLO di produzione. Nessuna soglia temporale fragile è imposta alla CI; il gate verifica invece metodo dei percentili e correttezza. Prima di ottimizzare o aggiungere dipendenze occorre confrontare misure su un ambiente stabile. La baseline indica che riusare un’istanza già validata evita il costo di ricostruzione a ogni query.

## Riproduzione

Dopo build, usare lo stesso catalogo e registry effettivi:

```bash
python scripts/semantic_engine_audit.py --output-dir /tmp/a6-audit
python scripts/semantic_question_suite.py --output-dir /tmp/a6-audit
python scripts/semantic_engine_benchmark.py --rounds 50 --output-dir /tmp/a6-audit
```

Sono prodotti coverage.json, connections.json, questions.json e performance.json con report Markdown. I report versionati in `reports/a6-engine-audit/` si riferiscono al catalogo effettivo della #336, invariato numericamente rispetto alla #334; il JSON dettagliato è rigenerabile dalle CLI. Il registro di performance JSON conserva la baseline misurata. Nessun output derivato diventa fonte canonica di metriche o relazioni.

Il gate generale post-build verifica inventario esatto, profili e backlog, carrier acquisiti senza adapter, formule, contesti e companion, aspettative numeriche/avvertenze/rifiuti, duplicati e checker alterati. Nessun workflow nuovo; Full e golden restano richiesti. A6 rimane aperta: la copertura dei dati è maggiore di quella degli adapter e le letture di politica richiedono revisione metodologica.
