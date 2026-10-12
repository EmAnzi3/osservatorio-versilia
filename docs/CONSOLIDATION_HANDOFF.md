# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 12 ottobre 2026

- Baseline dopo merge del proprietario #418: main `404ca19430b724319aa35ce16fb8a2ac632fe088`, albero `baf4fc859164db307142c7960cfa8f53732d428c`. PNRR v50: 220/225 effettivi, 162/181 sorgente, cinque residui; 3.322 PASS. Quick/Full locali e CI Quick→Full/A3 conclusi verdi nella #418; pubblicazione comunicata dal proprietario.
- Catalogo effettivo rigenerato: 225 indicatori, 124 storici, 137 confronti, SHA `d9fea44f9cf3e56309e1193bf63b5cfe32bfbc3ba088860843db8d14b9c12278`; registro SHA `261304eb74262058ba42f38d0b4584a3038f184e3bc602ab8e0b5d9eb9d13d5c`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-omi-adapter`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi preservati.

## Lotto in verifica

OMI v51: un carrier, tre viste comunali (alias vendita, vendita e affitto mensile); secondo semestre 2025 esplicito. Riferimenti territoriali, non prezzi effettivi o canoni registrati. 46 zone/92 valori pubblicati riconciliati con medie semplici comunali e media dei sette Comuni; nessuna ponderazione per transazioni/abitazioni. Originali OMI e intervalli min/max non rigiocati. Query comunali, nessuna equivalenza tra codici di zona di Comuni diversi. Metodo `docs/A6_OMI_ADAPTERS.md`.

14 riferimenti comunali fissi, alias/pari merito, puntatori e guardie su input/cache; 63 domande nuove con 3.322 precedenti preservate. Suite 3.385/3.385 PASS (1.844 calcoli e 1.541 rifiuti); copertura derivata 221/225 effettivi, 163/181 sorgente, quattro residui. Report `reports/a6-omi/`; gate canonici ancora da completare.

## Prossima azione

Concludere suite/audit/benchmark OMI. Quick locale completo su clone pulito prima del push/apertura PR. Full locale completo sequenziale e CI Quick→Full/A3 con identità degli alberi prima della prontezza. Merge del proprietario. Browser locali mai in parallelo; log/ricevute nel fascicolo. Residui dopo OMI da confermare: economyActivityAtlas, fuelPrices, outsideMunicipality, evPoints. Chiusura metodologica distinta dal numero degli adapter.

## Manutenzioni e monitor separati

#407: SISBON 154 codici (58 attivi/96 chiusi), MIMIT puntuale 10 ottobre/storico fino a settembre, ARS timeout 120 secondi; ZIP 255 del proprietario 2015–2025 invariato. #411: RUNTS Excel 11 ottobre verificato (SHA invariato), 465 sedi/residenti 1 gennaio 2026; AGCOM consistenze 6 luglio/revisione 14 luglio corrette su input congelati, nessun CSV acquisito. #413: refresh AGCOM soltanto dispatch/comando esplicito, test offline preservati. Radar #402, PNRR 25 settembre, #338 mensile, #329 ASIA/AGCOM e #117 watchdog separati; #306 archiviata. Nessuna acquisizione nel lotto A6.
