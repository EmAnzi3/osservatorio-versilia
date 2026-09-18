# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato:** `8c5bf2280d48ee76c50f5c98ad4fff6457f73d45` (merge `#242`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#242:** 2.025 coppie; **1.783 classificate, 242 residue**
- **A3 final head #242:** run `35375269584` **GREEN**
- **Pages post-merge #242:** run `35378475733` **GREEN**
- **Branch corrente:** `chore/a3-2-close-population-ratio-residuals`
- **PR corrente:** `#243`

## Residuo effettivo post-#242

La matrice effettiva conferma il bucket A strutturale chiuso. Le **8 residue B** sono:

- `evPoints / numeratore_denominatore`
- `publicWorks / numeratore_denominatore`
- `roadFinesPerResident / assoluto_normalizzato`
- `roadFinesPerResident / numeratore_denominatore`
- `pharmaciesPer1000 / assoluto_normalizzato`
- `pharmaciesPer1000 / numeratore_denominatore`
- `tourismStructuresPer1000 / assoluto_normalizzato`
- `tourismStructuresPer1000 / numeratore_denominatore`

Bucket attesi prima della tranche:

- **B — cross-source / companion:** 8
- **C — semanticamente `NOT_APPLICABLE`:** 34
- **D — verifica fonte ufficiale necessaria:** 200
- **Totale:** 242

## Intervento corrente — #243

La tranche chiude **6** coppie B.

### `ACQUIRED`

`publicWorks / numeratore_denominatore` usa il contratto generico `canonical_field_ratio_formula`:

- numeratore: `towns[*].governance.works.value`;
- denominatore: `population` dell'anno target 2026;
- formula verificata esattamente **7/7 Comuni**;
- detector invariato e privo di ID metrici hard-coded.

### `AVAILABLE_MISSING`

Sono classificati metric-specific, con fonte ufficiale verificabile:

- `evPoints / numeratore_denominatore`: PUN espone il numero di punti di ricarica per Comune, ma il conteggio non è conservato nella metrica pubblicata;
- `pharmaciesPer1000`: la fonte ministeriale espone l'elenco completo delle farmacie con Comune, ma la pipeline conserva soltanto la densità;
- `tourismStructuresPer1000`: Regione Toscana pubblica la consistenza 2025 per Comune e tipologia; il dettaglio canonico oggi disponibile è 2024 e non viene riusato come evidenza 2025.

**Esito atteso:** **1.789 classificate / 236 residue**. B scende da **8 a 2**; restano soltanto le due coppie `roadFinesPerResident`. C e D restano 34 e 200.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente; l'Effective Public Catalog resta una vista derivata.
2. A3 non deve introdurre una seconda lista manuale di indicatori o fonti.
3. `ACQUIRED` richiede evidenza strutturata o formula numericamente verificata; mai annotazioni manuali.
4. `AVAILABLE_MISSING` e `SOURCE_UNAVAILABLE` richiedono evidenza ufficiale verificabile.
5. `NOT_APPLICABLE` resta metric-specific.
6. I detector generici non devono hard-codare ID metrici; le relazioni concrete appartengono ai contratti.
7. Ogni formula deve essere fail-closed.
8. A3.2 non è chiuso finché `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
9. Nessun merge/pubblicazione senza A3, Quick e Full pertinenti GREEN e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Portare `#243` a A3 Enrichment Audit, Quick e Full GREEN sul final head.
2. Verificare nel log A3 il conteggio esatto **1.789 / 236** e i sei stati attesi.
3. Fermarsi prima del merge.
4. Dopo merge autorizzato, audit dedicato delle due residue `roadFinesPerResident`; poi chiudere C e D.
5. A3.2 termina soltanto a `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
