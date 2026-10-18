# A7 — lettura puntuale, disponibilità e accettazione misurata

## Capacità e contratto

`observe` è un'estensione esplicita del motore deterministico, non una riapertura
della certificazione A6. Usa una sola osservazione nativa di una vista numerica
già consultabile: un Comune obbligatorio, un solo periodo se specificato. Il
periodo omesso conserva esattamente la scelta nativa dell'adapter: non significa
data odierna né massimo anno di ogni campo acquisito.

```json
{"operation":"observe","selectors":[{"metric":"population","dimension":"total","towns":["046030"]}]}
```

Richiesta ammessa soltanto per viste che già dichiarano `compare`; tutte le
guardie di selezione, snapshot, classificazione, periodo, universo e fonte sono
riusate. La verifica di eleggibilità ha minimo uno e richiede esattamente una
osservazione. L'output usa `interpretationLevel=observation`, senza confronto,
graduatoria o conclusione amministrativa. Nessun Comune di appoggio nascosto.

Null, dato non applicabile e dato non disponibile restano osservazioni escluse;
anche con consenso parziale una selezione senza valore utilizzabile non produce
un calcolo. Zero resta zero. `compare` conserva minimo due; `lookup` rimane
riservato alla lettura GAIA per località/parametro, con limiti e valori censurati
originali. L'Atlante richiede ancora una vista esplicita: `territoryTotal` non è
una somma di divisioni, classi o righe artigiane. Nessuna aggregazione Versilia
aggiunta, nessuna operazione statistica o adapter indeboliti.

## Disponibilità e fonti

```bash
python scripts/a7_query_workbench.py --catalog dist/data/site-data.json \
  --availability --metric population --dimension total --town 046018
```

La risposta contiene la richiesta corrente e, dove dichiarata, la richiesta
`series` della stessa vista/Comune: osservazioni con periodi, fonti, puntatori,
hash, copertura e rifiuti. `history=null` con `not_declared` significa storico non
esposto, non assente nella fonte. Uno storico rifiutato conserva il motivo. Nessun
anno viene estratto dall'etichetta e nessuna combinazione viene inventata.
Le analisi GAIA restano un insieme di località, non un valore medio comunale.

Questo rende ispezionabile la disponibilità operativa di una selezione; non
completa l'audit di tutti i campi A3 acquisiti né espone un nuovo servizio pubblico.
Il catalogo effettivo resta derivato dalla build canonica. Nessun inventario
parallelo è usato per autorizzare richieste.

## Verifiche riproducibili

```bash
python scripts/test_a7_query_workbench.py --catalog dist/data/site-data.json
python scripts/test_a7_point_observations.py --catalog dist/data/site-data.json
python scripts/audit_a7_question_feasibility.py --catalog dist/data/site-data.json \
  --output-dir /tmp/a7-feasibility
```

I tre controlli fanno parte del preflight sul catalogo effettivo. La suite A6
conserva tutte le 3.727 aspettative indipendenti (2.033 calcoli / 1.694 rifiuti).
Le 3.393 osservazioni delle risposte `compare` revisionate vengono rilette
singolarmente: valori, componenti, periodi e provenance devono essere identici.
Un'ulteriore ancora usa direttamente i record POSAS congelati. Parità e ancore
non sono due conteggi di nuove prove numeriche indipendenti.

Le sonde generate coprono tutte le 3.342 viste numeriche con un Comune esplicito
e tutti i sette Comuni per la prima vista numerica di ogni carrier. Le 17 viste
GAIA sono preservate dalla suite originale. Questa prova di accesso non verifica
ogni combinazione vista×Comune×periodo e non certifica ogni valore sorgente.
Sono verificati anche zero/null, assenza di fonte, selezioni multiple/duplicate,
periodi inesistenti, dimensioni inventate, rifiuto del totale Atlante implicito,
parità con il workbench, isolamento e ripetibilità.

La matrice [dei quesiti](A7_QUESTION_FEASIBILITY.md) viene eseguita sul catalogo
reale. I casi in `ci/a7-question-feasibility-cases.json` dichiarano requisiti,
chiarimenti, richieste e lacune; non contengono risposte numeriche e non vengono
importati dal runtime. Il JSON generato conserva gli esiti completi. Sono esempi
revisionati, non una prova di comprensione linguistica generale. I quesiti su
metodo e segnalazioni hanno evidenze già disponibili, ma richiedono ancora un
resolver nel workbench: non vengono dichiarati risposte automatiche completate.

## Decisione di prodotto ed esecuzione su Pages

Prima modalità: esplorazione guidata di tema, misura, vista, Comune, periodo e
operazione, con spiegazioni/fonti. Testo libero successivo, eventualmente tradotto
in piano validato; nessun modello genera numeri. I dossier usano gli stessi piani.

Misura iniziale sul catalogo effettivo di questo candidato: 4.886.781 byte JSON,
423.191 byte gzip; scoperta sintetica 41.596 byte. Nel Python locale con
`tracemalloc` attivo: circa 1,05 s per inizializzare il motore, 4,8 ms mediana di
dieci letture puntuali, 2,19 s per la scoperta sintetica e circa 25 MB di picco
tracciato. Sono misure esplorative di un ambiente, senza soglie prestazionali e
senza valore predittivo per smartphone o JavaScript. Il catalogo non comprende
da solo tutti i payload climatici e gli snapshot necessari al motore.

Esperimento di dimensionamento su checkout isolato pulito: 3.359 viste × sette
Comuni = 23.513 richieste correnti, 14.869 calcolabili e 8.644 rifiutate per valore
mancante/non applicabile, senza altri motivi di rifiuto. Circa 496 MB di risposte
complete non compresse; 21.538.761 byte gzip sommati per vista, mediana 6.695 byte
e massimo 28.436 byte per vista. Include i lookup GAIA, non storici o combinazioni
arbitrarie. È una misura di accesso/dimensione, non 23.513 nuovi risultati numerici
indipendentemente certificati.

Un prototipo locale Chromium 149 ha verificato fetch, SHA256 e parsing JSON del
catalogo e del blocco di risposte più grande (359.759 byte non compressi). Dimostra
la fattibilità del caricamento selettivo di artefatti, non l'esecuzione del motore
nel browser o prestazioni su rete/mobile. Non va pubblicato l'intero insieme di
risposte come download obbligatorio. Per la prima modalità guidata è promettente
un caricamento per vista; servono ancora dimensionamento degli storici, manifest
di integrità/versione, copertura delle operazioni e test mobile prima del rollout.

| Esecuzione | Vantaggio | Prova ancora necessaria |
| --- | --- | --- |
| Artefatti deterministici suddivisi per vista/territorio | Pages, nessun invio delle domande | Byte complessivi anche degli storici; parità, copertura, aggiornamento e combinazioni non precompilate |
| Runtime nel browser | Selezioni dinamiche locali | Portabilità del motore e degli snapshot, parità numerica e dei rifiuti, memoria, caricamento e latenza mobile |
| Servizio autorizzato | Esecuzione centralizzata | Backend, costo, sicurezza, privacy e gestione operativa; fuori dall'attuale hosting statico |

La scelta guidata riguarda l'interazione; non elimina la decisione sull'esecuzione
deterministica. Non è ancora giustificato scegliere runtime browser o un servizio.
Prossimo passo: prototipo tecnico isolato di caricamento e parità su Pages,
misurando le due alternative statiche prima di estendere l'interfaccia. Un LLM
esterno cambierebbe il vincolo attuale di non invio a terzi e richiederebbe una
decisione esplicita; non è introdotto da questo incremento.

Restano da sviluppare: audit completo A3→A6→A7, aggregazioni ulteriori soltanto
riconciliate, CSV generale, spiegazioni/metadati, resolver Radar/Percorsi, piani
amministrativi e linguaggio libero. Nessun nuovo dato, UI, golden, acquisizione,
modello o infrastruttura esterna; nessuno step A7 dichiarato DONE.
