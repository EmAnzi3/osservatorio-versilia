# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.5` — integrazione nuove dimensioni in lotti controllati
- **Stato:** `IN_PROGRESS` — lotto 1 demografia/sesso mergiato; selezione lotto 2 dal backlog A3.4 LIVE
- **Main verificato:** `ee86142708a0c42731c67a1b12eb925902bc388d` (merge `#260`)
- **Final head #260:** `e54b90143aa636db5b53386f401e52130016642d`
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2:** 2.025 coppie; **2.025 classificate, 0 residue**
- **A3 final head #260:** run `35458115502` **GREEN**
- **Pages final head #260:** run `35458115505` **GREEN**
- **Controllo mensile dati final head #260:** run `35458115508` **GREEN**
- **Controllo frequente fonti final head #260:** run `35458115532` **GREEN**
- **Branch corrente:** `feat/a3-5-enrichment-lot-2`

## A3.5 — stato acquisizioni

Il lotto 1, mergiato con PR **#260**, ha acquisito dal backlog A3.4:

- `population × sesso`;
- `dependencyIndices × sesso`;
- `foreignResidents × sesso`.

Fonti governate:

- Istat POSAS 2026: `data/source-snapshots/istat-demography-lotto-a-2026-08.json`;
- Istat RCS 2025: `data/source-snapshots/istat-rcs-demography-2025.json`.

Le tre coppie sono materializzate nel dataset pubblico come `sexDimension` e devono risultare `ACQUIRED / catalog_structure`. A3.5 resta `IN_PROGRESS`.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale di indicatori, fonti o opportunità.
3. A3.2 resta strict a `unclassifiedPairCount = 0`.
4. Un passaggio a `ACQUIRED` deve derivare da struttura/formula verificabile, mai da override manuale.
5. A3.5 procede per lotti sostanziali ricavati dal backlog A3.4, con QA e fonte dichiarata.
6. Non introdurre UI/rendering se il lotto riguarda soltanto enrichment del dataset.
7. Nessun merge/pubblicazione senza A3, Quick e Full GREEN sul final head e approvazione esplicita del proprietario.
8. Non dichiarare preflight locale eseguito se il runtime continua a fallire su `Could not resolve host: github.com`.

## Prossima azione esatta

1. Leggere l'artifact A3.4 rigenerato sul final head di #260 e verificare il conteggio LIVE delle `AVAILABLE_MISSING`.
2. Ordinare i pacchetti `sourceProfileId × dimensione` secondo la rubric A3.4 già governata.
3. Scegliere il prossimo lotto A3.5 sostanziale esclusivamente dal backlog LIVE, verificando prima disponibilità e acquisibilità reale delle fonti.
4. Implementare materializzazione, QA ed evidenza A3 sul presente branch.
5. Aggiornare roadmap e questo handoff nella stessa PR.
6. Aprire una sola PR Ready ed eseguire A3 + Quick + Full sul final head.
7. Fermarsi prima del merge.
