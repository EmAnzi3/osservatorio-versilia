# A6.4 — primo motore deterministico

## Stato e perimetro

Dopo il merge manuale di #331 (`a3574070`, deploy `37240258981` SUCCESS), il motore `scripts/semantic_query_engine.py` esegue query strutturate sui dati già pubblicati. Questo primo lotto supporta **residenti POSAS** e **reddito imponibile medio MEF**, dimensione `total`. La copertura rimane parziale: A6.4 non è chiusa e non abilita A7 o nuove superfici pubbliche. Contratto A6.2–A6.3, interfaccia, dati e golden preservati.

Operazioni implementate: confronto, serie, variazione assoluta/relativa, rango, trend OLS e correlazione Pearson/Spearman. Benchmark, punti percentuali, rapporti ponderati e anomalie rimangono **operation_not_implemented**; altri indicatori e dimensioni richiedono adapter espliciti. Non estendere automaticamente un adapter da `unit` o dal nome dell'indicatore.

## Input e selezione

Una query contiene `operation` e uno o due `selectors` (due per correlazione). Ogni selettore specifica `metric`, opzionalmente `dimension` (solo `total`), codici comunali `towns` e `periods`. Nessun metadato di metodo/unità/definizione può essere iniettato dal chiamante: deriva dagli adapter controllati. Campi sconosciuti o non pertinenti sono rifiutati. I codici devono appartenere al catalogo validato A6.1, senza duplicati.

Per confronto e rango si seleziona un periodo. Senza periodi espliciti si usa il dato corrente; con periodi espliciti si usa il punto storico realmente presente. Per serie/trend/variazioni si seleziona un comune; i periodi annuali di questi adapter hanno esattamente quattro cifre, sono univoci e crescenti. Il motore non converte anni scolastici, mesi, date o norme composite in anni. Altri adapter potranno usare altre frequenze, con regole proprie. Senza periodi espliciti una query temporale usa gli anni disponibili, ordinati, senza interpolazione.

La selezione non elimina silenziosamente territori o periodi richiesti ma assenti: restituisce motivo di non calcolabilità. Nessuna aggregazione territoriale o denominatore ricostruito dal dato medio.

## Adapter, fonte e versione

`istat-posas-population/v1` richiede unità/definizione e fonte Istat coerenti. Ogni valore selezionato viene confrontato con il record di comune/anno dello snapshot POSAS versionato. Restituisce il download ufficiale specifico dell'anno, hash del file, data e stato dello snapshot. Il riferimento è uno stock al 1 gennaio: non un flusso o una media annuale. Snapshot e URL dichiarati non dimostrano disponibilità live.

`mef-taxable-income/v1` richiede unità monetaria, fonte MEF e nota pubblicata di omogeneità dell'imponibile. Usa il catalogo versionato e la nota di metodo, preservando il limite **raw_income_archive_not_verified_by_adapter**. Non dichiara verificati archivi che non legge. La selezione corrente/storica dello stesso anno deve riconciliarsi. Periodo = anno d'imposta, distinto da anno di pubblicazione; euro nominali, non reddito complessivo o potere d'acquisto. Ogni cambio di definizione richiede revisione dell'adapter.

Le dichiarazioni metodologiche degli adapter e le note del catalogo sono evidenze da revisionare: il motore non ne prova automaticamente il contenuto. Il suo risultato riguarda gli input versionati effettivamente letti.

## Output e riproducibilità

Output JSON: stato `computed`/`not_computable`, query originale, formula, policy, osservazioni, copertura, esclusioni con motivi, avvertenze e risultato. Provenienza per osservazione: chiave/dimensione, territorio, periodo/base temporale, unità/universo/definizione/metodo/frequenza, fonte, JSON Pointer del valore e del periodo, hash del catalogo, eventuali snapshot e versione dell'adapter. Radice: versione/hash del motore, hash del contratto e delle guardie di ammissibilità, percorso/hash del catalogo.

Il catalogo e gli snapshot letti sono congelati nell'istanza del motore; modifiche esterne richiedono una nuova istanza. Query e risultati non condividono oggetti mutabili con gli input interni. A parità di file e query non ci sono timestamp runtime o estrazioni casuali: risultato riproducibile. Nessun arrotondamento del calcolo; eventuale formattazione del report è separata.

Null, n.d. e n.a. non diventano zero. Le esclusioni richiedono `allowPartial: true`, copertura e motivi espliciti; il risultato conserva anche le osservazioni originali. I mancanti storici non ereditano automaticamente lo stato della riga corrente. Trend e serie parziali mantengono le distanze fra gli anni, senza comprimere i buchi. Variazioni richiedono due valori; base zero rifiutata.

## Calcoli e interpretazione

Il motore applica prima `semantic_operations.assess`. Rango decrescente con pari merito e salti, ordinamento stabile per codice; non è un giudizio di qualità. Trend = pendenza OLS sul vero asse annuale, unità per anno, senza previsione. Le variazioni hanno unità originale o `percent_change`, distinto dai punti percentuali.

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
