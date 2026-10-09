# A6 v23 — procedimenti SISBON

L'adapter legge i record congelati in `ambiente-acqua-v124-data.json`, riconciliati al manifest e al riepilogo della stessa acquisizione del 29 agosto 2026. CSV SISBON attestato SHA-256 `e5bd50e5b6a4a88b0f7bec0762b8719b69064ae1841bdbde925c5501e363dbcb`. Nessun dato acquisito o modificato da questo lotto.

152 codici regionali distinti, assegnati ai sette comuni; coordinate coincidenti non fondono procedimenti. Codici chiusi: 200, 210, 220, 230, 280. Attivi: 10, 40, 50, 60, 70, 120, 135, 140. Partizione esplicita, altri stati rifiutati. Identità comunali, record pubblici, componenti attivi/chiusi e totali devono riconciliarsi; duplicati rifiutati.

| Comune | Attivi | Chiusi | Tutti |
|---|---:|---:|---:|
| Camaiore | 9 | 22 | 31 |
| Forte dei Marmi | 10 | 11 | 21 |
| Massarosa | 6 | 10 | 16 |
| Pietrasanta | 10 | 13 | 23 |
| Seravezza | 3 | 6 | 9 |
| Stazzema | 3 | 4 | 7 |
| Viareggio | 15 | 30 | 45 |
| Totale | 56 | 96 | 152 |

`total` conserva il valore principale pubblico: **attivi**, alias `view:active`. `view:closed` legge i chiusi, `view:all` conta tutti i codici, `share:active` calcola attivi/tutti × 100. Compare e rank sono descrizioni dello stock amministrativo. Weighted ratio è consentito soltanto sulla quota, sommando componenti entro i comuni scelti, mai la media delle percentuali: Versilia 56/152 × 100 ≈ 36,8421%; Massarosa + Viareggio 21/61 × 100 ≈ 34,4262%.

Un procedimento attivo non equivale a un sito attualmente contaminato; chiuso non equivale necessariamente a bonificato. Conteggi e quota non misurano rischio, esposizione, efficacia o velocità di bonifica. L'acquisizione è uno stock, non un flusso annuo di nuovi procedimenti. Serie, variazioni e trend non hanno precedenti armonizzati; benchmark, anomalie e associazioni automatiche restano rifiutati. Acqua potabile mantiene i valori per località e parametro e resta fuori dal lotto: niente media comunale o indice sintetico.

35 osservazioni indipendenti per catalogo, alias inclusi; due quote aggregate, puntatori risolvibili e casi avversari. Suite 449 domande (242 calcoli, 207 rifiuti); copertura 145/225 effettivi, 97/181 sorgente, 80 residui e 16 ambientali. Report `reports/a6-remediation/`, 52 collegamenti e 58 carichi descrittivi. Dati, UI, asset, golden, Camaiore, workflow, Radar, 35 letture e due riepiloghi conservati. A6.4 parziale e A6.5–A6.6 aperte. Quick/Full locali e CI richiesti sul candidato; merge del proprietario.
