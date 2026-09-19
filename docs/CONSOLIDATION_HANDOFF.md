# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato:** `c8dbe2e076425cd847477925461c8cf5884d1051` (merge `#246`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#246:** 2.025 coppie; **1.812 classificate, 213 residue**
- **A3 final head #246:** run `35396490755` **GREEN**
- **Pages final head #246:** run `35396490786` **GREEN** (Quick + Full)
- **Branch corrente:** `chore/a3-2-semantic-nonperson-demographics-na`
- **PR corrente:** `#247`

## Residuo effettivo post-#246

Il bucket B è chiuso. Restano:

- **C — semanticamente `NOT_APPLICABLE`: 13**
- **D — verifica fonte ufficiale necessaria: 200**
- **Totale:** **213**

Distribuzione C ancora da chiudere:

- `sesso`: 3 — `economyActivityAtlas`, `erpArrears`, `roadFinesPerResident`
- `eta`: 3 — stesse tre metriche
- `assoluto_normalizzato`: 7 — `climateTemperatureTrend50y`, `climateTmaxTrend`, `climateTminTrend`, `emsResponseTimeP75`, `lifeExpectancy`, `municipalImuStandard`, `tariStandardHousehold`

## Intervento corrente — terza tranche C

La PR `#247` chiude le **6** coppie `sesso/eta` su tre metriche il cui oggetto pubblicato non è una persona:

- `economyActivityAtlas` — attività economiche/codici ATECO;
- `erpArrears` — grandezza economica di morosità ERP;
- `roadFinesPerResident` — proventi da sanzioni rapportati alla popolazione residente media.

Sesso ed età descriverebbero eventualmente persone collegate all'oggetto (imprenditori, assegnatari/debitori, trasgressori o residenti), non la metrica pubblicata. Le classificazioni sono tutte metric-specific; nessuna regola `NOT_APPLICABLE` è applicata a un source profile.

**Esito atteso:** **1.818 classificate / 207 residue**.

Dopo la tranche:

- **C residue:** 7
- **D residue:** 200

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale di indicatori.
3. `ACQUIRED` solo da evidenza strutturata o formula verificata.
4. `AVAILABLE_MISSING` / `SOURCE_UNAVAILABLE` solo con evidenza ufficiale verificabile.
5. `NOT_APPLICABLE` deve essere metric-specific e semanticamente dimostrabile.
6. Nessun source-profile `NOT_APPLICABLE` eterogeneo.
7. A3.2 non è chiuso finché `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
8. Nessun merge/pubblicazione senza A3, Quick e Full GREEN sul final head e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Portare `#247` a A3 Enrichment Audit, Quick e Full GREEN sul final head.
2. Verificare nel log A3 il conteggio esatto **1.818 / 207** e le 6 coppie `NOT_APPLICABLE`.
3. Fermarsi prima del merge.
4. Dopo merge autorizzato, chiudere le **7 C residue** su `assoluto_normalizzato` con una tranche metric-specific separata.
5. Solo dopo C=0 passare al bucket D.
6. A3.2 termina soltanto a `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
