# A7 — pacchetto immutabile e finalizzazione atomica

Incremento tecnico isolato: prepara un artifact, non esegue merge, upload o deploy.
Non modifica la build pubblica, `/chiedi/`, menu, dati, adapter o golden. A6 DONE,
A7 IN_PROGRESS. Non amplia i profili o le richieste materializzate.

## Perché questo incremento

La matrice A3→A6→A7 distingue prove native, risposte trasportate e capacità non
presentate. Un pacchetto parziale conserva `explicit_subset`: il confezionamento
non lo trasforma in copertura universale. Prima di esporre selettori generali,
la pagina deve poter dipendere da una release unica, verificata e identificata.
Il confezionatore attua il confine locale richiesto dal contratto del rollout in
`A7_ACCESSIBILITY_AUDIT.md`; il collegamento alla pagina/artifact Pages e il
controllo post-deploy restano da implementare prima di una pubblicazione autorizzata.

## Riproduzione

Dopo la materializzazione ordinaria del catalogo effettivo e del runtime:

```bash
python scripts/build_a7_query_runtime.py --catalog dist/data/site-data.json \
  --output-dir /tmp/a7-runtime
python scripts/a7_runtime_package.py --catalog dist/data/site-data.json \
  --runtime /tmp/a7-runtime --output-dir /tmp/a7-package
```

L'output deve essere assente, anche se una directory precedente fosse vuota.
Il modulo espone anche `verify_runtime(folder, catalog)` e
`verify_package(folder, catalog)` per la futura integrazione nella pipeline.
Nessun argomento abilita il deploy o modifica una release esistente.

## Controlli prima della finalizzazione

Il verificatore percorre tutti i dettagli e tutti gli shard del pacchetto:

- schema, identità di catalogo/motore/workbench/builder/lettore e Comuni;
- tutte le impronte native di adapter, policy, eleggibilità e versione nelle
  risposte, derivate dal medesimo header restituito dal motore A6 originale,
  senza un elenco parallelo di produttori;
- profili effettivi, ambito completo o sottoinsieme esplicito, viste e operazioni
  derivate dalle dichiarazioni A6 e richieste esatte delle ricette esistenti;
- byte e SHA256 compressi e decompressi, con letture limitate prima del parsing;
- identità richiesta/risposta e produttori, esiti originali e conteggi della misura;
- assenza di riferimenti mancanti, file estranei, link simbolici o residui di altre
  release; JSON non finito o con chiavi duplicate viene rifiutato;
- modulo d'ingresso, lettore e descrittore finale coerenti con il grafo verificato.

Non ricalcola i risultati né certifica nuovamente le fonti. La suite numerica A6,
la parità del trasporto e i gate generali rimangono distinti e obbligatori.
Il descrittore è un artefatto derivato: non è un secondo catalogo, un'autorità
per modificare l'ancora o una configurazione letta dalle domande del pubblico.

## Struttura del pacchetto

Il risultato contiene `package.json`, un modulo `a7-<SHA256-del-modulo>.mjs`
e la directory `runtime/<SHA256-di-release.json>/` con manifest, misura,
lettore originale e tutti i blocchi. I file del runtime vengono copiati byte
per byte. Il modulo include i byte originali del lettore e il digest atteso del
manifest come costante: nessun secondo motore e nessun hash fidato ricavato dal
manifest appena scaricato. Il nome del modulo cambia anche se cambia soltanto
il caricatore. I percorsi sono relativi al modulo, compatibili con un prefisso
di progetto Pages, e vincolati alla stessa origine.

La futura pagina deve incorporare direttamente il percorso del modulo prodotto
nella medesima build. Non deve scaricare un descrittore mutevole per scegliere
quale release considerare attendibile. Il modulo espone `openPackagedRuntime()`
senza argomenti per cambiare URL o ancora. L'API restituita è il lettore originale:
`discover()` e `run(plan, {approvedPartial})`, con consenso e rifiuti invariati.

## Atomicità e guasti

La copia e la validazione avvengono in staging privato nello stesso filesystem
della destinazione. Soltanto dopo tutti i controlli una singola rinomina rende
visibile la directory completa. Un fallimento elimina lo staging e lascia
assente la nuova destinazione; un pacchetto precedente resta immutato. Non si
aggiornano file di una release già esistente. Questo è il confine di finalizzazione
locale, non un protocollo di upload progressivo verso il sito live.

Nel browser il modulo carica soltanto il manifest all'apertura, poi dettaglio e
shard richiesti. Il manifest ha limite di 2 MiB ed è verificato contro l'ancora
incorporata; redirect e URL esterni non sono autorizzati. I limiti originali del
lettore si applicano ai blocchi. Errori di rete, file mancanti, corruzione o
incompatibilità interrompono la promessa: nessun risultato sostitutivo, nessun
cambio automatico di release o servizio esterno. Una nuova apertura ritenta la
stessa release e può recuperare dopo il ripristino dei file.

L'interfaccia futura dovrà cancellare i risultati della selezione fallita,
mostrare un errore comprensibile e offrire questo ritentativo. Quella gestione
visibile non è implementata o verificata da un modulo senza UI. Per il rollout
restano necessari pagina e pacchetto nell'unico artifact Pages, verifiche browser
della UI e controllo live di ancora e campione di shard. Rollback dell'intero
artifact, mai di singoli file.

## Prove

Il gate già esistente `test_a7_query_runtime.py` richiama le regressioni di
`test_a7_runtime_package.py` sullo stesso campione derivato, senza nuovo workflow
o inventario di indicatori. Due confezionamenti da percorsi diversi devono essere
byte-identici; una finalizzazione interrotta non deve esporre output parziale.
Le prove negative coprono dettagli/shard mancanti, corruzione, identità e schema,
misura errata, file misti, link, output esistente e descrittore alterato.
Grafi formalmente coerenti ma con impronte adapter/policy/eleggibilità/versione
errate o mancanti devono essere respinti prima della finalizzazione.

Il browser reale desktop/mobile importa il modulo generato sotto un prefisso
annidato; verifica caricamento selettivo, parità con il workbench, rifiuto di
manifest mancante/corrotto/troppo grande e dettagli/shard guasti, poi recupero
sulla stessa release. Sono verifiche dell'API e del confezionamento, non di una
nuova pagina pubblica né della disponibilità del CDN delle fonti.
