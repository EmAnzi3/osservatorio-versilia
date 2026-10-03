# A3 — chiusura del perimetro semplice

Decisione operativa del 3 ottobre 2026: utilizzare storici già disponibili e confronti Toscana/Italia ufficiali pronti, senza ricostruzioni territoriali, GIS o recuperi onerosi. Le opportunità non acquisite restano documentate nella matrice derivata; non sono tutte attività necessarie per chiudere questa fase.

## Conteggio e termine della fase

| Perimetro | Esito |
| --- | --- |
| Situazione dopo i lotti #318 e #319 | 115 storici pubblici derivati, 137 benchmark; 79 opportunità storiche e 76 benchmark ancora `AVAILABLE_MISSING` |
| Prima lista di 25 candidati storici | 4 implementati, 3 pronti per l'ultimo lotto, 18 rinviati o esclusi dal perimetro semplice |
| Ultimo lotto | `foreignResidents` 2024–2025, `incomeSourceProfile`, `pensionIncomeShare` |
| Dopo l'ultimo lotto | Publication contract locale: 118/118 storici e 137/137 benchmark pubblici, zero gap. Certificazione GitHub finale ancora da verificare |
| Lista di 8 candidati benchmark | 0 pronti; 4 esclusi dal lotto semplice e 4 rinviati dopo il controllo breve |

Dei 21 candidati storici rimasti dopo #318/#319, 14 sono stati controllati nelle famiglie fonte sotto: 3 pronti e 11 rinviati. Altri 7 sono esclusi dal lotto semplice: `ageDistribution`, `cohabitingHouseholds`, `householdSize`, `taxpayersAdultPopulationRate`, `motorization`, `wasteServiceCost`, `tourismIntensity`. Richiedono raccordi tra fasce o definizioni, denominatori annuali, recuperi ulteriori o verifiche non già disponibili. L'esclusione non dichiara l'assenza dei dati ufficiali.

**Le acquisizioni di questa fase terminano con l'ultimo lotto di tre storici.** Seguono soltanto QA, verifica dei gate e aggiornamento dell'handoff. Approvazione esplicita del proprietario e merge sono necessari per la chiusura formale; nessun merge o deploy è autorizzato da questo documento.

## Decisioni per famiglia fonte

| Famiglia | Esito del controllo breve | Azione finale |
| --- | --- | --- |
| Istat, lavoro e istruzione: 5 storici | Accesso alle fonti non concluso entro il limite; timeout. Nessun pannello completo certificato. | Rinviare tutti e cinque; non riaprire scansioni onerose. |
| Istat RCS: 1 storico | `foreignResidents` 2024–2025 pronto, stessa definizione e copertura comunale. | Integrare nell'ultimo lotto. |
| MEF: 3 storici | `incomeSourceProfile` e `pensionIncomeShare` pronti dai componenti annuali. `incomeDistribution` presenta celle soppresse e non consente una serie completa omogenea. | Integrare due; rinviare la distribuzione senza stimare le celle soppresse. |
| ACI: 1 storico della lista controllata | Archivio ufficiale HTTP 503; accesso fallito, non prova di indisponibilità. | Rinviare; nessun nuovo tentativo oneroso nella fase. |
| RSA: 1 storico | Fonte individuata come PDF di 22 pagine; manca un pannello storico comunale pronto e riconciliato. | Rinviare l'estrazione e il raccordo. |
| Turismo mensile: 1 storico | File mensile storico equivalente non trovato nel controllo breve. | Rinviare; conservare gli storici turistici già integrati. |
| ARPAT: 2 storici e 2 benchmark | Tavola storica comunale delle classi trovata, ma manca lo storico dei km eccellenti per la seconda componente. Accessi agli allegati CSV/PDF non conclusi, anche HTTP 403. I totali regionali 2025 includono 269 aree marine e 8 interne; il catalogo è marino. | Rinviare i quattro candidati; non inserire percentuali di perimetro diverso né ricostruire le aree. |
| ISPRA: 2 benchmark | Le fonti distinguono mosaicatura 2020 elaborata nel 2021, popolazione 2011, e nuove elaborazioni 2024 con popolazione 2021. Nessuna tavola esatta riconciliata con i sette valori pubblici del riferimento 2021. | Rinviare entrambi; nessuna sostituzione di anno o metodologia e nessun GIS. |

## Otto confronti: decisione conclusiva

| Stato nel lotto semplice | ID | Motivo |
| --- | --- | --- |
| Esclusi: 2 | `ftthReachedHouseholds`, `ftthUnreachedHouseholds` | Snapshot AGCOM: celle native mancanti in Toscana e Italia; nessuna ricostruzione dalle percentuali. Le due percentuali FTTH sono già nei 137 acquisiti. |
| Escluso: 1 | `fuelPrices` | Catalogo: mediane comunali del 28 agosto 2026. Dato MIMIT pronto: media aritmetica regionale giornaliera extra-autostradale; metodo e fotografia diversi. |
| Escluso: 1 | `evPoints` | Nessuna fotografia equivalente dei punti attivi e del denominatore già certificata; il conteggio corrente PUN non basta. |
| Rinviati: 2 | `bathingWaterQuality`, `bathingNonCompliantSamples` | Totale regionale con acque interne, contro perimetro marino pubblico. |
| Rinviati: 2 | `floodExposure`, `landslideExposure` | Periodo e metodologia esatti non riconciliati nel controllo breve. |

Non modificare manualmente gli stati della matrice: un'acquisizione diventa `ACQUIRED` soltanto per evidenza strutturale e pubblicazione verificata. `AVAILABLE_MISSING` continua a descrivere un'opportunità dati, anche quando esclusa dal lavoro corrente. I 76 benchmark mancanti non impediscono la chiusura del perimetro concordato e non richiedono di dimostrare l'esaurimento delle fonti.

## Evidenze riproducibili

- Istat RCS: `data/source-snapshots/istat-rcs-demography-2025.json`, campo `sources`; [cittadinanza 2025](https://demo.istat.it/data/rcs/Dati_RCS_cittadinanza_2025.zip).
- MEF: `data/source-snapshots/mef-income-lotto-a-2024.json`, campi `source` e `towns`; [archivio ufficiale](https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php).
- AGCOM: `data/source-snapshots/a3-agcom-benchmark-2025.json`, campi `benchmarks` e `blocked`.
- ARPAT: `data/source-snapshots/costa-mare-v123.json`, campi `sources`, `bathingWaterQuality2025` e `bathingNonCompliantSamples2025`; [classificazioni storiche comunali](https://www.arpat.toscana.it/app/uploads/datiemappe/dati/aree-di-balneazione-classificazioni/balneazione-qualita-aree-2010-2024.pdf), [controlli storici](https://www.arpat.toscana.it/datiemappe/aree-di-balneazione-controlli-e-superamenti/), [rapporto 2025](https://www.arpat.toscana.it/app/uploads/2026/07/controllo-acque-balneazione-2025.pdf), tabelle 4, 24, 26 e 27.
- ISPRA: [periodi e metodologia alluvioni](https://indicatoriambientali.isprambiente.it/it/pericolosita-da-alluvione/popolazione-esposta-ad-alluvioni) e [popolazione esposta a frane](https://indicatoriambientali.isprambiente.it/it/pericolosita-da-frana/popolazione-esposta-frane).
- Carburanti e ricarica: [metodo MIMIT](https://www.mimit.gov.it/it/prezzo-medio-carburanti/regioni), [PUN](https://pun.piattaformaunicanazionale.it/).
- Residui complessivi: `data/source-snapshots/a3-benchmark-residual-evidence.json`; conteggi da matrice A3 strict e publication contract, senza inventari manuali sostitutivi.

## Estensione successiva autorizzata sui cinque Istat

Il 3 ottobre 2026 il proprietario autorizza cinque storici Istat e calcoli semplici, con ACI escluso. Diploma 25–64: 1991/2001/2011 e 2024 invariato, discontinuità censuaria esplicita. I workbook A misura di Comune aggiungono componenti Totale per occupazione/disoccupazione/attività 15 anni e più (2019, 2021–2023) e diploma/terziario 25–49 (2018–2023), tutti 7/7 Comuni. Attività = 100 − inattività. Queste fasce restano distinte dalla lettura base 25–64; non ricostruire aggregati mancanti. Target totale 123 indicatori con storico/137 benchmark: 119 nella lettura base, quattro nelle componenti selezionabili; cinque indicatori ricevono nuove componenti. Pubblicazione locale 123/123 e 137/137 verificata; 44 casi browser confronto/Comune desktop/mobile PASS, 15 negativi nativi e 13 negativi di pubblicazione PASS. Quick locale si arresta al limite noto Percorsi/Leaflet CDN dopo i controlli dati, build, grafici e 105 fisarmoniche; coerenza 250 pagine, 7/7 stemmi e 40/40 baseline visive PASS, senza cambiare soglie/golden. Non dichiarare Full/Quick completi verdi o Ready prima della certificazione richiesta. Le richieste SDMX restano documentate come bloccate; acquisizione del lotto conclusa, non proseguire ricerche o riaprire altri candidati.
