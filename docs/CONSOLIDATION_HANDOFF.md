# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `fe07ff52201e4de31ac4bcdf1bf3ad176417023b`
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Matrice A3.2:** 2.025 coppie; 357 classificate, 1.668 da auditare alla baseline post-`#207`
- **Branch:** `chore/a3-2-evidence-audit-2`
- **PR corrente:** `#208` — Ready

## Completato

- `A0` chiuso con merge autorizzato della PR `#188`.
- `A1 — Data Governance Foundation` chiuso con le PR `#190` e `#193`.
- `A2 — Full Coverage Source Monitor` chiuso con la PR `#194`; gli interventi `#195`–`#203` e il refresh `#202` hanno poi irrobustito acquisizione e gate senza indebolire i contratti.
- `A3.1` chiuso con merge autorizzato della PR `#204`: nove dimensioni comuni e quattro stati finali (`ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`).
- La PR `#206` ha introdotto e pubblicato la matrice derivata A3.2 sull'Effective Public Catalog, con strict mode e regressioni.
- La PR `#207` è stata mergiata dopo Quick/Full verdi e ha portato la baseline A3.2 a `357/2.025` coppie classificate, con `1.668` residue.
- La PR `#208` estende l'audit source-profile usando evidenze ufficiali per Frame SBS Istat, ARS Toscana, MIM, turismo Regione Toscana, indicatori comunali Regione Toscana, Censimento Agricoltura, MEF IRPEF e pendolarismo Istat 2021.

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

1. Leggere dal Full della `#208` il nuovo conteggio classificato/residuo e il ranking aggiornato per dimensione/source profile.
2. Correggere eventuali evidenze troppo ampie se i gate mostrano conflitti o incongruenze; non indebolire la matrice per far passare la CI.
3. Proseguire sui profili residui ad alto impatto e introdurre override metric-specific solo dove la semantica della singola metrica lo richiede.
4. Ripetere fino a `unclassifiedPairCount = 0`; solo allora chiudere `A3.2` e passare ad `A3.3`.

## Verifiche

- Main di partenza della seconda tranche evidenze A3.2: `fe07ff52201e4de31ac4bcdf1bf3ad176417023b`.
- Full della `#207`: `357` coppie classificate, `1.668` residue; Quick e Full verdi.
- Release pubblica governata: 225 indicatori.
- A2 chiuso su perimetro operativo 225 indicatori / 122 fonti.
- Il container della sessione non viene usato per dichiarare preflight GitHub: i gate Actions restano obbligatori prima del merge.
