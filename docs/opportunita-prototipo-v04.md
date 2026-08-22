# Radar Opportunità Versilia — v0.4 coverage-first

La v0.4 cambia la domanda di collaudo: non basta più verificare che il motore classifichi bene ciò che ha già trovato. Il radar deve anche dimostrare di monitorare le principali **famiglie di opportunità** accessibili ai Comuni e deve rendere espliciti i buchi di copertura.

La route resta esclusivamente di anteprima, `noindex,nofollow,noarchive`, fuori dalla sitemap e dalla navigazione pubblica. La Draft PR #82 non implica merge o pubblicazione.

## Perché la v0.3 non bastava

Il backtest v0.3 misura precision e recall sui candidati osservati. Il suo stesso dataset specifica che non misura la completezza dell'intero web. Un recall elevato può quindi convivere con opportunità mai intercettate perché la relativa famiglia di fonti non viene monitorata.

La v0.4 conserva il classificatore v0.3 e aggiunge un audit distinto di **coverage**.

## Contratto di copertura

Sono considerate opportunità pertinenti:

- bandi e contributi;
- incentivi;
- avvisi competitivi;
- manifestazioni di interesse;
- premi e programmi finanziari;
- misure a sportello.

Sono escluse le normali gare in cui il Comune è stazione appaltante o acquirente: una gara per comprare beni o servizi non è un finanziamento o un'opportunità finanziaria per il Comune. Una procedura competitiva alla quale il Comune può invece candidarsi, partecipare o ricevere risorse resta nel perimetro.

Il contratto è versionato in `data/opportunity-coverage-contract-v04.json`.

## Tre stati operativi

La v0.4 distingue:

1. **Aperta** — finestra di candidatura attualmente attiva;
2. **A sportello** — misura accessibile senza una singola scadenza di bando;
3. **In arrivo** — procedura già annunciata da una fonte ufficiale ma non ancora aperta.

Questo evita due errori opposti: perdere incentivi permanenti perché non hanno una deadline, oppure mostrare come aperto un bando soltanto annunciato.

## Espansione discovery

Ai quattro canali discovery v0.3 si aggiungono venti canali complessivi di discovery, includendo:

- Conferenza Stato-Città;
- MiC — Direzione generale Creatività Contemporanea;
- Ministero della Cultura — rete generale avvisi;
- PCM — Dipartimento per le politiche del mare;
- PCM — Dipartimento per lo Sport;
- PCM — Dipartimento per le politiche della famiglia;
- PCM — Dipartimento per le pari opportunità;
- PCM — Dipartimento Casa Italia;
- PCM — Politiche di coesione;
- MIT — finanziamenti per enti locali;
- MASE — bandi e avvisi;
- Commissione europea / CINEA — LIFE;
- Commissione europea — Funding & Tenders;
- New European Bauhaus;
- Interreg Italia-Francia Marittimo;
- PA digitale 2026 — pagina corrente dedicata ai Comuni.

I canali restano **discovery**: non possono promuovere automaticamente una scheda nella preview. Per l'output serve comunque una fonte primaria ufficiale, la verifica del ruolo comunale e la matrice Comune-per-Comune.

## Famiglie minime coperte

L'audit richiede almeno una fonte configurata per ciascuna di dodici famiglie:

- Regione Toscana e programmi regionali;
- canali nazionali trasversali per enti locali;
- cultura;
- infrastrutture e mobilità;
- energia, clima e ambiente;
- sport e infrastrutture sociali;
- mare e Comuni costieri;
- famiglia, welfare e pari opportunità;
- resilienza, prevenzione e patrimonio pubblico;
- transizione digitale PA;
- programmi UE diretti;
- cooperazione territoriale.

La presenza della fonte non equivale a dichiararla sana: l'audit conserva separatamente lo stato runtime degli endpoint. Un sito che blocca il collector deve risultare degradato/errore, non essere sostituito da una falsa copertura.

## Sentinelle di copertura

La v0.4 introduce casi sentinella separati dal backtest del classificatore.

### Correnti al 22 agosto 2026

- **Cultura nei piccoli comuni — Edizione 1** — MiC DG Creatività Contemporanea — `Aperta`;
- **Capitale italiana del mare 2027** — PCM Politiche del mare — `Aperta`;
- **Conto Termico 3.0 — incentivi per edifici comunali** — GSE — `A sportello`;
- **Fondo investimenti stradali piccoli Comuni — bando 2026** — MIT — `In arrivo`;
- **Co-create New European Bauhaus 2026** — UE — `Aperta`;
- **Crescere nei piccoli comuni 2026** — PCM Politiche per la famiglia — `Aperta`;
- **Bando n. 8/2026 — progetti territoriali contro tratta e grave sfruttamento** — PCM Pari opportunità — `Aperta`.

Le sentinelle correnti sono materializzate solo dopo verifica della fonte primaria. Per resistere a un guasto transitorio del sito ufficiale è consentito un fallback sull'evidenza versionata per un massimo di sette giorni; oltre tale finestra la sentinella va in `coverageHold` e l'audit fallisce.

### Storiche

- **Sport e Periferie 2026** — il relativo canale PCM Sport deve essere monitorato anche se la finestra si è chiusa il 25 giugno 2026;
- **Interreg Italia-Francia Marittimo — V Avviso** — sentinella per la cooperazione territoriale, chiusa il 23 luglio 2026;
- **Avviso Aree interne in zone sismiche 1 e 2** — sentinella Casa Italia per resilienza e prevenzione, chiusa il 4 giugno 2026.

Questi casi non devono riapparire come opportunità aperte; servono a dimostrare che la famiglia non è più fuori dal radar.

## Matrice territoriale

Le nuove sentinelle non vengono applicate automaticamente a tutti e sette i Comuni.

Esempi:

- Cultura nei piccoli Comuni applica la soglia demografica del bando Comune-per-Comune;
- Capitale italiana del mare viene limitata ai Comuni costieri della Versilia;
- Conto Termico 3.0 distingue il regime rafforzato legato alla soglia dei 15.000 abitanti dai requisiti ordinari della misura;
- il futuro Fondo MIT piccoli Comuni espone Stazzema come caso condizionale, in attesa del testo definitivo 2026;
- Co-create NEB resta condizionale perché richiede un partenariato conforme alla call;
- Crescere nei piccoli comuni applica la soglia di 5.000 abitanti e rende Stazzema il caso direttamente ammissibile nel perimetro Versilia;
- il Bando n. 8/2026 mantiene tutti i sette Comuni `conditional` perché l'essere ente locale non sostituisce i requisiti progettuali e organizzativi.

## UI v0.4

Il Quadro operativo mostra separatamente:

- Aperte;
- A sportello;
- In arrivo;
- fonti monitorate;
- famiglie coperte;
- archivio.

È aggiunto il filtro **Stato**. Restano i filtri Comune, fonte, modalità e ricerca libera.

## Gate CI

Il workflow `.github/workflows/opportunity-radar-v04.yml` esegue:

- test del motore v0.3 per evitare regressioni;
- test specifici del contratto di copertura v0.4;
- test delle matrici territoriali delle sentinelle;
- backtest del classificatore, mantenuto separato dalla coverage;
- live probe delle fonti operative e discovery;
- verifica delle sentinelle correnti;
- verifica delle sentinelle storiche di famiglia;
- esclusione esplicita del procurement che non costituisce opportunità per il Comune;
- build della preview;
- Chromium desktop/mobile;
- filtro degli stati e controllo overflow;
- packaging dell'anteprima locale.

Codici bloccanti v0.4:

- `2` — continuity hold;
- `3` — backtest classificatore fallito;
- `5` — contratto di copertura o sentinelle non soddisfatti.

## Stato

La v0.4 resta sperimentale nella Draft PR #82. Nessun merge, nessuna route pubblica e nessuna modifica alla sitemap pubblica sono autorizzati da questa iterazione.
