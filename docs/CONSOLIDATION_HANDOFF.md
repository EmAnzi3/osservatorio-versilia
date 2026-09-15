# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A1 — Data Governance Foundation`
- **Step attivo:** seconda tranche `A1.4`–`A1.8` in PR draft
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `4b66e1a72790d0d0d74954da20e59da19ccfa1da`
- **Catalogo sorgente / pubblico auditato:** 181 / 225 indicatori
- **Branch:** `chore/a1-data-governance-completion`
- **PR corrente:** `#193` — draft

## Completato

- `A0` chiuso con merge autorizzato della PR `#188`.
- `A1.1`–`A1.3` chiusi con merge autorizzato della PR `#190`.
- Effective Public Catalog formalizzato come vista derivata `dist/data/site-data.json`, senza secondo catalogo canonico.
- Gate ID verificato: `225 ID pubblicati = 225 ID Stato dati = 225 policy fonte`.
- `A1.4`: introdotto blocco README derivato e verificabile dalla release materializzata.
- `A1.5`: Stato dati resta sulla stessa pipeline build-aware ed entra nel gate unificato.
- `A1.6`: versione, data e conteggi vengono riconciliati tra README, homepage, Stato dati e catalogo pubblico.
- `A1.7`: gate generale `PUBLIC DATA GOVERNANCE` inserito nel percorso del preflight esistente.
- `A1.8`: lineage minima derivata per tutti i 225 indicatori; contratto build schema 2 con 29 passaggi dichiarati.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Il catalogo effettivamente pubblicato è una vista derivata della build, non un manifest da mantenere a mano.
3. README, Stato dati e lineage sono superfici derivate/verificate, non nuove fonti canoniche.
4. A1 controlla la copertura strutturale delle policy; A2 controllerà esecuzione, freschezza e ultimo check delle fonti.
5. La PR `#193` usa una deroga circoscritta autorizzata dal proprietario il 2026-09-15: i gate A1 e la build 225 sono verdi localmente, mentre il Quick locale si ferma esclusivamente sul noto test browser Percorsi nell'ambiente locale. GitHub Actions è la verifica ufficiale della PR.
6. Nessun merge/pubblicazione senza Full verde e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Verificare il Quick GitHub della PR `#193` mantenendola draft.
2. Se Quick è verde, portare `#193` a Ready for review per eseguire il Full.
3. Se Full è verde, attendere approvazione esplicita del proprietario prima del merge.
4. Dopo il merge e il deploy post-merge, portare `A1` a `DONE` e avviare `A2 — Full Coverage Source Monitor`.

## Verifiche

- Build completa locale: RC 0, release `v1.40.0`, 225 indicatori.
- Gate locale: `PUBLIC DATA GOVERNANCE: GREEN`.
- Lineage derivata: 225 indicatori / 29 passaggi dichiarati.
- README derivato: `v1.40.0` / 225 indicatori / 14 settembre 2026.
- Il Quick locale ha superato i gate A1 e si è fermato solo sul test Percorsi `Filtro tipologia non applicato dalla URL: all`, già risultato verde nell'ambiente GitHub sulla PR `#190`.
- Il merge Radar `#192` è incluso nella baseline e non modifica catalogo dati, registry o file A1 di questa tranche.
