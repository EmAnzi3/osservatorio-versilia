# A6.4 — esempi riproducibili sul catalogo sorgente

Catalogo: `data/site-data.json`, SHA-256 `2a1f1ba0ee2ba4de98e12c00fe7e09c6a30d6edca2505f12587aefde1889a12b`.

Output derivato dal motore v1 e dalle query in `ci/semantic-query-examples.json`. Numeri della tabella arrotondati solo per leggibilità; JSON conserva la precisione degli input e dei calcoli. Non è una lettura di politica pubblica.

| Esempio | Esito | Risultato / motivo |
|---|---|---|
| residenti_correnti | computed | 7 osservazioni comunali con periodo e provenienza |
| residenti_massarosa_2019_2026 | computed | 86.000000 number |
| reddito_massarosa_2011_2024 | computed | 30.129876 percent_change |
| trend_reddito_massarosa | computed | 400.872296 currency/year · n=4 |
| associazione_periodi_correnti_rifiutata | not_computable | paired_period_mismatch |
| associazione_2024_descrittiva | computed | Spearman 0.428571 · n=7 · esclusione di un comune: 0.085714–0.942857 |

## Provenienza e limiti

- Residenti: dati al 1° gennaio; ogni osservazione riconciliata con il record POSAS nel file versionato `data/source-snapshots/istat-demography-lotto-a-2026-08.json`, conservando URL annuale, hash e stato dello snapshot.
- Reddito: imponibile medio per la relativa frequenza dei dichiaranti, euro nominali. Il catalogo e la nota di omogeneità sono versionati; questo adapter non verifica gli archivi grezzi MEF. Non mescolare con reddito complessivo, reddito familiare o potere d’acquisto.
- Correlazione 2024: residenti al 1 gennaio e reddito nell’anno fiscale hanno universi e riferimenti temporali diversi, espliciti negli output. Il coefficiente è un esempio tecnico di associazione comunale, non causalità, effetto atteso o priorità di politica.
- Sono restituite sensibilità, coppie/esclusioni, n e avvertenze. Nessun p-value o intervallo inferenziale automatico su sette comuni.
- Questi esempi non incorporano nuovi dati, non trasformano uno snapshot in prova del servizio live e non cambiano le superfici pubbliche.

## Riproduzione

```bash
python scripts/semantic_query_engine.py --examples ci/semantic-query-examples.json --output /tmp/a6-query-examples.json
python scripts/semantic_query_engine.py --coverage --output /tmp/a6-query-coverage.json
```

Per il catalogo effettivo usare `--catalog dist/data/site-data.json --layer effective` dopo build. Gli hash dei due cataloghi sono distinti; ogni osservazione conserva il suo JSON Pointer. La matrice effettiva comprende tutti gli indicatori pubblici e segnala gli adapter ancora mancanti.
