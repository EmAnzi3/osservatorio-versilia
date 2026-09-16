# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `9f69f591750db9699c6a73aef2f8c88325f48fe8`
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Matrice A3.2 su main:** 2.025 coppie; 1.245 classificate, 780 da auditare dopo il merge della `#213`
- **Branch corrente:** `chore/a3-2-evidence-audit-8`
- **PR corrente:** da aprire

## Completato

- `A0` chiuso con merge autorizzato della PR `#188`.
- `A1 — Data Governance Foundation` chiuso con le PR `#190` e `#193`.
- `A2 — Full Coverage Source Monitor` chiuso con la PR `#194`; gli interventi `#195`–`#203` e il refresh `#202` hanno poi irrobustito acquisizione e gate senza indebolire i contratti.
- `A3.1` chiuso con merge autorizzato della PR `#204`: nove dimensioni comuni e quattro stati finali (`ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`).
- La PR `#206` ha introdotto e pubblicato la matrice derivata A3.2 sull'Effective Public Catalog, con strict mode e regressioni.
- Le PR `#207`–`#210` hanno portato progressivamente la matrice a `804/2.025` coppie classificate.
- La PR `#211` ha portato la matrice a `920/2.025`.
- La PR `#212` ha portato la matrice a `1.101/2.025`.
- La PR `#213` è stata mergiata dopo Quick/Full verdi; il Full del run `35150096574` ha confermato `1.245/2.025` coppie classificate e `780` residue.

## Residuo A3.2 verificato sulla #213

Per dimensione:

- `serie_storica`: 63
- `sesso`: 86
- `eta`: 113
- `dettaglio_territoriale`: 43
- `benchmark_toscana_italia`: 54
- `assoluto_normalizzato`: 144
- `frequenza_infra_annuale`: 86
- `numeratore_denominatore`: 102
- `categorie_specifiche`: 89

Source profile con più residuo:

- `ars-toscana-mixed`: 74
- `istat-demography-annual`: 44
- `regione-toscana-indicatori-comunali`: 35
- `percorsi-curated`: 30
- `mef-irpef-annual`: 20
- `istat-agriculture-census-2020`: 19
- `istat-fragility-2022`: 18
- `ispra-coast-irregular`: 18
- `istat-social-services-annual`: 18
- `istat-geografie-funzionali-2021`: 18
- `arpat-bathing-annual`: 17
- `regione-toscana-prc-annual`: 17
- `ispra-idrogeo-risk`: 17
- `mim-school-year`: 17
- `siope-monthly`: 16
- `ispra-environment-annual`: 16
- `regione-toscana-biblioteche-annual`: 15

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

1. Continuare A3.2 dalla branch `chore/a3-2-evidence-audit-8`, nata dal `main` post-`#213`.
2. Dare priorità a profili omogenei e ad alto rendimento; `ars-toscana-mixed` resta metric-specific dove le dimensioni non sono uniformi.
3. Aprire la tranche successiva, eseguire Quick/Full e aggiornare questo handoff con il conteggio Full effettivo prima del merge.
4. Ripetere tranche verificabili fino a `unclassifiedPairCount = 0`; solo allora chiudere `A3.2` e passare ad `A3.3`.

## Verifiche

- Main di partenza dell'ottava tranche A3.2: `9f69f591750db9699c6a73aef2f8c88325f48fe8`.
- `#213` mergiata; Full `35150096574`: `1.245` coppie classificate, `780` residue; Quick e Full verdi.
- Release pubblica governata: 225 indicatori.
- A2 chiuso su perimetro operativo 225 indicatori / 122 fonti.
- I gate GitHub Actions restano obbligatori prima del merge.
