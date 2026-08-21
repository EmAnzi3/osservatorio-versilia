# Radar Opportunità Versilia — v0.2.4

## Obiettivo

La v0.2.4 trasforma la preview tecnica in una vista più vicina a uno strumento operativo per amministratori, mantenendo separati i concetti interni del motore dalla UI.

La route resta `/opportunita-preview/`, `noindex,nofollow,noarchive`, fuori dalla sitemap e dalla navigazione pubblica. La PR #82 resta Draft.

## Semantica pubblica

Non vengono più esposti:

- `Quality gate`;
- `review` / `Review residua`;
- `Da verificare`;
- `Perché compare` / evidenze tecniche del classificatore.

La distinzione utile resta quella della **modalità di partecipazione**:

- `Candidatura diretta` quando il Comune ha un canale operativo diretto documentato;
- un requisito concreto quando serve una condizione specifica, ad esempio `Richiede partenariato`, `Partecipazione tramite Sistema Museale`, `Richiede superficie ammissibile`.

Un dubbio sull'ammissibilità non viene quindi trasformato in una pillola pubblica: resta nella review interna.

## PDF-first sui casi ambigui

La pagina HTML ufficiale resta la prima fonte. Se, dopo la lettura della pagina di dettaglio, il candidato rimane in `review`, `scripts/opportunity_pdf_evidence.py`:

1. individua al massimo due allegati pertinenti (bando, avviso, decreto, disciplinare, linee guida);
2. legge il PDF con `pypdf`;
3. cerca le sezioni `Soggetti beneficiari`, `Destinatari / beneficiari`, `Soggetti ammissibili`, `Chi può presentare domanda` e varianti;
4. riprova la classificazione usando quell'evidenza.

Se neppure il documento ufficiale consente una classificazione affidabile, il caso resta interno.

## Presentazione e colori

`data/opportunity-presentation-v024.json` mantiene separati i metadati editoriali dalla logica di ammissibilità.

Le card sono differenziate per ambito con accenti distinti:

- ambiente;
- istruzione;
- sociale;
- cultura;
- opere;
- territorio;
- mobilità;
- abitare.

La fonte è identificata con un marchio-sorgente compatto (`RT`, `FCRL`, ecc.) e il nome completo. Non vengono incorporati marchi istituzionali esterni non necessari al prototipo.

## Contenuto delle card

Ogni opportunità aperta mostra:

- fonte;
- titolo;
- descrizione sintetica dell'intervento finanziato;
- scadenza e, quando documentato, orario;
- ruolo del Comune;
- soggetto che presenta domanda;
- ambito geografico;
- requisito specifico, solo quando esiste;
- matrice dei sette Comuni;
- destinatari finali;
- collegamento alla fonte ufficiale.

I valori testuali provenienti dal motore vengono presentati con iniziale maiuscola.

## Filtri

La preview v0.2.4 consente di filtrare per:

- Comune;
- fonte;
- modalità di partecipazione;
- ricerca testuale.

## Scadenze con orario

Lo strato v0.2.4 recupera l'orario quando compare nell'evidenza sorgente e corrisponde alla stessa data di scadenza. Nel campione corrente sono stati rilevati, tra gli altri:

- Amianto: 31/08/2026 ore 16:00;
- Toscanaincontemporanea: 23/09/2026 ore 12:00;
- Sistemi museali: 25/09/2026 ore 23:59;
- Risorse genetiche forestali: 30/09/2026 ore 13:00;
- Toscana Diffusa: 30/10/2026 ore 12:00.

Se l'orario non è documentato viene mostrata soltanto la data.

## Archivio

`scripts/opportunity_radar_v024.py` accetta `--previous` per confrontare lo stato corrente con un output precedente. Un'opportunità che non è più attiva e la cui scadenza è trascorsa viene spostata in `archive`.

L'archivio conserva soltanto i dati utili alla consultazione storica:

- titolo;
- fonte;
- scadenza;
- URL ufficiale;
- data di archiviazione.

La UI rende questi record in forma compatta, senza le card dettagliate dei bandi aperti.

La persistenza dello stato precedente dovrà essere resa durevole quando il radar passerà dal prototipo a un job di produzione.

## Preview locale

L'artifact `opportunity-radar-v024-browser-preview` contiene:

- `dist/` completo;
- `APRI_ANTEPRIMA.py`, che sceglie automaticamente una porta libera e apre il browser;
- `APRI_ANTEPRIMA.bat`, semplice wrapper Windows;
- `LEGGIMI.txt`.

## Stato

La v0.2.4 è una preview di collaudo. Nessun merge e nessuna pubblicazione sono autorizzati o eseguiti.
