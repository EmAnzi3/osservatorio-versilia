# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A3 — Enrichment Audit globale
- **Step attivo:** A3.6 — copertura enrichment e chiusura A3
- **Stato:** IN_PROGRESS — PR di chiusura A3 in preparazione; target `DONE` al merge
- **Main verificato:** `e445605a0121a089932acbc8686d8425ea032ad3` (merge #267)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2:** 2.025 coppie; 2.025 classificate; 0 residue
- **Baseline post-#267:** 544 `ACQUIRED` · 752 `AVAILABLE_MISSING` · 374 `SOURCE_UNAVAILABLE` · 355 `NOT_APPLICABLE`
- **Opportunità acquisibili:** 1.296 = `ACQUIRED + AVAILABLE_MISSING`
- **Copertura enrichment:** 544 / 1.296 = **42,0%**
- **A3.5:** 8 lotti mergiati (#260–#267), 120 nuove coppie acquisite; backlog 872 → 752
- **Backlog A3.4 residuo:** 752 opportunità · 257 pacchetti · 63 source profile
- **Branch corrente:** `feat/a3-5-bulk-enrichment-lot-9`
- **PR corrente:** da aprire — chiusura A3 + A3.6
- **Prossimo workstream dopo il merge:** A4 — Visualization & Content Contract, a partire da A4.1

## Criterio di chiusura A3

A3.5 non richiede di azzerare `AVAILABLE_MISSING`. Il backlog A3.4 è una roadmap governata di opportunità di prodotto, non debito obbligatorio del consolidamento.

Gli otto lotti A3.5 hanno verificato end-to-end più famiglie di fonte e dimensioni con:
- evidenza strutturale per ogni `ACQUIRED`;
- QA e riconciliazione contro fonti/snapshot ufficiali;
- nessun override manuale `ACQUIRED`;
- nessuna retro-derivazione di valori mancanti;
- nessuna modifica UI nei lotti puramente strutturali.

A3.6 deriva automaticamente dalla matrice strict la copertura:
`ACQUIRED / (ACQUIRED + AVAILABLE_MISSING)`.

`SOURCE_UNAVAILABLE` e `NOT_APPLICABLE` non entrano nel denominatore. Il valore è diagnostico, non un punteggio di qualità e non implica un target del 100%.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale.
3. A3.2 resta strict a `unclassifiedPairCount = 0`.
4. `ACQUIRED` deriva solo da struttura/formula/evidenza verificabile.
5. Le 752 opportunità residue restano integralmente nel backlog A3.4; non vengono riclassificate per ridurre artificialmente il residuo.
6. Le future acquisizioni A3.4 sono miglioramenti di prodotto e non riaprono A3 salvo modifica della metodologia o dei contratti.
7. Nessuna modifica UI/rendering nella PR di chiusura A3.

## Prossima azione esatta

1. Aprire PR Ready per chiusura A3 + A3.6.
2. Verificare sul final head A3, Quick e Full verdi.
3. Confermare artifact A3.6 con 544/1.296 = 42,0% e 752 `AVAILABLE_MISSING`.
4. Correggere solo regressioni reali senza indebolire detector o contratti.
5. Merge soltanto dopo approvazione esplicita del proprietario.
6. Dopo il merge avviare A4.1.
