# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 10 ottobre 2026

- Baseline #388 mergiata dal proprietario, main `2e80420c5900867aea2fe45f430c440ad196173e`, albero `4ccc08864261c61483f9ef554dbc2e66a7e11709`. Quick/Full locali e CI `38059711386` SUCCESS, audit A3 `38059711293` SUCCESS; deploy post-merge `38062949456` SUCCESS. Baseline 192/225 adapter effettivi, 136/181 sorgente, 33 residui.
- Catalogo effettivo invariato: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-connectivity-adapters`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte alla revisione metodologica; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

FTTH AGCOM v37: quattro carrier al riferimento 31 dicembre 2025. Percentuali DESI/entro 20 metri 7/7, conteggi raggiunte/non raggiunte 6/7: Forte dei Marmi zero percentuale ma conteggi mancanti, nessuna ricostruzione. Denominatore famiglie AGCOM, fotografia distinta dalla pubblicazione/acquisizione 2026. Confronto/rango, scostamenti Toscana/Italia solo percentuali. Aggregati pubblici riconciliati: percentuali arrotondate ponderate, totali assoluti parziali distinti. Snapshot A3 benchmark con run/artifact, nessuna falsa prova di replay del pannello nazionale non congelato. Nessuno storico, pooling o coppia non revisionata. Metodo `docs/A6_CONNECTIVITY_ADAPTERS.md`.

Test mirati: 28 celle pubbliche, 35 native, 28 gap, quattro aggregati e guardie su mancante/zero/provenienza/mutazioni. Suite 1.512 PASS (740 consultazioni/calcoli, 772 rifiuti), tutte le 1.402 precedenti conservate. Report preliminari `reports/a6-connectivity/` sul catalogo effettivo #388; nuove build fredde devono riconciliarne SHA e conteggi. Copertura derivata 196/225 effettivi, 140/181 sorgente, 29 residui; 58 collegamenti, 29 companion e 101 carichi descrittivi. Gate da verificare nel candidato.

## Prossima azione

Quick canonico locale prima del push; Full locale comprensivo di Quick in clone freddo distinto e CI Quick→Full sullo stesso albero prima della prontezza al merge. Log e ricevute finali complete richiesti. Nessun merge/deploy automatico. Dopo merge manuale scegliere il lotto dal residuo derivato; revisione metodologica A6.4–A6.6 distinta dal conteggio degli adapter.

## Manutenzioni e monitor separati

Radar #377 incorporato; nessuna modifica A6. Monitor e snapshot mensile conservati. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Nessuna nuova acquisizione onerosa; RUNTS non acquisito, ACI/Eligendo da verificare con harvester pertinenti. #329 refresh ASIA/AGCOM, #306 diagnostica Radar e #117 watchdog fuori dal lotto.

**Definition of done:** il linguaggio naturale facilita l’accesso ai dati ma non diventa una fonte autonoma di numeri o interpretazioni.
