# A6 — adapter spesa sociale Istat v35

Baseline #385 mergiata: `9f83be4341dadef03edb37d951cdfbe68b0ba760`. Due indicatori, sette Comuni; nessuna nuova acquisizione o modifica a catalogo, UI, golden, workflow o Radar. A6.4 resta parziale, A6.5–A6.6 richiedono revisione metodologica; A7 non avviata.

## Fonti e trasformazioni

- `data/source-snapshots/welfare-prima-infanzia-2026-08.json`: Tavole Istat A misura di Comune 10b (€/abitante 2014–2022) e 10a (sette quote 2022). SHA `b13bdc5b1c579b9db6f6875637b68653869e44b898c59803415f829a6ef3455d`.
- `data/source-snapshots/a3-istat-social-services-benchmark-2022.json`: benchmark ufficiali Tav. 1 2022, Toscana 167 e Italia 150 €/abitante. SHA `d48e8dd1ffdaabf45068a54e5daafabebfc9083073a1d370e6aa1e99303b66d0`. Si usa la colonna inclusiva dei servizi educativi per la prima infanzia, coerente con il perimetro comunale; non la colonna al netto di tali servizi.

Percorso, byte hash e fingerprint JSON sono ricontrollati anche per gli input in cache. Identità codice/nome/slug, unità, anno, formule, serie, quote, alias, summary e medie pubblicate sono riconciliati con la fonte congelata. Il catalogo effettivo conserva SHA `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`: 225 indicatori, 124 storici, 137 confronti.

`socialSpendingPerResident` usa euro nominali per popolazione residente media, non residenti POSAS 2026 o euro totali. Ogni cella della serie è arrotondata a due decimali come nella materializzazione pubblica; provenienza esplicita con puntatore al valore originale, trasformazione, precisione e puntatore alla cella pubblicata. I benchmark mantengono la precisione intera ufficiale. Nessuna correzione per inflazione o concatenazione con edizioni dal diverso perimetro.

`socialSpendingByUserArea` conserva direttamente le percentuali native, senza ricostruire euro per area o denominatori. Le parti della fonte non hanno chiavi: i selettori semantici seguenti sono associati esplicitamente a posizione ed etichette originali, senza modificare il catalogo.

| Dimensione | Etichetta Istat | Selettore pubblico |
|---|---|---|
| `part:families-minors` | Famiglia e minori | Famiglie e minori |
| `part:disability` | Disabili | Disabilità |
| `part:addictions` | Dipendenze | Dipendenze |
| `part:elderly` | Anziani (65 anni e più) | Anziani |
| `part:immigration` | Immigrati, Rom, Sinti e Caminanti | Immigrazione |
| `part:poverty-hardship` | Povertà, disagio adulti e senza dimora | Povertà e disagio |
| `part:multiuser` | Multiutenza | Multiutenza |

`total` è l'alias pubblico della prima area, **non** la somma delle quote o la spesa totale. Ogni partizione comunale somma a 100 entro la tolleranza numerica; gli zeri numerici sono valori validi (booleani rifiutati), non dati mancanti o prova di assenza del bisogno/servizi sanitari. `summaryValue` resta €/abitante e non è esposto come percentuale: si interroga l'indicatore dedicato. Aree miste di utenza non equivalgono a disaggregazioni per età o sesso.

## Operazioni e limiti

| Indicatore | Abilitato | Rifiutato |
|---|---|---|
| €/abitante | Confronto, rango numerico, serie 2014–2022; gap Toscana/Italia solo 2022 | Pooling, trend/variazioni, anomalie, correlazioni non revisionate; benchmark di altri anni o Versilia |
| Quote per area | Confronto/rango per le sette aree o alias iniziale, solo 2022 | Serie non pubblicata, benchmark scalare incompatibile, pooling, operazioni temporali, anomalie e correlazioni non revisionate |

Le medie pubbliche Versilia sono medie aritmetiche dei sette indici/quote comunali, non rapporti territoriali consolidati. Sono validate come riepiloghi descrittivi, senza abilitarle come benchmark o rapporto aggregato. Non si ricavano denominatori da residenti correnti, quote o summary; maggior spesa e rango non certificano bisogno, qualità, efficacia o priorità politica. Serie consultabile e comparabilità temporale per operazioni derivate restano decisioni distinte.

## Verifica indipendente e gate

Test `scripts/test_semantic_social_spending_adapters.py`, eseguito dal gate generale di coerenza: sette indici correnti fissi, nove celle Camaiore fisse, 49 quote fisse, due benchmark ufficiali; replay separato di 63 celle storiche e 14 gap comunali. Verificati puntatori/arrotondamento, zero, alias, unità summary, medie descrittive e rifiuti avversariali su identità, parti, fonte in cache, storia, unità, perimetro e benchmark.

55 domande aggiunte con aspettative indipendenti; tutte le precedenti conservate. Suite 1.350/1.350 PASS: 650 consultazioni/calcoli e 700 rifiuti attesi. Audit derivato: 190/225 effettivi, 135/181 sorgente, 35 residui; 58 collegamenti tipizzati e 29 companion conservati. Tre carichi aggiunti per un totale di 94, misura descrittiva locale e non stress test.

Report `reports/a6-social-spending/`: audit, domande e prestazioni. I report preliminari usano il catalogo della build validata #385; prima della readiness il candidato deve ricostruirlo in clone freddo con SHA identico. Quick locale prima del push, Full locale comprensivo di Quick in clone freddo distinto e Quick→Full CI sul medesimo albero; ricevute, log e prova di identità dell'albero nella PR. Nessun merge/deploy automatico.
