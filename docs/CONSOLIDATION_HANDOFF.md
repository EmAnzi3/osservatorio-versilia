# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `d20e3bb9f53b4ef438095427cb9239cc71f78ba7`
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Matrice A3.2 su main:** 2.025 coppie; 804 classificate, 1.221 da auditare dopo il merge della `#210`
- **Branch corrente:** `chore/a3-2-evidence-audit-5`
- **PR corrente:** `#211` — Ready, non mergiata
- **Full verificato della #211:** 920/2.025 coppie classificate; 1.105 residue

## Completato

- `A0` chiuso con merge autorizzato della PR `#188`.
- `A1 — Data Governance Foundation` chiuso con le PR `#190` e `#193`.
- `A2 — Full Coverage Source Monitor` chiuso con la PR `#194`; gli interventi `#195`–`#203` e il refresh `#202` hanno poi irrobustito acquisizione e gate senza indebolire i contratti.
- `A3.1` chiuso con merge autorizzato della PR `#204`: nove dimensioni comuni e quattro stati finali (`ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`).
- La PR `#206` ha introdotto e pubblicato la matrice derivata A3.2 sull'Effective Public Catalog, con strict mode e regressioni.
- La PR `#207` ha portato la baseline A3.2 a `357/2.025` coppie classificate.
- La PR `#208` ha portato la baseline a `539/2.025`.
- La PR `#209` è stata mergiata dopo Quick/Full verdi; il Full ha confermato `694/2.025` coppie classificate e `1.331` residue.
- La PR `#210` è stata mergiata dopo Quick/Full verdi; il Full ha confermato `804/2.025` coppie classificate e `1.221` residue.
- La PR `#211` estende le evidenze ad alto impatto con classificazioni source-level solo dove omogenee e override metric-specific per vere eccezioni semantiche. Il Full sull'head `19082aa4cfa361093a6c6ab08914b5581c16d32b` ha confermato `920/2.025` coppie classificate e `1.105` residue.

## Residuo A3.2 verificato sulla #211

Per dimensione:

- `serie_storica`: 74
- `sesso`: 131
- `eta`: 154
- `dettaglio_territoriale`: 58
- `benchmark_toscana_italia`: 108
- `assoluto_normalizzato`: 186
- `frequenza_infra_annuale`: 105
- `numeratore_denominatore`: 186
- `categorie_specifiche`: 103

Source profile con più residuo:

- `ars-toscana-mixed`: 74
- `istat-business-annual`: 64
- `openbdap-annual`: 48
- `istat-demography-annual`: 44
- `regione-toscana-indicatori-comunali`: 35
- `percorsi-curated`: 30
- `lamma-copernicus-climate`: 28
- `cb1-pmo-status-2026`: 28
- `istat-geografia-comunale-2021`: 27
- `mim-school-year`: 26
- `istat-census-annual`: 25
- `rgs-conto-annuale-annual`: 23

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

1. Mantenere la `#211` ferma prima del merge finché non arriva approvazione esplicita del proprietario.
2. Dopo l'eventuale merge autorizzato, aprire la tranche A3.2 successiva dal nuovo `main`, ricostruendo il residuo dal Full effettivo.
3. Dare priorità ai profili ad alto residuo, trattando `ars-toscana-mixed` in modo metric-specific quando la dimensione non è omogenea sull'intero profilo.
4. Ripetere tranche verificabili fino a `unclassifiedPairCount = 0`; solo allora chiudere `A3.2` e passare ad `A3.3`.

## Verifiche

- Main di partenza della quinta tranche A3.2: `d20e3bb9f53b4ef438095427cb9239cc71f78ba7`.
- `#210` mergiata; baseline main: `804` coppie classificate, `1.221` residue.
- Full della `#211` sull'head `19082aa4cfa361093a6c6ab08914b5581c16d32b`: `920` coppie classificate, `1.105` residue; Quick e Full verdi.
- Release pubblica governata: 225 indicatori.
- A2 chiuso su perimetro operativo 225 indicatori / 122 fonti.
- I gate GitHub Actions restano obbligatori prima del merge.
