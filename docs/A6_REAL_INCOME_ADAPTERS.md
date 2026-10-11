# A6 — Redditi vs inflazione, adapter v43

Un carrier `incomeVsInflation`, sette Comuni, nove anni d'imposta 2016–2024. `total` consulta la variazione cumulata reale rispetto al 2016; `nominal` consulta la variazione cumulata nominale dello stesso reddito imponibile medio per dichiarante. Non sono tassi di crescita annui, reddito disponibile delle famiglie, salari o potere d'acquisto personale. La popolazione dei dichiaranti cambia fra anni.

## Definizione e precisione

Per la vista reale: `[(media imponibile anno / media imponibile 2016) / (NIC Italia anno / NIC Italia 2016) − 1] × 100`. Per la nominale manca il fattore dei prezzi. Le medie comunali MEF sono arrotondate al centesimo; le variazioni pubbliche a quattro decimali. Lo zero del 2016 è la base comune, non assenza di reddito. Valori negativi e pari merito sono validi. Il NIC è nazionale, concatenato dalle variazioni medie annue Istat e ribasato a 2016=100: non è un indice locale o una misura dei prezzi affrontati dal singolo contribuente.

## Evidenza e limiti del replay

`data/source-snapshots/a3-mef-real-income-benchmark-2024.json` conserva i pannelli comunali normalizzati degli estremi: 7.979 record nel 2016 e 7.897 nel 2024. Si verificano identità, componenti imponibile/frequenza, anno d'imposta, schema, totali e riconciliazione 7/7 riusando il validatore A3. Italia include la riga esplicita non localizzata; Toscana comprende 276 Comuni nel 2016 e 273 nel 2024. Questo cambiamento è dichiarato, senza imputazioni o ricostruzione di un pannello territoriale omogeneo.

Gli archivi MEF originali non sono rigiocati: URL e hash dei file originari documentano la provenienza dell'estrazione normalizzata. Per il 2017–2023 si consulta esclusivamente la serie pubblica congelata nel catalogo; non si inventano importi o frequenze mancanti. Ogni osservazione porta puntatore e hash del catalogo, contesto NIC e, soltanto per gli estremi, componenti e documento MEF. Nella vista nominale il NIC è esplicitamente contesto, non deflatore applicato.

`data/source-snapshots/nic-italia-2016-2024.json` conserva indici e variazioni: la concatenazione è ricalcolata e riconciliata. Le serie reali e nominali sono controllate a una tolleranza di 0,00011 punti percentuali per la doppia precisione pubblica; gli estremi nativi a 0,000051. Il fingerprint dell'intera definizione pubblica e gli hash byte/struttura dei due snapshot sono controllati a ogni accesso, comprese modifiche ai dati già in cache. La verifica dei pannelli completi viene riusata solo dopo questo controllo immutabile.

## Operazioni revisionate

Confronto fra Comuni, rango numerico e serie annuale sono ammessi per entrambe le viste. Il rango decrescente non esprime qualità, priorità politica o benessere. I gap Toscana/Italia sono ammessi solo per `total` e 2024: gli aggregati usano imponibile totale/frequenza totale di ogni archivio, quindi il rapporto fra le due medie e lo stesso NIC nazionale. Non sono medie dei tassi comunali; mantengono la precisione del rapporto aggregato, distinta dall'arrotondamento municipale.

Il pooling dei tassi cumulati è rifiutato: non è una somma o una media ponderata da componenti di una singola annata. Variazioni, punti percentuali e trend automatici sono rifiutati finché continuità dei dichiaranti/perimetri e interpretazione dei tassi cumulati non sono revisionate. Benchmark nominali, benchmark storici, anomalie e correlazioni non congiuntamente revisionate sono rifiutati; il controllo vale in entrambe le direzioni della coppia. Nessuna causalità viene attribuita all'inflazione, a una politica locale o alla composizione dei contribuenti.

## Prove e avanzamento

`test_semantic_real_income_adapters.py` conserva 126 celle pubbliche fisse, 28 componenti fiscali degli estremi, quattro totali territoriali indipendenti, 14 gap e nove indici NIC. Verifica i 15.876 record normalizzati, lo zero/base, pari merito, precisione, provenienza e modifiche ostili dopo la prima query. La suite aggiunge 192 domande con aspettative indipendenti e conserva integralmente le 2.235 precedenti.

Copertura derivata: 208/225 effettivi, 152/181 sorgente, 17 residui. Report in `reports/a6-real-income/`; la baseline delle prestazioni è descrittiva e distinta dalla correttezza. Nessuna acquisizione o modifica dati, UI, asset, golden, workflow o Radar. A6.4 rimane parziale; A6.5–A6.6 aperte alla revisione metodologica, A7 non avviata. Quick canonico prima del push, Full locale completo e CI Quick→Full prima della prontezza; merge riservato al proprietario.
