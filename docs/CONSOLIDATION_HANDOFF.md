# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 12 ottobre 2026

- Baseline dopo merge del proprietario #416: main `4ffad7e02808a912528d201d2d8f1cb5db3a3ae7`, albero `ae40ec50f9612f99e0f5c0fa875f8de5c114dd80`. Affluenza v49: 218/225 effettivi, 160/181 sorgente, sette residui; 3.188 PASS. Quick/Full locali completi e CI Quick→Full/A3 verdi sullo stesso albero; merge distinto dal deploy pubblico.
- Catalogo effettivo rigenerato: 225 indicatori, 124 storici, 137 confronti, SHA `d9fea44f9cf3e56309e1193bf63b5cfe32bfbc3ba088860843db8d14b9c12278`; registro SHA `261304eb74262058ba42f38d0b4584a3038f184e3bc602ab8e0b5d9eb9d13d5c`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-pnrr-adapters`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi preservati.

## Lotto in verifica

PNRR v50: due carrier, sette viste 7/7; fotografia regionale 25 settembre 2026 e residenti 1 gennaio 2026 distinti. 101 ID unici attribuiti al Comune attuatore, non alla localizzazione (sei Viareggio/Camaiore, uno Stazzema/Sarteano). 36.683.107,64 € e 78 progetti macrofase ReGiS 5; quattro collaudi avviati inclusi. Viareggio 18 ReGiS contro 19 monitoraggio. Importi censiti diversi da erogazione/spesa, macrofase diversa da collaudo/servizio operativo. Replay dei 101 record normalizzati, non intero CSV originario; vecchie percentuali perTown non consumate. Pooling soltanto nativo su componenti additive della stessa fotografia. Storie/variazioni/trend, benchmark, anomalie e coppie non revisionate rifiutati. Metodo `docs/A6_PNRR_ADAPTERS.md`.

49 osservazioni fisse, 28 componenti, quattro rapporti territoriali, puntatori e prove ostili. 134 domande nuove e 3.188 precedenti invariate; suite 3.322 PASS (1.820 calcoli, 1.502 rifiuti). Copertura derivata 220/225 effettivi e 162/181 sorgente, cinque residui. Report `reports/a6-pnrr/`; gate canonici da completare sul medesimo albero.

## Prossima azione

Quick locale completo su clone pulito prima del push/apertura PR PNRR. Full locale completo sequenziale e CI Quick→Full/A3 con identità degli alberi prima della prontezza. Merge del proprietario. Browser locali mai in parallelo; log/ricevute nel fascicolo. Residui: economyActivityAtlas, fuelPrices, omiResidential, outsideMunicipality, evPoints. Chiusura metodologica distinta dal numero degli adapter.

## Manutenzioni e monitor separati

#407: SISBON 154 codici (58 attivi/96 chiusi), MIMIT puntuale 10 ottobre/storico fino a settembre, ARS timeout 120 secondi; ZIP 255 del proprietario 2015–2025 invariato. #411: RUNTS Excel 11 ottobre verificato (SHA invariato), 465 sedi/residenti 1 gennaio 2026; AGCOM consistenze 6 luglio/revisione 14 luglio corrette su input congelati, nessun CSV acquisito. #413: refresh AGCOM soltanto dispatch/comando esplicito, test offline preservati. Radar #402, PNRR 25 settembre, #338 mensile, #329 ASIA/AGCOM e #117 watchdog separati; #306 archiviata. Nessuna acquisizione nel lotto A6.
