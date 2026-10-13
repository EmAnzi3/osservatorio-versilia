# A6.4–A6.6 — revisione metodologica riproducibile

Questo documento accompagna il candidato metodologico successivo alla correzione Atlante #425. **Non è l'attestazione amministrativa di A6 DONE**. A6 rimane IN_PROGRESS fino ai gate, all'integrazione approvata e alla PR conclusiva verificata. A7 non è avviata.

## Cosa viene verificato

Il catalogo effettivo e il registry adiacente sono prodotti dalla pipeline pubblica; il catalogo sorgente rimane distinto. La copertura deriva dagli ID canonici, senza un inventario aggiuntivo. Il motore v56 conserva tutti gli adapter e le restrizioni approvate. La matrice espone ora `contextsByDimension` e `benchmarkScopesByDimension`: unità, universo, definizione, metodo, frequenza e basi temporali appartengono alla **vista selezionata**. Il benchmark della vista primaria non si estende a una fascia, a un settore, a un importo assoluto o a un componente.

`scripts/semantic_methodological_audit.py` produce un unico JSON verificabile con:

- tutte le metriche/dimensioni e le operazioni dichiarate;
- query effettivamente eseguite, esiti, motivi e SHA della risposta;
- verifiche numeriche e di provenienza indipendenti;
- tutte le 35 letture, i due riepiloghi e le loro annotazioni comprensibili;
- repertorio territoriale, limiti, dati mancanti e richieste strutturate;
- associazioni selezionate già presenti, campioni e sensibilità;
- impronte delle implementazioni, catalogo, registry e file realmente letti;
- eventuali errori residui, senza convertirli in PASS.

La matrice ordinaria continua a distinguere operazioni dichiarate e precondizioni. Nell'audit metodologico vengono inoltre interrogate le operazioni non dichiarate, **per ogni dimensione**, per verificare il rifiuto concreto e rilevare un eventuale calcolo consentito dal runtime ma omesso dalla matrice. Le correlazioni richiedono una coppia scelta: non si esegue una scansione indiscriminata di tutte le coppie.

## Evidenze A6.1–A6.6 e Definition of Done

| Step | Evidenza riproducibile | Condizione di accettazione |
|---|---|---|
| A6.1 | `validate_semantic_model_contract`, sorgente e catalogo effettivo nel preflight | Identità, appartenenza, route, fonti e periodi riconciliati; 225 effettivi distinti dai 181 sorgente |
| A6.2 | Contratto operazioni, `semantic_operations.assess`, calcolatori e checker razionale | Formula e precondizioni esplicite; risultato numerico verificato o rifiuto motivato |
| A6.3 | Suite comparabilità, guardie dei profili, richieste effettive della matrice | Universi/periodi/unità/metodi conservati, confronti impropri e ponderazioni senza componenti rifiutati |
| A6.4 | Audit copertura, suite 3.727, matrice per dimensione e provenance verifier | Zero carrier senza adapter, provenienza e riproducibilità; operazioni limitate alla capacità reale |
| A6.5 | Regressioni territoriali, 35 annotazioni, due riepiloghi, repertorio di problemi | Numeri originali preservati e utilità/limiti/lacune espliciti, senza raccomandazioni automatiche |
| A6.6 | Associazioni selezionate, n/coppie/leave-one-out, test di perdita avvertenze | Associazione distinta da causalità, previsione, significatività e inferenza individuale |

La Definition of Done richiede domande multi-indicatore risolvibili con calcoli riproducibili e fonti/metodo esatti. Le cinque letture combinano contesti e calcoli consentiti, e rifiutano associazioni temporali improprie; il repertorio rende verificabile anche il limite delle domande di decisione. La verifica di questi contenuti non sostituisce i gate pubblici, l'approvazione o l'integrazione. **Nessuno step A6.4–A6.6 viene segnato DONE da questo candidato**: la PR amministrativa conclusiva dovrà attestare l'albero integrato, i workflow pertinenti e gli effetti pubblici effettivamente osservati.

## Aritmetica indipendente e provenienza

`semantic_methodological_checks.py` non importa i calcolatori del motore. Usa frazioni razionali decimali per variazioni, benchmark, rapporti di somme, rango con pari merito, quantili e OLS. Per Pearson usa somme e prodotti, anziché l'algoritmo centrato/scalato del motore; per Spearman costruisce i ranghi dal numero dei valori minori e uguali. Verifica separatamente ogni esclusione leave-one-out, il campione, le coppie, le avvertenze e l'assenza di inferenza automatica.

Sono verificati descrittori delle osservazioni, SHA dei byte effettivamente conservati e puntatori JSON. INVALSI/affluenza richiedono ricostruzione dei frammenti dichiarati: SHA dei frammenti e SHA dei byte JSON decodificati sono basi diverse. Non si finge che il percorso virtuale sia un file originario. Per il compatto Atlante la risoluzione completa dei puntatori/celle rimane nella regressione specializzata già governata.

L'aritmetica su osservazioni non è da sola un audit delle fonti. Le suite dei singoli profili, ripetute dal preflight, forniscono riconciliazioni native, trascrizioni fisse, replay degli input disponibili e attacchi a valori/denominatori/cache/periodi/definizioni. Le aspettative fisse dei 3.727 casi non sono generate dalle risposte; tutti gli ID e richieste della baseline rimangono invariati. Le verifiche supplementari non gonfiano quel conteggio.

**Perimetro completo:** inventario degli indicatori, viste dichiarate, confini delle operazioni non accoppiate, tutte le risposte della suite congelata, tutte le 35 letture e i due riepiloghi. **Perimetro rappresentativo:** singolo Comune esplicito nelle prove temporali/benchmark e periodi scelti nelle query della matrice; non ogni possibile combinazione Comune × anno × vista × operazione. Il JSON conserva la query esatta. Le regressioni dei profili ampliano questa copertura nei rispettivi perimetri documentati; non diventano una certificazione universale di tutte le combinazioni.

## Comparabilità e limiti controllati

| Rischio | Regola applicata |
|---|---|
| Anni scolastici, mesi, date e annualità | Token e frequenza propri; nessuna conversione implicita |
| Stock, flussi e fotografie | Basi temporali esplicite; rapporti ibridi mantengono le date dei componenti |
| Tassi, valori assoluti, punti percentuali | Vista e unità distinte; nessun conteggio ottenuto da un tasso arrotondato |
| Popolazioni e denominatori | Residenti, contribuenti, alunni localizzati, addetti e unità locali restano universi distinti |
| Nominale e reale | Euro nominali dichiarati; deflazione solo nel carrier NIC/MEF già verificato |
| Comuni, territorio e benchmark | Scopi/periodi/metodi revisionati; totali regionali non diventano medie o benchmark municipali |
| Partizioni e gerarchie | Nessuna somma di macroclassi/dettagli sovrapposti o livelli ATECO |
| Null, n.a. e zero | Esclusioni esplicite, consenso per copertura parziale; nessuna interpolazione o imputazione |
| Serie e continuità | Consultazione dello storico distinta da autorizzazione a variazioni/trend |
| Correlazione | Pairing per identità/periodo, n effettivo, costanti rifiutate e sensibilità; associazione descrittiva |

Sette Comuni non sono un campione indipendente per default. Denominatori condivisi, dipendenze matematiche, outlier e discontinuità limitano la lettura. Nessun p-value, significatività, previsione, effetto di politica o inferenza sulle persone viene prodotto. Lo scopo testuale del chiamante non certifica scientificamente una coppia.

Gli input hanno livelli di evidenza diversi, conservati nelle risposte e nella documentazione dei profili: replay di dati nativi effettivamente inclusi; replay di estrazioni normalizzate; oppure lettura del solo catalogo pubblicato. Ospedali, densità EV, dimensione familiare e alcuni carrier legacy mantengono limiti sulle componenti/date/documenti originari. Non vengono promossi a dati raw certificati; le operazioni senza evidenza sufficiente restano rifiutate. Le ricostruzioni climatiche mantengono la natura ricostruita e le note sulla differenza dalla vecchia metadata. Questi sono limiti visibili, non dati inventati o acquisizioni future dichiarate completate.

La verifica dei dati congelati **non certifica la disponibilità attuale degli endpoint online**. Monitor, acquisizioni live e Radar restano separati. Il report registra soltanto file e trasformazioni effettivamente verificati.

## Revisione delle letture e riepiloghi

Le cinque ricette originali e tutti i loro risultati numerici rimangono intatti. L'audit aggiunge spiegazioni, fonti, ipotesi non verificate, opzioni non approvate, lacune e indicatori di monitoraggio in una sezione distinta. Non introduce un sesto percorso abitativo o finanziario dentro le 35 letture.

I due riepiloghi richiedono tutti i sette Comuni. I sei rapporti usano le componenti originali sommate; viene mostrata separatamente la media aritmetica comunale, per impedirne lo scambio con un aggregato ricostruito. Nel pendolarismo le somme lorde includono spostamenti interni al gruppo: non sono ingressi/uscite al confine Versilia. L'autocontenimento rimane lavoro nel **proprio Comune**, non autocontenimento dell'intera Versilia. Residenti 2021 e 2026 restano denominatori distinti.

`ci/a6-territorial-acceptance-questions.json` raccoglie problemi concreti di lavoro, scuola, assistenza, abitazione, mobilità, risorse e turismo. Ogni domanda descrive risposta oggi possibile, limiti, dati mancanti e valore conoscitivo, e rimanda a richieste con aspettative indipendenti già versionate. Il report espone indicatori, fonti, periodi, geografie, operazioni ammesse e rifiuti. `supported`, `partially_supported` e `not_determinable` qualificano la **domanda**, non il successo di una query di contesto. Un PASS dell'evidenza non rende risolvibile una domanda classificata non determinabile.

Abitazione e bilanci sono approfondimenti supplementari verificabili, senza nuove acquisizioni: non due percorsi originali A6.5. Accessibilità economica familiare della casa, numero di scuole/nidi/corse necessari e effetti degli interventi rimangono non determinabili dai soli indicatori disponibili. Il backlog informativo deriva dalle lacune esplicite del repertorio e delle letture; non viene azzerato artificialmente.

## Riproduzione e gate

Da checkout pulito, build pubblica governata e catalogo/registry effettivi adiacenti:

```bash
python scripts/preflight.py --quick
python scripts/preflight.py --full
python scripts/semantic_methodological_audit.py --catalog dist/data/site-data.json --output-dir /tmp/a6-methodological
```

Il report JSON restituisce exit nonzero se emergono errori; non può approvare o mergiare PR. Le verifiche indipendenti delle risposte e delle annotazioni sono integrate nel gate post-build esistente. Gli snapshot e la matrice sono identificati da hash; percorsi di provenienza differenti fra macchine non implicano numeri differenti.

Quick e Full locali devono essere sequenziali sul medesimo albero; CI Quick→Full e A3 sul candidato corrente; 40 golden, controlli browser e budget Lighthouse immutati. Camaiore resta congelata. Le evidenze e i log devono distinguere locale, CI, integrazione e pubblicazione. Solo dopo l'integrazione approvata delle PR funzionali verranno allineati roadmap/handoff e preparata l'attestazione amministrativa conclusiva. L'handoff A7 segue la chiusura reale di A6, senza UI conversazionale o servizi esterni anticipati.
