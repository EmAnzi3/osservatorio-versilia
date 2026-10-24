# Consolidamento Osservatorio Versilia — handoff operativo

## Main verificata il 24 ottobre 2026 — #474 integrata e pubblicata

Merge del proprietario `c5386a38f4a5c490b0e10e0bfa1ca50d20c77a1c`, albero
`7a2afdac9b425cf6b52686325a3a226ae1510a1b`, identico alla head #474
`7c766b417215da9a41deb6aa157e12ffbe8425be`. Nessun merge/deploy dell’assistente.
CI Quick→Full effettivo nello stesso run `40032825527`, job `120685009917`
e `120698490944`, SUCCESS; A3 `40032825514`, job `120685007265`, SUCCESS.
Checkout effettivo `6d24726c` con il medesimo albero. Quick e Full locali
ordinari eseguiti PASS; il Full termina il 23 ottobre alle 23:34 UTC.
La conservazione del suo log è incompleta: ricevuta e rapporti disponibili,
quattro log completi su cinque. Non è un’attestazione archivistica completa;
limite e tentativi distinti nella #474, senza trasferimento di verdi.
Evidenze #474 `A7_EXPLICIT_ASSOCIATIONS_e6d52b0_evidenze.zip`, SHA256
`958c9cfeb9f8e706b92db512c7b80eb39cf39aceed345e99230ce64cdb2324c9`.

Pubblicazione verificata separatamente: Pages push `40070233147`, build
`120801890630` e deploy `120806424596` SUCCESS. Reporter `40071753266`, job
`120806501424` SUCCESS; checkout effettivo del merge nei log build/live.
Integrità Chiedi asset/hash, `ov-public-routes` e `ov-pages-live` PASS;
log live SHA256 `b9e998ad7e2d6a69e02c03cb5dbca3e34ed5044b2a65d537ce8b0200b7e26cec`.
Quick/Full skipped del push non sono nuovi gate. Il reporter è un campione
live di disponibilità/integrità, non certifica tutte le richieste numeriche.

A6 DONE: 225/225 adapter, 3.727 casi indipendenti, 35 letture e due riepiloghi,
Atlante 20.325 unità locali native, 40 golden e Camaiore congelata. A7
IN_PROGRESS. La #473 espone la tendenza nativa; la #474 integra il trasporto
opzionale dei piani di associazione, senza abilitarli nella build pubblica.
Ultima misura approvata dei profili pubblici: 50.523 richieste,
28.422 computed / 22.101 rifiuti, 127.146.205 byte gzip. Misura di trasporto,
non nuovi casi numerici indipendenti. Nessuna promozione in navigazione.

## Incremento corrente — anteprima degli incroci guidati

Branch `feature/a7-guided-pair-selection`, base main #474. A7.5.4 resta aperta.
`build_a7_explorer_preview.py --associations` aggiunge nella stessa pagina due
variabili, asse, metodo, motivo/copertura, risultato e coppie originali A6.
Selezioni derivate dal piano ancorato, nomi/unità dal catalogo canonico:
nessuna whitelist di domande o coppia scelta dal coefficiente. Il grafico
proietta soltanto le coppie native; tabelle e fonti conservano periodi e unità.
Nessun coefficiente sostitutivo nei rifiuti, consenso esplicito e revoca dei
risultati superati durante il fetch. Metodo `A7_GUIDED_ASSOCIATION_PREVIEW.md`.

È un’opzione isolata: `public=True, associations=True` è vietato. Default,
materializzatore pubblico e interfaccia v6 restano invariati; soltanto questa
anteprima usa v7 e i due nuovi asset. Prima del rollout restano misura e
revisione del perimetro preparato. Non è interrogabilità universale né un
ampliamento automatico del runtime. Il motivo non viene riscritto: una modifica
richiede un’altra richiesta esatta e la sua materializzazione originale A6.

Il gate di trasporto esistente verifica anche la UI sulla shell canonica,
1440/390/320 px, parità nativa, selettori invertiti, rifiuto temporale A6,
testo ostile, consenso, cache, guasti/ripresa e selezione superata. Gli otto
casi originali del lettore conservano il proprio budget; undici casi UI in
runtime separato. La prova preliminare del componente non certifica la pagina
completa. Preview reale, Quick/Full locali ordinari e CI Quick→Full/A3 richiesti
sul nuovo candidato; nessun verde della #474 trasferito. Evidenze nella PR.

Restano incroci pubblici, perimetro generale, riuso/CSV/PDF e consolidamento.
Dossier e Radar separati; nessuna acquisizione, modifica di adapter/dati/golden,
modello esterno, backend o costo ricorrente. Merge e deploy restano del proprietario.
