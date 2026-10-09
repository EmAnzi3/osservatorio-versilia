# A6 — movimento turistico e capacità ricettiva

Il lotto v31 governa sette carrier: `tourismArrivals`, `tourismPresences`, `tourismAverageStay`, `foreignTourismShare`, `tourismBeds`, `tourismBedsPer1000`, `tourismStructuresPer1000`. Le presenze avevano già un adapter: sono sei nuovi carrier, non sette nuove acquisizioni. Copertura derivata 175/225 effettivi, 124/181 sorgente, 50 residui. `tourismIntensity` mantiene il proprio adapter; la stagionalità non viene certificata da questo lotto.

## Universo e fonti

Il movimento regionale 2023–2025 deriva dalla selezione dei sette Comuni già congelata in `a3-regione-toscana-tourism-benchmark-2025.json`, **al netto delle locazioni**. Arrivi sono registrazioni presso strutture, non persone uniche; presenze sono notti, non visitatori giornalieri. La componente estera riguarda la residenza all’estero, non la cittadinanza. Le tavole regionali restano provvisorie fino alla diffusione Istat. Ogni anno conserva URL, SHA e dimensione del file originario; gli ODS/XLSX non sono riacquisiti o rigiocati.

La capacità Istat 2024 conserva il pannello nativo di 7.899 Comuni, 273 toscani, con alberghiero/extralberghiero distinti. I 107 totali provinciali e il totale nazionale servono a riconciliare, senza entrare nella somma comunale. La geografia nativa non è convertita al pannello MEF. Lo snapshot conserva SHA di archivio/workbook e componente per ciascun Comune. Il 2025 è escluso: l’ampliamento agli alloggi privati non imprenditoriali non viene trattato come continuità automatica.

I rapporti di capacità usano posti letto o strutture **2024** e residenti stimati POSAS **1 gennaio 2026**, anche per Toscana/Italia. Il motore verifica separatamente conteggi, identità comunale, stock nativo POSAS e benchmark demografico congelato; nessun denominatore è retro-derivato dal rapporto pubblicato. Le date di numeratore e denominatore sono presenti nella risposta. Il rapporto non è una misura annuale omogenea del 2024 o del 2026.

## Precisione e aggregati

| Carrier/dimensione | Valore e calcolo consentito |
|---|---|
| Arrivi / presenze | Conteggi registrati nativi, confronti e ranghi |
| Permanenza media | Presenze / arrivi; rapporto territoriale da somme dei componenti |
| Quota estera `total` | Percentuale comunale pubblicata a un decimale; nessuna ponderazione come rapporto esatto |
| Quota estera `nativeRatio` | Presenze estere / presenze totali × 100, senza arrotondamento; ponderazione da conteggi nativi |
| Posti letto | Alberghiero + extralberghiero 2024, confronti e ranghi |
| Posti letto / strutture per 1.000 | Conteggi 2024 / residenti 2026 × 1.000; rapporto territoriale da somme |

Il catalogo pubblico resta identico. Per Massarosa la quota pubblicata è 47,8%; il rapporto nativo è 18.130 / 37.898 × 100 = 47,8389360916…%. La quota Versilia pubblicata pondera le percentuali comunali già arrotondate; il calcolo nativo usa 1.018.522 / 2.225.932 × 100. Le due risposte non sono intercambiabili e non si allarga una tolleranza per fingere la loro uguaglianza.

`nativeRatio` espone la formula e i puntatori ai componenti dello snapshot; il puntatore di catalogo identifica il record, poiché non esiste una cella pubblica non arrotondata. Per storici presenti soltanto nello snapshot sorgente vale la stessa distinzione: il valore è documentato dalla cella nativa e il catalogo identifica il carrier, senza creare uno storico pubblico ulteriore.

I benchmark regionali del movimento 2025 sono valori congelati acquisiti e riconciliati in A3, non un nuovo replay del pannello regionale. Le componenti regionali non sono tutte incorporate: nessun componente è ricostruito inversamente. La quota estera comunale arrotondata può essere confrontata con il benchmark regionale alla sua precisione originaria, con il limite esplicito di precisione; `nativeRatio` non ha un benchmark certificato in questo lotto. Italia assente per il movimento non diventa zero. La capacità dispone di Toscana e Italia riconciliate sul pannello nativo.

## Operazioni e limiti

Gli storici consultabili sono movimento 2023–2025 e posti letto 2002–2024. I rapporti con residenti 2026 non diventano rapporti annuali storici. Nuove variazioni, trend, anomalie e coppie statistiche non revisionate sono rifiutati per i sei nuovi carrier. **Le operazioni già ammesse sulle presenze vengono preservate**, inclusa la variazione assoluta Massarosa 2023→2025 di 2.791 notti; rimangono soggette ai contratti generali di periodo, copertura, finalità esplicita e assenza di interpretazioni causali. Questa conservazione non certifica nuove coppie turismo né chiude la revisione A6.5–A6.6.

Ogni accesso verifica SHA del file e impronta strutturale dello snapshot, anche con cache già caricata. La validazione completa del pannello è riusata solo per lo stesso stato del carrier e della popolazione; mutazioni di identità, componenti, periodo, unità, serie, benchmark o fonti invalidano il risultato.

## Evidenza

`test_semantic_tourism_adapters.py` usa una trascrizione fissa distinta dal motore: 56 osservazioni correnti (incluse le sette quote native), quattro rapporti territoriali e dieci benchmark. Il replay separato verifica 245 celle storiche congelate, senza presentarlo come una nuova acquisizione o una verifica indipendente dei file originari. I casi avversari esercitano precisione, aggregati, date dei residenti, identità, cache, fonti e limiti metodologici.

Suite generale: 960 domande, 449 consultazioni/calcoli e 511 rifiuti attesi. I 88 casi aggiunti non riscrivono le aspettative con le risposte del motore. Collegamenti 58 tipizzati e 29 companion invariati. Benchmark descrittivo: 81 carichi, con rapporto estero nativo, storico posti letto e rifiuto dello storico normalizzato; nessuna promessa di latenza o completezza.

Report riproducibili in `reports/a6-tourism/`. Quick locale canonico prima del push; Full locale canonico su checkout isolato e Quick→Full CI sul candidato prima del merge manuale. Nessuna modifica a valori pubblicati, rendering, golden, workflow, Radar, Camaiore, 35 letture o due riepiloghi. A6.4 rimane parziale, A6.5–A6.6 aperte e A7 non avviata.
