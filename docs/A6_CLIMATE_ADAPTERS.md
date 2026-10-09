# A6 v25 — valori climatici annui e trend distinti

Quattro carrier `external-climate` già pubblicati diventano interrogabili. Il catalogo sorgente e quello effettivo mantengono `rows: []`: i valori sono nei due file esterni e l'interfaccia li legge in `assets/climate-ux-v3.js`. L'adapter risolve i comuni dal catalogo canonico, senza creare un secondo catalogo o modificare dati, renderer o UI.

## Definizioni effettive

Gli ID e le vecchie etichette del catalogo citano il trend cinquantennale, ma il runtime pubblico presenta **il valore annuo 2025** come misura principale e il trend separatamente. `total` rispetta questa definizione effettiva; non restituisce il delta della retta come temperatura o pioggia dell'anno. Il caveat catalogo di Tmin/Tmax descrive ancora una vecchia sostituzione LaMMA: il file nativo e il runtime corrente attestano invece ERA5-Land continuo con offset costante. Questa discrepanza resta esplicita nei warning e nella documentazione; la metadata pubblica non viene riscritta in questo lotto.

| Carrier | `total` e serie annuale | Fonte congelata | Periodi |
|---|---|---|---|
| climateTemperatureTrend50y | Media annua territoriale, °C | meteo-clima-poc.json, temperature | 1950–2025 |
| climatePrecipitationTrend50y | Precipitazione annua territoriale, mm | meteo-clima-poc.json, precipitation | 1950–2025 |
| climateTminTrend | Media annua delle minime giornaliere, °C | meteo-clima-minmax-poc.json, tmin | 1975–2025 |
| climateTmaxTrend | Media annua delle massime giornaliere, °C | meteo-clima-minmax-poc.json, tmax | 1975–2025 |

Tmin/Tmax non sono i record minimo/massimo assoluto dell'anno. Pioggia in mm non è un volume d'acqua comunale, e la temperatura non è esposizione della popolazione. La media territoriale usa celle raster pesate frazionalmente sul perimetro Istat 2026, senza trasformarle in osservazioni di una stazione.

La dimensione `trend:1975-2025` restituisce, per ciascun carrier, la differenza fra i valori **stimati** della retta OLS nel 2025 e nel 1975, su 51 osservazioni annuali. Si centra l'asse nel 2000; variazione = pendenza × 50. Conserva n, pendenza, livelli stimati e finestra come componenti di derivazione. Non è differenza fra valori annuali osservati, serie di delta o previsione. Solo per pioggia, `trend_percent:1975-2025` divide il delta stimato per il livello **stimato positivo** del 1975; nessun rapporto percentuale su gradi Celsius. Nessun arrotondamento del renderer viene applicato ai valori del motore.

Massarosa 2025: 16,619 °C media; 1.336,5 mm; 12,656 °C minime; 20,959 °C massime. Il campo nativo riepilogativo `latestComplete.temperature` arrotonda a 16,62: il motore conserva 16,619 dalla serie, come il runtime prima della formattazione. Delta OLS 1975–2025: +2,046325792 °C; −18,600904977 mm; +1,948846154 °C minime; +2,029357466 °C massime. Pioggia: −1,609284377% del livello stimato iniziale.

## Fonti, operazioni e limiti

Temperatura media e pioggia combinano LaMMA 1 km nel 1995–2015 e ERA5-Land calibrato fuori dal periodo comune. La pioggia 2022–2024 usa il prodotto orario, secondo il metodo già congelato, per evitare il difetto del mensile. Si ammettono serie e confronti di annualità disponibili; il delta cinquantennale già mostrato dal runtime ha una dimensione esplicita. **Non si abilita un trend o una variazione arbitraria della serie composita** come se tutte le annualità fossero osservazioni omogenee della stessa fonte.

Tmin/Tmax `poc-5` sono ERA5-Land ARCO orario continuo 1975–2025: estremi giornalieri da 24 campioni UTC, livello raccordato con un unico offset comunale LaMMA 2011–2015 applicato all'intera serie. LaMMA resta riferimento di livello; non sostituisce il tratto centrale e non corregge la pendenza. Il gate SIR indipendente è attestato dal file, non ricalcolato da questo adapter. Serie, variazioni assolute e pendenze OLS descrittive di Tmin/Tmax sono ammesse; le percentuali Celsius restano rifiutate. Giorni UTC non equivalgono a una nuova verifica delle osservazioni giornaliere locali.

I due file conservano nome `poc` e stato `draft` pur essendo già usati dal runtime pubblicato. L'adapter certifica il riuso deterministico di questa ricostruzione congelata; non promuove i file a nuove misure ufficiali né ripete acquisizione dei raster, calibrazione o validazione SIR. Nessuna inferenza di significatività, previsione, attribuzione causale o riduzione del rischio.

Confronto e rango sono descrittivi entro la stessa misura, periodo e dimensione. Non si produce una media areale/popolazione della Versilia: mancano le componenti spaziali native necessarie. Le normali 1991–2020 sono riferimenti temporali comunali, non benchmark Toscana/Italia. Ponderazione, benchmark geografici, anomalie e correlazioni automatiche vengono rifiutati. I collegamenti minime/massime e pioggia/pericolosità alluvionale sono contesto, senza correlazione o causalità.

## Evidenza e gate

SHA-256 file annui `2c9c340ae557c25f708f77d8f5411b71d5a409f4cfe6f55b626b614a790b62c9`; min/max `50be932eea3e96352e0c8403fce7a944782071c87bbf04c4a75e69143f8e23c2`; runtime `a40e61ecb05e2daa9f4e5647885016bdba507964c8a42e56af3cd5272edc0626`. Si verifica anche il digest strutturale dell'intero payload in memoria, invalidando la cache fra selettori: una mutazione dopo la prima query non eredita una verifica valida.

63 riferimenti numerici fissi indipendenti (28 valori 2025, 28 delta OLS calcolati separatamente con Decimal, sette percentuali di pioggia); replay di 1.778 celle annue del payload congelato, distinto da una nuova verifica indipendente dei raster. Controlli su puntatori, periodi completi, pendenze min/max, contratti esterni, identità, mutazioni, null introdotti, hash e rifiuti. 37 domande aggiunte, suite complessiva 555; 56 collegamenti tipizzati e 64 carichi descrittivi.

Copertura 156/225 effettivi, 108/181 sorgente; 69 residui complessivi, cinque ambientali. Restano tre carrier agricoltura, acqua potabile per località/parametro e classificazione territoriale. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata. 35 letture e due riepiloghi, Camaiore, dati, UI, golden, workflow e Radar conservati. Quick/Full canonici locali isolati e CI sul candidato prima del merge del proprietario. Report in `reports/a6-climate/`.

Guardia browser mobile Percorsi: attesa esplicita massima di 10 secondi sul controllo e sul grafico già verificati, dopo `networkidle`; nessuna asserzione, soglia o golden modificato. Il controllo precedente era fallito nel Quick e passato isolatamente; l’attesa certifica il completamento della selezione asincrona prima della misura.
