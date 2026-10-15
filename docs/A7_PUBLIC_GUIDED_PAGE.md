# A7 — primi percorsi guidati sul sito

Stato: candidato in revisione. `/chiedi/` rende consultabili i percorsi Massarosa lavoro e infanzia/scuola della #434. Non conclude A7 né implementa una conversazione o un interprete libero. Merge e pubblicazione restano decisioni del proprietario.

## Esperienza e perimetro

Header, footer, ricerca, font e stili di base sono estratti dalla shell canonica. Il CSS del lettore è confinato a `.a7-guided`; il foglio delle sette pagine secondarie mantiene il proprio perimetro. Le altre pagine, i 40 golden e Camaiore non vengono ridisegnati.

L'accesso iniziale è l'URL `/chiedi/`, condivisibile e presente una sola volta nella sitemap. Nessuna voce viene aggiunta alla navigazione globale approvata. La pagina collega Massarosa, lavoro, istruzione e Stato dati; la ricerca globale rimane la ricerca degli indicatori. L'eventuale accesso da Home o menu richiede una successiva revisione visiva.

Domanda scritta, scelta delle alternative, consenso e download JSON riusano senza modifiche il modulo UI #434 e il lettore #432. Restano sei domande parziali e il bundle di 13 calcoli e tre rifiuti, derivato dai piani/casi canonici. La UI non promuove i rifiuti né dichiara implementati i 51 piani del programma. Fonti, periodi, universi, limiti e lacune restano visibili. Modificare una domanda revoca risposta e download; non elimina file già salvati volontariamente.

Senza JavaScript i controlli rimangono disabilitati, con link alle letture testuali generate. Evidenze mancanti o alterate bloccano i risultati, mantenendo disponibile la shell. Nessuna acquisizione, memorizzazione della digitazione o invio a terzi. La cache PWA contiene asset pubblici e risposte canoniche precalcolate, non le richieste scritte.

## Build, versioni e cache

Il wrapper transazionale originale chiama `build_a7_public_page.py` dopo la brandizzazione e l'uscita dal workspace temporaneo: il ripristino dei sorgenti deve precedere la verifica di provenienza A7. Il builder riusa `build_a7_dossier_preview.py` e il motore Python A6 sul catalogo effettivo della stessa build. Risolve il commit corrente in Git e riconcilia programma, dossier e hash degli snapshot prima di scrivere output; il solo formato dello SHA non basta. Nessun secondo catalogo, numero o inventario viene introdotto. Commit e hash restano esportabili.

La route è dichiarata come `standalone` e nelle eccezioni di trace del contratto dei contenuti. La build aggiunge soltanto `dist/chiedi/` e la voce sitemap, senza nuove mutazioni sorgente o workflow. Per riprodurre usare build pubblica/preflight ordinario. Il builder della sola pagina presuppone un dist coerente con catalogo effettivo e shell. Specifiche della preview separata in `A7_DOSSIER_PREVIEW.md`.

La PWA esistente usa stale-while-revalidate per `.mjs` e JSON diversi dal catalogo. La nuova regola interessa soltanto `bundle.json`, `release.mjs`, `reader.mjs` e `preview.mjs` sotto `/chiedi/`: rete prima della cache, con il fallback offline governato. Il lettore controlla hash e byte prima della risposta; una cache mista viene rifiutata. Una lettura offline coerente rimane congelata ai periodi/release dichiarati, senza promessa di aggiornamento. Le altre route mantengono la policy originale.

CSP ammette script locali e hash del JSON-LD, vieta oggetti, base e invio form. Stili inline rimangono ammessi per compatibilità con la shell. Le domande sono testo e non possono fornire URL, HTML, valori o metriche al lettore. Integrità rispetto alla release diversa da autenticità di un hosting compromesso; snapshot congelati diversi da disponibilità corrente delle fonti.

## Verifiche e revisione

Il gate A7 esistente conserva pilota/preview e verifica la pagina pubblica realmente generata: sei domande per due viewport, JSON interi rigiocati con il lettore originale, fonti/limiti, chiarimento, consenso, revoca, shell/ricerca, overflow, errori, assenza di richieste esterne e salvataggio della digitazione. Il service worker reale è provato con vecchi asset in cache e risposte HTTP nuove su tutti e quattro i file. Cache mista offline: rifiuto `bundle_integrity_mismatch`.

Il validatore pubblico build/live richiede route, asset e hash di bundle/lettore coerenti con la release. Prove negative: file mancanti e alterazioni. I gate browser generali scoprono la nuova pagina dal dist, senza nuove baseline o soglie. I due helper dei font usano una funzione esplicita, mantenendo la condizione originale anche quando la CSP vieta eval e i font caricano lentamente. Quick e Full locali ordinari in sequenza sullo stesso albero; CI Quick→Full e A3 sulla head attuale. Commit/log/esiti effettivi nella PR, skipped diverso da PASS.

Prima del merge: aprire `/chiedi/` nella preview desktop/mobile, scegliere e scrivere una domanda, provare una richiesta generica e una scelta esplicita, leggere limiti/copertura e scaricare il JSON. Modificare il testo deve rimuovere risposta/download. Controllare ricerca, link, leggibilità e sovrapposizioni. Dopo il merge: deploy e controllo live sul commit integrato, inclusi asset/hash A7. Il verde della PR non attesta la pubblicazione.

L'incremento avanza A7.5 soltanto sul perimetro verificato. Nessuno step A7 è dichiarato DONE prima di approvazione e verifica. Estensione dei dossier, interpretazione libera e servizi esterni rimangono decisioni separate; nessuna diagnosi causale, previsione, inferenza individuale o raccomandazione automatica.
