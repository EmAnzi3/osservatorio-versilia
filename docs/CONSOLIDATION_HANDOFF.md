# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 10 ottobre 2026

- Baseline #392 Radar mergiata manualmente: main `987c919b29a02b1c74a4f7abee3655df32ef4e88`, albero `3100a9b9c937306b901d32c6385fef28c2042815`. Lotto A6 stradale #391 pubblicato: 198/225 effettivi, 142/181 sorgente, 27 residui e 1.710 domande PASS; Quick/Full locali e CI verdi, evidenze archiviate.
- Catalogo effettivo invariato: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, PR #393, branch `feat/a6-vehicle-adapters`. A6.1–A6.3 pubblicate, A6.4 parziale; A6.5–A6.6 aperte alla revisione metodologica, A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

Parco autovetture ACI v39: `motorization` e `pollutingCars`, 7/7. `total` conserva un decimale pubblico, `nativeRatio` espone rapporti da conteggi interi con provenienza distinta e consente pooling delle somme su Comuni disgiunti. Autovetture 2024/residenti 1 gennaio 2026 per motorizzazione; Euro 0–3/tutte le autovetture 2024 per quota. Benchmark Toscana/Italia con la stessa base. Quota Versilia pubblicata pondera percentuali arrotondate e resta distinta dal rapporto nativo. Null Euro conservati, classi indefinite incluse nel totale; niente storico, trend, anomalie o coppie non revisionate. Metodo `docs/A6_VEHICLE_ADAPTERS.md`.

Test mirati PASS: 14 celle pubbliche, 14 rapporti nativi, 21 componenti fisse, 56 gap e due rapporti aggregati; replay dal workbook congelato di 7.997 righe di localizzazione ACI. Suite 1.850 PASS (970 letture/calcoli, 880 rifiuti), tutte le 1.710 precedenti invariate. Copertura derivata 200/225 effettivi, 144/181 sorgente, 25 residui. Report preliminari `reports/a6-vehicles/` sul catalogo effettivo #391, invariato nella #392; 58 collegamenti, 29 companion e 109 carichi descrittivi. Nuove build fredde devono riconciliare SHA e conteggi; gate canonici ancora da concludere. Primo Quick locale GREEN; CI ha rilevato dipendenza opzionale openpyxl assente, rimossa dal replay usando soltanto ZIP/XML stdlib, verificato con `python -S`. Nessuna modifica workflow/dependency o asserzione; ripetere Quick prima del push e Full completo sul candidato finale.

## Prossima azione

Quick canonico locale concluso prima di qualsiasi push. Full locale completo in clone freddo separato e CI Quick→Full sul medesimo albero prima della prontezza al merge. Log finali completi e ricevute verificati. Nessun merge/deploy automatico. Dopo merge manuale scegliere il lotto dal residuo derivato; chiusura metodologica A6 distinta dal conteggio adapter.

## Manutenzioni e monitor separati

Radar #392 incorporato byte per byte; lista compile condivisa unisce i moduli Radar e A6. Quick corretto sulla vecchia base verde; Full interrotto come obsoleto dopo il merge #392. Ripetere entrambi sul nuovo albero prima della prontezza. Monitor e snapshot mensile conservati. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Nessuna acquisizione onerosa; RUNTS non acquisito. #329 refresh ASIA/AGCOM, #306 diagnostica Radar e #117 watchdog fuori dal lotto.

**Definition of done:** il linguaggio naturale facilita l'accesso ai dati ma non diventa una fonte autonoma di numeri o interpretazioni.
