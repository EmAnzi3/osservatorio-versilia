# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A5 — Design System 2.0
- **Step attivo:** A5.4 — consolidamento dei golden master prima di A5.5
- **Stato:** IN_PROGRESS — sidebar, chart shell e toolbar condivisi applicati al pilot Viareggio/Demografia; golden master comunale non ancora completo
- **Main verificato e incorporato:** `9cc1f984f73c20e3c4a50ac9401ebf84fb9e4a81`
- **Branch:** `feat/a5-controlled-iteration`
- **PR:** #280 — Draft
- **Riconciliazione:** commit `edb17ea5d44a38ad21d2eb6cf330a3420a0b69d1`; branch 0 commit dietro `main`
- **A0–A4:** DONE
- **A5.1–A5.3:** DONE
- **A5.4:** IN_PROGRESS
- **A5.5:** NOT_STARTED

## Golden master congelati

I due contratti approvati sono documentati in `docs/A5_GOLDEN_MASTERS.md`.

1. **Pagina tematica:** `/confronta/demografia/?indicatore=population` sulla PR #280.
2. **Scheda comunale:** Viareggio Draft 19, SHA-256 `d17c486cd5d24dd181b80884282c8017e92a4189e5804412605072ab23c75875`.

Il Draft 19 è un riferimento visuale: il suo codice prototipale non va propagato.

## Audit di propagazione

Verificato che:
- il renderer delle pagine tematiche è condiviso; Demografia è il ramo A5 da generalizzare;
- le schede comunali condividono `renderTown()` / `renderTownMetric()`;
- grafici, storico e visual grammar sono già infrastrutture comuni;
- le route speciali `meteo-clima`, atlante economia e affluenza vanno gestite separatamente;
- nessun altro tema deve essere modificato prima che i due golden master siano riprodotti tramite componenti condivisi.

## Prossima azione esatta

1. Generalizzare i componenti A5 del golden master tematico senza cambiare il rendering Demografia.
2. Portare Viareggio sullo stesso renderer/component set condiviso, riproducendo il Draft 19 senza clone/fetch prototipali.
3. Verificare i due golden master desktop/mobile.
4. Eseguire Quick + Full sul final head.
5. Solo dopo approvazione esplicita iniziare A5.5 sugli altri temi.
6. Non aggiornare baseline A4 e non rendere la PR Ready/merge senza approvazione esplicita.
