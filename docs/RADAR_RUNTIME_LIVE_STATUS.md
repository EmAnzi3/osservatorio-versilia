# Radar: budget di esecuzione e stato della pubblicazione

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
