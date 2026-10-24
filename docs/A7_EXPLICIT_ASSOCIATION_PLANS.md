# A7 — trasporto di piani espliciti di associazione

Primo incremento tecnico A7.5.4, separato dai controlli pubblici. A6 resta DONE;
A7 IN_PROGRESS. Nessun adapter, dato, metodo numerico o default pubblico cambia.

## Perché un piano esplicito

La dichiarazione `correlation` di una vista non autorizza qualunque coppia.
Servono due selettori, asse, metodo e motivo della selezione; A6 verifica
allineamento, periodi, frequenze, universi e guardie proprie degli adapter.
Il nuovo trasporto non cerca tutte le coppie, non ordina coefficienti e non
sceglie relazioni dai risultati. Le domande di accettazione non sono una whitelist.

`build_a7_query_runtime.py --association-plan piano.json` accetta il contratto
generale del workbench: `schemaVersion: 1`, da una a 32 componenti e massimo
100.000 byte, con ID distinti e richieste strutturate. In questa estensione
ogni richiesta deve avere operazione `correlation`. Il piano viene copiato e
validato prima di creare l'output. I campi di selezione usano token stringa,
con booleani per il consenso; campi numerici nella richiesta sono fuori da questo
trasporto e rifiutati prima della build. Questo evita identità diverse fra
serializzazioni Python/JavaScript, senza riscrivere una richiesta nativa.
Nessun periodo, dimensione, metodo, asse,
scopo o consenso viene aggiunto o riscritto. Anche i rifiuti originali vengono
materializzati, compresi quelli per scopo mancante e metrica sconosciuta.

Il motore Python A6 esegue il piano originale. Ogni componente conserva
richiesta, risposta, precisione, coppie osservate, n, esclusioni, sensibilità
leave-one-out, fonti, puntatori e avvertenze. L'unica normalizzazione resta
quella approvata per il percorso locale del catalogo, identificato dal suo hash.
Correlazione non significa causalità; i sette Comuni non sono automaticamente
un campione indipendente. Nessuna significatività o efficacia amministrativa
viene inventata. I valori `null` originali restano `null`.

## Confine di materializzazione

L'opzione è assente per default: profili, ricette e materializzatore pubblico
restano quelli della #473. Il piano opzionale si aggiunge come indice ancorato
`associationPlan` nel manifest, con piano originale, hash e riferimenti ai blocchi
compressi. Il contatore `profiles.association` misura soltanto quelle componenti;
non è il numero di coppie universalmente disponibili. Il filtro `--metric`
riguarda le viste dei profili ordinari; il piano conserva il proprio perimetro
esplicito, senza ampliare implicitamente quei profili.
L'`envelope` ordinario continua a descrivere quei profili senza opt-in; il piano
dichiara separatamente `consent=original_request_and_browser_confirmation`.

Il lettore risolve soltanto la richiesta identica materializzata. Cambiare
selettori, ordine, periodi, asse, metodo o scopo restituisce `not_materialized`;
non è un rifiuto metodologico A6 né prova di dato assente. Gli ID dei passi del
piano chiamante possono cambiare: l'identità del risultato è la richiesta esatta.
Il browser non esegue né regressioni né correlazioni e non scarica blocchi prima
della richiesta. Cache, copie delle risposte e snapshot prima del primo `await`
restano protetti.

Il consenso protegge anche osservazioni numeriche conservate in un rifiuto con
coppie incomplete: `coverage` può essere completa per le due variabili mentre
`pairCoverage` non lo è. La conferma permette di consultare il rifiuto originale,
senza introdurre `allowPartial` nella richiesta o trasformarlo in risultato.

Il verificatore atomico controlla l'intero grafo, indice, hash del piano e delle
richieste, selezione e produttori delle risposte. I blocchi mancanti, corrotti o
di una release diversa non producono fallback. Il pacchetto conserva ancora
indipendente e pubblicazione in staging con un solo rename; non esegue deploy.

## Audit e riproduzione

L'audit A3→A6→A7 registra ogni selezione trasportata separatamente in
`associationSelections`, con richiesta esatta e stato nativo. Non promuove tutte
le correlazioni di una vista a materializzate e non attesta controlli pubblici:
`artifactGeneralExplorer=not_presented`. Anche queste risposte contribuiscono
alle prove dei soli percorsi A3 effettivamente testimoniati.

```bash
python scripts/build_a7_query_runtime.py --catalog dist/data/site-data.json \
  --output-dir /tmp/a7-piano --profile current \
  --metric population --metric income --max-views-per-metric 1 \
  --association-plan piano.json
python scripts/a7_runtime_package.py --help
python scripts/test_a7_query_runtime.py --catalog dist/data/site-data.json
```

Le metriche nell'esempio sono prove riproducibili, non autorizzazioni. Il gate
esistente verifica un'ancora Spearman indipendente già approvata in A6, parità
delle risposte Pearson e dei rifiuti, due build byte-identiche inclusi misura e
release, profili precedenti invariati, pacchetto atomico e browser 1440/390.
Include coppie incomplete con singole coperture complete, consenso, selezioni
non materializzate, blocco mancante, cache e modifica del piano durante il fetch.
Queste sono prove di trasporto, non nuove prove numeriche indipendenti.

Prima dell'interfaccia generale restano: scelta guidata e motivata delle coppie,
periodi e assi, misura del perimetro selezionato e dei suoi costi, grafico dei
punti e limiti comprensibili. Nessun catalogo parallelo di risposte, ricerca
indiscriminata di associazioni, nuovo servizio, modello esterno o costo ricorrente.
