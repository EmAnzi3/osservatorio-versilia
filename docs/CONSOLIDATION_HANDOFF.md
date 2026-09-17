# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `92b32cf80839774aeb1f153a16a66c359e4e38c5`
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Matrice A3.2 su main:** 2.025 coppie; 1.464 classificate, 561 da auditare dopo il merge della `#215`
- **Branch corrente:** `chore/a3-2-evidence-audit-10`
- **PR corrente:** da aprire

## Completato

- `A0` chiuso con la PR `#188`.
- `A1 — Data Governance Foundation` chiuso con le PR `#190` e `#193`.
- `A2 — Full Coverage Source Monitor` chiuso con la PR `#194`; gli interventi `#195`–`#203` hanno poi irrobustito acquisizione e gate.
- `A3.1` chiuso con la PR `#204`: nove dimensioni comuni e quattro stati finali (`ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`).
- La PR `#206` ha introdotto la matrice derivata A3.2 sull'Effective Public Catalog, con strict mode e regressioni.
- Le PR `#207`–`#210` hanno portato progressivamente la matrice a `804/2.025` coppie classificate.
- `#211`: `920/2.025`.
- `#212`: `1.101/2.025`.
- `#213`: `1.245/2.025`.
- `#214`: `1.373/2.025`.
- La PR `#215` è stata mergiata e pubblicata dopo tutti i gate verdi; il Full del run `35199903735`, job `105134200426`, ha confermato `1.464/2.025` coppie classificate e `561` residue.

## Residuo A3.2 verificato sulla #215

Per dimensione:

- `serie_storica`: 54
- `sesso`: 60
- `eta`: 87
- `dettaglio_territoriale`: 24
- `benchmark_toscana_italia`: 25
- `assoluto_normalizzato`: 114
- `frequenza_infra_annuale`: 61
- `numeratore_denominatore`: 71
- `categorie_specifiche`: 65

Source profile con più residuo:

- `ars-toscana-mixed`: 74
- `istat-demography-annual`: 44
- `regione-toscana-indicatori-comunali`: 35
- `istat-agriculture-census-2020`: 19
- `istat-fragility-2022`: 18
- `mim-school-year`: 17
- `mit-sid-demanio-irregular`: 14
- `istat-road-annual`: 14
- `regione-toscana-tourism-annual`: 12
- `mef-irpef-annual`: 12
- `cb1-pmo-status-2026`: 12
- `istat-business-annual`: 11
- `istat-commuting-irregular`: 11
- `regione-toscana-rsa`: 9
- `gaia-quality-semiannual`: 9
- `regione-toscana-early-childhood`: 9
- `regione-toscana-infocamere-annual`: 9
- `erp-lucca-annual-balance-sheet`: 9
- `pun-continuous`: 9
- `regione-toscana-opere-idrauliche-2021`: 9

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

1. Eseguire la tranche `audit-10` dalla branch `chore/a3-2-evidence-audit-10`, nata dal `main` post-`#215`.
2. La tranche interviene in modo conservativo su `istat-fragility-2022`, su coppie MIM selezionate e su numeratore/denominatore di metriche Agricoltura; non usa classificazioni broad su `ars-toscana-mixed`.
3. Le coppie che risultano già presenti strutturalmente ma non rilevate dal detector restano fuori dalle annotazioni manuali e saranno gestite con correzione strutturale dedicata.
4. Eseguire Quick/Full, registrare il conteggio effettivo e aggiornare questo handoff prima del merge.
5. Ripetere tranche verificabili fino a `unclassifiedPairCount = 0`; solo allora chiudere `A3.2` e passare ad `A3.3`.

## Verifiche

- Main di partenza della decima tranche A3.2: `92b32cf80839774aeb1f153a16a66c359e4e38c5`.
- `#215` mergiata e pubblicata; Full `35199903735` / job `105134200426`: `1.464` coppie classificate, `561` residue; Quick e Full verdi.
- Release pubblica governata: 225 indicatori.
- A2 chiuso su perimetro operativo 225 indicatori / 122 fonti.
- I gate GitHub Actions restano obbligatori prima del merge.
