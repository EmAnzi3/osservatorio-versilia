# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.4` — backlog ordinato degli `AVAILABLE_MISSING`
- **Stato:** `IN_PROGRESS` fino al merge del gate A3.4
- **Main verificato:** `8a945095b5275ee7efe178a620381d498a9a4a58` (merge `#258`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2:** 2.025 coppie; **2.025 classificate, 0 residue**
- **A3 final head #258:** run `35447973053` **GREEN**
- **Pages final head #258:** run `35447973039` **GREEN** (Quick + Full)
- **Pages post-merge #258:** run `35450390573` **GREEN**
- **Live status post-merge #258:** run `35450681832` **GREEN**
- **A3.3 source audit:** 63 profili fonte · 225 indicatori · 2.025 coppie · **872 AVAILABLE_MISSING**
- **Branch corrente:** `chore/a3-4-enrichment-backlog`

## Intervento corrente — A3.4 enrichment backlog

Il branch trasforma automaticamente tutte le coppie `AVAILABLE_MISSING` in un backlog operativo senza copiare indicatori in un nuovo inventario:

- input esclusivi: matrice A3 strict + audit A3.3;
- unità di copertura: coppia indicatore × dimensione;
- unità operativa: pacchetto `sourceProfileId × dimensione`;
- ogni `AVAILABLE_MISSING` deve comparire esattamente una volta;
- valore informativo: policy esplicita e versionata per dimensione;
- costo: proxy deterministico 1..5, non stima di tempi o euro;
- ordinamento: `priorityIndex = informationValuePoints / costPoints`;
- output derivati: `a3-enrichment-backlog.json` e `a3-enrichment-backlog.md`;
- nessuna acquisizione dati in A3.4: l'integrazione resta A3.5.

Il workflow deve derivare il conteggio corrente (oggi 872) dalla matrice: **872 non è una costante del codice**.

## Hardening A3.3 incluso

La review automatica di #258 aveva lasciato due P2 validi non recepiti prima del merge. Il branch li chiude nello stesso intervento, senza micro-PR separata:

1. il regression test che verifica la persistenza della matrice diagnostica viene ora realmente invocato dal `__main__` e importa le dipendenze necessarie;
2. il Markdown A3.3 espone anche licenza e conteggi delle origini di classificazione, coerentemente con la metodologia dichiarata.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale di indicatori, fonti o opportunità.
3. A3.2 resta chiuso a `unclassifiedPairCount = 0`.
4. A3.3 resta derivato dalla matrice e dal source registry.
5. A3.4 deve coprire esattamente tutte e sole le coppie `AVAILABLE_MISSING`.
6. Il modello di priorità A3.4 è una policy trasparente, non una misura oggettiva del costo reale.
7. Nessun A3.5 in questa PR.
8. Nessun merge/pubblicazione senza A3, Quick e Full GREEN sul final head e approvazione esplicita del proprietario.
9. Il preflight locale non è stato eseguito: il runtime continua a restituire `Could not resolve host: github.com`.

## Prossima azione esatta

1. Aprire una sola PR Ready dal branch corrente.
2. Eseguire un unico ciclo A3 Enrichment Audit + Quick + Full sul final head.
3. Verificare che A3 resti **2.025 / 0**.
4. Verificare che A3.4 copra tutte le **872** coppie correnti senza duplicati/perdite e riporti il numero derivato di pacchetti.
5. Verificare la presenza degli artifact `a3-source-audit` e `a3-enrichment-backlog`.
6. Fermarsi prima del merge.
7. Solo dopo merge autorizzato, verificare deploy/live post-merge e avviare A3.5.
