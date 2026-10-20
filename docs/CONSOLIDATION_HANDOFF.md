# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline verificata il 20 ottobre 2026

- Main `9ec855ff263c9ace7fabf957a12889dc58155f71`: #458 marker ai-memory integrata; nessuna variazione dei dati A6/A7. #448 è l’ultima integrazione A7 qui attestata come pubblicata. Nessuna nuova pubblicazione dedotta dai verdi delle PR.
- #451 OPEN/Ready, head `fd196e6681a75be3d4620d5155618a9f8568ebb4`, tree `8d30ba9dff733f38e1cde7a97901a47a5e819574`; Quick→Full `39178021176` e A3 `39178021175` PASS. Non integrata né pubblicata.
- #453 OPEN/Ready, head `be9fa6c6276cd6044fa2f5cc837a878ee5a2f946`, tree `5bf7dbde9937bd8a95c0d63501dc439be6273eef`; Quick e Full locali ordinari PASS, CI Quick→Full effettivo `39293987481` e A3 `39293987677` PASS sullo stesso albero. P2 riprodotto, corretto e risolto dopo i gate; preservata identità di categorie e anni nei puntatori. Evidenze `A7_PR453_be9fa6c_evidenze.zip`, SHA256 `822e9ff03d727bea59a87e420d5aeba77b856a5d9bff75daf31930da0f6e1ff6`. Non integrata né pubblicata.
- #454 OPEN/Ready, head `c75fdda28986e9c007f3d41907fc0bdcde817372`, tree `a3b0f8a7f429b9e82c561274fe5adacf7643fdb1`; Quick e Full locali ordinari, CI Quick→Full effettivo `39330914449` e A3 `39330914492` PASS sullo stesso albero. P2 sui massimi shard corretto e risolto. Evidenze `A7_PR454_c75fdda_evidenze.zip`, SHA256 `24c211acb9ce8045923e331d2d40537dc9d66c5e08b0d9d0032abcd04a064224`. Non integrata né pubblicata.
- #443 editoriale lavoro/redditi OPEN/Ready, head `89127cac42bfc1a0877695fff60e0b9103e01e86`, con conflitti all'ultima verifica; separata. Radar e social fuori perimetro.
- A6 DONE: 225/225 adapter, 3.727 casi indipendenti, 35 letture e due riepiloghi, Atlante 20.325 unità locali native, 40 golden e Camaiore congelata. Nessuna modifica di dati/adapter/golden.
- Dossier #430: 17 ambiti, 45 sotto-dossier, 51 piani, sei specifiche e due dimostrazioni; non 51 dossier completi. Piloti editoriali ed esploratore generale distinti.

## Incremento corrente — A7 IN_PROGRESS

Branch `feature/a7-public-explorer-integration`, da main #458 con #457
integrata soltanto nel branch locale. #457 OPEN/Ready, head
`1f115d0bcc890a0fc219ec37616a691929079e0f`, tree
`ffd81f04d5a88514a619e7eb40d371c795f01205`: Quick e Full locali ordinari
PASS; CI Quick→Full `39437265260` e A3 `39437265407` PASS sul medesimo albero.
Non integrata in main né pubblicata. Evidenze finali
`A7_PR457_1f115d0_evidenze.zip`, SHA256
`a6a78fa7c4b2159e44d957e51276516ff2b704315104f271f313156bb59735a0`;
salvataggio persistente non riuscito. PR precedenti ancora aperte.
Nessun merge o deploy autorizzato. Nuovo candidato ancora da verificare.

La matrice schema 3 estende la 2 con capacità UI derivate dal sito verificato e
pubblicazione non ispezionata, senza alterare i collegamenti A3/nativi/statici.
L’ultima misura schema 2 verificata resta:
746 riferimenti acquisiti risolti; tutti i percorsi richiesti provati per 275
coppie nel workbench e 187 nel trasporto, non intere dimensioni certificate.
Le 88 coppie con prove native complete ma non statiche comprendono 49 benchmark
e 39 dettagli territoriali; non sono dati assenti né 88 indicatori nuovi.
Restano 442 coppie senza prova nativa nel perimetro, non necessariamente inaccessibili.
Metodo e limiti `docs/A7_ACCESSIBILITY_AUDIT.md`; nessuno step A7 dichiarato DONE.

Il nuovo confezionatore valida l'intero grafo in staging: identità dei produttori,
dichiarazioni, richieste esatte, tutte le impronte native delle risposte, hash e
budget, misure e assenza di file misti. Un artefatto con identità adapter alterata
è stato riprodotto come accettato dalla prima versione: ora ogni header è
confrontato con quello nativo, senza modifiche ad A6 o inventari paralleli.
Finalizza una nuova directory con una sola rinomina, senza sostituire pacchetti
esistenti. Il modulo con nome content-addressed include il lettore originale e
l'ancora del manifest, con URL relativi della medesima release. Un errore non
restituisce dati sostitutivi; la nuova apertura ritenta la stessa release.
Metodo `docs/A7_ATOMIC_RUNTIME_PACKAGE.md`. Nessuna integrazione nella build o UI
pubblica; non è un deploy né il publisher completo del sito.

Il nuovo builder produce una preview isolata di `/chiedi/`, con selettori generali
derivati: tema, indicatore, vista filtrabile, operazione e Comune. Carica soltanto
il dettaglio scelto e i blocchi richiesti. Capacità native non trasportate,
rifiuti e copertura incompleta restano distinti; consenso esplicito, revoca anche
per risposte tardive, periodi e fonti originali, categorie e località preservate.
Pagina, presentazione e pacchetto ancorato sono nello stesso artifact locale
finalizzato in staging. Nessuna modifica al builder pubblico, menu o dossier;
nessuna nuova acquisizione o espansione del runtime. Metodo e limiti
`docs/A7_GUIDED_EXPLORER_PREVIEW.md`.

## Integrazione corrente e gate

Il builder canonico prepara il runtime completo sui tre profili predefiniti
in una directory temporanea e confeziona pagina e grafo verificato insieme.
Solo dopo verifica integrale sostituisce il dist generato, con ripristino in caso
di fallimento della rinomina. L’unico artifact Pages esistente contiene il sito
completo: nessun upload separato o progressivo, nessun nuovo servizio/workflow.
Le richieste al grafo passano dalla rete senza fallback CacheStorage/HTTP cache;
il lettore originale continua a verificare ancora, hash e budget. Il controllo
pubblico esistente richiede l’esploratore e verifica tutti i moduli, manifest,
un dettaglio e una risposta della release vincolata alla pagina. Il campione live
non certifica ogni risposta o la disponibilità futura del CDN.

Nessun aumento della navigazione, nessun ampliamento delle operazioni del runtime,
nessuna modifica a dati/adapter/golden. A6 DONE, A7 IN_PROGRESS. Questo incremento
richiede preview/browser locali, Quick e Full ordinari, CI Quick→Full effettivo
e A3 sul nuovo albero; i verdi #457 non vengono trasferiti. PR Draft fino alle
verifiche browser, nessun merge/deploy senza approvazione del proprietario.
Prima del rollout restano revisione dei testi, integrazione verificata e controllo
live del deploy effettivo; benchmark, altre selezioni, export generale e dossier
restano incrementi distinti motivati dalla matrice.

Metodo dell’incremento: `docs/A7_PUBLIC_EXPLORER_INTEGRATION.md`.
