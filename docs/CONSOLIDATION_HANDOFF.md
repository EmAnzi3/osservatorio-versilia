# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A3 — Enrichment Audit globale
- **Step attivo:** A3.5 — integrazione nuove dimensioni in lotti controllati
- **Stato:** IN_PROGRESS — lotti 1–6 mergiati; lotto 7 ARS legacy history in PR #266
- **Main verificato:** eaf4b9079d45aedd00a5c53ac27c68de68258b37 (merge #265)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2:** 2.025 coppie; 2.025 classificate, 0 residue
- **Backlog A3.4 post-#265:** 774 AVAILABLE_MISSING · 260 pacchetti · 63 source profile
- **Branch corrente:** feat/a3-5-enrichment-lot-7
- **PR corrente:** #266 — A3.5: acquire legacy ARS historical series
- **Autorizzazione operativa corrente:** proseguire sui lotti non-visivi; fermarsi quando serve verifica visiva del proprietario

## A3.5 — acquisizioni

- **Lotto 1 / #260:** 3 coppie sesso.
- **Lotto 2 / #261:** 16 coppie OpenBDAP numeratore/denominatore.
- **Lotto 3 / #262:** 20 coppie Frame SBS.
- **Lotto 4 / #263:** 12 coppie Istat Census.
- **Lotto 5 / #264:** 34 coppie source-backed.
- **Lotto 6 / #265:** 13 coppie historical + MEF; backlog confermato a 774.

Totale acquisito nei lotti 1–6: **98 coppie**.

### Lotto 7 — PR #266

Il lotto congela e versiona gli export ufficiali ARS Toscana e aggiunge esclusivamente una struttura `a3History` non consumata dal renderer.

Acquisizioni:
- 7 × `serie_storica` per `chronicTotal`, `dementia`, `diabetes`, `elderlyHomeCare`, `emergencyAccess`, `hospitalizedAll`, `mortalityAll`;
- serie da 9 a 16 periodi a seconda dell'indicatore, validate sui 7 Comuni e sull'aggregato ufficiale Zona Versilia;
- per `mortalityAll` ARS espone anche il periodo 2014–2023, ma il catalogo pubblico è ancora 2013–2022: A3.5 congela lo storico fino al periodo pubblicato e non anticipa il normale refresh della fonte.

Effetto atteso: `AVAILABLE_MISSING: 774 → 767`.

Il lotto non modifica valori, testi, grafici o rendering pubblici. A3.5 resta `IN_PROGRESS`; A3.6 non parte.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale.
3. A3.2 resta strict a `unclassifiedPairCount = 0`.
4. `ACQUIRED` deriva solo da struttura/formula/evidenza verificabile, mai da override manuale.
5. Nessuna retro-derivazione di componenti mancanti dai valori pubblicati.
6. Una disponibilità dichiarata dalla fonte senza numeri versionati resta `AVAILABLE_MISSING`.
7. Nessuna modifica UI/rendering nei lotti enrichment puramente strutturali.

## Prossima azione esatta

1. Verificare sul final head della PR #266: A3, Quick e Full verdi.
2. Confermare matrice 2025/2025, `unclassifiedPairCount = 0` e 767 `AVAILABLE_MISSING`.
3. Correggere solo regressioni reali senza indebolire detector o contratti.
4. Se tutti i gate sono verdi, merge secondo l'autorizzazione corrente.
5. Dopo il merge ripartire dal backlog LIVE; non iniziare A3.6 finché A3.5 non è realmente chiuso.
