# Osservatorio Versilia

Versione statica e autonoma dell'Osservatorio Versilia, ricostruita per GitHub Pages a partire dalle risorse pubbliche del precedente ChatGPT Site.

## Contenuto

- 7 schede comunali;
- 9 aree tematiche;
- 69 indicatori;
- confronti territoriali e benchmark disponibili;
- serie storiche;
- sottosezioni tematiche e dettagli analitici espandibili;
- navigazione contestuale tra temi e tra Comuni;
- ricerca globale;
- esportazione CSV e stampa/PDF;
- pagina del progetto e modulo `mailto:` per le segnalazioni.

La ricerca mobile usa un pannello a piena altezza con `100dvh`, pulsante di chiusura sempre visibile, supporto a `Escape` e chiusura tramite tasto Indietro del browser.

## Pubblicazione

1. Creare su GitHub un repository vuoto, preferibilmente `osservatorio-versilia`.
2. Caricare nella radice del repository **il contenuto di questa cartella**, non la cartella contenitore.
3. Aprire **Settings → Pages**.
4. In **Build and deployment → Source**, selezionare **GitHub Actions**.
5. Il workflow `.github/workflows/pages.yml` pubblicherà automaticamente il sito a ogni aggiornamento del ramo `main`, esclusivamente dopo build e test riusciti.

Il sito usa collegamenti relativi e funziona sia come GitHub Project Page sia con un eventuale dominio personalizzato.

## Struttura

- `index.html`: homepage;
- `comuni/`: pagine dei sette Comuni;
- `confronta/`: pagine dei nove temi;
- `data/site-data.json`: dati e metadati degli indicatori;
- `assets/app.js`: logica di caricamento per lo sviluppo;
- `assets/app-parts/`: moduli sorgente dell'applicazione;
- `assets/original.css`: stile recuperato dal sito pubblico;
- `assets/static.css` e `assets/fidelity.css`: adattamenti statici, responsive e navigazione contestuale;
- `progetto/` e `segnala/`: pagine informative.

## Aggiornamento dei dati

I valori sono centralizzati in `data/site-data.json`. Per aggiornamenti strutturali conviene modificare o rigenerare questo file, mantenendo per ogni indicatore:

- definizione;
- anno;
- unità;
- fonte e URL;
- valori comunali;
- formula degli indicatori derivati;
- eventuale serie storica;
- eventuali benchmark Toscana/Italia.

## Licenze e attribuzioni

Testi, elaborazioni e visualizzazioni originali seguono quanto dichiarato nella pagina **Il progetto**. Dati, stemmi, fotografia e materiali di terzi conservano le condizioni d'uso e le licenze dei rispettivi titolari. Per usi ufficiali va sempre consultata la fonte originaria.
