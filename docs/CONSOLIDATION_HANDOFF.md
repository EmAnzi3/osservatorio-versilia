# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `e6bab0c01933451ec8fef9d4c27952c0436724a2`
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Matrice A3.2 su main:** 2.025 coppie; 1.101 classificate, 924 da auditare dopo il merge della `#212`
- **Branch corrente:** `chore/a3-2-evidence-audit-7`
- **PR corrente:** da aprire

## Completato

- `A0` chiuso con merge autorizzato della PR `#188`.
- `A1 — Data Governance Foundation` chiuso con le PR `#190` e `#193`.
- `A2 — Full Coverage Source Monitor` chiuso con la PR `#194`; gli interventi `#195`–`#203` e il refresh `#202` hanno poi irrobustito acquisizione e gate senza indebolire i contratti.
- `A3.1` chiuso con merge autorizzato della PR `#204`: nove dimensioni comuni e quattro stati finali (`ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`).
- La PR `#206` ha introdotto e pubblicato la matrice derivata A3.2 sull'Effective Public Catalog, con strict mode e regressioni.
- Le PR `#207`–`#210` hanno portato progressivamente la matrice a `804/2.025` coppie classificate.
- La PR `#211` è stata mergiata dopo Quick/Full verdi; il Full ha confermato `920/2.025` coppie classificate e `1.105` residue.
- La PR `#212` è stata mergiata dopo Quick/Full verdi; il Full del run `35145431823` ha confermato `1.101/2.025` coppie classificate e `924` residue.

## Residuo A3.2 verificato sulla #212

Per dimensione:

- `serie_storica`: 70
- `sesso`: 105
- `eta`: 132
- `dettaglio_territoriale`: 55
- `benchmark_toscana_italia`: 69
- `assoluto_normalizzato`: 169
- `frequenza_infra_annuale`: 98
- `numeratore_denominatore`: 126
- `categorie_specifiche`: 100

Source profile con più residuo:

- `ars-toscana-mixed`: 74
- `istat-demography-annual`: 44
- `regione-toscana-indicatori-comunali`: 35
- `percorsi-curated`: 30
- `istat-census-annual`: 25
- `agcom-quarterly`: 20
- `mef-irpef-annual`: 20
- `istat-agriculture-census-2020`: 19
- `regione-toscana-gtfs-scheduled`: 18
- `istat-fragility-2022`: 18
- `health-ministry-annual`: 18
- `ispra-consumo-suolo-2024`: 18
- `aci-istat-annual`: 18
- `mef-municipal-tax-annual`: 18
- `regione-toscana-pab-annual`: 18
- `regione-toscana-pnrr-monthly`: 18

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

1. Continuare A3.2 dalla branch `chore/a3-2-evidence-audit-7`, nata dal `main` post-`#212`.
2. Dare priorità a profili omogenei e ad alto rendimento; `ars-toscana-mixed` resta metric-specific dove le dimensioni non sono uniformi.
3. Aprire la tranche successiva, eseguire Quick/Full e aggiornare questo handoff con il conteggio Full effettivo prima del merge.
4. Ripetere tranche verificabili fino a `unclassifiedPairCount = 0`; solo allora chiudere `A3.2` e passare ad `A3.3`.

## Verifiche

- Main di partenza della settima tranche A3.2: `e6bab0c01933451ec8fef9d4c27952c0436724a2`.
- `#212` mergiata; Full `35145431823`: `1.101` coppie classificate, `924` residue; Quick e Full verdi.
- Release pubblica governata: 225 indicatori.
- A2 chiuso su perimetro operativo 225 indicatori / 122 fonti.
- I gate GitHub Actions restano obbligatori prima del merge.
