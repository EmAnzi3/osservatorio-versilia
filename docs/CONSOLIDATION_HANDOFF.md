# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 10 ottobre 2026

- Baseline corrente #389 Radar dopo #390 A6, entrambe mergiate dal proprietario: main `ead0153b6371de2424849cb73bd896d58a84095a`, albero `28c571616396224984794e737c180e82ae04c0c4`. Le 14 modifiche Radar sono riportate byte per byte, fuori dal diff A6; il primo Quick stradale sulla sola #390 era GREEN e viene ripetuto sulla nuova base. Gate della #390: Quick/Full locali GREEN, CI canonica `38067222525` e audit A3 `38067222546` SUCCESS. Deploy post-merge `38070404725` e live-status `38071113161` SUCCESS. Copertura 196/225 effettivi, 140/181 sorgente, 29 residui; suite 1.512 PASS. Evidenze generate FTTH archiviate con log completi, ricevute e diagnosi precedenti.
- Catalogo effettivo invariato: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-road-safety-adapters`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte alla revisione metodologica; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

Sicurezza stradale e proventi v38: `roadSafety` in quattro letture con denominatori distinti e alias Incidenti; `roadFinesPerResident` contabile nominale. Riferimento 2024; serie incidenti/mortalità/lesività 2014–2024, feriti 2020–2024, proventi 2021–2024. Stazzema 2017 mancante nel nativo e omesso nel pubblico: null esplicito, nessuno zero o interpolazione. Snapshot Istat parsed con hash workbook; feriti dal carrier canonico legacy con impronta e limite distinto, nessun replay raw. Gap Toscana/Italia 2024 per tre misure e proventi, feriti esclusi. Medie comunali descrittive, nessun pooling, analisi temporale/coppia non revisionata o interpretazione causale dei proventi. Metodo `docs/A6_ROAD_ADAPTERS.md`.

Test mirati: 35 celle correnti, sette alias, 35 ancore storiche, 56 gap, cinque medie; replay distinto 294 celle incluse tre null native e 35 feriti legacy. Suite 1.710 PASS (876 letture/calcoli, 834 rifiuti), tutte le 1.512 precedenti conservate. Report preliminari `reports/a6-road/` sul catalogo effettivo #390; nuove build fredde devono riconciliarne SHA e conteggi. Copertura derivata attesa 198/225 effettivi, 142/181 sorgente, 27 residui; 58 collegamenti, 29 companion, 105 carichi descrittivi. Gate da verificare nel candidato.

## Prossima azione

Quick canonico locale prima del push; Full locale comprensivo di Quick in clone freddo distinto e CI Quick→Full sullo stesso albero prima della prontezza al merge. Log e ricevute finali completi richiesti. Nessun merge/deploy automatico. Dopo merge manuale scegliere il lotto dal residuo derivato; revisione metodologica A6.4–A6.6 distinta dal conteggio degli adapter.

## Manutenzioni e monitor separati

Radar #389 incorporato, nessuna modifica A6. Monitor e snapshot mensile conservati. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Nessuna acquisizione onerosa; RUNTS non acquisito, ACI/Eligendo da verificare con harvester pertinenti. #329 refresh ASIA/AGCOM, #306 diagnostica Radar e #117 watchdog fuori dal lotto.

**Definition of done:** il linguaggio naturale facilita l’accesso ai dati ma non diventa una fonte autonoma di numeri o interpretazioni.
