# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `0d10f8bb827bd56d2b59a22d96cf2411c4ece30a` (post-`#225`)
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Matrice A3.2 baseline #225:** 2.025 coppie; **1.705 classificate, 320 residue**
- **Branch corrente:** `chore/a3-2-closure-a2-structural`
- **PR corrente:** `#226`

## Completato

- `A0` chiuso con `#188`; `A1` con `#190/#193`; `A2` con `#194` e hardening `#195–#203`; `A3.1` con `#204`.
- `#206` ha introdotto la matrice A3.2 derivata dall'Effective Public Catalog.
- Progressione A3.2: `#207–#210` → `804/2.025`; `#211` → `920`; `#212` → `1.101`; `#213` → `1.245`; `#214` → `1.373`; `#215` → `1.464`; `#217` → `1.498`; `#218` → `1.532`; `#220` → `1.556`; `#221` → `1.596`; `#222` → `1.636`; `#223` → `1.674`; `#225` → **1.705**.
- `#224` ha prodotto il primo Residual Closure Audit sulle 351 residue post-#223.
- `#225` ha separato il core della matrice e migliorato i detector strutturali; Full `35259611965` / job `105333898344`: **GREEN**, 1.705 classificate / 320 residue.
- La Residual Closure Audit è stata ricalcolata sulle 320 residue reali post-#225: **A 43 / B 43 / C 34 / D 200**.

## Residual Closure Audit post-#225

- **A — falso residuo strutturale ancora presente:** 43
- **B — cross-source / companion:** 43
- **C — semanticamente `NOT_APPLICABLE`:** 34
- **D — verifica fonte ufficiale necessaria:** 200

A è ancora significativo e precede B. Si divide in:

- 30 coppie **same-payload structural**;
- 12 coppie **special-route** su `voterTurnout` / `economyActivityAtlas`;
- 1 coppia **external climate** su `climatePrecipitationTrend50y / assoluto_normalizzato`.

## Intervento corrente — #226

`#226` chiude esclusivamente le 30 coppie A same-payload con detector generici verificabili:

- unità normalizzate ereditate dal metadata della metrica;
- componenti assolute annidate (`count`, `numerator`, ecc.);
- rapporti annidati validati aritmeticamente su almeno 2 righe e >=90% delle osservazioni utilizzabili;
- denominatori row-level/map-level, sibling accounting, densità e distribuzioni exhaustive count/share.

Nessun ID metrica/source-profile è hard-coded; nessuna inferenza cross-source; catalogo e registry restano invariati.

**Esito atteso e verificato sul preview #225:** +30 `ACQUIRED` strutturali → **1.735 classificate / 290 residue**. Quick/Full GitHub restano autoritativi sull'head finale.

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

1. Portare `#226` a Quick e Full GREEN sull'head finale e verificare il conteggio effettivo.
2. Dopo merge autorizzato di `#226`, chiudere le **13 A residue** con un intervento route-aware separato: 12 special-route + 1 external climate.
3. Ricalcolare nuovamente la closure audit sul residuo effettivo.
4. Passare quindi a **B cross-source / companion**, poi C semantic closure e D source evidence.
5. Ripetere tranche verificabili fino a `unclassifiedPairCount = 0`; solo allora iniziare A3.3.
