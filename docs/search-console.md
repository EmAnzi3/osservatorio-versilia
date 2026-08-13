# Google Search Console

Il sito espone la sitemap canonica all'indirizzo:

`https://osservatorioversilia.it/sitemap.xml`

La build include 132 URL indicizzabili:

- homepage;
- 7 schede comunali;
- 10 confronti tematici;
- 111 pagine indicatore;
- pagina del progetto;
- pagina delle segnalazioni.

## Attivazione

1. Aprire [Google Search Console](https://search.google.com/search-console/).
2. Creare una proprietà di tipo **Dominio** per `osservatorioversilia.it`.
3. Copiare il record TXT fornito da Google nel DNS del dominio.
4. Completare la verifica in Search Console.
5. Aprire **Indicizzazione → Sitemap** e inviare `sitemap.xml`.

La verifica DNS è preferibile perché copre automaticamente dominio, protocollo e sottodomini e non richiede di inserire token nella repository.

## Controlli dopo il rilascio

Nei primi giorni verificare con **Controllo URL** almeno:

- `/`;
- `/comuni/massarosa/`;
- `/confronta/demografia/`;
- `/indicatori/popolazione-residente/`;
- `/indicatori/tasso-di-disoccupazione/`;
- `/indicatori/persone-con-almeno-una-patologia-cronica/`.

Dopo quattro settimane esportare dal rapporto **Rendimento**:

- query;
- pagina;
- clic;
- impressioni;
- CTR;
- posizione media.

Questi dati devono guidare titoli, descrizioni e futuri approfondimenti. Non va aperto un blog generico prima di sapere quali ricerche portano davvero gli utenti al sito.

## Regole tecniche

- una sola URL canonica per indicatore;
- nessuna pagina separata comune × indicatore finché non esiste contenuto realmente distinto;
- `lastmod` allineato alla versione dei dati;
- pagine query dei confronti e dei comuni subordinate alle rispettive canonical;
- dati strutturati `Dataset` e `BreadcrumbList` validati in CI.

Riferimenti ufficiali:

- [Introduzione a Search Console](https://developers.google.com/search/docs/monitor-debug/search-console-start);
- [Dati strutturati Dataset](https://developers.google.com/search/docs/appearance/structured-data/dataset);
- [Creare e inviare una sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap).
