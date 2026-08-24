# Osservatorio Versilia

Sito pubblico: **https://osservatorioversilia.it**

Versione dati corrente: **v1.17.0** — 24 agosto 2026.

Versione statica e autonoma dell'Osservatorio Versilia, ricostruita per GitHub Pages a partire dalle risorse pubbliche del precedente ChatGPT Site.

## Contenuto

- 7 schede comunali;
- 11 aree tematiche;
- 143 indicatori nel catalogo canonico: 139 con valori incorporati e 4 climatici con storici separati;
- confronti territoriali e riferimenti Versilia;
- benchmark Toscana/Italia quando la comparabilità è metodologicamente corretta;
- serie storiche nazionali, regionali e comunali;
- sottosezioni tematiche e dettagli analitici espandibili;
- navigazione contestuale tra temi e tra Comuni;
- ricerca globale;
- esportazione CSV e stampa/PDF;
- pagina del progetto e modulo `mailto:` per le segnalazioni.

La ricerca mobile usa un pannello a piena altezza con `100dvh`, pulsante di chiusura sempre visibile, supporto a `Escape` e chiusura tramite tasto Indietro del browser.

## Pubblicazione

Il sito è pubblicato con GitHub Pages tramite GitHub Actions e usa come dominio canonico **https://osservatorioversilia.it**.

1. Il repository mantiene il codice e i dati del sito.
2. In **Settings → Pages**, la sorgente è **GitHub Actions**.
3. Il workflow `.github/workflows/pages.yml` pubblica automaticamente il sito a ogni aggiornamento del ramo `main`, esclusivamente dopo build e test riusciti.
4. Canonical, JSON-LD, Open Graph, sitemap e `robots.txt` vengono generati usando il dominio ufficiale.

Il sito usa collegamenti relativi; l'indirizzo `emanzi3.github.io` resta soltanto l'infrastruttura tecnica sottostante di GitHub Pages e non è l'URL pubblico da indicizzare o condividere.

## Struttura

- `index.html`: homepage;
- `comuni/`: pagine dei sette Comuni;
- `confronta/`: pagine degli undici temi;
- `indicatori/`: 139 pagine canoniche generate in build, una per indicatore con dati incorporati;
- `data/site-data.json`: catalogo canonico dei 143 indicatori, con dati incorporati per 139 e riferimenti ai file storici separati per i 4 climatici;
- `data/source-registry.json`: perimetro e regole del controllo mensile;
- `data/source-monitor-state.json`: baseline approvata delle fonti monitorate;
- `data/source-snapshots/`: conteggi grezzi, serie comunali, formule, file originali e impronte delle fonti;
- `assets/app.js`: logica di caricamento per lo sviluppo;
- `assets/app-parts/`: moduli sorgente dell'applicazione;
- `assets/original.css`: base visuale storica;
- `assets/visual-grammar.css` e `assets/visual-grammar.js`: grammatica corrente dei confronti, riferimenti Versilia e scala di lettura;
- `assets/static.css`, `assets/fidelity.css` e `assets/fidelity.js`: adattamenti statici, responsive e integrazioni runtime;
- `assets/meteo-clima.css` e `assets/meteo-clima.js`: pagina editoriale Meteo e clima in bozza;
- `progetto/` e `segnala/`: pagine informative.

## Coerenza dell'interfaccia

Header, footer e navigazione globale hanno una fonte canonica in `assets/app-parts/00.txt`. Le pagine speciali riusano la stessa shell tramite `scripts/site_chrome.py`; il gate finale `scripts/test_site_consistency.py` controlla tutte le pagine prodotte, i link interni, i metadata e la sitemap dopo la materializzazione di Stato dati, PNRR e Percorsi.

Regole, profili ed eccezioni ammesse sono documentati in `docs/coerenza-interfaccia.md`. Una nuova pagina non classificata o una navigazione incompleta fanno fallire la pull request.

## Aggiornamento dei dati

Il catalogo e i metadati dei 143 indicatori sono centralizzati in `data/site-data.json`. Gli storici climatici più pesanti restano nei file dedicati richiamati da `dataStorage`. Per aggiornamenti strutturali conviene modificare o rigenerare questi dati mantenendo per ogni indicatore:

- definizione;
- anno;
- unità;
- fonte e URL;
- valori comunali;
- formula degli indicatori derivati;
- eventuale serie storica;
- eventuali benchmark Toscana/Italia.

Gli indicatori elaborati dall'Osservatorio devono essere ricostruibili dagli snapshot leggibili conservati in `data/source-snapshots/`. Gli snapshot riportano il perimetro territoriale, i conteggi o valori ufficiali utilizzati, le formule, le serie e i candidati esclusi.

La copertura standard è **7/7 Comuni**. Un indicatore può essere pubblicato con copertura **6/7** soltanto quando un unico Comune presenta un dato ufficiale mancante o non validabile; il valore resta `n.d.` e non viene stimato o ricostruito.

### Controllo mensile automatico

Il workflow `.github/workflows/monthly-data-refresh.yml` viene eseguito il giorno 5 di ogni mese e può essere avviato manualmente da GitHub Actions.

La procedura:

- valida tutti i 143 indicatori canonici, la ripartizione fra 139 valori incorporati e 4 storici climatici separati e la coerenza della copertura dichiarata;
- controlla metadati, formule, annualità e serie storiche;
- verifica la raggiungibilità delle fonti;
- rileva modifiche dei file ufficiali direttamente scaricabili;
- pubblica un rapporto nell'issue annuale `Registro controlli dati <anno>` menzionando `@EmAnzi3`;
- apre una PR in bozza quando deve essere registrata una nuova baseline o quando una fonte cambia.

Il controllo non modifica automaticamente i dati e non effettua merge. La procedura completa è descritta in `docs/aggiornamento-mensile-dati.md`.

Il registro assegna inoltre a ogni indicatore un profilo fonte esplicito: produttore, frequenza, finestra attesa di pubblicazione, metodo di acquisizione e condizioni di riuso. Il controllo mensile fallisce se un indicatore resta senza profilo.

La copertura e i criteri di ammissione delle serie comunali sono documentati in `docs/copertura-serie-storiche.md`.

## Indicizzazione e Search Console

La build genera una pagina autonoma per ciascuno dei 139 indicatori incorporati, con URL canonica, confronto comunale in ordine alfabetico, serie storica quando disponibile, fonte, metodo, dati strutturati `Dataset` e breadcrumb. Le URL sono incluse nella sitemap con `lastmod`.

I quattro indicatori climatici esterni sono integrati nell'esperienza Ambiente e rimandano all'approfondimento storico dedicato, senza duplicare i dataset più pesanti dentro `site-data.json`.

La configurazione operativa di Google Search Console e i controlli successivi al rilascio sono descritti in `docs/search-console.md`.

## Licenze e attribuzioni

Testi, elaborazioni e visualizzazioni originali seguono quanto dichiarato nella pagina **Il progetto**. Dati, stemmi, fotografia e materiali di terzi conservano le condizioni d'uso e le licenze dei rispettivi titolari. Per usi ufficiali va sempre consultata la fonte originaria.
