# Audit v1.39.0 — Bilanci: liquidità, accantonamenti e missioni

Data audit: 13 settembre 2026

Baseline: `main` al commit `2592a4694c89fc80f30fd643e0efc6acb67e30d5` (merge PR #181, release pubblicata v1.38.0).

Questa tranche estende il tema Bilanci senza ridefinire gli indicatori esistenti. In particolare resta invariato `tourismDevelopmentMissionExpenditurePerResident`, che rappresenta la somma degli impegni delle Missioni 07 e 14 rapportata ai residenti.

## Stato attuale del tema Bilanci

La pipeline storica v1.6.0 usa Rendiconto OpenBDAP e SIOPE, con storico 2019–2025 e copertura 7/7 per il perimetro già pubblicato. Le missioni già materializzate sono 04, 05+06, 07+14, 09, 10 e 12. La v1.29.0 aggiunge il profilo finanziario/debito con letture 10.4 ricostruita, 6.1 e 10.3.

La v1.39 estende la stessa famiglia di snapshot/materializzatori. Non viene creata una pipeline contabile parallela.

## Esito sintetico

| Candidato | Fonte/campo 2025 | Copertura 2025 | Esito v1.39 |
| --- | --- | ---: | --- |
| FCDE per residente | OpenBDAP, Allegato A, codice 0491 `Fondo crediti di dubbia esigibilità al 31/12`, `Totale di Gestione` | 7/7 | **GO** |
| Fondo cassa finale per residente | OpenBDAP, Allegato A, codice 0495 `Fondo di cassa al 31 dicembre`, `Totale di Gestione` | 7/7 | **GO** |
| Missione 01 per residente | Spese riepilogo missioni, M01, `Impegni` | 7/7 | **GO** |
| Missione 08 per residente | Spese riepilogo missioni, M08, `Impegni` | 7/7 | **GO** |
| Missione 11 per residente | Spese riepilogo missioni, M11, `Impegni` | 7/7 | **GO** |
| Missione 14 per residente | Spese riepilogo missioni, M14, `Impegni` | 7/7 | **GO** |
| Missione 17 per residente | Spese riepilogo missioni, M17 | 4/7 righe, di cui Camaiore zero esplicito | **NO-GO** |
| PDI 3.1 | Piano indicatori, tipologia 03 / indicatore 01 | 3/7 righe esplicite | **NO-GO** |
| PDI 3.2 | Piano indicatori, tipologia 03 / indicatore 02 | 3/7 righe esplicite | **NO-GO** |
| `1450 / 1400` come quota cassa vincolata generale | SIOPE/OPI stock | semantica non idonea | **NO-GO** |
| Flussi art. 195 TUEL | SIOPE movimenti cumulati | fonte centrale disponibile come dump, interrogazione filtrata non esposta dal wrapper pubblico usato dalla repo | **RINVIO** |

Il perimetro minimo coerente della v1.39 è quindi di **6 nuovi indicatori**. Nessun candidato escluso viene sostituito con proxy o zero ricostruiti senza prova.

## FCDE

Fonte primaria: Rendiconto OpenBDAP, Schemi di bilancio, `Allegato A — Prospetto dimostrativo del risultato di amministrazione`.

Il probe 2025 identifica per tutti i sette Comuni la riga ufficiale:

- codice `0491`;
- descrizione `Fondo crediti di dubbia esigibilità al 31/12`;
- valore `Totale di Gestione`.

Valori assoluti 2025 verificati:

| Comune | FCDE 2025 |
| --- | ---: |
| Camaiore | 14.240.754,05 € |
| Forte dei Marmi | 7.277.368,00 € |
| Massarosa | 11.078.011,94 € |
| Pietrasanta | 9.212.517,16 € |
| Seravezza | 7.585.000,00 € |
| Stazzema | 570.942,52 € |
| Viareggio | 77.527.811,19 € |

Metrica pubblica: `FCDE / popolazione residente`. Il valore assoluto resta disponibile nel dettaglio. L'aggregato Versilia è `Σ FCDE / Σ residenti`, non la media semplice dei sette rapporti.

Il FCDE è un accantonamento del risultato di amministrazione a presidio del rischio di mancata riscossione dei crediti di dubbia e difficile esazione; non viene descritto come quota di crediti che l'ente “sa di non incassare”.

Controllo di riconciliazione del nuovo snapshot: il codice 0491 deve essere confrontato, quando il campo totale è identificabile senza ambiguità, con `Allegato a/1 — Quote accantonate` e con il prospetto `Allegato C — FCDE`. Eventuali differenze bloccano la materializzazione; non vengono corrette manualmente.

Stato: **GO**.

## Liquidità: fondo cassa finale

Il candidato omogeneo che supera il gate è lo stock di cassa di fine esercizio direttamente esposto dall'OpenBDAP nello stesso Allegato A:

- codice `0495`;
- descrizione `Fondo di cassa al 31 dicembre`;
- valore `Totale di Gestione`.

Valori assoluti 2025 verificati:

| Comune | Fondo cassa al 31/12/2025 |
| --- | ---: |
| Camaiore | 8.104.846,43 € |
| Forte dei Marmi | 47.669.797,59 € |
| Massarosa | 7.030.169,59 € |
| Pietrasanta | 37.276.807,73 € |
| Seravezza | 5.188.811,87 € |
| Stazzema | 449.403,31 € |
| Viareggio | 46.361.668,52 € |

Metrica pubblica: `fondo cassa al 31 dicembre / popolazione residente`. L'aggregato Versilia è `Σ fondo cassa / Σ residenti`.

È uno **stock di cassa totale**, non un indicatore di cassa libera o immediatamente spendibile. Può comprendere somme soggette a vincoli e non misura da solo solidità, efficienza o capacità di pagamento. La polarità resta neutra.

Non duplica `cashBalancePerResident`: quest'ultimo deriva dai movimenti SIOPE dell'anno e misura il saldo fra incassi e pagamenti; il nuovo indicatore misura invece la consistenza del fondo cassa a fine esercizio.

Stato: **GO**.

## Cassa vincolata

### Rapporto stock 1450/1400

Il codice SIOPE/OPI 1450 ha etichetta sintetica di quota vincolata del fondo cassa 1400, ma la documentazione OPI lo riferisce alle giacenze del conto di tesoreria vincolate per pignoramenti. Non rappresenta quindi l'intera cassa vincolata dell'ente ai sensi della disciplina contabile/TUEL.

Le disponibilità 2200/2400 riguardano fondi vincolati su conti diversi dal conto ordinario di tesoreria e non consentono di ricostruire con una somma automatica uno stock generale omogeneo della cassa vincolata.

Conclusione: **non pubblicare `1450 / 1400` come “quota di cassa vincolata”**.

### Flussi art. 195 TUEL

SIOPE prevede codici specifici per utilizzo e reintegro degli incassi vincolati ex art. 195 TUEL. Sono concettualmente utili, ma sono flussi e non stock; il volume lordo può includere più cicli di utilizzo/reintegro nello stesso esercizio.

La repo dispone già dei dump SIOPE centrali versionati con URL e SHA-256. Tuttavia il wrapper API pubblico BDAP usato dall'Osservatorio non espone nel percorso testato un endpoint `datastore_search` filtrabile: il probe ha ricevuto HTTP 404. Sarebbe tecnicamente possibile rileggere i dump regionali completi, ma dopo l'ammissione del fondo cassa finale ciò aggiungerebbe complessità senza essere necessario a chiudere coerentemente la v1.39.

Conclusione: **rinvio a un lotto dedicato sulla gestione della liquidità**, senza scraper comunali e senza proxy.

## Anticipazioni di tesoreria — PDI 3.1 e 3.2

Il Piano degli indicatori resta la fonte metodologicamente preferibile rispetto ai flussi lordi delle anticipazioni. Il gate 2025, però, non raggiunge la copertura richiesta:

- Camaiore: 3.1 = 0 esplicito; 3.2 = 0 esplicito;
- Seravezza: 3.1 = 0 esplicito; 3.2 = 0 esplicito;
- Stazzema: 3.1 = 0 esplicito; 3.2 = 0 esplicito;
- Forte dei Marmi, Massarosa, Pietrasanta, Viareggio: righe 3.1 e 3.2 assenti.

L'assenza di riga non viene trasformata in zero. Neppure i flussi lordi di Titolo 7/Titolo 5 vengono usati come sostituti, perché più utilizzi e rimborsi possono alterarne la lettura.

Stato: **NO-GO v1.39**. Potranno essere rivalutati in un lotto futuro se una fonte ufficiale consente di distinguere in modo dimostrabile zero e mancata trasmissione.

## Missioni

Fonte: `Rendiconto SDB Spese Riepilogo Missioni_TOSCANA.csv`, campo `Impegni`; denominatore: popolazione residente al 1° gennaio dello stesso esercizio, coerente con la pipeline Bilanci esistente.

Formula comune: `impegni della missione / popolazione residente`.

### Missioni ammesse

M01, M08, M11 e M14 hanno nel 2025 una riga unica e un valore numerico per ciascuno dei sette Comuni.

La Missione 01 resta una lettura descrittiva della spesa per servizi istituzionali, generali e di gestione: non viene etichettata come efficienza, costo della burocrazia o peso della macchina amministrativa.

La Missione 14 viene aggiunta come indicatore autonomo senza modificare, rinominare o ricostruire `tourismDevelopmentMissionExpenditurePerResident`, che continua a rappresentare M07 + M14.

### Missione 17 esclusa

Nel 2025:

- Camaiore: riga presente e impegni pari a zero;
- Massarosa: 18.148,71 €;
- Seravezza: 40.000,00 €;
- Stazzema: 18.546,35 €;
- Forte dei Marmi, Pietrasanta, Viareggio: riga M17 assente.

La coesistenza nello stesso dataset di un vero zero esplicito e di righe assenti dimostra che `assenza → 0` non è una trasformazione accettabile. M17 resta quindi **NO-GO** per questa release. Inoltre un valore nullo non significherebbe assenza di interventi energetici, perché spese di efficientamento, illuminazione o opere possono essere imputate ad altre missioni/programmi.

## Perimetro definitivo v1.39.0

La tranche target contiene **6 nuove metriche**:

1. `fcdePerResident` — Fondo crediti di dubbia esigibilità per residente;
2. `yearEndCashFundPerResident` — Fondo cassa al 31 dicembre per residente;
3. `generalAdministrationMissionExpenditurePerResident` — Missione 01;
4. `territorialPlanningMissionExpenditurePerResident` — Missione 08;
5. `civilProtectionMissionExpenditurePerResident` — Missione 11;
6. `economicDevelopmentMissionExpenditurePerResident` — Missione 14.

Prima della materializzazione pubblica lo storico viene ricostruito dai raw OpenBDAP annuali con gate 7/7 per ciascun indicatore/annualità. Un'annualità incompleta non viene riempita o interpolata.

## Esclusioni v1.39

Restano fuori:

- Missione 17;
- PDI 3.1 e 3.2;
- rapporto 1450/1400 come cassa vincolata generale;
- flussi art. 195 TUEL, rinviati a un lotto dedicato;
- fiscalità locale;
- indicatore di tempestività dei pagamenti in assenza di una fonte centrale PCC/RGS pubblica, strutturata e riproducibile;
- generici aggregati di “tasse comunali”.

## Contratto CI della Fase 2

Prima del browser QA devono passare:

- inventory dei workflow e rispetto di `ci/workflow-contract.json`;
- required checks canonici `quick` e `full`;
- build smoke canonico;
- audit `paths` del workflow specializzato v1.39;
- controllo build non mutante;
- test di retrocompatibilità v1.6 e v1.29;
- gate 7/7 e zero-vs-n.d. sul perimetro ammesso;
- snapshot ufficiali versionati con hash dei file sorgente;
- verifica dei file che il materializzatore può modificare;
- nessun indebolimento dei gate esistenti.

Il workflow v1.39 è registrato nell'inventario CI come `specialized-gate`. Le eccezioni, se necessarie, devono essere specifiche, documentate e fail-closed.
