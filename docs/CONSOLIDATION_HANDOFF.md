# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline integrata

- Main `fed2a7c73f3ba480a153eea4748e7b874b2e8c28` dopo #448; #450 Radar integrata; #447 social, #442, #444 e #445 integrate dal proprietario. Gli otto file della #450 sono preservati senza modifiche A7. #445 mergiata il 18 ottobre alle 09:20 UTC; gate locali Quick→Full e CI/A3/Radar PASS sulla sua head; deploy `39114927336` e live `39116176854` SUCCESS sul merge. Un deploy non attesta un nuovo refresh produttivo del Radar. #443 lavoro/redditi resta una PR separata aperta, head `89127ca`, con gate locali e CI PASS e revisione editoriale del proprietario ancora richiesta.
- A6 DONE dopo #428: 225/225 adapter, 3.727 PASS (2.033 calcoli/1.694 rifiuti), 35 letture e due riepiloghi. Atlante 2025: 20.325 unità locali Registro Imprese. Nessuna riapertura di A6.
- Programma #430 conservato: 17 ambiti, 45 sotto-dossier, 51 piani, 20 domande A6; sei specifiche e due dimostrazioni Massarosa, non 51 dossier completati. 295 richieste (201 calcoli/94 rifiuti).
- Limiti, opportunità A3 non acquisite, 40 golden e Camaiore congelata preservati. Radar, acquisizioni e manutenzioni parallele fuori perimetro.

## A7 IN_PROGRESS — primi percorsi guidati

#432: builder A6 originale e lettore ES module. #433/#434: preview con due ambiti, sei domande parziali, 13 calcoli e tre rifiuti nel bundle; domanda scritta riconosciuta soltanto nel repertorio, alternative esplicite, consenso e JSON riproducibile. Fatti, periodi, universi, fonti, puntatori, rifiuti e hash conservati. Nessun classificatore libero o servizio.

Specifiche originarie: `docs/A7_STATIC_PILOT.md` e `docs/A7_DOSSIER_PREVIEW.md`. Nessuno step o Definition of Done A7 dichiarato completato.

## A7 — metodo generale integrato e runtime selettivo candidato

#448 mergiata dal proprietario il 18 ottobre 2026, commit `fed2a7c73f3ba480a153eea4748e7b874b2e8c28`, albero `ad8f632b6b0fe66c202b9f36dde6e9218c1aa2ff` identico al candidato verificato. Quick e Full locali ordinari PASS in sequenza; CI Quick→Full effettivo `39163394320` e A3 `39163394281` PASS sulla head `700fad3`. Dati, adapter, golden e risultati dei dossier conservati; classificazioni categoriali escluse dalla lettura numerica. `observe`, disponibilità e piani generali sono integrati; non certificano l'accesso a ogni campo A3 né l'ultimo anno di ogni fonte. Metodo e matrice: `docs/A7_POINT_OBSERVATIONS.md`, `docs/A7_QUESTION_FEASIBILITY.md`. Le trenta domande sono esempi di accettazione, non un routing chiuso.

Branch `feature/a7-static-query-runtime`: prototipo isolato del trasporto statico, senza nuova pagina, servizio, modello o integrazione nel builder pubblico. Dichiarazioni derivate dal catalogo; risposte originali A6 in blocchi per vista/profilo, caricati su richiesta dal browser con catena di hash, budget e cache limitata. Profili iniziali: corrente per Comune, confronto dei sette e storico per Comune, soltanto dove dichiarati. Operazioni non materializzate restano distinte da rifiuti A6 e dati mancanti; nessuna aggregazione Versilia implicita, riscrittura di richieste o consenso automatico. Metodo: `docs/A7_SELECTIVE_QUERY_RUNTIME.md`.

Review P2 accolta: i tempi restano nella diagnostica del chiamante/stdout, fuori dagli artefatti della release. Il gate rappresentativo confronta ora tutti i file generati delle due build, compreso `measurement.json`, e verifica parità delle risposte, browser desktop/mobile, integrità, isolamento, consenso e richieste fuori involucro. Misura completa isolata: 225 indicatori, 3.359 viste, 37.880 richieste; 100.804.953 byte gzip complessivi, manifest 101.722 byte, massimo blocco compresso 636.338 byte. È una misura di trasporto/accesso, non un audit numerico esaustivo. Gate mirato: 1.134 parità native su 58 carrier/93 viste, 155 selezioni browser a ciascuna larghezza desktop/mobile; build identiche da cataloghi collocati in directory diverse. Nessuno step A7 dichiarato DONE.

## Gate e prossima azione

Quick e Full locali ordinari in sequenza sul candidato, poi CI Quick→Full effettivo e A3 sulla sua head. Non riusare i verdi della #448 come gate della nuova PR. Deploy #448 `39171231146` e live `39172500248` SUCCESS sul merge `fed2a7c7`, con commit verificato nei log; pubblicazione attestata. Nessun merge o deploy dell'assistente.

Prima del rollout pubblico: completare audit A3→A6→A7 e copertura delle altre operazioni, confrontare dimensioni/costo della build e caricamento selettivo; integrare una release atomica e i selettori solo dopo queste prove. #443 resta separata e richiede riallineamento/revisione editoriale del proprietario. Radar, social e acquisizioni fuori perimetro.
