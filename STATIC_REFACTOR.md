# Pipeline statica pre-renderizzata

Il sito pubblico dell’Osservatorio Versilia viene generato con una build statica pre-renderizzata e distribuito tramite GitHub Pages.

## Stato attuale

- i sorgenti pubblicati sono conservati direttamente nel repository in formato leggibile;
- `data/site-data.json` contiene il dataset effettivamente usato dalla build;
- `assets/app-core.js` contiene il sorgente JavaScript unico dell’applicazione;
- `assets/static.css`, `assets/fidelity.css` e `assets/fidelity.js` sono revisionabili normalmente tramite diff Git;
- non vengono applicati payload Base64 o archivi opachi durante il deploy;
- la build genera un unico `assets/app-bundle.js` cacheabile;
- l’HTML completo viene prodotto con Playwright in fase di build;
- canonical URL, JSON-LD e `sitemap.xml` vengono generati automaticamente.

## Pipeline di pubblicazione

Il workflow `.github/workflows/pages.yml`, attivato dai push su `main`, esegue nell’ordine:

1. installazione degli strumenti di build;
2. generazione del sito pre-renderizzato in `dist/`;
3. test di regressione desktop, mobile e senza JavaScript;
4. controlli specifici sulla versione dei dati, sui 106 indicatori, sui 10 temi e sui 7 Comuni;
5. pubblicazione su GitHub Pages soltanto se tutti i controlli sono superati.

Lo stesso workflow viene eseguito sulle pull request verso `main`, senza alcun job di pubblicazione.

## Comandi locali

```bash
python scripts/build_static_safe.py
python scripts/test_static.py
python scripts/test_release_v170_compat.py
```

L’output locale viene scritto in `dist/`.

## Principi di manutenzione

- ogni cambiamento ai dati o al codice deve essere visibile nel diff della pull request;
- il contenuto di `main` deve rappresentare direttamente ciò che viene compilato e pubblicato;
- per congelare una versione approvata si usano commit, tag e branch Git;
- file codificati o archiviati possono essere utilizzati come artefatti temporanei di build, non come sorgente nascosta della produzione.
