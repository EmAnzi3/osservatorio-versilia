# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A6 — Semantic Data Layer e interrogazione deterministica
- **Step attivo:** A6.1 — modello semantico minimo
- **Stato:** IN_PROGRESS
- **Main di partenza A6:** `a98b89995e01cd12f2ab8422a0a6ed6aa81b5578`
- **A5:** DONE — PR #280 mergiata il 30/09/2026
- **Branch:** `feat/a6-semantic-model`
- **PR:** #301 — Ready, OPEN
- **A0–A5:** DONE
- **A7:** NOT_STARTED

## Contratto A6.1

La fonte di verità resta `data/site-data.json`. Non creare inventari paralleli di Comuni, temi o indicatori.

Il modello minimo deve derivare e governare:
- Comune;
- indicatore;
- tema;
- periodo;
- dimensione esplicita/source-backed;
- fonte;
- benchmark separato dall'osservazione comunale.

Il contratto machine-readable è `ci/semantic-model-contract.json`; la specifica è `docs/A6_SEMANTIC_MODEL.md`.

## Gate legacy A5

- `a5-change-scope.yml` è ritirato dopo la chiusura A5: il suo checkpoint non può governare i workstream successivi.
- I golden A5 restano attivi solo su modifiche UI/renderer pertinenti.

## Prossima azione esatta

1. Validare il contratto A6.1 nel Quick preflight.
2. Correggere solo eventuali incompatibilità reali con il catalogo canonico, senza rilassare il contratto per ottenere verde.
3. Eseguire Full sulla stessa PR.
4. Se Quick e Full sono verdi, marcare A6.1 DONE e preparare A6.2 — operazioni deterministiche.
5. Non introdurre ancora UI o linguaggio naturale.
