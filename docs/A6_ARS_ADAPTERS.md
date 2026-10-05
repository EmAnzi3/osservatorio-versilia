# A6 — adapter ARS sui dati acquisiti

Lotto successivo alla #337 pubblicata (`bdd88c98`). Il motore v5 aggiunge 18 indicatori ARS al catalogo effettivo: 29 indicatori con adapter su 225. Le esclusioni e le dimensioni non supportate restano derivate nel report di copertura; nessun nuovo dato viene acquisito o pubblicato e nessun renderer viene modificato.

## Misure e dimensioni

Le definizioni ammesse sono scoperte dai tre snapshot ARS già governati, non da un nuovo inventario di indicatori. Il catalogo effettivo deve esporre il carrier demografico con identificativo, periodo, unità e regola di misura corrispondenti. Le letture correnti di cronicità totale e ricoveri usano invece la serie totale riconciliata allo snapshot legacy.

- Speranza di vita: campo `raw` dell'export, in anni; `standardized=0` e componenti `0/0` sono strutturali. Non sono tassi grezzi di eventi, pesi o zero osservati.
- Altri totali e dettagli per sesso: misura standardizzata per età della fonte. Numeratore/denominatore grezzi restano contesto nella provenienza e non diventano componenti aggregabili.
- Fasce MaCro 16–44, 45–64, 65–84, 85+: misura grezza specifica della fascia, per sesso. Il campo standardizzato e gli IC 0–0 strutturali non sostituiscono il valore osservato e non costituiscono intervalli di confidenza.
- La dimensione `total` indica tutte le età e sesso totale; `sex:men`/`sex:women` indicano tutte le età del sesso selezionato. Le fasce richiedono `age:65-84|total` o, ad esempio, `age:65-84|sex:women`. Non si confrontano implicitamente popolazioni o misure differenti.

Confronto, rango e screening IQR restano descrittivi. Il significato sanitario non è un giudizio di qualità, una causa o una priorità politica. Gli algoritmi amministrativi di riconoscimento delle patologie non misurano automaticamente tutto il bisogno della popolazione.

## Periodi, precisione e storici

Gli anni e le finestre vengono normalizzati solo nel separatore (`2013–2022` → `2013-2022`). Il periodo completo rimane parte dell'identità; `2022` non seleziona la mortalità `2013-2022`. Le finestre devono mantenere la stessa ampiezza. L'ordine usa inizio/fine dichiarati, senza trasformare le finestre in osservazioni annuali.

Gli storici totali sono riconciliati ai record congelati. Per la speranza di vita sono disponibili anche gli storici per sesso; per gli altri indicatori le dimensioni sesso/fascia restano correnti. Lo storico totale non viene sostituito a uno storico demografico assente. `elderlyHomeCare` conserva l'adapter già pubblicato e la sua limitazione corrente: il suo storico non è esteso in questo lotto.

Le variazioni tra due finestre sono differenze descrittive dei tassi riferiti alle intere finestre. Serie e variazioni dichiarano la sovrapposizione; trend annuale e correlazione lungo finestre sovrapposte sono rifiutati. La correlazione comunale può usare due variabili riferite alla stessa finestra completa, con scopo esplicito, appaiamento, piccolo campione e avvertenze già governate. Nessuna inferenza causale o significatività automatica.

La lettura corrente seleziona i valori precisi dei `parts` quando disponibili. Gli storici mantengono la precisione realmente pubblicata: due decimali nelle serie v1.40 e della speranza di vita, valori precisi nelle serie legacy. Non si aggiungono decimali alle serie arrotondate. La riconciliazione è esatta per i carrier precisi, entro 0,0051 per gli storici arrotondati e 0,055 per i totali legacy già pubblicati con precisione ridotta; la tolleranza riguarda la verifica, non un'imputazione o una modifica dei valori.

## Benchmark e provenienza

Toscana e Zona Versilia sono record ufficiali per il medesimo sesso/fascia, misura e periodo. L'adapter riconcilia anche i rispettivi carrier pubblicati. La Zona Versilia non è una media dei tassi comunali. Italia e benchmark storici assenti sono rifiutati.

**Residuo concreto:** per `chronicTotal` e `hospitalizedAll` il lotto abilita soltanto il riferimento Zona Versilia, presente nello snapshot legacy. I benchmark Toscana esistenti restano pubblicati nel catalogo e nel sito, ma non sono interrogati da questo adapter perché il record regionale non è conservato nello snapshot letto. Non vengono cancellati o riclassificati nell'audit A3.

Ogni osservazione conserva pointer del valore e del periodo nel catalogo, SHA-256 del catalogo e dello snapshot, pointer del record sorgente, URL export, SHA dichiarato del CSV, misura e contesto. Il risultato contiene anche l'hash del modulo adapter ARS. Uno snapshot non prova la disponibilità live. Nessun download live è effettuato dal motore.

Null resta mancante: il valore del carrier non viene riempito dal record sorgente. Esclusioni richiedono `allowPartial=true` e restano nel risultato. Nessuna somma, media ponderata o derivazione di pesi è abilitata per questi indicatori.

## Verifiche e riproduzione

Il gate post-build generale verifica ogni dimensione recensita su tutti i sette Comuni, i riferimenti correnti, le serie ammesse, i rifiuti, record duplicati e carrier alterati. I casi numerici di accettazione sono trascritti separatamente in `ci/semantic-verified-questions.json`: 35 domande, 23 calcoli e 12 rifiuti attesi. Non sono aspettative rigenerate dalla risposta del motore.

```bash
python scripts/test_semantic_ars_adapters.py
python scripts/semantic_engine_audit.py --catalog dist/data/site-data.json --output-dir /tmp/a6-audit
python scripts/semantic_question_suite.py --catalog dist/data/site-data.json --output-dir /tmp/a6-questions
python scripts/semantic_engine_benchmark.py --catalog dist/data/site-data.json --rounds 50 --output-dir /tmp/a6-performance
```

La baseline #337 resta in `reports/a6-engine-audit/performance.*`; la nuova misura è in `reports/a6-ars/performance.*`, con sette carichi (i cinque precedenti e due ARS). Ambiente, hash e campioni vanno letti prima di confrontare i tempi. Non è un test concorrente o una promessa di capacità produttiva. Quick/Full locali e GitHub sono richiesti prima della dichiarazione di prontezza al merge; nessun workflow aggiunto.
