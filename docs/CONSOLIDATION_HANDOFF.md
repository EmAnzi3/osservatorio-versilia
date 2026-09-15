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
- **PR corrente:** da aprire

## Completato

- `A0` chiuso con merge autorizzato della PR `#188`.
- `A1.1`–`A1.3` chiusi con merge autorizzato della PR `#190`.
- `A1.4`–`A1.8` chiusi con merge della PR `#193`; Quick e Full GitHub verdi.
- Deploy post-merge della PR `#193`: Pages `#3219` verde; controllo live-status successivo verde.
- `A1 — Data Governance Foundation` è formalmente `DONE`.
- `A2.1` completato e documentato in `docs/A2_SOURCE_MONITOR_AUDIT.md`.
- Audit A2.1: il monitor mensile usa il catalogo sorgente e il registry `181/177/4`, mentre l'Effective Public Catalog contiene 225 indicatori.
- L'audit A1 aveva rilevato 180 ID nello stato operativo contro 225 pubblicati: gap operativo di 45 ID, pur con 225/225 policy fonte strutturalmente valide.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. L'Effective Public Catalog resta una vista derivata della build; non va copiato in un secondo manifest manuale.
3. A2 deve misurare la copertura operativa per identità degli ID pubblicati, non tramite un numero atteso mantenuto a mano.
4. Non sostituire `expectedMetricCount: 181` con una nuova costante `225`: `A2.2` deve derivare il perimetro dal catalogo effettivamente monitorato.
5. Il report futuro deve distinguere almeno `pubblicati`, `configurati`, `controllati` e `senza evidenza operativa`.
6. Nessun merge/pubblicazione senza Quick/Full pertinenti e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Implementare `A2.2`: portare il monitor sul perimetro dell'Effective Public Catalog senza duplicare la catena di materializzazione.
2. Eliminare dal percorso operativo i conteggi hard-coded quando derivabili dagli ID del dataset monitorato.
3. Aggiungere test che dimostrino che un ID pubblico non coperto non può passare silenziosamente.
4. Eseguire Quick; aprire/aggiornare la PR A2 e usare GitHub Actions come verifica ulteriore.

## Verifiche

- Main post-A1: `d498d2f931773cf8c30a8e051ccb340133d567a6`.
- Release pubblica: `v1.40.0`, 225 indicatori.
- Governance A1: `225 pubblicati = 225 Stato dati = 225 policy fonte`.
- Source registry sorgente: `expectedMetricCount=181`, `expectedInlineMetricCount=177`, `expectedExternalMetricCount=4`.
- Workflow mensile: prima del monitor materializza soltanto PNRR e invoca `monthly_data_check_status.py` senza override di `--data`/`--registry`.
- Stato operativo persistito: ultimo `checkedAt` generale `2026-08-31T17:19:31+02:00`.
