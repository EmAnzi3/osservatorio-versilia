# Radar Opportunità Versilia — v0.4.3 copertura residua

La v0.4.3 completa l'espansione mirata della rete avviata con la v0.4 coverage-first e la v0.4.2 independent audit. L'obiettivo non è aumentare indiscriminatamente il numero di portali, ma presidiare in modo distinto le principali famiglie di opportunità comunali italiane, regionali ed europee che l'audit esterno ha indicato come residue.

La route resta esclusivamente di anteprima, `noindex,nofollow,noarchive`, fuori sitemap e navigazione pubblica. La Draft PR #82 non implica merge o pubblicazione.

## Cinque misure distinte

1. **Backtest classificatore** — precision/recall sui candidati già osservati; non misura la completezza del web.
2. **Coverage contract** — verifica che le famiglie istituzionali minime siano presidiate e che le sentinelle note siano gestite correttamente.
3. **Independent audit** — usa sweep e fonti holdout che non alimentano direttamente il collector per cercare falsi negativi.
4. **Residual evidence audit** — richiede che ogni nuova fonte v0.4.3 abbia evidenza ufficiale recente e versionata; una voce nel file di configurazione non basta a dichiarare una famiglia coperta.
5. **Capture rate prospettico** — quota delle opportunità pertinenti emerse dal campione indipendente che il radar aveva già intercettato; diventa KPI solo dopo un campione minimo di 20 casi.

## Copertura v0.4.3

Il contratto passa da **18 a 25 famiglie**. Le sette nuove famiglie sono:

- programmi europei dedicati alle città (`eu-urban`);
- programmi UE per istruzione, giovani e sport (`eu-education-youth`);
- infrastrutture e connettività UE (`eu-infrastructure-connectivity`);
- ricerca e innovazione UE con ruolo territoriale (`eu-research-innovation`);
- Digital Europe (`eu-digital`);
- Comuni e territori montani (`mountain-territories`);
- sviluppo rurale, FEASR e LEADER (`rural-territorial-development`).

La famiglia cooperazione territoriale viene inoltre rafforzata con Interreg Europe e resilienza/protezione civile con il Dipartimento nazionale della Protezione Civile.

## Undici nuovi canali mirati

### Europa

- **URBACT** — reti europee di città;
- **European Urban Initiative (EUI)** — strumenti per autorità urbane, con City-to-City Exchanges a sportello;
- **Erasmus+** — solo azioni con ruolo documentato di organismi pubblici/locali;
- **Connecting Europe Facility (CEF)** — infrastrutture e connettività;
- **Horizon Europe** — solo topic con ruolo operativo verificabile per città/autorità locali;
- **Digital Europe** — trasformazione digitale e pubbliche amministrazioni;
- **Interreg Europe** — cooperazione interregionale, in aggiunta a Italia-Francia Marittimo.

### Italia

- **Dipartimento Affari regionali — Montagna**;
- **Dipartimento della Protezione Civile** — fonte upstream: le risorse vengono esposte solo quando diventano azionabili dal Comune;
- **MASAF** — fonte a priorità contenuta e fortemente filtrata per evitare misure rivolte esclusivamente alle imprese.

### Toscana

- **CSR Toscana / FEASR / ARTEA / LEADER-GAL** — presidio dedicato allo sviluppo rurale e territoriale con possibili beneficiari pubblici.

Il totale atteso della rete sale a circa **46 fonti configurate**, di cui **38 canali discovery**. Il numero reale e lo stato runtime vengono calcolati dal live-probe, non fissati nella UI.

## Evidenza ufficiale e scadenza della prova

`data/opportunity-coverage-evidence-v043.json` contiene una evidenza ufficiale per ciascuno degli undici nuovi canali. L'evidenza ha validità massima di **45 giorni**: trascorso il periodo senza nuova verifica, il gate v0.4.3 fallisce invece di trattare una prova storica come verità permanente.

Questo controllo non dichiara completezza del web. Dimostra però che le famiglie aggiunte non esistono soltanto nel contratto: hanno un programma, una call o un provvedimento ufficiale verificato.

## Sentinelle e audit review

Le sentinelle storiche includono:

- URBACT Action Networks 2026;
- EUI Innovative Actions — Call 4;
- Digital Europe — Innovative and Connected Public Administrations;
- CSR/LEADER 2026 con enti pubblici territoriali.

Restano invece in `audit_review`, quindi fuori dalla preview finché non è dimostrata l'applicabilità concreta ai sette Comuni:

- EUI City-to-City Exchanges — richiede classificazione DEGURBA 1 o 2;
- CEF Transport 2026 — servono pertinenza al topic/TEN-T e ruolo progettuale;
- Erasmus+ 2026 — va individuata la singola azione e il ruolo comunale;
- Horizon Europe 2026-2027 — va individuato il singolo topic e il partenariato;
- Protezione Civile — molte risorse transitano dalle Regioni;
- MASAF — la maggioranza delle misure è destinata ad imprese/operatori e non deve generare falsi positivi.

La regola è esplicita: **un portafoglio di programma non può pubblicare automaticamente una opportunità**.

## START Toscana

START non viene aggiunto al Radar Opportunità. È un sistema di e-procurement: gare, affidamenti e manifestazioni di interesse in cui l'amministrazione acquista lavori, beni o servizi non sono finanziamenti disponibili al Comune.

Il contratto continua quindi a escludere `procurement_where_municipality_is_contracting_authority` e `supplier_tender`. START potrà essere valutato in futuro per un eventuale radar separato su gare/lavori/attuazione, senza contaminare il perimetro dei finanziamenti.

## Independent audit v0.4.2 conservato

Restano attivi i tre holdout indipendenti e i tre falsi negativi baseline individuati il 22 agosto 2026:

- Vita & Opportunità 2026;
- CERV 2026 — Town Twinning;
- Potenziamento del servizio sociale professionale 2026.

Il loro recupero 3/3 misura la chiusura dei buchi noti, non un capture rate del 100%. Il capture rate prospettico resta separato e richiede almeno 20 casi indipendenti.

## UI

La v0.4.3 non reintroduce il buffet delle fonti. Restano:

- sintesi del quadro operativo;
- filtri Comune, Stato, Modalità, Fonte e ricerca libera;
- viewport con scroll interno delle opportunità;
- favicon con fallback testuale;
- nessuna esposizione di `discovery`, quality gate, hold o altri concetti tecnici interni.

## Gate CI

Il workflow `.github/workflows/opportunity-radar-v04.yml` esegue regressioni v0.3/v0.4.2, test v0.4.3, live-probe, audit e browser check desktop/mobile.

Codici bloccanti:

- `2` — continuity hold;
- `3` — backtest classificatore fallito;
- `5` — coverage contract/sentinelle fallite;
- `6` — independent audit/holdout non soddisfatto;
- `7` — copertura residua v0.4.3 non supportata da evidenza ufficiale recente.

## Stato

La v0.4.3 resta sperimentale nella Draft PR #82. Nessun merge, nessuna route pubblica e nessuna modifica alla sitemap pubblica sono autorizzati da questa iterazione.
