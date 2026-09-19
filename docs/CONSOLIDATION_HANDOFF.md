# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — chiusura classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS` fino a merge del gate strict finale
- **Main verificato:** `14a96153d9057aa3551cddad876fb2adf451cc99` (merge `#256`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#256:** 2.025 coppie; **1.982 classificate, 43 residue**
- **A3 final head #256:** run `35441146078` **GREEN**
- **Pages final head #256:** run `35441146083` **GREEN** (Quick + Full)
- **Pages post-merge #256:** run `35442368172` **GREEN** (build + deploy)
- **Live status post-merge #256:** `ov-pages-live` **SUCCESS**
- **Branch corrente:** `chore/a3-2-final-residual-closure`

## Intervento corrente — chiusura finale A3.2

Il batch chiude tutte le **43** coppie residue senza iniziare A3.3:

- **2 `ACQUIRED` strutturali:** `foreignResidents × categorie_specifiche` tramite detector generico di collezioni categoriali strutturate; `population × assoluto_normalizzato` tramite relazione verificata `population / municipalSurface = populationDensity`.
- **10 `AVAILABLE_MISSING`:** benchmark/componenti redditi reali; dettaglio nazionale foreste; benchmark affluenza; dettaglio LODE ERP; normalizzazioni Frame SBS; serie superficie/densità; serie RSA accreditate.
- **24 `SOURCE_UNAVAILABLE`:** disaggregazioni non comparabili di redditi/agricoltura/demografia; serie/categorie non offerte in forma omogenea da foreste, ERP, RSA, ARS, GAIA, farmacie, ISPRA, Istat costa, aree protette, Iter.Net e SISBON.
- **7 `NOT_APPLICABLE`:** valore assoluto del sintetico redditi-vs-inflazione; serie dei cinque inventari editoriali Percorsi; frequenza infra-annuale dell'affluenza elettorale.

Il workflow A3 passa da `--allow-unclassified` alla validazione **strict**.

**Esito atteso:** **2.025 classificate / 0 residue**.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale di indicatori.
3. `ACQUIRED` solo da evidenza strutturata o formula verificata.
4. `AVAILABLE_MISSING` / `SOURCE_UNAVAILABLE` solo con evidenza ufficiale verificabile.
5. `NOT_APPLICABLE` solo metric-specific e semanticamente dimostrabile.
6. Classificazioni source-profile solo se valide per tutto il profilo.
7. A3.2 è chiuso soltanto se la matrice strict restituisce `unclassifiedPairCount = 0`.
8. Nessun A3.3 in questa PR.
9. Nessun merge/pubblicazione senza A3, Quick e Full GREEN sul final head e approvazione esplicita del proprietario.
10. Il preflight locale non è stato eseguito perché il runtime della sessione non risolve `github.com`; non dichiararlo come eseguito.

## Prossima azione esatta

1. Aprire una sola PR sul branch corrente.
2. Eseguire un unico ciclo A3 Enrichment Audit + Quick + Full sul final head.
3. Verificare nel log A3 il conteggio esatto **2.025 / 0** e le 43 chiusure.
4. Fermarsi prima del merge.
5. Solo dopo merge autorizzato, verificare deploy/live post-merge e avviare A3.3 in una nuova attività.
