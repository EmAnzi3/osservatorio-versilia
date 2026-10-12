# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 12 ottobre 2026

- Baseline dopo merge del proprietario #414: main `8b2726ea023b84ffc58d6a9b34556cac2d7696e5`, albero `d20dde15c4eb0a31c51a107e1bdf114d40e67f2b`. Include RUNTS v48, manutenzioni #407/#411 e separazione refresh AGCOM #413. Quick/Full locali completi e CI Quick→Full/A3 verdi sullo stesso albero; ricevuta Full conclusiva dopo riesecuzione completa della prima esecuzione interrotta. 217/225 effettivi, 160/181 sorgente, otto residui; 2.928 PASS.
- Catalogo effettivo corrente rigenerato: 225 indicatori, 124 storici, 137 confronti, SHA `d9fea44f9cf3e56309e1193bf63b5cfe32bfbc3ba088860843db8d14b9c12278`; registro SHA `261304eb74262058ba42f38d0b4584a3038f184e3bc602ab8e0b5d9eb9d13d5c`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-turnout-adapter`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

Affluenza v49: carrier solo effettivo, 26 viste, 71 consultazioni sovracomunali 7/7; conteggi elettori/votanti, quattro famiglie, sesso solo con componenti completi. ID esatti e quesiti distinti, valori pubblici a quattro decimali separati dai rapporti nativi; alias corrente referendum marzo 2026. Pooling solo nativo entro stessa consultazione/sesso, serie irregolari per Camera/Europee/Regionali. Referendum come consultazioni distinte, nessuna serie univoca del quesito. Regionali 1990: flag mfComplete insufficiente, zero/null femminili trattati come mancanza di componenti. Comunali a date diverse e contesti provinciali esclusi; nessuna interpolazione, trend/variazione, benchmark, anomalia o coppia inferita. Metodo `docs/A6_TURNOUT_ADAPTERS.md`.

28 coppie correnti, 28 per sesso e 41 storiche fisse; replay distinto 2.982 celle normalizzate incluse mancanti, non file DAIT originali. Puntatori, formule/aggregati, ID, lacune e prove ostili. 260 domande nuove e 2.928 precedenti invariate; 3.188 PASS (1.758 calcoli, 1.430 rifiuti). Copertura derivata 218/225 effettivi, 160/181 sorgente invariata, sette residui. Report `reports/a6-turnout/`; gate canonici da completare sul medesimo albero.

## Prossima azione

Quick locale completo su clone pulito prima del push/apertura PR del lotto affluenza. Full locale completo sequenziale e CI Quick→Full/A3 con identità degli alberi prima della prontezza. Merge del proprietario. Browser locali mai in parallelo; log/ricevute nel fascicolo. Residui: economyActivityAtlas, fuelPrices, pnrrConcluded, pnrrFunding, omiResidential, outsideMunicipality, evPoints. Chiusura metodologica distinta dal numero degli adapter.

## Manutenzioni e monitor separati

#407: SISBON 154 codici (58 attivi/96 chiusi), MIMIT puntuale 10 ottobre/storico fino a settembre, ARS timeout 120 secondi; ZIP 255 del proprietario 2015–2025 invariato. #411: RUNTS Excel 11 ottobre verificato (SHA invariato), 465 sedi e denominatori 1 gennaio 2026; AGCOM consistenze 6 luglio/revisione 14 luglio corrette sugli input già congelati, nessun nuovo CSV acquisito. #413: live refresh AGCOM soltanto dispatch/comando esplicito, contratti/test offline preservati. Radar #402, PNRR 25 settembre, #338 mensile, #329 ASIA/AGCOM e #117 watchdog separati; #306 archiviata. Nessuna acquisizione nel lotto A6.
