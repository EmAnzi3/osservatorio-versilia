# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A2 — Full Coverage Source Monitor`
- **Step attivo:** `A2.4` — strategia verificabile per ogni fonte
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `d498d2f931773cf8c30a8e051ccb340133d567a6`
- **Catalogo sorgente / pubblico auditato:** 181 / 225 indicatori
- **Perimetro monitor pubblico verificato:** 225 indicatori / 122 fonti
- **Branch:** `chore/a2-source-monitor-foundation`
- **PR corrente:** `#194` — draft

## Completato

- `A0` chiuso con merge autorizzato della PR `#188`.
- `A1.1`–`A1.3` chiusi con merge autorizzato della PR `#190`.
- `A1.4`–`A1.8` chiusi con merge della PR `#193`; Quick e Full GitHub verdi.
- Deploy post-merge della PR `#193`: Pages `#3219` verde; controllo live-status successivo verde.
- `A1 — Data Governance Foundation` è formalmente `DONE`.
- `A2.1` completato e documentato in `docs/A2_SOURCE_MONITOR_AUDIT.md`.
- `A2.2` verificato: `materialize_source_monitor_snapshot.py` riusa la catena della build pubblica e si arresta prima del prerender; il monitor riceve lo snapshot derivato v1.40.0 con 225 indicatori, 221 inline, 4 esterni e 69 source profile.
- Il run `Controllo mensile dati #615` ha validato il perimetro A2.2: 225 indicatori, 122 fonti, 0 errori strutturali.
- `A2.3` implementato: workflow giornaliero read-only `Controllo frequente fonti` in modalità `light`, mentre il controllo mensile resta `deep`.
- Il primo run light `#1` è verde: 225 indicatori, 122 fonti, 0 errori strutturali; unit test `light/deep` verde e artifact diagnostico prodotto.
- Il Pages Quick `#3224` ha bloccato correttamente il nuovo workflow perché non era ancora dichiarato in `ci/workflow-contract.json`; la correzione consiste esclusivamente nell'aggiungerlo all'inventario workflow, senza indebolire il gate.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. L'Effective Public Catalog resta una vista derivata della build; non va copiato in un secondo manifest manuale.
3. A2 misura la copertura operativa per identità degli ID pubblicati, non tramite un numero atteso mantenuto a mano.
4. Non sostituire `expectedMetricCount: 181` con una nuova costante `225`: il perimetro operativo è derivato dalla stessa materializzazione della release.
5. Il controllo `light` è frequente, read-only e diagnostico: niente hash dei contenuti, niente verifiche semantiche PNRR/MIMIT, niente scrittura di baseline/issue/PR.
6. Il controllo `deep` resta periodico e conserva hash, confronti di contenuto e verifiche semantiche disponibili.
7. `A2.4` deve derivare una strategia per ogni fonte dal catalogo pubblico, registry e stato operativo esistenti; non va introdotto un manifest manuale parallelo.
8. Nessun merge/pubblicazione senza Quick/Full pertinenti e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Verificare il Quick dopo l'allineamento di `ci/workflow-contract.json` con `source-monitor-light.yml`.
2. Proseguire con `A2.4`: per ciascuna delle 122 fonti derivare frequenza attesa, modalità di rilevazione del cambiamento e ultimo controllo riuscito.
3. Usare la stessa vista derivata come base per `A2.5` e `A2.7`, evitando nuove tabelle manuali di copertura.

## Verifiche

- Main post-A1: `d498d2f931773cf8c30a8e051ccb340133d567a6`.
- Release pubblica: `v1.40.0`, 225 indicatori.
- Governance A1: `225 pubblicati = 225 Stato dati = 225 policy fonte`.
- A2.2 deep PR run `#615`: `metrics=225`, `sources=122`, `errors=0`.
- A2.3 light PR run `#1`: `metrics=225`, `sources=122`, `errors=0`; `Source monitor depth: light`.
- Il risultato `changes=45` nei run PR/offline è la transizione dalla vecchia baseline operativa incompleta al perimetro pubblico completo, non un errore strutturale.
- Stato operativo persistito su `main`: ultimo `checkedAt` generale `2026-08-31T17:19:31+02:00`; persistenza/freschezza per fonte è il perimetro di `A2.4`.
