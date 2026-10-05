# A6.4 — primo motore deterministico

## Stato e perimetro

Dopo #331, #332 e il merge manuale di #333 (`84bbadec`, deploy `37271484406` SUCCESS), il motore `scripts/semantic_query_engine.py` esegue query strutturate sui dati già pubblicati. Il motore supporta **residenti POSAS**, **reddito imponibile medio MEF** distribuzione per otto fasce d’età POSAS e quattro rapporti censuari: occupazione femminile/maschile 15–64 anni, abitazioni totali e non occupate da residenti ogni 1.000 abitanti. Dimensione `total`: i due indicatori di occupazione hanno già un universo per sesso esplicito; non sono un adapter generico dei carrier sesso. La copertura rimane parziale: A6.4 non è chiusa e non abilita A7 o nuove superfici pubbliche. Contratto A6.2–A6.3, interfaccia, dati e golden preservati.

Undici operazioni implementate: confronto, serie, variazione assoluta/relativa, punti percentuali, scostamento dal benchmark, rapporto ponderato, rango, trend OLS correlazione Pearson/Spearman e screening IQR esplicito; altri indicatori e dimensioni richiedono adapter espliciti. Supporto per operazione derivato dagli adapter: non tutte le undici operazioni sono valide per tutte le sette metriche. Non estendere automaticamente un adapter da `unit` o dal nome dell'indicatore.

## Input e selezione

Una query contiene `operation` e uno o due `selectors` (due per correlazione). Ogni selettore specifica `metric`, opzionalmente `dimension` (`total` per i sei adapter precedenti; fascia esplicita per `ageDistribution`), codici comunali `towns` e `periods`. Nessun metadato di metodo/unità/definizione può essere iniettato dal chiamante: deriva dagli adapter controllati. Campi sconosciuti o non pertinenti sono rifiutati. I codici devono appartenere al catalogo validato A6.1, senza duplicati.

Per confronto, rango, anomalia, rapporto ponderato e scostamento dal benchmark si seleziona un periodo. Senza periodi espliciti si usa il dato corrente; con periodi espliciti si usa il punto storico realmente presente. Per serie/trend/variazioni si seleziona un comune; i periodi annuali di questi adapter hanno esattamente quattro cifre, sono univoci e crescenti. Il motore non converte anni scolastici, mesi, date o norme composite in anni. Altri adapter potranno usare altre frequenze, con regole proprie. Senza periodi espliciti una query temporale usa gli anni disponibili, ordinati, senza interpolazione.

La selezione non elimina silenziosamente territori o periodi richiesti ma assenti: restituisce motivo di non calcolabilità. Nessuna aggregazione implicita o denominatore ricostruito dal dato medio.

## Adapter, fonte e versione

`istat-posas-population/v1` richiede unità/definizione e fonte Istat coerenti. Ogni valore selezionato viene confrontato con il record di comune/anno dello snapshot POSAS versionato. Restituisce il download ufficiale specifico dell'anno, hash del file, data e stato dello snapshot. Il riferimento è uno stock al 1 gennaio: non un flusso o una media annuale. Snapshot e URL dichiarati non dimostrano disponibilità live.

`mef-taxable-income/v1` richiede unità monetaria, fonte MEF e nota pubblicata di omogeneità dell'imponibile. Usa il catalogo versionato e la nota di metodo, preservando il limite **raw_income_archive_not_verified_by_adapter**. Non dichiara verificati archivi che non legge. La selezione corrente/storica dello stesso anno deve riconciliarsi. Periodo = anno d'imposta, distinto da anno di pubblicazione; euro nominali, non reddito complessivo o potere d'acquisto. Ogni cambio di definizione richiede revisione dell'adapter.

Le dichiarazioni metodologiche degli adapter e le note del catalogo sono evidenze da revisionare: il motore non ne prova automaticamente il contenuto. Il suo risultato riguarda gli input versionati effettivamente letti.

## Output e riproducibilità

Output JSON: stato `computed`/`not_computable`, query originale, formula, policy, osservazioni, copertura, esclusioni con motivi, avvertenze e risultato. Provenienza per osservazione: chiave/dimensione, territorio, periodo/base temporale, unità/universo/definizione/metodo/frequenza, fonte, JSON Pointer del valore e del periodo, hash del catalogo, eventuali snapshot e versione dell'adapter. Radice: versione/hash del motore, hash del contratto e delle guardie di ammissibilità, percorso/hash del catalogo.

Il catalogo e gli snapshot letti sono congelati nell'istanza del motore; modifiche esterne richiedono una nuova istanza. Query e risultati non condividono oggetti mutabili con gli input interni. A parità di file e query non ci sono timestamp runtime o estrazioni casuali: risultato riproducibile. Nessun arrotondamento del calcolo; eventuale formattazione del report è separata.

Null, n.d. e n.a. non diventano zero. Le esclusioni richiedono `allowPartial: true`, copertura e motivi espliciti; il risultato conserva anche le osservazioni originali. I mancanti storici non ereditano automaticamente lo stato della riga corrente. Trend e serie parziali mantengono le distanze fra gli anni, senza comprimere i buchi. Variazioni richiedono due valori; base zero rifiutata.

## Calcoli e interpretazione

Il motore applica prima `semantic_operations.assess`. Rango decrescente con pari merito e salti, ordinamento stabile per codice; non è un giudizio di qualità. Trend = pendenza OLS sul vero asse annuale, unità per anno, senza previsione. Le variazioni relative hanno unità `percent_change`. Differenze di tassi percentuali, compresi scostamenti dal benchmark, hanno unità `percentage_points`; le pendenze di tassi hanno unità `percentage_points/year`. Per gli altri valori le differenze conservano l'unità originale.

Correlazioni: due variabili selezionate, `method` Pearson/Spearman, `axis` municipalities/periods e `purpose` esplicito. Stesso periodo/frequenza per coppia; nelle serie temporali stesso comune e contesto coerente per ogni variabile. Pairing per codice o periodo, mai posizione negli array. Coefficienti Spearman su ranghi medi per i pari. Variabili costanti e coppie insufficienti vengono rifiutate; gli errori numerici non producono NaN/Infinity pubblicabili.

L'output conserva coppie usate/escluse, n e sensibilità all'esclusione di un'osservazione quando rimangono almeno tre coppie. Se un'esclusione rende una variabile costante, il coefficiente è null. Nessun p-value o intervallo inferenziale automatico. Universi diversi e stock/flusso restano dichiarati e accompagnati da avvertenze. Analisi comunale non implica proprietà individuali, causalità o effetto di una politica; le serie aggiungono avvertenze su trend comuni/autocorrelazione. Una motivazione testuale non è una certificazione metodologica della coppia.

## Copertura e uso

`--coverage` deriva una voce per ogni indicatore del catalogo, conservando i carrier scoperti da A6.2–A6.3. Gli adapter presenti sono segnalati con operazioni/dimensioni supportate e precondizioni ancora applicabili; gli altri hanno un motivo esplicito. Presenza dell'adapter non garantisce qualsiasi query. Contenitori sesso/lavoro/ERP, benchmark e MIMIT mensile esterno non vengono appiattiti nella dimensione principale o nascosti come supportati.

```bash
python scripts/semantic_query_engine.py --query /tmp/query.json --output /tmp/result.json
python scripts/semantic_query_engine.py --examples ci/semantic-query-examples.json --output /tmp/examples.json
python scripts/semantic_query_engine.py --catalog dist/data/site-data.json --layer effective --coverage
```

Esempi realmente eseguiti: `reports/a6-query-engine.md`; richieste riproducibili: `ci/semantic-query-examples.json`. Questo file contiene domande, non un inventario canonico o copie di valori.

## Verifiche e passi successivi

Regressioni numeriche indipendenti: Pearson con riferimento algebrico, Spearman con pari merito, pendenza su intervalli irregolari, variazione percentuale e rango. API: periodi/geografie/duplicati/campi impropri, adapter assenti, versione/hash/puntatori, input congelati, zero base, mancanti/esclusioni/pairing, costanti, selezione di periodi incompatibili e omogeneità corrente/storico. Audit Quick sul sorgente e dopo build sul catalogo effettivo, senza workflow nuovo.

Proseguire A6.4 con dimensioni versionate, benchmark e componenti/denominatori, adapter esterni, precisione/arrotondamenti espliciti e altre formule; aggiornare la matrice derivata e i test numerici per ogni estensione. A6.5 richiede domande territoriali e revisione del metodo prima di formulare proposte; A6.6 porta limiti dentro le letture pubbliche. L'AI di A7 dovrà esprimere risultati verificati del motore, con riferimenti e limiti conservati.

## Rapporti censuari e benchmark — secondo lotto

Gli adapter `istat-census-<metric>/v1` leggono lo snapshot `istat-sections-history-v1.8.0.json` (2021 e 2023), controllano identità codice/nome, definizione/unità/fonte, attestazione di comparabilità, conteggi finiti non negativi e denominatori positivi. Ogni punto corrente/storico selezionato viene riconciliato al rapporto originale entro 1e-8 assoluto, senza aumentare la tolleranza delle guardie A6.3 o usare dati arrotondati per ricostruire conteggi. URL annuale, record/colonne, hash del workbook e del file snapshot restano visibili. Il censimento non è equiparato allo stock POSAS al 1 gennaio.

`weighted_ratio` è abilitata per questi quattro rapporti e per le otto fasce POSAS: somma dei numeratori / somma dei denominatori × scala. Comuni ufficiali distinti e conteggi additivi per residenza costituiscono l'evidenza del perimetro disgiunto; mai sommare Toscana/Italia ai Comuni. Non è la media dei valori comunali. Si restituiscono somme, scala, periodo e codici effettivamente inclusi. Una selezione con dati mancanti richiede opt-in e rimane parziale: non viene etichettata come intera Versilia. Residenti e reddito non hanno un adapter di rapporto comunale verificato e vengono rifiutati da questa operazione. I conteggi in snapshot non riempiono automaticamente valori null pubblicati.

`percentage_points` richiede due punti percentuali dello stesso indicatore, Comune, universo e metodo, in ordine temporale. Non confronta implicitamente due metriche diverse o unità monetarie/per-mille. La variazione relativa resta distinta: 50% → 55% = +5 punti, +10% relativo.

`benchmark_gap` richiede un solo Comune e `benchmark: tuscany | italy` esplicito. Supporta i quattro rapporti censuari nel 2023 e imponibile MEF nel 2024. Non sceglie automaticamente un benchmark o un anno alternativo; il 2021 censuario è rifiutato. Le evidenze comunali e regionali/nazionali sono distinte. Snapshot censuario: profilo, anno, unità/formula, gate, 20 workbook regionali, stesso workbook Toscana del dato comunale; si ricalcola il benchmark dai conteggi. Snapshot MEF: imponibile/frequenza corrispondente, anno d'imposta, archivi/hash/gate e scope nazionale dichiarato; non viene mescolato al reddito complessivo. Il limite sugli archivi storici comunali MEF non cambia. Se il catalogo effettivo contiene il benchmark, anno/path/valore devono riconciliarsi allo snapshot: un carrier obsoleto non viene ignorato.

`sourceSnapshot` è un'evidenza versionata, non una prova live. Questi calcoli non acquisiscono nuovi dati e non sostituiscono il monitor. Il modulo adapter ha un proprio SHA-256 nell'output; input esterni non possono iniettare attestazioni, formule, scale o denominatori.

Regressioni: rapporto di somme con pesi diseguali e riferimento razionale indipendente; 2021/2023 su quattro adapter; punti vs variazione relativa; due scope benchmark su cinque adapter; mancanti con/senza opt-in e perimetro ridotto; zero denominatore, valore pubblico alterato, benchmark alterato/obsoleto, periodo diverso, scope ignoto e iniezione. Dopo build il gate ripete confronto, aggregazione e benchmark sul catalogo effettivo. Nessun nuovo workflow.

Restano altri adapter, carrier sesso e altre dimensioni composite, benchmark di altri profili e rapporti con precisione pubblicata arrotondata. Non estendere gli adapter ai rapporti arrotondati senza una regola esplicita di riconciliazione. A6.4 rimane parziale; A6.5 e A6.6 devono trasformare domande ed evidenze in letture territoriali revisionabili, distinguendo contesti e calcoli congiunti.


## Fasce d’età e anomalie — terzo lotto

`istat-posas-age-band/v1` richiede `dimension` esplicita: `age:0-14`, `age:15-19`, `age:20-34`, `age:35-49`, `age:50-64`, `age:65-79`, `age:80-84`, `age:85+`. Non esiste una dimensione `total`: il valore primario della card è la quota 20–34, non l’intera distribuzione né l’età media. Questi ID sono regole di selezione dell’adapter, non un inventario parallelo di indicatori. Il dato disponibile è solo lo stock POSAS al 1° gennaio 2026; serie, trend e variazioni sono rifiutati. Non viene fabbricato uno storico da un carrier corrente.

Ogni osservazione legge `parts` e riconcilia tutte le otto fasce ai 101 record di età nello snapshot POSAS già versionato (100 = 100 anni e oltre). Verifica età uniche/esaurienti, conteggi interi non negativi, uomini + donne = totale, somma delle età = popolazione comunale dello stesso anno, partizioni esaurienti/non duplicate e quote/count coerenti. Valori null restano null; un anno esplicito conserva lo stato n.a./n.d. della riga corrente. URL ufficiale 2026, hash/stato/data snapshot, fascia, numeratore/denominatore e Pointer di `parts` sono conservati. La piramide e l’età media non sono ancora adapter del motore.

Confronto, rango, aggregazione ponderata, correlazione e screening IQR operano sulla fascia selezionata. Il rapporto di somme usa residenti della fascia / residenti totali del perimetro, mai la media semplice delle quote. Le correlazioni tra due fasce vengono appaiate per **metrica e dimensione**: nessuna sovrascrittura della prima variabile. Restano un’associazione ecologica e composizionale con denominatore condiviso; non provano causalità. Benchmark delle otto fasce ora abilitati nel quarto lotto, da conteggi regionali/nazionali esaurienti.

`anomaly` richiede `rule: tukey_1_5_iqr`, `reference: selected_municipalities` e un `purpose` non vuoto. Usa un singolo indicatore/dimensione e periodo. Non accetta distribuzioni, soglie o evidenze fornite dal chiamante: il riferimento è il gruppo comunale realmente selezionato, documentato con osservazioni e provenienza. Quartili mediante interpolazione lineare alla posizione `(n−1)×p` (type 7); intervallo `[Q1−1,5×IQR, Q3+1,5×IQR]`. Valori esattamente sui limiti sono interni. Output: n, mediana, quartili/IQR, limiti, unità e classificazione descrittiva di ogni comune.

Minimo quattro osservazioni utilizzabili; IQR zero rifiutato, senza soglie alternative automatiche. Mancanti richiedono opt-in e modificano il gruppo di riferimento: esclusioni e n rimangono espliciti. Il risultato avverte sempre che i pochi comuni non sono un campione inferenziale, che scegliere il gruppo cambia i limiti e che un valore esterno non prova errore, qualità, bisogno o priorità di politica. Non vengono calcolati p-value, rischi individuali, allarmi live o proposte automatiche.

Il lotto restringe inoltre l’attestazione censuaria agli anni presenti in `acceptedIndicators.years`: un nuovo record grezzo non eredita automaticamente la comparabilità di 2021/2023. Test numerici indipendenti dei quartili e dei valori sui limiti; regressioni di conteggi, completezza, mancanti, n.a., denominatori e pairing; verifica dopo build su tutte le otto fasce e su screening IQR. A6.4 rimane parziale; A6.5–A6.6 e A7 restano aperti.

## Quarto lotto — dimensioni e letture territoriali

Base pubblicata #334, main `c0e018d8`, deploy `37276777611` SUCCESS. Motore v4: dieci adapter sul sorgente e undici sul catalogo effettivo, con copertura derivata di tutti i 225 indicatori pubblici. Supporto distinto per dimensione, operazione e scope benchmark; presenza del carrier non equivale a supporto generale.

- POSAS: uomini/donne 2026 dai carrier effettivi, riconciliati ai 101 record di età; nessuno storico per sesso inventato. Le otto fasce hanno benchmark Toscana/Italia 2026 ricalcolati dai conteggi: il benchmark primario 20–34 non viene usato per 85+ o altre fasce.
- Prima infanzia: ricettività potenziale / residenti 3–36 mesi, anno educativo esatto `2024/25`, rapporto di somme e benchmark Toscana. Zero verificati conservati. Non è frequenza, accessibilità, qualità o bisogno insoddisfatto. Italia e serie assenti vengono rifiutate.
- Turismo: presenze 2023–2025 senza locazioni; intensità = notti 2025 / residenti POSAS 2026. Entrambi i periodi rimangono nei risultati, anche aggregati e benchmark Toscana. Notti annuali non sono persone, picchi o pressione effettiva sui servizi. Nessun benchmark Italia inventato.
- ARS 260: tasso domiciliare standardizzato 2024, totale/uomini/donne, dal carrier effettivo e dallo snapshot; valori non arrotondati, benchmark ufficiali Toscana/Versilia. Numeratori e denominatori grezzi restano evidenze del tasso grezzo: non sono pesi del tasso standardizzato. Aggregazione e storico per sesso vengono rifiutati.

`semantic_query_territorial_adapters.py` ha SHA-256 separato nell’output. Nessuna nuova acquisizione live: sono controllati gli input versionati. Le regressioni post-build includono componenti alterate, carrier obsoleti, mancanti, periodi non allineati e benchmark assenti. Il prototipo A6.5 è documentato in `docs/A6_TERRITORIAL_READINGS.md` e generato in `reports/a6-territorial-readings.md`. A6.4 resta parziale e A6.5–A6.6 richiedono revisione; A7 non è avviata.
