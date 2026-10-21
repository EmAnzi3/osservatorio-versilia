# A7 — benchmark selettivi Toscana e Italia

Incremento opzionale del trasporto, derivato dal divario nativo/statico della
matrice A3→A6→A7. A6 resta DONE; nessuna modifica agli adapter, ai dati o alle
aspettative numeriche indipendenti. Nessun nuovo servizio o acquisizione.

## Perimetro

`--profile benchmark` materializza `benchmark_gap` soltanto sulle viste che
ammettono questa operazione e sui riferimenti `tuscany` / `italy` dichiarati in
`benchmarkScopesByDimension`. Per ciascuna vista/riferimento usa un Comune alla
volta, per tutti e sette i Comuni, con il periodo predefinito nativo. Non sceglie
l'ultimo anno disponibile e non ricostruisce benchmark assenti. I riferimenti
Versilia restano esclusi da questo incremento; nessun aggregato viene inferito.

Ogni risultato, rifiuto, periodo, componente, universo, avvertenza e fonte proviene
dal motore originale. La presenza nella dichiarazione non garantisce che tutte
le richieste siano calcolabili. Il browser non calcola differenze o percentuali.
Nessuna graduatoria politica o equivalenza tra scostamento e criticità.

```bash
python scripts/build_a7_query_runtime.py --catalog dist/data/site-data.json \
  --profile benchmark --output-dir /tmp/a7-benchmarks
python scripts/audit_a7_accessibility.py --catalog dist/data/site-data.json \
  --registry dist/data/source-registry.json --runtime /tmp/a7-benchmarks \
  --output-dir /tmp/a7-benchmark-access
```

Omettendo `--profile` restano i tre profili pubblici originali. Per misurare un
pacchetto combinato occorre specificare esplicitamente ciascun profilo. Un
pacchetto solo benchmark contiene comunque i dettagli delle viste: il suo peso
comprende tali metadati e non equivale al solo costo marginale degli shard.
Il confezionatore verifica richieste esatte, riferimenti, integrità, produttori
e misura; il lettore restituisce soltanto la richiesta esatta materializzata.
Periodi arbitrari, sottoinsiemi o consenso aggiunto non vengono riscritti.

## Trasporto distinto dall'interfaccia

La #462 non abilita il benchmark nell'esploratore pubblico: manca
ancora un selettore esplicito del riferimento e una presentazione revisionata
dello scostamento. Nella #462 anche una preview alimentata con un pacchetto benchmark lo
mantiene disabilitato. La matrice distingue quindi `materialized` nel trasporto
da `not_materialized` nell'interfaccia. Nessuna nuova pagina o promozione in menu.

Pubblicazione futura soltanto nel pacchetto atomico già approvato: intero grafo
verificato in staging, ancora indipendente incorporata nel modulo, un unico
artifact Pages, nessun fallback numerico per file mancanti o incompatibili.
Prima dell'ampliamento pubblico servono verifica della preview e dei controlli
nel browser, nuovi gate e merge autorizzato del proprietario.

Il successivo incremento UI, con scelta esplicita Toscana/Italia, è descritto in
`docs/A7_BENCHMARK_INTERFACE.md`. Non cambia il perimetro numerico del profilo.

## Misura del profilo isolato

Sul catalogo effettivo SHA256
`1416209ca86f27b4eaeede51e59a90edd0b24167f75c60e5157df4583678d710`:
112 indicatori hanno 353 viste con riferimenti Toscana/Italia dichiarati;
2.471 richieste Toscana e 1.400 Italia, 3.871 complessive. Risposte originali:
3.421 `computed`, 450 rifiuti. I rifiuti richiedono comparabilità esplicita e
conservano le guardie di osservazioni/copertura: nessun consenso viene aggiunto.

Il pacchetto solo benchmark include i dettagli di tutti i 225 indicatori e delle
3.359 viste: 2.462.131 byte gzip (239.766 di dettagli, 2.222.365 di risposte),
più 101.672 byte del manifest. Shard massimo: 8.202 byte gzip / 225.934 byte JSON.
Questi sono byte del profilo isolato, non del prodotto pubblico ampliato né del
solo download iniziale. Tempi locali solo diagnostici, fuori dagli artefatti;
nessuna promessa di latenza mobile. Non sono 3.871 nuove prove numeriche indipendenti.

## Verifiche

Il gate di trasporto esistente comprende il nuovo profilo opzionale, con campione
derivato dalle firme di operazioni e riferimenti dichiarati; due build identiche,
parità di tutte le risposte generate con A6, browser desktop/mobile per entrambi
i riferimenti presenti, rifiuto di richieste esterne al perimetro e verifica che
il benchmark resti disabilitato nella UI. La suite A6 resta l'autorità numerica;
le richieste del trasporto non sono nuovi casi indipendenti.

Misura completa, matrice derivata, gate e limiti del candidato sono attestati
nella PR. A7 resta IN_PROGRESS: non è un accesso universale a tutti i campi A3.
