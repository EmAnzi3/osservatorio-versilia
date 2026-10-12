# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 12 ottobre 2026

- Baseline dopo merge del proprietario #412: main `0aaf14dda8ab8fb1ac657afae934a8668f80b0d0`, albero `3164d9f164c21b1a75d657c179a784e1a5406ccc`, identico al lotto con Quick/Full locali completi e CI Quick→Full/A3 verdi. Include manutenzioni #407/#411 e separazione refresh AGCOM #413. Copertura 216/225 effettivi, 159/181 sorgente, nove residui; 2.847 PASS.
- Catalogo effettivo corrente rigenerato: 225 indicatori, 124 storici, 137 confronti, SHA `d9fea44f9cf3e56309e1193bf63b5cfe32bfbc3ba088860843db8d14b9c12278`; registro SHA `261304eb74262058ba42f38d0b4584a3038f184e3bc602ab8e0b5d9eb9d13d5c`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-third-sector-adapter`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

RUNTS v48: un carrier, tre viste densità/conteggio/rapporto nativo, confronto/rango 7/7; pooling soltanto nativo con sedi legali disgiunte per fotografia. Registro 11 ottobre 2026 distinto da residenti 1 gennaio 2026. 465 enti su 158.520 residenti; nessuna misura di attività, servizi o volontari. Snapshot normalizzato riconciliato, workbook/record individuali non rigiocati. Storia/trasferimenti, benchmark, anomalie e coppie non revisionate rifiutati. Metodo `docs/A6_THIRD_SECTOR_ADAPTERS.md`.

21 osservazioni fisse, 14 componenti, due aggregati, puntatori/date/alias e prove ostili dopo cache. 81 domande nuove e 2.847 precedenti invariate; suite 2.928 PASS (1.596 calcoli, 1.332 rifiuti). Copertura derivata 217/225 effettivi, 160/181 sorgente, otto residui. Report `reports/a6-third-sector/`; gate canonici da completare sul medesimo albero.

## Prossima azione

Quick locale completo su clone pulito prima del push e apertura PR; Full locale completo sequenziale, identità alberi e CI Quick→Full/A3 prima della prontezza. Merge riservato al proprietario. Browser locali mai in parallelo; ricevute e log nel fascicolo. Residui: voterTurnout, economyActivityAtlas, fuelPrices, pnrrConcluded, pnrrFunding, omiResidential, outsideMunicipality, evPoints. Chiusura metodologica distinta dal numero degli adapter.

## Manutenzioni e monitor separati

#407: SISBON 154 codici (58 attivi/96 chiusi), MIMIT puntuale 10 ottobre/storico fino a settembre, ARS timeout 120 secondi; ZIP 255 del proprietario 2015–2025 invariato. #411: RUNTS Excel 11 ottobre verificato (SHA invariato), 465 sedi e denominatori 1 gennaio 2026; AGCOM consistenze 6 luglio/revisione 14 luglio corrette sugli input già congelati, nessun nuovo CSV acquisito. #413: live refresh AGCOM soltanto dispatch/comando esplicito, contratti/test offline preservati. Radar #402, PNRR 25 settembre, #338 mensile, #329 ASIA/AGCOM e #117 watchdog separati; #306 archiviata. Nessuna acquisizione nel lotto A6.

Manutenzione Radar rumore — base main #414 `8b2726e`, separata da A6. Esclude navigazione/footer dalla discovery e dagli allegati; rimuove dalla coda cataloghi, archivi espliciti e resoconti amministrativi senza nuova candidatura. Versione lettore allegati aggiornata per rivalutare le vecchie ricerche; statuto ANCI e relativi errori non generano richieste manuali. Scarti motivati conservati nel JSON, riaperture/termini futuri/avvisi nazionali preservati. Replay runtime 12 ottobre `71bd9291e8b9eb5e`: discovery 141→90, interventi tecnici 77→62, ritentativi 33→24; 60 schede, archivio e salute fonti identici. Test mirati verdi; gate Quick/Full da completare sullo stesso albero, merge riservato al proprietario.

PR #417: Quick iniziale verde; i due dry-run live hanno bloccato la microzonazione ancora aperta (17 ottobre), assente dal listing. Recupero corretto con alias dichiarati, ultimo URL pubblico verificato e 30 secondi riservati alla continuità dentro i 180 secondi per host/fonte. Test positivi/negativi verdi; pagina primaria live riconfermata in 8,4 secondi anche dopo esaurimento della quota discovery; replay recupera il hold e mantiene 60 schede. Nuovi gate completi e dry-run da concludere prima della prontezza; nessun merge/pubblicazione eseguito.
