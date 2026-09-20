# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A4 — Visualization & Content Contract
- **Step attivo:** chiusura A4.5–A4.6
- **Stato:** IN_PROGRESS — implementazione completa in PR #271; in attesa del Full sul final head e del merge esplicito
- **Main verificato:** `f28d09ce85bce6198392b4f9fbe86c6afc6dedd8` (merge #270)
- **A3:** DONE
- **A4.1–A4.4:** mergiati
- **Catalogo effettivo baseline:** 225 indicatori · 1.547 righe
- **Confronti:** 87 `comparisonReference=aggregate` · 138 fallback media semplice
- **Rapporti strutturati:** 16 indicatori · 112 righe con `ratioComponents`
- **Visual regression:** 40 campioni rappresentativi derivati dal catalogo
- **Branch corrente:** `feat/a4-visual-regression`
- **PR corrente:** #271 — `A4: add representative visual regression gate` — Ready
- **Modifiche visive al prodotto:** nessuna

## A4.5–A4.6

Il lotto introduce una regressione visuale globale senza duplicare il catalogo.

Il campione viene risolto automaticamente dall'Effective Public Catalog e copre:
- 11 temi;
- 3 famiglie generiche `data-viz`;
- 22 famiglie `compositeType`;
- 2 varianti dello storico;
- vista corrente + storico di una scheda comunale.

Le baseline sono fingerprint visuali compatti in `ci/visual-regression-baselines/*.json`: dimensioni, average hash, difference hash e griglia colore 8×8. Gli screenshot PNG non vengono versionati; sono prodotti in `reports/visual-regression/` soltanto come diagnostica per baseline mancanti o mismatch.

Il primo Full completo, run `35522525947` sullo SHA `3c31b452c333ff5df94e58eb070293fdce586995`, ha superato tutti i test precedenti e si è arrestato esclusivamente sul bootstrap delle 40 baseline mancanti. L'artifact diagnostico è stato verificato prima di fissare i fingerprint.

Il gate è integrato nel Full di `scripts/preflight.py`; il workflow Pages carica sempre l'artifact diagnostico del visual regression. Il Quick resta invariato come gate rapido.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unica fonte canonica del catalogo.
2. Il campione visuale deve restare derivato dal catalogo e dalle famiglie renderizzate; niente lista manuale di ID metriche nel contratto.
3. I fingerprint visuali non sostituiscono i test semantici/DOM/browser già esistenti: li completano.
4. Un mismatch va diagnosticato tramite lo screenshot prodotto; non si allargano le soglie per far passare una regressione.
5. Un cambiamento visuale intenzionale richiede approvazione visiva prima dell'aggiornamento delle baseline.
6. La PR #271 non modifica rendering, contenuti o dati pubblici.

## Prossima azione esatta

1. Attendere Quick e Full sul final head di #271.
2. Richiedere 40/40 campioni visuali conformi e nessuna regressione nei gate precedenti.
3. Se verdi, #271 è pronta al merge; merge solo dopo approvazione esplicita del proprietario.
4. Dopo il merge verificare deploy Pages e live-status.
5. Procedere con A5.1 — audit quantitativo/visivo del Design System 2.0.
