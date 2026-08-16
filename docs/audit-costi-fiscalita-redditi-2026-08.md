# Audit dati — costi, fiscalità, inflazione e redditi

Data audit: **15 agosto 2026**  
Base iniziale: `main` @ `4c6f978043c98f34e1f1b186c4483d8be6e0f910` — **v1.12.0**, 121 indicatori (117 inline + 4 climatici esterni).

## Esito aggiornato

| Candidato | Copertura | Annualità | Fonte primaria | Esito |
|---|---:|---|---|---|
| Addizionale comunale IRPEF effettiva | 7/7 | 2025 | MEF — Dipartimento Finanze; Comune di Seravezza per conferma 2025 | **PROMOSSO** |
| TARI, 3 persone / 100 m² | 7/7 | 2025 | MEF / Comuni + ARERA | **PROMOSSO** |
| IMU, seconda abitazione standard | 7/7 | 2025 | MEF — Dipartimento Finanze | **PROMOSSO** |
| Prezzi carburanti self | 6/7 | 14/08/2026 | MIMIT | **PROMOSSO 6/7; Stazzema n.d.** |
| Mensa scolastica | non omogenea | 2025/26 | Comuni | **ESCLUSO** |
| Costo gestione rifiuti CTOTab | 7/7 | 2024 | ISPRA — Catasto Rifiuti | **PROMOSSO** |
| NIC prezzi al consumo | provinciale disponibile | 2011+ | ISTAT | **PROMOSSO; estrazione Provincia di Lucca da chiudere** |
| Reddito complessivo medio | definizione corrente 7/7 | anni recenti | MEF | **MANTENUTO** |
| Reddito imponibile medio, serie lunga | 7/7 | 2011–2024 | MEF | **PROMOSSO COME SERIE LUNGA DISTINTA** |

## 1. Addizionale comunale IRPEF — PROMOSSO

L'indicatore confronta l'**importo annuo dovuto** applicando aliquote, scaglioni ed esenzioni allo stesso reddito imponibile teorico. Scenari: **20.000 € / 30.000 € / 50.000 €**.

| Comune | 20.000 € | 30.000 € | 50.000 € |
|---|---:|---:|---:|
| Camaiore | 82,50 € | 144,50 € | 284,50 € |
| Forte dei Marmi | 0,00 € | 153,00 € | 283,00 € |
| Massarosa | 160,00 € | 240,00 € | 400,00 € |
| Pietrasanta | 150,00 € | 225,00 € | 375,00 € |
| Seravezza | 160,00 € | 240,00 € | 400,00 € |
| Stazzema | 160,00 € | 240,00 € | 400,00 € |
| Viareggio | 150,00 € | 225,00 € | 375,00 € |

Per **Seravezza** la continuità 2025 è verificata sulla comunicazione ufficiale del Comune e sulla deliberazione consiliare n. 63 del 28/11/2024 depositata nel Portale del federalismo fiscale.

## 2. TARI — PROMOSSO 7/7

Standard: **utenza domestica residente, 3 componenti, 100 m², senza agevolazioni personali**. Il confronto include quota fissa, quota variabile, TEFA 5% e componenti perequative ARERA 2025 (`UR1 + UR2 + UR3 = 7,60 € per utenza/anno`).

| Comune | Spesa annua standardizzata |
|---|---:|
| Camaiore | 422,94 € |
| Forte dei Marmi | 475,73 € |
| Massarosa | 542,51 € |
| Pietrasanta | 356,11 € |
| Seravezza | 502,22 € |
| Stazzema | 365,31 € |
| Viareggio | 417,86 € |

Le verifiche aggiuntive hanno chiuso i due buchi precedenti:

- **Forte dei Marmi:** prospetto ufficiale 2025, 3 componenti = `1,39 €/m² + 306,84 €/anno`;
- **Pietrasanta:** prospetto ufficiale 2025, 3 componenti = `1,25 €/m² + 206,91 €/anno`.

Non sono quindi necessari valori `n.d.`.

## 3. IMU — PROMOSSO 7/7

Standard dichiarato:

> **Seconda abitazione A/2 — base imponibile IMU standardizzata 100.000 €**

È un benchmark di pressione fiscale: non viene inventata una rendita catastale “tipica”. La fattispecie omogenea nei prospetti MEF 2025 è **Altri fabbricati**.

| Comune | Aliquota | Imposta standardizzata |
|---|---:|---:|
| Camaiore | 1,14% | 1.140 € |
| Forte dei Marmi | 1,06% | 1.060 € |
| Massarosa | 1,06% | 1.060 € |
| Pietrasanta | 1,06% | 1.060 € |
| Seravezza | 1,14% | 1.140 € |
| Stazzema | 1,06% | 1.060 € |
| Viareggio | 1,14% | 1.140 € |

Copertura: **7/7** da prospetti ufficiali MEF 2025.

## 4. Carburanti — PROMOSSO 6/7

Fotografia MIMIT del **14 agosto 2026**. Indicatore: **mediana comunale dei prezzi self-service degli impianti attivi**, con selettore Benzina / Gasolio.

| Comune | Benzina self | Gasolio self |
|---|---:|---:|
| Camaiore | 1,999 €/l | 2,089 €/l |
| Forte dei Marmi | 1,979 €/l | 2,089 €/l |
| Massarosa | 1,987 €/l | 2,088 €/l |
| Pietrasanta | 1,999 €/l | 2,099 €/l |
| Seravezza | 1,994 €/l | 2,079 €/l |
| **Stazzema** | **n.d.** | **n.d.** |
| Viareggio | 1,994 €/l | 2,099 €/l |

Stazzema resta `n.d.` perché l'anagrafica MIMIT non registra impianti attivi. Non viene attribuito il prezzo di un Comune vicino. L'indicatore è collocato in **Mobilità → Mezzi, carburanti e infrastrutture**.

## 5. Mensa scolastica — ESCLUSO

Le strutture tariffarie comunali combinano in modo troppo diverso ISEE, esenzioni, sconti fratelli, residenza e modalità di pagamento. Il confronto richiederebbe troppe ipotesi per essere più informativo che fuorviante. Non viene integrato.

## 6. Costo del servizio rifiuti — PROMOSSO 7/7

Variabile ISPRA: **CTOTab — costo totale del servizio di igiene urbana, €/abitante/anno**. Sono state accettate esclusivamente righe riferite al singolo Comune (`N. comuni = 1`), quindi nessuna aggregazione sovracomunale.

| Comune | CTOTab 2024 |
|---|---:|
| Camaiore | 343,24 €/ab |
| Forte dei Marmi | 998,69 €/ab |
| Massarosa | 275,56 €/ab |
| Pietrasanta | 360,36 €/ab |
| Seravezza | 295,50 €/ab |
| Stazzema | 317,81 €/ab |
| Viareggio | 348,20 €/ab |

L'indicatore è collocato in **Ambiente → Rifiuti e circolarità**. Il valore descrive il costo del servizio, non la TARI pagata da una famiglia.

## 7. Inflazione — Provincia di Lucca

La documentazione ISTAT conferma che gli indici NIC sono diffusi anche a **livello provinciale** per divisione di spesa. Il confronto redditi–prezzi userà quindi, se l'estrazione SDMX viene validata, **NIC Provincia di Lucca**, non “Lucca città” e non il dato regionale Toscana.

Il grafico deve rendere evidente la domanda sostanziale:

> **i redditi nominali crescono davvero più dei prezzi?**

Le tre linee saranno indicizzate a 100 nello stesso anno base:

1. reddito imponibile medio dei sette Comuni della Versilia;
2. NIC — Provincia di Lucca;
3. reddito reale indicizzato = indice reddito / indice prezzi × 100.

Nota obbligatoria: **il perimetro dei prezzi è l'intera Provincia di Lucca, quello dei redditi sono i sette Comuni della Versilia**. Il grafico è quindi un confronto di contesto, non un'identità territoriale perfetta.

## 8. Storico redditi — criterio definitivo

L'indicatore principale del sito resta **Reddito complessivo medio dichiarato**. È stato verificato se fosse possibile estenderlo al 2011 sommando le fasce reddituali MEF degli anni in cui manca il totale diretto.

Il test ha escluso questa soluzione: negli anni in cui sono presenti sia il totale diretto sia le classi, le due basi **non coincidono**. Caso di controllo: **Camaiore 2023**, differenza tra totale diretto e somma delle classi pari a **56.506.620 € e 277 dichiaranti**.

Di conseguenza non viene costruita una falsa serie continua di “reddito complessivo”.

È invece disponibile e omogenea **7/7 dal 2011 al 2024** la serie MEF:

> **Reddito imponibile — Ammontare / Reddito imponibile — Frequenza**

Questa entra come **serie lunga esplicitamente distinta** nella vista del reddito. Il valore corrente continua a essere il reddito complessivo medio; lo storico lungo viene etichettato `Reddito imponibile medio · serie lunga 2011–2024`.

Valore aggregato dei sette Comuni, ottenuto come ammontare complessivo / frequenza complessiva:

| Anno | Reddito imponibile medio |
|---|---:|
| 2011 | 18.913,88 € |
| 2012 | 18.934,57 € |
| 2013 | 19.105,31 € |
| 2014 | 19.152,80 € |
| 2015 | 19.383,32 € |
| 2016 | 19.584,39 € |
| 2017 | 20.029,96 € |
| 2018 | 20.440,58 € |
| 2019 | 20.628,85 € |
| 2020 | 20.136,56 € |
| 2021 | 21.438,86 € |
| 2022 | 22.923,37 € |
| 2023 | 23.759,32 € |
| 2024 | 24.920,45 € |

## Decisione di implementazione del draft

Nel draft entrano:

- `municipalIrpef` — 7/7;
- TARI standardizzata — 7/7;
- IMU seconda abitazione standard — 7/7;
- prezzi carburanti — 6/7, Stazzema `n.d.`;
- costo servizio rifiuti CTOTab — 7/7;
- serie lunga del reddito imponibile 2011–2024 come vista dello storico, senza sostituire la definizione corrente del reddito complessivo.

La mensa scolastica viene esclusa. Il confronto redditi–inflazione viene finalizzato solo dopo la validazione dell'estrazione ufficiale **NIC Provincia di Lucca**.
