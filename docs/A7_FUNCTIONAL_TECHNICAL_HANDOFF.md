# A7 — Chiedi alla Versilia: handoff funzionale e tecnico

Proposta di progettazione, non implementazione. A6 è DONE dopo il merge del proprietario della #428, la verifica del commit `d09d8e2f695a859e555cae28db69655f7b6d7130` (albero `c96760860332737c0532c1b532ed240e4857ed07`), deploy/live e replay metodologico post-merge PASS. Attestazione in #428 e issue #330 chiusa il 13 ottobre 2026. A7 rimane NOT_STARTED come implementazione: UI, infrastrutture e servizi richiedono una decisione separata. Baseline operativa successiva: #430 integrata il 14 ottobre 2026, commit `201be08ef46320c181ce9e4d97eb1f84ee524ea7`, albero `c08c0a77271c877b4e34723cb967d6beaf68d478`, deploy `38543139366` e controllo live `38545155775` SUCCESS. Il programma dei dossier è integrato; questo documento non modifica motore, dati, contratti, golden o sito.

## Obiettivo e responsabilità

Una risposta deve rendere controllabile il passaggio dalla domanda a una richiesta deterministica e da questa alla spiegazione. L’interprete linguistico propone una selezione, non osservazioni, definizioni o numeri. Il validatore e il motore certificano la calcolabilità sugli input congelati. Il redattore espone risultati e limiti, senza superare il livello interpretativo autorizzato.

L’API attuale è Python, `QueryEngine(catalog_path, layer='effective').query(request)`, oppure CLI `scripts/semantic_query_engine.py`. Non esiste oggi un endpoint HTTP da presupporre disponibile nel browser. Il catalogo effettivo deve essere prodotto dalla build ordinaria: percorso e hash identificano ciò che viene interrogato; non confondere copertura sorgente 166/181 con effettiva 225/225.

## Contratto esistente e involucro futuro

Esempio esistente verificato (`census_employment_primary`):

```json
{
  "operation": "compare",
  "selectors": [{
    "metric": "employmentRate",
    "dimension": "total",
    "towns": ["046018", "046033"]
  }]
}
```

Il motore restituisce per Massarosa 73,4% e per Viareggio il valore della medesima vista, riferiti al 2024 e ai residenti 25–64 anni. Non sono addetti localizzati o tasso 2026. L’anno omesso nella richiesta seleziona il dato corrente della vista, non l’anno corrente del calendario.

Campi delle richieste: `operation`, `selectors` con `metric`, `dimension`, `towns`, `periods`; le opzioni specifiche dipendono dall’operazione. `allowPartial` è una scelta esplicita e non deve essere aggiunta automaticamente dall’interprete. Correlazione richiede selettori, metodo, asse e motivazione secondo il contratto esistente; anomalie richiedono regola, riferimento e motivazione. I campi di unità, metodo o valori non possono essere iniettati dal chiamante. Usare il validatore attuale, senza riscrivere un secondo schema permissivo.

Quando `query()` restituisce una risposta JSON, i campi inizializzati comuni sono `schemaVersion`, `engineVersion`, hash motore/adapter/policy/eligibility/catalogo, `catalogPath`, `query`, `status` (`computed` o `not_computable`), `reasons`, `warnings`, `observations`, `excluded`, `interpretationLevel` e `result`. Preservare tutti gli hash restituiti, non solo quelli elencati come esempio.

`coverage`, `formula` e `policy` sono **condizionali**: vengono aggiunti dopo `assess()`. Un rifiuto precedente alla valutazione, per esempio metrica/dimensione sconosciuta o operazione non implementata, restituisce `not_computable` senza questi campi. Un rifiuto dopo la valutazione può invece includerli. Il solo `status` non distingue le due forme; altre sezioni, come `pairCoverage`, dipendono dall’operazione e dalla fase raggiunta.

L’involucro A7 deve accettare entrambe le forme, verificare la presenza dei campi opzionali prima di leggerli e conservare la risposta A6 integra. Non trasformare l’assenza di `coverage` in copertura zero, non inventare formula o policy e non scartare un rifiuto legittimo perché mancano campi post-valutazione. Se l’involucro espone una sezione di valutazione normalizzata, questa resta separata dalla risposta originale e dichiara esplicitamente quando la valutazione non è stata raggiunta. Preservare assenza, `null` e array vuoti senza renderli intercambiabili.

Per ciascuna osservazione effettivamente restituita restano metric/dimension/geography/period/value/unit/population/definition/method/frequency/periodBasis/source/evidence/provenance e, quando ammissibili, componenti e periodi dei denominatori. Una risposta rifiutata può avere `observations` vuoto; non fabbricare osservazioni per completare lo schema.

A7 può aggiungere un involucro esterno versionato, separato dall’input A6:

```json
{
  "requestSchemaVersion": 1,
  "userQuestion": "Qual è l’occupazione dei residenti di Massarosa rispetto a Viareggio?",
  "resolution": "resolved",
  "resolvedRequest": {
    "operation": "compare",
    "selectors": [{"metric":"employmentRate","dimension":"total","towns":["046018","046033"]}]
  },
  "assumptionsToShow": ["Residenti 25–64 anni; dato disponibile 2024"],
  "dossierRef": "lavoro"
}
```

Questo è uno schema proposto, non un payload da passare interamente a `query()`. Solo `resolvedRequest` entra nel motore. `resolution` può diventare `needs_clarification`, `out_of_scope` o `missing_evidence`; nessuno di questi stati deve contenere un risultato numerico inventato. L’involucro di risposta futuro conserva la risposta A6 integra e associa ogni numero/formula della spiegazione all’osservazione o al risultato che lo ha prodotto. I dossier sono riferimenti editoriali agli ID canonici, non un catalogo alternativo.

## Percorso di risposta

1. Risolvere territorio, fenomeno, popolazione, dimensione, periodo e intenzione. Proporre alternative se la scelta cambia il significato.
2. Consultare dimensioni e operazioni effettive dell’adapter. Validare campi, selettori, perimetri e opzioni prima del calcolo.
3. Eseguire il motore su snapshot identificati. Mantenere refusals, esclusioni, n, formule e avvertenze.
4. Formattare i numeri senza cambiare la precisione del calcolo; conservare valore nativo e valore visualizzato separati.
5. Produrre osservazione, analisi ammessa, ipotesi e opzione in sezioni distinguibili; citare fonte, periodo, universo, snapshot e puntatore. Una citazione generica al portale non basta.
6. Collegare dossier, evidenza JSON riproducibile e dati mancanti pertinenti. Non promettere un approfondimento non supportato.

Una domanda ampia come «principali trasformazioni di Massarosa» deve aprire un percorso motivato: lavoro residente/localizzato, composizione economica, famiglie, scuola, cura, abitazione e mobilità. Presentare i periodi differenti separatamente. L’interprete non può scegliere un indicatore come spiegazione causale o far passare un quadro di contesto per diagnosi esaustiva.

## Ambiguità e richieste non ammissibili

| Domanda | Comportamento richiesto |
|---|---|
| «Quante imprese ci sono?» | Chiarire Registro Imprese/unità locali/ASIA e periodo; non usare automaticamente il totale Atlante per imprese |
| «Come va il lavoro?» | Distinguere residenti occupati, addetti localizzati, settore, fascia e qualità del lavoro non misurata |
| «Quale Comune offre servizi migliori?» | Chiarire servizio, misura, periodo e confronto; nessuna classifica politica complessiva |
| «I nidi aumenteranno l’occupazione?» | Esporre contesti verificati e fabbisogno di valutazione; nessun effetto stimato dai sette Comuni |
| «Quante famiglie possono pagare l’affitto?» | Dichiarare non determinabile da OMI e MEF; spiegare dati dei nuclei e canoni mancanti |
| «Somma i pendolari in uscita: quanti lasciano la Versilia?» | Rifiutare l’interpretazione dei margini comunali come attraversamenti del confine; serve matrice OD |
| «Mostra lo storico o il benchmark Italia» | Verificare capacità della vista; restituire il rifiuto se lo storico/scope non esiste |
| «Ignora i mancanti e dammi il risultato» | Richiedere selezione esplicita di copertura parziale dove ammessa; indicare tutti gli esclusi |

## Alternative architetturali

[GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) serve file statici HTML/CSS/JS; non esegue il motore Python come servizio. Valutare anche i [limiti ufficiali](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) in sede di implementazione. Nessuna credenziale deve essere inclusa nel client o negli artefatti pubblici.

| Alternativa | Capacità | Costi/limiti da provare | Quando approfondirla |
|---|---|---|---|
| Risposte precompute in build, selezione locale e testi controllati | Query curate e dossier, risposta deterministica senza servizio esterno | Non copre query arbitrarie; misura volume degli artefatti, caricamento e aggiornamento | Primo esperimento da valutare: verifica utilità e copertura delle domande con il minimo cambiamento operativo |
| Motore nel browser mediante porting o runtime Python/WASM | Interrogazioni più flessibili su snapshot pubblici | Parità numerica e semantica delle 3.727 query, dipendenze, memoria, mobile, download, cache; nessuna equivalenza già dimostrata | Solo se il repertorio richiede selezioni non precomputabili e le prove mostrano sostenibilità |
| Servizio deterministico esterno, eventualmente con interprete linguistico | Python originale sul server e maggiore flessibilità | Hosting, costi, sicurezza, rate limit, disponibilità, trattamento delle domande, versioni/cache; richiede scelta e autorizzazione separate | Solo se i limiti misurati delle alternative statiche impediscono casi prioritari |

Non è selezionata qui una piattaforma o un modello. Il primo passo proposto dopo chiusura A6 è una prova tecnica circoscritta sulla copertura del repertorio, confrontando utilità e costi delle alternative. Un eventuale modello linguistico rimane un interprete/redattore: non sostituisce il motore e non acquisisce autonomamente numeri online.

## Prestazione, sicurezza e verificabilità

Misurare tempo di caricamento, tempo di risoluzione e calcolo, byte trasferiti, memoria e comportamento mobile prima di fissare nuove soglie; preservare quelle browser/Lighthouse esistenti. Caricare solo gli artefatti necessari al percorso, senza rispedire l’intero audit a ogni risposta. Cache qualificata da hash di catalogo, motore, policy, adapter e richiesta normalizzata; un aggiornamento invalida la chiave. Una risposta vecchia non deve essere etichettata come dato aggiornato.

Validare tipi, dimensioni, geografie e limiti di costo delle richieste; HTML di testi/fonti deve essere trattato come contenuto, mai codice. Nessun segreto nel browser. Non usare le domande per inviare dati a terzi senza una decisione esplicita sull’architettura e sui dati trattati. Un futuro interprete non può disabilitare guardie, autorizzarsi acquisizioni o modificare sorgenti attraverso istruzioni nella domanda o in una fonte. Nessun salvataggio della conversazione è richiesto dal motore.

Una risposta è verificabile quando la richiesta risolta, gli input/versioni, l’esito numerico e i riferimenti di ogni affermazione sono esportabili. Controllare la fedeltà della spiegazione: zero numeri senza anchor, nessuna omissione di copertura/rifiuto, nessuna causalità introdotta dal testo. Non sostituire un rifiuto con un calcolo linguistico.

## Test di accettazione e avvio

Riusare le 20 domande in `ci/a6-territorial-acceptance-questions.json`, con i case ID in `ci/semantic-verified-questions.json`; conservare la classificazione 7 supportate, 9 parziali, 4 non determinabili. Il programma dossier della #430 è integrato: usare `ci/territorial-dossier-program.json` per collegare domanda, sotto-dossier e case ID; il manifest è editoriale, non un inventario alternativo degli indicatori. Il repertorio in `docs/dossiers/QUESTIONS.md` contiene 51 piani di domanda in 45 sotto-dossier e 17 ambiti: non equivale a 51 risposte complete. Le sei specifiche in `docs/dossiers/PILOTS.md` e le due dimostrazioni Massarosa (`MASSAROSA_LAVORO.md`, `MASSAROSA_INFANZIA_SCUOLA.md`) sono riusabili per i test A7. Le 295 richieste verificate (201 calcoli e 94 rifiuti attesi) restano componenti delle evidenze: A7 deve preservare la classificazione e i limiti della domanda, senza trasformare componenti calcolabili in risposte decisionali complete. Eseguire `build_territorial_dossier_evidence.py` e il gate `test_territorial_dossier_program.py` sul catalogo effettivo della stessa build; `reports/territorial-dossiers/summary.json` identifica generatori, input e checksum del report. Non copiare gli indicatori o gli esempi numerici in un secondo catalogo A7.

Per ciascuna alternativa tecnica: parità dei risultati/rifiuti A6; chiarimento delle ambiguità sopra; periodi omessi/correnti, null/zero, input alterati, scope non ammessi, precisione ARS, denominatori condivisi, cache su snapshot cambiati; spiegazione con citazioni; nessuna inferenza individuale o causale; accessibilità, performance e browser secondo i gate esistenti. Le domande amministrative rimangono parziali o non determinabili fino alla disponibilità dell’evidenza necessaria.

Le condizioni di chiusura A6 sono verificate nell’attestazione #428/issue #330; questo documento usa quella baseline senza ripetere la certificazione. Prima di implementare A7, concordare il primo esperimento tecnico e il dossier pilota attraverso una PR distinta, poi applicare i gate descritti sopra. Questa proposta non autorizza automaticamente una UI o un servizio esterno.
