# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 12 ottobre 2026

- #422 mergiata e pubblicata dal proprietario: main `cdb953e923c002b248d29395a1e8b62d50e2824f`, albero `09fad950adc83b4c4226d9c6af4b15cb6ef23169`. v53, 224/225 effettivi e 166/181 sorgente; 3.543 PASS. CI Pages Quick→Full e A3 verificate verdi sul branch.
- Catalogo effettivo: 225 indicatori, 124 storici, 137 confronti; SHA `d9fea44f9cf3e56309e1193bf63b5cfe32bfbc3ba088860843db8d14b9c12278`, registro SHA `261304eb74262058ba42f38d0b4584a3038f184e3bc602ab8e0b5d9eb9d13d5c`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-economy-atlas-adapter`; A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte, A7 non avviata.
- Camaiore checkpoint `5aaf159870912eb49bffbd044963549bfb920150`, dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi protetti.

## Lotto in verifica

v54 Atlante: ultimo carrier, solo effettivo. 2.457 viste esplicite: totali territoriali, 1.228 codici diretti attivi 2014–2025 e artigiani solo 2025. Confronto/rango, serie attive consultabili; null distinti da zero e copertura parziale con consenso. Registro Imprese diverso da ASIA/addetti; classificazione ATECO2007/2022 distinta da ATECO2025. Nessuna somma gerarchica, quota/LQ non riconciliata, variazione/trend, benchmark municipale, pooling, anomalia o coppia inferita.

Divergenza esplicita: carrier pubblico292 deriva dalle sole righe dirette di divisione, contro 20.325 nei totali territoriali congelati. `total` implicito rifiutato, scelta esplicita necessaria; dati/UI non riscritti. Correzione del carrier e riconciliazione delle gerarchie da affrontare prima della chiusura metodologica A6. Metodo `docs/A6_ECONOMY_ATLAS_ADAPTERS.md`.

119 ancore fisse, replay separato 111.832 celle comunali compatte (56.238 null), file verificati dopo cache e cache immutabile. 184 domande nuove, tutte le 3.543 precedenti conservate. Report rigenerati `reports/a6-economy-atlas/`; 3.727/3.727 PASS (2.033 calcoli, 1.694 rifiuti). Copertura derivata 225/225 effettivi, 166/181 sorgente; nessun residuo di carrier, restano limiti delle operazioni e revisione A6.5–A6.6.

## Prossima azione

Quick canonico locale completo su clone pulito prima del push/apertura PR. Full locale completo sequenziale e CI Quick→Full/A3 sullo stesso albero prima della prontezza. Merge del proprietario. Browser locali mai paralleli. Dopo il merge: riconciliare il carrier Atlante e completare revisione metodologica/letture A6; A7 solo dopo chiusura A6.

## Manutenzioni e monitor separati

#407: SISBON 154 codici (58 attivi/96 chiusi), MIMIT puntuale 10 ottobre/storico fino a settembre, ARS timeout 120 secondi; ZIP 255 del proprietario 2015–2025 invariato. #411: RUNTS Excel 11 ottobre verificato (SHA invariato), 465 sedi/residenti 1 gennaio 2026; AGCOM consistenze 6 luglio/revisione 14 luglio corrette su input congelati, nessun CSV acquisito. #413: refresh AGCOM soltanto dispatch/comando esplicito, test offline preservati. Radar #402, PNRR 25 settembre, #338 mensile, #329 ASIA/AGCOM e #117 watchdog separati; #306 archiviata. Nessuna acquisizione nel lotto A6.
