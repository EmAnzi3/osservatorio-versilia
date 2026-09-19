# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato:** `ea22b9e6b6bce2d8472aef1d36ab1373385c156a` (merge `#247`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#247:** 2.025 coppie; **1.818 classificate, 207 residue**
- **A3 final head #247:** run `35401531994` **GREEN**
- **Pages final head #247:** run `35401531985` **GREEN** (Quick + Full)
- **Pages post-merge #247:** run `35420006901` **GREEN**
- **Live status post-merge #247:** run `35420279341` **GREEN**
- **Branch corrente:** `chore/a3-2-semantic-normalization-na`
- **PR corrente:** `#248`

## Residuo effettivo post-#247

Il bucket B è chiuso. Restano:

- **C — semanticamente `NOT_APPLICABLE`: 7**
- **D — verifica fonte ufficiale necessaria: 200**
- **Totale:** **207**

Le 7 C residue sono tutte sulla dimensione `assoluto_normalizzato`:

- `climateTemperatureTrend50y`
- `climateTmaxTrend`
- `climateTminTrend`
- `emsResponseTimeP75`
- `lifeExpectancy`
- `municipalImuStandard`
- `tariStandardHousehold`

## Intervento corrente — quarta tranche C

La PR `#248` chiude le ultime **7** coppie C su `assoluto_normalizzato`.

La definizione A3 richiede disponibilità congiunta di un valore assoluto e di una versione normalizzata coerente della **stessa misura**. Le metriche trattate sono:

- grandezze intensive fisiche (`climate*`);
- statistiche sintetiche già espresse nella propria scala (`emsResponseTimeP75`, `lifeExpectancy`);
- importi già standardizzati su uno scenario fisso (`municipalImuStandard`, `tariStandardHousehold`).

Una ulteriore normalizzazione per abitante, superficie, famiglia o percentuale cambierebbe l'oggetto metrico invece di produrre una seconda forma della stessa misura. Le classificazioni sono tutte metric-specific; nessuna regola `NOT_APPLICABLE` è applicata a un source profile.

**Esito atteso:** **1.825 classificate / 200 residue**.

Dopo la tranche:

- **C residue:** 0
- **D residue:** 200

La chiusura di C non chiude A3.2: si passa al bucket D e A3.2 termina solo a `unclassifiedPairCount = 0`.

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

1. Portare `#248` a A3 Enrichment Audit, Quick e Full GREEN sul final head.
2. Verificare nel log A3 il conteggio esatto **1.825 / 200** e le 7 nuove coppie `NOT_APPLICABLE`.
3. Fermarsi prima del merge.
4. Dopo merge autorizzato, ricostruire le **200 D residue effettive** dalla matrice e dalla closure audit.
5. Classificare D solo con verifica della fonte ufficiale in `AVAILABLE_MISSING` o `SOURCE_UNAVAILABLE` (o riclassificare A/B se emerge evidenza strutturata già acquisita).
6. Nessun A3.3 prima di `unclassifiedPairCount = 0`.
