# A5 — Golden master UI e regole di propagazione

Questo documento congela i riferimenti visuali approvati per il Design System 2.0 e i relativi lock di regressione. Non è un catalogo dati parallelo: indicatori, temi e contenuti restano derivati da `data/site-data.json`.

## Stato di riferimento

- PR: **#280 — A5: controlled Demografia iteration**
- Branch: `feat/a5-controlled-iteration`
- Checkpoint UI A5.5 approvato: `bc9e5086aa796637828e1a5ae6e9952873024ef7`
- `main` incorporato per la chiusura: `46a31d3ca60717827ac92c709349b0c77355c3b4` tramite merge commit `bde1c5ab82f85c6655908cd3002139caddc6245b`
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
13. la navigazione `Esplora Comuni` e le card Home `Esplora per territorio` usano l’ordine alfabetico: Camaiore, Forte dei Marmi, Massarosa, Pietrasanta, Seravezza, Stazzema, Viareggio.

## Golden master 3 — Camaiore completa

Dal **28 settembre 2026** Camaiore è approvata come scheda comunale A5 completa e **non deve più essere modificata** durante la propagazione agli altri Comuni.

Checkpoint approvato:

`5aaf159870912eb49bffbd044963549bfb920150`

Perimetro congelato:

- tutti gli **11 temi comunali standard**;
- tutti i **223 indicatori comunali** esposti dal catalogo corrente;
- viewport desktop `1440×1100`;
- viewport mobile `390×844`;
- hero, sintesi, navigazione, sidebar, card valore/Versilia, grafici, selettori, toolbar, CSV, Stampa/PDF, storico, tooltip, benchmark, approfondimenti, Metodo/Comparabilità, Scala di lettura e responsive.

Il gate `A5 municipal golden lock` costruisce il checkpoint approvato e confronta ogni stato Camaiore con l'output corrente. Il lock usa confronto di stato/computed layout su tutti gli indicatori e confronto visuale sulle famiglie rappresentative. Non è ammesso aggiornare il checkpoint per far passare una regressione: un cambiamento di Camaiore richiede approvazione esplicita del proprietario.

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

Route speciali confermate come **eccezioni intenzionali** nel closure audit A5.5:

- `confronta/meteo-clima/`: workspace climatico specializzato, con shell canonica, gate `Validate Meteo e clima page`, regressione interazioni clima e responsive dedicato;
- `confronta/economia/atlante-attivita-economiche/`: web component autonomo `ov-economy-atlas`, con browser contract dedicato a 1440/1024/390 px, controllo overflow, ricerca, storico e deep-link comunali;
- `confronta/comunita/affluenza/`: archivio elettorale con semantica/event selector propri; riusa token e componenti canonici e mantiene CSS specifico limitato agli adattamenti di layout/responsive.

Queste route non vanno forzate nel renderer standard `confronta/<tema>/` finché la loro semantica richiede un’interazione diversa. Devono però continuare a rispettare header/footer, identità tematica, responsive e contratti sorgente/browser pertinenti.

## Esito A5.5

Il gate A5.4 è chiuso:

1. i componenti del golden master tematico sono stati generalizzati senza alterare il rendering approvato;
2. Viareggio usa il sistema condiviso e non dipende dal codice prototipale Draft 19;
3. Massarosa usa lo stesso shell come seconda prova comunale, con hero dedicato e senza hard-code strutturale su Viareggio;
4. i 10 indicatori Demografia sono verificati nel browser su Viareggio e Massarosa, con controlli responsive e famiglie grafiche coerenti;
5. Viareggio e Massarosa sono stati approvati visivamente;
6. il commit di chiusura A5.4 è `7eadda666118f2450290a3b1c6edb93f061b7c7b`.

A5.5 è completato sul checkpoint UI `bc9e5086aa796637828e1a5ae6e9952873024ef7`: rollout tematico e comunale, golden lock, cohort e ordinamento alfabetico sono verificati. La PR #280 resta Draft fino all’approvazione esplicita del proprietario; A5 diventa formalmente `DONE` solo dopo il merge.
