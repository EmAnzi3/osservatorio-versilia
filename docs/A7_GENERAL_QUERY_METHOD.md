# A7 — metodo generale di esplorazione e analisi

## Obiettivo e perimetro

L'unità di sviluppo è una capacità riutilizzabile, non una risposta a una domanda
scritta in anticipo. I trenta quesiti proposti dal proprietario il 18 ottobre
sono esempi di accettazione, non un repertorio chiuso o una nuova fonte di dati.
Il criterio di generalità è poter cambiare tema, indicatore, dimensione, Comune,
periodo e operazione senza scrivere una risposta dedicata, nei limiti reali A6.

Un solo percorso collega esplorazione, incroci, dossier e approfondimento delle
scelte pubbliche: domanda → selezione esplicita → piano di evidenze → verifica
deterministica → lettura → opzioni da approfondire → monitoraggio. Ogni passaggio
aggiunge responsabilità verificabili; un calcolo riuscito non autorizza quelli
successivi. A6 resta DONE; A7 IN_PROGRESS.

## Fondazione implementata in questo incremento

`scripts/a7_query_workbench.py` usa il motore Python originale e il catalogo
effettivo prodotto dalla catena di build. Non modifica adapter o policy.

- `discover()` deriva tutti gli ID e i temi dal catalogo canonico; restituisce
  etichetta, numero di dimensioni e stato dichiarato, senza secondo inventario.
- `discover(metric)` restituisce la dichiarazione A6 completa: dimensioni,
  operazioni per dimensione, contesti e benchmark. La dichiarazione segnala
  possibilità condizionate, non garantisce che una selezione sia calcolabile.
- `run(plan)` esegue richieste strutturate indipendenti. Ogni risposta A6 rimane
  integra, comprese fonti, periodi, componenti, hash, esclusioni, motivi e campi
  opzionali assenti nei rifiuti precoci. Non inserisce consenso alla copertura
  parziale, non sostituisce periodi e non somma risultati di passi diversi.
- Il piano e la sua impronta accompagnano gli output. Gli stati
  `computed_components`, `mixed_components`, `refused_components` descrivono
  soltanto le componenti: `interpretationStatus=not_assessed` impedisce di
  scambiarli per risposta completa a una domanda amministrativa.
- Limiti di lavoro locali: massimo 32 componenti e 100.000 byte per piano.
  Piani più grandi richiedono suddivisione esplicita; nessun troncamento.

Non è ancora un'interfaccia pubblica, un interprete di domande libere, un servizio
HTTP, una nuova piattaforma o un generatore di dossier/PDF. La CLI è uno strumento
di verifica per sviluppatori. JSON interno non sostituisce il rapporto pubblico.
Le domande non vengono inviate a terzi.

## Contratto di piano

```json
{
  "schemaVersion": 1,
  "steps": [
    {
      "id": "evidenza",
      "request": {
        "operation": "compare",
        "selectors": [{"metric": "population", "towns": ["046018", "046033"]}]
      }
    }
  ]
}
```

L'esempio illustra il formato, non introduce un insieme privilegiato di metriche.
Solo `request` entra in `QueryEngine.query()`. A6 rimane il validatore delle sue
richieste; l'involucro verifica soltanto struttura e limiti del piano. Non
presupporre che questo strumento locale sia già sicuro come endpoint pubblico:
prima di un endpoint servono test e limiti anche su tipi annidati, costo dei
selettori, concorrenza, tempo, memoria e dimensione delle risposte. Errori inattesi
del motore non vengono trasformati in rifiuti metodologici riusciti.

```bash
python scripts/a7_query_workbench.py --catalog dist/data/site-data.json --discover
python scripts/a7_query_workbench.py --catalog dist/data/site-data.json --discover --metric population
python scripts/a7_query_workbench.py --catalog dist/data/site-data.json --plan piano.json --output evidenze.json
python scripts/test_a7_query_workbench.py --catalog dist/data/site-data.json
```

Il catalogo deve provenire dalla build candidata, non da un file copiato da una
release precedente. Il test è incluso nei check sul catalogo effettivo del
preflight e nel manifest di compilazione.

## Accesso generale ai dati

L'obiettivo riguarda tutto il patrimonio acquisito. La copertura degli indicatori
non prova l'accessibilità di ogni campo degli snapshot: A3 distingue dimensioni
acquisite e acquisibili; A6 dichiara quelle interrogabili; A7 deve renderle
raggiungibili. Un campo già congelato ma non modellato è una lacuna di accesso o
di semantica, non una fonte indisponibile. Nessuna nuova acquisizione automatica.

Le dimensioni dichiarate non sono sempre assi liberamente combinabili: per esempio
una vista può incorporare categoria, universo e misura. I controlli devono
selezionare le viste effettivamente dichiarate, senza fabbricare prodotti
cartesiani età×sesso×settore o traduzioni fra classificazioni.

L'esplorazione pubblica successiva dovrà derivare da queste capacità, senza un
elenco manuale di domande autorizzate: tema/indicatore, dimensione, territorio,
tempo, operazione e approfondimento. Etichette tecniche richiedono una resa
comprensibile ma non possono alterare definizioni e codici.

## Territori e tempo

Versilia è un perimetro da verificare, non l'ottavo Comune del selettore A6.
Una selezione dei sette Comuni restituisce sette osservazioni, non un totale.
Usare soltanto aggregazioni già autorizzate: un rapporto ponderato A6 dove
previsto oppure un aggregato nativo disponibile. Per quantità additive senza
operazione autorizzata documentare la capacità mancante; nessun `sum()` generico,
media semplice di tassi, sovrapposizione gerarchica o retrocalcolo da percentuali.
I benchmark nativi, gli aggregati ricostruiti e la media dei Comuni restano distinti.

"Oggi" significa ultimo dato disponibile con data di riferimento esplicita; non
anno del calendario. "Ultimi anni" e categorie comuni ma ambigue richiedono
chiarimento o una proposta esplicita da accettare. Per clima, scuola, bilanci e
fotografie amministrative valgono periodi e discontinuità propri.

## Incroci: quattro livelli distinti

1. **Giustapposizione:** un piano conserva evidenze di più fenomeni. Non attesta
   confrontabilità né dimostra una relazione fra loro.
2. **Calcolo derivato:** solo operazioni autorizzate con componenti e denominatori
   coerenti. Nessun rapporto fra numeri perché tecnicamente divisibili.
3. **Associazione:** una richiesta A6 `correlation` contiene due selettori,
   metodo, asse e scopo. Conservare n effettivo, allineamento, esclusioni,
   denominatori condivisi, outlier e avvertenze. Nessuna ricerca indiscriminata
   delle correlazioni più elevate; sette Comuni non dimostrano effetti individuali.
4. **Effetto di politica:** richiede un disegno di valutazione e dati ulteriori
   pertinenti. Prima/dopo e correlazione non identificano effetti causali.

Il workbench implementa la raccolta del primo livello e delega i calcoli e le
associazioni consentiti ad A6; non introduce un motore di inferenza fra passi.

## Dossier, letture e programmi amministrativi

Il dossier organizza un problema e riferisce piani di evidenze, senza conservare
una seconda copia canonica dei numeri. La futura presentazione web/PDF deve
associare ogni affermazione quantitativa al risultato o all'osservazione A6 che
la sostiene, con periodo, universo, fonte e copertura. I percorsi lavoro e scuola
esistenti restano conservati; la #443 è una composizione editoriale distinta,
non condizione per la generalità del workbench.

Una posizione numerica o una variazione non diventano automaticamente criticità.
Il contesto deve esplicitare polarità dove significativa, dimensione, confronto,
continuità, popolazione interessata e dati mancanti. Nessun punteggio politico
complessivo o graduatoria automatica di amministrazioni.

Per arrivare a spunti amministrativi occorre una scheda di argomentazione:
problema/ipotesi; evidenze favorevoli e contrarie; limiti; soggetti interessati;
competenze degli enti con fonti documentali; opzioni alternative da approfondire;
vincoli e costi conosciuti o mancanti; indicatori di attuazione e risultato.
La scheda non è implementata da questo incremento. Competenze, fattibilità e
efficacia non possono essere dedotte dai soli indicatori; le priorità rimangono
scelte politiche e pubbliche.

Radar e Percorsi richiedono resolver specifici: bandi per destinatario, settore,
scadenza e controllo corrente; percorsi come orientamento editoriale. Non sono
trasformati in metriche A6. PNRR distingue finanziamento, attuazione, pagamenti
e risultati: le dimensioni non acquisite non diventano risposte automatiche.

## Prove e passi successivi

La suite verifica tutte le aspettative indipendenti A6 già versionate attraverso
l'involucro, confronta le dichiarazioni di ogni indicatore e genera nuove
selezioni territoriali dai dati, senza repertorio di risposte. Include rifiuti,
copertura, mutazioni, riproducibilità, isolamento dei risultati e piani misti.
Sono verifiche delle capacità strutturate, non un audit di ogni combinazione
possibile, della comprensione linguistica o della qualità delle proposte.

Prima lacuna verificata: `compare` di `population` con un solo Comune è rifiutato
con `insufficient_observations`. Una dichiarazione `compare` non promette quindi
una query puntuale. Una futura lettura puntuale deve riferire un'osservazione di
una risposta A6 calcolabile, dichiarandone la selezione, oppure richiede una
capacità esplicita nuova. Non viene rimossa la guardia A6 per rendere verde A7.

Prima di estendere l'interfaccia:

1. misurare quali dimensioni A3 acquisite sono esposte A6 e quali raggiungibili
   A7, derivando il confronto dai contratti esistenti;
2. rendere espliciti periodi selezionabili e disponibilità territoriale per vista,
   senza dedurli dalle etichette del carrier o promettere benchmark non compatibili;
3. verificare strategie di esecuzione su Pages (artefatti per osservazioni e
   composizioni limitate, runtime browser o servizio autorizzato), misurando
   copertura, parità A6, byte, memoria e tempi: nessuna scelta già dimostrata;
4. integrare esplorazione e piani nelle letture, poi citazioni/export CSV e PDF;
5. aggiungere risoluzione delle ambiguità e interpretazione linguistica soltanto
   sopra le richieste validate; mantenere chiarimento, parzialità e impossibilità;
6. verificare dossier e schede amministrative come argomentazioni documentate.

Nessun punto A7 è dichiarato DONE, nessuna nuova UI o infrastruttura è introdotta.
