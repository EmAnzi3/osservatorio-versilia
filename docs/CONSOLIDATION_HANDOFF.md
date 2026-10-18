# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline integrata

- Main `3d3ccb010b821ba4cafaa41f17b875b8c70f1905`, tree `38207e43b6f1df5b1eae80a2dd317d24b259407c`: #442 mergiata dal proprietario il 17 ottobre alle 22:14 UTC. Albero integrato identico alla head approvata `5c465b5`. Quick/Full locali e CI Quick `39055373898`, Full effettivo `39058307423`, A3 `39055373937` PASS su quella head; i job push skipped non sono nuovi PASS. Deploy post-merge `39074244546` e controllo live `39075152471` SUCCESS sul commit integrato; pubblicazione verificata.
- A6 DONE dopo #428: 225/225 adapter, 3.727 PASS (2.033 calcoli/1.694 rifiuti), 35 letture e due riepiloghi. Atlante 2025: 20.325 unità locali Registro Imprese. Nessuna riapertura di A6.
- Programma #430 conservato: 17 ambiti, 45 sotto-dossier, 51 piani, 20 domande A6; sei specifiche e due dimostrazioni Massarosa, non 51 dossier completati. 295 richieste (201 calcoli/94 rifiuti).
- Limiti, opportunità A3 non acquisite, 40 golden e Camaiore congelata preservati. Radar, acquisizioni e manutenzioni parallele fuori perimetro.

## A7 IN_PROGRESS — primi percorsi guidati

#432: builder A6 originale e lettore ES module. #433/#434: preview con due ambiti, sei domande parziali, 13 calcoli e tre rifiuti nel bundle; domanda scritta riconosciuta soltanto nel repertorio, alternative esplicite, consenso e JSON riproducibile. Fatti, periodi, universi, fonti, puntatori, rifiuti e hash conservati. Nessun classificatore libero o servizio.

Specifiche originarie: `docs/A7_STATIC_PILOT.md` e `docs/A7_DOSSIER_PREVIEW.md`. Nessuno step o Definition of Done A7 dichiarato completato.

## Lettura educativa integrata e incremento lavoro/redditi

#442: domanda educativa per sette Comuni, selettore, capitoli, confronti e PDF legati alla release immutabile. Null INVALSI e zeri 0–3 conservati; nessuna graduatoria di qualità. Standard editoriale con logo canonico, firma/dominio/pagine, edizione distinta dai periodi, fonte distinta dall'elaborazione e riuso CC BY 4.0 per i soli contenuti originali. Metodo in `docs/A7_EDUCATION_EDITORIAL_READING.md`.

Branch `feature/a7-work-income-reading` riallineato alla main #442: compone la domanda centrale lavoro in sei capitoli e sette Comuni. Tutte le sei componenti obbligatorie lavoro; tre componenti fiscali come contesto distinto dal piano redditi, la cui serie pensioni non è composta. Ventuno richieste verificate A6, confronti alfabetici, segni negativi, null e coperture fiscali conservati; selezione Comune, URL, PDF verificato e cache governati dal grafo immutabile. Pilota originale, consenso, dodici export ed educazione conservati. Metodo in `docs/A7_WORK_INCOME_READING.md`. Nessun nuovo dato/adapter, acquisizione, accesso Home/menu o passo A7 dichiarato DONE.

Enrichment educativo domanda/accoglienza/attese 0–3 ancora proposto, non acquisito; catalogo Toscana CKAN 403 al controllo del 17 ottobre. Scheda in `docs/dossiers/METHOD.md`. Abitazione/bilanci e altri dossier rimangono sviluppi distinti.

## Gate e prossima azione

Verificare contenuti, navigazione e PDF desktop/mobile; Quick→Full locali ordinari in sequenza sul medesimo albero prima della prontezza al merge, CI Quick→Full/A3 sulla head corrente. Il verificatore numerico lavoro/redditi è dichiarato autonomamente in `canonical.effectiveCatalogChecks` del contratto workflow, senza invocazione nascosta o duplicata nel pilota statico. Il gate A7 esistente comprende riproducibilità del PDF, ancore indipendenti, scale/null/zeri e hash degli asset. Soglie/golden e prove della preview isolata conservate. Esiti effettivi, log e SHA nella PR; nessun verde precedente o skipped sostituisce un PASS.

Feedback del proprietario del 16 ottobre: direzione editoriale migliorata; rimossa la numerazione dai pulsanti dei capitoli, con una colonna sugli schermi fino a 360 px per mantenere intere le parole. In coerenza con AGENTS.md, Ready richiede preview/browser locali conclusi e Quick verde sulla head corrente: è uno stato di revisione, non una dichiarazione di prontezza al merge. Quick→Full locali ordinari restano obbligatori in sequenza sul medesimo albero; Full locale e CI Quick→Full/A3 devono essere tutti PASS sul candidato prima del via libera al merge. I Full possono procedere in parallelo, senza riusare esiti di altri alberi. I gate browser bulk, compositi e Lavoro/Istruzione età×genere usano l’attesa del client effettivamente renderizzato già condivisa dalla suite: i controlli del prerender possono precedere il binding degli eventi; assert, timeout, soglie e golden restano invariati. Il download PDF rifiuta errori HTTP e hash non coerenti; dopo un ritentativo verificato riuscito cancella messaggio e stato d’errore. La regressione esercita entrambi i recuperi senza manipolare il DOM. Nessun merge o deploy dell’assistente. Dopo eventuale merge del proprietario: verificare commit/albero, deploy e live. A7 resta IN_PROGRESS; interpretazione libera e rollout agli altri dossier separati.

## Limiti

Una domanda educativa riorganizzata non equivale a un servizio di interrogazione generale o a dossier completati in tutti gli ambiti. Capacità diversa da accesso; confronto selezionato diverso da territori equivalenti; evidenze congelate diverse da situazione attuale. Nessuna conclusione automatica sull’adeguatezza dei servizi o sulle politiche. Valutazione del proprietario sulla fruibilità ancora necessaria.
