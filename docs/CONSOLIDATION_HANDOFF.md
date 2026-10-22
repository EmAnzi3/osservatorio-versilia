# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline verificata il 22 ottobre 2026 — #464

A6 DONE: 225/225 adapter, 3.727 casi indipendenti, 35 letture e due riepiloghi,
Atlante 20.325 unità locali native, 40 golden e Camaiore congelata. Nessuna
regressione dimostrata: non riaprire A6. A7 IN_PROGRESS. Matrice derivata da
contratti/catalogo e prove effettive: `A7_ACCESSIBILITY_AUDIT.md`. Le prove di
percorsi non certificano dimensioni intere. Nessuna promozione in navigazione.

#464 MERGED dal proprietario: main `ab9bba0f3fd27ed00ecb1b654f05ee9e93047fa0`,
albero `db28245edb2f0e3e4fdfa60ab19ea319bc537f92`, identico al candidato
remoto `d054d02c1d05169bcf09ec4f82715ae7dfeeb8b5`. Quick locale ordinario
exit 0 con cattura log parziale, esplicitamente documentata; Full ordinario
senza skip PASS con Quick ripetuto e log completo. CI Quick→Full effettivo
`39740805211`, job `119697288976` / `119721207314` SUCCESS; A3 `39740805119`,
job `119697287767` SUCCESS. Checkout dei tre job `be4d7cea39db494dabee91f9c5d23fcdd0a93898`,
albero identico. Attestazione completa nella PR, archivio
`A7_NATIVE_AGGREGATES_7681b13_evidenze.zip`, SHA256
`13238adbb9d70f2dd334a705e999b3d7ae3690f7b63d4d61e4a46210cd95ea7c`.

Pubblicazione verificata separatamente: Pages push `39755137239`, build
`119745120310` e deploy `119753351885` SUCCESS. Reporter `39757746846`, job
`119753959233` SUCCESS, checkout del merge `ab9bba0f`; integrità Chiedi con
asset/hash PASS, `ov-public-routes` / `ov-pages-live` SUCCESS. I Quick/Full
skipped del push di pubblicazione non sono nuovi gate della PR.
Nessun merge o deploy dell’assistente. Dossier editoriali (#443) e Radar
restano filoni separati; nessuna modifica alle altre PR.

#464 espone rapporti aggregati nativi su sette Comuni solo con `weighted_ratio`:
242 viste / 94 indicatori, 210 computed / 32 rifiuti. Totale runtime pubblico
41.993 richieste, 24.914 computed / 17.079 rifiuti, 104.234.277 byte gzip.
Misure di trasporto, non nuove prove numeriche indipendenti. Benchmark
Toscana/Italia #463 e capacità precedenti conservati. Metodo:
`A7_NATIVE_AGGREGATES.md`; atomicità: `A7_ATOMIC_RUNTIME_PACKAGE.md`.

## Incremento corrente — variazioni temporali native

Branch `feature/a7-native-changes`, base #464. A7.5.3 in corso: profilo opzionale
`changes` per le sole variazioni assolute, relative e in punti percentuali
ammesse dalle dichiarazioni. Una coppia primo/ultimo periodo della serie nativa
per Comune, mostrata prima del calcolo; nessun salto degli estremi mancanti,
periodo arbitrario, annualizzazione o modifica A6. Comparabilità e rifiuti
restano nel motore originale. Metodo: `A7_TEMPORAL_CHANGES.md`.

Completare misura combinata e matrice, preview/browser desktop/mobile,
Quick e Full locali ordinari e CI Quick→Full/A3 sul medesimo nuovo candidato.
PR Draft finché preview/browser non verificati. Gate ed evidenze finali nella PR;
nessun verde #464 trasferito. Nessun merge/deploy dell’assistente.

Chrome Headless Shell ufficiale 151.0.7922.34, Playwright 1.62.0, Lighthouse
13.4.1; cache Python separate. Solo Percorsi riproduce i due originali Leaflet
1.9.4 verificati SRI per il limite Unpkg, senza modifiche DOM/dati/golden/soglie;
Lighthouse non intercettato. CDN/WAN e telefono fisico non certificati.
Altre operazioni/dimensioni, incroci, export e rapporti restano aperti: A7 non
conclusa. Nessuna nuova acquisizione, backend o modello esterno.
