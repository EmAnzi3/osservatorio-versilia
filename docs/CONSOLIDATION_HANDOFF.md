# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A2 — Full Coverage Source Monitor`
- **Step attivo:** `A2.2` — derivare il perimetro operativo del monitor dal catalogo pubblico
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `d498d2f931773cf8c30a8e051ccb340133d567a6`
- **Catalogo sorgente / pubblico auditato:** 181 / 225 indicatori
- **Branch:** `chore/a2-source-monitor-foundation`
- **PR corrente:** `#194` — draft

## Completato

- `A0` chiuso con merge autorizzato della PR `#188`.
- `A1.1`–`A1.3` chiusi con merge autorizzato della PR `#190`.
- `A1.4`–`A1.8` chiusi con merge della PR `#193`; Quick e Full GitHub verdi.
- Deploy post-merge della PR `#193`: Pages `#3219` verde; controllo live-status successivo verde.
- `A1 — Data Governance Foundation` è formalmente `DONE`.
- `A2.1` completato e documentato in `docs/A2_SOURCE_MONITOR_AUDIT.md`.
- Audit A2.1: il monitor mensile usa il catalogo sorgente e il registry `181/177/4`, mentre l'Effective Public Catalog contiene 225 indicatori.
- L'audit A1 aveva rilevato 180 ID nello stato operativo contro 225 pubblicati: gap operativo di 45 ID, pur con 225/225 policy fonte strutturalmente valide.
- Prima base della PR `#194`: Quick GitHub verde.
- Implementazione `A2.2` preparata nella stessa PR: `materialize_source_monitor_snapshot.py` riusa la catena della build pubblica e si arresta prima del prerender; il workflow mensile passa quindi al monitor lo snapshot pubblico derivato invece di `data/site-data.json`/`data/source-registry.json` sorgente.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. L'Effective Public Catalog resta una vista derivata della build; non va copiato in un secondo manifest manuale.
3. A2 deve misurare la copertura operativa per identità degli ID pubblicati, non tramite un numero atteso mantenuto a mano.
4. Non sostituire `expectedMetricCount: 181` con una nuova costante `225`: `A2.2` deriva il perimetro dalla stessa materializzazione della release e valida i conteggi rispetto agli ID effettivi.
5. Il report futuro deve distinguere almeno `pubblicati`, `configurati`, `controllati` e `senza evidenza operativa`.
6. Nessun merge/pubblicazione senza Quick/Full pertinenti e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Verificare sulla PR `#194` il nuovo run Quick e il workflow `Controllo mensile dati` dopo il commit A2.2.
2. Se entrambi sono verdi, chiudere formalmente `A2.2` nella roadmap e passare ad `A2.3`.
3. `A2.3`: separare controllo leggero frequente e controllo profondo periodico senza duplicare il perimetro pubblico.

## Verifiche

- Main post-A1: `d498d2f931773cf8c30a8e051ccb340133d567a6`.
- Release pubblica: `v1.40.0`, 225 indicatori.
- Governance A1: `225 pubblicati = 225 Stato dati = 225 policy fonte`.
- Source registry sorgente: `expectedMetricCount=181`, `expectedInlineMetricCount=177`, `expectedExternalMetricCount=4`; questi valori non definiscono più il perimetro operativo del monitor A2.2.
- Snapshot monitor A2.2: materializzazione transazionale della stessa release pubblica, copia temporanea di `site-data.json` e `source-registry.json`, arresto prima di `build_static_safe.py`, ripristino del checkout.
- Stato operativo persistito: ultimo `checkedAt` generale `2026-08-31T17:19:31+02:00`; persistenza/freschezza completa resta nel perimetro A2.4.
