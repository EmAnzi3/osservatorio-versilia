# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.5` — integrazione nuove dimensioni in lotti controllati
- **Stato:** `IN_PROGRESS` — lotto 1 mergiato; lotto 2 OpenBDAP numeratore/denominatore in PR **#261 Ready**, in attesa dei gate final-head
- **Main verificato:** `ee86142708a0c42731c67a1b12eb925902bc388d` (merge `#260`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2:** 2.025 coppie; **2.025 classificate, 0 residue**
- **Backlog A3.4 post-#260:** **869 AVAILABLE_MISSING · 263 pacchetti · 63 source profile**
- **Branch corrente:** `feat/a3-5-enrichment-lot-2` · PR **#261** Ready
- **Merge/pubblicazione:** vietati senza A3 + Quick + Full GREEN sul final head e approvazione esplicita del proprietario

## A3.5 — acquisizioni

### Lotto 1 — mergiato con #260

Acquisite `population × sesso`, `dependencyIndices × sesso`, `foreignResidents × sesso` da snapshot Istat POSAS/RCS già versionati. Le tre coppie risultano `ACQUIRED / catalog_structure` tramite `sexDimension`.

### Lotto 2 — branch corrente

Dal backlog LIVE è stato selezionato il pacchetto ad alto valore `openbdap-annual × numeratore_denominatore`. Vengono acquisite **16 delle 24 coppie** per cui entrambi i componenti sono realmente presenti negli snapshot versionati:

- 14 indicatori da `data/source-snapshots/bilanci-v1.6.0.json`;
- `cashReceiptsPerResident` e `cashBalancePerResident` da `data/source-snapshots/siope-history-v1.6.0.json`.

Il materializzatore aggiunge `ratioComponents` a 7/7 Comuni con numeratore, denominatore, scala, anno, fonte e snapshot e riconcilia la formula con il valore pubblico. Non modifica valori, grafici o layout.

Le altre 8 coppie dello stesso pacchetto restano `AVAILABLE_MISSING`: gli snapshot correnti non contengono entrambi i componenti richiesti e non è ammesso ricavarli a ritroso dal rapporto pubblicato.

Effetto atteso A3.4/A3.5 sul final head:

`AVAILABLE_MISSING: 869 → 853`

A3.5 resta `IN_PROGRESS`.

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

1. Verificare A3 + Quick + Full sul final head della PR #261.
2. Dall'artifact A3.4 final-head confermare `853 AVAILABLE_MISSING` e `unclassifiedPairCount = 0`.
3. Correggere soltanto eventuali regressioni reali, senza indebolire detector o contratti.
4. Fermarsi prima del merge e attendere approvazione esplicita del proprietario.
