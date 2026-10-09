# A6 — profili agricoli e quota biologica

Lotto v26, baseline main #372 `5ed97e3b740909ac749707ed72e8e637dac13d7a`, albero `08df5ffd4464721d3e6b1b15ad4c56354a775cce`. Motore, verifiche e documentazione: riuso dei dati congelati, senza nuove acquisizioni o modifiche a catalogo pubblico, UI, asset, golden, workflow o Radar.

## Cinque rapporti censuari distinti

`agriculturalRenewalAndLeadership`: `total` coincide con `part:youngManagers`; `part:femaleHolders` rimane separata. `agriculturalDiversificationAndModernization`: `total` coincide con `part:connectedActivities`; `part:informatization` e `part:innovation` sono letture distinte. Gli alias non sono nuove osservazioni.

| Lettura | Numeratore Versilia | Denominatore Versilia | Universo e riferimento |
|---|---:|---:|---|
| Capi azienda fino a 40 anni | 69 | 957 | Aziende escluse le proprietà collettive, Censimento 2020 |
| Aziende con conduttrice donna | 334 | 944 | Aziende con conduttore, Censimento 2020 |
| Attività connesse | 74 | 959 | Aziende agricole, Censimento 2020 |
| Informatizzazione | 202 | 957 | Aziende escluse le proprietà collettive, Censimento 2020 |
| Innovazione | 110 | 957 | Aziende escluse le proprietà collettive, investimenti 2018–2020 rilevati nel Censimento 2020 |

Numeratore/denominatore × 100 per Comune. `weighted_ratio` somma esclusivamente i componenti della stessa lettura e dello stesso universo sui Comuni selezionati. Le differenze 959/957/944 sono sostanziali: Seravezza e Stazzema hanno denominatori diversi fra le letture. I caratteri e le sottocategorie possono sovrapporsi; non si sommano per costruire un indice né per ricostruire aziende distinte. Conduttore e capo azienda non sono sinonimi. Le aziende con conduttrice non sono un conteggio di donne uniche o di capi azienda donne. Forte dei Marmi ha zero ufficiale esplicito nelle attività connesse, con denominatore sette: zero non è n.d.

Fonte nativa `data/source-snapshots/istat-agricoltura-ii-2020.json`: componenti, universi, flussi, metadati di acquisizione e hash SDMX. Il lotto riconcilia i rapporti con parti e valore primario pubblici, con puntatori a record e componenti. Usa l’attribuzione comunale ufficiale del censimento; non riacquisisce CSV SDMX, dati individuali o vincoli territoriali e non attesta deduplicazione di persone/aziende a livello microdato. Il conteggio comunale ufficiale governa l’aggregazione; nessuna misura della posizione fisica dei terreni viene ricostruita. Nessuno storico censuario, variazione, trend, benchmark geografico dei profili o associazione automatica viene autorizzato.

## SAU biologica regionale

`organicAgriculturalAreaShare/total` restituisce la percentuale regionale pubblicata nel 2024; `series` legge i sette anni 2018–2024 dal file congelato `data/source-snapshots/toscana-indicatori-v1.5.0.json`, indicatore `ind20`. Conserva gli zeri ufficiali e la precisione diversa fra annualità: non ricalcola valori o ettari. Confronto e rango restano descrittivi. Il confronto Toscana 2024, 33,57%, deriva dalla riga regionale ufficiale di `data/source-snapshots/a3-regione-toscana-indicators-benchmark-2024.json`, riconciliata ai valori pubblici. Il gap è in punti percentuali; non viene riutilizzato per altri anni. Italia non è disponibile nella stessa fonte e definizione.

Gli snapshot non congelano entrambi gli ettari biologici e SAU necessari a una quota territoriale ponderata. `weighted_ratio` è quindi rifiutato; la mediana comunale già pubblicata non diventa la quota ufficiale della Versilia. Il censimento SAU 2020 non fornisce un denominatore per le percentuali regionali 2024. Le serie restano leggibili, senza autorizzare variazioni, punti percentuali fra anni o trend prima della revisione della continuità metodologica. La quota non è la quota di aziende biologiche né una valutazione ambientale automatica.

## Evidenze e limiti

Hash del file e digest strutturale attestano gli input congelati, anche se un oggetto in cache viene mutato. Date, unità, identità, parti, componenti, serie e benchmark pubblici sono riconciliati; input incompatibili e valori mancanti non diventano zero. Le query di confronto rispettano il minimo di due osservazioni del contratto esistente. Correlazioni, anomalie, causalità e sintesi tra le tre metriche sono rifiutate; due collegamenti di contesto espongono universi e periodi diversi senza permesso di associazione.

Fixture fisse: 35 coppie censuarie e 49 percentuali annue regionali. Aritmetica indipendente dal codice adapter: 56 osservazioni correnti comprese le ripetizioni degli alias, 14 rapporti aggregati (sette su tutti i Comuni e sette sul sottoinsieme Forte dei Marmi/Massarosa), 49 valori annui e sette gap Toscana. I riferimenti provengono da snapshot già acquisiti, non da una nuova validazione delle fonti raw. Test avversari verificano valore nullo/alterato, identità, unità, universo della parte, periodo, hash e mutazione della cache. Corpus 622 domande (285 calcoli/337 rifiuti), comprensivo di tutti i casi precedenti; 159/225 adapter effettivi e 109/181 sorgente, 66 residui di cui due ambientali. 58 collegamenti tipizzati e 67 carichi descrittivi.

A6.4 rimane parziale; 35 letture territoriali e due riepiloghi conservati, revisione A6.5–A6.6 aperta. A7 non avviata. Quick locale prima del push, Full locale isolato e gate CI sul candidato prima del merge del proprietario.
