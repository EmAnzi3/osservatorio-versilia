# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato:** `a9af31cb3d49bdd7b01d5b74f477d0be5aed22c6` (merge `#245`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#245:** 2.025 coppie; **1.805 classificate, 220 residue**
- **A3 final head #245:** run `35392398929` **GREEN**
- **Pages final head #245:** run `35392398977` **GREEN**
- **Pages post-merge #245:** run `35395004156` **GREEN**
- **Branch corrente:** `chore/a3-2-semantic-direct-metrics-na`
- **PR corrente:** `#246`

## Residuo effettivo post-#245

Il bucket B è chiuso. Dopo la prima tranche C restano:

- **C — semanticamente `NOT_APPLICABLE`: 20**
- **D — verifica fonte ufficiale necessaria: 200**
- **Totale:** **220**

Distribuzione C ancora da chiudere:

- `sesso`: 3
- `eta`: 3
- `assoluto_normalizzato`: 7
- `numeratore_denominatore`: 7

## Intervento corrente — seconda tranche C

La tranche chiude tutte le **7** residue C sulla dimensione `numeratore_denominatore`.

La definizione A3 limita questa dimensione alle componenti che generano un rapporto, tasso, quota o indice pubblicato. Le sette metriche qui trattate sono invece valori diretti/statistiche non definite in tale forma:

- `emsResponseTimeP75` — percentile temporale in minuti;
- `extractiveSites` — conteggio diretto di siti;
- `hospitals` — conteggio diretto di presidi;
- `lifeExpectancy` — indicatore sintetico di tavola di mortalità espresso in anni;
- `municipalStaffTraining` — valori e medie RGS pubblicati, non un rapporto A3 con componenti dichiarate;
- `population` — conteggio diretto di residenti;
- `tourismBeds` — conteggio diretto di posti letto.

Le classificazioni sono tutte metric-specific; nessuna regola `NOT_APPLICABLE` viene applicata a un source profile.

**Esito atteso:** **1.812 classificate / 213 residue**.

Dopo la tranche:

- **C residue:** 13
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

1. Portare `#246` a A3 Enrichment Audit, Quick e Full GREEN sul final head.
2. Verificare nel log A3 il conteggio esatto **1.812 / 213** e le 7 coppie `NOT_APPLICABLE`.
3. Fermarsi prima del merge.
4. Dopo merge autorizzato, ricostruire le 13 C residue effettive e chiuderle per sottogruppi semantici omogenei.
5. Solo dopo C=0 passare al bucket D.
6. A3.2 termina soltanto a `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
