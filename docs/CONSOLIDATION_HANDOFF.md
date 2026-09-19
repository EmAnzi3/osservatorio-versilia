# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato:** `f3abad3dd3b9fd89bcbae55e7f34da99303130ac` (merge `#255`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#255:** 2.025 coppie; **1.960 classificate, 65 residue**
- **A3 final head #255:** run `35439271702` **GREEN**
- **Pages final head #255:** run `35439271705` **GREEN** (Quick + Full)
- **Pages post-merge #255:** run `35440479037` **GREEN** (build + deploy)
- **Live status post-merge #255:** `ov-pages-live` **SUCCESS**
- **Branch corrente:** `chore/a3-2-territorial-services-evidence-batch`

## Residuo effettivo post-#255

Le **65** coppie residue sono distribuite su:

- `serie_storica`: 19
- `categorie_specifiche`: 11
- `assoluto_normalizzato`: 10
- `sesso`: 5
- `eta`: 5
- `benchmark_toscana_italia`: 5
- `frequenza_infra_annuale`: 4
- `numeratore_denominatore`: 3
- `dettaglio_territoriale`: 3

## Intervento corrente — batch territoriale/servizi

Il batch classifica **22** coppie metric-specific su sette famiglie:

- **Istat / sicurezza stradale:** 5 coppie. Valori assoluti e componenti di `roadSafety` sono disponibili ma non acquisiti (**2 `AVAILABLE_MISSING`**); sesso/età non sono disponibili con la stessa granularità comunale e la disaggregazione dei proventi da sanzioni non è sufficientemente affidabile (**3 `SOURCE_UNAVAILABLE`**).
- **Regione Toscana — PNRR:** 4 coppie. Importo assoluto e componenti della misura per residente sono disponibili (**2 `AVAILABLE_MISSING`**); il dataset mensile espone lo stato corrente ma non una serie storica ufficiale di snapshot (**2 `SOURCE_UNAVAILABLE`**).
- **Regione Toscana — Biblioteche:** 3 coppie. Categorie di prestito e fasce di apertura sono disponibili (**2 `AVAILABLE_MISSING`**); per gli iscritti attivi, oltre alle classi di età già trattate, non risultano ulteriori categorie comparabili (**1 `SOURCE_UNAVAILABLE`**).
- **Regione Toscana — Uso e Copertura del Suolo:** dettaglio poligonale e benchmark Toscana disponibili (**2 `AVAILABLE_MISSING`**); nessuna frequenza infra-annuale (**1 `SOURCE_UNAVAILABLE`**).
- **Regione Toscana — RTCave:** benchmark Toscana disponibile (**1 `AVAILABLE_MISSING`**); serie storica, misura normalizzata e osservazioni infra-annuali storicizzate non disponibili (**3 `SOURCE_UNAVAILABLE`**).
- **Istat — pendolarismo:** conteggi assoluti companion di `outsideMunicipality` e `selfContainment` disponibili (**2 `AVAILABLE_MISSING`**).
- **Regione Toscana — turismo:** `tourismArrivals × assoluto_normalizzato` è **`SOURCE_UNAVAILABLE`** perché la fonte pubblica gli arrivi assoluti ma non una normalizzazione ufficiale coerente.

Tutti gli override sono additivi con `METRIC_EVIDENCE.setdefault(...).update(...)`; nessun nuovo `EVIDENCE.update(...)` è stato introdotto.

**Esito atteso:** **1.982 classificate / 43 residue**.

Composizione batch:

- `AVAILABLE_MISSING`: **11**
- `SOURCE_UNAVAILABLE`: **11**

Residuo atteso dopo il batch:

- `serie_storica`: 16
- `categorie_specifiche`: 7
- `sesso`: 4
- `eta`: 4
- `assoluto_normalizzato`: 4
- `benchmark_toscana_italia`: 3
- `dettaglio_territoriale`: 2
- `frequenza_infra_annuale`: 2
- `numeratore_denominatore`: 1

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
3. Verificare nel log A3 il conteggio esatto **1.982 / 43** e le 22 classificazioni.
4. Fermarsi prima del merge.
5. Dopo merge autorizzato, ricostruire le 43 residue e preparare il prossimo batch sostanzioso.
