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
- **Branch corrente:** `chore/a3-2-affluenza-route-contract`
- **PR corrente:** `#229`

## Completato

- `A0` chiuso con `#188`; `A1` con `#190/#193`; `A2` con `#194` e hardening `#195–#203`; `A3.1` con `#204`.
- `#206` ha introdotto la matrice A3.2 derivata dall'Effective Public Catalog.
- Progressione A3.2 fino a `#225`: **1.705 / 2.025**.
- `#226` ha chiuso 30 falsi residui same-payload: **1.735 classificate / 290 residue**.
- `#227` ha introdotto il resolver route-aware ma le due special-route non dichiaravano ancora il payload; nessuna chiusura special-route effettiva.
- `#228` ha aggiunto il resolver companion verificato, il gate A3 sul catalogo effettivo e ha chiuso 7 coppie demografiche `eta` più la coppia climate normalizzata: **1.743 classificate / 282 residue**. A3 audit, Quick e Full verdi prima del merge.

## Residual Closure Audit post-#228

- **A — falso residuo strutturale:** 12
- **B — cross-source / companion:** 36
- **C — semanticamente `NOT_APPLICABLE`:** 34
- **D — verifica fonte ufficiale necessaria:** 200

Le 12 A residue sono esclusivamente le due special-route:

- `voterTurnout`: 6 coppie — serie storica, sesso, dettaglio territoriale, assoluto/normalizzato, numeratore/denominatore, categorie specifiche.
- `economyActivityAtlas`: 6 coppie — serie storica, dettaglio territoriale, benchmark Toscana/Italia, assoluto/normalizzato, numeratore/denominatore, categorie specifiche.

## Intervento corrente — #229

`#229` chiude le 6 coppie `voterTurnout` collegando il contratto `dataStorage` al payload runtime reale `data/affluenza/archive-v2-00…03.b64`.

Il detector resta generico: supporta chiavi camelCase e vocabolario strutturale per territori, famiglie e turnout; una semplice data non viene più interpretata come frequenza infra-annuale.

**Esito atteso:** **1.749 classificate / 276 residue**, con A ridotto da 12 a 6. Il gate A3 verifica esplicitamente il conteggio e le sei evidenze Affluenza sull'Effective Public Catalog.

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

1. Portare `#229` a A3 audit, Quick e Full GREEN sull'head finale e verificare **1.749 / 276**.
2. Dopo merge autorizzato di `#229`, chiudere le 6 A residue di `economyActivityAtlas` con un contratto esplicito per il payload compatto, senza hard-code di ID nel detector.
3. Ricalcolare la closure audit sul residuo effettivo.
4. Passare quindi alle 36 B residue, poi C e D.
5. Ripetere tranche verificabili fino a `unclassifiedPairCount = 0`; solo allora iniziare A3.3.
