# Consolidamento Osservatorio Versilia — handoff operativo

## Main verificata il 23 ottobre 2026 — #473 pubblicata

Merge del proprietario `7d37d8656b10e97ddc5fe2bc6c9b2ddc9e15c232`, albero
`9a16feb1bd6e3bdd8b68dae8c22a93668ea19e43`, identico alla head #473
`ce727611df093bb12a52b9a9e2a0b87fd7c2d8e7`. Nessun merge/deploy dell’assistente.
CI Quick `40003816014` e Full effettivo `40012982032` SUCCESS: percorso UI
Draft→Ready con verifica esplicita del Quick sulla stessa head, checkout
`48f58384` e medesimo albero. A3 `40003815917` SUCCESS.
Quick locale ordinario PASS il 23 ottobre 19:40–20:37 UTC, dopo il merge;
log SHA256 `4f39e75fa1ee74225b7252ee4f8b4ce00de651cd406d86ce47241b1e1815841c`.
Il Full locale ordinario non era completato al merge e non è incluso nei verdi
pre-merge. Attestazioni successive e ricevute aggiornate nella descrizione #473,
da verificare separatamente senza trasferirle a questo ramo.

Pubblicazione verificata separatamente: Pages push `40017134080`, build
`120631985299` e deploy `120648520847` SUCCESS. Reporter `40022023719`, job
`120648692934` SUCCESS; checkout effettivo del merge verificato nei due log,
integrità Chiedi asset/hash, `ov-public-routes` e `ov-pages-live` PASS.
Log live SHA256 `4e800495f73f0b53ba55e83d8be4bd2f899bcd0acdec105ef084f2de6459dba0`.
Quick/Full skipped del push non sono nuovi gate. Archivio checkpoint #473:
`A7_GUIDED_TRENDS_e6ce9b5f_evidenze.zip`, SHA256
`736e75ca9a7e83d2289bff5bb759bfcc1fde9cd6821a8c67d0a1947935cea243`;
quattro gate conclusi al checkpoint, Full locale allora pendente; non è
un’attestazione completa né sostituisce gli esiti successivi nella PR.

A6 DONE: 225/225 adapter, 3.727 casi indipendenti, 35 letture e due riepiloghi,
Atlante 20.325 unità locali native, 40 golden e Camaiore congelata. A7
IN_PROGRESS. #473 presenta la tendenza nativa per Comune: precisione e asse
originali, metodo OLS e limiti; nessuna previsione o graduatoria delle pendenze.
Runtime pubblicato: 50.523 richieste, 28.422 computed / 22.101 rifiuti,
127.146.205 byte gzip; misura di trasporto, non nuove prove numeriche indipendenti.
Due build complete, 12.849 file inclusi misura/release, byte-identiche.
Nessuna maggiore visibilità in navigazione.

## Incremento corrente — piani espliciti di associazione

Branch `feature/a7-guided-associations`, base main #473. Primo passo A7.5.4.
Il trasporto candidato accetta un piano strutturato con al massimo 32 richieste
`correlation` e 100.000 byte, senza ricercare tutte le coppie. Due selettori,
periodi, asse, metodo, motivo e consenso restano espliciti; A6 produce ogni
risposta o rifiuto. Nessun default o materiale pubblico ampliato implicitamente.
Metodo `A7_EXPLICIT_ASSOCIATION_PLANS.md`.

L’indice del piano e i blocchi entrano nel grafo atomico verificato. Il lettore
risolve richieste identiche, protegge le coppie incomplete anche quando le
coperture individuali sono complete, conserva rifiuti/cache/integrità e non
calcola coefficienti. L’audit registra separatamente le selezioni trasportate:
nessuna promozione a tutte le correlazioni della vista o a controlli pubblici.

Gate nel controllo generale esistente: ancora Spearman indipendente già A6,
parità Pearson/rifiuti, riproducibilità completa, profili precedenti invariati,
pacchetto atomico, consenso, selezioni fuori perimetro, guasti e snapshot durante
fetch in browser desktop/mobile. Quick/Full locali ordinari e CI Quick→Full/A3
sul medesimo candidato prima della prontezza al merge. Nessun verde #473 trasferito.

Restano: scelta guidata delle coppie e dei riferimenti, grafico dei punti,
dimensionamento del perimetro selezionato, riuso/CSV/PDF e consolidamento pubblico.
Nessuna interrogabilità universale; associazione diversa da causalità.
Dossier editoriali e Radar separati, nessun refresh Radar attestato da A7.
Nessuna acquisizione, adapter, modello esterno, backend o costo ricorrente nuovi.
Nessun merge o deploy autorizzato all’assistente.
