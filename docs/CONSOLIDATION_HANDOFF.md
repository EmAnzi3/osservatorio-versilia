# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Workstream A3 benchmark attivo — PR #304

- Branch `feat/a3-benchmark-available-missing`, base `fix/a3-enrichment-publication-gap`; **OPEN/DRAFT**, non mergiare né Ready. A5 resta congelata.
- **Certificato corrente:** run `37025847458`, head `e4af73b5af76071ac2c435cdc7ff0de51725fb3a`: **129/129 benchmark pubblici, 0 gap, 84 AVAILABLE_MISSING su 38 profili, 98 chiusi** rispetto alla baseline 182. `benchmark-backlog` SUCCESS effettivo, non skipped; build, regressione matrice, publication audit, backlog e residual audit SUCCESS.
- Artifact `11234888793` scaricato e letto (backlog e residual closure JSON/Markdown): **84 residui, 84 blocchi documentati, zero diagnosi generiche**, `closureReady=false`. **A3 NON CHIUSA**: una diagnosi non è un’acquisizione né prova di esaurimento delle fonti.
- **Dieci nuovi ACQUIRED rispetto a 119:** redditi reali MEF 2016–2024 (+1,1133958655% Toscana / +1,8557286489% Italia, stesso NIC pubblico); capacità Istat 2024 (posti letto e due rapporti); sei confronti di pendolarismo Istat 2021 (entrate, uscite, saldo e tre tassi). Tutti 7/7 riconciliati, tutte le righe numeriche comunali invariate.
- Redditi: pannelli MEF completi, veri anni d’imposta verificati, medie da somme imponibile/frequenze; righe nazionali senza Comune esplicitamente incluse. Nessun campo mancante imputato. Capacità: 7.899 record nativi / 273 Toscana, 107/107 province e totale Italia riconciliati, aggregati esclusi dalla somma comunale. Worker dedicati PASS `37023510189`, gate pubblico `37023511530` (123/123, 90 residui).
- **Correzione fonte/periodo capacità:** i due tassi etichettati 2025 coincidevano esattamente 7/7 con conteggi Istat 2024 / popolazione pubblica 1° gennaio 2026. Corretti fonte/anno e dichiarato il denominatore; valori comunali invariati. Il perimetro ampliato dal 2025 non entra nel 2024.
- **Pendolarismo:** dataflow `ONLY_FILE`, archivio ufficiale di 523.949 flussi unici, 7.904 origini / 7.903 destinazioni, 273 Comuni toscani. Toscana entrate 641.790, uscite 643.052, saldo −1.262; Italia entrate = uscite 9.762.022, saldo zero verificato per conservazione dei flussi, non imputazione. I due tassi di entrata/uscita usano popolazione 2026; il tasso saldo usa P02 1° gennaio 2021, 7.904 Comuni e maschi + femmine = totale in ogni record (Toscana 3.692.865 / Italia 59.236.213), denominatori esatti 7/7. `outsideMunicipality` ancora non riconciliato. **Diagnosi autocontenimento corretta:** rapporto flussi interni / (interni + uscite) riconciliato esattamente 7/7 al decimale pubblico, candidato aggiuntivo PASS (Toscana 51,6171943% / Italia 50,1067270%). Fonte e descrizione rendono esplicita la popolazione della matrice; nessun valore comunale cambiato. Attendere gate prima di ACQUIRED.
- Worker pendolarismo PASS `37024641519` e `37025847391`; gate intermedi `37024640873` (128/128, 85 residui) e corrente sopra. Fan-in `37025847946` SUCCESS; idempotenza semantica locale verificata. Il fan-out conserva il riferimento 128/128 per l’ultima acquisizione, non sostituisce la certificazione corrente 129/129. Evitare replay storici e gate pesanti per soli contatori/diagnosi/docs.
- **OpenBDAP:** ultimo archivio live ancora 271/273 in tutti e quattro i CSV; assenti Villafranca in Lunigiana (`045016`) e Marradi (`048026`). Rendiconti ufficiali individuati ma accesso bloccato (502 Marradi, CAPTCHA Villafranca): nessun valore estratto, nessun aggregato parziale. 19 blocchi di copertura e 5 di definizione distinti. Restano 22 compositi incompatibili con il contratto di benchmark scalare: nessuna coercizione.
- **MIM approfondimento:** anagrafi 2024/25 statali/paritarie rilette con hash. Codici statali coincidono 5/7 (Viareggio 52 vs 49, Seravezza 14 vs 13). Nomi, indirizzo/ordine e corsi adulti non danno una definizione unica riconciliata 7/7; nessuna eccezione comunale né totale candidato.
- **ACI:** individuato archivio ufficiale Autoritratto 2024 distinto dal workbook urbano Istat del probe precedente. Landing e ZIP restituiscono HTTP 503 nel runtime; non prova di indisponibilità o assenza di dettaglio comunale. Acquisire e riconciliare quel pannello prima di aggregare.
- **Censimento completo verificato:** ZIP 189.148.593 byte, CSV 4.606.220.349 byte, 17.683.842 righe lette integralmente con CRC ZIP e hash. Per Italia, Toscana e sette Comuni RP_COM_DAY contiene 2018/2019, non 2021. I rapporti fuori Comune di entrambi gli anni non riconciliano il pubblico; nessuna sostituzione d’anno o complemento dell’autocontenimento. Evidenza e componenti 7/7 registrati.
- **QA:** contratti sorgente/dati, periodi/componenti, regressione matrice e rifiuto di duplicati, mancanti, booleani, unità errate e aggregati incoerenti PASS. Quick eseguito prima dei push; prerender locale bloccato da Chromium assente nel runtime. Certificazione pubblica completata su GitHub senza indebolire i gate. Nessun golden/UI A5 modificato.
- **Prossima azione tecnica:** quote censuarie nel dataflow separato `DF_DCSS_ISTR_LAV_PEN_2_TV_5` e allegato `DCSS_BULK_ISTR_LAV_PEN_2`; ACI completo; copertura OpenBDAP; fotografie storiche GTFS/Salute; definizione MIM. Acquisire soltanto con periodo, definizione, perimetro e componenti 7/7 certificati. Non chiudere A3 sulla sola base dei blocchi documentati.

## Stato A5 congelato

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** A5 — Design System 2.0
- **Step attivo:** A5.5 — propagazione progressiva DS2
- **Stato:** DONE tecnicamente — chiusura formale A5 sospesa soltanto fino ad approvazione esplicita e merge della PR #280
- **Main incorporato:** `46a31d3ca60717827ac92c709349b0c77355c3b4`
- **Merge di allineamento main:** `bde1c5ab82f85c6655908cd3002139caddc6245b`
- **Checkpoint UI approvato:** `bc9e5086aa796637828e1a5ae6e9952873024ef7`
- **Commit closure docs/scope:** `6fa94b4a569d5ee90b24fd061e3aeae379546162`
- **Branch:** `feat/a5-controlled-iteration`
- **PR:** #280 — Draft, OPEN, non mergiata
- **A0–A4:** DONE
- **A5.1–A5.5:** DONE tecnicamente
- **A6:** NOT_STARTED

## Contratti congelati

I contratti approvati sono documentati in `docs/A5_GOLDEN_MASTERS.md`.

- 11 pagine tematiche standard DS2 consolidate.
- 7 schede comunali consolidate sul renderer parametrico condiviso.
- Camaiore completa protetta dal checkpoint `5aaf159870912eb49bffbd044963549bfb920150`.
- Viareggio/Massarosa Demografia restano protette dal golden lock storico.
- Navigazione Comuni e Home “Esplora per territorio” in ordine alfabetico: Camaiore, Forte dei Marmi, Massarosa, Pietrasanta, Seravezza, Stazzema, Viareggio.
- Route speciali mantenute come eccezioni intenzionali: `meteo-clima`, Atlante attività economiche, Affluenza.

## Closure audit route speciali

- **Meteo/clima:** workspace specializzato; shell canonica e gate clima dedicati.
- **Atlante attività economiche:** web component autonomo con browser contract dedicato desktop/tablet/mobile.
- **Affluenza:** archivio/event selector specifico; token/componenti canonici e responsive dedicato.

Nessuna delle tre route richiede un rollout forzato nello shell standard A5.

## Prossima azione esatta

1. Attendere e verificare che tutti i gate della PR siano verdi sul nuovo head di closure.
2. Se verdi, fermarsi e chiedere al proprietario autorizzazione esplicita a rendere #280 Ready e mergiarla.
3. Solo dopo il merge: segnare A5 `DONE` e avviare A6.1 — modello semantico minimo.

Non aggiornare golden/baseline per ottenere verde e non mergiare senza approvazione esplicita.
