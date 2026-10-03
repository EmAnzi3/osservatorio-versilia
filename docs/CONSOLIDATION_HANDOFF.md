# Consolidamento Osservatorio Versilia — handoff operativo

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento.

## Estensione Istat autorizzata — 03-10-2026

- Branch `feat/a3-istat-history-extension`, base #320 head `6af5bd8`. #319/#320 Quick/Full/preview GitHub SUCCESS verificati (run `37136866117` e `37137911225`); #320 certifica 118/118 storici e 137/137 benchmark. Tutte le PR restano DRAFT/non mergiate. A5 congelata.
- Il proprietario autorizza espressamente i cinque storici Istat, inclusi i calcoli semplici già adottati dal sito, ed esclude ACI. Il vecchio termine delle ricerche del lotto semplice non impedisce questa estensione specifica; non riaprire altri indicatori.
- Acquisito `diplomaPlus`: CSV ufficiali 8milaCensus, 7/7 Comuni, percentuali 1991/2001/2011; lettura 25–64 anni Totale, affiancata al valore pubblico 2024 invariato. Snapshot conserva bytes, SHA, URL e tutte le righe native. Nota esplicita censimento tradizionale/permanente e osservazioni sparse, senza interpolazione. Nessun aggregato storico Versilia inventato da percentuali senza denominatori.
- Workbook ufficiali A misura di Comune: occupazione/disoccupazione/attività 15 anni e più (2019, 2021–2023), diploma e terziario 25–49 (2018–2023), Totale e 7/7 Comuni. Attività = 100 − inattività, unica trasformazione semplice. Collegamento alle componenti esistenti e al 2024 invariato, senza sostituire la lettura base 25–64. Estratti nativi, intestazioni, definizioni e SHA conservati nello snapshot.
- Le richieste SDMX 25–49/50–64 restano bloccate dopo tentativi mirati 150 secondi e comunali 60 secondi tutti timeout. Interrompere questi tentativi e le ulteriori ricerche: i workbook direttamente disponibili soddisfano il lotto.
- Materializzatore atomico/idempotente e riconciliazione dei valori correnti; selezioni senza storico non ereditano il totale. Nessun aggregato storico Versilia da percentuali senza denominatori.
- Acquisizione del lotto conclusa: 123/123 indicatori con storico pubblico e 137/137 benchmark verificati; 119 storici nella lettura base e quattro aggiuntivi nelle componenti selezionabili. 35 serie comunali XLS più sette serie diploma 25–64. Valori/numeratori/denominatori correnti preservati; idempotenza, 15 negativi atomici e 13 negativi di pubblicazione PASS. Browser 44 casi desktop/mobile, confronto e Comune, incluse note/fonti, disponibilità, valori correnti e perimetro dei benchmark PASS. La vista iniziale indica la selezione che dispone dello storico.
- Quick locale eseguito sulla build pulita con dipendenze browser del progetto: sorgenti/build non mutante, pubblicazione, grafici, governance, PNRR e 105 fisarmoniche PASS. Arresto al limite Percorsi già noto (Leaflet CDN non disponibile, filtro URL all invece di trekking); Quick completo non dichiarato verde. Coerenza finale 250 pagine e 7/7 stemmi PASS separati; regressione visiva 40/40 baseline PASS con le dipendenze browser del progetto, senza modificare soglie o golden. Certificazione GitHub/preview da verificare sulla PR DRAFT del branch; nessun Ready/merge/deploy autorizzato. Non riaprire ricerche né ricostruzioni.

## Fase A3 benchmark — consolidamento finale, PR #304

- Branch `feat/a3-benchmark-available-missing`, base `fix/a3-enrichment-publication-gap`, PR #304 **OPEN/DRAFT**, non mergiata. A5 resta congelata.
- **Perimetro concordato il 03-10-2026:** usare gli storici già disponibili. Per Toscana/Italia acquisire solo valori ufficiali direttamente fruibili. Interrompere ricostruzioni territoriali, recuperi storici onerosi e calcolo di aggregati mancanti. La fase non richiede azzerare i residui o dimostrare esaurimento delle fonti.
- **Certificato dati:** run `37117443259`, head `f981ef97810872e014dc5c3287c7de145431d06a`; build/matrice/publication/backlog/residual SUCCESS effettivi. **137/137 benchmark pubblici, 111/111 storici pubblici, zero gap; 76 AVAILABLE_MISSING su 35 profili, 106 chiusi dalla baseline 182.**
- Artifact dati `11272062994` scaricato, quattro report letti integralmente, SHA `6f6ff3e8bb7238f9554f347b885157e8b37dd14ab94472dcd26ef74d6163cb23` e CRC verificati. Matrice strict 225 × 9 = 2.025 coppie, tutte classificate; 76 blocchi documentati e zero da auditare. Il `closureReady=false` del residual audit riguarda l’acquisizione esaustiva, fuori dal perimetro concordato; nessuno stato della matrice viene alterato per dichiarare una chiusura.
- **Risultati conservati:** 18 nuovi benchmark rispetto a 119: redditi reali MEF, tre confronti capacità Istat, sette pendolarismo/autocontenimento, micro unità locali, reddito imponibile, farmacie, RSA Toscana, due ACI, dipendenti comunali RGS Toscana. Snapshot e verifiche native restano versionati; valori comunali numerici e aggregati raw invariati.
- **RGS certificato:** 23.255 dipendenti 31-12-2024 / 3.660.530 residenti 01-01-2024 × 1.000 = 6,3529051804; Italia null. Copertura 273/273: 271 enti BDAP più due zeri espliciti nei PIAO originali di Londa/San Godenzo. Componenti esatte 7/7. Worker `37118112560`, job `111188810630` ACQUIRED_CANDIDATE; artifact `11272142292`, SHA `d9527303f225565ec4b571860461040c6e7f7297a254553109853a7788ae3d0c`/CRC verificati, raw e result del wrapper identici allo snapshot. Join per codice BDAP, 19 negativi nel Quick canonico. Età/turnover/training restano mancanti.
- **QA certificato del lotto RGS:** run `37117443202`, Quick `111186864258`, Full `111186864330`, preview `111190858793` SUCCESS. Head routing `2689601`: Quick `111188761363` SUCCESS; Full `111188761304` FAIL su visibilità icona mappa A5, log completo letto. Riprodotto localmente su 150 selezioni: quattro invisibilità transitorie durante il ridisegno; l’icona torna visibile dopo attesa. Correzione esclusivamente nel test: `wait_for(state='visible', timeout=5000)` prima delle stesse verifiche di unicità, visibilità e geometria. Regressione browser locale completa Demografia/A5 PASS: tutti gli indicatori degli 11 temi, Viareggio/Massarosa desktop/tablet/mobile, piramidi e tooltip. Quick finale eseguito: sorgenti/build, pubblicazione 137/137 e 111/111, grafici, governance, PNRR, 105 fisarmoniche e coerenza 250 pagine/7 stemmi PASS. Limite locale Percorsi: filtro URL all vs trekking per Leaflet CDN non caricato, già diagnosticato; nessuna guardia aggirata. Checkout isolato riallineato dopo ripristino del file test, diff pulito verificato. Nessuna UI/golden modificata.
- **Confronti residui:** restano correttamente AVAILABLE_MISSING/null, con evidenze già versionate in `a3-benchmark-residual-evidence.json` e report derivati. Non avviare ulteriori ricostruzioni OpenBDAP, RGS, GTFS, PAB, MIM o foreste. Il candidato forestale non pubblicato è sospeso e rimosso dal branch; non incrementa i 137 acquisiti.
- **Prossima azione:** completare i controlli della correzione browser, aggiornare la PR con esito finale e sottoporre al proprietario la chiusura formale. Non Ready, merge o deploy senza sua approvazione. La fase può concludersi con i 76 confronti non direttamente disponibili documentati.

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
