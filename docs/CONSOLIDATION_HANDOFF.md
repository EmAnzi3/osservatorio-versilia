# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato:** `c9e838584d0bd39a27a1117731dd91a1ff4d86be` (merge `#253`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#253:** 2.025 coppie; **1.914 classificate, 111 residue**
- **A3 final head #253:** run `35432864404` **GREEN**
- **Pages final head #253:** run `35432864391` **GREEN** (Quick + Full)
- **Pages post-merge #253:** run `35434707060` **GREEN** (build + deploy)
- **Live status post-merge #253:** `ov-pages-live` **SUCCESS**
- **Branch corrente:** `chore/a3-2-operational-social-evidence-batch`

## Residuo effettivo post-#253

Le **111** coppie residue sono distribuite su:

- `serie_storica`: 23
- `eta`: 21
- `assoluto_normalizzato`: 19
- `categorie_specifiche`: 17
- `sesso`: 9
- `frequenza_infra_annuale`: 9
- `benchmark_toscana_italia`: 5
- `numeratore_denominatore`: 5
- `dettaglio_territoriale`: 3

## Intervento corrente — batch operativo/sociale/turismo

Il batch classifica **23** coppie metric-specific su più famiglie ufficiali:

- **Consorzio 1 Toscana Nord — PMO 2026:** 12 coppie. Date operative di inizio/fine rendono disponibili ma non materializzate serie e frequenza infra-annuale per i quattro indicatori di stato (**8 `AVAILABLE_MISSING`**); la fonte non definisce una normalizzazione ufficiale dei conteggi/importi (**4 `SOURCE_UNAVAILABLE`**).
- **Istat — A misura di Comune, spesa sociale:** `sesso/eta` per `socialSpendingByUserArea` e `socialSpendingPerResident` (**4 `SOURCE_UNAVAILABLE`**); le tavole 10a/10b non pubblicano queste stesse metriche per sesso o classi di età.
- **MEF — contribuenti comunali:** `taxpayersAdultPopulationRate × sesso/eta` (**2 `SOURCE_UNAVAILABLE`**); il numero contribuenti comunale non è incrociato con le classificazioni di sesso/età.
- **RGS — formazione personale:** `municipalStaffTraining × eta` (**1 `SOURCE_UNAVAILABLE`**); la fonte espone Totale/Uomini/Donne ma non classi d'età.
- **Regione Toscana — turismo 2025:** **3 `AVAILABLE_MISSING`** (`foreignTourismShare × assoluto_normalizzato`, `tourismIntensity × frequenza_infra_annuale`, `tourismSeasonality × assoluto_normalizzato`) e **1 `NOT_APPLICABLE`** (`tourismAverageStay × assoluto_normalizzato`).

Tutti gli override sono additivi con `METRIC_EVIDENCE.setdefault(...).update(...)`; nessun profilo eterogeneo viene classificato in blocco e nessun `ACQUIRED` è dichiarato manualmente.

**Esito atteso:** **1.937 classificate / 88 residue**.

Composizione batch:

- `AVAILABLE_MISSING`: **11**
- `SOURCE_UNAVAILABLE`: **11**
- `NOT_APPLICABLE`: **1**

Residuo atteso dopo il batch:

- `serie_storica`: 19
- `eta`: 17
- `categorie_specifiche`: 17
- `assoluto_normalizzato`: 12
- `sesso`: 6
- `benchmark_toscana_italia`: 5
- `numeratore_denominatore`: 5
- `frequenza_infra_annuale`: 4
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
3. Verificare nel log A3 il conteggio esatto **1.937 / 88** e le 23 classificazioni.
4. Fermarsi prima del merge.
5. Dopo merge autorizzato, ricostruire le 88 residue e preparare il prossimo batch sostanzioso.
