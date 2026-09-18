# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Parent #240 head:** `f89b75129c2f8be152a398113796fdf4ab690978` (post-`#239` main + tranche #240)
- **Catalogo pubblico governato:** 225 indicatori
- **Perimetro monitor A2 verificato:** 225 indicatori / 122 fonti
- **Parent #240 atteso/verificabile:** 2.025 coppie; **1.776 classificate, 249 residue**
- **Branch corrente:** `chore/a3-2-demographic-average-denominators`
- **PR corrente:** `#241` (stacked su `#240`)

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
- `#232` ha reso esplicito nel gate A3 il report di tutte le residue; `#233` ha chiuso 4 coppie ratio companion (`tourismIntensity`, `commuterBalanceRate`) → **1.759 / 266**.\n- `#234` ha chiuso 5 coppie demografiche tramite `series_change_formula` e `parts_ratio_formula` → **1.764 / 261**.
- `#235` ha chiuso 4 coppie commuter-rate (`inboundCommutersRate`, `outboundCommutersRate`) → **1.768 / 257**; A3, Quick e Full verdi prima del merge.
- `#237` riguarda il Radar opportunità e non modifica la matrice A3.2.
- `#238` ha chiuso 2 coppie `municipalStaffTurnover` → **1.770 / 255**; A3 e Pages verdi prima del merge.
- La Residual Closure Audit è stata ricalcolata sulle 320 residue reali post-#225: **A 43 / B 43 / C 34 / D 200**.

## Residual Closure Audit parent #240

Le **249 residue** attese sul parent #240 si ricompongono così:

- **B — cross-source / companion:** 15
- **C — semanticamente `NOT_APPLICABLE`:** 34
- **D — verifica fonte ufficiale necessaria:** 200

Il bucket A strutturale è chiuso. B procede soltanto con relazioni companion verificabili numericamente o strutturalmente.

## Intervento corrente — tranche demografia

La tranche stacked successiva a `#240` chiude 4 residue B `numeratore_denominatore`:

- `internalResidentialMobility`;
- `foreignResidentialMobility`;
- `totalResidentialMobility`;
- `naturalDemographicDynamics`.

Il contratto generico `part_count_average_population_formula` verifica per tutti i Comuni il conteggio assoluto nel `part` selezionato contro la popolazione media annua derivata dalla serie pubblica `population`: media tra popolazione all'inizio dell'anno target e all'inizio dell'anno successivo. La formula è validata 7/7 e fallisce su label, conteggi, anni, denominatori o valori discordanti.

**Esito atteso:** **1.780 classificate / 245 residue**; B da 15 a 11.

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

1. Chiudere `#239` sul final head soltanto con A3, Quick e Full GREEN.
2. Riallineare e portare `#240` a **1.776 / 249** su `main` post-`#239`.
3. Riallineare questa tranche sul `main` post-`#240`, aprire la PR e verificare **1.780 / 245** con A3, Quick e Full.
4. Dopo merge autorizzato, ricalcolare le **11 B residue**, poi chiudere C e D.
5. A3.2 termina soltanto a `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
