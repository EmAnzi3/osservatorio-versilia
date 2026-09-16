# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `3768ca5ae0d53db37c2c7ac526c93e9b125ac6ef`
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Matrice A3.2:** 2.025 coppie; 139 classificate, 1.886 da auditare alla baseline post-`#206`
- **Branch:** `chore/a3-2-evidence-audit`
- **PR corrente:** `#207` — Ready

## Completato

- `A0` chiuso con merge autorizzato della PR `#188`.
- `A1 — Data Governance Foundation` chiuso con le PR `#190` e `#193`.
- `A2 — Full Coverage Source Monitor` chiuso con la PR `#194`; gli interventi `#195`–`#203` e il refresh `#202` hanno poi irrobustito acquisizione e gate senza indebolire i contratti.
- `A3.1` chiuso con merge autorizzato della PR `#204`: nove dimensioni comuni e quattro stati finali (`ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`).
- La PR `#206` ha introdotto e pubblicato la matrice derivata A3.2 sull'Effective Public Catalog, con strict mode e regressioni; Quick e Full sono verdi.
- Il Full della `#206` ha misurato la baseline reale: `225 × 9 = 2.025` coppie, `139` già classificate e `1.886` residue.
- La PR `#207` aggiunge il report derivato del residuo per dimensione e source profile per guidare l'audit per fonte, senza inventari paralleli.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente; l'Effective Public Catalog resta una vista derivata.
2. A3 non deve introdurre una seconda lista manuale di indicatori o fonti.
3. L'unità di audit A3 è `indicatore pubblico × dimensione enrichment`.
4. Le dimensioni comuni sono: serie storica, sesso, età, dettaglio territoriale, benchmark Toscana/Italia, assoluto/normalizzato, frequenza infra-annuale, numeratore/denominatore, categorie specifiche.
5. Ogni coppia finale deve avere esattamente uno stato tra `ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`.
6. `ACQUIRED` richiede evidenza strutturata; non può essere dichiarato manualmente.
7. `AVAILABLE_MISSING` e `SOURCE_UNAVAILABLE` richiedono evidenza e riferimento verificabile alla fonte; `NOT_APPLICABLE` è ammesso solo a livello di singola metrica.
8. A3.2 non è chiuso finché la matrice strict non raggiunge `unclassifiedPairCount = 0`.
9. Le classificazioni vanno riusate a livello di source profile quando metodologicamente valide; override metric-specific solo per eccezioni reali.
10. Nessun merge/pubblicazione senza Quick/Full pertinenti e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Leggere dal Full della `#207` il residuo per dimensione e i source profile con più coppie non classificate.
2. Auditare prima i profili ad alto impatto usando riferimenti ufficiali verificabili e aggiungere `enrichmentDimensions` riusabili nel registry esistente.
3. Usare override metric-specific solo dove `NOT_APPLICABLE` o la disponibilità della dimensione dipendono davvero dalla singola metrica.
4. Ripetere il ciclo finché la validazione strict raggiunge `unclassifiedPairCount = 0`, quindi chiudere `A3.2` e passare ad `A3.3`.

## Verifiche

- Main di partenza della tranche evidenze A3.2: `3768ca5ae0d53db37c2c7ac526c93e9b125ac6ef`.
- Release pubblica governata: 225 indicatori.
- A2 chiuso su perimetro operativo 225 indicatori / 122 fonti.
- A3.1 mergiato con PR `#204`; fondazione matrice A3.2 mergiata e pubblicata con PR `#206`.
- Pages post-merge `#206` e live-status sono verdi.
- Il container della sessione non risolve `github.com`; il preflight locale completo non è eseguibile e non viene dichiarato come eseguito. I gate GitHub restano obbligatori prima del merge.
