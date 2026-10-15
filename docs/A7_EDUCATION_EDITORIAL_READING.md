# A7 — lettura pubblica dell’offerta educativa di Massarosa

## Problema e obiettivo

La prima integrazione #436 esponeva le componenti del motore in sequenza verticale. La correttezza del calcolo non rendeva quella pagina una risposta utile al pubblico. Il proprietario ha chiesto di cambiare il modello prima di ampliare il repertorio: sintesi, grafici commentati, dossier interno e rapporto PDF.

Questo incremento riguarda una sola esperienza completa: «L’offerta educativa risponde ai bisogni delle famiglie e dei giovani?». Le altre cinque domande conservano la presentazione precedente; non sono dichiarate convertite al nuovo modello. Non aumenta la copertura e non conclude A7. L’accesso da Home/menu resta escluso, come richiesto.

## Riferimenti trasferiti

- Openpolis / Con i Bambini, [offerta educativa nelle periferie](https://www.openpolis.it/la-questione-educativa-nelle-periferie/): problema concreto, risultati anticipati, grafici selezionati e spiegazione delle implicazioni. Si trasferisce la gerarchia editoriale, non le loro misure geografiche o conclusioni causali.
- ONS, [How life has changed in Stoke-on-Trent](https://www.ons.gov.uk/visualisations/censusareachanges/E06000021/): titoli che esprimono risultati, confronti contestualizzati, definizioni e fonti. Non si replica la lunghezza dell’articolo.
- ONS, [Build a custom area profile](https://digitalblog.ons.gov.uk/2025/05/23/weve-updated-build-a-custom-area-profile/): approfondimenti selezionabili e stampa anche in PDF. Qui il PDF è invece un documento già composto e scaricabile, senza richiedere la stampa manuale della pagina.

Sono riferimenti di progettazione, non nuove fonti acquisite per la Versilia.

## Esperienza proposta

La sintesi espone tre evidenze di Massarosa, una lettura dell’accesso ai servizi e un confronto selezionato sul tempo pieno. Il dossier è parte della stessa pagina, con capitoli raggiungibili: prima infanzia; tempo e organizzazione; spazi e accessibilità; apprendimenti e giovani; evidenze e scelte. Un solo capitolo è visibile alla volta. L’URL `?lettura=educazione#nidi` permette di raggiungere l’approfondimento; resta necessaria la conferma prevista dal lettore per le componenti parziali. «Cambia domanda» riapre i controlli e rimuove la risposta precedente.

Il download principale è «Scarica il rapporto PDF». Il rapporto ha una sintesi e capitoli impaginati con grafici, fonti, periodi e informazioni necessarie per le decisioni. Il JSON originale resta nei dettagli tecnici chiusi. Il dossier pubblico non rimanda a GitHub; il repository rimane una fonte tecnica facoltativa per riprodurre i risultati.

## Catena dei dati e limiti

`build_a7_static_pilot.py` esegue le richieste già approvate e verifica aspettative indipendenti e metodo. Il nuovo `a7_education_editorial.py` usa esclusivamente i fatti di quelle risposte, conservando riferimenti case/puntatore. Non introduce un catalogo di indicatori parallelo.

- Ricettività 2024/25: rapporto fra capacità potenziale e bambini residenti di 3–36 mesi. Non è frequenza o accesso effettivo. L’aggregato Versilia viene dal rapporto fra somme del motore, non dalla media delle percentuali. Gli zeri di Seravezza e Stazzema restano zeri della rilevazione e non attestano assenza di accessi intercomunali.
- MIM 2024/25: le richieste esistenti selezionano Massarosa e Viareggio. Il perimetro ridotto non viene descritto come indisponibilità degli altri Comuni. È un confronto descrittivo scelto, non un gruppo di territori dimostrati equivalenti. Alunni delle scuole presenti, residenti e posti potenziali sono universi distinti.
- Accessibilità: quota delle risposte definite, non certificazione di tutti gli edifici o dell’esperienza degli alunni.
- INVALSI 2024-25, grado 8: tutte le sette righe restano visibili, con tre valori non disponibili e senza barre sostitutive. Dispersione implicita diversa da abbandono; Comune della scuola diverso dalla residenza; nessuna graduatoria di qualità.
- Le lacune del piano canonico sono conservate. Monitoraggio suggerito e opzioni amministrative sono fabbisogni da approfondire, non dati già acquisiti né raccomandazioni automatiche. Nessuna correlazione o inferenza causale aggiunta.

Le frasi numeriche e i grafici sono generati dallo stesso modello utilizzato dal PDF. Le affermazioni editoriali dipendenti da soglie («oltre metà») falliscono la build se il valore non le sostiene più: non restano testi obsoleti dopo un aggiornamento.

## Integrità e riproducibilità

La cartella di release immutabile ora include modello editoriale, modulo e PDF. Il manifest lega i byte degli asset; la validazione build/live controlla anche il PDF binario e il legame modello/bundle/commit. Il browser verifica l’hash del modello prima di mostrare le risposte e l’hash del PDF prima del download. Un errore del PDF non rende falsa la lettura: blocca il download con un messaggio esplicito. Gli asset di altre release hanno URL differenti; la policy di rivalidazione A7 include i nuovi file.

Il PDF viene prodotto da Chromium già richiesto dalla build; nessun servizio esterno e nessuna nuova dipendenza. Date dei metadati PDF fissate alla data del commit sorgente, senza cambiare lunghezze o offset; verifica byte per byte di due generazioni. L’edizione identifica il codice, mentre ciascuna evidenza conserva il proprio periodo. Il PDF è marcato semanticamente dal generatore; non si dichiara conformità PDF/UA o audit completo delle tecnologie assistive.

## Verifiche e accettazione

Il gate A7 Full esistente viene esteso, senza nuovo workflow o soglie ridotte: ancore numeriche indipendenti, tracciabilità delle frasi, scale e barre, null/zeri, navigazione e collegamento interno, identità PDF scaricato/file generato, riproducibilità PDF, testo dei capitoli e confini, manifest alterati/mancanti e cache reale. Le cinque letture precedenti e i dodici export JSON restano verificati; il JSON pubblico richiede ora l’apertura dei dettagli tecnici. La preview isolata conserva il suo export originale.

Quick e Full locali ordinari in sequenza sullo stesso albero; successivamente CI Quick→Full e A3 sulla head corrente. Esiti e log effettivi nella PR. L’approvazione numerica non sostituisce il giudizio sul prodotto: il proprietario deve poter leggere la sintesi, esplorare i capitoli e aprire il PDF desktop/mobile prima del merge. Nessun merge/deploy dell’assistente, nessuna attestazione di pubblicazione prima della verifica post-merge.
