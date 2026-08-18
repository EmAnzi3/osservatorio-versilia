# Aggiornamento mensile dei dati

## Obiettivo

Il controllo viene eseguito una volta al mese e può essere avviato anche manualmente. La procedura è prudenziale: verifica dati e fonti, ma non pubblica valori senza controllo umano.

Il sistema distingue tre livelli che non devono essere confusi:

1. `data/site-data.json` descrive **cosa è pubblicato**: periodo, valori, fonte e metodo;
2. `data/source-registry.json` descrive **come si comporta la fonte**: produttore, frequenza, cadenza indicativa, acquisizione e licenza;
3. `data/source-monitor-state.json` registra **cosa è stato realmente controllato**: data del controllo, raggiungibilità e stato operativo per indicatore.

La pagina pubblica `/stato-dati/` è una vista derivata da questi tre livelli e non costituisce un quarto registro manuale.

## Calendario

Il workflow `Controllo mensile dati` è programmato per il giorno 5 di ogni mese alle 05:17 UTC. L'orario non tondo riduce la probabilità di attese nelle code dei runner GitHub.

Durante la revisione di una pull request il controllo viene eseguito in modalità offline: verifica integralmente struttura, copertura e coerenza del dataset senza contattare le fonti e senza generare notifiche.

## Cosa controlla

- presenza dei **127 indicatori** nel catalogo canonico e ripartizione attesa fra **123 valori incorporati e 4 climatici esterni**;
- copertura dichiarata dei sette Comuni e codici Istat corretti;
- presenza di anno o periodo, unità, fonte, metodo e formula;
- coerenza fra annualità e valori delle serie storiche;
- presenza, per ogni indicatore, di produttore, frequenza, cadenza indicativa, modalità di acquisizione e licenza;
- raggiungibilità delle fonti ufficiali;
- modifica dei file ufficiali direttamente scaricabili;
- cambiamenti di URL, reindirizzamenti ed eventuali segnali HTTP;
- stato operativo per indicatore, senza dedurre automaticamente l'attualità del dato dalla sola raggiungibilità della fonte.

Per `pnrrFunding` e `pnrrConcluded`, nelle esecuzioni live il monitor usa inoltre il dataset ufficiale **Regione Toscana — Open Data PNRR** come fonte machine-readable di verifica. Il perimetro comprende i progetti con `area = PNRR` o `PNRR-PNC`, esclude i PNC puri, richiede che uno dei sette Comuni sia `soggetto_attuatore`, deduplica su `id_progetto`, legge le risorse da `importo_finanziato_pnrr` e considera concluso un progetto quando `fase_avanzamento_da_regis = 5. conclusione`. Il feed regionale integra ReGiS e altre fonti amministrative ufficiali; nessun suo cambiamento autorizza la pubblicazione automatica.

## Cosa non fa

- non stima dati mancanti;
- non interpola annualità;
- non sostituisce valori pubblicati;
- non considera una pagina modificata come prova automatica di un nuovo rilascio;
- non considera una fonte raggiungibile come prova automatica che il periodo pubblicato sia l'ultimo disponibile;
- non effettua merge;
- non pubblica direttamente su GitHub Pages.

Per il clima resta una regola ulteriore: **nessun valore YTD viene pubblicato; entrano nel catalogo soltanto anni completi**.

## Stati dei dati

Gli stati pubblici descrivono l'attualità del singolo indicatore, non l'esito tecnico dell'intera esecuzione.

- `current` — **Ultimo dato disponibile**: il periodo pubblicato coincide con l'ultimo periodo effettivamente verificato sulla fonte;
- `source_checked` — **Fonte controllata**: la fonte è raggiungibile, ma il monitor non può certificare automaticamente quale sia l'ultimo periodo disponibile;
- `source_access_limited` — **Controllo automatico limitato**: il portale ufficiale respinge o limita le richieste automatizzate; non viene considerato né fonte guasta né dato aggiornato e resta necessaria la verifica manuale;
- `release_detected` — **Nuovo rilascio da verificare**: è stato verificato o registrato un periodo più recente di quello pubblicato; serve validazione prima di modificare i valori;
- `update_expected` — **Aggiornamento atteso**: è arrivata una finestra di rilascio documentata, senza conferma di un nuovo dato;
- `source_unavailable` — **Fonte temporaneamente non verificabile**: il controllo fallisce per indisponibilità reale, errore di rete/TLS non recuperabile o risposta del servizio che non rientra tra le limitazioni note dell'automazione;
- `verification_required` — **Verifica necessaria** per un cambiamento tecnico o una situazione ambigua.

Una fonte raggiungibile senza un periodo osservato viene quindi classificata `source_checked`, non `current`. Una nuova URL che entra nella baseline del monitor non diventa automaticamente `verification_required`: servono un cambiamento sostanziale di una fonte già monitorata o un'altra ambiguità effettiva.

Per alcuni portali istituzionali il monitor può usare, esclusivamente per verificare la raggiungibilità, un endpoint alternativo ufficiale dello stesso servizio o un client HTTP compatibile. L'URL pubblicato dell'indicatore non viene sostituito e il fallback non costituisce prova di un nuovo rilascio. Se anche gli endpoint ufficiali respingono sistematicamente i client automatici con risposte quali 401, 403 o 429, la fonte viene classificata `source_access_limited` invece di essere dichiarata indisponibile.

## Prossimo rilascio

La frequenza della fonte non genera automaticamente una data futura.

Una data o un mese di prossimo rilascio può essere mostrato soltanto quando esiste una base esplicita, ad esempio:

- calendario ufficiale;
- programma ufficiale di pubblicazione;
- finestra di rilascio documentata;
- periodicità storica verificata e registrata come tale.

Se sappiamo soltanto che la fonte è annuale, il sito mostra **Frequenza: annuale** e, quando utile, una **cadenza indicativa**. Non trasforma questa informazione in una falsa data di pubblicazione.

## Notifiche e registrazione

Per ogni esecuzione programmata o manuale il workflow:

1. crea, se necessario, l'issue `Registro controlli dati <anno>`;
2. aggiunge un commento con il rapporto mensile;
3. menziona `@EmAnzi3`, generando una notifica GitHub;
4. conserva il rapporto completo come artifact per 90 giorni;
5. per ogni controllo live riuscito apre o aggiorna una **PR in bozza** contenente i metadata di controllo aggiornati, anche quando non sono emerse variazioni sostanziali.

Questo quinto passaggio serve a evitare che il sito dichiari una vecchia data di controllo soltanto perché la fonte non è cambiata. Il merge resta comunque manuale.

## Esiti del workflow

Gli esiti tecnici dell'esecuzione restano distinti dagli stati dei singoli indicatori:

- `no_changes`: nessuna variazione sostanziale della fonte;
- `baseline_required`: prima fotografia delle fonti;
- `changes_detected`: una fonte è stata aggiunta, rimossa, reindirizzata o un file ufficiale è cambiato;
- `attention_required`: il dataset non supera i controlli strutturali; workflow fallito e pubblicazione impedita.

Le fonti realmente non raggiungibili sono segnalate senza cancellare dati esistenti. Le limitazioni note e riproducibili dei portali verso i client automatici vengono invece registrate separatamente come `source_access_limited`.

## Politica delle fonti

Il file `data/source-registry.json` associa ciascun URL primario a un profilo esplicito. Il profilo dichiara produttore, cadenza attesa, modalità di acquisizione e condizioni di riuso. Le eccezioni riferite a un singolo indicatore prevalgono sul profilo generale della fonte.

La frequenza indica quando è ragionevole controllare un aggiornamento; non è una promessa di disponibilità del dato e non autorizza a sostituire automaticamente un valore già pubblicato.

## Flusso di pubblicazione

Il flusso resta sempre:

**fonte → controllo → rilevazione → validazione → pubblicazione**

Quando il controllo rileva una variazione, la PR automatica è soltanto un avviso documentato. L'aggiornamento dei valori deve:

1. acquisire il nuovo dato dalla fonte originale;
2. verificare quale periodo sia realmente disponibile;
3. conservare lo snapshot leggibile;
4. aggiornare anno o periodo, valori, serie, formula e fonte in modo coerente;
5. superare build e test;
6. essere verificato manualmente prima del merge.

## Esecuzione manuale

Aprire:

`Actions → Controllo mensile dati → Run workflow`

Lasciare attivo `Controlla anche le fonti online` per un controllo reale. Disattivarlo soltanto per verificare struttura e copertura senza traffico verso le fonti.
