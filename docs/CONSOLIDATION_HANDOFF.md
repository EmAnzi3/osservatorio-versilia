# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Workstream A3 benchmark attivo — PR #304

- Branch `feat/a3-benchmark-available-missing`, base `fix/a3-enrichment-publication-gap`; OPEN/DRAFT, non mergiare.
- Certificato dal run `36984935304`, head `b59a35e7f5a2af1f96060f0b9ed2f32923239476`: 112/112 benchmark pubblici, 0 gap, 101 AVAILABLE_MISSING, 81 chiusi su baseline 182. Spesa sociale per residente ACQUIRED.
- ISPRA costa 2020: candidato PASS da run `36982743711`, artifact `11216461886`; fan-in locale, riconciliazione 4 costieri + 3 n.a.; ACQUIRED soltanto dopo il nuovo publication gate.
- OpenBDAP: candidato rigettato, 271/273 Comuni Toscana; nessun aggregato pubblicato. Restano distinti SIOPE, compositi e formule non certificate.
- Corretto il falso failure del fan-in senza diff; invariati perimetro file e soglia diff.
- QA locale: contratti sorgente/dati e idempotenza biblioteche PASS; preflight quick eseguito con `OV_RELEASE_BUILD=1`, bloccato al prerender per Chromium assente (download browser non valido nel runtime). Nessun gate indebolito; certificazione pubblica demandata al run completo GitHub.
- Prossima azione: leggere il nuovo publication gate, poi audit fonte/contratto sui residui. Nessuna chiusura A3 dichiarata; preservare golden master A5.

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
