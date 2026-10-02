# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Workstream A3 benchmark attivo — PR #304

- Branch `feat/a3-benchmark-available-missing`, base `fix/a3-enrichment-publication-gap`; **OPEN/DRAFT**, non mergiare né Ready.
- **Certificato:** run `36989516811`, head `b8b95be6fbc27f9b80576018bf5e5480cad79d87`: **115/115 benchmark pubblici, 0 gap, 98 AVAILABLE_MISSING su 44 profili, 84 chiusi** rispetto alla baseline 182.
- Artifact `11218717605`: backlog JSON/Markdown e residual closure audit JSON/Markdown. Build catalogo, regressione matrice, matrice effettiva, publication audit, backlog e residual audit tutti SUCCESS; `benchmark-backlog` non skipped.
- Nuovi ACQUIRED rispetto al passaggio 112: costa protetta ISPRA 2020, linea litoranea statistica Istat 2021, località Bandiera Blu FEE 2026. Per Istat DBF completo: 646 record univoci, 34 Toscana, 4 costieri + 3 n.a. riconciliati. Per FEE nomi delle sei località Versilia riconciliati; barre/parentesi conservate e revoche escluse; elenco nazionale comprende acque interne.
- Fan-in idempotente verde; preservati benchmark biblioteche. Inventario workflow A3 riallineato al contratto. **Nessuna modifica ai golden master A5**; i relativi workflow sono skipped.
- **Residual audit:** 98 righe, **68 blocchi documentati e 30 audit fonte ancora aperti**. Le diagnosi non modificano gli stati della matrice né contano come acquisizioni. `closureReady=false`: **A3 NON CHIUSA**.
- OpenBDAP aggiornato: **271/273**, assenti Villafranca in Lunigiana (`045016`) e Marradi (`048026`). Snapshot diagnostico FAIL, nessun aggregato parziale; SIOPE, compositi e formule non certificate restano distinti.
- QA locale: contratti sorgente/dati, idempotenza e rifiuto di duplicati, n.a. convertiti a zero e valori/nomi incoerenti PASS. Quick eseguito con `OV_RELEASE_BUILD=1`; prerender bloccato da Chromium assente e download browser invalido nel runtime. Certificazione pubblica completata su GitHub senza indebolire i gate.
- Il fan-out selezionato conserva il riferimento storico 111/111 del lotto precedente: non usarlo come certificazione corrente. Il riferimento corrente è il run sopra; aggiornare le selezioni soltanto insieme a un nuovo batch motivato, evitando di rilanciare tutti i worker per un refresh dei soli contatori.
- **Batch in certificazione:** quattro candidati PASS: accessibilità servizi essenziali IFC (anno effettivo 2019, mediana comunale Toscana 33,2 / Italia 27,1 minuti, 7.903 Comuni ufficiali); perdite idriche Istat 2018 (42,8% / 42,0% ufficiali); ricettività potenziale prima infanzia Toscana 2024/25 (28.077 / 59.052 × 100, Italia null); elementi censimento idraulico Toscana 2021 (3.666 feature, Italia null). Tutti riconciliati 7/7; non ancora ACQUIRED prima del gate pubblico.
- **Audit locale nuovo batch:** 94 AVAILABLE_MISSING, 88 chiusi dalla baseline; 94 diagnosi documentate, zero righe generiche, `closureReady=false`. Diagnosi fondate su probe, periodi/definizioni e componenti; limiti HTTP/dimensione file non trattati come indisponibilità. Le prossime azioni sono incluse per ciascuna metrica nell'evidenza residuale.
- **Prossima azione:** certificare il gruppo con un unico gate pubblico completo, leggere artifact e aggiornare il riferimento certificato. Poi proseguire le azioni tecniche documentate: nessuna dichiarazione di esaurimento delle fonti o chiusura A3 basata sulle sole diagnosi.

## Stato A5 congelato

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A5 — Design System 2.0
- **Step attivo:** A5.5 — propagazione progressiva DS2
- **Stato:** DONE tecnicamente — chiusura formale A5 sospesa soltanto fino ad approvazione esplicita e merge della PR #280
- **Main incorporato:** `46a31d3ca60717827ac92c709349b0c77355c3b4`
- **Merge di allineamento main:** `bde1c5ab82f85c6655908cd3002139caddc6245b`
- **Checkpoint UI approvato:** `bc9e5086aa796637828e1a5ae6e9952873024ef7`
- **Commit closure docs/scope:** `6fa94b4a569d5ee90b24fd061e3aeae379546162`
- **Branch:** `feat/a5-controlled-iteration`
- **PR:** #280 — Draft, OPEN, non mergiata
- **A0–A4:** DONE
- **A5.1–A5.5:** DONE tecnicamente
- **A6:** NOT_STARTED

## Contratti congelati

I contratti approvati sono documentati in `docs/A5_GOLDEN_MASTERS.md`.

- 11 pagine tematiche standard DS2 consolidate.
- 7 schede comunali consolidate sul renderer parametrico condiviso.
- Camaiore completa protetta dal checkpoint `5aaf159870912eb49bffbd044963549bfb920150`.
- Viareggio/Massarosa Demografia restano protette dal golden lock storico.
- Navigazione Comuni e Home “Esplora per territorio” in ordine alfabetico: Camaiore, Forte dei Marmi, Massarosa, Pietrasanta, Seravezza, Stazzema, Viareggio.
- Route speciali mantenute come eccezioni intenzionali: `meteo-clima`, Atlante attività economiche, Affluenza.

## Closure audit route speciali

- **Meteo/clima:** workspace specializzato; shell canonica e gate clima dedicati.
- **Atlante attività economiche:** web component autonomo con browser contract dedicato desktop/tablet/mobile.
- **Affluenza:** archivio/event selector specifico; token/componenti canonici e responsive dedicato.

Nessuna delle tre route richiede un rollout forzato nello shell standard A5.

## Prossima azione esatta

1. Attendere e verificare che tutti i gate della PR siano verdi sul nuovo head di closure.
2. Se verdi, fermarsi e chiedere al proprietario autorizzazione esplicita a rendere #280 Ready e mergiarla.
3. Solo dopo il merge: segnare A5 `DONE` e avviare A6.1 — modello semantico minimo.

Non aggiornare golden/baseline per ottenere verde e non mergiare senza approvazione esplicita.
