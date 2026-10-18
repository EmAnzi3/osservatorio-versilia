# A7 — fattibilità misurata dei quesiti di accettazione

Report derivato: le richieste sono eseguite sul catalogo indicato. Le mappature delle domande sono revisionate, non interpretate automaticamente.

Le componenti calcolate non provano completezza della risposta. Un chiarimento deve essere risolto prima della risposta pubblica; gli esempi di selezione non sono default impliciti.

Catalogo SHA256: `1416209ca86f27b4eaeede51e59a90edd0b24167f75c60e5157df4583678d710`

| ID | Domanda | Stato | Componenti calcolate | Limiti / chiarimenti / rifiuti |
| --- | --- | --- | ---: | --- |
| 1 | INVALSI di Massarosa rispetto a Versilia e Toscana | partial | 3 | Aggregato Versilia INVALSI non autorizzato; nessuna media dei punteggi comunali.; Grado scolastico e anno; g5 è una prova tecnica esplicita, non un default linguistico. |
| 2 | Quota con titolo terziario a Pietrasanta e confronto comunale | supported_after_clarification | 2 | Titolo terziario non coincide necessariamente con soli laureati; popolazione di riferimento esplicita. |
| 3 | Abitanti di Stazzema e anno del dato | supported | 1 | Riferimenti e definizioni nella risposta strutturata. |
| 4 | Spesa sociale pro capite del Comune | supported_after_clarification | 2 | Comune e definizione: indagine servizi sociali diversa dalla missione contabile. |
| 5 | Reddito imponibile medio a Forte dei Marmi | supported | 1 | Riferimenti e definizioni nella risposta strutturata. |
| 6 | Temperatura di Seravezza negli ultimi trenta anni | partial | 1 | Il trend 1975–2025 non risponde automaticamente alla finestra trentennale; serve selezione e operazione sul periodo esatto. |
| 7 | Pioggia e caldo estremo a Viareggio rispetto agli anni Novanta | partial | 2 | Tmax non è un conteggio di giorni estremi; servono soglia e periodi omogenei, nessuna conversione dal trend.; Definire caldo estremo e intervalli. |
| 8 | Comune con riscaldamento storico più marcato | supported_after_clarification | 1 | La prova usa il trend nativo 1975–2025, non qualsiasi finestra. |
| 9 | Cambiamenti di addetti e settori a Camaiore | partial | 3 | Il dettaglio industria/servizi del Frame non è un pannello storico degli addetti per tutti i codici ATECO; nessun incrocio di universi. |
| 10 | Unità locali delle costruzioni a Massarosa | partial | 2 | Tre divisioni dirette non autorizzano il totale di sezione F; manca la composizione additiva riconciliata.; ['insufficient_observations', 'partial_coverage_requires_opt_in'] |
| 11 | Addetti nella nautica a Viareggio e confronto | partial | 2 | Unità locali C301 non sono addetti della nautica; i due risultati sono solo contesto. Dettaglio addetti settoriale e perimetro nautica da verificare negli acquisiti. |
| 12 | Tre settori con più unità locali | not_determinable | 0 | Rank A6 ordina Comuni di una vista, non viste ATECO. Occorrono livello omogeneo e ranking fra categorie senza doppi conteggi.; Comune e livello ATECO. |
| 13 | Settori che hanno perso più unità locali in Versilia nel decennio | partial | 1 | Lo storico di un Comune/una divisione è disponibile; aggregazione Versilia, variazioni e ordinamento tra settori richiedono capacità riconciliate.; Decennio esatto e classificazione omogenea. |
| 14 | Peso di commercio e ospitalità sulle imprese di Forte | not_determinable | 0 | Imprese non equivalgono a unità locali; nessuna quota costruita con denominatori di universi diversi.; Imprese o unità locali; sezioni economiche e periodo. |
| 15 | Confronto del Comune su un tema | supported_after_clarification | 1 | Comune, tema e misura; la quota terziaria è una prova, non un punteggio di istruzione. |
| 16 | Indicatori di Camaiore sopra o sotto Toscana | partial | 2 | Due confronti verificati non sono una scansione di tutti i benchmark; disponibilità e confrontabilità devono essere valutate per vista. |
| 17 | Confrontabilità di Stazzema con Italia | supported_after_clarification | 1 | Indicatore, dimensione e periodo; il confronto riuscito non autorizza altri indicatori. |
| 18 | CSV di un confronto tra sette Comuni | partial | 1 | Risultato strutturato disponibile; export CSV generalizzato con metadati non implementato. |
| 19 | Principali criticità rispetto a Versilia | not_determinable | 0 | Criticità richiede criteri motivati, polarità e aggregato ammissibile; vietato punteggio automatico o media generica.; Comune, fenomeni e criteri. |
| 20 | Indicatori in cui Massarosa è prima o ultima | partial | 1 | Un rango numerico non è qualità amministrativa. Scansione completa con polarità e contesto non implementata. |
| 21 | Dati citabili per proposte su scuola o lavoro giovanile | partial | 2 | Servono competenze, destinatari, opzioni e monitoraggio; giovane in altra condizione non è automaticamente NEET. Nessuna efficacia causale inferita. |
| 22 | Temi che peggiorano nel tempo | partial | 1 | Storico numerico disponibile; peggioramento non si deduce dal segno. Valutazione trasversale e discontinuità da esplicitare.; Comune, tema, periodo e criterio. |
| 23 | Utilizzo fondi PNRR e numero progetti finanziati | partial | 3 | Finanziamento e macrofase non attestano spesa, qualità o risultato dell’opera; attribuzione al Comune attuatore distinta da localizzazione. |
| 24 | Bandi attivi oggi per una impresa locale | not_determinable | 0 | Resolver Radar con destinatario, settore, scadenza e freschezza non implementato nel workbench; dati Radar acquisiti separati.; Impresa, sede, settore, dimensione e data del controllo. |
| 25 | Opportunità recenti turismo e agricoltura | not_determinable | 0 | Resolver Radar e confronto fra aggiornamento, proroga e nuova opportunità non implementati nel workbench. |
| 26 | Percorso per conoscere il proprio Comune | not_determinable | 0 | Resolver editoriale Percorsi non implementato; non è una lacuna del catalogo numerico.; Comune e interesse. |
| 27 | Fonte e anno della quota con titolo terziario | supported | 1 | Riferimenti e definizioni nella risposta strutturata. |
| 28 | Significato di n.d. e differenza da zero | partial | 0 | Informazione documentata e accessibile nel sito; resolver di spiegazioni/metodo non ancora implementato nel workbench. |
| 29 | Calcolo del valore Versilia pro capite | supported_after_clarification | 1 | Indicatore, periodo, componenti e completezza; una formula ammessa non autorizza tutte le medie. |
| 30 | Segnalazione di un dato errato o non aggiornato | partial | 0 | Informazione documentata e accessibile nel sito; resolver di spiegazioni/metodo non ancora implementato nel workbench. |

## Limiti della misura

Nessuna percentuale unica di copertura: gli esempi non sono un campione statistico delle domande possibili. Fonte non esposta, capacità non implementata e dato non acquisito restano distinti. `data_access_or_data_gap` richiede audit degli snapshot prima di attribuire la lacuna alla fonte.

Il JSON conserva richieste, risultati, rifiuti e provenance; i riferimenti agli indicatori sono casi di accettazione, mai un secondo catalogo o routing di domande autorizzate. Le verifiche numeriche indipendenti rimangono la suite A6 e le regressioni puntuali.
