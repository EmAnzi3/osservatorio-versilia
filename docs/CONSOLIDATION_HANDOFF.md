# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 10 ottobre 2026

- Baseline main: #382 `5ba9efa6d8008db04ee54fcb0fff9ba5dfc1e14a`, mergiata dal proprietario alle 05:35:20 UTC. Lotto regionale concluso: Quick/Full CI `38002722209` SUCCESS sul head `a63befb0e27b2b41556746148bfd7024e677f516`; Full locale e prove di identità documentati nella #382. Copertura baseline 181/225 effettivi, 130/181 sorgente, 44 residui.
- Catalogo effettivo: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-library-adapters`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte alla revisione metodologica; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

Biblioteche v33: tre carrier pubblicati regionali, 2024 con copertura 5/7. Massarosa valori non alimentati e Stazzema assente conservati distinti; nessuna imputazione, riporto dell’ultimo dato o ponderazione. Indici arrotondati non sostituiti con rapporti da sedi. Prestiti/utenti 1998–2024 con null, ore solo 2022–2024, benchmark Toscana corrente. Confronto/rango/serie/gap; variazioni/trend/anomalie/coppie non revisionate e pooling rifiutati. Metodo `docs/A6_LIBRARY_ADAPTERS.md`.

Test mirati PASS: 21 celle correnti, tre benchmark, 57 celle storiche fisse Massarosa; replay separato di 399 celle congelate incluse null. Audit derivato: 184/225 effettivi, 133/181 sorgente, 41 residui. Suite 1.111/1.111 PASS (485 consultazioni/calcoli e 626 rifiuti), 58 collegamenti, 29 companion e 87 carichi descrittivi. Report `reports/a6-library/`. Gate canonici e ricevute locali/CI da verificare nella PR prima del merge.

## Prossima azione

Concludere Quick canonico e verificare Full locale in clone freddo distinto e Quick→Full CI sullo stesso albero. Nessun merge/deploy automatico. Dopo merge manuale scegliere il successivo lotto dal residuo derivato. Revisione metodologica A6.4–A6.6 separata dal numero di adapter; A7 non avviata.

## Manutenzioni e monitor separati

Radar #377 incorporato nella baseline; nessuna modifica in A6. Monitor e snapshot mensile conservati. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Nessuna nuova acquisizione onerosa; RUNTS non acquisito, ACI/Eligendo da verificare con harvester pertinenti. #329 refresh ASIA/AGCOM, #306 diagnostica Radar e #117 watchdog fuori dal lotto.
