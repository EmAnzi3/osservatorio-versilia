# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato:** `2443882c819c95a43256a1612c9bc3f11b6ae4c1` (merge `#254`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#254:** 2.025 coppie; **1.937 classificate, 88 residue**
- **A3 final head #254:** run `35437400106` **GREEN**
- **Pages final head #254:** run `35437400105` **GREEN** (Quick + Full)
- **Pages post-merge #254:** run `35438509913` **GREEN** (build + deploy)
- **Live status post-merge #254:** `ov-pages-live` **SUCCESS**
- **Branch corrente:** `chore/a3-2-ars-climate-evidence-batch`

## Residuo effettivo post-#254

Le **88** coppie residue sono distribuite su:

- `serie_storica`: 19
- `eta`: 17
- `categorie_specifiche`: 17
- `assoluto_normalizzato`: 12
- `sesso`: 6
- `benchmark_toscana_italia`: 5
- `numeratore_denominatore`: 5
- `frequenza_infra_annuale`: 4
- `dettaglio_territoriale`: 3

## Intervento corrente — batch ARS/clima

Il batch classifica **23** coppie metric-specific:

- **ARS Toscana:** **18** coppie su cronicità, ospedalizzazione, mortalità, assistenza e specialistica: **7 `AVAILABLE_MISSING`** per dimensioni esplicitamente offerte dalla fonte ma non acquisite (conteggi/tassi/componenti/cause/sesso) e **11 `SOURCE_UNAVAILABLE`** per classi d'età non esposte sulla stessa metrica comunale.
- **Speranza di vita alla nascita:** `lifeExpectancy × eta` è **`NOT_APPLICABLE`** perché una speranza di vita condizionata a una diversa età è un altro indicatore.
- **Trend climatici:** 4 coppie `categorie_specifiche` sono **`NOT_APPLICABLE`**; le metriche misurano singole variabili/trend e Tmin/Tmax sono già indicatori separati.

Nota: `chronicTotal × sesso` resta deliberatamente residuo perché l'evidenza ufficiale trovata non dimostra in modo sufficientemente diretto la disponibilità per l'aggregato specifico.

Tutti gli override sono additivi con `METRIC_EVIDENCE.setdefault(...).update(...)`; nessun profilo ARS eterogeneo viene classificato in blocco.

**Esito atteso:** **1.960 classificate / 65 residue**.

Composizione batch:

- `AVAILABLE_MISSING`: **7**
- `SOURCE_UNAVAILABLE`: **11**
- `NOT_APPLICABLE`: **5**

Residuo atteso dopo il batch:

- `serie_storica`: 19
- `categorie_specifiche`: 11
- `assoluto_normalizzato`: 10
- `sesso`: 5
- `eta`: 5
- `benchmark_toscana_italia`: 5
- `frequenza_infra_annuale`: 4
- `numeratore_denominatore`: 3
- `dettaglio_territoriale`: 3

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale di indicatori.
3. `ACQUIRED` solo da evidenza strutturata o formula verificata.
4. `AVAILABLE_MISSING` / `SOURCE_UNAVAILABLE` solo con evidenza ufficiale verificabile.
5. `NOT_APPLICABLE` solo metric-specific e semanticamente dimostrabile.
6. Classificazioni source-profile solo se valide per tutto il profilo.
7. A3.2 non è chiuso finché `unclassifiedPairCount = 0`.
8. Nessun A3.3 prima dello zero.
9. Preferire batch sostanziosi preparati prima dell'apertura PR per evitare cicli CI ripetuti.
10. Nessun merge/pubblicazione senza A3, Quick e Full GREEN sul final head e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Aprire una sola PR sul branch corrente.
2. Eseguire A3 Enrichment Audit + Quick + Full sul final head.
3. Verificare nel log A3 il conteggio esatto **1.960 / 65** e le 23 classificazioni.
4. Fermarsi prima del merge.
5. Dopo merge autorizzato, ricostruire le 65 residue e preparare il prossimo batch sostanzioso.
