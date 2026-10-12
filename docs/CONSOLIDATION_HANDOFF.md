# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 12 ottobre 2026

- #419 mergiata dal proprietario: main `a832b6c0bd5d47b8ac2eae5cb434aef4da8807f1`, albero `c08cc164f4bb593d5cb442fddf1e14d842feeffb`; v52 OMI/energia integrati, 223/225 effettivi, 165/181 sorgente, due residui, 3.502 PASS. Quick/Full locali e CI Quick→Full/A3 completi verdi sullo stesso albero.
- Catalogo effettivo: 225 indicatori, 124 storici, 137 confronti, SHA `d9fea44f9cf3e56309e1193bf63b5cfe32bfbc3ba088860843db8d14b9c12278`; registro SHA `261304eb74262058ba42f38d0b4584a3038f184e3bc602ab8e0b5d9eb9d13d5c`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-outside-municipality-adapter`; A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte, A7 non avviata.
- Camaiore checkpoint `5aaf159870912eb49bffbd044963549bfb920150`, dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi protetti.

## Lotto in verifica

v53: outsideMunicipality, quota censuaria dei lavoratori residenti fuori Comune nel 2021, una vista 7/7, confronto/rango. Universo distinto dai pendolari abituali della matrice per lavoro: Massarosa 62,9% diverso dal complemento dell’autocontenimento 71,384615…%. Solo replay del catalogo, nessun conteggio/componenti originali ricostruiti. Media dei Comuni diversa da quota aggregata dei lavoratori; uscite dal Comune diverse da uscite dalla Versilia. Pooling, storia, benchmark, anomalie e coppie non revisionate rifiutati. Metodo `docs/A6_OUTSIDE_MUNICIPALITY_ADAPTERS.md`.

Sette riferimenti fissi, ordine/puntatori, controesempio e prove ostili dopo cache. 41 domande nuove, 3.501 precedenti invariate; un caso legacy conserva ID/query e aggiorna aspettativa alla consultazione. Suite 3.543/3.543 PASS (1.904 calcoli, 1.639 rifiuti); copertura derivata 224/225 effettivi e 166/181 sorgente, un residuo. Report rigenerati `reports/a6-outside-municipality/`.

## Prossima azione

Quick canonico locale completo su clone pulito prima del push/apertura PR. Full locale completo sequenziale e CI Quick→Full/A3 sullo stesso albero prima della prontezza. Merge del proprietario. Browser locali mai paralleli. Unico residuo atteso economyActivityAtlas; chiusura metodologica A6 distinta dalla copertura degli adapter.

## Manutenzioni e monitor separati

#407: SISBON 154 codici (58 attivi/96 chiusi), MIMIT puntuale 10 ottobre/storico fino a settembre, ARS timeout 120 secondi; ZIP 255 del proprietario 2015–2025 invariato. #411: RUNTS Excel 11 ottobre verificato (SHA invariato), 465 sedi/residenti 1 gennaio 2026; AGCOM consistenze 6 luglio/revisione 14 luglio corrette su input congelati, nessun CSV acquisito. #413: refresh AGCOM soltanto dispatch/comando esplicito, test offline preservati. Radar #402, PNRR 25 settembre, #338 mensile, #329 ASIA/AGCOM e #117 watchdog separati; #306 archiviata. Nessuna acquisizione nel lotto A6.
