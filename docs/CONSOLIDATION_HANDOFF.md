# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.3` — audit fonte per fonte sul catalogo completo
- **Stato:** `IN_PROGRESS` fino a merge del gate A3.3
- **Main verificato:** `ad3ad336d1d6467475f13a3c869f7aaa790e99e1` (merge `#257`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2:** 2.025 coppie; **2.025 classificate, 0 residue**
- **A3 final head #257:** run `35443490785` **GREEN**
- **Pages final head #257:** run `35443490711` **GREEN** (Quick + Full)
- **Pages post-merge #257:** run `35446462208` **GREEN** (build + deploy)
- **Live status post-merge #257:** `ov-pages-live` **SUCCESS**
- **Branch corrente:** `chore/a3-3-source-audit`

## Intervento corrente — A3.3 source audit

Il branch introduce un audit fonte-per-fonte completamente derivato:

- la matrice A3 resta strict-complete a **2.025 / 0**;
- ogni metrica deve risolvere su un solo `sourceProfileId`;
- ogni profilo fonte usato deve esistere nel registry e avere publisher, frequenza, release attesa, metodo di acquisizione e licenza;
- per ogni profilo il numero di coppie deve essere esattamente `metriche × 9`;
- i conteggi per stato e origine devono riconciliarsi con la matrice A3 globale;
- le coppie `AVAILABLE_MISSING`, `SOURCE_UNAVAILABLE` e `NOT_APPLICABLE` vengono rese leggibili fonte per fonte;
- il workflow produce artifact `a3-source-audit.json` e `a3-source-audit.md`, senza introdurre un secondo inventario canonico.

Il conteggio dei profili fonte usati non è hard-coded: viene derivato a runtime dalla matrice dell'Effective Public Catalog.

## Hardening del gate strict

La review di #257 ha individuato un difetto diagnostico: una futura coppia non classificata avrebbe fatto fallire la validazione prima della scrittura della matrice.

Il branch corregge il comportamento:

1. la matrice diagnostica viene sempre scritta;
2. le residue vengono sempre riportate;
3. lo strict gate viene applicato in uno step successivo;
4. un regression test verifica che l'output resti disponibile anche quando lo strict gate fallisce.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale di indicatori o fonti.
3. A3.2 resta chiuso a `unclassifiedPairCount = 0`.
4. A3.3 usa esclusivamente il perimetro derivato dal catalogo effettivo e dalla matrice A3.
5. A3.3 non assegna priorità alle opportunità: la prioritizzazione appartiene ad A3.4.
6. Nessun A3.4 in questa PR.
7. Nessun merge/pubblicazione senza A3, Quick e Full GREEN sul final head e approvazione esplicita del proprietario.
8. Il preflight locale non è stato eseguito perché il runtime della sessione non risolve `github.com`; non dichiararlo come eseguito.

## Prossima azione esatta

1. Aprire una sola PR sul branch corrente.
2. Eseguire un unico ciclo A3 Enrichment Audit + Quick + Full sul final head.
3. Verificare che A3 resti **2.025 / 0**.
4. Verificare dal log A3.3 che tutti i profili fonte effettivamente usati coprano esattamente 225 indicatori e 2.025 coppie.
5. Verificare la presenza dell'artifact `a3-source-audit`.
6. Fermarsi prima del merge.
7. Solo dopo merge autorizzato, verificare deploy/live post-merge e avviare A3.4.
