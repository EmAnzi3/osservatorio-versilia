# A5 — Golden master UI e regole di propagazione

Questo documento congela i due riferimenti visuali approvati per il Design System 2.0 prima di A5.5. Non è un catalogo dati parallelo: indicatori, temi e contenuti restano derivati da `data/site-data.json`.

## Stato di riferimento

- PR: **#280 — A5: controlled Demografia iteration**
- Branch: `feat/a5-controlled-iteration`
- Commit di riconciliazione con `main`: `edb17ea5d44a38ad21d2eb6cf330a3420a0b69d1`
- `main` incorporato: `9cc1f984f73c20e3c4a50ac9401ebf84fb9e4a81`
- La PR resta **Draft** e non va mergiata senza approvazione esplicita.

## Golden master 1 — pagina tematica

Route di riferimento:

`/confronta/demografia/?indicatore=population`

Il riferimento approvato è il rendering A5 presente nella PR #280. I file funzionali/visuali che lo determinano al commit di riconciliazione hanno questi blob SHA:

- `assets/app-parts/03.txt` — `0ef62909a2a5c289c955cb3465b507c3fb5082e9`
- `assets/fidelity.css` — `826af0d139c93da4cccaa096687471396c1873c4`
- `assets/ux-history.js` — `6d639c445a2f434871d10f712287c6178a487bb7`
- `assets/visual-grammar.js` — `dc3852434414833148d3c297235d78395ff73413`

Contratto visuale/funzionale da preservare:

1. shell DS2, header e navigazione temi coerenti;
2. sidebar con intestazione `GRUPPI DI INDICATORI`, accordion e indicatore attivo;
3. grafico corrente a **lollipop**;
4. linea verticale con **media semplice dei 7 Comuni** quando semanticamente applicabile;
5. tooltip del lollipop con valore del Comune e riferimento Versilia;
6. toolbar con `Scheda indicatore`, `Scarica CSV`, `Stampa / PDF` e switch `Valore attuale / Storico`;
7. storico e tooltip funzionanti;
8. controlli specifici dell'indicatore nello stesso linguaggio visuale;
9. benchmark esterno, Metodo/Comparabilità e Scala di lettura nello standard approvato;
10. card dei Comuni e resto della pagina senza regressioni.

## Golden master 2 — scheda comunale

Route logica di riferimento:

`/comuni/viareggio/?tema=demografia&indicatore=population`

Riferimento visuale approvato:

`Osservatorio_Versilia_A5_Scheda_Viareggio_Draft_19.zip`

SHA-256:

`d17c486cd5d24dd181b80884282c8017e92a4189e5804412605072ab23c75875`

Il Draft 19 è **riferimento visuale**, non implementazione da copiare. La produzione deve riprodurlo usando i renderer e i componenti condivisi della repository; non va propagata la tecnica prototipale di clone/fetch usata durante l'iterazione locale.

Contratto visuale/funzionale da preservare:

1. hero con immagine specifica del Comune;
2. identità comunale nella parte alta del banner;
3. tre KPI hero: **Popolazione, Superficie, Anno di istituzione**, con icone;
4. sintesi: **Reddito medio, Tasso di occupazione, Speranza di vita**, con icone;
5. navigazione Comuni e Temi coerente con DS2;
6. sidebar indicatori **identica al componente della pagina tematica**, non ricostruita;
7. card del valore comunale e card quota Versilia con la stessa superficie cromatica;
8. grafico che riusa **lo stesso componente** della pagina tematica: lollipop, riferimento medio, tooltip, storico, toolbar/export;
9. riga del Comune aperto evidenziata tramite l'accento del tema senza alterare le altre righe;
10. pulsanti export/stampa presenti una sola volta nella toolbar del grafico;
11. Confronto esterno, Metodo/Comparabilità e Scala di lettura con disposizione e colori della pagina tematica;
12. il box `Mobilità dei laureati italiani 25–39 anni` compare solo per:
    - `internalResidentialMobility`
    - `foreignResidentialMobility`
    - `totalResidentialMobility`

## Regola di implementazione

Quando il requisito dice **identico**, il componente esistente va riusato o generalizzato. Non è ammessa una ricostruzione visualmente simile con CSS/markup parallelo.

Lo standard deve essere parametrico per tema attraverso i token DS2:

- `--ds-theme-accent`
- `--ds-theme-soft`
- `--ds-theme-line`

Non devono nascere copie CSS per singolo tema quando il ruolo visuale è comune.

## Audit di propagazione

L'audit A5.5 preliminare ha verificato che:

- le 11 pagine tematiche passano dallo stesso renderer in `assets/app-parts/03.txt`; Demografia è oggi il ramo A5 speciale da generalizzare;
- le 7 schede comunali passano da `renderTown()` / `renderTownMetric()`;
- `assets/visual-grammar.js` e lo storico sono già infrastrutture condivise;
- `data/site-data.json` resta la fonte canonica;
- non servono decine di copie del layout.

Route da trattare come eccezioni/lotto separato e non forzare nel primo rollout generico:

- `confronta/meteo-clima/`
- `confronta/economia/atlante-attivita-economiche/`
- `confronta/comunita/affluenza/`

## Gate prima di A5.5

Prima di toccare un altro tema:

1. estrarre/generalizzare i componenti del golden master tematico;
2. far renderizzare Viareggio con gli stessi componenti condivisi, senza dipendere dal prototipo Draft 19;
3. verificare che i due golden master restino visualmente invariati;
4. eseguire Quick e Full;
5. mantenere la PR Draft fino alla verifica browser desktop/mobile e all'approvazione esplicita.
