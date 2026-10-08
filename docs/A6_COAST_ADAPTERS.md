# A6 — linea litoranea, protezione e dinamica costiera

Lotto v19 sul main dopo #364. Solo motore deterministico, test e documentazione: snapshot, catalogo, UI, asset, renderer, golden, freeze Camaiore, workflow e Radar conservati. A6.4 resta parziale e la revisione metodologica A6.5–A6.6 aperta.

| Carrier canonico | Universo e periodo | Operazioni revisionate |
|---|---|---|
| `statisticalCoastlineLength` | Linea statistica Istat al 31 dicembre 2021; comprende tratti antropizzati | Confronto e ranking descrittivo in km |
| `rigidDefenceProtectedCoast` | Costa ISPRA 2020; protezione rigida, esclusi ripascimenti | Confronto/ranking di quota o km; rapporto aggregato nativo; scarto percentuale Toscana/Italia |
| `shorelineDynamics` | Costa naturale bassa analizzata tra 2006 e 2020, soglia di spostamento 5 m | Confronto/ranking delle tre classi in quota o km; quota aggregata su km analizzati |

Le tre lunghezze non sono intercambiabili. La quota protetta non descrive l'efficacia delle difese né il rischio di danni. Le quote della dinamica non sono tassi annuali di erosione: classificano tratti per arretramento superiore a 5 m, variazione entro ±5 m o avanzamento superiore a 5 m nell'intero intervallo 2006–2020. Nessuno storico annuale, variazione, trend, correlazione automatica o anomalia viene abilitato in questo lotto.

Quattro comuni sono litoranei: Camaiore, Forte dei Marmi, Pietrasanta, Viareggio. Massarosa, Seravezza e Stazzema restano **non applicabili**, senza essere trasformati in zero. Le query sull'intero perimetro richiedono `allowPartial: true`; altrimenti vengono rifiutate. In alternativa si selezionano esplicitamente i comuni litoranei. Esclusioni e copertura restano nell'output. Il valore zero di protezione rigida a Viareggio è un dato valido e partecipa ai rapporti aggregati.

`data/source-snapshots/costa-mare-v123.json` conserva chilometri protetti/costa totale e chilometri erosion/stable/advance/costa analizzata. Si verificano hash degli input ufficiali, soglia, esclusione dei ripascimenti, quattro codici fonte, sette identità pubbliche, componenti e quote. Le tre classi di dinamica partizionano i km analizzati. Il rapporto aggregato è somma dei km della classe / somma dei km del relativo universo × 100, anche per sottoinsiemi espliciti; niente media semplice delle percentuali, pesi demografici o uso della linea Istat come denominatore ISPRA.

`data/source-snapshots/territorio-ucs-v136.json` conserva la linea statistica comunale con precisione pubblicata a nove decimali. Il dato è riconciliato alla riga del DBF completo in `a3-istat-coastline-benchmark-2021.json`, identificato dall'hash del file Istat. La lunghezza nativa del DBF ha più decimali: la differenza massima ammessa per la riconciliazione è 0,5 × 10⁻⁹ km più tolleranza numerica. I totali Toscana/Italia presenti nel benchmark sono **somme territoriali**, non una media comunale; il motore non calcola uno scarto comune meno totale regionale/nazionale.

`data/source-snapshots/a3-ispra-coast-benchmark-2020.json` conserva i componenti della quota protetta: Toscana 83,685 / 652,037 km; Italia 1.516,207 / 8.329,045 km. Il benchmark è ammesso solo sulla quota protetta e nello stesso universo ISPRA 2020, riconciliando percentuali native e catalogo. La dinamica composita non eredita quel benchmark scalare. Lo scarto percentuale è descrittivo, non una priorità politica.

Ogni osservazione conserva puntatori al valore del catalogo e al record nativo, con SHA-256; per la linea Istat anche il record DBF. Per i comuni n.a. la provenienza ISPRA punta alla lista esplicita di esclusione, senza inventare un record costiero. La regressione risolve anche i puntatori e verifica valori fissi, componenti, quote aggregate, zero valido, null reali, n.a., identità, perimetri, soglie, hash, benchmark alterati e rifiuti metodologici.

Copertura derivata: 136/225 effettivi, 88/181 sorgente; 89 residui, 25 ambientali. Nel lotto 56 verifiche di osservazioni effettive e 52 sorgente, inclusi alias e ripetizioni dei benchmark, non 56 dati tutti distinti. Suite complessiva 308 domande: 175 calcoli e 133 rifiuti attesi. 46 collegamenti tipizzati e 46 carichi sequenziali locali; due collegamenti costieri sono solo contesto e non consentono associazioni automatiche. Le misure non sono un test di carico produttivo. Le 35 letture territoriali e i due riepiloghi restano nel loro perimetro; nessuna nuova lettura o conclusione causale viene pubblicata.
