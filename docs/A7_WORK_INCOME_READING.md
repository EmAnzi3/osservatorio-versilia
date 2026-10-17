# A7 — preparazione della lettura lavoro e redditi

Incremento di composizione, non riapertura A6. La #442 educativa è ancora aperta: questo branch deriva dalla sua head `5c465b5` per riutilizzare lo standard editoriale, senza cambiare quel candidato. Prima di integrare la lettura pubblica occorre il merge del proprietario e la verifica post-merge della #442.

## Problema e prodotto

La domanda del piano `lavoro-centrale` riguarda il rapporto fra attività localizzate e opportunità per i residenti. Il piano `redditi-centrale` aggiunge il contesto fiscale, senza trasformarlo in misura del bisogno delle famiglie. Il preparatore esegue le richieste dei piani esistenti, estendendo i territori ai sette Comuni oppure ripetendo gli storici per singolo Comune. Non aggiunge domande al programma, indicatori, fonti, adapter o operazioni.

Questo primo incremento produce un modello derivato e sette **bozze PDF per revisione**, ciascuna con sintesi pertinente al Comune, confronti alfabetici, sei sezioni, grafico temporale e fonti. Non pubblica route, non cambia le sei domande del pilota né la lettura educativa. Non espone link dalla Home o dai menu. Il modello tecnico serve alla successiva integrazione, mentre il rapporto è l'output leggibile.

## Evidenze e confini

| Lettura | Capacità riutilizzata | Confine |
|---|---|---|
| Residenti che lavorano | Tasso 25–64 del 2024 | Non posti di lavoro localizzati, tasso di disoccupazione o transizioni individuali |
| Attività e addetti | ASIA, variazione cumulata 2018–2023 e addetti medi annui 2023 | Non crescita annuale, occupati residenti o totale Registro Imprese 2025 |
| Industria e servizi | Frame SBS, valore aggiunto industriale 2023 e differenza nominale servizi 2015–2023 | Non PIL comunale, crescita reale o prova di spostamento dei lavoratori |
| Retribuzioni | Media lorda per dipendente industriale 2023 | Non salario mediano, netto, qualità o durata dei contratti |
| Redditi da lavoro | MEF, ammontare/frequenza della fonte lavoro dipendente e assimilati, anno d'imposta 2024 | Non tutti i contribuenti, reddito disponibile o reddito familiare |
| Redditi e prezzi | Serie cumulata dal 2016 deflazionata con NIC Italia | Popolazioni fiscali diverse fra anni; non prezzi locali o potere d'acquisto individuale |
| Fasce fiscali | Macrofascia derivata dal catalogo, numeratore e denominatore nativi | Denominatore delle sole frequenze note; celle assenti non imputate. Non misura della povertà |

Il segno negativo della variazione ASIA di Stazzema è conservato nel grafico e nel testo. Ogni confronto usa una sola misura, definizione, unità e periodo. Le fonti ASIA, Frame e Registro Imprese non formano uno stock additivo o una serie unica. Toscana/Italia e un pannello di territori simili non vengono inventati.

## Verifiche riproducibili

```bash
python scripts/test_a7_work_income_reading.py --catalog dist/data/site-data.json
python scripts/a7_work_income_reading.py --catalog dist/data/site-data.json --output-dir /tmp/a7-lavoro --pdf
```

Prima si verificano le aspettative canoniche dei casi originari; poi il verificatore metodologico A6 controlla tutte le risposte estese. Il test separato riconcilia ogni Comune con snapshot congelati di occupazione, ASIA, Frame SBS, MEF e componenti reddituali 2016/2024 con NIC. Gli anni intermedi del reddito reale rimangono replay del catalogo: non è dichiarata una nuova verifica degli archivi MEF originali. Si verificano riproducibilità, copertura esatta, segni, celle mancanti, denominatori e rifiuto di output alterati o periodi mescolati.

Il controllo numerico è richiamato dal gate A7 esistente `test_a7_static_pilot.py`; nessun nuovo workflow o suite della release viene introdotto. I PDF delle bozze richiedono inoltre rendering e ispezione visiva prima della consegna. L'integrazione pubblica e i relativi gate browser restano un passaggio successivo.

L'hash delle evidenze rileva alterazioni rispetto al modello generato, non autentica un file riscritto da terzi. Il commit e gli hash dei sorgenti del renderer/CSS, programma, casi, catalogo e motore identificano gli input; i risultati A6 completi mantengono puntatori e provenienza. La disponibilità online corrente delle fonti non viene attestata.

## Passo successivo e ammissione

Integrare questi contenuti nella lettura A7 a capitoli e scelta del Comune, con consenso coerente per le componenti parziali, URL, PDF verificato e controlli browser/cache/riproducibilità come quelli educativi. Prima di Ready: Quick e Full locali ordinari sul candidato integrato, CI Quick→Full/A3, preview e revisione del proprietario. Le prove mirate delle bozze non sostituiscono questi gate.

Formazione, accessibilità delle aree produttive e sportelli sono opzioni istruttorie del programma esistente, non raccomandazioni. Domanda di professionalità, contratti, transizioni, ISEE, patrimonio e costi essenziali rimangono fabbisogni. Per valutare interventi occorrono platea, baseline, accessi, completamenti, esiti e confronto appropriato: il prima/dopo descrittivo non identifica effetti causali.
