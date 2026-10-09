# A6 — adapter MEF: distribuzioni, fonti, pensioni e contribuenti

Lotto v29, baseline #378 `1df5a9aec027b143355fc6e05e5b8de276bb61a1`, albero `6d8886d7c5c19504945ac7a707840d94533ef073`. Quattro carrier già pubblicati, nessuna acquisizione o modifica dei dati/UI/asset/golden/workflow/Radar. Motore e prove deterministiche; non completa A6.4 né la revisione A6.5–A6.6, A7 non avviata.

## Operazioni e universi

| Indicatore | Dimensioni | Lettura e denominatore |
|---|---|---|
| incomeDistribution | total = macro:0; macro:0–3; band:<chiave nativa> per otto fasce | Macro: frequenze note del gruppo / somma delle frequenze note delle otto fasce; dettaglio: frequenza della fascia / frequenza totale del reddito complessivo |
| incomeSourceProfile | total = source:employment; source:<chiave nativa> per sette fonti | Ammontare in euro / frequenza dei dichiaranti della stessa fonte |
| pensionIncomeShare | total | Ammontare da pensione / ammontare complessivo, non percentuale di pensionati |
| taxpayersAdultPopulationRate | total | Contribuenti MEF a.i. 2024 / residenti Istat 18+ al 1 gennaio 2026 × 100; non quota degli adulti che paga IRPEF |

`compare`, `rank` e `weighted_ratio` per le dimensioni dichiarate; rank è un ordinamento numerico, non qualità o priorità politica. `weighted_ratio` somma componenti omogenee della stessa fonte/fascia nei Comuni distinti, mai frequenze di fonti sovrapposte né medie delle percentuali comunali. Le categorie MEF non sono gli scaglioni fiscali vigenti. Valori correnti 2024; anno di imposta distinto da dichiarazione e pubblicazione. Il carrier contribuenti conserva il token ibrido completo e `numeratorPeriod=2024`, `denominatorPeriod=2026-01-01`; un semplice 2024 è rifiutato.

Le macrofasce normalizzano soltanto le frequenze pubblicate disponibili, come il catalogo esistente. Non ricostruiscono le frequenze mancanti e non descrivono la distribuzione completa quando vi sono celle vuote. La riconciliazione include conteggi, copertura e differenza rispetto alla frequenza totale: Camaiore 331, Pietrasanta 301, Stazzema 4, senza attribuire una causa non dichiarata dalla fonte. Il dettaglio conserva i null; lo zero di frequenza ufficiale resta zero. Le due basi di denominatore sono esplicite e non intercambiabili. Nessuna redistribuzione delle quote mancanti. `allowPartial` richiede opt-in esplicito ed espone osservazioni escluse; i minimi delle operazioni e le guardie generiche restano invariati.

Le frequenze di lavoro, pensione, autonomo, imprese, partecipazione e fabbricati non sono persone uniche disgiunte fra fonti: lo stesso contribuente può comparire in più fonti. Nessun totale delle sette frequenze viene calcolato. Importi e medie sono redditi nominali dichiarati, non reddito disponibile familiare. Per Stazzema la contabilità ordinaria mancante non diventa zero.

`series` per le sette fonti e la quota pensionistica, dove il carrier materializzato ha osservazioni 2023–2024; annualità con celle mancanti restano assenti e non vengono create dal motore. Serie della distribuzione e del rapporto contribuenti/adulti non inventate. Variazioni, punti percentuali, trend, anomalie e correlazioni sono rifiutati: omogeneità temporale e coppie non sono certificate da questo lotto. Le coppie sono rifiutate anche quando MEF è il secondo selettore.

Benchmark Toscana/Italia 2024 solo lavoro dipendente (anche alias total), quota pensionistica e rapporto contribuenti/adulti con identico riferimento ibrido. Nessun benchmark delle altre fonti o fasce. Gap = valore comunale − benchmark; non misura efficacia o priorità.

## Provenienza e verifiche

Snapshot correnti `mef-income-lotto-a-2024.json`, storici `a3-simple-mef-history-2023-2024.json`, POSAS `istat-demography-lotto-a-2026-08.json`, benchmark `a3-mef-benchmark-2024.json` e `a3-mef-taxpayers-benchmark-2024.json`. Percorsi sotto `data/source-snapshots/`; impronte byte e strutturali versionate nell'adapter e verificate anche sulla cache. Ogni misura espone SHA/puntatore pubblico e record/componenti nativi; il denominatore adulto include il riferimento POSAS e le età 18–120. Le componenti del rapporto contribuenti/adulti vengono ricalcolate dalle età congelate, non ricavate dalla percentuale arrotondata.

161 osservazioni correnti con componenti fisse, inclusi alias e null; replay storico distinto di 124 osservazioni con alias. Tre rapporti aggregati da componenti fisse e sei riferimenti geografici fissi. Domande includono anche due aggregazioni delle fasce con denominatori distinti e due riferimenti storici Camaiore 2023. Le fixture sono trascritte dalle estrazioni versionate, non nuove acquisizioni indipendenti delle fonti live. Mutazioni di valori/null/unità/identità/periodi/componenti/benchmark/hash/cache falliscono; prove dedicate contro imputazione zero e scambio di denominatori.

Suite 802 domande (380 consultazioni/calcoli, 422 rifiuti). Copertura derivata 165/225 effettiva, 114/181 sorgente, 60 residui; nessun ambientale senza adapter. Report `reports/a6-mef/`. Collegamenti tipizzati e letture territoriali conservati: nessuna associazione automatica dei nuovi carrier. Baseline prestazioni descrittiva, non promessa di produzione.

La PR incorpora le due attese browser rimaste locali dopo la #378: label/superficie Demografia per metrica attiva (15 s), metrica/richiamo cartografico Camaiore mobile (10 s). Asserzioni, geometrie, contenuti, soglie e golden invariati. Le prove mirate precedenti sono distinte dall'evidenza canonica del nuovo candidato. Quick prima del push e Full locale isolato più Quick/Full CI prima della revisione per merge del proprietario.
