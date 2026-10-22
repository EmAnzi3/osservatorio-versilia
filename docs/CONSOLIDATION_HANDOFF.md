# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline verificata il 22 ottobre 2026 — #463

A6 DONE: 225/225 adapter, 3.727 casi indipendenti (2.033 calcoli / 1.694 rifiuti),
35 letture e due riepiloghi, Atlante 20.325 unità locali native, 40 golden e
Camaiore congelata. Nessuna regressione dimostrata: non riaprire A6.
La matrice schema 3 deriva acquisizione, capacità native, trasporto e UI dai
contratti, dal catalogo e dall’artifact verificato: `A7_ACCESSIBILITY_AUDIT.md`.
Le prove di accesso a percorsi non certificano intere dimensioni.
L’esploratore resta senza nuova promozione nella navigazione; confezionamento
atomico e ancora indipendente: `A7_ATOMIC_RUNTIME_PACKAGE.md`.

#463 MERGED dal proprietario il 22 ottobre 2026 alle 06:10:49 UTC:
main `699da628cd93fa864e4d5bda7ece675fab76a4de`, albero
`432b9c117dd028a4868c6abf8552f0c7eaf1f615`, identico al candidato attestato
remoto `af22d7beb1db090e70303d6c8df7aef8c56484ca`.
Quick locale ordinario PASS (SHA256
`497ba115765ab2229a736c95ca2112443deb3b526fc2db08c1e5104a0503cec8`),
Full locale ordinario senza skip PASS (SHA256
`452ae76782ec7c770bd1d983d8389991b48bd70ba97fb886a4e3234053e93742`).
CI Quick→Full effettivo `39675496733`, job `119484150667` / `119511077841`
SUCCESS; A3 `39675496750`, job `119484149846` SUCCESS. I tre checkout CI
`da2aeae677b6ff7036f0ba011082154f7df3b109` hanno lo stesso albero.
40 golden e 582 controlli browser PASS. Lighthouse locale supera le soglie;
CI usa l’eccezione Wikimedia preesistente esplicita, senza nuove deroghe.
Evidenze recuperate e SHA256 verificato:
`A7_PR463_af22d7b_evidenze.zip`,
`4583ef9e51aa76137870daee6848254dad5fd005496c03595ff142473301854f`.

Pubblicazione del merge verificata: Pages `39732351995`, build `119670040985`
e deploy `119676960542` SUCCESS. Reporter `39734566308`, job `119677133488`
SUCCESS: checkout `699da628cd93fa864e4d5bda7ece675fab76a4de`, integrità live
PASS e `ov-public-routes` / `ov-pages-live` SUCCESS. Pubblicazione e controlli
sono distinti dai gate della PR. Nessun merge o deploy dell’assistente. #443 verificata ancora aperta con conflitti, filone
editoriale separato; nessuna modifica alle altre PR o a Radar.

La #463 integra il selettore esplicito Toscana/Italia, valore comunale,
riferimento e scostamento originali A6. Metodo: `A7_BENCHMARK_INTERFACE.md`.
Il profilo benchmark copre 112 indicatori / 353 viste, 3.871 richieste
(3.421 computed / 450 rifiuti). I default del generatore restano i tre profili
originari; la build pubblica sceglie esplicitamente benchmark.

## Incremento corrente — rapporti aggregati nativi

Branch `feature/a7-native-operations`: A7.5.3 in corso, un solo nuovo profilo
opzionale `aggregation`, derivato dalle viste con `weighted_ratio`. Rapporto nativo
sugli esatti sette Comuni, senza periodi arbitrari, sottoinsiemi o `allowPartial`.
La ricognizione sul catalogo congelato trova 242 viste / 94 indicatori, 210
risultati e 32 rifiuti: misura del perimetro, non nuove prove numeriche indipendenti.
La misura combinata riprodotta è 41.993 richieste: 24.914 computed / 17.079
rifiuti, 104.234.277 byte gzip, +1.172.148 rispetto alla #463; nessun caricamento
integrale iniziale. La UI candidata mostra risultato e componenti originali con periodi; copertura
incompleta non produce un valore dell’intera Versilia. Nessuna somma generica,
media semplice dei tassi o sostituzione di n.d. con zero. Dettagli:
`A7_NATIVE_AGGREGATES.md`. Matrice derivata dalla ricevuta dell’interfaccia v3.

## Ambiente e prossima azione

Chrome Headless Shell ufficiale 151.0.7922.34, Playwright 1.62.0, Lighthouse
canonico 13.4.1; cache Python separate per modalità. Solo Percorsi riproduce
i due originali Leaflet 1.9.4 verificati SRI per il limite locale Unpkg, senza
modifica a DOM/dati/golden/soglie. Lighthouse non intercettato. CDN/WAN e telefono
fisico non certificati.

Completare preview e browser desktop/mobile, misura combinata e matrice, poi
Quick/Full locali ordinari e CI Quick→Full/A3 sul medesimo nuovo candidato.
PR Draft finché preview/browser non verificati. Gate ed evidenze finali nella PR:
nessun verde della #463 viene trasferito. Nessun merge/deploy dell’assistente.
Altre dimensioni/operazioni, incroci guidati, export e rapporti restano aperti;
A7 non è conclusa. Dossier editoriali e Radar restano separati.
