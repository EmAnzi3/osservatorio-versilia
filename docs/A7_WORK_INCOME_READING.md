# A7 — lettura a capitoli su lavoro e redditi

Incremento di composizione, non riapertura A6. Baseline integrata #442, commit `3d3ccb010b821ba4cafaa41f17b875b8c70f1905`; standard editoriale educativo conservato. Il branch dedicato aggiunge una lettura candidata, soggetta ai gate e alla revisione prima del merge.
## Problema e prodotto

La domanda del piano `lavoro-centrale` riguarda il rapporto fra attività localizzate e opportunità per i residenti. Il piano `redditi-centrale` aggiunge il contesto fiscale, senza trasformarlo in misura del bisogno delle famiglie. Il preparatore esegue le richieste dei piani esistenti, estendendo i territori ai sette Comuni oppure ripetendo gli storici per singolo Comune. Non aggiunge domande al programma, indicatori, fonti, adapter o operazioni.

La domanda centrale sul lavoro apre sei capitoli per ciascuno dei sette Comuni, con selettore, grafici alfabetici, URL condivisibile e rapporto PDF del Comune. Si mostrano soltanto i contenuti del capitolo scelto. La lettura educativa, le sei domande originali, il consenso e i dodici export originali rimangono conservati; l'export tecnico del pilota Massarosa non diventa un export del Comune selezionato e viene etichettato separatamente. Nessun accesso aggiunto dalla Home o dai menu.

Le sei componenti obbligatorie del piano lavoro sono tutte composte. Le tre componenti fiscali sono contesto editoriale dal piano redditi, distinto dalla risposta canonica lavoro. Il campo `incomePlanCoverage` dichiara le componenti usate e la serie `mef_pensionIncomeShare_history` non composta: non si attesta il completamento del piano redditi. Le 21 richieste sono sette confronti su sette Comuni e due storici ripetuti per ciascun Comune.

## Pubblicazione e interazioni

`build_a7_public_page.py` genera il modello e i sette rapporti nello stesso grafo immutabile della lettura educativa. `a7_public_release.py` verifica inventario, hash, commit, bundle, domanda, sette viste e PDF. Il browser carica il modello solo se coincide con il manifest della release; il download verifica HTTP e SHA prima di consegnare il PDF. Una selezione sconosciuta non mostra dati o PDF di un altro Comune; un download lento della selezione precedente non può consegnare un rapporto dopo il cambio. Gli errori di download permettono il ritentativo e vengono cancellati soltanto dopo il recupero verificato.

`?lettura=lavoro&comune=046030#attivita` ripristina Comune e capitolo, mantenendo il consenso originale. Il contesto fiscale, le cui richieste canoniche ammettono componenti parziali, richiede inoltre un’apertura esplicita nei capitoli interessati; il download del rapporto completo rinvia a quella conferma prima di consegnarlo. Il consenso non viene salvato e si azzera ricaricando o cambiando domanda. Il service worker rivalida dalla rete modulo, modello e PDF: i dati di release diverse non vengono combinati. Nessun servizio esterno o interpretazione numerica libera.

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

Il controllo numerico è richiamato dal gate A7 esistente `test_a7_static_pilot.py`; nessun nuovo workflow o suite della release viene introdotto. Il gate pubblico esistente verifica i sette rapporti (sei pagine, metadati, provenienza, rigenerazione byte per byte), sette Comuni × sei capitoli su desktop e mobile, selezione PDF, segno negativo, serie temporale, consenso, errori di rete/integrità, ritentativo, download obsoleto e cache HTTP reale. Rendering e ispezione visiva precedono la consegna dell'anteprima.

L'hash delle evidenze rileva alterazioni rispetto al modello generato, non autentica un file riscritto da terzi. Il commit e gli hash dei sorgenti del renderer/CSS, programma, casi, catalogo e motore identificano gli input; i risultati A6 completi mantengono puntatori e provenienza. La disponibilità online corrente delle fonti non viene attestata.

## Ammissione e limiti

La preview e i controlli browser precedono Ready. Quick e Full locali ordinari in sequenza sul medesimo albero e CI Quick→Full/A3 sulla head corrente sono obbligatori prima del via libera al merge. Le prove mirate non sostituiscono questi gate; esiti e log effettivi nella PR. Nessuna dichiarazione di pubblicazione prima del deploy e del controllo live successivi al merge del proprietario.

Formazione, accessibilità delle aree produttive e sportelli sono opzioni istruttorie del programma esistente, non raccomandazioni. Domanda di professionalità, contratti, transizioni, ISEE, patrimonio e costi essenziali rimangono fabbisogni. Per valutare interventi occorrono platea, baseline, accessi, completamenti, esiti e confronto appropriato: il prima/dopo descrittivo non identifica effetti causali.
