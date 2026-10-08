# A6 — RTCave, produzione estrattiva e quadro PRC

Lotto v22 dopo #367 mergiata, sugli snapshot già acquisiti. Tre carrier con universi distinti; motore, test e documentazione. A6.4 parziale, revisione A6.5–A6.6 aperta.

| Carrier | Universo e riferimento | Operazioni |
|---|---|---|
| `extractiveSites` | Record RTCave al 2 settembre 2026, distinti per `codice_rt` | Confronto/ranking del totale e 13 letture di stato/tipologia/macro-classe produttiva |
| `extractiveProduction` | Volumi annui comunicati tramite obblighi informativi, 2019–2025; raccordo comunale verificato per Seravezza e Stazzema | Confronto/ranking corrente e serie nativa; cinque comuni n.d., copertura 2/7 |
| `extractivePlanning` | PRC vigente, variante 2025, geometrie EPSG:3003 intersecate per categoria | Confronto/ranking di superfici, conteggi e percentuali pubblicate; quote ricostruite separatamente dai componenti arrotondati |

## Record e applicabilità

Snapshot `data/source-snapshots/attivita-estrattive-v128.json`, SHA256 `bf67bf162733219bdd6ecde59480e2d451f42f466230c02dc8bc2a8c79295be6`. L'acquisizione RTCave è attestata dal digest `f507c5bb018619ac95bd8a681d24b9aaa3a584c41c3f8d67632b72dd685f62f2`, con 666 record regionali distinti e 90 record locali disponibili nel file. Si ricontrollano i 90 record locali, `codice_rt`/`id_cava` univoci, Comune, categorie originali, componenti pubblici e anagrafiche; non si ripete la scansione live né si deduplicano da capo i 666 record regionali non presenti integralmente.

| Comune | Record RTCave | Attivi | Chiusi | Stato n.d. | Produzione 2025 m³ |
|---|---:|---:|---:|---:|---:|
| Camaiore | 0 | 0 | 0 | 0 | n.d. |
| Forte dei Marmi | 0 | 0 | 0 | 0 | n.d. |
| Massarosa | 1 | 0 | 0 | 0 | n.d. |
| Pietrasanta | 2 | 0 | 2 | 0 | n.d. |
| Seravezza | 44 | 6 | 33 | 0 | 55.801 |
| Stazzema | 43 | 9 | 29 | 1 | 23.651 |
| Viareggio | 0 | 0 | 0 | 0 | n.d. |

Uno zero RTCave è valido. La produzione n.d. non viene trasformata in zero o n.a.; il confronto di sette comuni richiede opt-in esplicito, conserva cinque esclusioni e non attesta tutta la produzione della Versilia. Se manca anche uno dei due valori documentati, il confronto non ha due osservazioni sufficienti. Un record non equivale necessariamente a una cava fisica indipendente. Chiusa, Inattiva, Ripristino e SED non sono sinonimi di cava dismessa; Ornamentale è una macro-classe, non una litologia.

`total` e dimensioni `view:<chiave parte>` RTCave: stati `state_active`, `state_inactive`, `state_suspended`, `state_expired`, `state_restoration`, `state_closed`, `state_nd`; tipi `type_ordinary`, `type_restoreworks`, `type_recovery`; macro-classi `prod_ornamental`, `prod_industrial`, `prod_construction`. Non si sommano partizioni diverse. Non si ponderano i conteggi come rapporti.

## Produzione e pianificazione

Produzione: `total`, periodo corrente `2025`, serie 2019–2025. Si riconciliano ogni annualità e i componenti Bacino di Stazzema + Cardoso/Apuane; la somma documentata 2025 è 79.452 m³ dei soli due comuni. Gli OPS 2019–2038 sono pianificazione e non diventano produzione osservata. Lo storico resta consultabile; variazioni e trend automatici richiedono una revisione di continuità separata.

PRC: `total` è alias di `view:g_ha`. Dimensioni `view:<g|gp|acc>_<ha|pct|n>` mantengono separati Giacimenti, Giacimenti Potenziali e Aree Contigue di Cava; `view:mos`, `view:pmos`, `view:sed` leggono i conteggi nativi di dettaglio. SED è ricognizione non esaustiva, senza pretesa di censimento completo. Le tre superfici di unione sono 56,997, 11,390 e 556,495 ha; non si sommano come un'unica superficie di cava. Non attestano superficie effettivamente escavata o autorizzata.

Le percentuali `view:<categoria>_pct` preservano il valore GIS pubblicato a tre decimali: non abilitano `weighted_ratio`. Le dimensioni distinte `share:<g|gp|acc>` ricostruiscono il rapporto da ettari nativi a tre decimali e km² comunali a due decimali, dichiarandone l'approssimazione rispetto alle geometrie originarie. Numeratore ha, denominatore km² × 100, scala 100; l'unione usa la somma dei componenti della stessa categoria e 356,86 km², mai la media semplice delle percentuali. Ad esempio, ACC Seravezza: percentuale GIS 3,971; rapporto ricostruito 156,322/39,36 ≈ 3,9715955. La riconciliazione propaga gli arrotondamenti di 0,0005 ha, 0,005 km² e 0,0005 punti percentuali; non finge componenti GIS a piena precisione né modifica i valori pubblici.

Snapshot RTCave, flusso annuale di produzione e quadro pianificatorio PRC non sono universi intercambiabili. Due collegamenti tipizzati sono solo contesto. Niente produzione per sito attivo, consumo di riserva, superficie escavata, storico RTCave/PRC inventato, correlazioni o anomalie automatiche. Totali territoriali e OPS non sono medie comunali: benchmark rifiutati.

## Evidenza e avanzamento

226 verifiche numeriche per catalogo nel lotto, incluse ripetizioni dell'alias PRC e 14 osservazioni storiche; record/serie/componenti attestati, puntatori risolvibili, percentuali pubblicate distinte dai rapporti ricostruiti, tre quote aggregate, n.d. e zero, guardie avversarie su duplicati, identità, categorie, hash, denominatori, aree, arrotondamenti, CRS, annualità e componenti pubblici.

Copertura derivata 144/225 effettivi, 96/181 sorgente; 81 residui, 17 ambientali. Suite 435 domande (236 calcoli, 199 rifiuti), 52 collegamenti e 55 carichi di prestazione descrittivi; report `reports/a6-extractive/`. Dati, UI, asset, renderer, golden, Camaiore, workflow e Radar conservati; 35 letture territoriali e due riepiloghi invariati. A6.4 resta parziale, A6.5–A6.6 aperte, A7 non avviata. Quick/Full locali e CI sul candidato prima del merge del proprietario.
