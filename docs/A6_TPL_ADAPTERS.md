# A6 — offerta TPL programmata, 26 agosto 2026

Tre carrier GTFS già congelati, 7/7 Comuni. Nessuna acquisizione, modifica del catalogo o dell'interfaccia. Il giorno osservato è un mercoledì feriale estivo: non rappresenta l'anno, l'orario invernale o il servizio effettivamente svolto.

| Carrier | Dimensioni | Universo e formula |
|---|---|---|
| `scheduledTplTripsPer1000` | `total`, `view:normalized` | Il nome legacy contiene «Per1000», ma `total` è il conteggio assoluto. Una trip è contata una volta per Comune se serve almeno un punto utilizzabile; bus e ferrovia riconciliati. Scala rapportata: conteggio comunale / residenti al 1 gennaio 2026 × 1.000. |
| `activeTplAccessPoints` | `total`, `view:normalized` | Coppie `(feed, stop_id)` attive e utilizzabili nella giornata; identificativi di feed diversi distinti. Scala rapportata: punti / stessi residenti × 1.000. Non è un conteggio di fermate fisiche deduplicate. |
| `tplServiceSpan` | `total` | Differenza fra prima e ultima partenza sui secondi GTFS, divisa per 3.600 e arrotondata a due decimali. Gli orari oltre 24:00 appartengono alla stessa giornata operativa. |

Esempio Camaiore: 05:50:00–29:51:10 equivale a 86.470 secondi, 24,02 ore pubblicate. Viareggio: ultima partenza 30:04:00, ossia 06:04 del giorno successivo. Nessun modulo 24 o troncamento. Una finestra ampia non dimostra servizio continuo né frequenza elevata. Gli zero delle corse ferroviarie a Forte dei Marmi/Stazzema restano componenti valide; non diventano assenza di TPL.

Confronto e rango descrittivi della stessa dimensione e giornata. Date ISO `2026-08-26` esplicite; la sola annualità `2026` è ambigua e rifiutata. Il denominatore della scala rapportata è una stima di residenti con data propria, non passeggeri né popolazione servita. Media aritmetica delle osservazioni comunali: ogni Comune pesa uguale. Le medie normalizzate pubblicate vengono riconciliate, ma non sono automaticamente il riferimento del risultato del motore.

La somma delle corse comunali conta appartenenze: una stessa trip può servire più Comuni. Non è il totale delle corse uniche in Versilia. Gli identificativi GTFS e il join territoriale non sono congelati nello snapshot comunale in forma rigiocabile: nessun pooling deduplicato o ricostruzione di rete è autorizzato. Non si sommano le ampiezze orarie per misurare la durata del servizio territoriale.

Byte e fingerprint decodificato di `mobilita-tpl-2026-08-26.json` sono verificati distintamente. Il materializzatore versionato riconcilia tutte le definizioni, righe, scale e aggregati del catalogo. Il QA del denominatore confronta anche le sette popolazioni pubblicate. Provenienza: puntatori catalogo/snapshot, data di servizio, componenti bus/ferrovia o secondi dell'orologio e data del denominatore. Questa è riconciliazione dello snapshot normalizzato: non un nuovo replay dei feed, di `calendar.txt`/`calendar_dates.txt`, dei punti o delle geometrie Istat. Gli hash e URL originari restano nello snapshot, senza equivalere alla ripetizione della lavorazione raw.

Serie, variazioni, trend, pooling, anomalie, benchmark geografici e coppie non revisionate sono rifiutati. Non si deducono puntualità, capacità, passeggeri, accessibilità pedonale entro 500 m o priorità politica. Nessuna associazione causale automatica.

Prove indipendenti: 35 celle pubbliche nelle cinque dimensioni, 14 conteggi bus/ferrovia, 14 orari in secondi, formule, unità, graduatorie, date esplicite e provenienza. Attacchi a identità, anno, formula, dati booleani, scala, aggregati, storico fittizio, denominatore e hash. Corpus precedente di 2.010 domande conservato; 101 casi nuovi. Audit e performance in `reports/a6-tpl/`. Quick locale prima del push, Full locale completo e CI Quick→Full prima della prontezza. A6.4 resta parziale; A6.5–A6.6 aperte, A7 non avviata.
