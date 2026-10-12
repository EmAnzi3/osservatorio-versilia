# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 12 ottobre 2026

- Baseline dopo merge del proprietario #418: main `404ca19430b724319aa35ce16fb8a2ac632fe088`, albero `baf4fc859164db307142c7960cfa8f53732d428c`. PNRR v50: 220/225 effettivi, 162/181 sorgente, cinque residui; 3.322 PASS. Quick/Full locali completi e CI Quick→Full/A3 verdi sullo stesso albero; pubblicazione riferita dal proprietario.
- Catalogo effettivo rigenerato: 225 indicatori, 124 storici, 137 confronti, SHA `d9fea44f9cf3e56309e1193bf63b5cfe32bfbc3ba088860843db8d14b9c12278`; registro SHA `261304eb74262058ba42f38d0b4584a3038f184e3bc602ab8e0b5d9eb9d13d5c`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-energy-adapters`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi preservati.

## Lotto in verifica

Energia v51: due carrier, sei viste. Carburanti self: cinque fotografie e 57 mesi; mediana puntuale distinta dalla media mensile delle mediane giornaliere. Giorni osservati espliciti, Stazzema null e copertura parziale solo con consenso; conteggi impianti non ricostruiti dal massimo dei conteggi per combustibile. Densità EV pubbliche arrotondate, anno 2026; identità punto/connettore e date native/denominatore restano non certificate, diagnosi A3 irrisolta. Nessuna aggregazione di mediane o retro-derivazione dei punti. Serie consultabili solo carburanti; variazioni/trend, pooling, benchmark, anomalie e coppie non revisionate rifiutati. Metodo `docs/A6_ENERGY_ADAPTERS.md`.

21 ancore carburanti e sette EV, cinque coppie puntuali e tre mensili Massarosa; replay distinto 868 celle normalizzate incluse 124 null, non archivi/record originari. Provenienza/giorni/periodi e prove ostili. 117 nuove domande; 3.321 precedenti invariate, solo rifiuto legacy fuel_adapter_missing aggiornato al limite reale di copertura parziale, query e ID preservati. Suite 3.439 PASS (1.869 calcoli, 1.570 rifiuti). Copertura derivata 222/225 effettivi e 164/181 sorgente, tre residui. Report `reports/a6-energy/`; gate canonici da completare sul medesimo albero.

## Prossima azione

Quick locale completo su clone pulito prima del push/apertura PR energia. Full locale completo sequenziale e CI Quick→Full/A3 con identità degli alberi prima della prontezza. Merge del proprietario. Browser locali mai in parallelo; log/ricevute nel fascicolo. Residui: economyActivityAtlas, omiResidential, outsideMunicipality. Chiusura metodologica distinta dal numero degli adapter.

## Manutenzioni e monitor separati

#407: SISBON 154 codici (58 attivi/96 chiusi), MIMIT puntuale 10 ottobre/storico fino a settembre, ARS timeout 120 secondi; ZIP 255 del proprietario 2015–2025 invariato. #411: RUNTS Excel 11 ottobre verificato (SHA invariato), 465 sedi/residenti 1 gennaio 2026; AGCOM consistenze 6 luglio/revisione 14 luglio corrette su input congelati, nessun CSV acquisito. #413: refresh AGCOM soltanto dispatch/comando esplicito, test offline preservati. Radar #402, PNRR 25 settembre, #338 mensile, #329 ASIA/AGCOM e #117 watchdog separati; #306 archiviata. Nessuna acquisizione nel lotto A6.
