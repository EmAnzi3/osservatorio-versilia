# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — pubblicazione A3 approvata, 4 ottobre 2026

- PR #322, branch `feat/a3-integration-approved-ui`, Ready. Il proprietario ha approvato la preview del head `896383d3180169ec905d5e2acdd6be48cc03a766` e autorizzato merge e pubblicazione. Nessun merge/deploy ancora eseguito: concludere i gate prima del merge, senza chiedere nuovamente il consenso già dato.
- Raccolta conclusa: +12 storici e +106 confronti rispetto alla baseline; totali 123 storici (119 base, quattro nelle componenti) e 137 confronti. Catalogo 225 indicatori e 1.547 valori correnti invariati. Le 76 opportunità residue restano documentate, fuori da questo lotto; non riaprire ricerca, GIS, ricostruzioni o ACI.
- Occupazione/disoccupazione/attività: storico disponibile scegliendo 15 anni e oltre → Totale, punti 2019 e 2021–2024. Diploma/terziario 25–49 Totale: 2018–2024; diploma 25–64 Totale: 1991, 2001, 2011, 2024. Nessuna interpolazione o aggregazione storica di percentuali senza denominatori.

## UI approvata e golden

- #309/#312/#313/#314/#315 già integrate. La preview canonica applica la UI secondaria finale al dist Quick, poi valida prima dell’upload. Non usare il dist intermedio come prova della homepage pubblicata.
- Classificazioni: toolbar standard con icone e tre azioni nel confronto e nei sette Comuni, contenuto nativo invariato. Preview approvata; verifiche 16 toolbar + sei storici Lavoro desktop/mobile e suite export PASS.
- I gate contro i riferimenti antecedenti segnalano la toolbar richiesta: A4 solo Classificazioni mobile; Camaiore solo Classificazioni desktop/mobile. Aggiornato soltanto quel campione A4 (39 altri campioni invariati). Per A5 si proietta sul DOM del riferimento la toolbar statica della preview approvata, fissata al commit sopra e a un digest; il contenuto nativo viene verificato identico prima della proiezione e mantenuto. Tutti i confronti di stato/pixel e le soglie restano attivi. Il DOM reale viene ripristinato dopo ogni cattura. Classificazioni è aggiunta anche alle catture visive Camaiore.
- CSS, renderer, dati, banner e commit baseline generali non cambiano con questo aggiornamento dei gate. Verifica mirata della proiezione: confronto/Camaiore desktop/mobile, stati e pixel identici; pulsanti mancanti e contenuto alterato respinti.

## Verifiche e prossima azione

- Quick locale e GitHub sul head approvato SUCCESS. Full locale eseguito: exit 0; log disponibile fino al monitor offline, senza marker finale GREEN. A4 40 campioni, export, 578 controlli qualità browser e Lighthouse PASS osservati nel log. Non dichiarare un marker non osservato.
- Sul head `17096fdf` tutti i workflow eseguiti sono SUCCESS tranne il golden Camaiore: Quick/Full Pages, Quick/Full e preview Salute, golden tematico, rollout e audit A3 verdi. Camaiore segnala otto differenze visive su quattro indicatori Ambiente desktop/mobile dopo la cattura Classificazioni: gli artifact mostrano l’header sticky soltanto su una superficie. Le catture ora iniziano e terminano entrambe a scroll zero, come il golden tematico; regioni e soglie invariate. Verifica mirata contro il riferimento immutabile `5aaf159`: dieci catture Classificazioni e quattro indicatori × desktop/mobile PASS, nav baseline normalizzata con il contratto esistente.
- Quick locale eseguito sul test aggiornato e checkout committato: contratti sorgente/dati, build non mutante, 123/137 pubblicazioni, compositi, grammatica e governance PASS. Il controllo PNRR ha rilevato il vecchio marchio O nel dist locale: ripristinato soltanto l’output con la funzione canonica `apply_brand_and_pwa` e rieseguiti i controlli rimanenti, senza modificare sorgenti o asserzioni. Non dichiarare una singola esecuzione Quick GREEN.
- Dopo il push verificare golden e Full canonici sul nuovo head; poi effettuare il merge già autorizzato, attendere il deploy Pages e controllare online Classificazioni e i tre storici Lavoro. Nessun nuovo consenso necessario.
- Non mergiare/chiudere automaticamente #302/#303/#304 e #318–#321. #301 A6.1 resta sospesa/Draft; dopo questa pubblicazione riallinearla a main e rivalidare il catalogo effettivo prima di ripartire.
