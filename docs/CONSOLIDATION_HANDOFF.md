# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato prima della tranche:** `405b08b5e98828934bcea1df74562e5a5310242a` (merge `#241`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#241:** 2.025 coppie; **1.780 classificate, 245 residue**
- **A3 #241:** run `35370483761` **GREEN**
- **Pages #241:** run `35370483766` **GREEN**
- **Branch corrente:** `chore/a3-2-siope-canonical-ratios`
- **PR corrente:** `#242`

## Residuo effettivo post-#241

La matrice è stata ricostruita dal log A3 finale di `#241`, non dall'handoff precedente.

- **A — falsi residui strutturali:** 0
- **B — cross-source / companion:** **11**
- **C — semanticamente `NOT_APPLICABLE`:** **34**
- **D — verifica fonte ufficiale necessaria:** **200**
- **Totale:** **245**

Le 11 coppie B residue sono:

- `currentPayments / numeratore_denominatore`
- `capitalPayments / numeratore_denominatore`
- `siopePayments / numeratore_denominatore`
- `evPoints / numeratore_denominatore`
- `publicWorks / numeratore_denominatore`
- `roadFinesPerResident / assoluto_normalizzato`
- `roadFinesPerResident / numeratore_denominatore`
- `pharmaciesPer1000 / assoluto_normalizzato`
- `pharmaciesPer1000 / numeratore_denominatore`
- `tourismStructuresPer1000 / assoluto_normalizzato`
- `tourismStructuresPer1000 / numeratore_denominatore`

## Intervento corrente — tranche SIOPE

La tranche chiude soltanto le tre coppie SIOPE `numeratore_denominatore`.

Il contratto `canonical_field_ratio_formula` dichiara il percorso concreto del numeratore già strutturato nel canonico `data/site-data.json` e usa `population` come companion del denominatore. Il detector resta generico e:

- allinea i record per identità comunale;
- legge soltanto percorsi dichiarati dal contratto;
- usa la popolazione dell'anno successivo al target (`target_next_year`);
- verifica numericamente il rapporto per tutti i record;
- fallisce chiuso su record, campo, anno, denominatore o valore discordante;
- richiede almeno due verifiche e non contiene ID metrici hard-coded.

Verifica preliminare sul canonico post-#241: **7/7 Comuni** coerenti per tutte e tre le metriche.

**Esito atteso:** **1.783 classificate / 242 residue**; bucket B da **11 a 8**. C e D restano invariati a 34 e 200.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente; l'Effective Public Catalog resta una vista derivata.
2. A3 non deve introdurre una seconda lista manuale di indicatori o fonti.
3. L'unità di audit è `indicatore pubblico × dimensione enrichment`.
4. Ogni coppia finale deve avere uno stato tra `ACQUIRED`, `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE`, `NOT_APPLICABLE`.
5. `ACQUIRED` richiede evidenza strutturata/formula verificata e non può essere dichiarato manualmente.
6. `AVAILABLE_MISSING` e `SOURCE_UNAVAILABLE` richiedono evidenza ufficiale verificabile; `NOT_APPLICABLE` solo metric-specific.
7. I detector generici non devono hard-codare ID metrici; le relazioni concrete appartengono ai contratti.
8. Ogni formula deve essere fail-closed.
9. A3.2 non è chiuso finché `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
10. Nessun merge/pubblicazione senza A3, Quick e Full pertinenti GREEN e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Portare `#242` a A3 Enrichment Audit, Quick e Full GREEN sul final head.
2. Verificare nel log A3 il conteggio esatto **1.783 / 242** e l'evidenza `canonical_field_ratio_formula` sulle tre coppie.
3. Fermarsi prima del merge.
4. Dopo merge autorizzato, ricostruire le 8 B residue effettive e procedere per sottoinsiemi omogenei; poi C e D.
5. A3.2 termina soltanto a `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
