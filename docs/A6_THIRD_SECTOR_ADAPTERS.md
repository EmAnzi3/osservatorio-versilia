# A6 — Terzo settore RUNTS

Un carrier `thirdSector`, tre viste: `total` (densità pubblica non arrotondata, ogni 1.000 residenti), `registeredEntities` (conteggio) e `nativeRatio` (componenti del rapporto). La stringa formattata a due decimali non sostituisce il valore numerico. Confronto e rango sono descrittivi; il rapporto ponderato è ammesso soltanto nella vista nativa, sommando i conteggi e le popolazioni dei Comuni selezionati.

La fotografia RUNTS è dell'11 ottobre 2026, in tutte le sezioni, per codice fiscale univoco e sede legale corrente. Il denominatore Istat è del 1° gennaio 2026. `2026` è un alias della fotografia, mai una media annuale; le osservazioni conservano la data esatta e i rapporti nativi espongono separatamente le date dei componenti. Le sedi non misurano attività, servizi, persone occupate o volontari, né tutte le associazioni locali.

| Comune | Enti | Residenti 1 gennaio 2026 |
|---|---:|---:|
| Camaiore | 85 | 31.763 |
| Forte dei Marmi | 24 | 6.550 |
| Massarosa | 53 | 21.782 |
| Pietrasanta | 67 | 22.678 |
| Seravezza | 50 | 12.284 |
| Stazzema | 13 | 2.783 |
| Viareggio | 173 | 60.680 |

Il rapporto Versilia è `465 / 158520 × 1000 = 2,9333838001514003`. Non è la media semplice dei sette tassi. Le sedi legali attribuite una volta al Comune rendono additivi i conteggi della fotografia; ciò non dimostra una distribuzione disgiunta delle attività svolte dagli enti. I sottogruppi usano soltanto i propri componenti.

## Evidenza e limiti

`data/source-snapshots/runts-public-2026-10-11.json` congela gli aggregati normalizzati e l'hash dell'Excel ufficiale verificato dalla manutenzione #411. Il workbook e i record personali individuali non sono versionati: l'adapter rigioca gli aggregati, non la deduplicazione dei codici fiscali o l'attribuzione originaria delle sedi. Le popolazioni sono congelate separatamente nei componenti; nessuna retro-derivazione da tassi arrotondati. Il lotto non acquisisce dati e non cambia il catalogo pubblico.

Hash dei byte, fingerprint completo dell'oggetto e fingerprint del carrier pubblico sono verificati anche dopo la cache; tutte le identità comunali, formule e somme territoriali sono riconciliate. La provenienza conserva il puntatore pubblico, il puntatore alla riga normalizzata, l'hash del documento originario e il perimetro reale del replay. `nativeRecordReplayAvailable=false` distingue l'evidenza aggregata dai record originali.

Storici, variazioni e trend sono rifiutati: le sedi correnti non ricostruiscono i trasferimenti del 2025 e i tassi legacy non sono una baseline riconciliata. Toscana/Italia e il gap verso Versilia, anomalie, categorie RUNTS e coppie con altri indicatori non sono stati revisionati. Il rapporto nativo Versilia è disponibile come pooling esplicito, non come benchmark inferito. Rango numerico diverso da qualità o priorità politica.

## Verifiche

21 osservazioni e 14 componenti fissati indipendentemente; due rapporti aggregati (intera Versilia e Camaiore/Massarosa), controllo della differenza dalla media semplice, provenienza, date esatte/alias e rifiuti. Prove ostili modificano dati, definizioni, identità, formule, date, hash e oggetti dopo cache, oltre ai byte su disco a cache fredda. Le 81 nuove domande preservano esattamente le 2.847 precedenti: 2.928 PASS (1.596 letture/calcoli, 1.332 rifiuti). Sei carichi rappresentativi aggiunti alla baseline prestazionale descrittiva, senza soglie portabili.

Copertura derivata dal catalogo effettivo corrente: 217/225, otto residui; sorgente 160/181. Report in `reports/a6-third-sector/`. A6.4 resta parziale, A6.5–A6.6 aperte, A7 non avviata. Quick locale completo prima del push, Full locale completo e CI Quick→Full/A3 sullo stesso albero prima della prontezza; merge del proprietario.
