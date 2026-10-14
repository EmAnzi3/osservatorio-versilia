# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline integrata

- Main verificata: `4c4a03f7ad47a4261cf4c65de674dfbde0e5fba3`, tree `f450b7852e573b68014623dbb2b818ad0f70cc2b`, merge del proprietario della #429 il 14 ottobre 2026. Deploy `38566370077` e controllo live `38568149233` PASS sul commit integrato; attestazione nella #429.
- A6 DONE dopo #428: 225/225 adapter, 3.727 PASS (2.033 calcoli/1.694 rifiuti), 35 letture e due riepiloghi. Atlante 2025: 20.325 unità locali Registro Imprese, distinto da ASIA e dalle righe dirette ATECO. Catalogo sorgente 166/181 distinto dall'effettivo. Nessuna riapertura o modifica A6.
- #430 integrata: 17 ambiti, 45 sotto-dossier, 51 piani collegati alle evidenze, 20 domande A6 preservate, sei specifiche pilota e due dimostrazioni Massarosa. 295 richieste (201 calcoli/94 rifiuti), sei documenti riprodotti. Non sono 51 dossier completi.
- Limiti, rifiuti, opportunità A3 non acquisite, 40 golden e Camaiore congelata preservati. Nessuna manutenzione Radar in questo lotto.

## Primo esperimento A7 — candidato in revisione

Il proprietario ha autorizzato la prova statica sui due dossier Massarosa. Branch `experiment/a7-static-pilot`; specifica `docs/A7_STATIC_PILOT.md`. Il builder usa piani/casi canonici e motore Python originale; il lettore ES module consulta i risultati offline. Scope con soli riferimenti, senza un catalogo parallelo.

Sei domande curate, 13 calcoli e tre rifiuti pertinenti. Richieste esatte o selezioni per ID; chiarimento per altro testo, consenso esplicito per copertura parziale. Ogni fatto numerico ha un puntatore alla risposta A6 e citazioni; classificazione parziale, periodi, universi, null/zero, esclusioni e campi condizionali dei rifiuti restano distinti. Bundle e release identificati da hash; output derivati e misure sono artefatti di verifica, non dati canonici.

A7 IN_PROGRESS nel candidato: A7.1–A7.4 provati soltanto su questo perimetro; nessuno step è dichiarato DONE. UI, modelli e servizi esterni non introdotti e architettura definitiva non selezionata. Dati, adapter, interfacce, dossier approvati e golden invariati.

## Gate e prossima azione

Verifiche mirate su aspettative indipendenti, provenance, frasi ancorate, input alterati, cache, null/zero, rifiuti e parità Node/browser. Gate A7 sul catalogo effettivo nel Quick ordinario, dichiarato nel contratto workflow. Quick→Full locali obbligatori in sequenza sul medesimo albero, poi CI Quick→Full e A3 sullo stesso candidato. Stato, commit e log effettivi nella PR: nessun verde della baseline sostituisce questi gate.

Dopo revisione e merge del proprietario: verifica commit/albero integrato, deploy e live. Valutare poi utilità e presentazione delle risposte prima di autorizzare un primo lotto UI; eventuali servizi/modelli richiedono una decisione separata. Non ampliare indefinitamente il programma dossier prima di realizzare i piloti.

## Limiti

Misure Node/Chromium locali non sono prestazioni mobile o di rete. Matching esatto del repertorio non equivale a comprensione generale del linguaggio. Integrità rispetto a una release fidata non autentica manifest forniti da soggetti non fidati. Dati congelati e disponibilità online restano distinti; associazioni e variazioni non provano causalità o risultati di politica. Nessuna inferenza individuale o raccomandazione automatica.
