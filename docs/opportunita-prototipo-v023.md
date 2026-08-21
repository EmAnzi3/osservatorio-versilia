# Radar Opportunità Versilia — v0.2.3 UI preview

## Obiettivo

La v0.2.3 aggiunge una **vista browser di collaudo** sopra il motore v0.2.2 già validato. Non modifica la logica di classificazione e non amplia le fonti.

La preview è intenzionalmente separata dal sito pubblico:

- route di build: `/opportunita-preview/`;
- `meta robots`: `noindex,nofollow,noarchive`;
- nessuna voce nella sitemap;
- nessun link aggiunto alla navigazione pubblica;
- nessun merge o deploy richiesto per il collaudo;
- la shell viene estratta dalla build brand canonica tramite `scripts/site_chrome.py`, senza duplicare header/footer.

## Contenuto della preview

La pagina rende le opportunità `quality-pass` del live probe corrente e mostra:

- conteggio complessivo, dirette e condizionate;
- filtro per Comune;
- filtro per stato;
- ricerca testuale;
- ordinamento per scadenza;
- fonte;
- scadenza;
- ruolo del Comune tradotto in linguaggio leggibile;
- ambito geografico;
- richiedente;
- beneficiari finali;
- condizioni operative;
- matrice dei sette Comuni;
- evidenza sintetica della classificazione;
- link alla fonte ufficiale.

Il filtro Comune usa la matrice `municipality_eligibility`: un'opportunità non viene mostrata per un Comune classificato `not_eligible`.

## Etichette UI

Le etichette tecniche vengono tradotte:

| Valore motore | Etichetta preview |
| --- | --- |
| `eligible` | Opportunità diretta |
| `conditional` | Da verificare |
| `direct_applicant` | Candidatura diretta |
| `partner` | Partecipazione come partner |
| `implementing_body` | Ente attuatore / proponente |
| `system_member` | Tramite sistema / aggregazione |

La semantica tecnica resta nel JSON; la pagina evita di esporre al lettore termini interni non necessari.

## Sicurezza editoriale

La preview non è una nuova sezione pubblica. Il builder verifica esplicitamente che:

1. la route contenga `noindex,nofollow,noarchive`;
2. `opportunita-preview` non compaia in `sitemap.xml`;
3. la pagina usi `data-page="special"`;
4. header/footer derivino dalla shell canonica;
5. il runtime applicativo canonico resti disponibile per ricerca e navigazione.

La build usata per materializzare la shell è `scripts/build_static_brand.py`, la stessa base brand utilizzata dal workflow Pages del sito. La precedente `build_static.py` non è sufficiente per le pagine speciali che devono rispettare il contratto `site_chrome`.

## Test

La v0.2.3 aggiunge una suite statica per il rendering e un collaudo Playwright reale.

Controlli browser previsti su desktop 1440×1000 e mobile 390×844:

- header, logo, footer e ricerca globali canonici;
- 11 schede del campione corrente;
- nessun overflow orizzontale;
- filtro Forte dei Marmi: 9 opportunità;
- Forte dei Marmi + `conditional`: 4 opportunità;
- reset filtri: ritorno a 11;
- ricerca `parcheggi`: una sola scheda;
- footer social rimosso nella route `noindex`, come previsto dal contratto `site_chrome`.

## Come aprire la preview

Il workflow `Prototipo Radar Opportunità` genera l'artifact:

`opportunity-radar-v023-browser-preview`

Dopo averlo scaricato e scompattato, dalla cartella estratta:

```bash
python -m http.server 8000 --directory dist
```

Poi aprire:

```text
http://127.0.0.1:8000/opportunita-preview/
```

Su Windows, se il comando `python` non è registrato, è possibile usare:

```text
py -m http.server 8000 --directory dist
```

Il server si interrompe con `Ctrl+C`.

## Build manuale dal repository

Con le dipendenze Playwright già installate:

```bash
python scripts/opportunity_radar_v022.py --date 2026-08-21 --output reports/runtime/opportunities-v022.json
python scripts/build_static_brand.py
python scripts/build_opportunity_preview.py --data reports/runtime/opportunities-v022.json --dist dist
python scripts/preview_dist.py --directory dist --port 8000
```

La preview è quindi disponibile su `/opportunita-preview/`.

## Stato

**v0.2.3 è una UI di collaudo non pubblica. La PR #82 deve restare Draft finché la resa browser non viene approvata.**
