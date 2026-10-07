# A6 — adapter del censimento agricolo 2020

Il motore v13 aggiunge cinque indicatori: 118/225 effettivi e 85/181 sorgente. Residuo: 107 indicatori, 42 ambientali. Nessuna acquisizione o modifica dati/UI/golden/workflow. A6.4 resta parziale; letture A6.5–A6.6 da revisionare.

## Fonti e ambiti

Si riusa `data/source-snapshots/istat-agricoltura-territorio-2020.json`, flussi Istat HO/ARU/FUAA, colture localizzate e IA. Anno censuario 2020, annata agraria 2019/2020; superficie SITUAS al 31/12/2020. Non descrive lo stato corrente 2026.

| Indicatore/dimensione | Numeratore | Denominatore e limiti |
|---|---|---|
| Aziende agricole | HO, aziende con centro nel comune | Conteggio, distinto dalle sole aziende con SAU FUAA |
| SAU, totale | ARU/ALL/TOT localizzata nel comune, ettari | Non SAU attribuita per centro aziendale |
| SAU, `view:normalized` | SAU localizzata | Superficie comunale SITUAS in ettari × 100 |
| Dimensione media | SAU per centro aziendale | FUAA, aziende con SAU; non tutte le aziende HO |
| Colture, totale e `part:<codice>` | ALL e ARLAND/OLIVOOILTR/OLIVTTR/VINEY/PGRAPM localizzati | Selezione non esaustiva: nessun obbligo di sommare al totale, nessuna quota inventata |
| Irrigazione, totale | IA, ettari irrigati almeno una volta | Attribuzione per centro aziendale, non volume d'acqua né fabbisogno |
| Irrigazione, `view:normalized` | IA | SAU per centro aziendale × 100, non SAU localizzata |

Ogni carrier è riconciliato allo snapshot per identità, unità, periodo e valore; eventuali componenti A3 vengono controllate contro le componenti native. Risposte con hash, puntatori e scopi. Il centro aziendale può attribuire terreni esterni ai comuni selezionati: aggregare le aziende non delimita fisicamente tutti i loro terreni.

Tre aggregazioni ammesse: dimensione media, quota territoriale SAU, quota irrigata; sempre rapporto fra somme delle componenti coerenti. Nessuna media delle percentuali. Denominatori non positivi rifiutati. Mancanti pubblici restano mancanti anche con dati nativi disponibili.

## Limiti, benchmark e collegamenti

Nessuna serie o variazione 2010/2020/2026: è congelata una sola base censuaria. Vite mancante a Forte dei Marmi e olive da tavola mancanti in Forte/Stazzema/Viareggio restano null; copertura parziale richiede opt-in. I null non sono zeri. Non si deducono produttività, reddito, volume idrico, qualità o effetto di politiche.

La dimensione media usa Toscana/Italia da `a3-istat-agriculture-benchmark-2020.json`, componenti SAU per centro/FUAA riconciliate e gate PASS. I totali regionali/nazionali di aziende ed ettari hanno estensione differente dai valori comunali: scostamenti rifiutati. I benchmark delle quote normalizzate non hanno tutte le componenti territoriali omogenee congelate: rifiutati.

Il grafo aggiunge due contesti (37 totali): aziende/irrigazione per centro aziendale, associazione descrittiva soggetta a dimensione condivisa; SAU localizzata/irrigazione per centro, correlazione rifiutata per attribuzione diversa. Correlazione distinta da causalità; nessuna lettura agricola pubblicata in questo lotto.

## Verifiche

86 osservazioni indipendenti (84 celle comunali/dimensioni, incluse quattro mancanti, più due benchmark). Riferimenti trascritti, tre rapporti del gruppo, denominatore FUAA, componenti alterate, ambiti scambiati, null e gate di benchmark avversari. Suite cumulativa: 182 domande, 116 calcoli e 66 rifiuti attesi. Le 35 letture territoriali e due riepiloghi restano coperte dai gate esistenti.

```bash
python scripts/test_semantic_agriculture_adapters.py
python scripts/semantic_engine_audit.py --output-dir /tmp/a6-agriculture
python scripts/semantic_question_suite.py --output-dir /tmp/a6-agriculture
python scripts/semantic_engine_benchmark.py --output-dir /tmp/a6-agriculture
python scripts/preflight.py --full
```

Report e baseline di 28 carichi in `reports/a6-agriculture/`; misure sequenziali locali, senza promessa di latenza produttiva. Merge solo dopo gate e approvazione del proprietario.
