# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `11392b87deabf8c28b79c01fa11c4eadb5f3f61e`
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Branch:** `chore/a3-2-enrichment-matrix`
- **PR corrente:** `#206` — Ready

## Completato

- `A0` chiuso con merge autorizzato della PR `#188`.
- `A1 — Data Governance Foundation` chiuso con le PR `#190` e `#193`.
- `A2 — Full Coverage Source Monitor` chiuso con la PR `#194`; gli interventi `#195`–`#203` e il refresh `#202` hanno poi irrobustito acquisizione e gate senza indebolire i contratti.
- `A3.1` chiuso con merge autorizzato della PR `#204`: nove dimensioni comuni e quattro stati finali (`ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`).
- In `A3.2`, `scripts/enrichment_audit_matrix.py` deriva una riga per ogni coppia `indicatore pubblico × dimensione` dall'Effective Public Catalog e dalle source policy esistenti.
- L'evidenza strutturata prevale e può assegnare `ACQUIRED`; disponibilità/indisponibilità e non-applicabilità richiedono annotazioni documentate nel registry esistente.
- La modalità strict rifiuta qualunque coppia non classificata: `state: null` è solo lavoro residuo, non un quinto stato A3.
- Il Full post-build verifica la matrice sul catalogo pubblico realmente materializzato e la copertura `indicatori × 9`.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente; l'Effective Public Catalog resta una vista derivata.
2. A3 non deve introdurre una seconda lista manuale di indicatori o fonti.
3. L'unità di audit A3 è `indicatore pubblico × dimensione enrichment`.
4. Le dimensioni comuni sono: serie storica, sesso, età, dettaglio territoriale, benchmark Toscana/Italia, assoluto/normalizzato, frequenza infra-annuale, numeratore/denominatore, categorie specifiche.
5. Ogni coppia finale deve avere esattamente uno stato tra `ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`.
6. `ACQUIRED` richiede evidenza strutturata; non può essere dichiarato manualmente.
7. `AVAILABLE_MISSING` e `SOURCE_UNAVAILABLE` richiedono evidenza e riferimento verificabile alla fonte; `NOT_APPLICABLE` è ammesso solo a livello di singola metrica.
8. A3.2 non è chiuso finché la matrice strict non raggiunge `unclassifiedPairCount = 0`.
9. Nessun merge/pubblicazione senza Quick/Full pertinenti e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Verificare Quick e Full della PR `#206` e leggere dal Full il conteggio reale di coppie classificate/non classificate sul catalogo pubblico materializzato.
2. Restando dentro `A3.2`, colmare le coppie residue tramite evidenze riusabili a livello di source profile e soli override metric-specific necessari, senza enumerare manualmente i 225 indicatori.
3. Portare la stessa matrice a validazione strict (`unclassifiedPairCount = 0`) prima di segnare `A3.2` come completato e passare ad `A3.3`.

## Verifiche

- Main di partenza A3.2: `11392b87deabf8c28b79c01fa11c4eadb5f3f61e`.
- Release pubblica governata: 225 indicatori.
- A2 chiuso su perimetro operativo 225 indicatori / 122 fonti.
- A3.1 mergiato con PR `#204`.
- Il container della sessione non risolve `github.com`; il preflight locale completo non è eseguibile e non viene dichiarato come eseguito. I gate GitHub restano obbligatori prima del merge.
