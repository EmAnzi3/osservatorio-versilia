# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `a17996d4c134ba80e17e1acc1315d4f72acf8607` (post-`#224`)
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Matrice A3.2 su main:** 2.025 coppie; **1.674 classificate, 351 residue**
- **Branch corrente:** `chore/a3-2-closure-a1-structural`
- **PR corrente:** da aprire

## Completato

- `A0` chiuso con `#188`; `A1` con `#190/#193`; `A2` con `#194` e hardening `#195–#203`; `A3.1` con `#204`.
- `#206` ha introdotto la matrice A3.2 derivata dall'Effective Public Catalog.
- Progressione A3.2: `#207–#210` → `804/2.025`; `#211` → `920`; `#212` → `1.101`; `#213` → `1.245`; `#214` → `1.373`; `#215` → `1.464`; `#217` → `1.498`; `#218` → `1.532`; `#220` → `1.556`; `#221` → `1.596`; `#222` → `1.636`; `#223` → **1.674**.
- Full `#223`: run `35241061878`, job `105271718007`, **GREEN**, 1.674 classificate / 351 residue.
- `#224` ha materializzato la **Residual Closure Audit** diagnostica delle 351 residue senza modificare stati A3.2.

## Residual Closure Audit post-#223

- **A — falso residuo strutturale:** 22
- **B — cross-source / companion:** 20
- **C — semanticamente N/A:** 37
- **D — verifica fonte ufficiale:** 272

Il bucket A contiene anche 8 coppie su route speciali (`voterTurnout`, `economyActivityAtlas`), da trattare separatamente dal detector del catalogo standard.

## Residuo A3.2 verificato sulla #223

Per dimensione:

- `serie_storica`: 27
- `sesso`: 35
- `eta`: 56
- `dettaglio_territoriale`: 6
- `benchmark_toscana_italia`: 7
- `assoluto_normalizzato`: 83
- `frequenza_infra_annuale`: 45
- `numeratore_denominatore`: 52
- `categorie_specifiche`: 40

Profili principali:

- `ars-toscana-mixed`: 64
- `istat-demography-annual`: 41
- `regione-toscana-indicatori-comunali`: 35
- `istat-agriculture-census-2020`: 12
- `cb1-pmo-status-2026`: 12
- `istat-commuting-irregular`: 11
- `regione-toscana-tourism-annual`: 11
- `istat-road-annual`: 11
- `istat-business-annual`: 10

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente; l'Effective Public Catalog resta una vista derivata.
2. A3 non deve introdurre una seconda lista manuale di indicatori o fonti.
3. L'unità di audit è `indicatore pubblico × dimensione enrichment`.
4. Ogni coppia finale deve avere uno stato tra `ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`.
5. `ACQUIRED` richiede evidenza strutturata e non può essere dichiarato manualmente.
6. `AVAILABLE_MISSING` e `SOURCE_UNAVAILABLE` richiedono evidenza ufficiale verificabile; `NOT_APPLICABLE` solo metric-specific.
7. A3.2 non è chiuso finché `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
8. Le classificazioni source-profile sono ammesse solo quando valide per l'intero profilo; altrimenti override metric-specific.
9. Coppie già materializzate ma non riconosciute dal detector richiedono correzione strutturale, non annotazioni artificiali.
10. I rapporti con componenti provenienti da fonti/metriche companion richiedono un contratto cross-source esplicito.
11. Nessun merge/pubblicazione senza Quick/Full pertinenti e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Chiudere **A1 — structural local** sulla branch `chore/a3-2-closure-a1-structural`.
2. Migliorare il detector solo con pattern generici verificabili: serie annidate `years + vettore numerico`, rapporti aritmeticamente ricostruibili, assoluto+normalizzato espliciti, categorie strutturate.
3. Mantenere fuori da A1 le 8 coppie delle route speciali e `municipalStaffTurnover/numeratore_denominatore`, il cui denominatore vive in una metrica companion.
4. Regressioni positive e negative obbligatorie; nessun ID metrica/source-profile hard-coded nel detector.
5. Il prototipo sul preview #223 indica **24 coppie strutturali** potenzialmente chiudibili; Quick/Full sono l'unica misura autorevole dell'effetto reale.
6. Dopo A1, procedere con **B cross-source**, poi **C semantic closure**, quindi **D source evidence**.

## Verifiche

- Main di partenza A1: `a17996d4c134ba80e17e1acc1315d4f72acf8607`.
- `#223`: Full `35241061878` / job `105271718007`, 1.674 classificate / 351 residue, GREEN.
- `#224`: Residual Closure Audit mergiata, solo documentazione, conteggi A3.2 invariati.
- Release pubblica governata: 225 indicatori; A2 chiuso su 225 indicatori / 122 fonti.
