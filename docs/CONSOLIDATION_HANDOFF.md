# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato:** `4eb6413ca0729036d00c6fe23775428130a2e3ae` (merge `#243`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#243:** 2.025 coppie; **1.789 classificate, 236 residue**
- **A3 final head #243:** run `35380701626` **GREEN**
- **Pages post-merge #243:** run `35383489445` **GREEN**
- **Branch corrente:** `chore/a3-2-close-road-fines-ratios`
- **PR corrente:** da aprire

## Residuo effettivo post-#243

Il bucket A strutturale è chiuso. Dopo #243 restano nel bucket B soltanto:

- `roadFinesPerResident / assoluto_normalizzato`
- `roadFinesPerResident / numeratore_denominatore`

Bucket prima della tranche:

- **B — cross-source / companion:** 2
- **C — semanticamente `NOT_APPLICABLE`:** 34
- **D — verifica fonte ufficiale necessaria:** 200
- **Totale:** 236

## Intervento corrente — road fines

Entrambe le coppie vengono classificate `AVAILABLE_MISSING` con evidenza ufficiale Istat/DAIT.

La nota metodologica Istat definisce esplicitamente l'indicatore come:

`Totale proventi violazioni al codice della strada / Popolazione residente media`

e indica come fonte il rendiconto del Ministero dell'Interno — Dipartimento per gli Affari Interni e Territoriali.

Nel canonico `roadFinesPerResident` sono presenti soltanto il valore per abitante e la serie 2021–2024; il totale proventi e il denominatore non sono conservati come componenti strutturate della metrica. Non esiste quindi evidenza per `ACQUIRED`, ma esiste evidenza ufficiale sufficiente per `AVAILABLE_MISSING`.

**Esito atteso:** **1.791 classificate / 234 residue**. Il bucket B scende a **0**; restano C=34 e D=200.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale di indicatori.
3. `ACQUIRED` solo da evidenza strutturata o formula verificata.
4. `AVAILABLE_MISSING` / `SOURCE_UNAVAILABLE` solo con evidenza ufficiale verificabile.
5. `NOT_APPLICABLE` resta metric-specific.
6. A3.2 non è chiuso finché `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
7. Nessun merge/pubblicazione senza A3, Quick e Full GREEN sul final head e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Aprire la PR della tranche road fines.
2. Portare A3 Enrichment Audit, Quick e Full GREEN sul final head.
3. Verificare nel log A3 il conteggio esatto **1.791 / 234** e i due `AVAILABLE_MISSING`.
4. Fermarsi prima del merge.
5. Dopo merge autorizzato, il bucket B è chiuso: procedere con C semantic closure, quindi D official-source evidence.
6. A3.2 termina soltanto a `unclassifiedPairCount = 0`; nessun A3.3 prima dello zero.
