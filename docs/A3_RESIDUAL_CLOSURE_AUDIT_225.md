# A3.2 — Residual Closure Audit post-#225

## Baseline verificata

Audit diagnostico ricalcolato sulle **320 coppie indicatore × dimensione** realmente residue dopo il Full della PR #225.

- main post-merge #225: `0d10f8bb827bd56d2b59a22d96cf2411c4ece30a`
- catalogo pubblico: **225 indicatori**
- dimensioni A3.2: **9**
- matrice: **2.025 coppie**
- classificate: **1.705**
- residue: **320**
- Full #225: run `35259611965`, job `105333898344`, **GREEN**

L'audit non modifica `data/site-data.json`, `data/source-registry.json` o stati A3.2. Ricalcola soltanto la closure route diagnostica sulla fotografia corrente: i conteggi post-#223 non sono riutilizzati.

## Nuova matrice di closure

| Bucket | Significato | Coppie |
|---|---|---:|
| A | Falso residuo strutturale ancora presente | **43** |
| B | Cross-source / companion | **43** |
| C | Semanticamente `NOT_APPLICABLE` | **34** |
| D | Vera verifica fonte ufficiale necessaria | **200** |
| **Totale** |  | **320** |

### Distribuzione per dimensione

| Dimensione | A | B | C | D | Totale |
|---|---:|---:|---:|---:|---:|
| `serie_storica` | 2 | 0 | 0 | 24 | 26 |
| `sesso` | 1 | 0 | 10 | 24 | 35 |
| `eta` | 0 | 7 | 10 | 39 | 56 |
| `dettaglio_territoriale` | 2 | 0 | 0 | 4 | 6 |
| `benchmark_toscana_italia` | 1 | 0 | 0 | 6 | 7 |
| `assoluto_normalizzato` | 26 | 13 | 7 | 25 | 71 |
| `frequenza_infra_annuale` | 0 | 0 | 0 | 45 | 45 |
| `numeratore_denominatore` | 9 | 23 | 7 | 8 | 47 |
| `categorie_specifiche` | 2 | 0 | 0 | 25 | 27 |

## Lettura operativa

Il bucket **A resta significativo (43 coppie)**, quindi precede B. È composto da tre sottogruppi distinti:

1. **30 same-payload structural**: dato già presente nella metrica materializzata ma ancora non riconosciuto dal detector; chiusura generica tramite detector e regressioni.
2. **12 special-route**: coppie già strutturate nelle route canoniche `voterTurnout` e `economyActivityAtlas`, da chiudere con un contratto route-aware separato.
3. **1 external-climate**: `climatePrecipitationTrend50y / assoluto_normalizzato`, già rappresentato nel contratto climatico esterno, da trattare separatamente dal catalogo inline.

Il bucket **B (43)** comprende dimensioni che dipendono esplicitamente da una metrica o fonte companion già governata: soprattutto denominatori demografici, componenti di rapporti e disaggregazioni demografiche. Queste coppie non devono essere confuse con dati assenti dalla fonte primaria.

Il bucket **C (34)** contiene soltanto decisioni semanticamente metric-specific; nessuna regola `NOT_APPLICABLE` è applicata a un source profile eterogeneo.

Il bucket **D (200)** resta conservativo: il payload corrente non basta a distinguere `AVAILABLE_MISSING` da `SOURCE_UNAVAILABLE`; serve verifica della fonte ufficiale per ogni coppia o gruppo metodologicamente omogeneo.

## Ordine aggiornato di chiusura

1. A2 — same-payload structural: **30** coppie.
2. A3 — special-route + external climate: **13** coppie.
3. B — cross-source / companion: **43** coppie.
4. C — semantic closure: **34** coppie.
5. D — official-source evidence: **200** coppie.

A3.2 resta `IN_PROGRESS` fino a `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
