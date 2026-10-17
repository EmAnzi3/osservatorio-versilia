# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline integrata

- Main `97350ccd7ca623dd40d1cef86002a5e356a8575b`, tree `69aa253e1398c0209cf4d1de7210710454bf9d85`: #436 mergiata dal proprietario il 15 ottobre. CI Quick→Full `38803154090` e A3 `38803154200` SUCCESS sull’albero candidato. Deploy `38810123390` e live `38812506527` SUCCESS sul commit integrato. Quick/Full locali ordinari PASS sul medesimo albero; il Full locale si è concluso dopo il merge del proprietario, come attestato nella #436. I job push skipped non sono nuovi PASS.
- A6 DONE dopo #428: 225/225 adapter, 3.727 PASS (2.033 calcoli/1.694 rifiuti), 35 letture e due riepiloghi. Atlante 2025: 20.325 unità locali Registro Imprese. Nessuna riapertura di A6.
- Programma #430 conservato: 17 ambiti, 45 sotto-dossier, 51 piani, 20 domande A6; sei specifiche e due dimostrazioni Massarosa, non 51 dossier completati. 295 richieste (201 calcoli/94 rifiuti).
- Limiti, opportunità A3 non acquisite, 40 golden e Camaiore congelata preservati. Radar, acquisizioni e manutenzioni parallele fuori perimetro.

## A7 IN_PROGRESS — primi percorsi guidati

#432: builder A6 originale e lettore ES module. #433/#434: preview con due ambiti, sei domande parziali, 13 calcoli e tre rifiuti nel bundle; domanda scritta riconosciuta soltanto nel repertorio, alternative esplicite, consenso e JSON riproducibile. Fatti, periodi, universi, fonti, puntatori, rifiuti e hash conservati. Nessun classificatore libero o servizio.

Specifiche originarie: `docs/A7_STATIC_PILOT.md` e `docs/A7_DOSSIER_PREVIEW.md`. Nessuno step o Definition of Done A7 dichiarato completato.

## Incremento candidato — nuova lettura educativa

Branch `feature/a7-education-editorial`, baseline pulita #436. Il proprietario ha fermato l’espansione della vecchia presentazione e chiesto un modello ispirato a ONS/Openpolis. Incremento circoscritto alla domanda centrale sull’offerta educativa: sintesi, grafici selezionati, dossier interno per capitoli e rapporto PDF composto dagli stessi risultati. Revisione dopo feedback del 16 ottobre: gerarchia editoriale più marcata e confronti MIM estesi ai sette Comuni, con componenti visibili; le quattro richieste aggiuntive riusano catalogo/motore e preservano integralmente il bundle dimostrativo originale. Non confondere il precedente filtro Massarosa/Viareggio con dati mancanti. Le cinque altre domande conservano la lettura precedente; il JSON pubblico diventa un’opzione nei dettagli tecnici. Nessun accesso da Home/menu richiesto, nessun nuovo dato o adapter. Specifica e catena delle evidenze: `docs/A7_EDUCATION_EDITORIAL_READING.md`.

## Gate e prossima azione

Verificare contenuti, navigazione e PDF desktop/mobile; Quick→Full locali ordinari in sequenza sul medesimo albero prima della prontezza al merge, CI Quick→Full/A3 sulla head corrente. Il gate A7 esistente comprende riproducibilità del PDF, ancore indipendenti, scale/null/zeri e hash degli asset. Soglie/golden e prove della preview isolata conservate. Esiti effettivi, log e SHA nella PR; nessun verde precedente o skipped sostituisce un PASS.

Feedback del proprietario del 16 ottobre: direzione editoriale migliorata; rimossa la numerazione dai pulsanti dei capitoli, con una colonna sugli schermi fino a 360 px per mantenere intere le parole. In coerenza con AGENTS.md, Ready richiede preview/browser locali conclusi e Quick verde sulla head corrente: è uno stato di revisione, non una dichiarazione di prontezza al merge. Quick→Full locali ordinari restano obbligatori in sequenza sul medesimo albero; Full locale e CI Quick→Full/A3 devono essere tutti PASS sul candidato prima del via libera al merge. I Full possono procedere in parallelo, senza riusare esiti di altri alberi. I gate browser bulk, compositi e Lavoro/Istruzione età×genere usano l’attesa del client effettivamente renderizzato già condivisa dalla suite: i controlli del prerender possono precedere il binding degli eventi; assert, timeout, soglie e golden restano invariati. Il download PDF rifiuta errori HTTP e hash non coerenti; dopo un ritentativo verificato riuscito cancella messaggio e stato d’errore. La regressione esercita entrambi i recuperi senza manipolare il DOM. Nessun merge o deploy dell’assistente. Dopo eventuale merge del proprietario: verificare commit/albero, deploy e live. A7 resta IN_PROGRESS; interpretazione libera e rollout agli altri dossier separati.

## Limiti

Una domanda educativa riorganizzata non equivale a un servizio di interrogazione generale o a dossier completati in tutti gli ambiti. Capacità diversa da accesso; confronto selezionato diverso da territori equivalenti; evidenze congelate diverse da situazione attuale. Nessuna conclusione automatica sull’adeguatezza dei servizi o sulle politiche. Valutazione del proprietario sulla fruibilità ancora necessaria.
