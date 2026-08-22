# Radar Opportunità Versilia — v0.3

La v0.3 è la prima espansione controllata dopo il consolidamento v0.2.5. La route resta **solo di anteprima**, `noindex` e fuori dalla sitemap: nessun merge e nessuna pubblicazione sono implicati da questo lavoro.

## Obiettivi

1. ampliare il bacino senza trasformare il radar in un aggregatore indiscriminato;
2. distinguere le **fonti operative** dai **canali di discovery**;
3. conservare deduplicazione, continuità, archivio e backtest v0.2.5;
4. rendere la preview più leggibile e dinamica, soprattutto nel Quadro operativo;
5. usare icone fonte affidabili e verificabili dal browser.

## Fonti operative

Sono monitorati come canali operativi autonomi:

- Regione Toscana — bandi aperti generalisti;
- **PR Toscana FESR 2021-2027**;
- **PR Toscana FSE+ 2021-2027**;
- Fondazione Cassa di Risparmio di Lucca;
- **Sviluppo Toscana**;
- **Ministero della Cultura — DG Spettacolo**;
- **Ministero dell'Interno — Prefetture**;
- PA Digitale 2026 resta accessoria e `degraded` finché il dataset selezionato rimane stale.

I canali FESR/FSE riusano la famiglia documentale `regione-toscana`: una scheda non viene promossa perché compare sul portale di programma, ma solo se trova una regola documentale valida. La deduplicazione cross-source assegna priorità al canale più specifico e collassa record equivalenti.

## Canali di discovery

Entrano in monitoraggio:

- ANCI Toscana;
- ANCI nazionale;
- GSE;
- Ministero dell'Interno — Finanza locale.

Questi canali **non possono alimentare direttamente l'output pubblico**. Un risultato produce solo una voce `discoveryQueue` interna; per diventare opportunità deve essere ricondotto alla fonte ufficiale del bando e passare le stesse verifiche su richiedente, ruolo del Comune, territorio, scadenza e documento ufficiale.

La v0.3 aggiunge il passaggio `discovery → fonte ufficiale → regola documentale → quality gate`, recuperando opportunità che nella prima iterazione restavano confinate nella coda interna.

## Opportunità recuperate nella v0.3

Fra i falsi negativi risolti e verificati documentalmente:

- **Patti per la sicurezza urbana / Videosorveglianza 2026** — Ministero dell'Interno;
- **Bando per la promozione della musica Jazz 2027** — Ministero della Cultura;
- **Avviso Mercati Rionali** — Sviluppo Toscana.

La videosorveglianza viene inoltre deduplicata semanticamente quando la stessa misura compare con titoli diversi.

## Icone e identità fonte

Le fonti con favicon remote affidabili continuano a usare il dominio ufficiale. Per le fonti che hanno mostrato problemi di caricamento la preview usa asset SVG locali versionati nel repository:

- Fondazione Cassa di Risparmio di Lucca;
- ANCI Toscana;
- Ministero dell'Interno;
- Sviluppo Toscana.

Gli asset sono serviti come `/assets/source-icons/*.svg`. Chromium verifica che siano realmente caricati (`naturalWidth > 0`), quindi la presenza del solo tag `<img>` non è sufficiente a far passare il collaudo.

## UI v0.3

Il Quadro operativo non usa più quattro box quasi indistinguibili sul fondo beige. È un pannello autonomo blu/petrolio con quattro card iconiche: opportunità aperte, fonti monitorate, Comuni coperti e archivio. Sotto compare una riga compatta delle fonti con icona e stato `Attiva`, `Discovery`, `Degradata` o `Errore`.

Anche le schede usano icone per Scadenza, Ruolo del Comune, Richiedente e Ambito. Il filtro Fonte mantiene il menu e aggiunge pulsanti rapidi con icona.

## Backtest

Il backtest è stato ampliato a **33 casi ufficiali**.

Risultato dell'ultimo run validato:

- precision: **100,0%**;
- recall: **94,1%**;
- F1: **97,0%**;
- esito: **PASS**.

Il falso negativo musei/ecomusei resta volutamente nel campione finché non esiste una mappa strutturata tra titolarità comunale e musei accreditati.

Soglie bloccanti invariate: precision >= 95%; recall >= 85%.

## Continuità

La v0.3 recupera lo stato precedente dagli artifact v0.3/v0.2.5/v0.2.4. Un'opportunità che scompare prima della propria scadenza produce `continuityHold` e rende rosso il workflow.

La continuità viene riconciliata **dopo** i recuperi documentali verificati: un bando recuperato nella fase finale non può risultare contemporaneamente presente nell'output corrente e in `continuityHold`.

## Ultimo live probe validato — 22 agosto 2026

- candidati raccolti: **92**;
- opportunità correnti uniche: **14**;
- eligible: **6**;
- conditional: **8**;
- archivio: **0**;
- continuity hold: **0**;
- duplicati collassati: **2**;
- fonti configurate: **12**;
- fonti attive: **11**;
- fonti attive sane: **9**;
- fonti degradate: **2**;
- canali discovery: **4**;
- coda discovery interna: **35**.

Stato discovery dell'ultimo probe:

- ANCI Toscana: `ok`;
- ANCI nazionale: `error`;
- GSE: `degraded`;
- Ministero dell'Interno / Finanza locale: `ok`.

Il degrado o errore di un canale discovery non promuove né rimuove opportunità operative.

## Collaudo

Il workflow dedicato `.github/workflows/opportunity-radar-v03.yml` valida:

- motore e regole;
- post-processing v0.3;
- backtest;
- live probe delle fonti operative e discovery;
- deduplicazione;
- continuità;
- build canonica;
- Chromium desktop/mobile;
- controllo overflow;
- caricamento reale delle icone;
- filtri e Quadro operativo;
- packaging della preview.

Ultimo run validato: **32571826653**, completamente verde (`test`, `live-probe`, `browser-preview`).

## Stato

La v0.3 resta nella Draft PR #82. Nessun merge, nessuna route pubblica e nessuna modifica alla sitemap pubblica.
