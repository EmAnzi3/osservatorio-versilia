# Consolidamento Osservatorio Versilia — handoff operativo

## Main corrente — #468 integrata dal proprietario

Main `4085e198f1a9a0c3b812d4f2c7004f60cfcc25f3`, albero
`8111ed42bd125a0b272507baaeedd3415541c57c`: merge #468 dopo #466.
Il budget Radar (build 60 minuti, job 105; stesso contratto nel rehearsal shadow)
resta quello approvato nella PR #468, con i suoi gate attestati separatamente.
Nessun refresh produttivo riuscito è attestato qui. Residui Radar: coda/rumore
documentale, BELLA Lì!/GRANFEST, ANCI/MIM/GSE; filone separato da A7.
Il riallineamento A7 conserva integralmente workflow, contratto e test #468;
risolve il solo conflitto nell’handoff, mantenendo la baseline A7 #466 qui sotto.
Quick/Full locali e CI Quick→Full/A3 vanno attestati sul nuovo albero integrato:
i verdi del candidato precedente non sostituiscono questi gate.

## Baseline verificata il 22 ottobre 2026 — #466

A6 DONE: 225/225 adapter, 3.727 casi indipendenti, 35 letture e due riepiloghi,
Atlante 20.325 unità locali native, 40 golden e Camaiore congelata. Nessuna
regressione dimostrata: non riaprire A6. A7 IN_PROGRESS. Matrice derivata da
contratti/catalogo e prove effettive: `A7_ACCESSIBILITY_AUDIT.md`. Le prove di
percorsi non certificano dimensioni intere. Nessuna promozione in navigazione.

#466 MERGED dal proprietario: main `cb05e95d7d637ea01c3c3cfd6eab51594335d028`,
albero `3f4b8111055f697816e99993f1feecbea1e95132`, identico al candidato
remoto `fa1d3223b506ef6cc1c314bbf7f9f542696946ed`. Quick e Full locali
ordinari senza skip PASS. CI Quick→Full effettivo `39767472109`, job
`119786384909` / `119813990113` SUCCESS; A3 `39767472142`, job `119786384886`
SUCCESS. Checkout effettivo dei tre job `b14acb2e63e0744110d500d6d3c089f092f62547`,
albero identico. 40 baseline / 582 controlli browser PASS. Attestazione nella PR;
archivio `A7_TEMPORAL_CHANGES_97c8d7d_evidenze.zip`, SHA256
`c2516d983de0e0a93104bf4cd35e495a5939d24e5dc96b5c3cb6f714677c7752`.

Pubblicazione verificata separatamente: Pages push `39818801445`, build
`119964229390` e deploy `119977667709` SUCCESS. Reporter `39822722032`, job
`119977913249` SUCCESS: checkout del merge `cb05e95d`, integrità Chiedi con
asset/hash PASS, `ov-public-routes` / `ov-pages-live` SUCCESS. I Quick/Full
skipped del push non sono nuovi gate della PR. Nessun merge/deploy dell’assistente.
Radar ha un timeout nel refresh separato; non è un fallimento del deploy A7.
Dossier editoriali (#443) e Radar restano separati; nessuna modifica alle altre PR.

#466 espone variazioni native fra estremi per Comune dove dichiarate:
3.780 richieste, 1.836 computed / 1.944 rifiuti. Totale runtime pubblico
45.773 richieste, 26.750 computed / 19.023 rifiuti, 105.527.018 byte gzip.
Misure di trasporto, non nuove prove numeriche indipendenti. Benchmark e rapporti
precedenti conservati. Metodo: `A7_TEMPORAL_CHANGES.md`; atomicità:
`A7_ATOMIC_RUNTIME_PACKAGE.md`. Matrice: 9.411 capacità preparate; 4.577 dichiarate
non materializzate, di cui 3.336 `rank`, 202 `trend`, 515 `correlation`,
515 `anomaly`, 9 `benchmark_gap`. Nessuna promessa di interrogabilità universale.

## Incremento corrente — ordine numerico descrittivo

Branch `feature/a7-descriptive-order`, base main #468 (baseline prodotto A7 #466). A7.5.3 in corso: attivazione
pubblica esplicita del profilo opzionale `ranking` già esistente, soltanto sulle
viste che dichiarano `rank`, sui sette Comuni al riferimento nativo. Posizioni e
pari merito originali, valori/unità/periodi/fonti; nessun ricalcolo o giudizio
amministrativo. Rifiuti senza posizioni sostitutive. Metodo:
`A7_DESCRIPTIVE_ORDER.md`. Ricevuta UI v5; default invariati.

Completare misura combinata e matrice, preview/browser desktop/mobile,
Quick e Full locali ordinari e CI Quick→Full/A3 sul medesimo nuovo candidato.
PR Draft finché preview/browser non verificati. Gate ed evidenze finali nella PR;
nessun verde #466 trasferito. Nessun merge/deploy dell’assistente.

Chrome Headless Shell ufficiale 151.0.7922.34, Playwright 1.62.0, Lighthouse
13.4.1; cache Python separate. Solo Percorsi riproduce i due originali Leaflet
1.9.4 verificati SRI per il limite Unpkg, senza modifiche DOM/dati/golden/soglie;
Lighthouse non intercettato. CDN/WAN e telefono fisico non certificati.
Altre operazioni/dimensioni, incroci, export e rapporti restano aperti: A7 non
conclusa. Nessuna nuova acquisizione, backend o modello esterno.
