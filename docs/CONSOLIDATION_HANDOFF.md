# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A5 — Design System 2.0
- **Step attivo:** nessuno — A5.4 chiuso; A5.5 è il prossimo step ma non è ancora iniziato
- **Stato:** A5.4 DONE — golden master tematico e comunale approvati; Viareggio e Massarosa verificati sullo stesso sistema condiviso
- **Main verificato e incorporato:** `9cc1f984f73c20e3c4a50ac9401ebf84fb9e4a81`
- **Branch:** `feat/a5-controlled-iteration`
- **PR:** #280 — Draft
- **Riconciliazione:** commit `edb17ea5d44a38ad21d2eb6cf330a3420a0b69d1`; branch 0 commit dietro `main`
- **A0–A4:** DONE
- **A5.1–A5.3:** DONE
- **A5.4:** DONE
- **A5.5:** NOT_STARTED

## Golden master congelati

I contratti approvati sono documentati in `docs/A5_GOLDEN_MASTERS.md`.

1. **Pagina tematica:** `/confronta/demografia/?indicatore=population` sulla PR #280.
2. **Scheda comunale:** Viareggio/Demografia, derivata dal Draft 19 e approvata visivamente.
3. **Prova di generalizzazione:** Massarosa/Demografia sullo stesso shell condiviso, approvata visivamente.

Il Draft 19 resta solo un riferimento visuale: il suo codice prototipale non è stato propagato.

## Audit di propagazione

Verificato che:
- il renderer delle pagine tematiche è condiviso; Demografia è il ramo A5 da generalizzare;
- le schede comunali condividono `renderTown()` / `renderTownMetric()`;
- grafici, storico e visual grammar sono già infrastrutture comuni;
- le route speciali `meteo-clima`, atlante economia e affluenza vanno gestite separatamente;
- nessun altro tema deve essere modificato prima che i due golden master siano riprodotti tramite componenti condivisi.

## Prossima azione esatta

1. Non modificare più il golden master Viareggio/Massarosa salvo regressioni.
2. A5.5 è il prossimo step, ma resta `NOT_STARTED` finché non viene avviato esplicitamente.
3. Quando A5.5 parte, propagare DS2 per lotti piccoli e verificabili, riusando i componenti condivisi invece di creare copie tema-specifiche.
4. Mantenere separate le route speciali già censite in `docs/A5_GOLDEN_MASTERS.md`.
5. Non aggiornare baseline A4 e non rendere la PR Ready/merge senza approvazione esplicita.
