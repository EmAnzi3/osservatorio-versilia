# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Workstream A3 benchmark attivo — PR #304

- Branch `feat/a3-benchmark-available-missing`, base `fix/a3-enrichment-publication-gap`; **OPEN/DRAFT**, non mergiare né Ready.
- **Certificato:** run `37016547027`, head `64c5ff994e45d775483313e33e2e86a599a63a6b`: **119/119 benchmark pubblici, 0 gap, 94 AVAILABLE_MISSING su 41 profili, 88 chiusi** rispetto alla baseline 182.
- Artifact `11231710442` scaricato e verificato: backlog JSON/Markdown e residual closure audit JSON/Markdown. Build catalogo, regressione matrice, matrice effettiva, publication audit, backlog e residual audit tutti SUCCESS; `benchmark-backlog` non skipped.
- Nuovi ACQUIRED rispetto a 115: accessibilità servizi essenziali IFC (anno effettivo 2019, mediana comunale Toscana 33,2 / Italia 27,1 minuti); perdite idriche Istat 2018 (percentuali ufficiali 42,8% / 42,0%); ricettività potenziale prima infanzia Toscana 2024/25 (28.077 / 59.052 × 100, Italia null); elementi censimento idraulico Toscana 2021 (3.666 feature, Italia null). Tutti riconciliati 7/7.
- IFC: perimetro ufficiale 7.903 Comuni / 273 Toscana, Misiliscemi escluso dalla metodologia; mediana non ponderata coerente con il contratto pubblico. Worker dedicato PASS, run `37016339495`, artifact `11230142798`. Nessuna conversione di decili/ventili ordinali.
- Idraulica: ZIP e confini con hash identici allo snapshot pubblico; 82 areali, 2.572 lineari, 1.012 puntuali, escluso reticolo DCR 81/2021. Un'invalidità geometrica corretta senza cambiare alcuna intersezione regionale/comunale; il benchmark conta feature, non cantieri.
- Fan-in idempotente verde: run `37016547207`. **Nessuna modifica ai golden master A5**; i relativi workflow sono skipped. Corretto e verificato via hash il trasferimento del catalogo, mantenendo i gate invariati.
- **Audit diagnostico completato:** 94 righe, **94 blocchi documentati e zero diagnosi generiche**. Evidenza include probe controllati, periodi, definizioni, componenti e prossime azioni metric-level. Limiti HTTP/dimensione file non sono prove di indisponibilità. Diagnosi e acquisizioni restano distinte; `closureReady=false`: **A3 NON CHIUSA**.
- OpenBDAP: **271/273**, assenti Villafranca in Lunigiana (`045016`) e Marradi (`048026`). Nessun aggregato parziale; 19 blocchi di copertura e 5 di definizione restano distinti. Restano inoltre 22 compositi incompatibili con un benchmark scalare.
- QA locale: contratti sorgente/dati, regressione matrice, idempotenza e rifiuto di duplicati, aggregati/componenti/periodi incoerenti PASS. Quick eseguito con `OV_RELEASE_BUILD=1`; prerender bloccato da Chromium assente e download browser invalido nel runtime. Certificazione pubblica completata su GitHub senza indebolire i gate.
- Il fan-out conserva il riferimento storico 111/111: non usarlo come certificazione corrente. Il riferimento corrente è il run sopra; evitare rilanci di tutti i worker o gate pesanti per soli contatori/diagnosi/documentazione.
- **Prossima azione:** seguire le azioni tecniche del residual audit verificato, a partire da copertura OpenBDAP, dati storici GTFS/Salute e riconciliazione MIM. Acquisire soltanto con periodo/definizione/perimetro e componenti 7/7 certificati. Un solo gate dopo un gruppo sensato di nuovi PASS; nessuna dichiarazione di esaurimento delle fonti o chiusura A3 basata sulle sole diagnosi.

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
