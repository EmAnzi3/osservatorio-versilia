# Radar Opportunità Versilia — v0.4.2 independent coverage audit

La v0.4.2 aggiunge un controllo non autoreferenziale alla v0.4 coverage-first. Il fatto che tutte le famiglie definite dal radar risultino presidiate non è sufficiente a dimostrare l'assenza di buchi: l'universo delle fonti deve essere messo alla prova anche dall'esterno.

La route resta esclusivamente di anteprima, `noindex,nofollow,noarchive`, fuori sitemap e navigazione pubblica. La Draft PR #82 non implica merge o pubblicazione.

## Quattro misure diverse

1. **Backtest classificatore** — precision/recall sui candidati già osservati; non misura la completezza del web.
2. **Coverage contract** — verifica che le principali famiglie istituzionali siano presidiate e che le sentinelle note siano gestite correttamente.
3. **Independent audit** — usa sweep e fonti di controllo che non alimentano direttamente il collector per cercare falsi negativi.
4. **Capture rate prospettico** — quota delle opportunità pertinenti emerse dal campione indipendente che il radar aveva già intercettato; diventa KPI solo dopo un campione minimo di 20 casi.

## Famiglie presidiate

Il contratto passa da 12 a 18 famiglie. Alle precedenti si aggiungono:

- disabilità e inclusione;
- turismo ed enti territoriali;
- politiche giovanili e Servizio civile;
- lavoro e servizi sociali;
- istruzione, edilizia e servizi scolastici;
- capacità amministrativa dei Comuni.

Le nuove fonti di produzione/discovery includono PCM Disabilità, Ministero del Turismo, PCM Politiche giovanili e SCU, Ministero del Lavoro, MIM, Funzione Pubblica e un canale CERV dedicato. Il canale CERV tematico affianca Funding & Tenders perché il portale generale può non essere enumerabile in modo affidabile dal collector HTML.

## Holdout indipendenti

Tre fonti sono deliberatamente escluse dalla raccolta di produzione e servono soltanto al controllo:

- Invitalia — incentivi e strumenti;
- CERV Italia — National Contact Point;
- Europe Direct Lucca-Viareggio.

Un holdout può confermare un'opportunità o far emergere un falso negativo, ma non può pubblicare automaticamente una scheda.

## Falsi negativi baseline del 22 agosto 2026

Lo sweep indipendente ha trovato tre opportunità correnti che la v0.4.1 non conteneva:

- **Vita & Opportunità 2026** — PCM Disabilità — scadenza 29 agosto 2026 ore 17:00;
- **CERV 2026 — Town Twinning** — Commissione europea — scadenza 23 settembre 2026 ore 17:00;
- **Potenziamento del servizio sociale professionale 2026** — Ministero del Lavoro — adesioni fino all'11 settembre 2026.

Questi tre casi sono versionati come `missed at baseline`. La v0.4.2 deve chiuderli 3/3 per passare il gate, ma questo **non** viene presentato come capture rate 100%: il campione è stato costruito appositamente cercando buchi e quindi non è rappresentativo.

### Controlli territoriali

- Vita & Opportunità distingue Stazzema, classificato `D - Intermedio` nella Mappa nazionale Aree interne AI 2020, dagli altri Comuni. Stazzema può rientrare nella candidatura diretta degli Enti locali; gli altri restano condizionali come partner secondo la rettifica ufficiale dell'Avviso.
- Town Twinning mantiene tutti i sette Comuni condizionali perché richiede un partenariato transnazionale conforme alla call.
- L'avviso assistenti sociali mantiene tutti i sette Comuni condizionali perché l'adesione richiede delega all'ATS, impegno assunzionale e disponibilità delle risorse previste.

## Casi non pubblicati

La v0.4.2 introduce anche `audit_review`. Un caso in questa classe resta fuori dalla preview finché non viene verificato il requisito che determina l'ammissibilità.

Primo caso: **Servizio civile universale — programmi e progetti 2026**. La finestra è aperta, ma l'accesso dipende dall'iscrizione/accreditamento utile dell'ente proponente all'Albo SCU. Il semplice fatto che un Comune ospiti sedi o progetti non basta per pubblicarlo come opportunità direttamente utilizzabile.

Le sentinelle storiche presidiano inoltre i cicli FUNT Turismo, MIM/edilizia scolastica e Funzione Pubblica senza ripubblicare finestre già chiuse.

## Capture rate e detection lag

Il file `data/opportunity-independent-audit-v042.json` definisce:

- target capture rate prospettico: **95%**;
- campione minimo prima di esporre il KPI: **20 casi**;
- target detection lag mediano: **3 giorni**.

Fino al raggiungimento del campione minimo la UI deve mostrare `capture rate prospettico: in raccolta`, non una percentuale artificiale.

## UI v0.4.2

La preview non espone più il buffet completo delle fonti né i chip duplicati sopra i filtri. Il Quadro operativo mostra invece una sintesi della rete, delle famiglie presidiate e dell'audit indipendente.

Restano i filtri Comune, Fonte, Stato, Modalità e ricerca libera. Le opportunità sono contenute in un viewport con scroll verticale interno: l'aumento del numero di schede non deve allungare indefinitamente la pagina e allontanare il footer.

Le favicon esterne che falliscono vengono eliminate e lasciano visibile il fallback testuale della fonte.

## Gate CI

Il workflow `.github/workflows/opportunity-radar-v04.yml` esegue:

- regressioni v0.3 e v0.4;
- validazione dei registri v0.4.2;
- verifica delle 18 famiglie;
- verifica delle sentinelle correnti/storiche e degli `audit_review`;
- live probe del collector;
- probe delle fonti holdout senza alimentare la produzione;
- chiusura dei falsi negativi baseline;
- backtest del classificatore separato dalla coverage;
- build della preview e browser check desktop/mobile;
- verifica dello scroll interno delle opportunità e dell'assenza dei buffet fonti.

Codici bloccanti:

- `2` — continuity hold;
- `3` — backtest classificatore fallito;
- `5` — coverage contract/sentinelle fallite;
- `6` — audit indipendente non soddisfatto o nessun holdout raggiungibile nel live run.

## Stato

La v0.4.2 resta sperimentale nella Draft PR #82. Nessun merge, nessuna route pubblica e nessuna modifica alla sitemap pubblica sono autorizzati da questa iterazione.
