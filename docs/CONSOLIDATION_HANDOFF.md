# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A3 — Enrichment Audit globale
- **Step attivo:** A3.5 — integrazione nuove dimensioni in lotti controllati
- **Stato:** IN_PROGRESS — lotti 1, 2 e 3 mergiati; lotto 4 Istat Census components sul branch dedicato
- **Main verificato:** 2b5815a9513237d1c44e71e03a30a5fdd595b255 (merge #262)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2:** 2.025 coppie; 2.025 classificate, 0 residue
- **Backlog A3.4 post-#262:** 833 AVAILABLE_MISSING · 263 pacchetti · 63 source profile
- **Branch corrente:** feat/a3-5-enrichment-lot-4
- **Merge/pubblicazione:** richiedono A3 + Quick + Full GREEN sul final head e autorizzazione del proprietario

## A3.5 — acquisizioni

- **Lotto 1 / #260:** 3 coppie sesso da snapshot Istat demografici.
- **Lotto 2 / #261:** 16 coppie OpenBDAP numeratore/denominatore da snapshot OpenBDAP/SIOPE.
- **Lotto 3 / #262:** 20 coppie Frame SBS: 8 categorie specifiche, 8 assoluto/normalizzato, 4 numeratore/denominatore. Backlog confermato a 833.

### Lotto 4 — branch corrente

Il lotto riusa data/source-snapshots/istat-sections-history-v1.8.0.json, già versionato e già usato per verificare le serie censuarie 2021–2023.

Sei indicatori dispongono dei componenti grezzi 2023 necessari:
femaleEmploymentRate, maleEmploymentRate, housingStockPer1000, nonOccupiedHomesPer1000, vacantHomes e singleHouseholds.

La struttura censusRatioComponents deve acquisire 12 coppie:
- 6 × numeratore_denominatore;
- 6 × assoluto_normalizzato.

I valori pubblici restano invariati e vengono soltanto riconciliati con i componenti ufficiali. Effetto atteso:

AVAILABLE_MISSING: 833 → 821

A3.5 resta IN_PROGRESS; A3.6 non parte.

## Decisioni vincolanti

1. data/site-data.json resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale di indicatori, fonti o opportunità.
3. A3.2 resta strict a unclassifiedPairCount = 0.
4. Un passaggio a ACQUIRED deve derivare da struttura/formula verificabile, mai da override manuale.
5. A3.5 procede per lotti sostanziali ricavati dal backlog A3.4, con QA e fonte dichiarata.
6. Non introdurre UI/rendering se il lotto riguarda soltanto enrichment del dataset.
7. Non retro-derivare componenti mancanti da percentuali/rapporti già pubblicati.

## Prossima azione esatta

1. Aprire la PR Ready del lotto 4.
2. Verificare A3 + Quick + Full sullo stesso final head.
3. Confermare dall'artifact A3.4 821 AVAILABLE_MISSING e unclassifiedPairCount = 0.
4. Correggere soltanto regressioni reali, senza indebolire detector o contratti.
5. Se i gate sono verdi, procedere secondo l'autorizzazione del proprietario e ripartire dal backlog LIVE.
