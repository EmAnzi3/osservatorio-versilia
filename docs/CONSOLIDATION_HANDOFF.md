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
- Full GitHub sul head approvato rileva ancora il vecchio campione A4; i gate Salute sui dati sono verdi. Rollout Camaiore funzionale e audit A3 SUCCESS. Il passaggio anticipato a Ready aveva cancellato il Quick in corso: Quick rilanciato e SUCCESS, poi rilanciato soltanto il Full dipendente.
- Prima del prossimo push eseguire Quick sul codice dei gate aggiornati. Verificare i golden e il Full canonici sul nuovo head; poi effettuare il merge già autorizzato, attendere il deploy Pages e controllare online Classificazioni e i tre storici Lavoro.
- Non mergiare/chiudere automaticamente #302/#303/#304 e #318–#321. #301 A6.1 resta sospesa/Draft; dopo questa pubblicazione riallinearla a main e rivalidare il catalogo effettivo prima di ripartire.
