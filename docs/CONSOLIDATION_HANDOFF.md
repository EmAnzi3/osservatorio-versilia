# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 10 ottobre 2026

- Baseline main: #385 `9f83be4341dadef03edb37d951cdfbe68b0ba760`, mergiata dal proprietario. Lotto INVALSI concluso: Quick/Full locali e CI `38043017534` SUCCESS, deploy `38045981059` SUCCESS. Copertura baseline 188/225 effettivi, 133/181 sorgente, 37 residui.
- Catalogo effettivo: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-social-spending-adapters`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte alla revisione metodologica; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

Spesa sociale v35: due indicatori Istat, €/abitante e sette quote per area di utenza, 7/7 Comuni. Serie nominale inclusiva 2014–2022 con arrotondamento pubblico esplicito; benchmark Toscana/Italia solo 2022. Quote native solo 2022, zeri conservati; alias iniziale distinto da totale e summary €/abitante distinto dalle percentuali. Nessun pooling da denominatori ricostruiti o medie Versilia consolidate; trend/variazioni/anomalie/coppie non revisionate rifiutati. Metodo `docs/A6_SOCIAL_SPENDING_ADAPTERS.md`.

Test mirati PASS: sette indici correnti, nove celle storiche Camaiore, 49 quote e due benchmark fissi; replay distinto di 63 celle storiche e 14 gap comunali. Audit derivato: 190/225 effettivi, 135/181 sorgente, 35 residui. Suite 1.350/1.350 PASS (650 consultazioni/calcoli, 700 rifiuti), 58 collegamenti, 29 companion e 94 carichi descrittivi. Report `reports/a6-social-spending/`. Gate canonici e ricevute locali/CI da verificare nella PR prima del merge.

## Prossima azione

Concludere Quick canonico e verificare Full locale in clone freddo distinto e Quick→Full CI sullo stesso albero. Nessun merge/deploy automatico. Dopo merge manuale scegliere il successivo lotto dal residuo derivato. Revisione metodologica A6.4–A6.6 separata dal numero di adapter; A7 non avviata.

## Manutenzioni e monitor separati

Radar #377 incorporato nella baseline; nessuna modifica in A6. Monitor e snapshot mensile conservati. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Nessuna nuova acquisizione onerosa; RUNTS non acquisito, ACI/Eligendo da verificare con harvester pertinenti. #329 refresh ASIA/AGCOM, #306 diagnostica Radar e #117 watchdog fuori dal lotto.

**Definition of done:** il linguaggio naturale facilita l'accesso ai dati ma non diventa una fonte autonoma di numeri o interpretazioni.
