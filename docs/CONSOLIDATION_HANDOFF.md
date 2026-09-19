# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato:** `4628c3514cc83b2f404dcfc9ed61224307fba82c` (merge `#251`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#251:** 2.025 coppie; **1.890 classificate, 135 residue**
- **A3 final head #251:** run `35430634616` **GREEN**
- **Pages final head #251:** run `35430634633` **GREEN** (Quick + Full)
- **Pages post-merge #251:** run `35431884819` **GREEN**
- **Live status post-merge #251:** run `35432134481` **GREEN**
- **Branch corrente:** `chore/a3-2-scalar-tourism-evidence-batch`

## Residuo effettivo post-#251

Le **135** coppie residue sono distribuite su:

- `assoluto_normalizzato`: 25
- `categorie_specifiche`: 25
- `serie_storica`: 24
- `eta`: 21
- `numeratore_denominatore`: 11
- `frequenza_infra_annuale`: 10
- `sesso`: 9
- `benchmark_toscana_italia`: 6
- `dettaglio_territoriale`: 4

## Intervento corrente — batch scalar/tourism

Il batch classifica **24** coppie con evidenza ufficiale verificata e solo override metric-specific:

- **Regione Toscana — Indicatori comunali:** 19 coppie residue su 7 metriche (`assoluto_normalizzato`, `numeratore_denominatore`, `categorie_specifiche`) come `SOURCE_UNAVAILABLE`; la batteria ufficiale diffonde gli indicatori comunali sintetici e i metadati, ma non i companion assoluti/componenti/disaggregazioni richiesti per queste specifiche metriche.
- **Istat — capacità degli esercizi ricettivi:** 4 coppie di `tourismBeds` come `AVAILABLE_MISSING`: serie storica, dettaglio territoriale, benchmark Toscana/Italia e tipologie ricettive sono disponibili nella rilevazione ufficiale ma non acquisite strutturalmente dalla pipeline corrente.
- **Regione Toscana / InfoCamere — Banca dati Imprese:** `economyActivityAtlas × frequenza_infra_annuale` come `AVAILABLE_MISSING`; la fonte ufficiale espone dati dell'anno in corso all'ultimo trimestre disponibile e serie storiche trimestrali.

Nessuna nuova classificazione source-profile è introdotta; gli override si aggiungono con `METRIC_EVIDENCE.setdefault(...).update(...)` e preservano tutta l'evidenza precedente.

**Esito atteso:** **1.914 classificate / 111 residue**.

Composizione batch:

- `AVAILABLE_MISSING`: **5**
- `SOURCE_UNAVAILABLE`: **19**
- `NOT_APPLICABLE`: **0**

Residuo atteso dopo il batch:

- `serie_storica`: 23
- `eta`: 21
- `assoluto_normalizzato`: 19
- `categorie_specifiche`: 17
- `sesso`: 9
- `frequenza_infra_annuale`: 9
- `benchmark_toscana_italia`: 5
- `numeratore_denominatore`: 5
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
3. Verificare nel log A3 il conteggio esatto **1.914 / 111** e le 24 classificazioni.
4. Fermarsi prima del merge.
5. Dopo merge autorizzato, ricostruire le 111 residue e preparare il prossimo batch sostanzioso.
