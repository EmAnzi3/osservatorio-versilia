# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `72900d43392a9f988dfd25b108ad2baadb04af20` (post-`#228`)
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Matrice A3.2 post-#228:** 2.025 coppie; **1.743 classificate, 282 residue**
- **Branch corrente:** `chore/a3-2-route-storage-contracts`
- **PR corrente:** `#230`

## Completato

- `A0` chiuso con `#188`; `A1` con `#190/#193`; `A2` con `#194` e hardening `#195–#203`; `A3.1` con `#204`.
- `#206` ha introdotto la matrice A3.2 derivata dall'Effective Public Catalog.
- Progressione A3.2: `#207–#210` → `804/2.025`; `#211` → `920`; `#212` → `1.101`; `#213` → `1.245`; `#214` → `1.373`; `#215` → `1.464`; `#217` → `1.498`; `#218` → `1.532`; `#220` → `1.556`; `#221` → `1.596`; `#222` → `1.636`; `#223` → `1.674`; `#225` → **1.705**.
- `#224` ha prodotto il primo Residual Closure Audit sulle 351 residue post-#223.
- `#225` ha separato il core della matrice e migliorato i detector strutturali; Full `35259611965` / job `105333898344`: **GREEN**, 1.705 classificate / 320 residue.
- `#226` ha chiuso 30 falsi residui same-payload → **1.735 / 290**.
- `#227` ha introdotto il resolver route-aware ma senza chiudere le 12 coppie special-route; ha invece reso riconoscibile il contratto climate normalizzato poi verificato nella matrice effettiva.
- `#228` ha chiuso 7 coppie demografiche `eta` tramite companion verificato; A3 gate, Quick e Full verdi. Matrice effettiva post-merge: **1.743 classificate / 282 residue**.
- La Residual Closure Audit è stata ricalcolata sulle 320 residue reali post-#225: **A 43 / B 43 / C 34 / D 200**.

## Residual Closure Audit post-#228

Le 282 residue reali si ricompongono così:

- **A — special-route strutturale:** 12
- **B — cross-source / companion:** 36
- **C — semanticamente `NOT_APPLICABLE`:** 34
- **D — verifica fonte ufficiale necessaria:** 200

Le 12 A residue sono:
- `voterTurnout`: serie storica, sesso, dettaglio territoriale, assoluto/normalizzato, numeratore/denominatore, categorie specifiche;
- `economyActivityAtlas`: serie storica, dettaglio territoriale, benchmark Toscana/Italia, assoluto/normalizzato, numeratore/denominatore, categorie specifiche.

## Intervento corrente — #230

`#230` dichiara nei due indicatori il payload reale delle route speciali e rende verificabile il formato compatto dell'Atlante senza hard-code degli ID nel detector.

Il gate A3 richiede:
- tutte le 12 coppie special-route in `ACQUIRED` con evidenza `structured:storage:`;
- conservazione delle 7 coppie companion chiuse da `#228`;
- conteggio esatto **1.755 classificate / 270 residue**.

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

1. Portare `#230` a A3 gate, Quick e Full GREEN sullo stesso head e verificare **1.755 / 270**.
2. Dopo merge autorizzato di `#230`, ricalcolare le 270 residue.
3. Proseguire con **B cross-source / companion** (baseline attesa: 36), poi C semantic closure e D source evidence.
4. Ripetere tranche verificabili fino a `unclassifiedPairCount = 0`; solo allora iniziare A3.3.
