# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline integrata

- Main: `4b972e4e8197064522bc3a058df2dcc70d8b0a1b`, tree `0ebe0e074e0a8effdd9faef1922019e37a4420e4`, merge del proprietario della #433 il 15 ottobre 2026. Albero identico alla head con Quick→Full locali, CI Quick→Full, A3 e Full CI Ready PASS. Attestazione post-merge nella #433: deploy `38697939202` e controllo live `38700032140` SUCCESS sul commit integrato. I job push Quick/Full skipped non sono nuovi PASS.
- A6 DONE dopo #428: 225/225 adapter, 3.727 PASS (2.033 calcoli/1.694 rifiuti), 35 letture e due riepiloghi. Atlante 2025: 20.325 unità locali Registro Imprese, distinto da ASIA e dalle divisioni ATECO dirette. Catalogo sorgente 166/181 distinto dall'effettivo. Nessuna riapertura di A6.
- #430 integrata: 17 ambiti, 45 sotto-dossier, 51 piani e 20 domande A6 preservate; sei specifiche pilota e due dimostrazioni Massarosa. 295 richieste (201 calcoli/94 rifiuti), sei documenti riprodotti. Non sono 51 dossier completi.
- Limiti, rifiuti, opportunità A3 non acquisite, 40 golden e Camaiore congelata preservati. Radar, acquisizioni e altre manutenzioni fuori da questo lotto.

## A7 IN_PROGRESS — prova statica e preview integrate

#432: builder Python originale A6 e lettore ES module con risultati precalcolati. #433: preview navigabile isolata, due dossier e sei domande curate, 13 calcoli e tre rifiuti pertinenti. Tutte le domande restano parzialmente supportate. Consenso esplicito per componenti parziali, nessuna promozione dei rifiuti; fatti ancorati, periodi/universi/fonti/puntatori e risposte originali conservati. Commit delle fonti risolto in Git e riconciliato con programma, dossier e hash snapshot, anche ricostruiti.

Specifiche: `docs/A7_STATIC_PILOT.md` e `docs/A7_DOSSIER_PREVIEW.md`. Nessuna route pubblica, servizio o modello. A7.1–A7.4 provati solo sul perimetro curato; nessuno step o Definition of Done A7 dichiarato completato.

## Incremento in revisione

Branch `experiment/a7-guided-questions-export`: accesso per domanda scritta attraverso il lettore approvato, chiarimento esplicito per testi non riconosciuti ed esportazione JSON della selezione canonica e delle componenti originali. Nessun classificatore libero, nuovo dato, adapter, domanda canonica o inventario parallelo. Il file scaricato non contiene richieste ambigue o selezioni precedenti; modificare testo/selezione revoca risposta, consenso e download precedente.

Test browser reali su domande normalizzate, richieste ambigue/causali/fuori periodo o territorio, input HTML, selezione esplicita e consenso rinnovato, revoca anche per controlli distaccati ed export riconciliato con le risposte A6. Rimangono le verifiche precedenti di provenienza, bundle alterato, null/zero, browser/Node e sei domande desktop/mobile. Il gate resta nel test A7 esistente, senza nuovi workflow o soglie.

## Gate e prossima azione

Quick→Full locali ordinari obbligatori in sequenza sullo stesso albero; preview e verifiche browser prima della review della UI, CI Quick→Full e A3 sullo stesso candidato. Stato, commit e log effettivi nella PR: nessun verde della baseline o skipped sostituisce un gate. Nessun merge o deploy dell'assistente.

Dopo integrazione e verifica, valutare con il proprietario l'accesso pubblico ai due percorsi guidati e l'utilità del chiarimento, separatamente dall'interpretazione libera e dalla scelta di eventuali servizi/modelli. Il repertorio più ampio rimane nel programma dossier: questo incremento non lo dichiara implementato.

## Limiti

Matching del repertorio diverso da comprensione generale del linguaggio. Misure locali non sono prestazioni mobile/rete. Integrità rispetto a una release fidata non autentica un file modificato o un hosting compromesso. Dati congelati e disponibilità corrente delle fonti distinti; associazioni e variazioni non provano causalità. Nessuna inferenza individuale, previsione o raccomandazione automatica.
