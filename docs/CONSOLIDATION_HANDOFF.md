# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato:** `0eab4a474518bd2c2d46e6f68041dd747c44bc43` (merge `#250`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#250:** 2.025 coppie; **1.860 classificate, 165 residue**
- **A3 final head #250:** run `35427835657` **GREEN**
- **Pages final head #250:** run `35427835778` **GREEN** (Quick + Full)
- **Pages post-merge #250:** run `35429886826` **GREEN**
- **Live status post-merge #250:** run `35430142810` **GREEN**
- **Branch corrente:** `chore/a3-2-demographic-evidence-batch`

## Residuo effettivo post-#250

Le **165** coppie residue sono distribuite su:

- `eta`: 36
- `assoluto_normalizzato`: 25
- `categorie_specifiche`: 25
- `serie_storica`: 24
- `sesso`: 24
- `numeratore_denominatore`: 11
- `frequenza_infra_annuale`: 10
- `benchmark_toscana_italia`: 6
- `dettaglio_territoriale`: 4

## Intervento corrente — batch demografico D

Il batch classifica **30** coppie `sesso/eta` con evidenza ufficiale, senza regole source-profile eterogenee:

- **Regione Toscana — Indicatori comunali:** 14 coppie su 7 metriche. I metadati ufficiali pubblicano valori comunali scalari; 8 coppie informative ma non disponibili sono `SOURCE_UNAVAILABLE`, 6 coppie non semanticamente pertinenti sono `NOT_APPLICABLE`.
- **Istat — Frame SBS Territoriale:** 8 coppie su 4 indicatori economici, tutte `SOURCE_UNAVAILABLE`; il rilascio territoriale espone territorio, attività economica, dimensione e governance ma non sesso/età per gli indicatori comunali.
- **Regione Toscana — Biblioteche:** 6 coppie. `libraryActiveBorrowersPer100 × eta` è `AVAILABLE_MISSING` perché il tracciato espone 0-14, 15-24, 25-64, 65+; tre coppie sono `SOURCE_UNAVAILABLE`; gli orari di apertura per sesso/età sono `NOT_APPLICABLE`.
- **Istat — capacità ricettiva:** `tourismBeds × sesso/eta` è `NOT_APPLICABLE`.

**Esito atteso:** **1.890 classificate / 135 residue**.

Composizione batch:

- `AVAILABLE_MISSING`: **1**
- `SOURCE_UNAVAILABLE`: **19**
- `NOT_APPLICABLE`: **10**

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
2. Eseguire un solo ciclo A3 Enrichment Audit + Quick + Full sul final head.
3. Verificare nel log A3 il conteggio esatto **1.890 / 135** e le 30 classificazioni.
4. Fermarsi prima del merge.
5. Dopo merge autorizzato, ricostruire le 135 residue e preparare il prossimo batch sostanzioso.
