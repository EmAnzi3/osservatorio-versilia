# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

Non è un diario storico: deve restare breve, concreto e aggiornato. La cronologia completa resta in Git e nelle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A0 — Governance del programma e handoff`
- **Step attivo:** `A0.3/A0.4`
- **Stato:** `IN_PROGRESS`
- **Baseline main di avvio:** `f7c132eb5262ff2fcf028bfb3c5fecb339c95e2f`
- **Catalogo dichiarato dalla baseline:** 225 indicatori
- **Branch corrente:** `chore/consolidation-roadmap`
- **PR corrente:** da aprire

## Completato in questa fase

- Definita la roadmap di consolidamento con workstream `A0`–`A7` e step identificabili.
- Definito questo handoff persistente per il passaggio tra chat/sessioni.
- Confermato che `data/site-data.json` resta il catalogo canonico: il consolidamento non deve introdurre un inventario parallelo.
- Registrata come problema strutturale da risolvere in `A1` la possibile divergenza tra conteggi/versioni/stato mostrati da README, sito, Stato dati e output materializzati.

## Decisioni vincolanti

1. Nessun push diretto su `main`; sempre branch + PR.
2. Nessun nuovo catalogo canonico parallelo a `data/site-data.json`.
3. Stato del progetto e controlli devono essere **derivati**, non mantenuti copiando conteggi manuali.
4. Ogni PR che avanza la roadmap deve aggiornare questo handoff.
5. La nuova sessione deve leggere, nell'ordine: `AGENTS.md`, `docs/CONSOLIDATION_ROADMAP.md`, questo file.
6. Nessun merge o pubblicazione senza approvazione esplicita del proprietario.

## Prossima azione esatta

1. Aggiornare `AGENTS.md` con la regola di lettura/aggiornamento roadmap + handoff per il programma di consolidamento.
2. Aprire la PR di fondazione del tracking.
3. Registrare qui il numero della PR e portare `A0.3/A0.4` a completati.
4. Dopo approvazione e merge, avviare `A1.1`: audit completo del percorso `site-data.json` → materializzatori → catalogo effettivamente pubblicato.

## Verifiche

- Modifiche previste in questa PR: solo documentazione/regole operative, nessuna UI e nessun dato pubblico.
- Il preflight locale non è stato ancora eseguito nella sessione corrente.

## Per ripartire in una nuova chat

Prompt minimo consigliato:

> Riprendi il consolidamento di `EmAnzi3/osservatorio-versilia`. Leggi `AGENTS.md`, `docs/CONSOLIDATION_ROADMAP.md` e `docs/CONSOLIDATION_HANDOFF.md`, verifica che branch/PR indicati siano ancora attuali e prosegui dalla “Prossima azione esatta” senza saltare i gate.
