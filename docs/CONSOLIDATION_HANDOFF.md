# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente

- Main verificata: `201be08ef46320c181ce9e4d97eb1f84ee524ea7`, albero `c08c0a77271c877b4e34723cb967d6beaf68d478`, merge del proprietario della #430 il 14 ottobre 2026. Albero identico al candidato verificato; build/deploy `38543139366` e controllo live `38545155775` SUCCESS sul commit integrato, comprese le route Stato dati, PNRR e Percorsi.
- A6 DONE efficace dopo #428 e verifica post-merge, attestata nella #428/issue #330 chiusa. Baseline certificata: 225/225 adapter, 3.727 PASS (2.033 calcoli, 1.694 rifiuti), 35 letture e due riepiloghi; Atlante 2025 20.325 unità locali del Registro Imprese, distinto da ASIA e dalle righe ATECO dirette. Catalogo sorgente 166/181 distinto dall'effettivo. A7 implementazione NOT_STARTED.
- Limiti, rifiuti, 552 opportunità A3 non acquisite, 40 golden e Camaiore congelata preservati. Nessuna acquisizione o manutenzione Radar in questo lotto.

## Programma dossier integrato

- #430: 17 ambiti, 45 sotto-dossier e 51 piani di domanda collegati alle evidenze. Le 20 domande A6 restano immutate. Sei piloti sono specifiche; due dimostrazioni leggibili Massarosa lavoro e infanzia/scuola collegano risultati, interpretazioni e fabbisogni. Gli altri ambiti non sono dichiarati dossier completi.
- Manifest editoriale `ci/territorial-dossier-program.json`, repertorio e moduli in `docs/dossiers/`, evidenze derivate in `reports/territorial-dossiers/`. Nessun catalogo canonico parallelo. Replay di 295 richieste (201 calcoli, 94 rifiuti attesi), sei documenti e riepilogo/hash riprodotti; gate nel Quick. Correzione del test Agricoltura conservata: attesa della percentuale visibile dopo gli enhancer, senza modificare runtime o golden.
- Gate propri #430 Quick→Full locali PASS sul medesimo albero; CI Quick→Full `38523942443` e A3 `38523942469` SUCCESS. Evidenze e limiti dell'ambiente nella PR. I gate #430 non attestano quelli della #429.

## Proposta in revisione

- #429, `docs/a7-functional-handoff`: `docs/A7_FUNCTIONAL_TECHNICAL_HANDOFF.md` riallineato alla main integrata e al repertorio #430. Distingue campi comuni della risposta A6 e campi condizionali post-valutazione: preservare anche i rifiuti senza coverage/formula/policy. Aggiorna soltanto documentazione; non introduce UI, modelli, servizi o infrastrutture. A6 non viene riaperta; A7 implementazione non avviata. Gate e stato effettivo della proposta nella PR.

## Prossima azione

Completare Quick→Full locali in sequenza sul candidato aggiornato #429, verificare CI Quick→Full e A3 sullo stesso albero, quindi consegnare l'handoff al proprietario per revisione e approvazione del merge. Nessun merge o deploy dell'assistente; gli esiti della baseline non sostituiscono quelli del nuovo candidato.

Dopo l'integrazione dell'handoff, sviluppare i dossier per lotti motivati e decidere separatamente il primo esperimento tecnico A7. Hosting statico, calcolo deterministico, fonti, rifiuti e chiarimenti restano vincoli; nessuna architettura esterna è stata selezionata. Non ampliare indefinitamente il programma dei dossier prima di realizzare i piloti.

## Limiti

Dati congelati verificati nei perimetri dichiarati; disponibilità online delle fonti distinta dalla riconciliazione degli snapshot. Numeri e provenance verificabili non certificano automaticamente pertinenza editoriale o adeguatezza di una decisione. Correlazioni, spesa e stati amministrativi non sono prove causali o risultati di politica; nessuna inferenza individuale.
