# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 10 ottobre 2026

- Baseline main: #386 `1f4a970a3903097ea700248f41b48f9903ae23fb`, mergiata dal proprietario. CI `38050147410` e audit A3 SUCCESS, deploy `38057001822` e live status `38057733682` SUCCESS. Baseline 190/225 effettivi, 135/181 sorgente e 35 residui. Quick locale finale verde; il precedente Full locale finale ha log fino a Percorsi mobile ma ricevuta incompleta dopo interruzione della sessione: non dichiarato verde né usato per certificare il nuovo candidato.
- Catalogo effettivo: 225 indicatori, 124 storici, 137 confronti, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-health-facilities-adapters`. A6.1–A6.3 pubblicate, A6.4 parziale, A6.5–A6.6 aperte alla revisione metodologica; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

Presìdi Salute v36: farmacie e RSA accreditate, 7/7 Comuni, snapshot completo 31 dicembre 2025. Farmacie pubbliche a due decimali / residenti POSAS stimati 1 gennaio 2026; benchmark Toscana/Italia con stesso perimetro e precisione distinta. RSA conteggi esatti, deduplicazione regionale 337→336 e riconciliazione locale; totale regionale non usato come tasso comunale. Ospedali esclusi per supporto nativo congelato insufficiente. Nessun pooling pubblico, storico singleton, temporalità, anomalie o coppia non revisionata. Metodo `docs/A6_HEALTH_FACILITIES_ADAPTERS.md`.

Test mirati PASS: 14 celle fisse, sette conteggi/denominatori farmacie indipendenti, 14 gap e guardie su zeri/provenienza/mutazioni. Audit derivato 192/225 effettivi, 136/181 sorgente, 33 residui. Suite 1.402/1.402 PASS (680 consultazioni/calcoli, 722 rifiuti), tutte le 1.350 precedenti conservate; 58 collegamenti, 29 companion e 97 carichi descrittivi. Report `reports/a6-health-facilities/`. Audit preliminare sul catalogo effettivo verificato della #386; build candidate fredde devono riconciliarne SHA e conteggi.

## Prossima azione

Quick canonico locale prima del push; Full locale comprensivo di Quick in clone freddo distinto e CI Quick→Full sullo stesso albero prima della prontezza al merge. Conservare log e ricevute finali complete: una sessione interrotta non certifica un gate. Nessun merge/deploy automatico. Dopo merge manuale scegliere il successivo lotto dal residuo derivato. Revisione metodologica A6.4–A6.6 separata dal numero di adapter; A7 non avviata.

## Manutenzioni e monitor separati

Radar #377 incorporato; nessuna modifica A6. Monitor e snapshot mensile conservati. PNRR fotografia 25 settembre 2026, carburanti puntuali 3 ottobre e mensili fino a settembre. Nessuna nuova acquisizione onerosa; RUNTS non acquisito, ACI/Eligendo da verificare con harvester pertinenti. #329 refresh ASIA/AGCOM, #306 diagnostica Radar e #117 watchdog fuori dal lotto.

**Definition of done:** il linguaggio naturale facilita l’accesso ai dati ma non diventa una fonte autonoma di numeri o interpretazioni.
