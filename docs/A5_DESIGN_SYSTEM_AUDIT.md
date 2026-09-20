# A5 — Design System 2.0: audit e fondazione

## Scopo

Questo documento chiude A5.1–A5.3 senza modificare il rendering pubblico. L'obiettivo è misurare i problemi del sistema visuale attuale, definire i ruoli cromatici del Design System 2.0 e fissare un vocabolario comune di token prima della pagina pilota.

L'audit usa come sorgenti:

- `assets/original.css`;
- `assets/static.css`;
- `assets/fidelity.css`;
- `assets/agricoltura-ii-draft.css`;
- `ci/content-contract.json`;
- le famiglie di pagina e i componenti renderizzati dall'app;
- il contratto visuale A4 e il relativo campione di regressione.

Non vengono modificati dati, indicatori, contenuti, route o baseline visuali.

## Baseline quantitativa

Perimetro CSS analizzato: **116.412 caratteri** distribuiti nei quattro fogli stile pubblici principali.

| Misura | Baseline |
| --- | ---: |
| Colori HEX distinti | 246 |
| Dichiarazioni `background` / `background-color` | 187 |
| Dichiarazioni di bordo | 336 |
| Dichiarazioni `box-shadow` | 29 |
| Riferimenti a `var(--blue)` | 90 |
| Riferimenti a `var(--muted)` | 82 |
| Riferimenti a `var(--theme-color)` | 21 |
| Riferimenti a `var(--theme-accent)` | 38 |
| Dichiarazioni `font-size` espresse in px | 288 |
| Dichiarazioni da 11 px o meno | 177 · 61,5% |
| Dichiarazioni da 10 px o meno | 136 · 47,2% |
| Dichiarazioni sotto 9 px | 46 |
| Regole con testo esplicitamente 8–10 px | 123 |

Questi conteggi descrivono il codice CSS, non la quota di pixel effettivamente occupata sullo schermo. Servono a misurare frammentazione e densità del sistema, non a stimare una superficie geometrica.

## A5.1 — audit

### 1. Superfici e predominanza del beige

I due ruoli principali attuali sono:

- `--paper: #f4eee2`;
- `--surface: #fffaf1`.

Il loro contrasto relativo è **1,11:1**. La differenza è quindi molto debole: canvas, header, navigazione sticky, pannelli e card tendono a fondersi in una stessa famiglia calda. Il beige non è un accento editoriale: è diventato il contesto dominante.

Il problema non è che il beige debba scomparire. Deve smettere di svolgere contemporaneamente il ruolo di canvas, superficie, navigazione e sfondo di controllo.

### 2. Contrasto

Coppie strutturali principali:

| Coppia | Rapporto |
| --- | ---: |
| `--ink` / `--paper` | 12,00:1 |
| `--ink` / `--surface` | 13,33:1 |
| `--muted` / `--paper` | 4,37:1 |
| `--muted` / `--surface` | 4,86:1 |
| `--blue` / `--surface` | 7,22:1 |
| `--paper` / `--surface` | 1,11:1 |

Il testo primario è solido. Il punto debole è il testo secondario sul canvas: `--muted` su `--paper` resta sotto 4,5:1, e il rischio è amplificato dall'uso frequente di corpi 8–10 px.

Gli accenti dei nove temi oggi esplicitamente definiti hanno invece contrasto sufficiente sui rispettivi fondi soft, circa **5,05:1–6,96:1**. Il problema è quindi soprattutto di governance e copertura, non di saturazione insufficiente.

### 3. Densità tipografica

Il sistema usa molte micro-label:

- 61,5% delle dichiarazioni in px è da 11 px o meno;
- quasi metà è da 10 px o meno;
- 46 dichiarazioni scendono sotto 9 px.

Queste dimensioni compaiono in metadati, fonti, tab, badge, note, tooltip, etichette di grafici e pannelli di approfondimento. Su desktop la gerarchia resta spesso leggibile grazie allo spazio; su mobile la stessa densità diventa fragile.

A5 deve ridurre il numero di livelli tipografici e impedire che informazioni necessarie vengano affidate a testi microscopici.

### 4. Gerarchia

La homepage ha una gerarchia forte: hero, fotografia, sezioni e grandi titoli sono ben distinti. Nelle pagine dati la gerarchia si appiattisce:

- molti pannelli usano bordo + sfondo + raggio + ombra con peso simile;
- i metadati sono distribuiti in numerosi piccoli elementi;
- le superfici annidate competono con il dato principale;
- il colore globale blu compare nel CSS più del doppio dei riferimenti ai sistemi tematici combinati.

Il Design System 2.0 deve far emergere prima il dato, poi il contesto, poi il metadato.

### 5. Frammentazione dei token

Il CSS contiene **246 colori HEX distinti**. Una parte è giustificata da grafici e stati specifici, ma il numero segnala una forte presenza di valori locali.

Inoltre convivono due modelli tematici:

- `--theme-color` + `--theme-soft`;
- `--theme-accent` + `--theme-soft` + `--theme-line`.

`--theme-soft` ha quindi anche una semantica sovrapposta tra due generazioni del sistema.

La migrazione A5 deve convergere su un solo vocabolario.

### 6. Copertura dei temi

Il prodotto espone **11 temi**, ma nei fogli stile analizzati esistono token tematici espliciti soltanto per:

`demografia`, `economia`, `lavoro`, `istruzione`, `salute`, `mobilita`, `abitare`, `ambiente`, `comunita`.

Non risultano definizioni dedicate per `sicurezza` e `bilanci`.

L'app assegna direttamente `data-theme="${themeKey}"` alle superfici di confronto e comunali e usa esplicitamente `themeKey === 'sicurezza'`. La mancanza di token dedicati è quindi un gap reale del sistema, non un tema teorico.

A5 deve avere una mappa completa 11/11.

### 7. Desktop

Il desktop dispone di una buona base:

- larghezza editoriale massima coerente;
- hero e sezioni con respiro;
- pannelli di confronto capaci di ospitare controlli e grafici complessi.

Le criticità sono soprattutto nelle superfici analitiche: troppi livelli di bordo/sfondo hanno importanza simile e la distinzione fra area di controllo, dato principale e contesto è debole.

### 8. Mobile

Il CSS adotta correttamente pattern dedicati, ma scarica molta complessità sullo scroll orizzontale:

- navigazione tematica sticky;
- cataloghi metriche a scorrimento;
- selettori senza wrapping;
- grafici storici con `min-width: 500px`.

Questi pattern sono ammissibili per contenuti complessi, ma non devono essere accompagnati da una riduzione ulteriore della tipografia a 8–9 px.

Obiettivo A5: touch target più leggibili, gerarchia verticale più netta e nessun overflow dell'intera pagina; lo scroll orizzontale deve restare confinato ai componenti che lo richiedono.

### 9. Famiglie di pagina

Il contratto architetturale distingue quattro famiglie derivate:

- `town`;
- `theme`;
- `standard-indicator`;
- `special-route`.

A queste si aggiungono homepage, pagine statiche e standalone.

Le famiglie principali riusano il layer comune, mentre molte route speciali introducono superfici e colori locali. A5 non deve riscrivere tutto insieme: il nuovo sistema va validato su una famiglia rappresentativa e poi esteso per lotti.

## A5.2 — ruoli cromatici

Il Design System 2.0 adotta questi ruoli, indipendenti dai valori finali:

1. **Canvas neutro** — sfondo globale non tematico, più neutro dell'attuale beige.
2. **Surface primaria** — pannelli analitici e card che contengono il dato.
3. **Surface secondaria** — controlli, gruppi e sotto-sezioni.
4. **Surface editoriale** — spazio in cui il tono caldo storico può sopravvivere senza dominare il prodotto.
5. **Text primary** — titoli, numeri e contenuto principale.
6. **Text secondary** — descrizioni e metadati necessari.
7. **Text tertiary** — informazioni accessorie, mai indispensabili se il contrasto o la dimensione risultano insufficienti.
8. **Border subtle / strong** — separazione strutturale senza creare una griglia di scatole equivalenti.
9. **Theme accent / soft / line** — colore tematico come informazione, completo per 11/11 temi.
10. **Semantic states** — success, warning, danger, info separati dai colori dei temi.
11. **Focus** — ruolo accessibile e indipendente dal tema.
12. **Elevation** — pochi livelli dichiarati; niente ombre locali arbitrarie.

Il colore tematico identifica il contesto, non deve diventare il colore di tutto il layout.

## A5.3 — vocabolario token

Vocabolario canonico previsto per l'implementazione:

### Superfici

- `--ds-canvas`
- `--ds-surface`
- `--ds-surface-secondary`
- `--ds-surface-editorial`
- `--ds-surface-inverse`

### Testo

- `--ds-text`
- `--ds-text-secondary`
- `--ds-text-tertiary`
- `--ds-text-inverse`

### Bordi e focus

- `--ds-border`
- `--ds-border-strong`
- `--ds-focus`

### Elevazione

- `--ds-shadow-1`
- `--ds-shadow-2`

### Tema

- `--ds-theme-accent`
- `--ds-theme-soft`
- `--ds-theme-line`

### Stati

- `--ds-success`
- `--ds-success-soft`
- `--ds-warning`
- `--ds-warning-soft`
- `--ds-danger`
- `--ds-danger-soft`
- `--ds-info`
- `--ds-info-soft`

### Migrazione

Durante A5.4–A5.5 gli alias storici possono restare temporaneamente per evitare una riscrittura massiva:

- `--paper` → canvas/editorial secondo il contesto;
- `--surface` → surface primaria;
- `--ink` → text primary;
- `--muted` → text secondary;
- `--theme-color` e `--theme-accent` → un unico `--ds-theme-accent`.

Gli alias sono compatibilità transitoria, non il nuovo contratto.

## Soglie operative per la pagina pilota

La pagina pilota deve rispettare almeno:

- testo normale: contrasto >= 4,5:1;
- testo primario: obiettivo >= 7:1;
- nessuna informazione necessaria affidata a testo sotto 11 px; obiettivo ordinario >= 12 px;
- token tematici presenti per tutti gli 11 temi;
- nessun valore colore nuovo locale quando esiste un ruolo DS equivalente;
- nessun overflow orizzontale della pagina;
- scroll orizzontale confinato a grafici/controlli che lo richiedono;
- dati, contenuti, unità, tooltip e comportamento funzionale invariati.

## A5.4 — pagina pilota

Pagina proposta: **`confronta/demografia/`**.

Motivi:

- usa la famiglia `theme`, centrale nell'esperienza analitica;
- contiene hero tematico, catalogo/selettori, definizione, confronto a barre, aggregato, fonte e collegamenti alle schede comunali;
- espone sia gerarchia sia densità;
- è coperta dai gate A4 e permette di validare un cambiamento intenzionale tramite artifact di visual regression.

La modifica A5.4 dovrà essere una PR **Draft**. Il primo Full è atteso in mismatch rispetto alle baseline A4: gli screenshot diagnostici saranno il materiale da approvare visivamente. Le baseline verranno aggiornate solo dopo approvazione esplicita.

Verifica richiesta sulla pilota:

- desktop: gerarchia, separazione canvas/surface, leggibilità dei metadati, uso dell'accento;
- mobile: header/navigation, selettori, leggibilità minima, assenza di overflow di pagina;
- confronto prima/dopo: nessuna variazione di dati, testo, ordine, tooltip o interazioni.

## Esito

A5.1 identifica problemi misurabili e non richiede modifiche UI. A5.2 e A5.3 fissano una direzione e un vocabolario comune. Il primo cambiamento visivo è deliberatamente rinviato ad A5.4.
