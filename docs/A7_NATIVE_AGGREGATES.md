# A7 — rapporti aggregati nativi della Versilia

A6 DONE, A7 IN_PROGRESS. Incremento A7.5.3 su branch dedicato; nessun merge o
deploy dell’assistente. La matrice A3→A6→A7 individua capacità native ancora
non materializzate nel trasporto: questo incremento ne seleziona una sola.

## Perimetro derivato

Il profilo opzionale `aggregation` deriva le viste con `weighted_ratio` dalle
dichiarazioni degli adapter del catalogo canonico. Non contiene un elenco
parallelo di indicatori. Produce una richiesta per vista sui sette codici
comunali canonici ordinati, senza periodi arbitrari, sottoinsiemi, riferimento
sintetico “versilia” o `allowPartial`. I tre profili predefiniti del generatore
restano invariati. La build pubblica candidata sceglie esplicitamente i tre
profili, `benchmark` e `aggregation`; ranking e altre operazioni non si attivano.

Sul catalogo congelato SHA256
`1416209ca86f27b4eaeede51e59a90edd0b24167f75c60e5157df4583678d710`,
la ricognizione riproducibile trova 242 viste di 94 indicatori con questa
operazione dichiarata. Le 242 richieste native producono 210 risultati e 32
rifiuti; tutte le 32 hanno copertura parziale che richiederebbe opt-in. Quattro
hanno anche osservazioni insufficienti. Questa ricognizione delimita il profilo:
non è un nuovo corpus indipendente di prove numeriche. La build combinata completa misura 41.993 richieste (24.914 risultati e
17.079 rifiuti), 225 indicatori e 3.359 viste, 104.234.277 byte gzip: incremento
di 1.172.148 byte rispetto ai quattro profili della #463. Il massimo shard resta
68.838 byte gzip / 2.338.129 byte decompressi. È una misura del trasporto, non
una nuova certificazione numerica. I gate del candidato sono attestati separatamente.

## Metodo e interfaccia

Il workbench originale esegue il rapporto delle componenti coerenti ammesse
dall’adapter. Il browser presenta il risultato, numeratore, denominatore,
scala, unità e periodi originali; non somma e non ricalcola. Il rapporto non è
la media semplice dei tassi comunali. Nessuna somma generica di indicatori,
nessuna sostituzione di n.d. con zero, nessun giudizio politico o causale.

Il controllo “Rapporto aggregato della Versilia” compare soltanto per le viste
materializzate con questa capacità. Il selettore comunale viene nascosto perché
il perimetro è obbligatoriamente quello dei sette Comuni. Un risultato mostrato
come Versilia richiede copertura utilizzabile completa e gli esatti sette codici,
oltre a componenti numeriche finite con denominatore e scala positivi. Un
incompatibile risultato computed causa un errore, senza rappresentazione parziale.

La sintesi arrotonda soltanto la presentazione come gli altri risultati;
“Componenti del calcolo” conserva la precisione di presentazione originale e i
campi del risultato nativo. La tabella conserva osservazioni, componenti,
metadati e fonti. I periodi di numeratore e denominatore, quando distinti nel
motore, restano espliciti: non si inventa un anno comune.

I rifiuti A6 restano rifiuti: eventuali osservazioni comunali non sostituiscono
il rapporto dell’intera Versilia. Il consenso al caricamento di una copertura
parziale non aggiunge `allowPartial` alla richiesta e non trasforma il rifiuto in
un risultato. Cambio di indicatore, vista o operazione revoca risultati e
consenso; una risposta tardiva non riappare dopo una nuova selezione.

## Artefatti e verifiche

Il confezionamento atomico, l’ancora d’integrità indipendente e il comportamento
in presenza di file mancanti o incompatibili restano quelli di
`A7_ATOMIC_RUNTIME_PACKAGE.md`. Il profilo è attestato nell’envelope; il lettore
rifiuta richieste fuori dal perimetro esatto. La ricevuta dell’interfaccia versione
3 permette alla matrice derivata di distinguere capacità trasportata e presentata.
Nessuna attestazione di pubblicazione deriva da una preview o dai verdi della PR.

I gate esistenti verificano parità delle risposte native, riproducibilità di tutti
i file, limiti di selezione, integrità, consenso, guasti e recupero. Le prove
browser desktop/mobile includono risultati e rifiuti aggregati, componenti e
periodi, revoca e risposta tardiva. Quick e Full locali ordinari e CI Quick→Full
con audit A3 devono passare sul medesimo nuovo candidato prima del via libera.
