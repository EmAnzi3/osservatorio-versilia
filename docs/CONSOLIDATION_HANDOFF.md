# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline integrata

- Main `0ec115fad78966cf6e8269d678acdccd731e7291`, tree `2ff9054b4031bbcfe90d6251f9b60ef05523bfbb`: #442, #444 e #445 integrate dal proprietario. #445 mergiata il 18 ottobre alle 09:20 UTC; gate locali Quick→Full e CI/A3/Radar PASS sulla sua head; deploy `39114927336` e live `39116176854` SUCCESS sul merge. Un deploy non attesta un nuovo refresh produttivo del Radar. #443 lavoro/redditi resta una PR separata aperta, head `89127ca`, con gate locali e CI PASS e revisione editoriale del proprietario ancora richiesta.
- A6 DONE dopo #428: 225/225 adapter, 3.727 PASS (2.033 calcoli/1.694 rifiuti), 35 letture e due riepiloghi. Atlante 2025: 20.325 unità locali Registro Imprese. Nessuna riapertura di A6.
- Programma #430 conservato: 17 ambiti, 45 sotto-dossier, 51 piani, 20 domande A6; sei specifiche e due dimostrazioni Massarosa, non 51 dossier completati. 295 richieste (201 calcoli/94 rifiuti).
- Limiti, opportunità A3 non acquisite, 40 golden e Camaiore congelata preservati. Radar, acquisizioni e manutenzioni parallele fuori perimetro.

## A7 IN_PROGRESS — primi percorsi guidati

#432: builder A6 originale e lettore ES module. #433/#434: preview con due ambiti, sei domande parziali, 13 calcoli e tre rifiuti nel bundle; domanda scritta riconosciuta soltanto nel repertorio, alternative esplicite, consenso e JSON riproducibile. Fatti, periodi, universi, fonti, puntatori, rifiuti e hash conservati. Nessun classificatore libero o servizio.

Specifiche originarie: `docs/A7_STATIC_PILOT.md` e `docs/A7_DOSSIER_PREVIEW.md`. Nessuno step o Definition of Done A7 dichiarato completato.

## Incremento candidato — metodo generale di interrogazione

#442 educativa sette Comuni è integrata; #443 lavoro/redditi resta distinta. Il proprietario richiede capacità generali su tutti i dati, non altre risposte predefinite. Branch `feature/a7-general-query-method`: scoperta derivata dal catalogo effettivo e dalle dichiarazioni A6, piani di richieste strutturate e risposte originali integre. Nessun nuovo inventario, adapter, dato, UI, modello o servizio. Metodo in `docs/A7_GENERAL_QUERY_METHOD.md`; CLI `scripts/a7_query_workbench.py`. Giustapposizione diversa da relazione, aggregazione Versilia soltanto se autorizzata, componenti calcolate diverse da risposta amministrativa completa. A7 rimane IN_PROGRESS; nessuno step dichiarato DONE.

Prove: tutte le aspettative indipendenti A6 attraverso l'involucro, tutte le dichiarazioni degli indicatori, varianti territoriali generate, parità delle risposte e rifiuti, isolamento/riproducibilità e limiti dei piani. Esiti effettivi e hash nei log del candidato/PR, non verdi attribuiti anticipatamente. Il test entra nei check del catalogo effettivo del preflight. Passi successivi: disponibilità per vista/periodo, accessibilità A3→A6→A7, scelta di esecuzione compatibile Pages misurata, poi esplorazione pubblica e dossier basati sugli stessi piani. Interpretazione libera e schede amministrative ancora da implementare.

Enrichment educativo 0–3 proposto e non acquisito; nessuna nuova acquisizione autorizzata da questo incremento. Radar e manutenzioni social conservati fuori perimetro.

## Gate e prossima azione

Verificare contenuti, navigazione e PDF desktop/mobile; Quick→Full locali ordinari in sequenza sul medesimo albero prima della prontezza al merge, CI Quick→Full/A3 sulla head corrente. Il gate A7 esistente comprende riproducibilità del PDF, ancore indipendenti, scale/null/zeri e hash degli asset. Soglie/golden e prove della preview isolata conservate. Esiti effettivi, log e SHA nella PR; nessun verde precedente o skipped sostituisce un PASS.

Feedback del proprietario del 16 ottobre: direzione editoriale migliorata; rimossa la numerazione dai pulsanti dei capitoli, con una colonna sugli schermi fino a 360 px per mantenere intere le parole. In coerenza con AGENTS.md, Ready richiede preview/browser locali conclusi e Quick verde sulla head corrente: è uno stato di revisione, non una dichiarazione di prontezza al merge. Quick→Full locali ordinari restano obbligatori in sequenza sul medesimo albero; Full locale e CI Quick→Full/A3 devono essere tutti PASS sul candidato prima del via libera al merge. I Full possono procedere in parallelo, senza riusare esiti di altri alberi. I gate browser bulk, compositi e Lavoro/Istruzione età×genere usano l’attesa del client effettivamente renderizzato già condivisa dalla suite: i controlli del prerender possono precedere il binding degli eventi; assert, timeout, soglie e golden restano invariati. Il download PDF rifiuta errori HTTP e hash non coerenti; dopo un ritentativo verificato riuscito cancella messaggio e stato d’errore. La regressione esercita entrambi i recuperi senza manipolare il DOM. Nessun merge o deploy dell’assistente. Dopo eventuale merge del proprietario: verificare commit/albero, deploy e live. A7 resta IN_PROGRESS; interpretazione libera e rollout agli altri dossier separati.

## Limiti

Una domanda educativa riorganizzata non equivale a un servizio di interrogazione generale o a dossier completati in tutti gli ambiti. Capacità diversa da accesso; confronto selezionato diverso da territori equivalenti; evidenze congelate diverse da situazione attuale. Nessuna conclusione automatica sull’adeguatezza dei servizi o sulle politiche. Valutazione del proprietario sulla fruibilità ancora necessaria.
