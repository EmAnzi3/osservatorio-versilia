# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A3 — Enrichment Audit globale
- **Step attivo:** A3.5 — integrazione nuove dimensioni in lotti controllati
- **Stato:** IN_PROGRESS — lotti 1–4 mergiati; lotto 5 source-backed companions sul branch dedicato
- **Main verificato:** b6d6196443ddae826244bdeefdf291dd5d41322d (merge #263)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2:** 2.025 coppie; 2.025 classificate, 0 residue
- **Backlog A3.4 post-#263:** 821 AVAILABLE_MISSING · 263 pacchetti · 63 source profile
- **Branch corrente:** feat/a3-5-enrichment-lot-5
- **Autorizzazione operativa corrente:** proseguire sui lotti non-visivi; fermarsi quando serve verifica visiva del proprietario

## A3.5 — acquisizioni

- **Lotto 1 / #260:** 3 coppie sesso.
- **Lotto 2 / #261:** 16 coppie OpenBDAP numeratore/denominatore.
- **Lotto 3 / #262:** 20 coppie Frame SBS.
- **Lotto 4 / #263:** 12 coppie Istat Census; backlog confermato 821.

### Lotto 5 — branch corrente

Il lotto usa esclusivamente strutture e snapshot già versionati. Non modifica valori, testi, grafici o rendering pubblici.

Acquisizioni attese:
- 16 × OpenBDAP assoluto/normalizzato dai ratioComponents già governati;
- 4 × Census (cohabitingHouseholds e oldAgeIndex);
- 4 × Agricoltura (tre indicatori);
- 10 × Business (cinque indicatori).

Totale: 34 coppie. Effetto atteso:

AVAILABLE_MISSING: 821 → 787

Per i due indicatori di variazione ASIA il valore assoluto è il delta 2023−2018; non viene usato il livello finale come falso assoluto. householdSize resta escluso per mancata riconciliazione sufficiente.

A3.5 resta IN_PROGRESS; A3.6 non parte.

## Decisioni vincolanti

1. data/site-data.json resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale.
3. A3.2 resta strict a unclassifiedPairCount = 0.
4. ACQUIRED deriva solo da struttura/formula verificabile, mai da override manuale.
5. Nessuna retro-derivazione di componenti mancanti dai valori pubblicati.
6. Nessuna modifica UI/rendering nei lotti enrichment puramente strutturali.

## Prossima azione esatta

1. Aprire la PR Ready del lotto 5.
2. Verificare A3 + Quick + Full sullo stesso final head.
3. Confermare 787 AVAILABLE_MISSING e 0 residue.
4. Correggere solo regressioni reali senza indebolire detector o contratti.
5. Se i gate sono verdi, merge secondo l'autorizzazione corrente e ripartenza dal backlog LIVE.
