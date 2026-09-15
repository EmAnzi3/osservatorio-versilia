# Osservatorio Versilia

**Dati pubblici, confrontabili e verificabili per i sette Comuni della Versilia.**

Sito pubblico: **https://osservatorioversilia.it**

<!-- OV_PUBLIC_STATUS_START -->
Release corrente: **v1.40.0** — aggiornata **14 settembre 2026**.

## Stato del progetto

- **7 Comuni**: Camaiore, Forte dei Marmi, Massarosa, Pietrasanta, Seravezza, Stazzema e Viareggio;
- **11 aree tematiche**;
- **225 indicatori pubblicati**;
- **221 indicatori incorporati**: 219 con scheda autonoma e 2 con route dedicata;
- **4 indicatori climatici esterni**, integrati nell'esperienza del sito con storici separati;
- confronti territoriali, profili comunali, serie storiche e benchmark Versilia;
- benchmark Toscana/Italia quando la comparabilità metodologica è adeguata;
- esportazione CSV e stampa/PDF nelle viste che la supportano;
- approfondimenti dedicati, tra cui PNRR, Atlante economico/ATECO, Opportunità e Percorsi;
- Stato dati, metodologia, fonti e segnalazioni accessibili dal sito pubblico.
<!-- OV_PUBLIC_STATUS_END -->

## Metodo e qualità dei dati

Il registro canonico usato dal frontend è `data/site-data.json`. Gli indicatori elaborati dall'Osservatorio devono essere ricostruibili dagli snapshot e dalle formule conservati nel repository.

Principi di pubblicazione:

- la copertura ordinaria è **7/7 Comuni**;
- un valore ufficialmente assente, vuoto o non validabile resta **`n.d.`** e non viene trasformato in zero;
- uno zero è pubblicato come tale solo quando la fonte lo riporta esplicitamente;
- non vengono introdotte stime o interpolazioni per colmare dati comunali mancanti, salvo una metodologia esplicita e documentata;
- per gli indicatori pro capite con aggregato territoriale reale, il riferimento Versilia è calcolato come **somma dei numeratori / somma della popolazione**, non come media semplice dei sette valori pro capite;
- benchmark regionali e nazionali vengono mostrati solo quando definizione, periodo e unità sono confrontabili;
- ogni indicatore deve dichiarare almeno definizione, annualità, unità, fonte e URL della fonte.

Gli snapshot leggibili in `data/source-snapshots/` conservano, secondo il tipo di indicatore, valori ufficiali, perimetro territoriale, formule, serie, file originali o impronte delle fonti e motivazioni delle eventuali esclusioni.

## Cosa pubblica il sito

- `index.html` — homepage e accesso ai contenuti;
- `confronta/` — confronti per tema e indicatore;
- `comuni/` — profili dei sette Comuni;
- `indicatori/` — schede indicatore autonome generate dalla build, salvo route dedicate e indicatori esterni;
- `stato-dati/` — stato, annualità e copertura dei dati;
- `progetto/` — finalità e metodo del progetto;
- `segnala/` — canale per segnalazioni e correzioni;
- pagine e route dedicate per gli approfondimenti che richiedono una visualizzazione specifica.

La ricerca globale è disponibile anche tramite `/` e `Ctrl/Cmd+K`. Il sito include supporto tecnico PWA/offline e strumenti di accessibilità per contrasto, dimensione del testo e riduzione del movimento.

## Struttura del repository

- `data/site-data.json` — catalogo canonico e metadati del frontend;
- `data/source-snapshots/` — snapshot, dati grezzi e basi di audit versionate;
- `scripts/` — materializzatori, builder, audit e test;
- `assets/` — sorgenti e runtime dell'interfaccia;
- `docs/` — metodologia e documentazione dei singoli lotti o processi;
- `ci/build-materialization-contract.json` — contratto delle mutazioni ammesse durante la build;
- `ci/workflow-contract.json` — inventario dei workflow CI riconosciuti;
- `scripts/preflight_compile.txt` — inventario dei file Python sottoposti al controllo canonico.

Header, footer e navigazione globale sono trattati come componenti condivisi. I gate di coerenza verificano le pagine prodotte, i link interni, i metadata, la sitemap e le principali regressioni responsive/browser.

## Build e validazione

I comandi canonici sono:

```bash
python scripts/preflight.py --quick
python scripts/preflight.py --full
```

La build statica principale è prodotta da:

```bash
python scripts/build_static_brand.py
```

L'output pubblico viene generato in `dist/`. La pipeline verifica inoltre che la build non lasci mutazioni non dichiarate nei file sorgente.

## CI e pubblicazione

Il workflow `.github/workflows/pages.yml` gestisce il percorso canonico di verifica e pubblicazione. Le pull request verso `main` passano dai gate `quick` e `full`; dopo il merge su `main`, GitHub Pages costruisce e pubblica il sito sul dominio canonico **https://osservatorioversilia.it**.

I workflow specializzati sono registrati in `ci/workflow-contract.json`: un nuovo workflow non dichiarato o una violazione del contratto di build fa fallire il preflight.

Il controllo periodico delle fonti è separato dalla pubblicazione: può rilevare cambiamenti, registrare una nuova baseline o aprire una PR di revisione, ma non modifica né pubblica automaticamente dati senza passare dai gate del repository.

## Indicizzazione

Le schede indicatore autonome includono URL canonica, fonte, metodo, dati strutturati e breadcrumb; la build aggiorna sitemap e metadata per il dominio ufficiale. I quattro indicatori climatici esterni restano collegati agli approfondimenti storici dedicati senza duplicare nel catalogo principale dataset più pesanti.

## Licenze e attribuzioni

Testi, elaborazioni e visualizzazioni originali seguono quanto dichiarato nella pagina **Il progetto**. Dati, stemmi, fotografie e materiali di terzi conservano le condizioni d'uso e le licenze dei rispettivi titolari. Per usi ufficiali va sempre consultata la fonte originaria.
