# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.5` — integrazione nuove dimensioni in lotti controllati
- **Stato:** `IN_PROGRESS` — lotti 1 e 2 mergiati; lotto 3 Frame SBS in lavorazione
- **Main verificato:** `36359352cf6d7fe74592768b71d473ce84d6807a` (merge `#261`)
- **Deploy post-#261:** `35465415565` GREEN
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2:** 2.025 coppie; **2.025 classificate, 0 residue**
- **Backlog A3.4 post-#261:** **853 AVAILABLE_MISSING · 263 pacchetti · 63 source profile**
- **Branch corrente:** `feat/a3-5-enrichment-lot-3`
- **Merge/pubblicazione:** vietati senza A3 + Quick + Full GREEN sul final head e approvazione esplicita del proprietario

## A3.5 — acquisizioni

### Lotto 1 — mergiato con #260

Acquisite `population × sesso`, `dependencyIndices × sesso`, `foreignResidents × sesso` da snapshot Istat POSAS/RCS già versionati. Le tre coppie risultano `ACQUIRED / catalog_structure` tramite `sexDimension`.

### Lotto 2 — mergiato con #261

Acquisite **16 coppie** `openbdap-annual × numeratore_denominatore` per cui entrambi i componenti sono presenti negli snapshot versionati OpenBDAP/SIOPE. La struttura `ratioComponents` riconcilia ogni formula senza retro-derivare componenti dal rapporto pubblicato.

Backlog verificato sul final head #261:

`AVAILABLE_MISSING: 869 → 853`

### Lotto 3 — in lavorazione

Dal backlog A3.4 LIVE è stato selezionato un lotto coerente sul profilo `istat-business-annual`, riusando esclusivamente gli snapshot Frame SBS Territoriale Istat v1.34 già versionati.

Per gli 8 indicatori Economia prodotta il lotto punta ad acquisire **20 coppie**:
- 8 × `categorie_specifiche`: perimetri Frame SBS `Totale / Industria / Servizi` già materializzati in `economicScopes`;
- 8 × `assoluto_normalizzato`: valore assoluto e misura normalizzata coerente dai componenti Frame SBS;
- 4 × `numeratore_denominatore`: componenti verificabili per produttività, fatturato/addetto, valore aggiunto/fatturato e retribuzione media/dipendente.

I valori pubblici restano autoritativi; le riconciliazioni ammettono esclusivamente le tolleranze motivate dall'arrotondamento delle tavole Istat. Effetto atteso, da confermare dai gate:

`AVAILABLE_MISSING: 853 → 833`

A3.5 resta `IN_PROGRESS`; A3.6 non viene avviato.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale di indicatori, fonti o opportunità.
3. A3.2 resta strict a `unclassifiedPairCount = 0`.
4. Un passaggio a `ACQUIRED` deve derivare da struttura/formula verificabile, mai da override manuale.
5. A3.5 procede per lotti sostanziali ricavati dal backlog A3.4, con QA e fonte dichiarata.
6. Non introdurre UI/rendering se il lotto riguarda soltanto enrichment del dataset.
7. Non retro-derivare componenti mancanti da percentuali/rapporti già pubblicati.
8. Non dichiarare preflight locale eseguito se il runtime continua a fallire su risoluzione DNS verso GitHub/fonti esterne.

## Prossima azione esatta

1. Implementare e testare il materializzatore A3.5 Frame SBS sulle 20 coppie candidate.
2. Registrarlo nei contratti build/Quick e nel workflow A3 senza indebolire i detector.
3. Aggiornare la roadmap nello stesso branch.
4. Aprire PR Ready e verificare A3 + Quick + Full sullo stesso final head.
5. Confermare dall'artifact A3.4 il nuovo conteggio e fermarsi prima del merge.
