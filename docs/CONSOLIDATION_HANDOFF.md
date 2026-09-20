# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A4 — Visualization & Content Contract
- **Step attivo:** A4.3 — coerenza dato/testo/asse/tooltip/legenda
- **Stato:** IN_PROGRESS — A4.1 e A4.2 implementati nel branch corrente
- **Main verificato:** `571fb09ec2bb3bea7907b6ad61e4723cb25a2b78` (merge #268)
- **A3:** DONE
- **Catalogo effettivo baseline:** 225 indicatori · 1.547 righe
- **Confronti baseline:** 84 `comparisonReference=aggregate` · 141 fallback media semplice
- **Missing baseline:** 22 righe `n.d.` · 24 righe `n.a.`
- **Branch corrente:** `feat/a4-visual-content-contract-foundation`
- **PR corrente:** da aprire — A4.1 + A4.2
- **Modifiche visive:** nessuna

## A4.1–A4.2

Il lotto consolida le regole già presenti e introduce un contratto globale senza creare un inventario parallelo di indicatori.

Governati:
- unità e precisione;
- scale generiche;
- dato mancante vs non applicabile;
- polarità e semantica non valutativa del colore;
- riferimenti di confronto e modi di differenza;
- benchmark Toscana/Italia;
- coerenza tra valore visibile, tooltip e accessibilità.

Il contratto è `ci/visualization-content-contract.json`.
Il validator `scripts/visualization_content_contract.py` viene eseguito sul catalogo sorgente e sul catalogo effettivo materializzato.

## Residuo A4 immediato

1. **A4.3:** testare coerenza tra dato, unità, testo, asse, tooltip e legenda.
2. **A4.4:** distinguere e testare media semplice, media ponderata, totale, rapporto e denominatori.
3. **A4.5:** introdurre visual regression rappresentativa; qui potrà essere necessaria verifica visiva del proprietario.
4. **A4.6:** completare l'integrazione dei gate nel preflight generale.

## Decisioni vincolanti

1. `data/site-data.json` resta la fonte canonica del catalogo.
2. Il contratto A4 descrive regole, non ID di metriche.
3. Nessuna semantica di aggregazione viene cambiata automaticamente in A4.1–A4.2.
4. I 141 fallback alla media semplice sono un perimetro di audit A4.4, non 141 errori presunti.
5. `n.d.` e `n.a.` devono restare distinti.
6. Nessuna modifica visuale in questo lotto.

## Prossima azione esatta

1. Aprire PR Ready A4.1 + A4.2.
2. Verificare Quick e Full sul final head.
3. Se verdi, merge soltanto dopo approvazione esplicita del proprietario.
4. Dopo il merge procedere direttamente con A4.3 + A4.4 in un lotto sostanziale non-visivo.
