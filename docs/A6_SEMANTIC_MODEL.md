# A6 — Modello semantico minimo

## Scopo

A6 introduce un livello semantico deterministico sopra il catalogo canonico senza creare un secondo inventario di Comuni, temi o indicatori.

La fonte di verità resta `data/site-data.json`. Il semantic layer normalizza identità e relazioni; non inventa nuovi numeri e non interpreta causalmente i dati.

## Entità minime

| Entità | Identità canonica | Derivazione |
| --- | --- | --- |
| Comune | codice Istat | `data.towns[].code`, nome da `data.towns[].name` |
| Tema | chiave tema | chiave di `data.themes`; appartenenza indicatori da `theme.metrics` |
| Indicatore | chiave metrica | chiave di `data.metrics`; tema da `metric.meta.theme` |
| Periodo | token/anno dichiarato | corrente da `metric.meta.year`; storico da `series.years` |
| Dimensione | facet esplicita | solo strutture source-backed già presenti: parts, detailParts, normalized, ratioComponents |
| Fonte | etichetta + URL | `metric.meta.source` + `metric.sourceUrl` |
| Benchmark | riferimento esterno | `metric.meta.benchmark`, separato dall'osservazione comunale |

## Grana dell'osservazione

L'unità logica minima è:

`Comune × Indicatore × Periodo × Dimensione opzionale`

Ogni osservazione utilizzabile dal futuro motore A6 deve poter restituire almeno:

- codice Comune;
- chiave indicatore;
- chiave tema;
- periodo;
- unità;
- valore o stato n.d./n.a.;
- fonte;
- eventuale dimensione esplicita;
- benchmark separato, quando disponibile.

## Regole

1. **Nessun inventario parallelo.** Comuni, temi e indicatori sono sempre derivati dal catalogo.
2. **Nessuna dimensione dedotta dal testo.** Una dimensione esiste solo se il catalogo espone una struttura dati esplicita.
3. **Periodo esplicito.** Il dato corrente usa `meta.year`; una serie storica usa esclusivamente i periodi dichiarati in `series.years`.
4. **Fonte obbligatoria.** Etichetta e URL della fonte devono essere disponibili per ogni indicatore.
5. **Benchmark separato.** Toscana/Italia o altri riferimenti non diventano righe comunali.
6. **Missing data invariati.** `n.d.` e `n.a.` restano semanticamente distinti.
7. **Nessuna causalità.** A6 normalizza e calcola operazioni riproducibili; non introduce spiegazioni causali.

## Contratto machine-readable

`ci/semantic-model-contract.json` definisce il mapping e le invarianti senza elencare metriche o territori.

`scripts/semantic_model_contract.py` valida il contratto sul catalogo reale e controlla:

- unicità dei Comuni;
- coerenza bidirezionale tema ↔ indicatore;
- risoluzione delle righe comunali;
- periodo e fonte espliciti;
- allineamento `years` / `values` nelle serie;
- presenza di unità esplicite per i valori numerici;
- forma minima dei benchmark;
- presenza delle sole dimensioni già source-backed.

## Confine A6.1

A6.1 definisce il modello e i suoi invarianti. Non implementa ancora confronto, trend, rango, correlazione o anomalie: quelle operazioni appartengono ad A6.2.
