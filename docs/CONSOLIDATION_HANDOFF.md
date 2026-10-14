# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline integrata

- Main integrata: `ae1249784c6e3ba25a99da52cc35780049a88380`, tree `77d24913d6603c63461abd8f080442fa16beb55f`, merge del proprietario della #432 il 14 ottobre 2026. Albero identico al candidato con Quick→Full locali e CI/A3 PASS; deploy `38629658417` e live `38631526143` PASS sul commit integrato, attestati nella #432. I job push skipped non sono nuovi PASS.
- A6 DONE dopo #428: 225/225 adapter, 3.727 PASS (2.033 calcoli/1.694 rifiuti), 35 letture e due riepiloghi. Atlante 2025: 20.325 unità locali Registro Imprese, distinto da ASIA e dalle righe dirette ATECO. Catalogo sorgente 166/181 distinto dall'effettivo. Nessuna riapertura o modifica A6.
- #430 integrata: 17 ambiti, 45 sotto-dossier, 51 piani collegati alle evidenze, 20 domande A6 preservate, sei specifiche pilota e due dimostrazioni Massarosa. 295 richieste (201 calcoli/94 rifiuti), sei documenti riprodotti. Non sono 51 dossier completi.
- Limiti, rifiuti, opportunità A3 non acquisite, 40 golden e Camaiore congelata preservati. Nessuna manutenzione Radar in questo lotto.

## Primo esperimento A7 — integrato, A7 ancora IN_PROGRESS

Il proprietario ha autorizzato la prova statica sui due dossier Massarosa. PR #432 integrata; specifica `docs/A7_STATIC_PILOT.md`. Il builder usa piani/casi canonici e motore Python originale; il lettore ES module consulta i risultati offline. Scope con soli riferimenti, senza un catalogo parallelo.

Sei domande curate, 13 calcoli e tre rifiuti pertinenti. Richieste esatte o selezioni per ID; chiarimento per altro testo, consenso esplicito per copertura parziale anche nei rifiuti A6 che conservano osservazioni numeriche. Il consenso non promuove il rifiuto a calcolo. Ogni fatto numerico ha un puntatore alla risposta A6 e citazioni; classificazione parziale, periodi, universi, null/zero, esclusioni e campi condizionali dei rifiuti restano distinti. Bundle e release identificati da hash; output derivati e misure sono artefatti di verifica, non dati canonici.

A7 IN_PROGRESS: A7.1–A7.4 provati soltanto su questo perimetro; nessuno step è dichiarato DONE. UI, modelli e servizi esterni non introdotti e architettura definitiva non selezionata. Dati, adapter, interfacce, dossier approvati e golden invariati.

## Gate e prossima azione

Verifiche mirate su aspettative indipendenti, provenance, frasi ancorate, input alterati, cache, null/zero, rifiuti e parità Node/browser. Gate A7 sul catalogo effettivo nel Quick ordinario, dichiarato nel contratto workflow. Quick→Full locali obbligatori in sequenza sul medesimo albero, poi CI Quick→Full e A3 sullo stesso candidato. Stato, commit e log effettivi nella PR: nessun verde della baseline sostituisce questi gate.

Dopo il via del proprietario successivo al merge #432: branch `experiment/a7-dossier-preview`, prima preview navigabile isolata sui due dossier e sulle sei domande esistenti. Specifica `docs/A7_DOSSIER_PREVIEW.md`. Nessuna route o modifica al sito pubblico: la preview serve alla revisione di utilità, fonti, limiti e consenso. Commit dei link risolto in Git e riconciliato con programma, dossier e hash snapshot, inclusi sorgenti ricostruiti. P2 corretto; il Full locale della prima head interrotto non vale PASS. Gate browser integrato nel test A7 esistente; Quick→Full locali e CI/A3 sullo stesso candidato prima della prontezza al merge. Nuova PR Draft fino alla verifica browser locale; integrazione pubblica, servizi e modelli restano decisioni successive.

## Limiti

Misure Node/Chromium locali non sono prestazioni mobile o di rete. Matching esatto del repertorio non equivale a comprensione generale del linguaggio. Integrità rispetto a una release fidata non autentica manifest forniti da soggetti non fidati. Dati congelati e disponibilità online restano distinti; associazioni e variazioni non provano causalità o risultati di politica. Nessuna inferenza individuale o raccomandazione automatica.
