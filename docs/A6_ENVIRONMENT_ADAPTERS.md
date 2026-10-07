# A6 — adapter ambientali: acqua e rifiuti

Il motore v12 aggiunge cinque indicatori congelati: 113/225 adapter effettivi e 80/181 sorgente. Restano 112 indicatori senza adapter, di cui 47 ambientali. Dati pubblici e interfaccia restano invariati; A6.4 è parziale, A6.5–A6.6 richiedono ancora revisione metodologica.

## Evidenze e operazioni

| Indicatore | Evidenza congelata | Operazioni e limiti |
|---|---|---|
| Perdite idriche | `ambiente-acqua-v124-data.json`, volumi immessi/erogati Istat 2012, 2015, 2018 | Rapporti esatti e aggregazione da somme dei volumi; confronto, serie, variazioni e trend sui periodi osservati. Il 2018 non descrive la rete del 2026; componenti fisiche/amministrative delle perdite non separate. |
| Raccolta differenziata | Carrier ISPRA nel catalogo canonico, 2010–2024 | Quota pubblicata, non riciclo effettivo. Confronti comunali 2024 e benchmark; serie consultabili senza attestare continuità metodologica. |
| Rifiuti per residente | Carrier ISPRA nel catalogo canonico, 2010–2024 | Kg pubblicati arrotondati; residenti diversi da popolazione presente o produzione dei turisti. |
| Rifiuti residui per residente | Stessi carrier, formula totale × (1 − quota RD / 100) | Formula riconciliata alle due componenti arrotondate e al valore pubblico; non misura diretta di smaltimento. |
| Costo servizio rifiuti | `costi-fiscalita-validated-2026-08.json`, CTOTab 2024, N. comuni = 1 | Euro/abitante/anno; non TARI della famiglia, qualità o efficienza. Solo 2024. |

La provenienza di ogni osservazione conserva snapshot, hash e puntatori. Per i rifiuti il catalogo canonico è evidenza congelata dei carrier pubblicati: tonnellaggi comunali originali e denominatori residenti non sono conservati. Il motore verifica la precisione disponibile senza inventare componenti. Valori mancanti restano mancanti; coperture incomplete richiedono opt-in esplicito.

L'aggregazione idrica somma acqua persa e immessa: **non** media percentuali né pesa per residenti. Per tutti e quattro gli indicatori rifiuti, la ponderazione è rifiutata senza componenti additive verificate. Serie rifiuti disponibili, ma variazioni assolute/relative, punti percentuali, trend e correlazioni temporali sono rifiutati: gli snapshot non attestano autonomamente la continuità metodologica storica. Non si attribuisce una discontinuità a un anno specifico senza evidenza.

## Benchmark e collegamenti

Toscana/Italia usano gli snapshot `a3-istat-water-benchmark-2018.json`, `a3-ispra-environment-benchmark-2024-v2.json` e, per i costi, `a3-ispra-environment-benchmark-2024.json`. Gate PASS, anno, unità, profilo, riferimento e valori pubblici vengono riconciliati. Acqua: precisione aggregata ufficiale arrotondata. Rifiuti: rapporti da somme provinciali; il residuo comunale da carrier arrotondati ha una precisione distinta. Costi: CTOTab dei campioni dichiarati, non costo complessivo di tutti i comuni della regione/nazione.

Tre collegamenti aggiuntivi portano il grafo a 35: formula dei residui con entrambe le componenti; costo/quantità come contesto 2024; acqua/rifiuti come contesto con periodi 2018/2024 incompatibili per una correlazione contemporanea. Nessuna deduzione causale o graduatoria. Componenti condivise e normalizzazione per residente richiedono interpretazione anche quando la correlazione comunale è calcolabile.

## Verifiche riproducibili

Regressione ambientale: 121 osservazioni native/storiche/benchmark verificate con riferimenti indipendenti, somme idriche, formule, null, periodi mancanti e alterazioni avversarie. Suite cumulativa: 166 domande, 105 calcoli e 61 rifiuti attesi. Le 35 letture territoriali e due riepiloghi restano coperti dalle regressioni esistenti. Nessuna modifica ai golden o alle soglie.

```bash
python scripts/test_semantic_environment_adapters.py
python scripts/semantic_engine_audit.py --output-dir /tmp/a6-environment
python scripts/semantic_question_suite.py --output-dir /tmp/a6-environment
python scripts/semantic_engine_benchmark.py --output-dir /tmp/a6-environment
python scripts/preflight.py --full
```

Report congelati in `reports/a6-environment/`: copertura/collegamenti, domande e prestazioni. Le misure locali sequenziali non sono uno stress test o una promessa di latenza produttiva. A6.4 non è completata; nessuna nuova lettura ambientale pubblicata o revisione metodologica approvata in questo lotto.
