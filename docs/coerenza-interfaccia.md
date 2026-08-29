# Contratto di coerenza delle pagine

Questo documento definisce le regole obbligatorie per ogni pagina pubblica di Osservatorio Versilia. L'obiettivo è impedire che nuovi indicatori, approfondimenti o mini-app introducano shell, link, metadata o comportamenti paralleli.

## Fonte canonica

Header e footer nascono in `assets/app-parts/00.txt`. Le pagine generate dopo il prerender devono riusarli tramite `scripts/site_chrome.py`; non devono copiarli e modificarli localmente.

La navigazione globale ha ordine e testi stabili:

- header: **Temi · Comuni · Il progetto · Stato dati · Segnala**;
- footer: **Il progetto · Stato dei dati · Metodo · Licenza · Versioni dei dati · Segnala un dato · Contatti**.

Il link a `/stato-dati/` deve essere presente nel markup iniziale, non aggiunto soltanto da JavaScript. In questo modo resta disponibile anche senza runtime e viene ereditato da pagine speciali come `/pnrr/`.

## Regole per nuove implementazioni

1. Un nuovo indicatore entra in `data/site-data.json` e usa i renderer esistenti. Non crea una shell o una pagina manuale separata.
2. Una nuova pagina speciale estrae la shell con `extract_native_shell()` e deve essere aggiunta all'inventario esplicito di `scripts/test_site_consistency.py`.
3. Ogni pagina indicizzabile deve avere un solo `title`, una description, canonical, JSON-LD, Open Graph e Twitter Card coerenti con l'URL pubblico.
4. Ogni link interno deve risolvere a una route realmente prodotta dalla build.
5. Ogni pagina indicizzabile deve comparire una sola volta nella sitemap; pagine `noindex`, 404 e offline ne restano fuori.
6. Colori, font, spaziature, logo, ricerca e footer usano gli asset canonici. Non sono ammessi header/footer locali con un sottoinsieme dei link.
7. Desktop e mobile devono essere verificati senza overflow orizzontale. I testi non possono uscire dai contenitori.

### Selettori Agricoltura e territorio

Il profilo colture riusa i controlli compositi canonici della pagina di confronto e delle schede comunali. SAU e superficie irrigata riusano il selettore assoluto/rapportato esistente. Non sono introdotte pagine, shell, colori o componenti paralleli. I valori `null` devono essere resi come `n.d.` e non possono essere classificati o ordinati come zeri reali.

### Selettori Costa e mare

Qualità delle aree, campioni non conformi e dinamica del litorale riusano il selettore composito canonico. Le tabelle di dettaglio dichiarano numeratori, denominatori e chilometri. I Comuni non costieri espongono `n.a.` e non partecipano a ordinamento, media o aggregazione.

## Profili ed eccezioni esplicite

- `offline.html`: pagina di servizio senza shell, canonical o runtime completo; deve essere `noindex,nofollow`.
- `404.html`: usa la shell completa ma deve essere `noindex,follow`.
- `/confronta/meteo-clima/`: bozza accessibile ma `noindex,nofollow`; shell e metadata restano comunque completi.
- `/percorsi/`: mini-app cartografica full-screen. Usa lo header canonico; il footer è l'unica eccezione ammessa perché sottrarrebbe spazio e resterebbe nascosto sotto l'interfaccia a mappa.
- `/percorsi/metodo.html`: pagina editoriale normale, quindi usa header e footer completi.

Qualsiasi nuova eccezione deve essere motivata qui e codificata nel test: non può nascere implicitamente perché una pagina viene generata più tardi delle altre.

## Gate di build

Il controllo finale va eseguito dopo Stato dati, PNRR e copia di Percorsi:

```bash
python scripts/test_site_consistency.py
```

Il gate verifica inventario delle pagine, shell, link di navigazione, metadata, route interne e corrispondenza esatta con la sitemap. Una pagina nuova o divergente fa fallire la pull request prima del merge.

Per un controllo rapido sui soli sorgenti, senza build browser:

```bash
python scripts/test_site_consistency.py --source-only
```

## Pubblicazione

Le modifiche si preparano su branch e pull request. Il merge su `main` avvia la pubblicazione GitHub Pages e richiede quindi approvazione esplicita del proprietario del progetto.
