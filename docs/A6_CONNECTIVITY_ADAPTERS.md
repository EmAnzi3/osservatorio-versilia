# A6 — FTTH AGCOM: disponibilità dichiarata e famiglie

Il lotto v37 abilita quattro carrier già pubblicati senza acquisire dati né cambiare la UI: `ftthCoverageDesi`, `ftthCoverage20m`, `ftthReachedHouseholds` e `ftthUnreachedHouseholds`. Riferimento **31 dicembre 2025**, distinto dalla pubblicazione/acquisizione 2026. Il token delle risposte è `2025-12-31`; `2025` e l'etichetta pubblica risolvono la stessa fotografia, non una media annuale.

## Evidenza e universi

Fonte primaria: AGCOM Broadband Map, reportistica comunale, CSV ufficiale ArcGIS `25830559c5784c1eb5eb1cf748889f4c`. Si usa esclusivamente `towns[].agcom.primaryOfficialCsv` dello snapshot `data/source-snapshots/agid-asia-agcom-2026-08.json`. I vecchi shard e `auditOfficialCsv` restano diagnostici e non sostituiscono il primario. Gli hash dei byte e del JSON canonico congelato sono verificati anche sulla cache del motore; le osservazioni espongono puntatore del record primario, campi nativi, data, URL e SHA, insieme al puntatore del catalogo.

Le percentuali DESI ed entro 20 metri sono misure distinte, pubblicate a un decimale, con copertura 7/7. I conteggi DESI sono disponibili per 6/7: **Forte dei Marmi conserva percentuali 0,0 e conteggi `null`**. Non si ricava il conteggio da percentuale × famiglie, né si sostituisce `null` con zero. La metrica non raggiunta è il complemento nativo `famiglie_residenti − famiglie_ftth` soltanto dove il secondo dato esiste. Il denominatore è quello AGCOM, non le famiglie Istat o i residenti POSAS.

| Comune | Famiglie AGCOM | FTTH DESI | FTTH entro 20 m | DESI % | Entro 20 m % | Non raggiunte DESI |
|---|---:|---:|---:|---:|---:|---:|
| Camaiore | 13.119 | 11.978 | 10.512 | 91,3 | 80,1 | 1.141 |
| Forte dei Marmi | 2.707 | n.d. | n.d. | 0,0 | 0,0 | n.d. |
| Massarosa | 8.982 | 4.219 | 3.084 | 47,0 | 34,3 | 4.763 |
| Pietrasanta | 9.353 | 5.546 | 4.133 | 59,3 | 44,2 | 3.807 |
| Seravezza | 5.068 | 35 | 4 | 0,7 | 0,1 | 5.033 |
| Stazzema | 1.148 | 1.009 | 889 | 87,9 | 77,4 | 139 |
| Viareggio | 25.039 | 23.734 | 21.536 | 94,8 | 86,0 | 1.305 |

## Operazioni e aggregati

Confronto e rango sono abilitati. I conteggi richiedono l'esplicito `allowPartial` quando la selezione include il Comune mancante; i minimi di osservazioni del contratto comune restano invariati. Media semplice dei Comuni disponibili e rango sono descrittivi: non rappresentano un totale territoriale né una priorità politica.

I due aggregati percentuali pubblici sono riconciliati come media delle **percentuali ufficiali arrotondate**, ponderate per famiglie AGCOM: DESI `71.12488687782805`, entro 20 m `61.37692766295708`. Non si dichiarano equivalenti al rapporto tra conteggi nativi sommati, anche perché Forte ha conteggi mancanti. I totali assoluti pubblici `46.521` raggiunte e `16.188` non raggiunte sono parziali 6/7 e mantengono la propria etichetta. Il lotto verifica gli aggregati esistenti ma non introduce pooling nel contratto `weighted_ratio` né nuovi companion pubblici.

Gli scostamenti Toscana/Italia sono ammessi **solo sulle percentuali**. Lo snapshot A3 `data/source-snapshots/a3-agcom-benchmark-2025.json` conserva benchmark con quality gate PASS, formula, 273/7.896 Comuni e riferimenti alla run/artifact. Il lotto verifica impronte, periodo, unità e riconciliazione dei valori materializzati. Il pannello nazionale non è congelato localmente: nessuna dichiarazione di replay raw dei benchmark. Si restituisce la provenienza dell'acquisizione A3, distinta dall'evidenza primaria delle sette righe comunali. Le celle assolute mancanti in entrambi gli scope bloccano confronti sui conteggi.

## Rifiuti e significato

Nessuno storico omogeneo è disponibile nello snapshot: serie, variazioni e trend sono rifiutati. Rifiutati inoltre pooling di percentuali arrotondate, dimensioni sesso/età o componenti non revisionate, anomalie e correlazioni automatiche in entrambi gli ordini dei selettori, benchmark assoluti e scope non revisionati.

La disponibilità dichiarata della rete non equivale ad abbonamenti, velocità effettiva, servizio attivabile a un civico, bisogno sociale, qualità o successo di una politica. Gli zeri sono valori della fotografia ufficiale, non una nuova verifica della rete sul territorio nel 2026.

## Verifica

Regressioni indipendenti: 28 celle pubbliche (incluse quattro `null`), 35 celle native, 28 scostamenti, quattro aggregati, ranghi, data e puntatori, zero/mancante e mutazioni avverse su catalogo/cache/hash. Corpus: 110 nuove domande con aspettative fisse e rifiuti, tutte le 1.402 precedenti conservate; totale 1.512 PASS, 740 letture/calcoli e 772 rifiuti. Audit derivato e carichi descrittivi in `reports/a6-connectivity/`.

Il report preliminare usa catalogo e registry effettivi della #388 con SHA conservato; Quick e Full in clone freddo devono ricostruire e riconciliare la stessa vista prima della prontezza al merge manuale. A6.4 resta parziale; A6.5–A6.6 richiedono la revisione metodologica. A7 non avviata.
