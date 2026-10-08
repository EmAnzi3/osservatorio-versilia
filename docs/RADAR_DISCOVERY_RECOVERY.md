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

## ANCI News: evidenza del proprietario, 6 ottobre 2026

Il sorgente e la schermata forniti dal proprietario confermano la rotta canonica
`https://www.anci.it/category/generico/news/`, dieci articoli nella prima pagina,
paginazione e feed dichiarato `/category/generico/news/feed/`.
Il parser legge titoli e permalink senza richiedere rendering JavaScript.
Questo prova la struttura della fonte, non la raggiungibilità dal runner.
I tentativi da questo ambiente restituiscono 502 su HTML/feed; Chromium 502
sulla lista; reader 403. Non attribuire questi errori a un disservizio generale.

Il replay del sorgente con le regole precedenti conserva due segnalazioni e
scarta due casi pertinenti: la proroga Sport/Cultura Missione Comune (`bando`
non intercetta `bandi`) e l'avviso MIM otto per mille edilizia scolastica
(l'anteprima non nomina i beneficiari). L'override ANCI usa `band`, intercetta
riparti/stanziamenti con destinatari comunali e ammette le anteprime di edilizia
scolastica alla sola coda `internal_review`. Nessuna ammissibilità, scadenza o
pubblicazione automatica è dedotta da questi segnali. Il test ridotto verifica
proroga, avviso MIM, riparto e l'esclusione di una notizia senza finanziamenti.

ANCI Piemonte resta supplementare. MIM resta non recuperato come trasporto:
`https://pn20212027.istruzione.it/avvisi/` è un elenco ufficiale pertinente ma
restituisce 502 qui. Concorsando `/blog/concorsi-mim/` riguarda assunzioni,
non opportunità di finanziamento per enti locali, e non viene configurato.
Il sorgente allegato non viene incorporato nella scansione live né usato per
aggiornare la memoria di salute della fonte.

## Follow-up del 7 ottobre: evidenze e confronto shadow

Le 12 evidenze v043 e le due Sport/LIFE sono state rilette dai documenti
ufficiali via HTTP 200. Il receipt versionato
`reports/radar/coverage-revalidation-2026-10-07.json` conserva URL richiesto,
destinazione, stato, dimensione e SHA-256. Non attesta la salute dal runner:
il gate live resta indipendente. La durata massima di 45 giorni è conservata;
nuova revisione necessaria entro il 21 novembre, non rinnovo automatico delle date.
Erasmus e Interreg usano la destinazione osservata. MASAF IDPagina/11795
elenca appalti: discovery ed evidenza passano a SviluppoRurale, dove sono
presenti contributi; gare escluse come prima. CEF Transport è chiuso e resta
evidenza storica del canale, non una candidatura aperta.

Il report nomina le evidenze scadute e le famiglie runtime con errori: un
coverage fail non viene più spiegato soltanto con zero famiglie non configurate.
Lo shadow ha budget job 60/scan 30/build 20 minuti. Il confronto semantico
avviene dopo la validazione e prima della build; un guasto nella build non
cancella il confronto, ma blocca comunque il successo complessivo.

ANCI News HTML/feed e PN2021 MIM restano 502 da questo ambiente; MIM comunicati
403. Il run candidato #351 aveva timeout HTTP/Chromium e reader 403. Nessuna
fonte viene marcata recuperata con un documento allegato, un mirror o una data
rinnovata. Il trasporto ANCI/MIM resta aperto: questa correzione risolve
la scadenza delle evidenze e il budget shadow, non l'accesso a quei publisher.

Il probe aggiuntivo versionato `reports/radar/source-route-probe-2026-10-07.json`
registra sette tentativi su domini senza www, HTTP, API WordPress dichiarata
ANCI e PN2021: nessun contenuto ottenuto, 502 o timeout. Non configura rotte
non validate e non deduce blocchi IP/WAF dai soli timeout.
