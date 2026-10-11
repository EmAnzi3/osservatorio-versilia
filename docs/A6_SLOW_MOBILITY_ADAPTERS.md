# A6 — Inventario Percorsi Versilia, adapter v47

Cinque carrier: `slowMobilityRoutes`, `slowMobilityTrekking`, `slowMobilityCammini`, `slowMobilityBici`, `slowMobilityMtb`. Dimensione `total`; confronti e ranghi numerici sui sette Comuni. Il conteggio riguarda record pubblici A0/B1 dell'inventario editoriale, non tutti i percorsi fisicamente esistenti. Il rango non misura accessibilità, qualità, sicurezza o priorità politica.

## Riferimento e universo

Fotografia pubblicata il 12 agosto 2026: 41 record, 30 A0 e 11 B1. Il periodo di risposta è `2026-08-12`; l'anno pubblico `2026` è un alias di selezione, non un'attestazione delle condizioni attuali. Lo stato pubblicato nel 2023 di alcune tracce non è stato ricontrollato. A0 significa geometria ufficiale redistribuibile; B1 geometria OSM corroborata documentalmente. Queste classi descrivono provenienza e controllo documentale, non agibilità o sicurezza.

Le modalità sono quelle **primarie** dei record: 31 trekking, due cammini, sette bici e un MTB. Un record viene contato una volta nella sua modalità primaria: non è una rilevazione di tutte le attività possibili sulla traccia. Gli zeri significano assenza di record della modalità nell'inventario pubblico comunale, non assenza di percorsi sul territorio.

## Replay e provenienza

L'adapter decodifica i cinque `percorsi/data/routes-part-*.b64` (base64, gzip, JSON). Verifica hash dei byte originali e del JSON decodificato; conserva in cache solo le proprietà semantiche `p`, senza coordinate `l`. Fingerprint completi delle proprietà e dei riferimenti sono ricontrollati a ogni uso, insieme al carrier pubblico, a `site_stats.json` e a `master_summary.json`. Identità comunali, ID univoci, filtro pubblico, classi, modalità e riepiloghi sono riconciliati.

Ogni osservazione riporta gli ID contati e le prove del catalogo, delle cinque parti e dei due riepiloghi; i puntatori ai record si riferiscono al JSON **decodificato**, con encoding e hash espliciti. Il replay riguarda ID, modalità e appartenenze comunali già assegnate nello snapshot. Non riesegue le intersezioni delle geometrie con confini amministrativi né la validazione originaria delle tracce. Le fonti originali restano nel dataset; non sono state acquisite nuovamente.

## Non additività e limiti

I totali comunali sommano a 68 **presenze di percorso**, a fronte di 41 record distinti. Il record MTB `mm-vrg-mtb-05` appartiene a Camaiore, Massarosa e Viareggio: tre conteggi locali rappresentano un solo percorso. Il cicloturistico `mm-vrg-cyc-03` attraversa sei Comuni. Le somme per modalità sono 40 trekking, cinque cammini, 20 bici e tre MTB: non sono i conteggi univoci 31/2/7/1.

Sono rifiutati pooling, benchmark geografici, anomalie e correlazioni non revisionate. Il totale pubblico 41 è riconciliato come universo di record; non diventa automaticamente un benchmark comunale o una somma dei Comuni. Serie, variazioni e trend sono rifiutati: versioni precedenti dell'inventario descriverebbero la storia editoriale del prodotto, non una serie territoriale omogenea. Non vengono introdotti chilometri comunali, quote A0/B1, rapporti pro capite o componenti retro-derivate.

## Verifica e perimetro

`test_semantic_slow_mobility_adapters.py`: 35 conteggi fissi indipendenti dalle risposte, replay distinto dei 41 record e 68 appartenenze, modalità/classi, ID condivisi, zeri/pari merito, puntatori, periodi e operazioni rifiutati, attacchi al carrier e alle proprietà/riferimenti/riepiloghi in cache e al file prima della lettura. 135 nuove domande conservano le 2.712 della baseline corrente; conteggi osservati nei report di `reports/a6-slow-mobility/`. Otto carichi prestazionali aggiunti, uno per carrier e casi di rango/rifiuto, senza soglie hardware-indipendenti.

Copertura derivata 216/225 effettivi, 159/181 sorgente, nove residui. Il main dopo #409 include anche la manutenzione fonti #407: catalogo e registro effettivi sono rigenerati dalla baseline corrente, senza riutilizzare i precedenti snapshot analitici. Nessuna modifica a dati, interfaccia, asset, golden, workflow, Radar o checkpoint Camaiore; 35 letture territoriali e due riepiloghi conservati. A6.4 resta parziale, A6.5–A6.6 aperte e A7 non avviata. Quick locale prima del push; Full completo locale e CI Quick→Full prima della prontezza al merge del proprietario.
