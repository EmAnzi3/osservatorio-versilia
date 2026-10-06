# Recovery delle fonti Radar e copertura discovery

Il recupero delle rotte ufficiali non equivale all'acquisizione di nuovi dati
statistici né all'attestazione che ogni publisher sia raggiungibile.

La PR #347 distingue endpoint `listing` e `supplementary`: solo il primo tipo
attesta la copertura della scoperta di nuovi avvisi. Un mirror regionale,
un singolo bando, una FAQ o una pagina di programma possono aggiungere candidati
e informazioni senza trasformare un listing fallito in copertura riuscita.
ANCI Piemonte, Gazzetta per il Piano del Mare, il singolo bando SCU, le due FAQ
GSE, le pagine dei singoli avvisi Sport e i dettagli/programmi LIFE sono
supplementari. Le liste ufficiali restano censite e gli errori restano visibili.

La memoria legacy riconcilia questi ruoli: un successo derivato solo da pagine
supplementari non crea una falsa ultima discovery riuscita. Non modifica il
contenuto delle opportunità valide già pubblicate. Le regole di grace, scadenze,
continuità e pubblicabilità restano invariate.

## Evidenze operative

Il run PR `37448430823`, head `14f2ecf9`, del 6 ottobre 2026 è riuscito con avvisi:
64 record invarianti, cinque endpoint falliti. ANCI/MIM erano in grace;
GSE risultava degraded perché le FAQ erano ancora listing. Il follow-up corregge
anche queste FAQ, oltre a Sport/LIFE; il successo delle FAQ non attesta più
discovery GSE. Il nuovo head richiede nuove verifiche, senza riusare questo run.

| Publisher | URL esatto | Errore osservato in quel run |
|---|---|---|
| ANCI nazionale | https://www.anci.it/feed/ | Timeout HTTP e Chromium 20 s; reader 403 |
| ANCI Comuni Digitali | https://sistemacomunidigitali.anci.it/feed/ | Timeout HTTP e Chromium 20 s; reader 403 |
| GSE news | https://www.gse.it/servizi-per-te/news | HTTP/Chromium/reader 403 |
| MIM PNRR scuola | https://pnrr.istruzione.it/feed/ | Timeout HTTP e Chromium 20 s; reader 403 |
| MIM comunicati | https://www.mim.gov.it/web/guest/comunicati | HTTP/Chromium/reader 403 |

Queste sono fonti del Radar opportunità, non indicatori statistici; non attestano
indisponibilità generale dei servizi. Il campo `httpAttempts` ereditato indica
il budget, non il conteggio puntuale delle richieste. Lo shadow usa lo stesso
motore h5: il suo verde non prova indipendenza o miglior capture rate.

Il checksum SRI CSS Leaflet 1.9.4 viene corretto ai byte ufficiali,
`p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=`; nessuna grafica ridisegnata.
L'audit delle percentuali usa il catalogo effettivo e attende la selezione nel
browser; soglie, assert e golden restano.

## Gate

Test mirati: ruoli dei canali reali, mancata copertura con sole pagine secondarie,
legacy GSE/ANCI, trasporto Chromium con HTTP 503, archivio annuale, salute e report.
Prima del merge: Quick/Full locali e CI sul candidato riallineato a main.
Il precedente Full locale Demografia 60/100 non viene dichiarato verde dalla CI:
la causa deve essere chiarita dal controllo locale isolato del candidato.
