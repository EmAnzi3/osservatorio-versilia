# A6 — titoli demaniali e canoni dovuti SID

Lotto v21 sul main dopo #366. Due carrier canonici, dodici dimensioni correnti: motore deterministico, test e documentazione. A6.4 resta parziale; revisione metodologica A6.5–A6.6 aperta.

| Carrier | Dimensioni revisionate | Operazioni |
|---|---|---|
| `maritimeConcessions` | Totale titoli, turistico-ricreativi e loro quota, titoli al canone minimo e loro quota, scadenza non indicata | Confronto/ranking; quote aggregate da conteggi nativi |
| `maritimeConcessionFeesDue` | Totale dovuto, dovuto turistico e sua quota, medio per titolo, medio per titolo turistico, mediana nativa | Confronto/ranking; quote e medie aggregate da importi/conteggi nativi; nessuna aggregazione delle mediane |

## Universo, attribuzione e periodo

Snapshot SID **agosto 2026**, token `2026-08`, distinto da una misura annuale generica. I canoni sono importi annuali **dovuti per il 2026**, non un flusso cumulato di otto mesi, incassi, arretrati riscossi o gettito comunale. Il numero di titoli `idconc` non conta stabilimenti balneari o concessionari.

Fonte congelata `data/source-snapshots/demanio-marittimo-v127.json`, SHA256 `90359a0947ad558d3e1dd0212f5ed9eabb8c7f642387b55ab4bb5f9fce6f2977`. Il CSV nazionale acquisito EPSG4326 ha SHA256 `66b492555b29147421693080555f7d29eb5f7469f2c3aa5bffe00aa5d27ad28d`: 29.248 righe, 29.242 titoli distinti, sei duplicati perfetti, stato `Vigente`. L'adapter riconcilia i componenti dello snapshot e la sua prova di acquisizione; non ripete l'importazione nazionale da record raw assenti nel checkout.

L'attribuzione territoriale approvata è congelata: titoli dei Comuni, 165 titoli dell'Autorità Portuale Regione Toscana attribuiti a Viareggio e 17 della Capitaneria attribuiti per posizione. Per questi ultimi si controllano anche i 17 identificativi e l'assegnazione al Comune; unicità nazionale e posizione non sono ricalcolate da nuove geometrie live.

| Comune | Titoli comunali | Capitaneria | Autorità Portuale | Totale titoli | Turistici | EUR dovuti |
|---|---:|---:|---:|---:|---:|---:|
| Camaiore | 129 | 1 | 0 | 130 | 124 | 852.515,21 |
| Forte dei Marmi | 185 | 2 | 0 | 187 | 161 | 1.449.307,39 |
| Pietrasanta | 122 | 1 | 0 | 123 | 116 | 1.552.876,15 |
| Viareggio | 181 | 13 | 165 | 359 | 174 | 2.669.422,99 |
| Unione costiera | 617 | 17 | 165 | 799 | 575 | 6.524.121,74 |

Massarosa, Seravezza e Stazzema sono n.a., mai zero. Una selezione di sette comuni richiede opt-in alla copertura parziale; ogni esclusione mantiene motivo e puntatore alla lista nativa. Un valore corrente effettivamente mancante resta indisponibile, distinto dalla non applicabilità.

## Componenti e operazioni

Dimensioni dei titoli: `total`, `view:tourist`, `share:tourist`, `view:minimumCount`, `share:minimum`, `view:expiryMissing`. Dimensioni dei canoni: `total`, `view:touristDue`, `share:touristDue`, `view:mean`, `view:touristMean`, `view:median`.

Rapporti dai componenti nativi: 575/799 titoli turistici, 268/799 al minimo, EUR 5.469.023,68/EUR 6.524.121,74 dovuti turistici, EUR 6.524.121,74/799 per titolo ed EUR 5.469.023,68/575 per titolo turistico. Le percentuali native a sei decimali e le medie native a due decimali vengono riconciliate alla precisione dichiarata; le osservazioni derivate mantengono il rapporto esatto e numeratore/denominatore. Nessuna media semplice di percentuali o medie comunali.

Le mediane comunali sono quelle native già acquisite. La mediana dell'unione non si ricostruisce dalle quattro mediane; `weighted_ratio` sulla mediana è rifiutato, così come sui semplici totali. Non si abilita un benchmark dai soli totali o dalla mediana aggregata dello snapshot. Gli importi non attestano incasso o competenza di bilancio comunale.

La copertura dei poligoni è incompleta e non abilita superficie occupata, metri di costa concessi, quota di spiaggia o concentrazione dei concessionari. Le precedenti edizioni SID non sono armonizzate: serie, variazioni e trend rifiutati. I due collegamenti titoli–canoni e titoli–linea statistica Istat sono contesto, senza correlazioni automatiche, anomalie o conclusioni causali.

## Verifiche e avanzamento

48 valori correnti di riferimento per catalogo (dodici dimensioni × quattro comuni); componenti e puntatori risolvibili, esclusioni, ranking, cinque rapporti aggregati. Test avversari su identità/coorte, SHA, stato e duplicati, attribuzione portuale, identificativi Capitaneria duplicati/scambiati/rimossi, partizioni, conteggi frazionari, importi negativi, arrotondamenti, componenti pubblici, n.a. trasformati in zero e dati mancanti.

Copertura derivata: 141/225 effettivi, 93/181 sorgente; 84 residui, di cui 20 ambientali. Suite 383 domande (212 calcoli, 171 rifiuti), 50 collegamenti tipizzati e 52 carichi di prestazione. Report `reports/a6-maritime/`; tempi locali descrittivi. Dati, UI, asset, renderer, golden, Camaiore, workflow e Radar conservati. Le 35 letture territoriali e due riepiloghi mantengono perimetro e revisione aperta; nessuna nuova lettura pubblicata, nessuna chiusura di A6 o avvio A7. Quick/Full locali e CI sul candidato prima della revisione per merge del proprietario.
