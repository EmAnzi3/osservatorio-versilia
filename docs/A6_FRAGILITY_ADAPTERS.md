# A6 — IFC: classi ordinali e accessibilità ai servizi

Lotto v18 sul main dopo #363 e #362. Solo motore deterministico, test e documentazione; nessuna acquisizione, modifica di snapshot, catalogo, UI, renderer, golden o Radar. Non chiude A6.4 né la revisione metodologica A6.5–A6.6.

| Carrier canonico | Unità e periodo | Operazioni revisionate |
|---|---|---|
| `municipalFragility` | Decile 1–10, 2022; classi 2018/2019/2021/2022 | Confronto di classi, consultazione serie |
| `lowProductivityEmployment` | Ventile 1–20, 2022; classi 2018/2019/2021/2022 | Confronto di classi, consultazione serie |
| `essentialServicesAccessibility` | Minuti, riferimento effettivo 2019, release IFC 2022 | Confronto, ranking descrittivo dei tempi, scarto dalla mediana Toscana/Italia |

Lo snapshot `data/source-snapshots/fragilita-comunale-v133.json` fornisce identità e componenti native. Si riconciliano codice, nome, slug, fonte, edizione, periodi e valori del catalogo; il bundle di input resta identificato da SHA-256. Ogni osservazione conserva puntatori precisi al catalogo e alla componente nativa, con hash. La copertura è derivata dal catalogo: i tre carrier sono materializzati nella build e assenti nella sorgente, quindi 133/225 effettivi e 86/181 sorgente.

Decili e ventili sono posizioni ordinali, non quantità con distanze uguali. Il confronto restituisce osservazioni senza media. Non si calcolano variazioni assolute o percentuali, trend, rapporti ponderati, anomalie, correlazioni, ranking aggiuntivi o benchmark scalari. Le classi native devono essere intere entro la scala; la serie è verificata anno per anno. Il 2020 manca e non viene interpolato. Per l'indice composito la fonte dichiara decili della distribuzione comunale al 2018; un cambiamento di classe non misura un aumento percentuale della fragilità. I ventili non sono il numero di addetti o una misura cardinale della produttività.

L'accessibilità è il tempo in auto dal centro comunale al Polo/Polo intercomunale più vicino. Non è il tempo medio di viaggio dei residenti né la quota di popolazione servita. Il riferimento resta 2019, anche se la release IFC è del 2022 e le righe SDMX hanno etichetta 2022. Le ripetizioni negli export IFC non producono uno storico. Lo zero dei comuni Polo è valido, non mancante. Correlazioni, anomalie e operazioni temporali restano non attestate in questo lotto.

`data/source-snapshots/a3-istat-accessibility-benchmark-2019.json` conserva 7.903 record nazionali e 273 toscani nella geografia IFC al 31 dicembre 2022, esclusa Misiliscemi (`081025`). Si ricontrollano unicità dei codici, valori non negativi, riconciliazione dei sette comuni, hash CSV/struttura, riferimento e mediane: Toscana 33,2 minuti, Italia 27,1. Il sottoinsieme toscano usa i dieci codici provinciali ufficiali del perimetro congelato. Lo scarto è tempo del comune meno **mediana non ponderata dei tempi comunali**; i descrittori di ogni benchmark conservano aggregazione e numero dei comuni. Nessuna media ponderata per popolazione o media dei sette comuni sostituisce il benchmark ufficiale.

Regressione generale nel preflight, su source ed effective: 105 verifiche di osservazioni contro valori fissi, comprese serie e ripetizioni dei benchmark, non 105 dati distinti. Controlli avversari su scala, identità, storia, anno effettivo, valori negativi, null, record benchmark duplicati e mediana alterata. Suite complessiva 278 domande: 160 calcoli e 118 rifiuti attesi. Due collegamenti IFC sono solo contesto: dipendenza componente/composito e anni diversi non autorizzano correlazioni. 44 collegamenti tipizzati e 43 carichi sequenziali locali; le misure non sono un test di carico produttivo.

Le 35 letture territoriali e i due riepiloghi aggregati restano nel loro perimetro. Nessuna nuova lettura o conclusione causale viene pubblicata. La revisione metodologica rimane aperta.
