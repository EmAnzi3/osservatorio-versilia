# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `da27fb3608acc28a8073d7f721dbf8685be60ef1`
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Matrice A3.2 su main:** 2.025 coppie; 1.556 classificate, 469 da auditare dopo il merge della `#220`
- **Branch corrente:** `chore/a3-2-evidence-audit-13`
- **PR corrente:** da aprire

## Completato

- `A0` chiuso con `#188`.
- `A1` chiuso con `#190` e `#193`.
- `A2` chiuso con `#194`; `#195`–`#203` hanno irrobustito acquisizione e gate.
- `A3.1` chiuso con `#204`.
- `#206` ha introdotto la matrice A3.2 derivata sull'Effective Public Catalog.
- Progressione A3.2: `#207`–`#210` → `804/2.025`; `#211` → `920`; `#212` → `1.101`; `#213` → `1.245`; `#214` → `1.373`; `#215` → `1.464`; `#217` → `1.498`; `#218` → `1.532`.
- `#220` ha aggiunto evidenza ufficiale mirata MIT/SID, MEF IRPEF e Agricoltura; il Full `35225796180`, job `105219100711`, ha confermato `1.556/2.025` coppie classificate e `469` residue.

## Residuo A3.2 verificato sulla #220

Per dimensione:

- `serie_storica`: 42
- `sesso`: 49
- `eta`: 70
- `dettaglio_territoriale`: 21
- `benchmark_toscana_italia`: 20
- `assoluto_normalizzato`: 99
- `frequenza_infra_annuale`: 59
- `numeratore_denominatore`: 61
- `categorie_specifiche`: 48

Source profile con più residuo:

- `ars-toscana-mixed`: 64
- `istat-demography-annual`: 41
- `regione-toscana-indicatori-comunali`: 35
- `istat-agriculture-census-2020`: 12
- `cb1-pmo-status-2026`: 12
- `istat-commuting-irregular`: 11
- `regione-toscana-tourism-annual`: 11
- `istat-road-annual`: 11
- `istat-business-annual`: 10
- `regione-toscana-rsa`: 9
- `gaia-quality-semiannual`: 9
- `regione-toscana-early-childhood`: 9
- `regione-toscana-infocamere-annual`: 9
- `pun-continuous`: 9
- `regione-toscana-opere-idrauliche-2021`: 9
- `regione-toscana-ucs-2007-2019`: 9
- `regione-toscana-biblioteche-annual`: 9
- `regione-toscana-reticolo-v137`: 9
- `cb1-pmo-2026`: 9
- `openbdap-continuous`: 9
- `sisbon-weekly`: 9
- `dait-eligendo-irregular`: 9

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente; l'Effective Public Catalog resta una vista derivata.
2. A3 non deve introdurre una seconda lista manuale di indicatori o fonti.
3. L'unità di audit A3 è `indicatore pubblico × dimensione enrichment`.
4. Ogni coppia finale deve avere esattamente uno stato tra `ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`.
5. `ACQUIRED` richiede evidenza strutturata e non può essere dichiarato manualmente.
6. `AVAILABLE_MISSING` e `SOURCE_UNAVAILABLE` richiedono evidenza e riferimento verificabile alla fonte; `NOT_APPLICABLE` è ammesso solo a livello di singola metrica.
7. A3.2 non è chiuso finché `unclassifiedPairCount = 0`.
8. Le classificazioni vanno riusate a livello source profile solo quando metodologicamente valide; override metric-specific per eccezioni reali.
9. Coppie già materializzate ma non riconosciute dal detector non vanno etichettate artificialmente `AVAILABLE_MISSING`: richiedono correzione strutturale dedicata.
10. Nessun merge/pubblicazione senza Quick/Full pertinenti e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Eseguire `audit-13` dalla branch `chore/a3-2-evidence-audit-13`, nata dal `main` post-`#220`.
2. Classificare con fonti ufficiali sei profili territoriali/servizio: opere idrauliche, reticolo, aree protette, Iter.Net, SISBON e prima infanzia.
3. La tranche comprende 40 coppie ad alta confidenza; non introduce `ACQUIRED` manuali e lascia aperte le coppie già presenti nel payload ma non ancora riconosciute strutturalmente.
4. Non introdurre classificazioni broad su `ars-toscana-mixed`, `istat-demography-annual` o `regione-toscana-indicatori-comunali`.
5. Eseguire Quick/Full e aggiornare questo handoff con il conteggio effettivo prima del merge.
6. Ripetere tranche verificabili fino a `unclassifiedPairCount = 0`; solo allora passare ad `A3.3`.

## Verifiche

- Main di partenza audit-13: `da27fb3608acc28a8073d7f721dbf8685be60ef1`.
- `#220` mergiata; Full `35225796180` / job `105219100711`: `1.556` classificate, `469` residue; Quick e Full verdi.
- Release pubblica governata: 225 indicatori.
- A2 chiuso su 225 indicatori / 122 fonti.
