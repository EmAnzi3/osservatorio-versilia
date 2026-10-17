# A7 — lettura educativa: dal pilota Massarosa ai sette Comuni

## Problema e obiettivo

La prima integrazione #436 esponeva le componenti del motore in sequenza verticale. La correttezza del calcolo non rendeva quella pagina una risposta utile al pubblico. Il proprietario ha chiesto di cambiare il modello prima di ampliare il repertorio: sintesi, grafici commentati, dossier interno e rapporto PDF.

Questo incremento riguarda una sola esperienza completa: «L’offerta educativa risponde ai bisogni delle famiglie e dei giovani?». Le altre cinque domande conservano la presentazione precedente; non sono dichiarate convertite al nuovo modello. Non aumenta la copertura e non conclude A7. L’accesso da Home/menu resta escluso, come richiesto.

## Riferimenti trasferiti

- Openpolis / Con i Bambini, [offerta educativa nelle periferie](https://www.openpolis.it/la-questione-educativa-nelle-periferie/): problema concreto, risultati anticipati, grafici selezionati e spiegazione delle implicazioni. Si trasferisce la gerarchia editoriale, non le loro misure geografiche o conclusioni causali.
- ONS, [How life has changed in Stoke-on-Trent](https://www.ons.gov.uk/visualisations/censusareachanges/E06000021/): titoli che esprimono risultati, confronti contestualizzati, definizioni e fonti. Non si replica la lunghezza dell’articolo.
- ONS, [Build a custom area profile](https://digitalblog.ons.gov.uk/2025/05/23/weve-updated-build-a-custom-area-profile/): approfondimenti selezionabili e stampa anche in PDF. Qui il PDF è invece un documento già composto e scaricabile, senza richiedere la stampa manuale della pagina.

Sono riferimenti di progettazione, non nuove fonti acquisite per la Versilia.

## Esperienza proposta

La sintesi usa un’apertura editoriale sul rapporto fra vita quotidiana e servizi, tre evidenze di Massarosa e un confronto sul tempo pieno esteso ai sette Comuni. Colori, dimensioni tipografiche, numeri e capitoli hanno ruoli distinti: nessuna immagine decorativa sostituisce i grafici. Il dossier è parte della stessa pagina, con capitoli raggiungibili: prima infanzia; tempo e organizzazione; spazi e accessibilità; apprendimenti e giovani; evidenze e scelte. Un solo capitolo è visibile alla volta. L’URL `?lettura=educazione#nidi` permette di raggiungere l’approfondimento; resta necessaria la conferma prevista dal lettore per le componenti parziali. «Cambia domanda» riapre i controlli e rimuove la risposta precedente.

Il download principale è «Scarica il rapporto PDF». Il rapporto ha una sintesi e capitoli impaginati con grafici, fonti, periodi e informazioni necessarie per le decisioni. Il JSON originale resta nei dettagli tecnici chiusi. Il dossier pubblico non rimanda a GitHub; il repository rimane una fonte tecnica facoltativa per riprodurre i risultati.

## Catena dei dati e limiti

`build_a7_static_pilot.py` esegue le richieste già approvate e verifica aspettative indipendenti e metodo. Il nuovo `a7_education_editorial.py` conserva quelle risposte e aggiunge quattro interrogazioni scolastiche estese ai sette Comuni, sul medesimo catalogo effettivo e motore. `territorial_evidence` riusa metriche/dimensioni/operazioni delle richieste originali, cambia soltanto la selezione territoriale, applica il verificatore metodologico A6 e riconcilia byte per byte le osservazioni originarie. Le risposte supplementari e i fatti rimangono nel modello editoriale con query, fonte, periodo, componenti, hash e puntatori. Il bundle e gli export originali delle sei domande non cambiano. Non introduce un catalogo di indicatori parallelo.

- Ricettività 2024/25: rapporto fra capacità potenziale e bambini residenti di 3–36 mesi. Non è frequenza o accesso effettivo. L’aggregato Versilia viene dal rapporto fra somme del motore, non dalla media delle percentuali. Gli zeri di Seravezza e Stazzema restano zeri della rilevazione e non attestano assenza di accessi intercomunali.
- MIM 2024/25: le richieste dimostrative originali selezionano Massarosa e Viareggio, ma i dati già acquisiti consentono i confronti su tutti i sette Comuni per alunni, alunni per classe, tempo pieno e accessibilità. La nuova lettura usa questo perimetro completo senza acquisizioni o modifiche agli adapter. Le quote mostrano i componenti: il 100% del tempo pieno di Stazzema è 64/64 alunni; non è un giudizio di qualità o un benchmark di territori equivalenti. Alunni delle scuole presenti, residenti e posti potenziali restano universi distinti.
- Accessibilità: quota delle risposte definite, non certificazione di tutti gli edifici o dell’esperienza degli alunni.
- INVALSI 2024-25, grado 8: tutte le sette righe restano visibili, con tre valori non disponibili e senza barre sostitutive. Dispersione implicita diversa da abbandono; Comune della scuola diverso dalla residenza; nessuna graduatoria di qualità.
- Le lacune del piano canonico sono conservate. Monitoraggio suggerito e opzioni amministrative sono fabbisogni da approfondire, non dati già acquisiti né raccomandazioni automatiche. Nessuna correlazione o inferenza causale aggiunta.

Le frasi numeriche e i grafici sono generati dallo stesso modello utilizzato dal PDF. Le affermazioni editoriali dipendenti da soglie («oltre metà») falliscono la build se il valore non le sostiene più: non restano testi obsoleti dopo un aggiornamento.

## Integrità e riproducibilità

La cartella di release immutabile ora include modello editoriale, modulo e PDF. Il manifest lega i byte degli asset; la validazione build/live controlla anche il PDF binario e il legame modello/bundle/commit. Il browser verifica l’hash del modello prima di mostrare le risposte e l’hash del PDF prima del download. Un errore del PDF non rende falsa la lettura: blocca il download con un messaggio esplicito. Gli asset di altre release hanno URL differenti; la policy di rivalidazione A7 include i nuovi file.

Il PDF viene prodotto da Chromium già richiesto dalla build; nessun servizio esterno e nessuna nuova dipendenza. Date dei metadati PDF fissate alla data del commit sorgente, senza cambiare lunghezze o offset; verifica byte per byte di due generazioni. L’edizione identifica il codice, mentre ciascuna evidenza conserva il proprio periodo. Il PDF è marcato semanticamente dal generatore; non si dichiara conformità PDF/UA o audit completo delle tecnologie assistive.

## Verifiche e accettazione

Il gate A7 Full esistente viene esteso, senza nuovo workflow o soglie ridotte: riconciliazione delle 28 osservazioni MIM con i componenti degli snapshot congelati (alunni/classi/tempo pieno e risposte SI/NO), conservazione delle otto osservazioni precedenti, rifiuto di coperture ristrette, ancore numeriche indipendenti, tracciabilità delle frasi, scale e barre, null/zeri, navigazione e collegamento interno, identità PDF scaricato/file generato, riproducibilità PDF, testo dei capitoli e confini, manifest alterati/mancanti e cache reale. Le cinque letture precedenti e i dodici export JSON restano verificati; il JSON pubblico richiede ora l’apertura dei dettagli tecnici. La preview isolata conserva il suo export originale.

Quick e Full locali ordinari in sequenza sullo stesso albero; successivamente CI Quick→Full e A3 sulla head corrente. Esiti e log effettivi nella PR. L’approvazione numerica non sostituisce il giudizio sul prodotto: il proprietario deve poter leggere la sintesi, esplorare i capitoli e aprire il PDF desktop/mobile prima del merge. Nessun merge/deploy dell’assistente, nessuna attestazione di pubblicazione prima della verifica post-merge.

## Estensione dopo #437 — il Comune selezionato

Il feedback del 17 ottobre chiede che il lettore riconosca ciò che emerge nel proprio Comune. Si conserva una sola domanda e la struttura approvata, con sette viste editoriali composte dai medesimi risultati A6. Il selettore bianco è interno alla lettura educativa: non estende le altre cinque domande del pilota Massarosa. Home/menu rimangono senza nuovi collegamenti.

`build_reading(..., focus_code)` seleziona le osservazioni già disponibili; `build_education` conserva una sola copia delle richieste/risposte territoriali e sette viste derivate. Non è un nuovo catalogo. Le tre conclusioni iniziali dichiarano osservazione, riferimento, periodo, questione istruttoria ed evidenze con puntatori: posti potenziali rispetto ai bambini e al rapporto fra somme della Versilia; diffusione effettiva del tempo pieno nella primaria; consistenza della rete e media alunni/classe. Sono confronti descrittivi, senza equiparare copertura teorica, accesso, qualità o adeguatezza. Le condizioni dipendono dai dati, non dal nome del Comune: zero posti censiti non significa zero accessi; tempo pieno a tutti gli alunni non significa adeguatezza universale. Le informazioni mancanti rimangono esplicite, compresi i tre null INVALSI. Una risorsa osservata non diventa una raccomandazione e non si forza un pregio/difetto per territorio.

URL della vista: `?lettura=educazione&comune=046030#nidi`. Il vecchio URL senza Comune conserva Massarosa; un codice sconosciuto mostra la scelta senza numeri o PDF, mai un fallback silenzioso. Il cambio Comune conserva il capitolo e aggiorna sintesi, evidenziazione e PDF; una nuova apertura mantiene il consenso richiesto. Nessuna memorizzazione della scelta. Le verifiche tecniche distinguono esplicitamente il pilota originale Massarosa dalle osservazioni territoriali.

Il manifest lega sette PDF (il file storico `education.pdf` resta Massarosa), i relativi hash per Comune e il modello. Builder e validatore controllano insieme completezza dei sette territori, Comune del rapporto, bundle e commit. Nel browser il download verifica l'hash del PDF scelto; una risposta lenta della precedente selezione non può scaricare un rapporto o pubblicare un errore per il nuovo Comune. Service worker e gate cache includono i PDF territoriali. Nessun servizio aggiuntivo per GitHub Pages.

Il gate A7 esistente verifica tutte le sette viste: componenti native Toscana/MIM, testi condizionati dai valori, evidenze, highlight, null/zeri, integrità e riproducibilità di ogni PDF, selezione, capitoli e download desktop/mobile, URL e consenso, Comune sconosciuto e risposta PDF tardiva. Gli assert precedenti restano applicati al pilota e ai dodici export. Le aspettative del vecchio modello sono adattate soltanto al nuovo contenitore delle viste; non vengono ridotte le soglie o aggirati i controlli.

L'enrichment su domanda, rinunce, accoglienza, utilizzo e serie recenti Toscana è un lotto successivo proposto, non dato già acquisito. La scheda di ammissione vive nel metodo dei dossier; nessun campo esterno viene introdotto nei risultati di questa estensione.


## Firma editoriale, attribuzione e riuso — 17 ottobre

I sette rapporti educativi usano il logo vettoriale canonico `assets/brand-mark.svg`, incorporato nel PDF senza risorse remote, accanto al nome Osservatorio Versilia. Il piè di pagina riporta nome, dominio, Comune e numerazione. La data di edizione del rapporto deriva dal commit sorgente per preservare la riproducibilità; è distinta dai periodi delle osservazioni, che rimangono espliciti per ogni grafico.

I grafici della lettura web e gli stessi grafici esportati nel rapporto recano separatamente «Elaborazione: Osservatorio Versilia» e la fonte originaria collegata. Non attribuiscono all'Osservatorio la produzione delle rilevazioni. L'intestazione conserva misura, territorio, periodo e copertura; scale, valori, null, ordine e selezione non cambiano. Questo incremento non aggiunge formati di esportazione o controlli alla pagina.

La sezione finale «Attribuzione e riuso» riprende la policy già pubblicata in `Il progetto#licenza`: CC BY 4.0 per testi, elaborazioni e visualizzazioni originali; dati e materiali di terzi conservano le rispettive condizioni. Non è una nuova licenza uniforme sui dati acquisiti e non certifica diritti ulteriori sui materiali delle fonti. La natura civica indipendente e il rinvio alla fonte originaria per usi ufficiali sono dichiarati una sola volta, insieme al metodo; nessuna clausola generale di esonero sostituisce i limiti specifici delle analisi.

Riferimenti di impaginazione: [logo ONS](https://service-manual.ons.gov.uk/brand-guidelines/logo) e [fonti e note dei grafici ONS](https://service-manual.ons.gov.uk/data-visualisation/guidance/chart-text). I marchi degli enti citati non vengono inseriti come partner o approvatori. Lo standard governa questa lettura e i suoi sette rapporti; le altre cinque domande del pilota e le interfacce/export già approvati rimangono conservati.

Il gate A7 esistente controlla il logo rispetto al vettore canonico, crediti e link per ogni grafico, data di edizione, policy di riuso distinta dai dati di terzi e firma/numerazione su ogni pagina dei sette PDF, oltre alle verifiche numeriche e di riproducibilità precedenti. Rendering dei PDF e controllo browser desktop/mobile restano necessari prima di Ready.
