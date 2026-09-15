# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A1 — Data Governance Foundation`
- **Step attivo:** prima tranche A1 pronta per PR draft; `A1.1`–`A1.3` completati e verificati sul catalogo pubblico
- **Stato:** `IN_PROGRESS`
- **Baseline main:** `850fad77dc506d19f33351e092e926fa8fc3728a`
- **Catalogo sorgente / pubblico auditato:** 181 / 225 indicatori
- **Branch previsto:** `chore/a1-data-governance-foundation`
- **PR corrente:** da aprire in draft con deroga esplicita del proprietario al solo requisito di Quick locale letteralmente verde

## Completato

- `A0` chiuso con merge autorizzato della PR `#188`; foundation pubblicata.
- `A1.1`: audit documentato in `docs/A1_DATA_GOVERNANCE_AUDIT.md`.
- `A1.2`: formalizzato l'**Effective Public Catalog** come vista derivata `dist/data/site-data.json`, senza secondo catalogo canonico.
- `A1.3`: aggiunto il gate per identità degli ID tra catalogo pubblico e Stato dati e per policy fonte valida su ogni ID pubblicato.
- Verificata sulla release pubblica la relazione `225 ID pubblicati = 225 ID Stato dati = 225 policy fonte`.
- Confermato che la copertura temporale/operativa del monitor resta separata e va chiusa in `A2`.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Il catalogo effettivamente pubblicato è una vista derivata della build, non un manifest da mantenere a mano.
3. A1 controlla la copertura strutturale delle policy; A2 controlla esecuzione, freschezza e ultimo check delle fonti.
4. Regola generale: nessun push senza Quick locale verde. Eccezione una tantum autorizzata dal proprietario il 2026-09-15 per questa prima PR A1: il solo failure residuo è ambientale (`unpkg.com`/Leaflet nel test Percorsi) ed è stato isolato con prova causale. Nessun merge/pubblicazione senza ulteriore approvazione esplicita.

## Prossima azione esatta

1. Creare/pushare `chore/a1-data-governance-foundation` e aprire la PR tecnica **draft** contro `850fad77...`, usando la deroga esplicita già autorizzata.
2. Usare la CI della PR come verifica ufficiale dell'ambiente GitHub e registrare l'esito nell'handoff.
3. Prima della merge readiness eseguire `python scripts/preflight.py --full` oppure documentare qualsiasi failure esclusivamente ambientale rimasto.
4. Dopo la prima tranche A1 proseguire con `A1.4`, `A1.5`, `A1.6`, `A1.7` e `A1.8` senza introdurre inventari paralleli.

## Verifiche

- Modifiche della prima tranche A1: documentazione e gate di governance; nessuna modifica UI intenzionale.
- Il gate è inserito nel percorso esistente di `build_data_status.py`, già attraversato dal preflight generale.
- Sul `main` precedente il Quick ha materializzato 225 indicatori e il gate ha verificato `225 = 225 = 225`; i controlli finali di consistency e stemmi sono verdi.
- Il solo failure residuo è ambientale e fuori perimetro A1: Percorsi carica Leaflet da `unpkg.com`, irraggiungibile nel container; una prova con Leaflet locale ha confermato filtri e pagina funzionanti.
- Il merge radar #189 non modifica `data/site-data.json` né `data/source-registry.json`, quindi l'audit A1 resta valido.
- I numeri 181/225 documentano la baseline auditata e non devono diventare contatori hard-coded operativi.
