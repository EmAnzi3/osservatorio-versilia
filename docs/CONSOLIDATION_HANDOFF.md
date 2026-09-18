# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `a0b0a8086fee747fc762d767d98092b924d76ac5` (post-`#230`)
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Matrice A3.2 post-#230:** 2.025 coppie; **1.755 classificate, 270 residue**
- **Branch corrente:** `chore/a3-2-cross-source-ratios`
- **PR corrente:** `#233`

## Completato

- `A0` chiuso con `#188`; `A1` con `#190/#193`; `A2` con `#194` e hardening `#195–#203`; `A3.1` con `#204`.
- `#206` ha introdotto la matrice A3.2 derivata dall'Effective Public Catalog.
- Progressione A3.2: `#207–#210` → `804/2.025`; `#211` → `920`; `#212` → `1.101`; `#213` → `1.245`; `#214` → `1.373`; `#215` → `1.464`; `#217` → `1.498`; `#218` → `1.532`; `#220` → `1.556`; `#221` → `1.596`; `#222` → `1.636`; `#223` → `1.674`; `#225` → **1.705**.
- `#224` ha prodotto il primo Residual Closure Audit sulle 351 residue post-#223.
- `#225` ha separato il core della matrice e migliorato i detector strutturali; Full `35259611965` / job `105333898344`: **GREEN**, 1.705 classificate / 320 residue.
- `#226` ha chiuso 30 falsi residui same-payload → **1.735 / 290**.
- `#227` ha introdotto il resolver route-aware ma senza chiudere le 12 coppie special-route; ha invece reso riconoscibile il contratto climate normalizzato poi verificato nella matrice effettiva.
- `#228` ha chiuso 7 coppie demografiche `eta` tramite companion verificato; A3 gate, Quick e Full verdi. Matrice effettiva post-merge: **1.743 classificate / 282 residue**.
- `#229` ha chiuso le 6 coppie `voterTurnout` tramite il payload `archive-v2-*`; `#230` ha chiuso le 6 coppie `economyActivityAtlas` con schema compatto verificato. Baseline post-merge: **1.755 / 270**.
- La Residual Closure Audit è stata ricalcolata sulle 320 residue reali post-#225: **A 43 / B 43 / C 34 / D 200**.

## Residual Closure Audit post-#230

Le **270 residue** reali si ricompongono così:

- **B — cross-source / companion:** 36
- **C — semanticamente `NOT_APPLICABLE`:** 34
- **D — verifica fonte ufficiale necessaria:** 200

Il bucket A strutturale è chiuso. La prima tranche B usa soltanto rapporti ricalcolabili da metriche pubbliche companion già governate.

## Intervento corrente — #233

`#233` estende il contratto companion con un resolver generico `ratio_formula` che:

- allinea le righe per identità territoriale;
- seleziona il valore del denominatore nell'anno della metrica target;
- ricalcola il rapporto con la scala derivata dall'unità;
- produce `ACQUIRED` soltanto se tutte le righe pubbliche coincidono numericamente.

Prima tranche: `tourismIntensity` e `commuterBalanceRate`, per entrambe le dimensioni `assoluto_normalizzato` e `numeratore_denominatore`. `outboundCommutersRate` e `inboundCommutersRate` restano residui per disallineamento temporale del denominatore; `tourismBedsPer1000` resta residuo perché il catalogo effettivo materializza un numeratore `tourismBeds` non coerente con il valore del rapporto pubblicato.

Esito verificato dal primo gate effettivo: **+4 coppie → 1.759 classificate / 266 residue**; B scende da 36 a 32.

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

1. Portare `#233` a A3 gate, Quick e Full GREEN sullo stesso head e verificare **1.759 / 266**.
2. Dopo merge autorizzato, proseguire sulle **32 B residue** con ulteriori contratti cross-source verificabili.
3. Chiudere quindi C semantic closure e D official-source evidence.
4. A3.2 termina soltanto a `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
