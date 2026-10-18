# Radar: budget di esecuzione e stato della pubblicazione

## Trasporto regionale — correzione candidata del 18 ottobre 2026

Il run [39093561987](https://github.com/EmAnzi3/osservatorio-versilia/actions/runs/39093561987/job/117575186565)
si è fermato con `coverageHold=1` e `regionalCompleteness=fail`.
Il journal mostra richieste Regione Toscana rifiutate dopo l'esaurimento del
budget condiviso della fonte e un allegato con spazi nel percorso rifiutato
dal client HTTP. Persistenza e pubblicazione sono state saltate.

La correzione candidata mantiene 60 secondi per endpoint, 180 cumulativi per
fonte/host e 1.200 per scansione. Non aumenta i limiti: riserva 60 secondi alle
verifiche ufficiali e 30 al controllo di completezza di `www.regione.toscana.it`,
oltre ai 30 già riservati alla continuità. Sul dominio regionale la discovery
ordinaria può quindi spendere al massimo 60 secondi, la verifica ufficiale 120,
il safety net regionale 150 e la continuità 180, sempre cumulativi e soggetti
alla scadenza globale. La riserva regionale non riduce il budget degli altri host.

Il safety net usa un tipo di richiesta distinto nel journal. Non cambia
lo storico diagnostico della discovery per lo stesso URL: i due esiti restano
separati, anche se uno fallisce e l'altro riesce. Non cambia
classificazione, finestre temporali o destinatari; se le riserve o la scansione
scadono, la richiesta resta un errore e i gate possono ancora bloccare il run.
La codifica degli URL PDF conserva `%2F`, `%20`, `+`, parametri e firme già
codificati; tratta soltanto i caratteri non validi per il trasporto e rimuove il
frammento, che non viene inviato al server. La deduplicazione degli allegati
riconosce la stessa risorsa scritta con spazi o `%20`.

Regressioni negli script esistenti `test_opportunity_discovery_resilience.py`
e `test_opportunity_run_report.py`: richieste HTTP locali reali nelle diverse
fasi, esaurimento per fonte/scansione, continuità, URL osservato nel run, Unicode,
query firmate e deduplicazione. Queste prove verificano il codice; non attestano
la disponibilità corrente delle fonti esterne né un nuovo snapshot pubblicato.
Quick/Full locali e CI del candidato restano necessari prima del merge.

Il test di terminazione del gruppo di processi legge il PID esposto da `/proc`
dal figlio stesso: in un container con namespace PID annidato `Popen.pid` può
identificare un altro processo nella vista procfs dell'host. Il figlio deve
essere partito prima del timeout e deve risultare terminato o zombie dopo la
pulizia, con gli stessi limiti e assert precedenti. Il codice di terminazione
del runtime non cambia.

## Avviso Pro Loco — qualificazione documentale del 18 ottobre 2026

Il dry-run del primo candidato trasporto `9977c7`, run `39106642616`, ha
riconfermato le richieste regionali ma si è fermato sul caso
`rt-completeness-07ac9db033e1e3`: quattro giorni di review oltre la grazia di
tre giorni. L'esito rimane FAIL, con pubblicazione saltata. Non basta correggere
il trasporto per dichiarare risolto un caso documentale.

Recuperati e letti integralmente il decreto 22288 del 7 ottobre 2026 e gli
Allegati A (13 pagine), B (8) e C (3). L'impronta SHA256 dell'Allegato A
`d350edaa454a9e24fa3db658721869f2d60f60a91a9842c8b55af5b13d2aed9f`
coincide con quella riportata nel decreto; anche le impronte B/C coincidono.
Le copie ufficiali e la pagina di fonte sono congelate in
`tests/fixtures/proloco-notices/`, con URL, hash e articoli in `provenance.json`.
Il link della pagina al decreto apre una rotta SPA nella ricerca atti; questo
non rende indisponibili gli allegati della banca dati.

L'art. 2 riserva domanda e contributo alle Pro Loco iscritte per il 2026.
Gli artt. 1.3 e 6.1.d prevedono realizzazione condivisa e accordi con attività,
ruoli e territorio espliciti; il criterio 7.C1 contempla la compartecipazione
economica comunale. L'Allegato C, sezione 5, identifica i soggetti coinvolti.
È quindi documentato un percorso di partnership operativa condizionata,
non una candidatura diretta comunale. Non è accertata l'esistenza di un
accordo, di una Pro Loco proponente o di un progetto in uno dei sette Comuni.

La nuova voce riusa `verifiedEntries` dell'overlay audit canonico esistente:
sette Comuni condizionati, Pro Loco beneficiaria, accordo operativo necessario,
finestra entro il 3 novembre 2026 ore 13:00. Attività e spese devono concludersi
nel 2026; contributo fino all'80%, tetti 15.000/10.000 euro secondo graduatoria,
almeno 20% a carico del beneficiario. L'Allegato B non ammette la rendicontazione
di spese sostenute da altri soggetti: nessun contributo diretto al Comune.
La pagina primaria viene riconfermata dal percorso ordinario, senza fallback
recente. Nessuna nuova fonte di discovery, regola generale, esclusione,
estensione della grazia o soglia modificata.

La regressione nell'esistente `test_opportunity_audit_gap_fixes.py` controlla
PDF e pagina reali congelati, hash e articoli, ruolo e sette condizioni comunali,
separazione dal conteggio principale, riconciliazione safety net, deduplicazione,
variazione del termine, fonte mancante ed archiviazione. Un hold estraneo resta
intatto. Non usa soltanto fixture costruite dai termini della voce.
Le copie congelate verificano la qualificazione; un nuovo dry-run sulla head
aggiornata deve ancora riconfermare disponibilità online e pubblicabilità.

## Diagnosi del 6 ottobre 2026

Main era al merge #346 `93647a10`. Il run Radar `37469514913` ha completato
scansione (13:17:19–13:40:09 UTC) e validazione dello snapshot. Il gate build/browser
è stato cancellato alle 13:46:49, circa 30 minuti dall'avvio del job, con budget
configurato di 30 minuti. Persistenza e deploy sono stati saltati: il candidato
incompleto non ha sostituito lo snapshot e il sito precedenti.

Il reporter `37473539264` ha ricevuto HTTP 503 da
`https://osservatorioversilia.it/pnrr/` e ha scritto `ov-pages-live=failure` con
descrizione «deploy skipped». Questo esito era relativo a quel controllo;
non dimostrava un guasto permanente della pagina. Il proprietario ha confermato
di aprirla regolarmente. La pubblicazione precedente `37462135273` era riuscita.

## Contratto corretto

- Job refresh: massimo 60 minuti; scansione live: 30; build/browser: 20.
  Installazione, artifact, rapporti e notifiche hanno margine nel budget globale.
  Il limite resta finito: nessun timeout diventa successo e tutti i gate restano.
- Le PR hanno un gruppo di concorrenza per numero distinto dal gruppo produttivo.
  Un nuovo candidato PR può cancellare il proprio precedente senza cancellare
  un refresh produttivo. I run produttivi restano seriali.
- `ov-pages-live`: pubblicazione effettivamente tentata e relative route.
  Un deploy saltato o assente **non scrive** questo context, conservando l'ultima
  evidenza di pubblicazione. Un deploy fallito/cancellato resta failure.
- `ov-public-routes`: verifica corrente di Stato dati, PNRR, Percorsi e dettagli
  comunali/tematici tramite il validatore canonico. Massimo tre tentativi,
  due secondi tra tentativi, massimo 300 secondi per passata; timeout e HTTP/errori
  sono visibili nei log. Non certifica freschezza o disponibilità delle fonti dati.
- `ov-radar-refresh`: esito del run Radar, indipendente dalla raggiungibilità
  del sito precedente. Run cancellato/fallito resta failure; dry-run riuscito
  dichiara che non era richiesta pubblicazione.

Il reporter non forza stati verdi e non ripubblica artifact precedenti. Il suo job
può riuscire quando ha registrato correttamente un context failure; i context
descrivono gli esiti, il job l'esecuzione del reporter. Il nuovo codice entra in
uso nei successivi eventi `workflow_run`; non riscrive retroattivamente i run.

## Verifica

`scripts/test_pages_live_status.py` copre refresh cancellato con sito sano/guasto,
dry-run, deploy riuscito/fallito/saltato/assente e Pages ordinario. La matrice è
nel Quick canonico, nel contratto workflow e nel test dell'automazione Radar.
Nessun cambiamento a dati, pagine, asset, golden o soglie Lighthouse.

Prima del merge: Quick e Full locali, CI Quick→Full sul medesimo albero.
Dopo il merge: un solo refresh produttivo completo per verificare runtime,
persistenza, gate browser, eventuale deploy e context separati. Non avviare
serie di retry Actions per diagnosticare il codice.
