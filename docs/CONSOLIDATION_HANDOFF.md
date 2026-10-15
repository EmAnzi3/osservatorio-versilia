# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline integrata

- Main `d1ca5f603235431ee97a319273b60a655fac8c00`, tree `6b8ea2b36565f102aec73261a5e02ab40be4c2fe`: merge del proprietario della #434 il 15 ottobre 2026. Albero identico alla head con Quick→Full locali, CI Quick→Full e A3 PASS. Deploy `38713425144` e controllo live `38715250485` SUCCESS sul commit integrato, attestati nella #434; i job push Quick/Full skipped non sono nuovi PASS. La preview #434 resta isolata dal sito.
- A6 DONE dopo #428: 225/225 adapter, 3.727 PASS (2.033 calcoli/1.694 rifiuti), 35 letture e due riepiloghi. Atlante 2025: 20.325 unità locali Registro Imprese, distinto da ASIA e divisioni ATECO dirette. Sorgente 166/181 distinto dall'effettivo; nessuna riapertura di A6.
- Programma #430: 17 ambiti, 45 sotto-dossier, 51 piani e 20 domande A6 conservati; sei specifiche e due dimostrazioni Massarosa. 295 richieste (201 calcoli/94 rifiuti), sei documenti riprodotti. Non sono 51 dossier o risposte complete.
- Limiti, opportunità A3 non acquisite, 40 golden e Camaiore congelata preservati. Radar, acquisizioni e manutenzioni parallele fuori perimetro.

## A7 IN_PROGRESS — primi percorsi guidati

#432: builder A6 originale e lettore ES module. #433/#434: preview con due ambiti, sei domande parziali, 13 calcoli e tre rifiuti nel bundle; domanda scritta riconosciuta soltanto nel repertorio, alternative esplicite, consenso e JSON riproducibile. Fatti, periodi, universi, fonti, puntatori, rifiuti e hash conservati. Nessun classificatore libero o servizio.

Specifiche originarie: `docs/A7_STATIC_PILOT.md` e `docs/A7_DOSSIER_PREVIEW.md`. Nessuno step o Definition of Done A7 dichiarato completato.

## Incremento candidato

Branch `feature/a7-public-guided-dossiers`: prima integrazione `/chiedi/`, con shell e ricerca canoniche, link di approfondimento e stesso lettore/bundle. La UI risolve il bundle rispetto al modulo, senza variazioni ai calcoli o alle interazioni. Un adattatore pubblico mantiene visibili i titoli dopo il focus senza modificare la preview. Accesso iniziale tramite URL e sitemap; nessuna modifica al menu globale o ai percorsi approvati. Contratto standalone esplicito; generazione nel builder pubblico e validazione build/live di route, asset e hash. Senza JavaScript resta il testo delle letture; errori nelle evidenze bloccano i risultati.

I sette asset sono legati a una cartella immutabile con hash del manifest: moduli di deployment diversi non condividono URL. Una release parziale non può riusare il vecchio lettore; l’entry point blocca i risultati se manca un modulo. La cache PWA usa rivalidazione HTTP e rete prima della cache soltanto per i cinque asset di evidenza/codice sotto la cartella di release di `/chiedi/`. Browser reale: cache HTTP attiva con TTL di un’ora e vecchi asset online non prevalgono sui nuovi; cache mista offline rifiutata dal lettore. Le policy delle altre route restano invariate. Il campo scritto non viene salvato o trasmesso.

Metodo e revisione in `docs/A7_PUBLIC_GUIDED_PAGE.md`. Il candidato avanza A7.5 sul perimetro curato, senza dichiarare pubblicato il nuovo accesso o conclusa A7. Nessun nuovo dato, adapter, numero o repertorio canonico.

## Gate e prossima azione

Quick→Full locali ordinari in sequenza sullo stesso albero; preview/browser/visione desktop-mobile prima della review UI, CI Quick→Full e A3 sulla head attuale. Test A7 esistente esteso alla pagina generata, dodici export completi riconciliati, shell/ricerca, fallback senza JS, dati mancanti/corrotti e service worker reale. Gate generali, golden e soglie invariati. Esiti, commit e log effettivi nella PR; nessun skipped o verde precedente sostituisce un gate.

Il proprietario rivede la pagina nella preview prima del merge. Dopo l'eventuale integrazione verificare commit/albero, deploy e live con asset/hash A7. Nessun merge o deploy dell'assistente. Ulteriori dossier, accesso da Home/menu e interpretazione libera restano incrementi separati, guidati da esigenze reali.

## Limiti

Matching del repertorio diverso da comprensione generale. Misure locali diverse da prestazioni mobile/rete o certificazione completa delle tecnologie assistive. Integrità di release diversa da autenticità di hosting/file alterati. Snapshot congelati diversi da disponibilità corrente online. Nessuna causalità, previsione, inferenza individuale o raccomandazione automatica.
