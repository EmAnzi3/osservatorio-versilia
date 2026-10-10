# A6 — Indicatori comunali regionali

Sei nuovi carrier del profilo `regione-toscana-indicatori-comunali`: `youthOtherStatus`, `foreignBornSoleProprietorShare`, `emsResponseTimeP75`, `disability064Per1000`, `municipalOnlineServicesAdvanced`, `innovationBusinessShare`. `organicAgriculturalAreaShare` è già governata dal lotto agricolo e non viene ricontata. Nessuna modifica ai valori pubblici, alle letture territoriali o alla UI.

## Universi, formule e riferimenti

| Carrier | Definizione e denominatore della fonte | Riferimento |
|---|---|---|
| Giovani in altra condizione | Giovani 15–24 in altra condizione professionale / giovani 15–24 × 100; non disoccupazione né automaticamente NEET | 2024; serie 2018–2024 senza 2020 |
| Ditte individuali | Ditte individuali attive con conduttore nato all’estero / ditte individuali attive × 100; nascita, non cittadinanza | 2024; serie 2018–2024 |
| Risposta 118 | P75 della distribuzione degli intervalli chiamata–arrivo del primo mezzo, minuti; non tempo medio | 2024; serie 2018–2024 |
| Disabilità | Persone 0–64 con disabilità riconosciuta, anche grave / residenti 0–64 × 1.000; registrazione amministrativa, non prevalenza sanitaria | 2024; serie 2018–2024 |
| Servizi online | Servizi offerti ai livelli 3 o 4 / servizi pertinenti offerti nella rilevazione ICT PA × 100 | Definitivo 31/12/2022; sole rilevazioni 2018 e 2022 |
| Imprese dell’innovazione | Imprese attive nelle divisioni Ateco selezionate / imprese attive × 100; non misura diretta di innovazione prodotta | 2024; serie 2018–2024 |

Il metadato ufficiale regionale è `https://www.regione.toscana.it/documents/d/guest/modellometadatinew-1`, verificato in preparazione del lotto. Le divisioni Ateco dichiarate per ind19 sono 13, 19, 20, 21, 22, 25, 26, 27, 28, 30, 61, 62, 66, 71, 72 e 74. Ind18 include invio della modulistica (livello 3) e procedimento interamente online con eventuale pagamento (livello 4); il paniere passa da 24 servizi nel 2018 a 27 nel 2022. La riproposizione nel CSV 2024 non è una nuova osservazione. Il denominatore concettuale è esplicito; i conteggi comunali e la distribuzione degli interventi 118 **non sono congelati**. `nativeComponentsAvailable=false`: nessuna divisione inversa del valore percentuale e nessuna sostituzione con residenti 2026.

## Evidenza congelata e riconciliazione

- `toscana-indicatori-v1.5.0.json`: estrazione di percentuali/tassi/P75 dai file annuali ufficiali, identità ISTAT e anni nativi. Non contiene numeratori/denominatori numerici né gli interventi individuali.
- `regione-toscana-servizi-online-2018-2022.json`: valori delle due rilevazioni effettive, data di riferimento e cambio di paniere.
- `a3-regione-toscana-indicators-benchmark-2024.json`: riga Toscana ufficiale, sette righe comunali riconciliate e riferimenti dell’acquisizione A3. Italia assente nella stessa fonte. Non contiene un nuovo pannello regionale o componenti per ricalcolare il benchmark.

SHA-256 dei byte e fingerprint JSON canonico sono controllati ad ogni accesso, anche dopo una mutazione del cache. Tutte le sette identità, valori correnti e serie sono riconciliati; le mediane pubbliche dei primi cinque indicatori annuali restano riepiloghi non ponderati, non aggregati ufficiali Versilia. Ind18 mantiene la media aritmetica pubblica non ponderata. Il benchmark Toscana è la riga regionale pubblicata, distinto da questi riepiloghi. I file sorgente annuali non vengono nuovamente acquisiti o rigiocati: l’evidenza è l’estrazione già congelata, non un nuovo audit dei microdati.

## Operazioni e rifiuti

Ammessi `compare`, `rank`, `series` e `benchmark_gap` Toscana al solo riferimento corrente. Rango numerico, senza valutazione della qualità del Comune. Le serie mostrano le osservazioni pubblicate e conservano lacune e cambi di paniere; non attestano continuità tra rilasci. Trend, variazioni, punti percentuali, anomalie e correlazioni non congiuntamente revisionate vengono rifiutati in entrambe le posizioni dei selector. Nessun rapporto territoriale senza componenti, P75 aggregato da percentili comunali, benchmark Italia o storico, normalizzazione per residenti o disaggregazione sesso/età non congelata. Le formule sopra documentano la definizione della fonte e non vengono presentate come calcoli da conteggi inesistenti.

## Validazione e copertura

42 osservazioni correnti e sei benchmark con trascrizioni fisse; 36 celle storiche di Massarosa con aspettative fisse indipendenti dalle risposte del motore. Replay separato di 252 celle storiche dell’estrazione congelata. Mutazioni avversarie su identità, anni/unità/fonti, valori, riepiloghi, componenti inventate, benchmark e snapshot/cache, oltre ai rifiuti metodologici.

Suite derivata 1.053 domande: 473 consultazioni/calcoli e 580 rifiuti. Copertura derivata dall’audit: 181/225 effettivi, 130/181 sorgente, 44 residui; zero ambientali senza adapter. 58 collegamenti tipizzati e 29 companion conservati. Tre carichi descrittivi regionali portano la baseline a 84, senza soglia o promessa di prestazioni. Report `reports/a6-regional/`.

Quick locale canonico prima del push e Full locale canonico in clone freddo distinto (Quick incluso) prima della prontezza per il merge, più Quick→Full CI sul medesimo albero candidato. Merge e pubblicazione manuali del proprietario. A6.4 resta parziale; revisione metodologica e validazione delle letture A6.5–A6.6 aperte; A7 non avviata.
