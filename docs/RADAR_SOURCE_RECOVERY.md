# Radar — acquisizione ANCI/MIM e ANCI Toscana

## Evidenza verificata l'8 ottobre 2026

La #351 è mergiata. Sul suo head `b03acc0`, Quick/Full CI, refresh, dry-run e shadow sono verdi. La scansione shadow impiega circa 12 minuti e il confronto finale viene eseguito; il confronto risulta divergente, non prova superiorità del motore. Il refresh produce 63 opportunità, zero nuove, 14 endpoint falliti, sette fonti in grace e una unhealthy.

Nel journal dello shadow `37782316952` ANCI Toscana risponde direttamente su tutti i cinque endpoint configurati. L'archivio `https://ancitoscana.it/categorie/bandi/` impiega 1,492 secondi, senza Chromium o reader proxy. La fonte era già configurata; non viene aggiunta come sostituzione della copertura nazionale.

Sul medesimo runner ANCI News e feed falliscono dopo circa 60 secondi; l'archivio PN 2021–2027 del MIM e il vecchio feed PNRR vanno in timeout, MIM Comunicati restituisce 403. Nel probe Work contemporaneo ANCI News e l'archivio MIM restituiscono HTTP 200; MIM Comunicati rimane 403. Questa differenza non identifica ancora la causa di rete e non certifica il recupero automatico.

## Lettura ANCI Toscana

Il parser generico associava a una scheda testo e categorie successive. La lettura dei contenitori Elementor `.e-loop-item` mantiene insieme titolo, link e sola anteprima della stessa scheda. Sul payload acquisito dall'archivio si ricavano cinque segnalazioni invece di tre: vengono recuperate anche Valorizzazione Centri Commerciali Naturali e Musica Jazz 2027. PRAF, senza un termine di opportunità nella scheda, resta escluso.

Soltanto le schede dell'archivio Bandi possono entrare nella coda interna con anteprima priva di beneficiari comunali. Tutte restano `internal_review` e `discovery_only`; i gate documentali e di pubblicazione non cambiano. Le pagine tematiche mantengono il filtro comunale. Diverse scadenze mostrate sono già trascorse: cinque segnalazioni non significano cinque nuovi bandi aperti.

## Prossima discriminante sul runner

Il dry-run esegue `opportunity_transport_smoke.py --diagnose-routes` prima dell'entrypoint produttivo. Confronta curl normale e IPv4 sui percorsi ANCI/MIM configurati e sull'archivio ANCI Toscana come controllo. Quattro worker, otto secondi massimi per richiesta, quattro per connessione, dodici per processo; nessun retry. HTTPS, verifica TLS e soli redirect HTTPS rimangono obbligatori.

L'artifact conserva `opportunity-route-diagnostic.json`: codice curl/HTTP, IP remoto, URL finale, redirect, protocollo HTTP, verifica TLS, tempi DNS/connessione/TLS/primo byte, quantità scaricata e candidati estratti. Non modifica snapshot o salute delle fonti; il suo esito non promuove opportunità e non sostituisce i gate live.

Se soltanto IPv4 funziona ripetutamente, va verificato quel trasporto mantenendo verifica TLS, URL e provenienza ufficiali. Se entrambi falliscono, non introdurre un fallback come copertura equivalente senza un'acquisizione aggiornata dimostrata. Un eventuale collettore esterno richiede un ambiente automatico disponibile e ricevute verificabili; oggi non è configurato. ANCI Toscana amplia la scoperta regionale, non attesta recupero ANCI nazionale/MIM.


## Primary candidate pipeline — verified-opportunities-v1

The daily primary workflow now owns the shadow semantic comparison and the
complete public-site build/browser validation. The old shadow is manual failure
rehearsal only: no second scheduled or PR live scan.

The owner requested this operational change on 2026-10-09. Persistent discovery
failure is explicitly degraded coverage, not proof that the published grants are
invalid. The primary can publish otherwise verified opportunities while recording
`discoveryCoverage.status=degraded` and retaining `runtimeUncoveredFamilies`,
endpoint failures, last successful fetch and consecutive failure counts. The
public audit summary displays the discovery gap. This does not recover ANCI/MIM
and does not assert complete coverage or invent grants. Both workflows inherit
the same failed-primary-run diagnostic; a green shadow no longer resets grace.

Strict mode remains the CLI default. Only the explicit workflow policy opts into
verified-only publication. Structural coverage, direct primary verification,
continuity, expired-item lifecycle, backtest, regional fail, exhausted scan
budget, snapshot validation, comparison execution, full-site build and browser
checks still block publication. Invalid snapshots cannot seed a later release.
Deploy remains restricted to main production events; pull requests and dry runs
cannot persist or publish. The production workflow name and runtime branch remain
stable for Pages and live-status consumers.
