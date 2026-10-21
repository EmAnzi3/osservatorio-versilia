# A7 — accessibilità A3 → A6 → A7

Audit derivato, non inventario canonico aggiuntivo. A6 resta DONE, A7 IN_PROGRESS.
La matrice A3 strict, il catalogo effettivo, le dichiarazioni A6, i casi indipendenti
originali e gli artefatti del runtime sono gli input. Nessuna acquisizione nuova.

## Riproduzione

```bash
python scripts/build_static_brand.py
python scripts/build_a7_query_runtime.py --catalog dist/data/site-data.json \
  --output-dir /tmp/a7-runtime
python scripts/audit_a7_accessibility.py --catalog dist/data/site-data.json \
  --registry dist/data/source-registry.json --runtime /tmp/a7-runtime \
  --site dist \
  --output-dir /tmp/a7-accessibility
```

Il runtime deve provenire da questo candidato. L'audit verifica identità del
catalogo, motore, workbench, builder e lettore; verifica hash e dimensioni di ogni
artefatto e confronta ogni risposta trasportata con il motore nativo. Una release
parziale resta parziale: le richieste mancanti non diventano materializzate.
Senza `--runtime`, soltanto l'accesso statico è `not_inspected`, mai una falsa
attestazione del trasporto. Le prove native passano comunque dal workbench.

Con `--site` viene verificato il grafo completo vincolato alla pagina. Le capacità
dei controlli sono derivate dalle dichiarazioni e dai blocchi del medesimo grafo,
riusando le ricette native. `artifactGeneralExplorer` e `interfaceSummary`
distinguono capacità preparate, non materializzate e non ammesse. Senza `--site`
rimangono `not_inspected`. `publicGeneralExplorer=publication_not_inspected`
resta indipendente: un artifact locale non prova una pubblicazione. Il report 3
estende la matrice 2 senza trasformare le prove di percorsi in nuova copertura
semantica. Integrazione candidata: `A7_PUBLIC_EXPLORER_INTEGRATION.md`.

Il JSON contiene tutte le coppie A3 e tutte le coppie vista/operazione A6. Include
contesto, benchmark, ammissione condizionata, delega del workbench, copertura
statica effettiva e capacità preparate dell’interfaccia quando viene fornito il sito generato.
Le tre modalità predefinite non coprono periodi o selezioni arbitrari.
Il Markdown riepiloga i conteggi derivati; il JSON permette di risalire alle righe.

Tutte le aspettative indipendenti originali passano attraverso il workbench,
compresi benchmark, ranking, variazioni, rapporti ponderati e associazioni.
Non sono una whitelist e non provano ogni combinazione di richieste. L'ammissione
di una operazione nella dichiarazione non evita le precondizioni di una selezione.
`weighted_ratio` è il rapporto ammesso delle componenti, non un `sum()` generale.

## Stati da non confondere

| Livello | Stato | Significato |
| --- | --- | --- |
| A3 | AVAILABLE_MISSING | Opportunità disponibile ma non acquisita; non si amplia qui il catalogo |
| A3 | SOURCE_UNAVAILABLE / NOT_APPLICABLE | Classificazione originale con evidenza conservata |
| A3 → A6 | acquired_access_not_proven | Acquisito, ma accesso alla specifica evidenza non provato in questo perimetro |
| A3 → A6 | catalog_path_witness_only | Puntatore di evidenza raggiunto; non certifica tutta la dimensione |
| A6 | not_admitted | Operazione non ammessa sulla vista, indipendentemente dall'esistenza dei numeri |
| A7 statico | not_materialized | Capacità dichiarata fuori dai profili/selezioni realmente trasportati |
| A7 statico | materialized | Tutte le richieste del profilo nativo verificato sono presenti; possono includere rifiuti |
| A7 artifact UI | prepared_native_defaults | Controlli preparati sui profili nativi del sito generato verificato; non prova tutte le interazioni browser |
| A7 artifact UI | not_inspected / not_materialized | Sito non ispezionato oppure capacità senza blocco consultabile nella UI |
| A7 pubblicazione | publication_not_inspected | L’audit offline non attesta integrazione in main, deploy o disponibilità live |

Il collegamento delle nove dimensioni A3 alle viste A6 **non è interamente
risolto**. Gli acquisiti possono risiedere in companion, route speciali, formule o
altri snapshot. Non si deduce l'accesso dal nome della dimensione, né si dichiara
una fonte assente perché il motore non la espone. Il resolver conserva separati
percorsi risolti, operandi mancanti e collegamenti semantici non ancora provati.
Un puntatore è una prova limitata, non una nuova certificazione numerica o
semantica. Il debito residuo resta esplicito: non si dichiara chiusa
l'accessibilità universale.
Il confronto normalizza soltanto l'indice della riga comunale: conserva gli
indici di categoria e le chiavi degli anni. Un'altra categoria o un altro anno
non sono una prova di accesso al percorso acquisito; regressioni negative
impediscono di far coincidere questi puntatori.

## Prove native e statiche separate — schema del report 3

`acquisitionReference` deriva i requisiti dalla matrice strict. Le espressioni
locali composte (`+`, `/`, `×`, `=`, `sum`) vengono lette per individuare gli
operandi, **senza eseguirle**. Tutti gli operandi devono essere raggiunti prima
di dichiarare `all_required_paths_witnessed`. Le wildcard sulle categorie sono
espanse contro il payload canonico e conservano ogni indice concreto.
Un solo numeratore non prova anche il denominatore; un valore uguale non collega
due campi diversi. Espressioni o operandi non risolti restano espliciti.

I companion riusano esclusivamente `data/enrichment-companion-contract.json`.
Le relazioni di dettaglio rimangono relazioni verso il companion: non trasferiscono
automaticamente la dimensione alla misura originaria. Il resolver legge le sette
famiglie presenti nel contratto: rapporti tra metriche, companion normalizzati,
variazioni tra estremi di una serie, rapporti tra parti, conteggi su popolazione
media, campi target su un companion e numeratori nel catalogo sorgente canonico.
Individua campi, parti e periodi dichiarati; nessuna formula viene ricalcolata.
`metric_current` resta il riferimento nativo del companion, anche quando la sua
descrizione temporale non è un semplice anno; non si inventa un token annuale.
Gli estremi di una variazione provengono dal contratto, non dal titolo del target.
Nuove famiglie non riconosciute restano `formula_bridge_not_proven`. Il fatto che
A3 abbia riconciliato una formula non prova da solo che A6 ne esponga ogni campo.

`workbenchAccess` osserva risposte realmente calcolate dal workbench:
confronto nativo corrente sui sette Comuni (oppure letture puntuali se dichiarate),
serie nativa del primo Comune ordinato per codice, rapporti ponderati dichiarati,
benchmark dichiarati per Comune e richieste delle componenti con periodo esplicito
del contratto companion. Si aggiungono tutti i casi indipendenti originali,
incluse associazioni e variazioni. Se è fornito un runtime, anche ogni sua
risposta viene rigiocata attraverso il workbench e aggiunta al ledger nativo:
un riferimento statico interamente provato deve avere la corrispondente prova
nativa. Non è una prova di ogni periodo, sottoinsieme o coppia possibile.
I rifiuti rimangono nel ledger, ma non diventano prove di
accesso calcolato; le osservazioni mancanti o non applicabili non sono numeri.

`staticAccess` verifica gli stessi requisiti soltanto nelle risposte realmente
materializzate. Può quindi differire dal workbench senza che manchi il dato.
I ledger `nativeProbes` e `staticProbes` conservano richiesta, esito, motivi e
digest portabile della risposta; ogni prova di percorso riferisce il suo ledger,
ruolo, periodo e Comune. Per le componenti datate, anche il periodo restituito
deve coincidere: un indice di array uguale non basta a provare lo stesso anno.

Si riconoscono i puntatori di valore/componenti del catalogo anche quando A6 li
restituisce come `published_benchmark`, vincolati al digest del catalogo effettivo.
Un puntatore di definizione non prova l'accesso a un valore. Per storage separati
servono hash dei file/parti e dei byte decodificati restituiti da A6, uguaglianza
con l'intero payload dichiarato da A3 e percorso realmente esistente. Nome della
route o prefisso del file, da soli, non costituiscono una prova. Il confronto
conserva i tipi JSON (`true` è distinto da `1`); la cache di verifica è vincolata
anche alla lista delle parti e ai loro digest. Il rapporto relativo dello storage
elettorale riusa la sintassi del detector A3 per due campi nello stesso oggetto.
I riferimenti compact dell'Atlante riusano il suo `compactSchema` validato da A3:
si individuano assi, categorie e totali dichiarati, senza trasferire questa prova
strutturale a tutte le viste o operazioni dell'adapter. Un asse non restituito
come valore rimane un requisito senza prova, anche se il payload lo contiene.

Stati di accesso: `all_required_paths_witnessed`, `some_required_paths_witnessed`,
`no_path_witness_in_probe_scope`, `unresolved_acquisition_reference`,
`not_acquired` e (solo statico) `not_inspected`. **Anche il primo stato certifica
percorsi osservati, non l'intera dimensione A3 né una nuova capacità di calcolo.**

`linkageSummary`, `linkage` e `accessEvidencePaths` restano per compatibilità la
misura precedente dei soli riferimenti semplici nel trasporto statico. Non vanno
confrontati come se fossero la nuova copertura nativa: usare i riepiloghi distinti
`acquisitionReferenceSummary`, `workbenchAccessSummary`, `staticAccessSummary`.
Nessun ampliamento del runtime, dei suoi default o dell'interfaccia pubblica.

## Incremento selettivo: ranking descrittivo

Il divario tra capacità A6 e trasporto comprende il ranking comunale delle viste
che lo ammettono. Il profilo opzionale `ranking` materializza una sola richiesta
`rank` per vista sui sette Comuni, al riferimento nativo. Nessun ordinamento tra
categorie ATECO, sottoinsieme territoriale, periodo, consenso o polarità implicita.
Rifiuti, pari merito, null, fonti e avvertenze restano originali.

```bash
python scripts/build_a7_query_runtime.py --catalog dist/data/site-data.json \
  --profile ranking --output-dir /tmp/a7-rank-only
```

`--profile` è esplicito e ripetibile. Se omesso conserva i tre profili iniziali.
Una build solo ranking consente di misurare il costo incrementale prima di
aggiungerlo a una release. Nessuna nuova pagina o integrazione pubblica.
Il gate di trasporto verifica tutti e quattro i profili nel campione derivato,
con due build byte-identiche e parità browser desktop/mobile.
Il lettore usa una copia privata validata del piano prima del primo `await`:
un test sospende un fetch reale, sostituisce la richiesta del chiamante e verifica
che selezione, risposta, piano restituito e digest conservino l'intento iniziale.
Il rilievo P2 della revisione #453 è stato riprodotto sulla versione precedente;
non si trasferiscono i suoi verdi alla correzione.

## Pubblicazione atomica e ancora d'integrità: contratto prima del rollout

1. Costruire runtime e pagina in una directory di staging vuota dalla stessa
   revisione/catalogo. Non scrivere shard nella release già pubblicata.
2. Validare l'intero grafo: schema/versioni, riferimenti, dimensioni, digest
   compressi/decompressi, corrispondenza catalogo e lettore; eseguire i gate.
   Qualsiasi artefatto mancante, incompatibile o corrotto interrompe la build.
3. Incorporare nella pagina/modulo della release il digest atteso di
   `release.json` e l'identità del lettore. L'ancora non viene ricavata dallo
   stesso manifest scaricato o dai parametri della domanda.
4. Conservare manifest e shard sotto un percorso immutabile identificato dal
   digest della release. Tutte le URL del lettore rimangono relative a quella
   directory, sulla stessa origine; nessun puntatore globale a shard mutevoli.
5. Pubblicare insieme pagina, modulo, manifest e grafo con l'unico artifact Pages
   già esistente. Solo dopo validazione completa; nessun upload progressivo sulla
   directory live e nessun nuovo workflow o servizio implicito.
6. Client e cache restano vincolati a una release. Un errore di rete/integrità/
   versione elimina i risultati della selezione e mostra un errore comprensibile
   con ritentativo della stessa release. Nessun fallback automatico a numeri
   vecchi o a un'altra release; nessun risultato parziale silenzioso.
7. Il controllo post-deploy deve verificare ancora e campione di shard della
   release live, separatamente dai verdi della PR. Il rollback ripristina
   l'intero artifact approvato, mai file isolati.

Il confezionamento locale e il verificatore del grafo sono implementati in
`A7_ATOMIC_RUNTIME_PACKAGE.md`; la build pubblica non li integra ancora. Questo
resta il contratto del rollout futuro, **non una pubblicazione autorizzata**. Il lettore sperimentale verifica già ancora separata,
hash, budget, consenso e copie/cache isolate. L'integrazione nel builder pubblico
richiede ancora legame pagina/lettore/ancora e prove
browser di errori e recupero nella UI, prima di rendere Chiedi più raggiungibile.

## Benchmark opzionali e interfaccia

Le ricette del profilo opzionale `benchmark` derivano operazione e riferimenti
dalla dichiarazione della specifica vista; includono solo Toscana/Italia, un
Comune alla volta al riferimento nativo. Il report valuta le richieste esatte
materializzate, non il nome del profilo. L'interfaccia rimane distinta: il
trasporto benchmark non implica un selettore pubblico del riferimento.
Metodo e riproduzione: `A7_SELECTIVE_BENCHMARKS.md`.
