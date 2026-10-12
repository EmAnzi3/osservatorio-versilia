# A6 — Carburanti e densità pubblica di ricarica

Due carrier, sei viste. Nessuna acquisizione o modifica di valori, UI, asset, golden, workflow o Radar. Le viste espongono statistiche già congelate con provenienza e limiti; la presenza dell'adapter non certifica i record originari.

## Carburanti: due statistiche separate

| Dimensione fuelPrices | Statistica | Periodi |
|---|---|---|
| total | Alias benzina self, mediana comunale nella fotografia | Cinque date, 14 agosto–10 ottobre 2026 |
| fuel:benzina | Mediana comunale benzina self nella fotografia | Stesse cinque date |
| fuel:gasolio | Mediana comunale gasolio self nella fotografia | Stesse cinque date |
| monthly:benzina | Media delle mediane comunali giornaliere disponibili | 57 mesi, gennaio 2022–settembre 2026 |
| monthly:gasolio | Media delle mediane comunali giornaliere disponibili | Stessi 57 mesi |

Unità €/litro nominali, riepiloghi pubblici a tre decimali. Il default è l'ultima data della statistica scelta: 10 ottobre per la fotografia, settembre per la serie mensile. `2026` non è un alias annuale carburanti. Le selezioni mese/data puntuale non si mescolano; token e ordinamento dei periodi sono espliciti.

Gli snapshot `fuel-history-mimit.json` e `fuel-history-mimit-monthly.json` sono verificati tramite SHA dei byte e fingerprint dell'intero oggetto, anche dopo cache. Le cinque fotografie sono riconciliate con le due parti e le serie del catalogo; i valori mensili e le loro evidenze puntano direttamente allo snapshot acquisito, senza inventare un campo mensile nel catalogo. Gli archivi CSV/tar originari, prezzi e ID dei singoli impianti non sono rigiocati. Gli hash documentali presenti nel trimestre 2026 Q3 restano metadati di acquisizione, non prova di un replay degli archivi.

La serie mensile espone `observationDays`, `fuelObservationDays` e `calendarDays`. Marzo 2022 ha 29 giorni osservati su 31; settembre 2026 ha 29 su 30, con 5 settembre mancante nei metadati di acquisizione. Non si interpolano giorni. Gli impianti che riportano prezzi possono cambiare: consultazione della serie ammessa, continuità di un pannello fisso non attestata per variazioni o trend.

Stazzema ha prezzo null in entrambe le statistiche, non prezzo zero. Confronti/ranghi sui sette Comuni richiedono `allowPartial=true`; nessuna esclusione silenziosa. Il campo congelato `stations` è il massimo fra i due conteggi di prezzi disponibili, non un'unione certificata degli ID impianto: non diventa un nuovo conteggio territoriale o peso.

Nessun pooling delle mediane. La media delle mediane comunali, anche ponderata da conteggi, non ricostruisce la mediana degli impianti Versilia: [1,1,4] e [3,3,3] danno mediane 1 e 3, media 2, ma mediana congiunta 3. La media comunale pubblicata non diventa prezzo regionale, prezzo ponderato dai litri venduti o spesa delle famiglie.

## Ricarica elettrica: soltanto densità pubblica

`evPoints/total`: sette densità pubbliche arrotondate ogni 1.000 residenti, anno dichiarato 2026. Confronto e rango descrittivi, replay del catalogo. Conteggi, ID/stato/accesso pubblico dei record, distinzione EVSE/connettore e data esatta del punto e del denominatore **non certificati nello snapshot**. La diagnosi A3 rimane `POINT_CONNECTOR_AND_REFERENCE_DATE_UNRESOLVED`; l'adapter non la chiude. Il caveat legacy sui pendolari non prova il riferimento delle ricariche e non è riusato come metodo.

Nessun conteggio ricostruito moltiplicando densità arrotondata e popolazione. Stazioni, colonnine, punti e connettori restano distinti. Nessun pooling/benchmark o inferenza su potenza, accessibilità, disponibilità istantanea o qualità. Il riferimento Versilia del catalogo non diventa un rapporto nativo verificato dall'adapter.

## Operazioni e verifiche

Confronto/rango per tutte le viste; serie solo carburanti, separate per statistica e combustibile. Variazioni, trend, punti percentuali, aggregazioni native, benchmark geografici, anomalie e coppie non revisionate rifiutati.

21 ancore puntuali carburanti incluse null/alias e sette densità EV; cinque coppie puntuali e tre mensili Massarosa. Replay distinto di 868 celle normalizzate, incluse 124 null, giorni osservati, puntatori, selezioni di periodo e attacchi a input/cache/hash/definizioni/identità. 117 nuove domande. 3.321 casi precedenti restano invariati; aggiornato soltanto il rifiuto legacy `fuel_adapter_missing`, ora `partial_coverage_requires_opt_in` con la stessa query e ID, perché l'adapter è presente ma il confronto completo ha una lacuna.

Report `reports/a6-energy/`, prestazioni descrittive senza soglie portabili. Copertura derivata 222/225, tre residui; 164/181 sorgente. A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata. Quick locale completo prima della pubblicazione; Full locale completo sequenziale e CI Quick→Full/A3 sullo stesso albero prima della prontezza al merge del proprietario.
