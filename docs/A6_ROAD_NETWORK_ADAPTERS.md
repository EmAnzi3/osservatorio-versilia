# A6 — Grafo viario Iter.Net, adapter v46

`roadNetworkProfile` è un carrier presente soltanto nel catalogo effettivo. Espone lunghezza degli elementi del grafo, densità pubblicata, cinque classi amministrative e tre classi di pavimentazione per i sette Comuni. `total` è alias della lunghezza; `view:<parte>` identifica le dieci letture; `nativeRatio` ricalcola la densità dai componenti congelati. Confronti e ranghi sono descrittivi, non valutazioni di qualità, accessibilità o priorità politica.

## Fonte, date e replay

Fonte Regione Toscana Iter.Net 4.48, giugno 2022; ritaglio sui confini comunali Istat generalizzati al 1 gennaio 2026, EPSG:3003. Il periodo esplicito `2022-map/2026-boundaries` separa le due date; `2022` è soltanto un alias di selezione. La verifica dello snapshot risale a settembre 2026 e non aggiorna la rete al 2026. Gli elementi possono distinguere le carreggiate: i chilometri non misurano strade univoche, responsabilità di manutenzione o condizioni attuali.

Replay di `data/source-snapshots/territorio-v137-official.json`: risultati normalizzati del ritaglio, metadati fonte/confini e componenti per Comune, non shapefile originali o riesecuzione geometrica del ritaglio. Ogni osservazione conserva hash, percorso e puntatori al valore pubblico e ai componenti; fingerprint completi del carrier e dello snapshot vengono ricontrollati anche dopo accessi in cache. Identità comunali e confini sono verificati.

## Densità e partizioni

`view:density` legge la densità pubblicata a sei decimali. `nativeRatio` calcola graphKm / municipalAreaKm2 dai due componenti normalizzati a sei decimali. La densità è stata arrotondata indipendentemente dai componenti: la riconciliazione propaga mezzo milionesimo di unità per numeratore, denominatore e densità. Per Forte dei Marmi il rapporto congelato è 15.023004289675226, mentre il valore pubblicato è 15.023005; entrambi restano espliciti, senza sostituzioni.

Solo `nativeRatio` ammette `weighted_ratio`: somma delle lunghezze / somma delle superfici dei Comuni selezionati, con evidenza di territori disgiunti nello stesso ritaglio. Nessuna media delle densità pubblicate. La somma comunale delle superfici differisce dall'area di unione normalizzata di un milionesimo di km², per arrotondamento; la verifica ammette la precisione congelata, senza imporre identità numerica artificiale.

Le cinque classi amministrative costituiscono una partizione della lunghezza; le tre classi di pavimentazione ne costituiscono un'altra. Non si sommano le due classificazioni fra loro. Zero e pavimentazione non classificata sono conservati. Serie, variazioni, trend, benchmark geografici, anomalie e coppie non revisionate sono rifiutati: una sola fotografia ibrida non documenta continuità temporale.

## Verifica e perimetro

`test_semantic_road_network_adapters.py` confronta 84 osservazioni fisse, comprese alias e rapporti nativi; verifica 14 componenti, due aggregazioni territoriali, partizioni, zeri e pari merito, puntatori, periodi/dimensioni rifiutati e mutazioni ostili dopo cache. Riferimenti trascritti indipendentemente dalle risposte del motore. 202 nuove domande mantengono invariate le 2.510 precedenti: suite 2.712/2.712 PASS (1.527 letture/calcoli, 1.185 rifiuti); i conteggi osservati e le prestazioni sono generati in `reports/a6-road-network/`.

Copertura derivata 211/225 effettivi, 154/181 sorgente e 14 residui: il carrier non esiste nel catalogo sorgente. A6.4 resta parziale, A6.5–A6.6 aperte e A7 non avviata. Nessuna acquisizione o modifica dati/UI/asset/golden/workflow/Radar, checkpoint Camaiore, 35 letture territoriali e due riepiloghi. Quick locale prima del push; Full completo locale e CI Quick→Full sul medesimo albero prima della prontezza per il merge del proprietario.
