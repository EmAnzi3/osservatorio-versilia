# Consolidamento Osservatorio Versilia — handoff operativo

## Main verificata il 23 ottobre 2026 — #469 integrata dal proprietario

Main `3708ecd61830feaafffdd6448ce05b26d7b5c6a7`, albero
`2afcc231435d857cc2e5a9a755209de06f60b6a9`, identico al candidato #469
`b91bbe77f0a03eaea195f902231a378d3e471b13`. Merge del proprietario verificato.
Attestazione #469: Quick/Full locali ordinari PASS, CI Quick→Full effettivo
`39859863476`, A3 `39859863417` SUCCESS, checkout effettivo `308507b7`,
medesimo albero. Archivio `A7_DESCRIPTIVE_ORDER_76b3b18_evidenze.zip`, SHA256
`5d44826e6c1080776fd0310d1278cabf2a483838a186dd49a025a133f9bd66b4`.
Pubblicazione verificata separatamente: Pages push `39890806377`, build
`120209849257` e deploy `120214902757` SUCCESS. Reporter `39892422975`, job
`120215040598` SUCCESS: checkout effettivo del merge `3708ecd6`, integrità
Chiedi con asset/hash PASS, `ov-public-routes` e `ov-pages-live` SUCCESS.
Quick/Full skipped nel push non sono nuovi gate PR. Nessun merge/deploy
dell’assistente.

A6 DONE: 225/225 adapter, 3.727 casi indipendenti, 35 letture e due riepiloghi,
Atlante 20.325 unità locali native, 40 golden e Camaiore congelata. Nessuna
regressione dimostrata. A7 IN_PROGRESS, nessuna promozione in navigazione.
#469 espone l’ordine numerico dei sette Comuni con posizioni e pari merito A6.
Runtime pubblico candidato: 49.109 richieste, 27.698 computed / 21.411 rifiuti,
124.872.856 byte gzip; misura di trasporto, non nuovi casi indipendenti.
Matrice #469: 12.747 capacità preparate e 1.241 dichiarate non materializzate:
202 trend, 515 correlation, 515 anomaly, 9 benchmark_gap. Dichiarazioni
condizionali, non 1.241 risultati calcolabili. Acquisiti A3 746; percorsi
275 completi / 29 parziali / 442 senza prova nel perimetro, non dati assenti.

## Incremento corrente — trend nativo opzionale e prove di selezione

Branch `feature/a7-native-trend-transport`, base main #469. Passo A7.5.3.
La matrice esegue una richiesta trend per vista dichiarata e Comune: serie
nativa completa, nessun periodo, filtro dei mancanti o consenso aggiunto.
Prove puntuali nel ledger con esiti e motivi, dichiarazioni ancora condizionali.
Profilo opzionale `trends`: 202 viste / 1.414 richieste, 724 computed e 690
rifiuti originali; pacchetto dedicato 2.476.698 byte gzip (inclusi dettagli),
non costo incrementale della build combinata. Nessun nuovo calcolo browser,
previsione o ordinamento delle pendenze. Metodo `A7_NATIVE_TREND_TRANSPORT.md`.

I tre default e i profili della build pubblica restano invariati. La UI non
presenta trend; controlli e browser pubblici continuano a verificare i profili
precedenti. Prima della futura integrazione: resa di periodi/unità/n/limiti,
costo combinato e preview/browser. Altre operazioni e dimensioni, associazioni,
riuso/CSV/PDF e dossier restano aperti. Nessuna interrogabilità universale.

Gate del nuovo candidato: parità del trasporto, pacchetto atomico, matrice,
Quick/Full locali ordinari e CI Quick→Full effettivo/A3 sul medesimo albero;
attestazioni finali nella PR. Non trasferire i verdi #469 al nuovo candidato.
Ambiente: Chrome ufficiale 151.0.7922.34, Playwright 1.62.0, Lighthouse 13.4.1;
cache Python separate. Le sonde HTTP ottengono gli originali Leaflet, ma il
browser restituisce ERR_EMPTY_RESPONSE da Unpkg e non inizializza Percorsi.
Solo quelle pagine riproducono i due originali Leaflet 1.9.4 verificati contro
SRI; nessuna modifica DOM/dati/golden/soglie, altre pagine con cache HTTP reale,
Lighthouse non intercettato. Prova del prodotto congelato, non disponibilità
CDN/WAN o telefono fisico. Diagnosi e riproduttori nelle evidenze.

Radar #468 conserva budget build 60/job 105 e i propri gate separati;
nessun refresh riuscito attestato da A7. Dossier editoriali e Radar separati.
Nessuna nuova acquisizione, adapter, modello esterno, backend o infrastruttura.
Nessun merge o deploy autorizzato all’assistente.
