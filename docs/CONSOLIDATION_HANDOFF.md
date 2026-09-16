# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `e35dd64e56b03da78dc983be32b69ae8488ee529`
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Branch:** `chore/a3-enrichment-audit-foundation`
- **PR corrente:** `#204` — Ready

## Completato

- `A0` chiuso con merge autorizzato della PR `#188`.
- `A1 — Data Governance Foundation` chiuso con le PR `#190` e `#193`.
- `A2.1`–`A2.3` hanno portato il monitor sul catalogo pubblico effettivo e separato controllo light frequente e deep periodico.
- La PR `#194` ha implementato `A2.4`–`A2.7`: strategia derivata per fonte, report operativo, visibilità GitHub Actions/artifact e gate sulla copertura applicabile.
- Gli interventi successivi `#195`–`#203` e il refresh dati `#202` hanno irrobustito acquisizione AGCOM, refresh e gate senza indebolire i contratti A2.
- `A2 — Full Coverage Source Monitor` è formalmente `DONE`.
- `A3.1` completato: `docs/A3_ENRICHMENT_AUDIT.md` definisce le nove dimensioni comuni di enrichment e la semantica unica di `ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente; l'Effective Public Catalog resta una vista derivata.
2. A3 non deve introdurre una seconda lista manuale di indicatori o fonti.
3. L'unità di audit A3 è `indicatore pubblico × dimensione enrichment`.
4. Le dimensioni comuni sono: serie storica, sesso, età, dettaglio territoriale, benchmark Toscana/Italia, assoluto/normalizzato, frequenza infra-annuale, numeratore/denominatore, categorie specifiche.
5. Ogni coppia deve avere esattamente uno stato tra `ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`.
6. `AVAILABLE_MISSING` richiede evidenza verificabile presso la fonte ufficiale; `NOT_APPLICABLE` è una decisione semantica e non una scorciatoia per una mancata acquisizione.
7. A3 misura il potenziale informativo disponibile alla fonte; nuove integrazioni entrano solo in A3.5 dopo backlog e QA.
8. Nessun merge/pubblicazione senza Quick/Full pertinenti e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Implementare `A3.2` come vista derivata dal catalogo pubblico effettivo e dalle policy/source profile già esistenti, senza enumerare manualmente i 225 indicatori.
2. Produrre per ogni coppia indicatore/dimensione: ID indicatore, fonte risolta, stato, evidenza/motivazione e riferimento fonte quando necessario.
3. Rendere la classificazione riproducibile e testabile prima di avviare l'audit fonte-per-fonte di `A3.3`.

## Verifiche

- Main di partenza A3: `e35dd64e56b03da78dc983be32b69ae8488ee529`.
- Release pubblica governata: 225 indicatori.
- A2 chiuso su perimetro operativo 225 indicatori / 122 fonti.
- La tassonomia A3.1 è metodologica: nessuna modifica a UI, dati pubblicati o pipeline di acquisizione.
- Il container della sessione non risolve `github.com`; il preflight locale non è eseguibile e non viene dichiarato come eseguito. I gate GitHub restano obbligatori prima del merge.
