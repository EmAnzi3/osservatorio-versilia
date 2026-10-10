# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 10 ottobre 2026

- Baseline main: #384 `d9c84b58e727fa141c0c1391b7399ad9fc59b1f3`, mergiata dal proprietario. Lotto biblioteche concluso: Quick/Full locale e CI `38037908200` SUCCESS, deploy `38040242645` SUCCESS. Copertura baseline 184/225 effettivi, 133/181 sorgente, 41 residui.
- Catalogo effettivo: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-invalsi-adapters`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte alla revisione metodologica; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

INVALSI v34: quattro carrier, 32 viste grado/prova e 46 categorie di competenza correnti. Universo Comune plesso, aggregazione ufficiale Totale, anni scolastici esatti. Null e interruzione 2019–20 conservati; grado 10 senza 2020–21. Confronto/rango/serie dei valori pubblicati e gap Toscana/Italia; livelli solo correnti. Nessun pooling da partecipazione/copertura, variazioni/trend/anomalie/coppie non revisionate rifiutati. Provenienza ricostruibile dai cinque frammenti reali congelati. Metodo `docs/A6_INVALSI_ADAPTERS.md`.

Test mirati PASS: 28 celle correnti, 21 storiche, otto benchmark e due livelli QCER fissi; replay separato 1.442 celle storiche, 412 benchmark e 322 categorie correnti incluse null. Audit derivato: 188/225 effettivi, 133/181 sorgente, 37 residui. Suite 1.295/1.295 PASS (631 consultazioni/calcoli e 664 rifiuti), 58 collegamenti, 29 companion e 91 carichi descrittivi. Report `reports/a6-invalsi/`. Gate canonici e ricevute locali/CI da verificare nella PR prima del merge.

## Prossima azione

Concludere Quick canonico e verificare Full locale in clone freddo distinto e Quick→Full CI sullo stesso albero. Nessun merge/deploy automatico. Dopo merge manuale scegliere il successivo lotto dal residuo derivato. Revisione metodologica A6.4–A6.6 separata dal numero di adapter; A7 non avviata.

## Manutenzioni e monitor separati

Radar #377 incorporato nella baseline; nessuna modifica in A6. Monitor e snapshot mensile conservati. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Nessuna nuova acquisizione onerosa; RUNTS non acquisito, ACI/Eligendo da verificare con harvester pertinenti. #329 refresh ASIA/AGCOM, #306 diagnostica Radar e #117 watchdog fuori dal lotto.
