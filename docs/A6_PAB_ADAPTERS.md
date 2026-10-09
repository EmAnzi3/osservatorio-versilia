# A6 v24 — PAB approvato e stato operativo

Sette carrier già pubblicati diventano interrogabili senza acquisire o modificare dati. Le fonti congelate sono `bonifica-rischio-v126.json`, `a3-pab-native-source-verification-2026.json` e `bonifica-rischio-v126-status.json`. Il primo separa export comunali e Allegato A-1; il secondo conserva i record nativi del PDF; il terzo conserva gli aggregati della fotografia WFS del 31 agosto 2026, ore 17:19:31 +02:00.

## Universi e unità

| Carrier | Universo e misura | Periodo del motore |
|---|---|---|
| pabProgrammedInterventionLength | Somma Metri degli export comunali / 1000: km-intervento | 2026, export acquisiti il 31 agosto |
| pabProgrammedInterventions | Codici univoci approvati dell'Allegato A-1 | PAB 2026, DGR 367 del 30 marzo |
| pabProgrammedMaintenanceValue | Importi approvati A-1, da centesimi nativi | PAB 2026 |
| pabInterventionsInProgress | Feature operative con lavori_inizio presente e lavori_fine vuoto | 2026-08-31 |
| pabInterventionsCompleted | Feature operative con lavori_fine presente | 2026-08-31 |
| pabInProgressOperationalGrossValue | importo_lordo delle feature in corso | 2026-08-31 |
| pabCompletedOperationalGrossValue | importo_lordo delle feature completate | 2026-08-31 |

`total` conserva ciascun valore pubblico; confronto e rango descrivono soltanto la misura selezionata. Per i due conteggi operativi, `share:operational` aggiunge la quota della fase selezionata su tutte le feature operative comunali dello stesso snapshot. Il token pubblico 2026 dei quattro carrier operativi viene esplicitamente tradotto in 2026-08-31; non diventa un consuntivo annuale.

| Comune | Codici A-1 | EUR approvati | Feature operative | In corso | Completate | km-intervento export |
|---|---:|---:|---:|---:|---:|---:|
| Camaiore | 341 | 1.060.763,74 | 342 | 91 | 150 | 270,094 |
| Forte dei Marmi | 27 | 98.194,06 | 27 | 0 | 13 | 18,410 |
| Massarosa | 464 | 1.998.372,37 | 469 | 6 | 1 | 317,413 |
| Pietrasanta | 182 | 821.438,02 | 182 | 43 | 68 | 174,004 |
| Seravezza | 52 | 370.837,00 | 51 | 26 | 7 | 50,704 |
| Stazzema | 91 | 392.752,72 | 92 | 56 | 9 | 71,776 |
| Viareggio | 102 | 454.075,17 | 102 | 0 | 0 | 101,693 |
| Totale | 1.259 | 5.196.433,08 | 1.265 | 222 | 248 | 1.004,094 |

Allegato A-1 CB1: 5.328 codici distinti nel ledger completo, 16.119.754,60 EUR, una riga NULL non assegnata a nessun Comune; non viene trasformata in zero o attribuita alla Versilia. Il lotto riaggrega i record dei sette comuni in centesimi, controlla identità, codice, pagina fisica 10–56 e digest del ledger `11f4159a315569587cafdbebc20df96139b9fb8794bbfcc68c9caa08b87ea15c`. PDF SHA-256 `c97b4c3dc7d1ac838121c381a279a41335cc012fb3823d9d073f91d626c6c0d9`. Il totale CB1 non è un benchmark comunale; A-3 e altri consorzi non vengono mescolati.

## Stato operativo e limiti

WFS `cb_pmo_lineare` al 31 agosto: CSV SHA-256 `81cb1aa82f7df4b4243f4372e35e5ab7bac2624e42ded67c25a6e1a911f4f322`. Il join già attestato associa le 1.265 righe degli export a 1.265 feature distinte: 1.244 codici 2026CB1E, 16 codici 2026CB1P e cinque senza codice_rt. Le collisioni identiche Quadrellara risultano risolte uno-a-uno nel processo di acquisizione. Questo adapter verifica il contratto del matching e gli aggregati congelati; lo snapshot non contiene un ledger completo di ID WFS e date lavori individuali, quindi **non riproduce indipendentemente quel join o la classificazione di ogni record**.

Le 251 feature puntuali globali condividono ID con il layer lineare: rappresentazione alternativa, non altri interventi da sommare. Le tre fasi programmato/in_corso/completato sono partizioni dello stesso universo operativo. Importi e metri operativi sono già pubblicati a due decimali: i sette subtotali riconciliano gli aggregati con la sola tolleranza numerica di 1e-8, senza margini aggiuntivi di centesimi o metri; questo non equipara gli importi operativi al budget A-1. L'importo lordo operativo complessivo è 4.165.243,17 EUR, distinto dagli importi arrotondati del CSV comunale e dai 5.196.433,08 EUR approvati.

Weighted ratio è consentito soltanto sulle due quote di feature operative: somme dei numeratori e dei denominatori entro i comuni selezionati, mai media delle percentuali. In corso 222/1265 × 100 ≈ 17,5494%; completate 248/1265 × 100 ≈ 19,6047%. Massarosa + Viareggio: denominatore 571, numeratori rispettivamente 6 e 1. **248/1259 è rifiutato come quota di attuazione del piano approvato**: i due inventari non sono omologhi. Gli zeri documentati restano zero; n.d. resta un'esclusione esplicita con opt-in per confronti parziali. Un denominatore nullo non genera una quota.

Km-intervento non è reticolo fisico unico: attività ripetute sullo stesso tratto restano separate. Le 49 feature senza geometria per 28.562,44 m di attività impediscono di derivare superficie/lunghezza fisica manutenzionata o una quota di reticolo. Importo approvato, importo lordo operativo e spesa pagata/liquidata/certificata sono distinti. Completamento registrato non prova efficacia, riduzione del rischio o condizioni attuali del corso d'acqua. Serie, trend, variazioni, anomalie e correlazioni automatiche restano rifiutati. La definizione regionale A-1 non è ancora certificata omogenea fra consorzi, e manca un pannello nazionale omologo: nessun benchmark Toscana/Italia inventato.

## Verifiche e avanzamento

63 osservazioni fisse indipendenti per catalogo, quattro quote aggregate, evidenze risolvibili, guardie su record duplicati, centesimi frazionari, fingerprint, unità, matching, rappresentazioni puntuali, data/regola di stato, importi negativi, conteggi frazionari, totali, valori pubblici, storico inventato e invalidazione della cache fra query. La validazione del ledger si riusa soltanto entro lo stesso selettore e viene rifatta a ogni nuova query, anche se il dizionario nativo in memoria è stato modificato.

Copertura derivata 152/225 effettivi e 104/181 sorgente; 73 residui e nove ambientali. Suite 518 domande, 253 calcoli e 265 rifiuti; 54 collegamenti tipizzati e 61 carichi descrittivi. I due collegamenti PAB sono contesto, senza calcolo di correlazione o conclusioni causali. Report in `reports/a6-pab/`. Dati, UI, asset, golden, Camaiore, workflow, Radar, 35 letture territoriali e due riepiloghi conservati. A6.4 parziale, revisione A6.5–A6.6 aperta; A7 non avviata. Gate canonici Quick/Full locali e CI prima del merge del proprietario.
