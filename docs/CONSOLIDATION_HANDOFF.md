# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 13 ottobre 2026

- Baseline reale `main` `16bb319b2cda57127e9b66d1c1a75c68b6280519`, albero `ef94d1bf09a1ede9f4d7692e173f2afbb9b2d32c`: #423 e #424 mergiate dal proprietario. Deploy e live-status su main risultano SUCCESS; nessun merge/deploy dell'assistente.
- #423 completa gli adapter: 225/225 effettivi, 166/181 sorgente, zero carrier residui, 2.457 viste Atlante. Baseline 3.727 casi (2.033 calcoli/1.694 rifiuti); copertura non equivale a chiusura metodologica.
- A0–A5 DONE; A6 attiva, issue #330. A6.1–A6.3 integrate, A6.4 parziale e A6.5–A6.6 aperte; A7 non avviata.
- Camaiore checkpoint `5aaf159870912eb49bffbd044963549bfb920150`, 40 golden master, UI/asset, 35 letture e due riepiloghi conservati. Radar #424 è baseline separata, non modificata da questo lotto.

## Lotto candidato — correzione Atlante v55

Branch `fix/a6-atlas-territorial-total`, base main sopra. Materializzatore di produzione: riepilogo dai totali nativi `tt`, non dalle sole divisioni ATECO (292). Totali 2025 per ISTAT: 046005=3822, 046013=1556, 046018=1940, 046024=3327, 046028=1437, 046030=245, 046033=7998; somma 20.325. Metadati esplicitano formula e universo. File congelati, serie 2014–2025, classificazioni, gerarchie e runtime invariati.

`total` implicito ancora rifiutato per scelta esplicita (`atlas_explicit_view_required`), senza più motivazione di carrier non riconciliato. Nessuna nuova operazione autorizzata. Fingerprint del carrier aggiornato; regressioni avversarie su assi, identità, null/zeri, totali incompleti, categorie duplicate e tutte le 84 celle territoriali via query. Fonte delle aspettative: tabella congelata, già trascritta nella #423; nessun replay dei CSV originali o verifica live dichiarato.

Test mirati e suite 3.727/3.727 PASS sul catalogo effettivo corretto. Il primo Full ha fallito il controllo RCS immediato dopo navigazione; il test originale passa integralmente su baseline e candidato in replay sequenziale, e otto navigazioni mirate confermano il dettaglio. Le quattro navigazioni RCS ora usano il helper condiviso di prontezza client/vista/font, preservando tutte le asserzioni geometriche e di contenuto. Nuovi Quick/Full locali sequenziali e CI Quick→Full/A3 devono verificare il candidato con questa correzione prima del merge. Nessun gate della #423 viene riutilizzato come prova del candidato.

## Prossima azione

Concludere gate locali, aprire PR Atlante Draft e verificare CI/effetti pubblici; approvazione e merge riservati al proprietario. Dopo correzione e integrazione: audit globale A6.4/A6.6, revisione integrale A6.5 (35 letture e due riepiloghi), repertorio di domande e lacune. PR di chiusura soltanto dopo integrazione/verifica delle precedenti, quindi handoff A7. Non dichiarare A6 DONE anticipatamente.

## Manutenzioni separate

Monitor fonti #338/#329/#117, Radar e acquisizioni live fuori perimetro. Nessuna nuova UI A7, modello linguistico o servizio esterno introdotto.
