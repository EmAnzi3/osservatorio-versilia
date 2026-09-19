# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato:** `42711dc8e9ba2291c6612c39dcfb5d44169f9c47` (merge `#248`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#248:** 2.025 coppie; **1.825 classificate, 200 residue**
- **A3 final head #248:** run `35423110733` **GREEN**
- **Pages final head #248:** run `35423110753` **GREEN** (Quick + Full)
- **Pages post-merge #248:** run `35424503833` **GREEN**
- **Live status post-merge #248:** run `35424781973` **GREEN**
- **Bucket C:** **0**
- **Bucket D:** **200**
- **Branch corrente:** `chore/a3-2-annual-source-frequency-unavailable`
- **PR corrente:** da aprire

## Residuo effettivo post-#248

Le **200** coppie residue coincidono con il bucket D: richiedono verifica della fonte ufficiale e classificazione in `AVAILABLE_MISSING` o `SOURCE_UNAVAILABLE`, salvo nuova evidenza strutturata che dimostri `ACQUIRED`.

Distribuzione per dimensione:

- `frequenza_infra_annuale`: 45
- `eta`: 36
- `assoluto_normalizzato`: 25
- `categorie_specifiche`: 25
- `serie_storica`: 24
- `sesso`: 24
- `numeratore_denominatore`: 11
- `benchmark_toscana_italia`: 6
- `dettaglio_territoriale`: 4

## Intervento corrente — prima tranche D

La tranche classifica come `SOURCE_UNAVAILABLE` quattro coppie `frequenza_infra_annuale` appartenenti a profili interamente annuali:

- `municipalImuStandard` — `mef-municipal-tax-annual`
- `tariStandardHousehold` — `mef-municipal-tax-annual`
- `tourismBeds` — `istat-tourism-annual`
- `erpArrears` — `erp-lucca-annual-balance-sheet`

La regola è applicata a livello source-profile solo perché la cadenza annuale è valida per l'intero profilo ed è documentata dalla fonte ufficiale.

**Esito atteso:** **1.829 classificate / 196 residue**.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale di indicatori.
3. `ACQUIRED` solo da evidenza strutturata o formula verificata.
4. `AVAILABLE_MISSING` / `SOURCE_UNAVAILABLE` solo con evidenza ufficiale verificabile.
5. `NOT_APPLICABLE` solo metric-specific e semanticamente dimostrabile.
6. Classificazioni source-profile solo se valide per tutto il profilo.
7. A3.2 non è chiuso finché `unclassifiedPairCount = 0`.
8. Nessun A3.3 prima dello zero.
9. Nessun merge/pubblicazione senza A3, Quick e Full GREEN sul final head e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Aprire la PR della prima tranche D.
2. Portare A3 Enrichment Audit, Quick e Full GREEN sul final head.
3. Verificare nel log A3 il conteggio esatto **1.829 / 196** e le quattro classificazioni `SOURCE_UNAVAILABLE`.
4. Fermarsi prima del merge.
5. Dopo merge autorizzato, ricostruire le 196 residue e scegliere la tranche D successiva per evidenza ufficiale omogenea.
