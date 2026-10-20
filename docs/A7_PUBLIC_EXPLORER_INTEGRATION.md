# A7 — integrazione candidata dell’esploratore

A6 DONE, A7 IN_PROGRESS. Nessun merge o deploy autorizzato. La #457 verifica
l’esploratore isolato; questo incremento ne prepara l’integrazione nella build
ordinaria, senza aumentare la raggiungibilità nella navigazione.

`build_static_brand.py`, dopo il ripristino delle sorgenti canoniche e la pagina
editoriale A7, invoca `materialize_a7_public_explorer.py`. Il runtime viene prodotto
dal workbench originale con i tre profili predefiniti, su tutte le metriche e viste
native. Nessuna acquisizione, inventario manuale o operazione nuova. Ranking resta
opzionale nella preview precedente, non viene introdotto implicitamente qui.

Il confezionatore verifica tutti gli artefatti e i produttori prima di costruire
una nuova copia completa del sito in staging. Il verificatore ricontrolla tutti
gli hash del grafo. Soltanto allora viene sostituito il dist generato, conservando
la copia precedente per il ripristino se la rinomina finale fallisce. Questo è un
passaggio di build offline: la pubblicazione atomica avviene con l’unico artifact
Pages esistente, dopo i suoi gate. Un errore di build impedisce l’upload; il rollback
pubblico deve ripristinare l’intero artifact approvato, mai shard isolati.

La pagina contiene il percorso immutabile del grafo e l’hash del descrittore
`explorer-preview.json` (nome conservato per gli strumenti di revisione). Il percorso
del grafo deriva dagli hash dei suoi file; il modulo caricato contiene l’ancora
indipendente del runtime. Un descrittore scaricato non sceglie l’ancora fidata.
Il lettore originale verifica hash compressi/decompressi, schema/versioni e budget.
Nessun fallback ad altre release o numeri sostitutivi.

Il service worker non usa CacheStorage o cache HTTP per il grafo dell’esploratore:
le richieste richiedono rete e conservano la verifica del lettore. Una vecchia
pagina può soltanto leggere la propria release verificata o mostrare un errore;
non viene aggiornata silenziosamente a un altro manifest. Le altre pagine e i
piloti editoriali mantengono il comportamento approvato. La consultazione offline
dell’esploratore non è promessa.

Il verificatore pubblico esistente richiede anche il pannello e il descrittore
vincolato alla pagina. Controlla tutti i moduli/presentazione, manifest del runtime,
un dettaglio e uno shard di risposta con hash compressi e decompressi. Sotto
`--dist` e nel controllo live è un campione di disponibilità/integrità, non nuova
certificazione numerica o controllo di tutte le richieste. Il confezionamento
locale verifica invece l’intero grafo. Nessun nuovo workflow o servizio. Gli shard `.json.gz` sono byte applicativi:
il server deve conservarli senza un `Content-Encoding` HTTP aggiuntivo. Il probe
richiede `identity` e rifiuta una codifica inattesa, perché il browser la decodifica
prima degli hash mentre urllib normalmente conserva i byte ricevuti. Il deploy
live deve verificare anche questa condizione, non presumerla dai verdi locali.

Gate obbligatori sul nuovo candidato: browser desktop/mobile, guasti e recupero,
cache offline senza fallback, Quick e Full locali ordinari, CI Quick→Full effettivo
e A3. Non si trasferiscono i verdi della #457; la nuova main contiene anche il
marker #458, preservato. PR Draft fino alla verifica della preview. Pubblicazione
e controllo live effettivi soltanto dopo approvazione/merge del proprietario.

L’accesso resta limitato alle selezioni materializzate: nessun periodo arbitrario,
sottoinsieme, somma generica Versilia o media semplice dei tassi. Capacità non
trasportate, dati assenti e rifiuti metodologici rimangono distinti. Traduzione dei
metodi originali, export generale, altre operazioni e dossier restano incrementi
successivi; nessuna chiusura anticipata di A7.
