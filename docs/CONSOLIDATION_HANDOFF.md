# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A5 — Design System 2.0
- **Step attivo:** A5.5 — propagazione progressiva DS2
- **Stato:** IN_PROGRESS — lotto 1: pagina tematica Economia sullo shell A5 condiviso; Atlante Economia e schede comunali esclusi dal lotto
- **Main verificato e incorporato:** `9cc1f984f73c20e3c4a50ac9401ebf84fb9e4a81`
- **Branch:** `feat/a5-controlled-iteration`
- **PR:** #280 — Draft
- **Riconciliazione:** commit `edb17ea5d44a38ad21d2eb6cf330a3420a0b69d1`; branch 0 commit dietro `main`
- **A0–A4:** DONE
- **A5.1–A5.3:** DONE
- **A5.4:** DONE
- **A5.5:** IN_PROGRESS

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

1. Completare il lotto 1 A5.5 su `confronta/economia/` e verificare preview desktop/mobile.
2. Non modificare i golden master Viareggio/Massarosa salvo regressioni.
3. Mantenere fuori dal lotto `confronta/economia/atlante-attivita-economiche/`.
4. Dopo approvazione visiva del lotto 1, decidere il successivo tema/lotto; non propagare in massa.
5. Non aggiornare baseline A4 e non rendere la PR Ready/merge senza approvazione esplicita.
