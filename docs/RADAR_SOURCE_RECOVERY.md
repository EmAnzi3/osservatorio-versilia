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

## Controlli settimanali e audit indipendente — 10 ottobre 2026

ANCI nazionale e MIM enti locali passano a `checkEveryDays: 7`: sette giorni
dall'ultimo tentativo effettivo, anche fallito, sullo snapshot runtime accettato
o sulla diagnostica più recente. Senza memoria il controllo viene eseguito subito.
I run intermedi saltano sia prefetch sia collector, dichiarano `deferred`,
conservano ultimo tentativo/esito/successo, contatore dei fallimenti e diagnostica
dell'ultimo controllo (`lastCheckedEndpoints`). Il rinvio non incrementa i
fallimenti e non equivale a un successo. Le segnalazioni precedenti restano nella
coda interna con data dell'ultima lettura. Verifica documentale dei singoli bandi
e gate di pubblicazione restano giornalieri e invariati.

Il rapporto distingue nuove schede pubbliche e nuove segnalazioni interne da verificare, senza attribuire alle segnalazioni la data di un nuovo bando.
Indica ultima verifica e prossima scadenza per le fonti
rinviate. Non viene creato un secondo workflow: il primario esegue il controllo
settimanale quando dovuto. Il budget finito resta applicato anche alle nuove rotte.

### Alternative valutate

| Percorso | Evidenza del 10 ottobre | Decisione |
|---|---|---|
| ANCI feed principale `/feed/` | HTTP 200 nel probe Work | Inserito nel controllo settimanale, prima delle rotte già fallimentari |
| ANCI WordPress REST `/wp-json/wp/v2/posts?per_page=5` | HTTP 200 nel primo probe; richiesta a 30 articoli poi in timeout | API a 30 articoli inserita tra le rotte settimanali; parser JSON già supportato, recupero dal runner ancora da provare |
| ANCI News/feed e MIM PN/PNRR/Comunicati | Fallimenti persistenti nei log del runner | Conservati come tentativi settimanali, non dichiarati recuperati |
| MIM `istruzione.it/edilizia_scolastica/news.shtml` | Link indicato nella circolare istituzionale per gli avvisi correnti; HTTP 403 nel probe Work | Aggiunto alle rotte MIM settimanali, recupero non attestato |
| MIM pagina Avviso 79378/2026 | HTTP 403 anche nel probe Work | Evidenza del blocco, non soluzione di trasporto |
| INDIRE `ottopermille.indire.it` | HTTP 200, redirect a pagina SPID di candidatura | Non usato come archivio o prova documentale: la pagina accessibile contiene soltanto login |
| ANCI Lombardia: Edilizia scolastica e archivio circolari | Entrambi HTTP 200; link ai nuovi avvisi scolastici | Canale giornaliero supplementare di segnalazioni, con parser che conserva il link della singola scheda; nessuna copertura sostitutiva MIM/ANCI nazionale né ammissibilità Toscana presunta |
| IPv4, HTTPS/Chromium, reader | Prove precedenti senza recupero ripetibile; reader non è verifica primaria | Nessuna disattivazione TLS né ulteriore ripetizione quotidiana delle stesse rotte |
| Collettore esterno / runner con rete diversa | Nessun ambiente persistente disponibile/configurato in questo progetto | Opzione architetturale residua, non una soluzione già operativa |

### Lo zero nuove non prova un periodo di magra

Confronto indipendente con lo snapshot runtime del 10 ottobre, generato alle
12:41:59 UTC, 55 schede e 137 segnalazioni interne:

- **Otto per mille, interventi urgenti di edilizia scolastica**: avviso ministeriale
  prot. 78918 del 1 ottobre 2026, candidature 5–23 ottobre, dotazione assegnabile
  103.426.620 euro. Assente da opportunità, discovery, review, quality/coverage
  hold e archivio. Il PDF ministeriale ospitato da ANCI è stato acquisito HTTP 200
  e letto integralmente nel probe Work; include gli enti locali e l'area Centro
  con Toscana. È un falso negativo di scoperta confermato; ammissibilità del
  singolo intervento da verificare, non una candidatura garantita per ogni Comune.
  Documento: https://www.anci.it/wp-content/uploads/2026/10/m_pi.AOODGFIESD.REGISTRO-UFFICIALEU.0078918.01-10-2026.pdf
  Copia integrale accessibile anche su host ANCI Lombardia distinto: https://anci.lombardia.it/documenti/24093-Avviso%20MIM%20n.%2078918%20del%201%20ottobre%202026.pdf
  Questa è una strada concreta per la verifica documentale, da provare sul runner.
- **Vulnerabilità sismica edifici scolastici**, Avviso MIM 79378 del 6 ottobre:
  circolare ANCI Lombardia del 7 ottobre indica richieste 7–14 ottobre ore 14.
  Assente dagli stessi bucket. Segnalazione istituzionale concreta ma documento
  ministeriale ancora 403: falso negativo di segnalazione, verifica primaria
  non completata; non promuovere automaticamente.
  https://anci.lombardia.it/dettaglio-circolari/20261071633-edilizia-scolastica-%E2%80%93-vulnerabilit%C3%A0-sismica/
- Microzonazione/CLE (17 ottobre) e Toscana Diffusa (30 ottobre) risultano già
  nelle schede pubbliche: il collector intercetta alcuni avvisi regionali.

Limite strutturale: `opportunity_radar_v03.run_v03` assegna il discovery a una
coda `internal_review`; questa coda non viene trasformata automaticamente in
nuove schede pubbliche. L'output usa collector/classificatore primari, regole
verificate e corpus di promozioni audit. La presenza di segnalazioni non misura
la capacità di pubblicare nuovi bandi. Il confronto pubblico e il badge `new`
misurano schede pubblicate, non completezza della ricerca.

Questa modifica riduce i tentativi inutili e amplia la discovery. Non risolve
da sola la verifica/promozione degli avvisi nazionali nuovi e non aggiunge
manualmente i due esempi al corpus per simulare capacità automatica. Prima di
dichiarare il Radar completo serve chiudere quel passaggio con evidenze primarie,
revisione tempestiva e una prova indipendente di avvisi recenti intercettati.
