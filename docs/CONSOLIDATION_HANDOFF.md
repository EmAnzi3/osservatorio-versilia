# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.5` — integrazione nuove dimensioni in lotti controllati
- **Stato:** `IN_PROGRESS` — lotto 1 demografia/sesso
- **Main verificato:** `466e370a233e78c074f97bf145f7d8794a4c1dbc` (merge `#259`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2:** 2.025 coppie; **2.025 classificate, 0 residue**
- **A3 final head #259:** run `35451203191` **GREEN**
- **Pages final head #259:** run `35451203130` **GREEN**
- **Live status post-merge #259:** run `35452607256` / `ov-pages-live` **GREEN**
- **A3.4 backlog post-#259:** **872 AVAILABLE_MISSING → 263 pacchetti su 63 profili**
- **Branch corrente:** `feat/a3-5-demography-sex-enrichment`

## Intervento corrente — A3.5 lotto 1

Il lotto integra realmente tre dimensioni oggi presenti nel backlog `istat-demography-annual × sesso`:

- `population × sesso`;
- `dependencyIndices × sesso`;
- `foreignResidents × sesso`.

Fonti già versionate e governate:

- Istat POSAS 2026: `data/source-snapshots/istat-demography-lotto-a-2026-08.json`;
- Istat RCS 2025: `data/source-snapshots/istat-rcs-demography-2025.json`.

Il nuovo materializzatore pubblico aggiunge `sexBreakdown` a righe comunali e aggregato Versilia con anno, unità e fonte. Il QA riconcilia i totali, ricalcola gli indici di dipendenza per sesso e verifica che il detector A3 classifichi le tre coppie come `ACQUIRED` da struttura del catalogo. L'effetto atteso è **872 → 869 AVAILABLE_MISSING**; A3.5 non si chiude con questo lotto.

## Hardening #259 incluso

Nello stesso PR vengono chiusi i due P2 validi emersi dalla review di #259:

1. la rubric A3.4 usa chiavi JSON stabili e viene validata anche dopo serializzazione/deserializzazione;
2. il regression test A3.4 e il nuovo test A3.5 entrano nel preflight canonico Quick/Full, oltre al workflow A3.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale di indicatori, fonti o opportunità.
3. A3.2 resta strict a `unclassifiedPairCount = 0`.
4. Un passaggio a `ACQUIRED` deve derivare da struttura/formula verificabile, mai da override manuale.
5. A3.5 procede per lotti piccoli ma sostanziali, con QA e fonte dichiarata; nessuna acquisizione opportunistica fuori backlog.
6. Questo lotto modifica il dataset pubblico materializzato; non introduce un nuovo controllo UI dedicato.
7. Nessun merge/pubblicazione senza A3, Quick e Full GREEN sul final head e approvazione esplicita del proprietario.
8. Il preflight locale non è stato eseguito: il runtime restituisce ancora `Could not resolve host: github.com` su `git ls-remote`.

## Prossima azione esatta

1. Completare il branch corrente e aprire una sola PR Ready.
2. Eseguire un unico ciclo A3 Enrichment Audit + Quick + Full sul final head.
3. Verificare matrice **2.025 / 0**.
4. Verificare `population`, `dependencyIndices`, `foreignResidents` × `sesso` = `ACQUIRED` / `catalog_structure`.
5. Verificare backlog A3.4 rigenerato a **869 AVAILABLE_MISSING** e assenza delle tre coppie dal backlog.
6. Verificare artifact A3.3/A3.4 e assenza di regressioni Quick/Full.
7. Fermarsi prima del merge.
