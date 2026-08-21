# Radar Opportunità Versilia — v0.3

La v0.3 è la prima espansione controllata dopo il consolidamento v0.2.5. La route resta **solo di anteprima**, `noindex` e fuori dalla sitemap: nessun merge e nessuna pubblicazione sono implicati da questo lavoro.

## Obiettivi

1. ampliare il bacino senza trasformare il radar in un aggregatore indiscriminato;
2. distinguere le **fonti operative** dai **canali di discovery**;
3. conservare deduplicazione, continuità, archivio e backtest v0.2.5;
4. rendere la preview più leggibile e dinamica, soprattutto nel Quadro operativo;
5. usare favicon ufficiali delle fonti con fallback grafico locale.

## Fonti operative

Entrano come canali autonomi:

- Regione Toscana — bandi aperti generalisti;
- **PR Toscana FESR 2021-2027**;
- **PR Toscana FSE+ 2021-2027**;
- Fondazione Cassa di Risparmio di Lucca;
- PA Digitale 2026 resta accessoria e `degraded` finché il dataset selezionato rimane stale.

I canali FESR/FSE riusano la famiglia documentale `regione-toscana`: una scheda non viene promossa perché compare sul portale di programma, ma solo se trova una regola documentale valida. La deduplicazione cross-source assegna priorità al canale di programma quando lo stesso bando compare anche nella pagina regionale generalista.

## Canali di discovery

Entrano in monitoraggio:

- ANCI Toscana;
- ANCI nazionale;
- GSE;
- Ministero dell'Interno — Finanza locale.

Questi canali **non possono alimentare direttamente l'output pubblico**. Un risultato produce solo una voce `discoveryQueue` interna; per diventare opportunità deve essere ricondotto alla fonte ufficiale del bando e passare le stesse verifiche su richiedente, ruolo del Comune, territorio, scadenza e documento ufficiale.

Per GSE questo approccio è deliberatamente prudente: una news o FAQ può segnalare una misura utile, ma non basta a stabilire che la finestra sia effettivamente aperta in quel momento.

## Favicon e identità fonte

La matrice di presentazione e quella di copertura registrano il favicon del dominio ufficiale. La UI usa il favicon nella testata delle schede, nei filtri rapidi, nel pannello delle fonti monitorate e nell'archivio. Se il favicon remoto non è disponibile resta visibile il fallback con le iniziali della fonte.

## UI v0.3

Il Quadro operativo non usa più quattro box quasi indistinguibili sul fondo beige. È un pannello autonomo blu/petrolio con quattro card iconiche: opportunità aperte, fonti monitorate, Comuni coperti e archivio. Sotto compare una riga compatta delle fonti con favicon e stato `Attiva`, `Discovery`, `Degradata` o `Errore`.

Anche le schede usano icone per Scadenza, Ruolo del Comune, Richiedente e Ambito. Il filtro Fonte mantiene il menu e aggiunge pulsanti rapidi con favicon.

## Backtest

Il backtest passa da 24 a **28 casi**, includendo esplicitamente i nuovi source id FESR/FSE per controllare che l'alias documentale non cambi il giudizio. Il falso negativo musei/ecomusei resta volutamente nel campione finché non esiste una mappa strutturata tra titolarità comunale e musei accreditati.

Soglie bloccanti invariate: precision >= 95%; recall >= 85%.

## Continuità

La v0.3 recupera lo stato precedente dagli artifact v0.3/v0.2.5/v0.2.4. Un'opportunità che scompare prima della propria scadenza produce `continuityHold` e rende rosso il workflow.

## Collaudo

Il workflow dedicato `.github/workflows/opportunity-radar-v03.yml` deve superare test del motore, backtest, live probe delle fonti operative e discovery, build canonica, Chromium desktop/mobile, controllo overflow, favicon, filtri e nuovo Quadro operativo.

## Stato

La v0.3 resta nella Draft PR #82. Nessun merge, nessuna route pubblica e nessuna modifica alla sitemap pubblica.
