# A6 — classificazione balneare, campioni e Bandiere Blu

Lotto v20 sul main dopo #365. Motore deterministico, test e documentazione; dati e snapshot, UI, asset, renderer, golden, Camaiore, workflow e Radar conservati. A6.4 resta parziale; revisione metodologica A6.5–A6.6 aperta.

| Carrier canonico | Universo e periodo | Operazioni revisionate |
|---|---|---|
| `bathingWaterQuality` | Classificazione ARPAT 2025 sui dati 2022–2025; aree e km classificati distinti | Confronto/ranking di quote, conteggi e km per quattro classi; quote aggregate da componenti native |
| `bathingNonCompliantSamples` | Campioni marini unici ARPAT nella stagione 2025; tutti, routinari e supplettivi | Confronto/ranking di quote o conteggi; rapporto aggregato entro lo stesso tipo di campione |
| `blueFlagBeaches` | Località costiere riconosciute da FEE, annualità 2019–2026 | Confronto/ranking dei conteggi; lettura dello storico nativo |

## Applicabilità e componenti

Quattro comuni costieri: Camaiore, Forte dei Marmi, Pietrasanta e Viareggio. Massarosa, Seravezza e Stazzema restano n.a., mai zero. Una selezione di tutti e sette richiede opt-in esplicito alla copertura parziale; ogni esclusione mantiene motivo e prova nativa. I valori correnti realmente mancanti restano distinti dalla non applicabilità.

La classificazione ha quattro classi: eccellente, buona, sufficiente e scarsa. `total` è alias della quota di **aree** eccellenti. Dimensioni `share:areas:<classe>`, `share:kilometres:<classe>`, `count:areas:<classe|total>` e `kilometres:<classe|total>` leggono i componenti congelati. Il periodo restituito è `2022-2025`; la richiesta `2025` è alias dell'edizione, non una misura annuale della qualità. Le quote aggregate usano separatamente aree o km: 14/21 aree eccellenti e 18,84/20,62 km eccellenti. Nessuna media semplice delle percentuali comunali.

Per i campioni `total` è alias di `share:all`. Le dimensioni `share:<tipo>`, `nonCompliant:<tipo>` e `samples:<tipo>` preservano tutti/routinari/supplettivi. I componenti si riconciliano: 35/167 non conformi complessivi, 29/126 routinari, 6/41 supplettivi. La chiave di deduplicazione è codice area, data e tipo di controllo. Si controllano partizione, denominatori positivi, conteggi interi, soglie microbiologiche e quote pubbliche. Lo zero supplettivo di Forte e Viareggio è valido.

I controlli supplettivi sono mirati: la loro quota non stima un campione casuale di bagnanti, giorni, esposizioni né probabilità di danno. Aree interessate da non conformità e numero di campioni non sono unità intercambiabili. Non si sommano fra loro tutti, routinari e supplettivi: tutti contiene già gli altri due tipi.

## Riconoscimenti FEE e limiti

I conteggi 2019–2026 sono riconciliati con lo storico pubblico e lo snapshot nativo. Il conteggio 2026 è ricontrollato sull'elenco FEE acquisito: comune e regione, località, assenza di revoca. Il confronto normalizza solo maiuscole e spazi; la barra resta parte della denominazione (`Marina di Viareggio (Ponente/Levante)` è una località). Pietrasanta: 1, 1, **0**, 2, 2, 2, 2, 2; nessuna interpolazione del 2021.

Lo storico conserva conteggi, non identità di tutte le località storiche. Serie consultabili; variazioni, trend e continuità dell'oggetto premiato richiedono revisione separata e sono rifiutati. Il riconoscimento multicriterio FEE non è un proxy della sola qualità microbiologica. I 45 riconoscimenti Toscana e i 524 Italia includono località anche di acque interne: sono totali, non medie comunali, e non abilitano `benchmark_gap`. Nessun rapporto ponderato è applicato ai conteggi FEE.

Classificazione quadriennale ARPAT, campioni annuali e riconoscimenti FEE hanno unità, periodi e metodi distinti. I due collegamenti tipizzati sono solo contesto; correlazioni automatiche e anomalie non revisionate sono rifiutate. Lo snapshot non attesta la sicurezza live della balneazione. Nessuno storico ARPAT è inventato dai soli metadati degli archivi.

## Verifica e provenienza

Ogni osservazione conserva catalogo e snapshot con SHA256, puntatori risolvibili, unità, universo, periodo, componenti, applicabilità ed eventuale indisponibilità. Le n.a. puntano alla lista nativa di esclusione; i conteggi 2026 FEE anche al record dell'elenco nazionale. Le quote derivate dalle classi non eccellenti puntano all'oggetto di componenti attestato.

152 verifiche fisse per catalogo nel lotto: 120 valori correnti comprese ripetizioni di alias e 32 conteggi storici; non 152 osservazioni tutte distinte. Test avversari su denominatori, partizioni, identità/coorte, hashes, finestra di classificazione, definizioni, deduplicazione, conteggi frazionari, serie pubbliche, revoche e località duplicate. Il gate generale verifica anche il rifiuto della copertura parziale prima dell'opt-in e le somme native dei rapporti.

Copertura derivata: 139/225 effettivi, 91/181 sorgente; 86 residui, di cui 22 ambientali. Suite 342 domande (194 calcoli, 148 rifiuti), 48 collegamenti tipizzati e 49 carichi di prestazione. Report `reports/a6-bathing/`; misure di prestazione locali descrittive, non benchmark di produzione. Le 35 letture territoriali e due riepiloghi conservano il loro perimetro; nessuna nuova lettura pubblicata né chiusura A6.
