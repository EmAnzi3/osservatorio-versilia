# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente

- Main verificata: `d09d8e2f695a859e555cae28db69655f7b6d7130`, albero `c96760860332737c0532c1b532ed240e4857ed07`, merge del proprietario della #428. A6 DONE efficace dopo verifica post-merge e attestazione nella #428/issue #330, chiusa. A7 implementazione NOT_STARTED.
- Build/deploy `38401356844` e controllo live `38403216866` SUCCESS sul commit integrato. Replay post-merge sul catalogo pubblico: 225/225 adapter, zero scoperti; 3.727 PASS (2.033 calcoli, 1.694 rifiuti attesi); 35 letture e due riepiloghi preservati. Atlante 2025: 20.325 unità locali, universo Registro Imprese distinto da ASIA e dalle righe ATECO dirette.
- Catalogo sorgente 166/181 distinto dall’Effective Public Catalog. Limiti, rifiuti, 552 opportunità A3 non acquisite, 40 golden e Camaiore congelata restano invariati.

## Proposte in revisione

- #429, `docs/a7-functional-handoff`: documento tecnico e funzionale A7. Non introduce UI, modelli o servizi esterni. Gate e stato effettivo nella PR; non presumere Full verde da Quick verde.
- #430, `docs/territorial-dossiers-program`: programma editoriale separato, 17 ambiti con piani per domanda, sotto-dossier e lacune. Le 20 domande A6 restano immutate. Sei piloti sono specifiche; due dimostrazioni leggibili su Massarosa (lavoro e infanzia/scuola) collegano risultati, interpretazioni e fabbisogni. Gli altri ambiti non sono dichiarati dossier completi.
- Nuovo contratto editoriale nel Quick: piani e input ostili prima della build; replay numerico e rigenerazione dei documenti dopo la build. Nessuna modifica a dati, adapter, interfacce, Radar o acquisizioni.
- Revisione P2 #430: riepilogo/hash derivati e verificati, percorso del catalogo indirizzato per hash; esempi numerici di PILOTS inclusi nella riproduzione. Test mirati: 295 richieste e sei documenti PASS; Quick/Full e CI da riconfermare sul candidato aggiornato, senza riutilizzare i verdi della head precedente.
- Full CI #430: riprodotta la lettura vuota nel transitorio nascosto del grafico Agricoltura. Il gate attende ora la percentuale visibile dopo gli enhancer, conservando le verifiche di unità e valori. Nessuna modifica al runtime o ai golden; gate completi da riconfermare sulla nuova head.

## Prossima azione

Completare Quick→Full locali in sequenza su un checkout pulito del candidato #430, verificare CI Quick→Full e A3 sullo stesso albero, quindi consegnare il contenuto al proprietario per revisione e approvazione del merge. Esiti, commit e log sono nella PR: questo handoff non anticipa i gate. #429 richiede i propri gate. Nessun merge o deploy dell’assistente.

Dopo l’integrazione delle proposte, sviluppare i singoli dossier per lotti motivati e decidere separatamente il primo prototipo A7. Hosting statico, calcolo deterministico, fonti e gestione delle richieste ambigue restano vincoli; non è stata scelta né avviata una nuova infrastruttura.

## Limiti

Dati congelati verificati nei perimetri dichiarati; disponibilità online delle fonti distinta dalla riconciliazione degli snapshot. Numeri e provenance verificabili non certificano automaticamente la pertinenza editoriale o l’adeguatezza di una decisione. Correlazioni, spesa e stati amministrativi non sono prove causali o risultati di politica. Nessuna inferenza individuale da aggregati.
