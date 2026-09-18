# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato:** `ee82faeed8c4052b8ebc47d4c8ac2c7ce91f4d81` (merge `#244`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#244:** 2.025 coppie; **1.791 classificate, 234 residue**
- **A3 final head #244:** run `35387050718` **GREEN**
- **Pages final head #244:** run `35387050727` **GREEN**
- **Pages post-merge #244:** run `35391343566` **GREEN**
- **Branch corrente:** `chore/a3-2-semantic-territory-na`
- **PR corrente:** `#245`

## Residuo effettivo post-#244

Il bucket B cross-source/companion è chiuso.

Restano:

- **C — semanticamente `NOT_APPLICABLE`: 34**
- **D — verifica fonte ufficiale necessaria: 200**
- **Totale:** **234**

La closure audit diagnostica assegna C esclusivamente con override metric-specific, mai a livello source-profile.

## Intervento corrente — prima tranche C

La tranche chiude **14 coppie** ad alta confidenza: `sesso` e `eta` su sette metriche che misurano esclusivamente superficie, composizione fisica del territorio o siti.

Metriche:

- `agriculturalUsedArea`
- `averageAgriculturalFarmSize`
- `cropProfile`
- `irrigatedAgriculturalArea`
- `forestCoverIndex`
- `landCoverProfile`
- `extractiveSites`

Per queste metriche sesso/età descriverebbero eventualmente soggetti collegati (conduttori, operatori), non l'oggetto metrico pubblicato. L'audit originario individua esplicitamente come C superfici agricole, dimensione media aziendale, profili colturali, copertura/uso del suolo e cave.

**Esito atteso:** **1.805 classificate / 220 residue**.

Dopo la tranche:

- **C residue:** 20
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

1. Portare `#245` a A3 Enrichment Audit, Quick e Full GREEN sul final head.
2. Verificare nel log A3 il conteggio esatto **1.805 / 220** e le 14 coppie `NOT_APPLICABLE`.
3. Fermarsi prima del merge.
4. Dopo merge autorizzato, ricostruire le 20 C residue effettive e proseguire per sottogruppi semantici omogenei.
5. Solo dopo C=0 passare al bucket D.
6. A3.2 termina soltanto a `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
