# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A3 — Enrichment Audit globale
- **Step attivo:** A3.5 — integrazione nuove dimensioni in lotti controllati
- **Stato:** IN_PROGRESS — lotti 1–7 mergiati; lotto 8 in lavorazione
- **Main verificato:** 5a6b7701c747dd99ed73754be485397e2df406eb (merge #266)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2:** 2.025 coppie; 2.025 classificate, 0 residue
- **Backlog A3.4 post-#266:** 767 AVAILABLE_MISSING · 259 pacchetti · 63 source profile
- **Branch corrente:** feat/a3-5-enrichment-lot-8
- **PR corrente:** da aprire — A3.5 lotto 8
- **Autorizzazione operativa corrente:** proseguire sui lotti non-visivi; fermarsi quando serve verifica visiva del proprietario

## A3.5 — acquisizioni mergiate

- **Lotto 1 / #260:** 3 coppie sesso.
- **Lotto 2 / #261:** 16 coppie OpenBDAP numeratore/denominatore.
- **Lotto 3 / #262:** 20 coppie Frame SBS.
- **Lotto 4 / #263:** 12 coppie Istat Census.
- **Lotto 5 / #264:** 34 coppie source-backed.
- **Lotto 6 / #265:** 13 coppie historical + MEF.
- **Lotto 7 / #266:** 7 serie storiche ARS legacy.

Totale acquisito nei lotti 1–7: **105 coppie**.

## Lotto 8 — official structural companions

Il lotto usa esclusivamente numeri ufficiali già versionati e non modifica valori, testi, grafici o renderer pubblici.

Target verificabile: **21 coppie**:
- **8 Istat lavoro:** sesso/età per `femaleEmploymentRate`, `maleEmploymentRate`, `employmentGenderGap`; categorie occupati/in cerca/inattivi per i due tassi per sesso;
- **10 AGCOM FTTH:** assoluto/normalizzato e categorie per quattro indicatori FTTH, più numeratore/denominatore per le due percentuali di copertura;
- **3 RGS:** assoluto/normalizzato + categorie assunzioni/cessazioni per `municipalStaffTurnover`; sesso per `municipalStaffTraining`.

Fonti congelate:
- `data/source-snapshots/istat-lavoro-istruzione-eta-genere-2024.json`;
- `data/source-snapshots/lia-v1.4.0.json` per la sola riconciliazione dei valori pubblici 2023;
- `data/source-snapshots/agid-asia-agcom-2026-08.json`;
- `data/source-snapshots/rgs-amministrazione-2024.json`;
- `data/source-snapshots/rgs-formazione-2024.json`.

Effetto atteso: **AVAILABLE_MISSING 767 → 746**. A3.5 resta `IN_PROGRESS`; A3.6 non parte.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale.
3. A3.2 resta strict a `unclassifiedPairCount = 0`.
4. `ACQUIRED` deriva solo da struttura/formula/evidenza verificabile, mai da override manuale.
5. Nessuna retro-derivazione di componenti mancanti dai valori pubblicati.
6. Una disponibilità dichiarata dalla fonte senza numeri versionati resta `AVAILABLE_MISSING`.
7. Nessuna modifica UI/rendering nei lotti enrichment puramente strutturali.

## Prossima azione esatta

1. Completare lotto 8 e aprire PR Ready.
2. Verificare sul final head A3, Quick e Full verdi.
3. Confermare matrice 2025/2025, `unclassifiedPairCount = 0` e 746 `AVAILABLE_MISSING`.
4. Correggere solo regressioni reali senza indebolire detector o contratti.
5. Merge soltanto dopo approvazione esplicita del proprietario.
6. Dopo il merge ripartire dal backlog LIVE; non iniziare A3.6 finché A3.5 non è realmente chiuso.
