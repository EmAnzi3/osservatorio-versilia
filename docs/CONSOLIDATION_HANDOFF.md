# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — integrazione A3, 4 ottobre 2026

- PR #322, branch `feat/a3-integration-approved-ui`: integra #321, il parent aggiornato #302 e main `ac5e14ecb37b00e8b734a9bce0acf61c2983e677`. Nessun merge o deploy eseguito.
- Raccolta conclusa: 123/123 indicatori con storico e 137/137 benchmark pubblici, zero gap. Rispetto alla baseline delle nuove acquisizioni: 111 → 123 storici (+12), 31 → 137 confronti (+106). I 76 benchmark residui restano opportunità documentate, fuori dal lavoro necessario per chiudere questa fase. Non riaprire ricerche, GIS, ricostruzioni o recuperi onerosi; ACI escluso.
- Storici: 119 nella lettura base e quattro aggiuntivi nelle componenti selezionabili. I cinque Istat aggiungono lavoro Totale 15+ (2019, 2021–2024), diploma/terziario Totale 25–49 (2018–2024) e diploma Totale 25–64 (1991, 2001, 2011, 2024). Attività = 100 − inattività; fasce distinte, discontinuità censuaria esplicita e nessun aggregato storico da percentuali senza denominatori.

## UI e contratti da preservare

- Ultima UI approvata: #313 e correzione Atlante #315, presenti nel main indicato. Asset visuali, CSS, banner e toolbar Atlante sono byte-identici a quel main; l'unico asset diverso è `assets/ux-history.js`, che collega le serie A3 già verificate nella #321. Nessun redesign o modifica di baseline, immagini golden, soglie, palette o renderer A5.
- Pubblicazione tramite `scripts/build_public_site.py`, inclusa l'applicazione finale della UI alle sole sette route approvate. Il solo prerender del preflight non certifica la UI pubblicata.
- 225 indicatori e 1.547 valori comunali/aggregati correnti invariati rispetto a main; 14 confronti diretti dei banner desktop/mobile senza differenze pixel significative. Meteo/clima, Atlante e Affluenza conservano le proprie eccezioni.

## Verifiche correnti

- Sul head `988d4e37d532b411dc353e402472d96bab8f103b`, tutti e tre i gate prima falliti sono SUCCESS: A3 `37162739346`, golden municipale `37162739298`, golden tematico `37162739220`. Quick GitHub SUCCESS; Full/deploy saltati perché Draft. Nessun run residuo fallito su questo head.
- Le correzioni A3 riconciliano conteggi/copertura con la matrice e richiedono evidenza strutturale per quattro coppie già acquisite. Tutti i 13 blocchi Python PASS, 17 negativi respinti. I golden mantengono baseline/soglie e validano fonti, dati e DOM prima di distinguere le aggiunte dalle superfici congelate; Camaiore 446 stati e tematico 11 temi × 223 stati per viewport PASS su GitHub.
- Il blocco locale Percorsi era la configurazione di rete di Chromium: il runtime usa ora il proxy e le CA già installate nell'ambiente. Dipendenze reali, nessuna sostituzione/mock, nessuna modifica al prodotto o alle asserzioni. Percorsi desktop/mobile e Quick locale PASS da build pulita.
- Il Full ha riprodotto una lettura anticipata del pulsante carburanti, prima del frame di aggiornamento dello storico. Il test ora attende entro 5 secondi un unico pulsante abilitato; tutti i controlli originali su storico, 6 Comuni e 54 mesi restano invariati. Transitorio riprodotto 20/20; indisponibilità persistente respinta. Regressione completa degli 11 temi e delle schede responsive PASS. Quick locale GREEN; 40 baseline A4 e Browser Quality Gate (578 controlli) PASS. Il Full unitario si è interrotto su un blocco di rete del runtime verso registry.npmjs.org, senza un esito GREEN. Lighthouse 13.4.1 sulle quattro route e i 17 controlli statici estesi sono PASS nelle esecuzioni mirate. La copia locale già scaricata di Lighthouse 13.4.1 è disponibile per una successiva esecuzione senza accesso al registro; nessun gate saltato o indebolito.

## Correzione preview approvata

- Audit delle PR recenti: #309, #312, #313, #314 e #315 già integrate e byte-identiche a main nei rispettivi file, salvo ux-history A3. La preview Quick caricata da Pages non eseguiva la build pubblica finale: mancavano gli adapter della UI secondaria. Il workflow ora completa il dist già materializzato dal Quick con apply_secondary_pages_ui.py, poi esegue build_public_site.py --validate-only e consistenza prima dell’upload. Il contratto impone Quick → UI finale → validazione pubblica → upload, evitando una seconda build integrale e la rimaterializzazione parziale dell’Atlante. Preview locale dal dist GitHub 0fa9f6b: adapter ufficiale, sole sette pagine modificate, dati/asset/tematiche/comuni byte-invariati; homepage desktop/mobile verificata con immagini locali e senza overflow. La preview precedente non certifica la homepage approvata.

## Correzione richiesta dal proprietario — Classificazioni

- Difetto riprodotto negli screenshot: Classificazioni bypassava la shell confronto e non era inclusa nei renderer comunali con toolbar standard. Correzione limitata all’indicatore territorialClassification: shell attuale/storico standard nel confronto, fallback A5 esistente nelle schede comunali; CSS, contenuto delle classificazioni e dati invariati. Verifica mirata sui due cambiamenti runtime: 16 casi toolbar (confronto + sette Comuni, desktop/mobile), icone/CSV/stampa e assenza di overflow PASS; sei casi storici Lavoro PASS con sette serie e cinque punti ciascuna. Regressione toolbar aggiunta al gate export esistente. Quick locale precedente interrotto dal ripristino del browser dopo manutenzione del workspace; validazione finale da completare.
- Lavoro: la selezione iniziale 25–64 Totale non ha lo storico acquisito. Le tre nuove serie si consultano scegliendo 15 anni e oltre, Totale (2019, 2021–2024); nessun cambio del perimetro o del valore iniziale.

## Prossima azione esatta

1. Caricare la correzione del test e questo handoff, dopo il Quick locale già GREEN. Mantenere Draft e concludere il Full locale con Lighthouse 13.4.1 già presente nel runtime; poi verificare Quick e Full canonici sul nuovo head prima del merge. Non dichiarare verde un controllo non concluso.
2. Prima di merge e pubblicazione ottenere approvazione esplicita del proprietario, come richiesto da `AGENTS.md`. Le PR #302/#303/#304 e #318–#321 non vanno mergiate o chiuse automaticamente; #303 contiene opportunità fuori dal lotto certificato.
3. Dopo integrazione approvata riallineare #301 A6.1 a main e rivalidare il catalogo dei 225 indicatori. #301 resta sospesa/Draft; nessuna UI A6 avviata.
