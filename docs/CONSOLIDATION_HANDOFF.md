# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline integrata

- Main `c80749a1e2871f491b5087732cf8c70610cc9dce`, tree `bac4fa1b0072f0484840e567cb77d381ad35ce82`: #437 mergiata dal proprietario il 17 ottobre. Quick/Full locali ordinari PASS sul medesimo albero; CI Quick `39030351987`, Full effettivo `39032237491`, A3 `39030352000` PASS sulla head `01e0138`. Deploy post-merge `39039130288` e live `39040063783` SUCCESS sul commit integrato; pubblicazione verificata. I job push skipped non sono nuovi PASS. Il fix del ritentativo PDF è integrato.
- A6 DONE dopo #428: 225/225 adapter, 3.727 PASS (2.033 calcoli/1.694 rifiuti), 35 letture e due riepiloghi. Atlante 2025: 20.325 unità locali Registro Imprese. Nessuna riapertura di A6.
- Programma #430 conservato: 17 ambiti, 45 sotto-dossier, 51 piani, 20 domande A6; sei specifiche e due dimostrazioni Massarosa, non 51 dossier completati. 295 richieste (201 calcoli/94 rifiuti).
- Limiti, opportunità A3 non acquisite, 40 golden e Camaiore congelata preservati. Radar, acquisizioni e manutenzioni parallele fuori perimetro.

## A7 IN_PROGRESS — primi percorsi guidati

#432: builder A6 originale e lettore ES module. #433/#434: preview con due ambiti, sei domande parziali, 13 calcoli e tre rifiuti nel bundle; domanda scritta riconosciuta soltanto nel repertorio, alternative esplicite, consenso e JSON riproducibile. Fatti, periodi, universi, fonti, puntatori, rifiuti e hash conservati. Nessun classificatore libero o servizio.

Specifiche originarie: `docs/A7_STATIC_PILOT.md` e `docs/A7_DOSSIER_PREVIEW.md`. Nessuno step o Definition of Done A7 dichiarato completato.

## Incremento candidato — lettura educativa per sette Comuni

Branch `feature/a7-education-seven-towns`, baseline pulita #437. Il feedback del 17 ottobre chiede evidenze e conclusioni pertinenti al Comune selezionato. La stessa domanda educativa viene composta per ciascuno dei sette Comuni usando le risposte A6 già disponibili: selettore locale, sintesi argomentata, evidenziazione nei grafici, URL condivisibile e PDF del Comune, tutti legati al manifest immutabile. Null INVALSI e zeri 0–3 conservati; nessuna graduatoria di qualità o indicazione automatica di politica. Le cinque altre domande e i dodici export del pilota Massarosa restano distinti. Nessun nuovo dato/adapter o accesso da Home/menu. Metodo e contratto in `docs/A7_EDUCATION_EDITORIAL_READING.md`.

Prossimo enrichment proposto, non acquisito: domanda/accoglienza/attese 0–3 dalla fonte Toscana già usata, con verifica di campi e copertura ancora necessaria; catalogo CKAN 403 al controllo del 17 ottobre. Scheda di ammissione in `docs/dossiers/METHOD.md`. Prima completare e valutare questa lettura; lavoro/redditi successivo come composizione degli acquisiti. Nessuna riapertura A6.

## Gate e prossima azione

Verificare contenuti, navigazione e PDF desktop/mobile; Quick→Full locali ordinari in sequenza sul medesimo albero prima della prontezza al merge, CI Quick→Full/A3 sulla head corrente. Il gate A7 esistente comprende riproducibilità del PDF, ancore indipendenti, scale/null/zeri e hash degli asset. Soglie/golden e prove della preview isolata conservate. Esiti effettivi, log e SHA nella PR; nessun verde precedente o skipped sostituisce un PASS.

Feedback del proprietario del 16 ottobre: direzione editoriale migliorata; rimossa la numerazione dai pulsanti dei capitoli, con una colonna sugli schermi fino a 360 px per mantenere intere le parole. In coerenza con AGENTS.md, Ready richiede preview/browser locali conclusi e Quick verde sulla head corrente: è uno stato di revisione, non una dichiarazione di prontezza al merge. Quick→Full locali ordinari restano obbligatori in sequenza sul medesimo albero; Full locale e CI Quick→Full/A3 devono essere tutti PASS sul candidato prima del via libera al merge. I Full possono procedere in parallelo, senza riusare esiti di altri alberi. I gate browser bulk, compositi e Lavoro/Istruzione età×genere usano l’attesa del client effettivamente renderizzato già condivisa dalla suite: i controlli del prerender possono precedere il binding degli eventi; assert, timeout, soglie e golden restano invariati. Il download PDF rifiuta errori HTTP e hash non coerenti; dopo un ritentativo verificato riuscito cancella messaggio e stato d’errore. La regressione esercita entrambi i recuperi senza manipolare il DOM. Nessun merge o deploy dell’assistente. Dopo eventuale merge del proprietario: verificare commit/albero, deploy e live. A7 resta IN_PROGRESS; interpretazione libera e rollout agli altri dossier separati.

## Limiti

Una domanda educativa riorganizzata non equivale a un servizio di interrogazione generale o a dossier completati in tutti gli ambiti. Capacità diversa da accesso; confronto selezionato diverso da territori equivalenti; evidenze congelate diverse da situazione attuale. Nessuna conclusione automatica sull’adeguatezza dei servizi o sulle politiche. Valutazione del proprietario sulla fruibilità ancora necessaria.
