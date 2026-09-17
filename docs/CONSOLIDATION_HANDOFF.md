# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `28dbdd6cb90a856ec17854d52dffd55281fe52be`
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Matrice A3.2 su main:** 2.025 coppie; 1.532 classificate, 493 da auditare dopo il merge della `#218`
- **Branch corrente:** `chore/a3-2-evidence-audit-12`
- **PR corrente:** da aprire

## Completato

- `A0` chiuso con `#188`.
- `A1` chiuso con `#190` e `#193`.
- `A2` chiuso con `#194`; `#195`–`#203` hanno irrobustito acquisizione e gate.
- `A3.1` chiuso con `#204`.
- `#206` ha introdotto la matrice A3.2 derivata sull'Effective Public Catalog.
- Progressione A3.2: `#207`–`#210` → `804/2.025`; `#211` → `920`; `#212` → `1.101`; `#213` → `1.245`; `#214` → `1.373`; `#215` → `1.464`; `#217` → `1.498`.
- `#218` ha esteso esclusivamente il detector strutturale `ACQUIRED`; il Full `35218906000`, job `105195844064`, ha confermato `1.532/2.025` coppie classificate e `493` residue.

## Residuo A3.2 verificato sulla #218

Per dimensione:

- `serie_storica`: 44
- `sesso`: 56
- `eta`: 77
- `dettaglio_territoriale`: 21
- `benchmark_toscana_italia`: 22
- `assoluto_normalizzato`: 101
- `frequenza_infra_annuale`: 61
- `numeratore_denominatore`: 63
- `categorie_specifiche`: 48

Source profile con più residuo:

- `ars-toscana-mixed`: 64
- `istat-demography-annual`: 41
- `regione-toscana-indicatori-comunali`: 35
- `istat-agriculture-census-2020`: 14
- `mit-sid-demanio-irregular`: 14
- `mef-irpef-annual`: 12
- `cb1-pmo-status-2026`: 12
- `istat-commuting-irregular`: 11
- `regione-toscana-tourism-annual`: 11
- `istat-road-annual`: 11
- `istat-business-annual`: 10

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente; l'Effective Public Catalog resta una vista derivata.
2. A3 non deve introdurre una seconda lista manuale di indicatori o fonti.
3. L'unità di audit A3 è `indicatore pubblico × dimensione enrichment`.
4. Ogni coppia finale deve avere esattamente uno stato tra `ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`.
5. `ACQUIRED` richiede evidenza strutturata e non può essere dichiarato manualmente.
6. `AVAILABLE_MISSING` e `SOURCE_UNAVAILABLE` richiedono evidenza e riferimento verificabile alla fonte; `NOT_APPLICABLE` è ammesso solo a livello di singola metrica.
7. A3.2 non è chiuso finché `unclassifiedPairCount = 0`.
8. Le classificazioni vanno riusate a livello source profile solo quando metodologicamente valide; override metric-specific per eccezioni reali.
9. Nessun merge/pubblicazione senza Quick/Full pertinenti e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Eseguire `audit-12` dalla branch `chore/a3-2-evidence-audit-12` nata dal `main` post-`#218`.
2. Classificare con fonti ufficiali il blocco MIT/SID demanio, sesso/età delle metriche reddituali MEF e sesso/età della sola metrica Istat di ricambio/leadership agricola.
3. Non introdurre classificazioni broad su `ars-toscana-mixed`, `istat-demography-annual` o `regione-toscana-indicatori-comunali`.
4. Eseguire Quick/Full e registrare il conteggio effettivo prima del merge.
5. Ripetere tranche verificabili fino a `unclassifiedPairCount = 0`; solo allora passare ad `A3.3`.

## Verifiche

- Main di partenza audit-12: `28dbdd6cb90a856ec17854d52dffd55281fe52be`.
- `#218` mergiata; Full `35218906000` / job `105195844064`: `1.532` classificate, `493` residue; Quick e Full verdi.
- Release pubblica governata: 225 indicatori.
- A2 chiuso su 225 indicatori / 122 fonti.
