# A7 — anteprima degli incroci guidati

Secondo incremento A7.5.4, dopo il trasporto della #474. A6 resta DONE e A7
IN_PROGRESS. È una presentazione generica delle richieste native preparate in
un piano esplicito, nella stessa pagina dell’esploratore. Non è un repertorio
di domande curate, una ricerca automatica di correlazioni o il rollout pubblico.

## Scelte visibili

`build_a7_explorer_preview.py --associations` aggiunge una sezione con due
variabili, asse, metodo e motivo/copertura della richiesta. Le opzioni si
derivano dal piano ancorato; nomi e unità dal catalogo canonico e dalle risposte.
Viste, territori e periodi espliciti sono leggibili prima dell’esecuzione.
Non vengono aggiunti periodi, motivo, consenso o campi alla richiesta originale.
Il motivo è quello dichiarato dall’autore del piano: modificarlo richiederebbe
una richiesta diversa, che il trasporto della #474 non materializza implicitamente.
Le modalità «Una misura» e «Due variabili» occupano lo stesso spazio: il
modulo precedente conserva controlli e stato, senza due form simultanei.
Cambiare modalità revoca risultato e consenso pendente dell’incrocio.

La combinazione dei controlli seleziona una richiesta esatta. Il budget di
32 componenti non è una whitelist di domande di prodotto. Questa anteprima
non rende interrogabili altre combinazioni: non trasportato, rifiutato e dato
assente rimangono distinti. Il catalogo non viene duplicato in un inventario UI.
Per i controlli occorrono due selettori strutturati con ID metrica stringa;
i piani diagnostici senza questa struttura restano trasportabili dalla #474,
ma sono rifiutati esplicitamente da questa opzione di presentazione.

## Risultati e limiti

Coefficiente, metodo, n, coppie, periodi, fonti, esclusioni e sensibilità
leave-one-out provengono integralmente da A6. Il grafico proietta le coordinate
delle coppie originali: non calcola correlazioni, regressioni, stime o numeri
sostitutivi. Nessuna retta stimata, significatività, causalità, graduatoria
politica o raccomandazione. Le scale del grafico sono esplicite; zeri e negativi
non vengono eliminati. I punti sovrapposti rimangono distinti nella tabella.
Le etichette della scala sono arrotondate per la lettura; gli estremi riportati
nella didascalia, il coefficiente e le coppie conservano la precisione originale.
Il coefficiente usa la rappresentazione numerica originale senza tagliare le
cifre; la virgola è editoriale e l’eventuale notazione esponenziale resta tale.
Le tabelle lunghe sono paginate, senza tagliare il risultato originale.

Un rifiuto non produce coefficiente o grafico, anche quando conserva valori
numerici. La conferma sulla copertura incompleta permette di consultare il
rifiuto originale; non inserisce `allowPartial` e non promuove il risultato.
I limiti delle coppie stock/flusso sono visibili; gli altri avvertimenti e le
definizioni originali rimangono consultabili nei dettagli delle evidenze.
I sette Comuni non sono automaticamente un campione indipendente.

## Confine tecnico e pubblicazione

L’opzione è assente per default. Il materializzatore pubblico, l’interfaccia
v6 e i profili esistenti restano invariati. Soltanto l’anteprima opt-in usa
ricevuta v7 e i due asset aggiuntivi; `public=True, associations=True` è vietato
prima di creare output. Prima del rollout restano la misura e la revisione del
perimetro di richieste da preparare: nessuna espansione indiscriminata.

La sezione usa un proprio lettore dello stesso pacchetto immutabile ancorato.
Le due sezioni condividono la release, senza mescolare stato o cache. Il costo
iniziale aggiuntivo riguarda il manifest, non i blocchi delle risposte.
Nessun blocco numerico è scaricato prima della richiesta. Cache, hash, budget
e conferma restano quelli del lettore della #474. Errori di disponibilità o
integrità revocano il risultato; il tentativo successivo conserva la versione.
Cambiare un controllo revoca subito risultato e consenso pendente; un fetch
precedente non può ripristinare una selezione ormai superata.

```bash
python scripts/build_a7_query_runtime.py --catalog dist/data/site-data.json \
  --output-dir /tmp/a7-runtime --association-plan piano.json
python scripts/build_a7_explorer_preview.py --dist dist \
  --runtime /tmp/a7-runtime --output-dir /tmp/a7-anteprima --associations
```

La shell, i box e i menu bianchi sono quelli approvati. Nessun nuovo link di
navigazione, servizio, modello, backend o costo ricorrente. Radar e dossier
restano separati; nessuna acquisizione né modifica ad adapter/dati/golden.

## Verifiche

Il gate esistente di trasporto esegue anche la nuova interfaccia sulla shell
canonica della build: 1440/390/320 px, parità di tutte le risposte originali,
Pearson/Spearman, ordine invertito delle variabili, testo ostile trattato come
testo, rifiuti per scopo/periodi/metrica, rifiuto temporale indipendente già A6,
coppie incomplete, conferma, cache, blocco mancante, ripresa e fetch superato da
una nuova selezione. Nessun ampliamento dei budget: gli otto casi originali
del lettore restano separati dagli undici casi della UI. Sono prove di accesso
e presentazione, non nuovi casi numerici indipendenti.
Le attese usano selettori nativi compatibili con la CSP canonica, senza
`unsafe-eval`. Coefficiente su una riga ed etichette del grafico non tagliate
sono verificati anche nella pagina completa a 320 px; lo stile della nuova
sezione evita il padding annidato delle sezioni editoriali esistenti.

La prova preliminare su fixture del componente non certifica la shell pubblica.
Preview reale, browser, Quick e Full locali ordinari, CI Quick→Full effettivo e
A3 restano obbligatori sul nuovo candidato. Nessun verde #474 trasferito.
