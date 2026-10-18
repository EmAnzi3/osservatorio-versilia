# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline integrata

- Main `8e186186419f5434839e3397d0811817743cfc50` dopo #450 Radar; #447 social, #442, #444 e #445 integrate dal proprietario. Gli otto file della #450 sono preservati senza modifiche A7. #445 mergiata il 18 ottobre alle 09:20 UTC; gate locali Quick→Full e CI/A3/Radar PASS sulla sua head; deploy `39114927336` e live `39116176854` SUCCESS sul merge. Un deploy non attesta un nuovo refresh produttivo del Radar. #443 lavoro/redditi resta una PR separata aperta, head `89127ca`, con gate locali e CI PASS e revisione editoriale del proprietario ancora richiesta.
- A6 DONE dopo #428: 225/225 adapter, 3.727 PASS (2.033 calcoli/1.694 rifiuti), 35 letture e due riepiloghi. Atlante 2025: 20.325 unità locali Registro Imprese. Nessuna riapertura di A6.
- Programma #430 conservato: 17 ambiti, 45 sotto-dossier, 51 piani, 20 domande A6; sei specifiche e due dimostrazioni Massarosa, non 51 dossier completati. 295 richieste (201 calcoli/94 rifiuti).
- Limiti, opportunità A3 non acquisite, 40 golden e Camaiore congelata preservati. Radar, acquisizioni e manutenzioni parallele fuori perimetro.

## A7 IN_PROGRESS — primi percorsi guidati

#432: builder A6 originale e lettore ES module. #433/#434: preview con due ambiti, sei domande parziali, 13 calcoli e tre rifiuti nel bundle; domanda scritta riconosciuta soltanto nel repertorio, alternative esplicite, consenso e JSON riproducibile. Fatti, periodi, universi, fonti, puntatori, rifiuti e hash conservati. Nessun classificatore libero o servizio.

Specifiche originarie: `docs/A7_STATIC_PILOT.md` e `docs/A7_DOSSIER_PREVIEW.md`. Nessuno step o Definition of Done A7 dichiarato completato.

## Incremento candidato — metodo generale di interrogazione

#442 educativa sette Comuni è integrata; #443 lavoro/redditi resta distinta. Il proprietario richiede capacità generali su tutti i dati, non altre risposte predefinite. Branch `feature/a7-general-query-method`: scoperta derivata dal catalogo effettivo e dalle dichiarazioni A6, piani di richieste strutturate e risposte originali integre. Nessun nuovo inventario, adapter, dato, UI, modello o servizio. Metodo in `docs/A7_GENERAL_QUERY_METHOD.md`; CLI `scripts/a7_query_workbench.py`. Giustapposizione diversa da relazione, aggregazione Versilia soltanto se autorizzata, componenti calcolate diverse da risposta amministrativa completa. A7 rimane IN_PROGRESS; nessuno step dichiarato DONE.

Prove: tutte le aspettative indipendenti A6 attraverso l'involucro, tutte le dichiarazioni degli indicatori, varianti territoriali generate, parità delle risposte e rifiuti, isolamento/riproducibilità e limiti dei piani. Esiti effettivi e hash nei log del candidato/PR, non verdi attribuiti anticipatamente. Il test entra nei check del catalogo effettivo del preflight. Passi successivi: disponibilità per vista/periodo, accessibilità A3→A6→A7, scelta di esecuzione compatibile Pages misurata, poi esplorazione pubblica e dossier basati sugli stessi piani. Interpretazione libera e schede amministrative ancora da implementare.

Incremento generale candidato della #448 (ancora aperta): lettura numerica `observe`
con Comune esplicito e un solo periodo, selezione/provenance native e rifiuti
esistenti preservati. `compare` richiede ancora almeno due osservazioni; `lookup`
GAIA distinto. Nessun adapter o dato modificato. Disponibilità corrente/storico
dichiarato verificabile via CLI, senza promessa di ultimo anno o di accesso a
ogni campo acquisito. Metodo `docs/A7_POINT_OBSERVATIONS.md`, matrice derivata
`docs/A7_QUESTION_FEASIBILITY.md`: esempi di accettazione, non routing di risposte.
Prima modalità pubblica prevista guidata, nessun modello/servizio scelto. Runtime
Pages da misurare nel browser prima della decisione; dossier conservati.

Review P2 della head precedente riprodotta e corretta: le quattro viste della
classificazione territoriale non sono numeriche, quindi non dichiarano né
ammettono `observe`. Confronto categoriale ed etichette originari conservati;
regressione su tutte le viste e sette Comuni, disponibilità ed eleggibilità
diretta. I 3.727 casi A6 restano integri; 3.337 parità numeriche puntuali e
3.338 viste numeriche distinte. Verdi CI della head precedente e Full locali
interrotti non attestano questo nuovo candidato: ripetere i gate senza scorciatoie.

## Gate e prossima azione

Rieseguire Quick e Full locali ordinari in sequenza sul medesimo albero candidato,
poi CI Quick→Full effettivo e A3 sulla nuova head. I verdi della precedente head
#448 non attestano questo incremento. Registrare ricevute e limiti nella PR;
nessun merge o deploy dell'assistente. #443 resta separata, da riallineare dopo
l'integrazione approvata della #448, con revisione editoriale del proprietario.
Nessuno step A7 dichiarato DONE. Nuove acquisizioni, Radar e social fuori perimetro.

Quick locale PASS il 18 ottobre sull'albero pre-#450 `6c8ec7f`, inclusa la
sitemap; Full interrotto per riallineare la baseline dopo il merge parallelo.
Non attestano l'albero aggiornato: nuova sequenza locale e CI sulla nuova head.
Il precedente Quick con voce Opportunità mancante e i tentativi interrotti
restano documentati senza convertirli in PASS.
