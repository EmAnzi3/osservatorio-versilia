# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Workstream A3 benchmark attivo — PR #304

- Branch `feat/a3-benchmark-available-missing`, base `fix/a3-enrichment-publication-gap`; OPEN/DRAFT, non mergiare.
- Certificato dal run `36987416265`, head `85f39414eef27db0323e4b3f62e2117f0a7237d0`: **113/113 benchmark pubblici, 0 gap, 100 AVAILABLE_MISSING, 82 chiusi** su baseline 182. Spesa sociale e costa protetta ISPRA ACQUIRED.
- Fan-in idempotente verde sullo stesso head; preservati benchmark biblioteche e golden A5. Inventario workflow A3 riallineato al contratto.
- Nuovo candidato PASS: linea litoranea Istat 2021, Toscana 722,930 km / Italia 9.333,026 km; DBF ufficiale completo, 646 record univoci, 34 Toscana, 4 Comuni costieri + 3 n.a. riconciliati. Il materializzatore geografia lo integra nel catalogo effettivo; ACQUIRED soltanto dopo il nuovo publication gate.
- Candidato FEE Bandiera Blu 2026 PASS: 45 località Toscana / 524 Italia secondo il conteggio delle voci separate FEE, con barre e parentesi conservate; revoche escluse. Italia include le spiagge in acque interne dell’elenco nazionale. Riconciliati nomi e conteggi 4 costieri + 3 n.a.; fan-in canonico, ancora non ACQUIRED.
- OpenBDAP aggiornato localmente: **271/273**; assenti Villafranca in Lunigiana (`045016`) e Marradi (`048026`). Snapshot diagnostico FAIL, nessun aggregato parziale. SIOPE, compositi e formule non certificate restano distinti.
- QA locale: contratti sorgente/dati e idempotenza PASS; quick eseguito con `OV_RELEASE_BUILD=1`, prerender bloccato da Chromium assente e download browser invalido nel runtime. Nessun gate indebolito; certificazione pubblica eseguita sul run completo GitHub.
- Residual audit derivato: non cambia la matrice né conta diagnosi come acquisizioni. Sui 100 residui certificati documenta 68 blocchi e lascia 32 audit fonte esplicitamente aperti; include ragioni e prove metric-level. Dopo linea litoranea e FEE attesi 98 residui, da leggere realmente nel gate.
- Prossima azione: leggere il nuovo publication gate e il residual audit; continuare acquisizioni/diagnosi sui residui. Nessuna chiusura A3 dichiarata.

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
