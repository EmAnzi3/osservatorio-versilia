# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline verificata il 21 ottobre 2026

- #459 MERGED dal proprietario: main `cf5a9b97f92f8c3b82d7f9b23e81ce620667b3b4`, albero `f2f896a13b54c2ce7246219ba7066cd990e65a2d`, identico alla head verificata `70bd2eae8c3b3b9e99564d93dce1abc9921c7d02`. #451/#453/#454/#455/#457 risultano mergiate con la sequenza cumulativa.
- Gate #459 sul medesimo albero: Quick locale ordinario PASS (`bfae22588587f06eeaf395463323564f955b17fe0315429a8fb579db0daccbc0`); Full locale ordinario senza skip PASS (`2f756bda5a10c7f0e7a9a15fa473d0e7e401b328235b84b51438c9528e28de93`); CI Quick→Full effettivo `39579374567`, job `119152879702`/`119168383392` SUCCESS; A3 `39579374657`, job `119152877141` SUCCESS. Checkout CI `4e328f4b98e024835614b6de285a554b190d841a`, albero identico. 40 golden e 582 controlli browser PASS.
- Pubblicazione effettiva #459: run Pages `39612898406`, build `119266192566` e deploy `119280228309` SUCCESS. Il reporter `39617730098` ha verificato route/asset/hash live, ma al primo tentativo ha erroneamente pubblicato failure per una conclusione job `None`. Rilanciato soltanto il reporter: job `119286143098` SUCCESS, controllo live PASS, `ov-public-routes` e `ov-pages-live` SUCCESS. Nessun nuovo deploy dell’assistente.
- Evidenze #459: `A7_PR459_70bd2ea_evidenze.zip`, SHA256 `840266a8dae69a3e10aa285096e6bcc59f2781f16284e0a5cf18237623dde5e4`. Log locali/CI e tentativi distinti dai PASS; non comprende il successivo deploy/reporter, documentati nei run sopra.
- A6 DONE: 225/225 adapter, 3.727 casi indipendenti (2.033 calcoli / 1.694 rifiuti), 35 letture e due riepiloghi, Atlante 20.325 unità locali native, 40 golden e Camaiore congelata. Nessuna regressione dimostrata: non riaprire A6.
- #443 resta un filone editoriale aperto con conflitti, non un duplicato dell’esploratore. #338 conserva un rapporto storico; #407 è mergiata. #117 è un PoC Cloudflare Draft con stato del Worker da verificare. Nessuna modifica a queste PR o a Radar in questo incremento.

## A7 IN_PROGRESS — accessibilità e prodotto

La matrice schema 3 deriva acquisizione, capacità native, trasporto e UI dai
contratti, dal catalogo e dall’artifact verificato. Ultima misura: 746 riferimenti
acquisiti risolti; percorsi richiesti interamente provati per 275 coppie nel
workbench e 187 nel trasporto, non intere dimensioni certificate. Le 88 coppie
con prove native complete ma non statiche comprendono 49 benchmark e 39 dettagli
territoriali. Le 442 coppie senza prova nativa nel perimetro non sono dati assenti.
Metodo: `docs/A7_ACCESSIBILITY_AUDIT.md`.

L’esploratore generale è integrato e pubblicato, senza aumento della navigazione.
Tema, indicatore, vista, operazione e Comune derivano dal catalogo. I tre profili
nativi coprono osservazione/lookup, confronto dei sette Comuni e serie comunale
ove ammesse. Nessun periodo arbitrario, aggregato generico, ranking aggiuntivo o
associazione inferita. Risposte/rifiuti A6, fonti, periodi, consenso e revoca
preservati. La tabella mobile mantiene valori leggibili e scorrimento da tastiera.

225 indicatori / 3.359 viste; 37.880 richieste, 21.283 computed / 16.597 rifiuti,
100.804.953 byte gzip: misura di trasporto, non nuovo corpus numerico indipendente.
Manifest `f554516cb141788b6612d7ed8229351771834d228e16189221b552e089282fe3`.
Pagina/grafo in staging, ancora indipendente, artifact Pages unico e fallimenti
d’integrità/budget/disponibilità senza fallback numerici. Metodo:
`docs/A7_ATOMIC_RUNTIME_PACKAGE.md`, `docs/A7_GUIDED_EXPLORER_PREVIEW.md`,
`docs/A7_PUBLIC_EXPLORER_INTEGRATION.md`.

## Baseline #462 e incremento corrente — benchmark nella UI

#462 MERGED dal proprietario: main `c348ce5541c7bf21e771a5baa309d417bf0017fa`,
albero `a26f7ba228c5330047ffdc62f5d0717994a9809b`, identico al candidato
attestato `76cebc7c289633ce8b20fa0e784bcd55ca40f3e1`.
Quick locale ordinario PASS (`80d68ccb3e7c290f4a8c35feaf4ef6aed4d56038009256fcda748883510051ed`),
Full locale ordinario senza skip PASS (`87f36da65c8d1207eac0f68c1b239c1f905771f58fc05f876e9849d472be6662`).
CI Quick→Full effettivo `39645881405`, job `119381203290` / `119411459504`
SUCCESS; A3 `39645881435`, job `119381200112` SUCCESS. Checkout CI
`1069f3abd2bd8553579f3e6defd9ba402be0333a`, stesso albero. Evidenze finali
`A7_PR462_76cebc7_evidenze.zip`, SHA256
`b652503adf7fa43bbf1c4e07321630a2643da392a62d7dcffdfa0912c0e2c9b6`.
Lighthouse CI passa con l’eccezione preesistente Wikimedia esplicita nel log:
best-practices grezzi 100/77/77/100, nessuna modifica a soglie o eccezioni.
Pubblicazione #462 verificata: Pages `39660779681`, build `119432880221` e
deploy `119446930204` SUCCESS. Reporter `39664875469`, job `119447145831`
SUCCESS, checkout del merge; integrità live PASS e `ov-public-routes` /
`ov-pages-live` SUCCESS. Descrittore live identico a quello dell’albero attestato:
grafo `32079418788605d147f0d79003201933d6ad8ab566b952330f034241eb255a54`,
manifest `fcbe6d7deca22cc78a1f7b58f76d4ca0bec6088b8534436ed1677acd62543317`.
Il prodotto pubblico conserva i tre profili precedenti: nessun benchmark UI
abilitato dalla sola #462. Nessun merge o deploy dell’assistente.
#461 era già pubblicata: Pages `39637327110` e reporter `39641519892` SUCCESS,
validazione live PASS sul merge `bed825e02c36b566a94e8601e9d87da7c7c6e1cf`.

Il profilo opzionale della #462 copre 112 indicatori / 353 viste, 3.871 richieste
Toscana/Italia (3.421 computed / 450 rifiuti originali). I 49 percorsi benchmark
acquisiti con prova nativa completa risultano raggiungibili anche nel trasporto
isolato; non sono intere dimensioni certificate o nuove prove numeriche indipendenti.
Metodo: `docs/A7_SELECTIVE_BENCHMARKS.md`. I conteggi della matrice iniziale sopra
si riferiscono ai tre profili pubblici precedenti: i diversi perimetri di probe
non vanno confrontati come una regressione.

Branch `feature/a7-benchmark-ui`: A7.5.2, selettore esplicito del riferimento,
valore comunale, valore Toscana/Italia e scostamento già prodotti da A6. Nessuna
aritmetica nel browser, nessun benchmark Versilia, periodo arbitrario o consenso
aggiunto alla richiesta. Per le percentuali, scostamento in punti percentuali.
Risultati e consenso revocati anche cambiando riferimento; rifiuti originali
conservati. Riferimenti disponibili derivati dalla dichiarazione della vista.
La build pubblica candidata include esplicitamente i tre profili più benchmark;
i default del generatore restano invariati, ranking non aggiunto.
Metodo e limiti: `docs/A7_BENCHMARK_INTERFACE.md`.

La roadmap A7 distingue requisiti trasversali e passi di prodotto A7.5.1–A7.5.6.
Altre dimensioni/operazioni, incroci guidati, export e rapporti sono successivi,
non funzionalità dichiarate completate. Dossier e Radar restano separati.

## Ambiente e prossima azione

Chrome Headless Shell ufficiale 151.0.7922.34, Playwright 1.62.0, Lighthouse
canonico 13.4.1; cache Python separate per modalità. Solo Percorsi riproduce
i due originali Leaflet 1.9.4 verificati SRI per il limite locale Unpkg, senza
modifica a DOM/dati/golden/soglie. Lighthouse non intercettato. CDN/WAN e telefono
fisico non certificati.

Completare preview e browser desktop/mobile, misura combinata e matrice, poi
Quick/Full locali ordinari e CI Quick→Full/A3 sul medesimo nuovo candidato.
PR Draft finché preview/browser non verificati. Gate ed evidenze finali nella PR:
nessun verde della #462 viene trasferito. Nessun merge/deploy dell’assistente.
