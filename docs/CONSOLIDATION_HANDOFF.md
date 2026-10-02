# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Workstream A3 benchmark attivo — PR #304

- Branch `feat/a3-benchmark-available-missing`, base `fix/a3-enrichment-publication-gap`; **OPEN/DRAFT**, non mergiare né Ready. A5 resta congelata.
- **Certificato corrente:** run `37048901904`, head `58e1d926665cfe1c4541e87f9b4dbde8fc1e6faf`: **132/132 benchmark pubblici, 0 gap, 81 AVAILABLE_MISSING su 37 profili, 101 chiusi** rispetto alla baseline 182. `benchmark-backlog` SUCCESS effettivo, non skipped; build, regressione matrice, publication audit, backlog e residual audit SUCCESS.
- Artifact `11245134888` scaricato e letto (backlog e residual closure JSON/Markdown): **81 residui, 81 blocchi documentati, zero diagnosi generiche**, `closureReady=false`. **A3 NON CHIUSA**: una diagnosi non è un’acquisizione né prova di esaurimento delle fonti.
- **Tredici nuovi ACQUIRED rispetto a 119:** redditi reali MEF 2016–2024 (+1,1133958655% Toscana / +1,8557286489% Italia, stesso NIC pubblico); capacità Istat 2024 (posti letto e due rapporti); sette confronti di pendolarismo Istat 2021 (entrate, uscite, saldo, tre tassi e autocontenimento); quota micro unità locali ASIA-UL 2023; reddito medio imponibile MEF 2024. Tutti 7/7 riconciliati, tutte le righe numeriche comunali invariate.
- Redditi: pannelli MEF completi, veri anni d’imposta verificati, medie da somme imponibile/frequenze; righe nazionali senza Comune esplicitamente incluse. Nessun campo mancante imputato. Capacità: 7.899 record nativi / 273 Toscana, 107/107 province e totale Italia riconciliati, aggregati esclusi dalla somma comunale. Worker dedicati PASS `37023510189`, gate pubblico `37023511530` (123/123, 90 residui).
- **Correzione fonte/periodo capacità:** i due tassi etichettati 2025 coincidevano esattamente 7/7 con conteggi Istat 2024 / popolazione pubblica 1° gennaio 2026. Corretti fonte/anno e dichiarato il denominatore; valori comunali invariati. Il perimetro ampliato dal 2025 non entra nel 2024.
- **Pendolarismo:** dataflow `ONLY_FILE`, archivio ufficiale di 523.949 flussi unici, 7.904 origini / 7.903 destinazioni, 273 Comuni toscani. Toscana entrate 641.790, uscite 643.052, saldo −1.262; Italia entrate = uscite 9.762.022, saldo zero verificato per conservazione dei flussi, non imputazione. I due tassi di entrata/uscita usano popolazione 2026; il tasso saldo usa P02 1° gennaio 2021, 7.904 Comuni e maschi + femmine = totale in ogni record (Toscana 3.692.865 / Italia 59.236.213), denominatori esatti 7/7. `outsideMunicipality` ancora non riconciliato. **Diagnosi autocontenimento corretta:** rapporto flussi interni / (interni + uscite) riconciliato esattamente 7/7 al decimale pubblico, candidato aggiuntivo PASS (Toscana 51,6171943% / Italia 50,1067270%). Fonte e descrizione rendono esplicita la popolazione della matrice; nessun valore comunale cambiato. Gate corrente PASS: autocontenimento ACQUIRED.
- Worker pendolarismo PASS `37024641519` e `37025847391`; gate intermedi `37024640873` (128/128, 85 residui) e `37025847458` (129/129, 84 residui); gate corrente sopra. Fan-in `37025847946` SUCCESS; idempotenza semantica locale verificata. Worker autocontenimento `37028478378` e fan-in `37028478045` SUCCESS. Il fan-out conserva il riferimento 129/129 per l’ultima acquisizione, non sostituisce la certificazione corrente sopra. Evitare replay storici e gate pesanti per soli contatori/diagnosi/docs.
- **ASIA-UL ACQUIRED:** `microUnits` riconciliato 7/7 con conteggi nativi 2023 W0_9 e TOTAL; Toscana 344.514/366.636 = 93,9662226%, Italia 4.847.158/5.144.482 = 94,2205260%. Denominatori identici ai livelli UL già certificati. Snapshot con CSV/hash/query per tutte le nove aree e pannello completo di 7.900 Comuni (273 toscani), somme identiche agli aggregati nativi per entrambe le classi; valori comunali invariati. Gate corrente PASS; worker `37047843587` e fan-in `37047843533` SUCCESS. Artifact worker `11244888532` letto: pannello 7.900/7.900, componenti 9/9 e benchmark identici al congelato locale. L’allegato ONLY_FILE occupazione contiene posizioni lavorative, non conteggi UL: non usato come proxy.
- **MEF imponibile ACQUIRED:** `income` 7/7 al centesimo con ammontare/frequenza imponibile 2024 del pannello completo già certificato per redditi reali; 7.897 record nazionali inclusa localizzazione non disponibile esplicita, 273 toscani. Toscana 67.730.328.839/2.691.349 = 25.165,9405 €, Italia 1.013.394.277.109/40.709.947 = 24.893,0385 €. Nessun valore comunale cambiato; nessuna media delle medie e nessun reddito complessivo usato. Gate pubblico corrente SUCCESS; worker `37048901707` e fan-in `37048901639` SUCCESS. Artifact worker `11245760874` letto: candidato identico al congelato locale.
- **OpenBDAP:** ultimo archivio live ancora 271/273 in tutti e quattro i CSV; assenti Villafranca in Lunigiana (`045016`) e Marradi (`048026`). Rendiconti ufficiali individuati ma accesso bloccato (502 Marradi, CAPTCHA Villafranca): nessun valore estratto, nessun aggregato parziale. 19 blocchi di copertura e 5 di definizione distinti. Restano 22 compositi incompatibili con il contratto di benchmark scalare: nessuna coercizione.
- **MIM approfondimento:** anagrafi 2024/25 statali/paritarie rilette con hash. Codici statali coincidono 5/7 (Viareggio 52 vs 49, Seravezza 14 vs 13). Nomi, indirizzo/ordine e corsi adulti non danno una definizione unica riconciliata 7/7; nessuna eccezione comunale né totale candidato.
- **ACI:** individuato archivio ufficiale Autoritratto 2024 distinto dal workbook urbano Istat del probe precedente. Landing e ZIP restituiscono HTTP 503 nel runtime; non prova di indisponibilità o assenza di dettaglio comunale. Archivio ufficiale Open Data 2024 alternativo ancora 503. Portale OPV e query categorie/dimensioni 200; anni timeout, launcher pubblico 2024/AV 401. Nessun pannello comunale estratto. Acquisire e riconciliare i conteggi prima di aggregare.
- **Censimento completo verificato:** ZIP 189.148.593 byte, CSV 4.606.220.349 byte, 17.683.842 righe lette integralmente con CRC ZIP e hash. Per Italia, Toscana e sette Comuni RP_COM_DAY contiene 2018/2019, non 2021. I rapporti fuori Comune di entrambi gli anni non riconciliano il pubblico; nessuna sostituzione d’anno o complemento dell’autocontenimento. Evidenza e componenti 7/7 registrati.
- **QA:** contratti sorgente/dati, periodi/componenti, regressione matrice e rifiuto di duplicati, mancanti, booleani, unità errate e aggregati incoerenti PASS. Quick eseguito prima dei push; prerender locale bloccato da Chromium assente nel runtime. Certificazione pubblica completata su GitHub senza indebolire i gate. Nessun golden/UI A5 modificato.
- **PAB nativo:** sei consorzi / sette PDF 2026 acquisiti tramite API della banca dati regionale, hash CB1 identico alla fonte pubblica. A-1 CB1: 5.328 codici E/P unici, 16.119.754,60 €, conteggi e importi 7/7 esatti. Corretta la formula documentata E/P; valori comunali invariati. Pannello/atti/hash congelati in `a3-pab-native-source-verification-2026.json`. Nessun benchmark candidato: granularità/deduplicazione degli altri consorzi e perimetro nazionale ancora da certificare.
- **Prossima azione tecnica:** certificare A-1 omogenei degli altri consorzi e fonte nazionale; provenienza pubblica di `outsideMunicipality`; ACI completo; copertura OpenBDAP; fotografie storiche GTFS/Salute; definizione MIM. Acquisire soltanto con periodo, definizione, perimetro e componenti 7/7 certificati. Non chiudere A3 sulla sola base dei blocchi documentati.

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
