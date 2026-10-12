# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 12 ottobre 2026

- Baseline dopo merge #420 e #417: main `4dfe03af24d6be7954b32952e3ccd0def6243906`; energia v51 integrata, 222/225 effettivi e 3.439 PASS.
- Catalogo effettivo rigenerato: 225 indicatori, 124 storici, 137 confronti, SHA `d9fea44f9cf3e56309e1193bf63b5cfe32bfbc3ba088860843db8d14b9c12278`; registro SHA `261304eb74262058ba42f38d0b4584a3038f184e3bc602ab8e0b5d9eb9d13d5c`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-omi-adapter`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi preservati.

## Lotto in verifica

#419 riallineata al main, motore v52 con OMI ed energia conservati. OMI: vendita e affitto comunali al secondo semestre 2025, 14 ancore fisse e replay di 92 valori pubblicati delle 46 zone; quotazioni distinte da transazioni/canoni registrati. Solo confronto e rango, nessun pooling, storico, benchmark o coppia non revisionata. Metodo `docs/A6_OMI_ADAPTERS.md`.

63 domande OMI aggiunte alle 3.439 del main, preservate integralmente; 3.502 PASS (1.893 calcoli, 1.609 rifiuti). Copertura derivata 223/225 effettivi, 165/181 sorgente, due residui. Report OMI rigenerati sulla versione combinata; quelli dei lotti precedenti restano evidenze storiche. Radar #417 preservato.

## Prossima azione

Quick locale canonico completo prima dell'aggiornamento della #419; Full locale sequenziale e CI Quick→Full/A3 sullo stesso albero prima della prontezza. Merge del proprietario. Residui economyActivityAtlas e outsideMunicipality; A6.4 parziale e chiusura metodologica distinta dalla copertura.

## Manutenzioni e monitor separati

#407: SISBON 154 codici (58 attivi/96 chiusi), MIMIT puntuale 10 ottobre/storico fino a settembre, ARS timeout 120 secondi; ZIP 255 del proprietario 2015–2025 invariato. #411: RUNTS Excel 11 ottobre verificato (SHA invariato), 465 sedi/residenti 1 gennaio 2026; AGCOM consistenze 6 luglio/revisione 14 luglio corrette su input congelati, nessun CSV acquisito. #413: refresh AGCOM soltanto dispatch/comando esplicito, test offline preservati. Radar #402, PNRR 25 settembre, #338 mensile, #329 ASIA/AGCOM e #117 watchdog separati; #306 archiviata. Nessuna acquisizione nel lotto A6.
