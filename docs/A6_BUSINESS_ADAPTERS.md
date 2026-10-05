# A6 — business Istat sui dati già acquisiti

Lotto successivo alla #339 pubblicata, main `4775c587`. Motore v6: 16 indicatori business aggiuntivi, **45 con adapter / 180 senza su 225** nel catalogo effettivo. Fonte canonica, dati pubblicati e UI invariati. Il catalogo sorgente non materializzato ha una copertura diversa, dichiarata separatamente dal gate.

## Universi, dimensioni e misure

| Famiglia | Indicatori | Dimensioni interrogabili | Evidenza |
|---|---|---|---|
| ASIA unità locali | localUnits, localEmployees, employeesPerLocalUnit, localUnitsChange, localEmployeesChange | totale; storici 2018–2023 | `agid-asia-agcom-2026-08.json`; acquisizione AgID dichiarata, titolare Istat |
| ASIA micro unità | microUnits | totale 2023; quota pubblicata arrotondata | CSV ufficiali congelati in `a3-istat-micro-units-benchmark-2023.json`, SHA e classi TOTAL/W0_9 riconciliati |
| Frame SBS | businessTurnover, businessValueAdded, labourProductivity, turnoverPerPersonEmployed, valueAddedTurnoverShare, averageGrossRemunerationPerEmployee, labourCost, grossOperatingMargin | totale, `sector:industry`, `sector:services`; storici pubblicati | manifest `economia-prodotta-frame-sbs-v134.json` e tre parti, righe/tavole/archivi e SHA per anno |
| Composizione Frame | industryValueAddedShare, industryWorkerShare | quota industriale sul totale industria e servizi; storici | componenti industria/totale negli stessi snapshot Frame |

Gli addetti sono osservati sul luogo di lavoro e non equivalgono ai residenti occupati. ASIA e Frame hanno universi diversi; non si mescolano automaticamente i loro componenti. Il valore aggiunto Frame non è il PIL comunale. Valori monetari, produttività e retribuzioni sono nominali: una variazione non certifica crescita reale o potere d'acquisto.

Il costo del lavoro e il MOL hanno serie 2021–2023; gli altri otto indicatori Frame/composizione arrivano al 2015. La disponibilità viene letta dai carrier e riconciliata con il record sorgente; non vengono riempiti anni assenti. I null restano mancanti e le letture parziali richiedono consenso esplicito tramite `allowPartial`.

## Periodi e aggregazioni

Le variazioni ASIA mantengono il riferimento completo `2018-2023`. Le serie vengono selezionate come `2018-2018`, `2018-2019`, …, `2018-2023`, con anno iniziale ed endpoint espliciti. Un token `2023` non significa la variazione cumulata; trend e correlazioni temporali su queste sequenze sono rifiutati. Una differenza tra due valori cumulati è una differenza in punti percentuali, non una crescita anno su anno del livello.

Le misure ufficiali Frame arrotondate vengono conservate: produttività, retribuzione per dipendente e VA/fatturato non vengono sostituite con il rapporto ricalcolato dai conteggi. Micro unità conserva la precisione pubblicata di due decimali (riconciliazione entro 0,0051 punti). Gli altri valori devono riconciliare entro 0,000001 nelle rispettive unità.

`weighted_ratio` è abilitato esclusivamente per addetti/UL ASIA, fatturato/addetto Frame e le due quote industriali. Usa rapporto delle somme di componenti nelle geografie comunali distinte, con perimetro economico e conversioni espliciti. Non è la media dei tassi comunali. Non si aggregano settori sovrapposti, rapporti ufficiali arrotondati o variazioni cumulative usando pesi impliciti.

## Benchmark e residui

Toscana/Italia correnti sono riconciliate ai record congelati ASIA e Frame, con carrier pubblico e provenienza distinti. I rapporti regionali usano le stesse formule o i campi ufficiali arrotondati della tavola. Non vengono inventati benchmark storici o benchmark dei singoli settori.

Per le due quote industriali i benchmark pubblicati rimangono nel catalogo e nel sito: questo adapter non li interroga perché lo snapshot regionale letto non congela i componenti industria/totale. Lo stesso limite vale per riferimenti regionali di settore. Nessuna cancellazione o riclassificazione A3. I carrier `aggregate` Versilia restano pubblicati, ma non sono abbinati a `benchmark_gap` in questo lotto: le regole di aggregazione e precisione vanno verificate separatamente; i quattro rapporti ammessi si possono già calcolare sui sette Comuni con `weighted_ratio`. La normalizzazione ASIA per residente pubblicata resta fuori dalle dimensioni interrogabili di questo lotto: non si attribuisce un periodo al denominatore senza evidenza.

Il manifest Frame ereditato associa il 2017 a una pagina il cui URL contiene `anno-2016`: il record/file 2017 resta congelato e il motore aggiunge `source_release_url_label_differs_from_reference_year`. La pagina non viene dichiarata verificata o corretta da questo lotto; provenienza del file e URL dichiarato restano distinguibili.

Ogni risultato conserva pointer del valore e del periodo, snapshot/record/tavola, URL della fonte, hash e versione dell'adapter. Per le serie cumulative il pointer dell'anno è accompagnato da baseline/endpoint espliciti. Gli hash degli archivi Frame sono quelli dichiarati nel manifest; il motore non rilegge i file XLSX originali. Uno snapshot o CSV congelato non prova disponibilità live: nessuna richiesta di rete nell'adapter.

## Collegamenti e accettazione

La mappa aggiunge tre dipendenze matematiche riconciliate: ASIA addetti e UL con il rapporto addetti/UL; fatturato Frame in milioni convertito in euro con il numeratore del fatturato/addetto. Aggiunge tre collegamenti di contesto: lavoro locale/occupazione femminile residente, unità locali/turismo, produzione/reddito residente. Nessun arco causale o correlazione automatica autorizzata dalla semplice appartenenza al gruppo.

La coppia lavoro/occupazione femminile 2023 è descrittivamente interrogabile sui sette Comuni, con scopo, universi e sensibilità leave-one-out espliciti; gli altri due accostamenti correnti sono rifiutati per periodi diversi. Non si deducono risultati individuali o effetti delle politiche.

**50 domande: 33 calcoli e 17 rifiuti attesi**, con numeri/ranghi trascritti separatamente dall'output del motore. Il gate verifica tutte le dimensioni correnti, tutti i sette Comuni e le loro serie ammesse, benchmark disponibili, componenti, duplicati, hash CSV e carrier alterati. Il contratto semantico intercetta anche periodi duplicati prima della query.

```bash
python scripts/test_semantic_business_adapters.py
python scripts/semantic_engine_audit.py --catalog dist/data/site-data.json --output-dir /tmp/a6-business-audit
python scripts/semantic_question_suite.py --catalog dist/data/site-data.json --output-dir /tmp/a6-business-questions
python scripts/semantic_engine_benchmark.py --catalog dist/data/site-data.json --rounds 50 --output-dir /tmp/a6-business-performance
```

La baseline separata è in `reports/a6-business/performance.*`: nove carichi, inclusi rapporto industriale e rifiuto del periodo finale. Non è uno stress test, una prova concorrente o un SLO. I gate sono integrati nel preflight generale esistente; nessun nuovo workflow. A6.4 rimane parziale, A6.5–A6.6 aperte alla revisione, A7 non avviata. Merge solo su istruzione specifica del proprietario.
