# Radar Opportunità Versilia — prototipo

## Obiettivo

Verificare se un collettore automatico può individuare opportunità finanziarie realmente utilizzabili dai sette Comuni della Versilia senza introdurre rumore o false certezze.

Il prototipo è intenzionalmente separato dalla parte pubblica del sito: non crea route, non modifica `data/site-data.json`, non entra nella sitemap e non pubblica automaticamente opportunità.

## Perimetro v0.1

Comuni: Camaiore, Forte dei Marmi, Massarosa, Pietrasanta, Seravezza, Stazzema e Viareggio.

Prime fonti:

1. Regione Toscana — bandi aperti;
2. Fondazione Cassa di Risparmio di Lucca — bandi in corso;
3. PA digitale 2026 — dataset open data degli avvisi selezionato nel prototipo.

## Regola di sicurezza sull'ammissibilità

Il motore non usa inferenze generative per dichiarare ammissibile un Comune.

- `eligible`: la fonte cita esplicitamente Comuni, enti locali o amministrazioni pubbliche locali;
- `conditional`: sono ammessi soggetti pubblici ma esistono condizioni/partenariati da verificare;
- `review`: il testo disponibile non basta;
- `not_relevant`: i destinatari espliciti non sono amministrazioni comunali e l'elemento viene escluso dall'output operativo.

Una futura interfaccia dovrà mostrare la motivazione e la fonte, non soltanto l'etichetta.

## Collaudo live — 21 agosto 2026

Il live probe è stato eseguito su GitHub Actions usando `Europe/Rome` come riferimento temporale.

Esito tecnico:

- test automatici: verdi;
- live probe: verde;
- Regione Toscana: 40 opportunità trattenute;
- Fondazione CR Lucca: 2 opportunità trattenute;
- PA digitale 2026, sul dataset selezionato nella v0.1: 0 opportunità correnti trattenute.

Output complessivo:

- 42 opportunità;
- 7 `eligible`;
- 1 `conditional`;
- 34 `review`.

### Difetti emersi e corretti durante il collaudo

1. Il parser degli importi di Regione Toscana poteva fallire su valori non numerici o punteggiatura: ora l'estrazione è tollerante e non interrompe il collector.
2. Il parser HTML generico della Fondazione CR Lucca intercettava titoli di servizio come “Informazioni e contatti” e non i due bandi reali: ora usa i `Grant` JSON-LD della pagina ufficiale.
3. Il testo dell'intera pagina poteva contaminare l'ammissibilità, per esempio un footer contenente la parola “Comuni”: il filtro di qualità estrae sezioni mirate come Destinatari/Beneficiari.
4. Il workflow usava implicitamente la data UTC: ora il riferimento giornaliero è esplicitamente `Europe/Rome`.

### Casi correttamente intercettati

Tra i risultati del probe:

- Bando Amianto Edifici Pubblici 2026 — `eligible`, scadenza 31 agosto 2026;
- Nidi di qualità 2026-2027 — `eligible`, scadenza 4 settembre 2026;
- Fondazione CR Lucca, Progett-Azioni — `conditional`, scadenza 11 settembre 2026;
- Fondazione CR Lucca, Progettare per il futuro – opere pubbliche — `eligible`, scadenza 11 settembre 2026;
- Avviso Comuni Toscana Diffusa — rilevato come opportunità comunale, ma il vincolo territoriale dimostra che serve una verifica per singolo Comune.

## Limiti emersi

Il prototipo è tecnicamente funzionante ma non è ancora pronto per essere esposto pubblicamente.

### 1. Troppo rumore nella coda `review`

34 record su 42 richiedono ancora verifica. La pagina bandi aperti di Regione Toscana contiene opportunità per destinatari molto diversi. La coda `review` deve diventare una coda interna di controllo, non materiale da mostrare all'utente.

### 2. Ammissibilità da calcolare per singolo Comune

La regola “bando destinato ai Comuni = tutti i sette Comuni” è insufficiente. Alcuni avvisi aggiungono vincoli territoriali, dimensionali, demografici o di partenariato. Il caso Toscana Diffusa è il primo controesempio concreto.

La v0.2 deve quindi produrre, per ogni opportunità e Comune:

- stato: `eligible`, `not_eligible`, `conditional`, `review`;
- motivazione;
- regola documentale da cui deriva lo stato.

### 3. Freschezza delle fonti

Il dataset PA digitale 2026 scelto per la v0.1 non fornisce copertura corrente sufficiente per il radar. Prima di considerare affidabile una fonte machine-readable bisogna registrarne e controllarne anche la freschezza, non solo la raggiungibilità HTTP.

## Criteri per passare alla v0.2

Prima di aggiungere molte altre fonti:

1. introdurre il resolver di ammissibilità per singolo Comune;
2. introdurre metadata e controllo di freschezza per ogni fonte;
3. tenere `review` come coda interna e non come output pubblico;
4. migliorare il filtro Regione Toscana fino a ridurre sensibilmente il rumore;
5. ripetere lo stesso live probe e misurare precisione e falsi positivi/negativi;
6. solo dopo valutare FESR/FSE+, GSE, ANCI, Ministeri, LIFE/UE e Interreg.

## Stato

**Prototipo valido come base tecnica, non ancora pronto per pubblicazione o merge come funzionalità pubblica.**
