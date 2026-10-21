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

## Incremento corrente — reporter della pubblicazione

Riprodotto il rosso del reporter #459: un job di pubblicazione presente con
conclusione nulla diventava failure anche con route live PASS. Il reporter ora
rilegge soltanto i metadati GET del medesimo run, con tentativi/timeout limitati.
Successo o fallimento esplicito del job restano necessari: il successo complessivo
del workflow non sostituisce l’esito della pubblicazione. Se l’esito rimane
incompleto, lo stato è pending, senza falsi verdi o fallimenti inventati.
Pubblicazioni skipped/assenti continuano a preservare lo stato precedente;
esito delle route e refresh Radar restano distinti. Nessun trigger o deploy nuovo.

Il gate esistente copre conclusione nulla, stato ancora in corso, successi e
fallimenti dopo rilettura, API indisponibile, lista incompleta e limite dei retry,
oltre ai contratti precedenti. Regressione mirata PASS; nuovi Quick/Full locali
ordinari e CI Quick→Full/A3 obbligatori su questo candidato prima della prontezza
al merge. I verdi della #459 non si trasferiscono alla correzione del reporter.

## Ambiente e prossima azione

Chrome Headless Shell ufficiale 151.0.7922.34 (SHA256
`e11fc9ce65c96313476f7ee9844b6fb6a9220fb048693cfe9eee00acf4170a9f`),
Playwright 1.62.0, Lighthouse canonico 13.4.1, cache Python separate per modalità.
Solo Percorsi riproduce i due originali Leaflet 1.9.4 verificati SRI, perché il
browser locale non raggiunge Unpkg. Le route persistono sulla medesima pagina e
ne disabilitano lì la cache; Lighthouse separato non intercettato. La fixture CDN
non modifica DOM, dati, golden o soglie; CDN/WAN/telefono fisico non certificati.

Completare gate e PR tecnica dedicata al reporter. Nessun merge/deploy senza
approvazione del proprietario. Poi proseguire A7 dai divari della matrice, con
benchmark selettivi come prossimo incremento proposto; export generale e dossier
restano distinti. A7 non è DONE.
