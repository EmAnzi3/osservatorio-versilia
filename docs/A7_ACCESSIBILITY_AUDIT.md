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
  --output-dir /tmp/a7-accessibility
```

Il runtime deve provenire da questo candidato. L'audit verifica identità del
catalogo, motore, workbench, builder e lettore; verifica hash e dimensioni di ogni
artefatto e confronta ogni risposta trasportata con il motore nativo. Una release
parziale resta parziale: le richieste mancanti non diventano materializzate.
Senza `--runtime`, lo stato è `not_inspected`, mai una falsa attestazione.

Il JSON contiene tutte le coppie A3 e tutte le coppie vista/operazione A6. Include
contesto, benchmark, ammissione condizionata, delega del workbench, copertura
statica effettiva e assenza dell'esploratore generale nell'interfaccia pubblica.
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
| A7 pubblico | not_presented | Esploratore generale non integrato; i piloti editoriali esistenti sono distinti |

Il collegamento delle nove dimensioni A3 alle viste A6 **non è interamente
risolto**. Gli acquisiti possono risiedere in companion, route speciali, formule o
altri snapshot. Non si deduce l'accesso dal nome della dimensione, né si dichiara
una fonte assente perché il motore non la espone. Il detector accetta soltanto
percorsi strutturali locali non ambigui e registra puntatori del catalogo
realmente restituiti. Un puntatore è una prova limitata, non una nuova
certificazione numerica o semantica. Restano da definire collegamenti verificabili
per le evidenze composite e misurare i dettagli non raggiunti: questo è un debito
esplicito dell'audit, non la chiusura dell'accessibilità universale.
Il confronto normalizza soltanto l'indice della riga comunale: conserva gli
indici di categoria e le chiavi degli anni. Un'altra categoria o un altro anno
non sono una prova di accesso al percorso acquisito; regressioni negative
impediscono di far coincidere questi puntatori.

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

Questo è il contratto del rollout futuro, **non un publisher implementato o una
pubblicazione autorizzata**. Il lettore sperimentale verifica già ancora separata,
hash, budget, consenso e copie/cache isolate. L'integrazione nel builder pubblico
richiede ancora verificatore del grafo, legame pagina/lettore/ancora e prove
browser di errori e recupero nella UI, prima di rendere Chiedi più raggiungibile.
