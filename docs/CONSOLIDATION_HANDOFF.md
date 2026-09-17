# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `bc17396efae8fc2896a5f011c371bd07ff860104`
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Matrice A3.2 su main:** 2.025 coppie; 1.498 classificate, 527 da auditare dopo il merge della `#217`
- **Branch corrente:** `chore/a3-2-structural-detector-11`
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
- `#215`: `1.464/2.025`.
- La PR `#217` è stata mergiata dopo Quick/Full verdi; il Full del run `35214401001`, job `105181107927`, ha confermato `1.498/2.025` coppie classificate e `527` residue.

## Residuo A3.2 verificato sulla #217

Per dimensione:

- `serie_storica`: 54
- `sesso`: 56
- `eta`: 77
- `dettaglio_territoriale`: 21
- `benchmark_toscana_italia`: 22
- `assoluto_normalizzato`: 108
- `frequenza_infra_annuale`: 61
- `numeratore_denominatore`: 63
- `categorie_specifiche`: 65

Source profile con più residuo:

- `ars-toscana-mixed`: 74
- `istat-demography-annual`: 44
- `regione-toscana-indicatori-comunali`: 35
- `istat-agriculture-census-2020`: 14
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
- `regione-toscana-ucs-2007-2019`: 9
- `regione-toscana-biblioteche-annual`: 9

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

1. Eseguire la tranche strutturale `audit-11` dalla branch `chore/a3-2-structural-detector-11`, nata dal `main` post-`#217`.
2. Estendere esclusivamente il riconoscimento automatico `ACQUIRED` a tre forme già presenti nel catalogo: serie compatte `years + values`, coppie assoluto/normalizzato dichiarate da `meta.normalized`, e categorie selezionabili `selectorLabel + aggregate.parts`.
3. Mantenere guardie negative per evitare falsi positivi; nessuna nuova classificazione manuale in questa tranche.
4. Eseguire Quick/Full e aggiornare questo handoff con il conteggio effettivo prima del merge.
5. Ripetere tranche verificabili fino a `unclassifiedPairCount = 0`; solo allora chiudere `A3.2` e passare ad `A3.3`.

## Verifiche

- Main di partenza della tranche strutturale A3.2: `bc17396efae8fc2896a5f011c371bd07ff860104`.
- `#217` mergiata; Full `35214401001` / job `105181107927`: `1.498` coppie classificate, `527` residue; Quick e Full verdi.
- Release pubblica governata: 225 indicatori.
- A2 chiuso su perimetro operativo 225 indicatori / 122 fonti.
- I gate GitHub Actions restano obbligatori prima del merge.
