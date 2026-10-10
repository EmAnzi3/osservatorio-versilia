# A6 — Farmacie e RSA accreditate

Lotto v36 dopo #386: due carrier di presenza territoriale, nessuna nuova acquisizione o modifica del catalogo, della UI o dei workflow. Ospedali esclusi: il canonico corrente non dispone di un pannello nativo congelato equivalente per riconciliare strutture e posti letto.

## Farmacie

`pharmaciesPer1000`: sedi ministeriali valide al **31 dicembre 2025**, incluse ordinarie, succursali, dispensari e dispensari stagionali. Il pannello completo congelato contiene 20.730 sedi attive nazionali, 1.270 toscane; codice ministeriale univoco e intervalli di validità governati dall’acquisizione A3. Non si sommano le 57.805 righe storiche del CSV.

Denominatore: residenti POSAS stimati al **1° gennaio 2026**, distinti dall’anno della fotografia delle sedi. Conteggi comunali e popolazioni nativi riconciliano esattamente `round(conteggio / residenti × 1000, 2)` con il valore pubblico. Il motore restituisce il valore pubblico arrotondato e conserva selezione dei record, conteggio, puntatore/hash del denominatore e data nelle evidenze. Non ricostruisce conteggi dal tasso.

| Comune | Sedi | Residenti 01-01-2026 | Valore pubblico ogni 1.000 |
|---|---:|---:|---:|
| Camaiore | 11 | 31.763 | 0,35 |
| Forte dei Marmi | 5 | 6.550 | 0,76 |
| Massarosa | 6 | 21.782 | 0,28 |
| Pietrasanta | 9 | 22.678 | 0,40 |
| Seravezza | 4 | 12.284 | 0,33 |
| Stazzema | 1 | 2.783 | 0,36 |
| Viareggio | 20 | 60.680 | 0,33 |

Sono ammessi confronto, rango e gap Toscana/Italia sul solo riferimento 2025. Benchmark: `1270 / 3659222 × 1000` e `20730 / 58942828 × 1000`, con medesima fotografia delle sedi e denominatore 2026. Il gap sottrae un riferimento non arrotondato al valore comunale pubblico a due decimali: avvertenza esplicita, nessuna falsa precisione sul valore comunale. La densità Versilia pubblica è verificata da 56 sedi / 158.520 residenti × 1000, non dalla media semplice dei tassi.

## RSA

`accreditedRsaCount`: strutture RSA accreditate localizzate nei sette Comuni al **31 dicembre 2025**. Il PDF regionale congelato fornisce 337 righe RSA e **336 strutture uniche**, dopo deduplicazione per Comune e denominazione; EMD Ciapetti è ripetuta identicamente. Due celle di impresa vuote restano tali: non servono al conteggio e non sono imputate. Tutto il pannello, non un estratto parziale, sostiene gli zeri comunali.

Conteggi indipendenti: Camaiore 5, Forte dei Marmi 0, Massarosa 0, Pietrasanta 2, Seravezza 2, Stazzema 0, Viareggio 4; totale **13**. Il pannello completo è riconciliato anche con lo snapshot locale Salute v140. Puntatore ai record, selezione per nome comunale, chiavi di deduplicazione, conteggio e SHA accompagnano la risposta.

Sono ammessi confronto e rango dei conteggi comunali. Il dato regionale 336 è conservato e validato come **stock assoluto regionale**, ma non abilita un gap comunale: universi territoriali di dimensione diversa, nessun tasso per residenti/anziani/posti letto acquisito. Italia non disponibile, nessuna stima. La serie pubblica con un solo punto 2025 non costituisce uno storico interrogabile.

## Limiti e validazione

Presenza fisica diversa da accessibilità, orari, capacità, posti letto, assistiti residenti, convenzionamento SSR e qualità. Gli zeri non significano assenza di cure usufruibili fuori Comune. Rango e densità non determinano automaticamente fabbisogni o priorità politiche. RSA localizzate e anziani residenti assistiti ARS non hanno lo stesso universo.

Nessuna variazione/trend, anomalia o associazione automatica; pooling non abilitato per questo carrier pubblico arrotondato. I componenti nativi sono conservati come evidenza di riconciliazione, senza nuove dimensioni pubbliche o override della matrice A3. Confronti singoli continuano a rispettare il minimo di osservazioni del contratto generale.

Gli input sono vincolati al percorso, SHA-256 byte e fingerprint JSON; viene controllata anche la cache parsata per impedire mutazioni con metadati invariati. Identità 7/7, periodi, unità, formule, valori, aggregati, flag, benchmark e storico singleton riconciliati prima della risposta. Nessun valore nullo, booleano o dato errato sostituito silenziosamente.

Test: 14 celle pubbliche fisse, sette conteggi e denominatori farmacie indipendenti, 14 gap, rango con pari merito e zeri; mutazioni avverse di catalogo/snapshot/cache/provenienza e rifiuti temporali/territoriali. 52 nuove domande con aspettative indipendenti; tutte le 1.350 precedenti conservate. Microbenchmark descrittivo, nessuna promessa di latenza o concorrenza.

Audit e suite preliminari usano il catalogo effettivo verificato della #386, SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; il candidato deve riconciliarlo nelle build fredde Quick/Full. Prima del push Quick canonico locale; prima della prontezza Full locale comprensivo di Quick e CI Quick→Full sul medesimo albero. A6.4 parziale, revisione A6.5–A6.6 aperta, A7 non avviata.
