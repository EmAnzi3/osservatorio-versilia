# Verifica live delle fonti — 4 ottobre 2026

Scansione deep: 225 indicatori, 138 fonti, zero errori strutturali. Nessun nuovo valore viene pubblicato dal monitor.

## Tentativi non riusciti

| Indicatori associati | URL esatto | Esito | Tentativi |
|---|---|---|---:|
| Autovetture ogni 1.000 residenti; Autovetture Euro 0–3 | https://aci.gov.it/attivita-e-progetti/studi-e-ricerche/autoritratto/ | 503: HTTP 503 | 5 |
| Affluenza al voto | https://elezionistorico.interno.gov.it/eligendo/opendata.php | 403: HTTP 403 | 3 |
| Qualità delle aree di balneazione | https://www.arpat.toscana.it/datiemappe/balneazione-in-toscana-dati-relativi-alle-stagioni-precedenti/ | 403: HTTP 403 | 3 |
| Prevalenza ipertensione | https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=255 | HTTP n.d.: The read operation timed out | 2 |
| Prevalenza BPCO | https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=268 | HTTP n.d.: The read operation timed out | 2 |
| Prevalenza cardiopatia ischemica | https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=269 | HTTP n.d.: The read operation timed out | 2 |
| Persone con demenza | https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=270 | HTTP n.d.: The read operation timed out | 2 |
| Persone con diabete | https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=271 | HTTP n.d.: The read operation timed out | 2 |
| Prevalenza insufficienza cardiaca/scompenso | https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=272 | HTTP n.d.: The read operation timed out | 2 |
| Prevalenza pregresso ictus | https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=273 | HTTP n.d.: The read operation timed out | 2 |

- ACI: anche il download alternativo https://aci.gov.it/app/uploads/2025/06/Autoritratto-2024-Parco-Veicolare.zip restituisce HTTP 503.
- Aree naturali protette: il vecchio URL https://www.regione.toscana.it/-/il-sistema-delle-aree-naturali-protette restituisce 404; il nuovo https://www.regione.toscana.it/sistema-aree-naturali-protette risponde 200.

## Acquisizione da verificare

- Bonifiche SISBON: il vecchio export https://sira.arpat.toscana.it/apex/f?p=SISBON:REPORT_PER_RT::CSV:IR_REPORT_GEOSCOPIO è dismesso secondo ARPAT. SISBON 2.0: https://sisbon.regione.toscana.it/ — HTTP 200 della landing; export dati non verificato.
- Enti del Terzo settore (RUNTS): https://servizi.lavoro.gov.it/runts/it-it/Lista-enti — catalogo del 4 ottobre, download/elaborazione comunale non acquisiti.

I timeout descrivono una verifica fallita dalla rete dello scanner e non certificano che la fonte sia offline. HTTP 403 indica accesso negato, senza attribuire automaticamente la causa a un blocco anti-bot. I dati validi e gli snapshot esistenti vengono conservati. La diagnostica completa, gli URL alternativi e ogni tentativo sono nel JSON a fianco.

## Evidenza fornita dall’operatore

Il proprietario raggiunge ACI, Eligendo, ARPAT e gli export ARS dal proprio browser. Le schermate mostrano le pagine ufficiali: gli errori precedenti restano esiti della rete dello scanner, non certificazioni di indisponibilità generale.

- ZIP ACI 2024: SHA-256 archivio `733dd5877d127d9e55a202ea444044e2b789c975c670a07204f8f966e352372c` e workbook `700e7fbc0a1f3d68502aec979a11fc6d25f4c07ecc563fc356ee9d610b77dabc` identici allo snapshot versionato.
- ARS 255 (ipertensione): CSV SHA-256 `3af05ca683f059b15f75895df669d7f74bbb2e39181b3f3357ad25db6beb1f46`, 4.769.433 byte, identico alla sorgente dello snapshot; periodi 2015–2025. Gli altri export ARS sono dichiarati raggiungibili dall’operatore, senza confronto dei file in questa sessione.
- Nuovo candidato ACI 2025 individuato nel catalogo ufficiale: https://aci.gov.it//app/uploads/2026/06/Autoritratto2025_Parco_veicolare.zip — il probe automatizzato restituisce 503; non acquisito. La regex è stata corretta per riconoscere anche il nuovo nome senza trattino.

La [prova JSON](operator-evidence-2026-10-04.json) distingue esplicitamente file ricevuto, ultimo rilascio non certificato e acquisizione live non verificata. Nessun file ZIP duplicato nel repository.

ARS 255: prova live aggiuntiva con il GET del harvester (timeout 120 s) riuscita in 33,52 secondi, CSV di 4.769.433 byte con SHA identico allo snapshot. Il monitor deep usa ora 90 secondi solo sui sette export ARS osservati; light mantiene 20 secondi. Questo corregge la verifica, senza sostituire valori e senza generalizzare il successo del 255 agli altri sei export. Il report deep iniziale conserva i timeout realmente riscontrati prima della correzione.

Conferma sul monitor corretto: probe deep ARS 255 HTTP 200, timeout configurato 90 s, hash completo `zip-members`, nessun troncamento. Esito salvato nella baseline; gli altri sei timeout ARS restano da riverificare dal deep mensile. Il controllo light non cancella la prova deep acquisita. Nessun valore aggiornato per ARS, poiché il CSV coincide con la sorgente pubblicata.
