# Specifiche dei dossier pilota

Due dimostrazioni leggibili accompagnano queste specifiche: [lavoro](MASSAROSA_LAVORO.md) e [infanzia/scuola](MASSAROSA_INFANZIA_SCUOLA.md). Questi sei piloti sono specifiche tecniche, non sei dossier pubblici completi.

Cinque dossier sono sviluppabili come composizioni descrittive; casa è un pilota esplorativo prioritario. Le specifiche non approvano interventi né modificano le 35 letture A6. Non viene calcolato un indice politico dei Comuni.

Ogni esempio qui sotto è una richiesta realmente eseguita sul catalogo effettivo identificato nel riepilogo. Codici ISTAT e periodi sono quelli della query: non si estendono silenziosamente ai sette Comuni. La risposta leggibile conserva universo e unità; JSON completo e provenance sono riproducibili con lo script.

## Lavoro e trasformazioni produttive

**Domanda centrale:** La crescita economica localizzata si accompagna a opportunità per i residenti?

**Primo prodotto:** un percorso di contesto con capitoli fenomeno → servizi/risorse → limiti → istruttoria. Aprire con occupazione dei residenti per fascia/sesso, poi addetti e unità locali ASIA, composizione Frame e Atlante Registro Imprese. Gli storici rimangono interni a ciascuna fonte: le basi non formano una serie unica. Affiancare retribuzioni e redditi con platee esplicite, distinguendo nominale e indicatore reale autorizzato.

**Connessioni:** mobilita, redditi, capacita

**Lettura sostanziale verificabile:** Negli esempi selezionati Massarosa ha un tasso di occupazione residente 2024 superiore a Viareggio, mentre la crescita cumulata delle unità locali ASIA 2018–2023 è inferiore. Universi e intervalli differenti rendono visibili più trasformazioni; non identificano un unico giudizio di sviluppo o transizioni individuali.

**Domande da verificare:** La composizione industria/servizi cambia nei periodi realmente confrontabili?; Produzione nominale, addetti e redditi dei dichiaranti descrivono la stessa popolazione?

**Competenze da coinvolgere:** Comune: pianificazione e servizi locali; Regione: lavoro/formazione; imprese e parti sociali come interlocutori, non decisori comunali sostitutivi.

**Opzioni istruttorie:** Approfondire formazione, accessibilità delle aree produttive e sportelli, previa analisi di domanda e competenze.

**Monitoraggio proposto:** Occupazione residente per coorte, addetti localizzati e risultati dei programmi con denominatori separati.

**Dati che impediscono la decisione:** Transizioni professionali e qualità dei contratti; Pannello settoriale a prezzi costanti e dati recenti

**Criterio di accettazione:** le richieste seguenti e i rifiuti della matrice si riproducono; ogni numero mantiene la definizione; le lacune sono visibili nella conclusione. Nessuna decisione automatica.

### Esempio `census_employment_primary`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "employmentRate",
      "dimension": "total",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2024 | 73.4 | percent | resident population; 25–64 total residents |
| 046033 | 2024 | 71.9 | percent | resident population; 25–64 total residents |

**Fonte e metodo:** https://esploradati.istat.it/SDMXWS/rest; Istat published census carrier; explicit frozen source reconciliation.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `business_asia_employment`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "localEmployees",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2023 | 4938.33 | people | ASIA active local units; annual average employment at workplace; ASIA total |
| 046033 | 2023 | 22358.35 | people | ASIA active local units; annual average employment at workplace; ASIA total |

**Fonte e metodo:** https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500DICA,1.0/DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7; Istat ASIA snapshot via AgID; explicit source formulas.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `business_asia_cumulative`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "localUnitsChange",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2018-2023 | 6.991260923845188 | percent | ASIA active local units; annual average employment at workplace; ASIA total |
| 046033 | 2018-2023 | 9.226699859965759 | percent | ASIA active local units; annual average employment at workplace; ASIA total |

**Fonte e metodo:** https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500DICA,1.0/DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7; Istat ASIA snapshot via AgID; explicit source formulas.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `atlas_territory_2025`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "economyActivityAtlas",
      "dimension": "territoryTotal",
      "periods": [
        "2025"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046005 | 2025 | 3822 | number | registered active local units in the frozen territorial total |
| 046013 | 2025 | 1556 | number | registered active local units in the frozen territorial total |
| 046018 | 2025 | 1940 | number | registered active local units in the frozen territorial total |
| 046024 | 2025 | 3327 | number | registered active local units in the frozen territorial total |
| 046028 | 2025 | 1437 | number | registered active local units in the frozen territorial total |
| 046030 | 2025 | 245 | number | registered active local units in the frozen territorial total |
| 046033 | 2025 | 7998 | number | registered active local units in the frozen territorial total |

**Fonte e metodo:** https://www.regione.toscana.it/-/banca-dati-imprese-toscana; direct compact snapshot value; no hierarchy sums or imputation.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Valore rispetto a una scheda:** Evita di scambiare unità locali per imprese o addetti per occupati residenti.

## Infanzia, scuola e giovani

**Domanda centrale:** L’offerta educativa risponde ai bisogni delle famiglie e dei giovani?

**Primo prodotto:** un percorso di contesto con capitoli fenomeno → servizi/risorse → limiti → istruttoria. Descrivere ricettività potenziale e denominatore 3–36 mesi, poi classi, tempo pieno, edifici e perimetro scolastico. Affiancare lavoro femminile come contesto con periodo proprio. Richiedere bacini, domanda, frequenza e attese prima di dimensionare posti o sedi.

**Connessioni:** demografia, mobilita, investimenti

**Lettura sostanziale verificabile:** Nel confronto selezionato 2024/25 Massarosa presenta classi medie meno numerose e una quota primaria a tempo pieno maggiore di Viareggio. Il risultato riguarda organizzazione scolastica localizzata; bacini, accesso e qualità didattica richiedono evidenze ulteriori.

**Domande da verificare:** Posti potenziali, utenti effettivi e liste d’attesa sono distinti?; Le scuole localizzate nel Comune servono quali bacini?

**Competenze da coinvolgere:** Comune: servizi scolastici ed edilizia non provinciale; Provincia: edilizia secondaria superiore; scuole autonome/Regione per offerta e programmazione.

**Opzioni istruttorie:** Approfondire orari, trasporto, accessibilità e uso degli edifici; nessuna conclusione automatica scuole troppe/poche.

**Monitoraggio proposto:** Attese, frequenza, accessibilità, tempi e risultati per coorte; evitare attribuzione causale ai soli indicatori INVALSI.

**Dati che impediscono la decisione:** Utenti residenti, domanda inevasa, tariffe e orari; Bacini degli alunni, capienza effettiva e tempi di percorso

**Criterio di accettazione:** le richieste seguenti e i rifiuti della matrice si riproducono; ogni numero mantiene la definizione; le lacune sono visibili nella conclusione. Nessuna decisione automatica.

### Esempio `child_weighted`

```json
{
  "operation": "weighted_ratio",
  "selectors": [
    {
      "metric": "earlyChildhoodPotentialCapacityRate",
      "dimension": "total"
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046005 | 2024/25 | 40.596330275229356 | percent | resident children aged 3–36 months |
| 046013 | 2024/25 | 84.0 | percent | resident children aged 3–36 months |
| 046018 | 2024/25 | 29.292929292929294 | percent | resident children aged 3–36 months |
| 046024 | 2024/25 | 74.91525423728814 | percent | resident children aged 3–36 months |
| 046028 | 2024/25 | 0.0 | percent | resident children aged 3–36 months |
| 046030 | 2024/25 | 0.0 | percent | resident children aged 3–36 months |
| 046033 | 2024/25 | 53.018660812294186 | percent | resident children aged 3–36 months |

**Risultato dell’operazione:**

```json
{
  "value": 46.504285069914296,
  "unit": "percent",
  "numerator": 1031.0,
  "denominator": 2217.0,
  "scale": 100,
  "geographies": [
    "046005",
    "046013",
    "046018",
    "046024",
    "046028",
    "046030",
    "046033"
  ],
  "period": "2024/25",
  "aggregation": "ratio of sums; not mean of municipal ratios"
}
```

**Fonte e metodo:** https://dati.toscana.it/dataset/98ee6064-b61a-45e2-a790-86c55b278574/resource/01588909-8f0b-4b80-8af7-1749bab80a5e/download/opendata-_-da-pubblicare-24-25.csv; Tuscany explicit municipal capacity and children counts.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `school_class_size`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "studentsPerClass",
      "dimension": "total",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2024/25 | 17.805555555555557 | studentsPerClass | pupils in state and private schools located in the municipality; not resident children |
| 046033 | 2024/25 | 19.400516795865634 | studentsPerClass | pupils in state and private schools located in the municipality; not resident children |

**Fonte e metodo:** https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti; located-school pupils / classes.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `school_full_time`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "primaryFullTimeShare",
      "dimension": "total",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2024/25 | 55.287817938420346 | percent | pupils in state and private schools located in the municipality; not resident children |
| 046033 | 2024/25 | 46.80073126142596 | percent | pupils in state and private schools located in the municipality; not resident children |

**Fonte e metodo:** https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti; primary full-time pupils / all primary pupils * 100.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `female_weighted`

```json
{
  "operation": "weighted_ratio",
  "selectors": [
    {
      "metric": "femaleEmploymentRate",
      "dimension": "total"
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046005 | 2023 | 55.84045584045584 | percent | women resident aged 15–64 |
| 046013 | 2023 | 49.36086529006883 | percent | women resident aged 15–64 |
| 046018 | 2023 | 56.43635321100918 | percent | women resident aged 15–64 |
| 046024 | 2023 | 53.942953020134226 | percent | women resident aged 15–64 |
| 046028 | 2023 | 53.10186367117692 | percent | women resident aged 15–64 |
| 046030 | 2023 | 49.941656942823805 | percent | women resident aged 15–64 |
| 046033 | 2023 | 56.339951675596176 | percent | women resident aged 15–64 |

**Risultato dell’operazione:**

```json
{
  "value": 55.26488943831874,
  "unit": "percent",
  "numerator": 27717.0,
  "denominator": 50153.0,
  "scale": 100,
  "geographies": [
    "046005",
    "046013",
    "046018",
    "046024",
    "046028",
    "046030",
    "046033"
  ],
  "period": "2023",
  "aggregation": "ratio of sums; not mean of municipal ratios"
}
```

**Fonte e metodo:** https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip; Istat permanent census section additive variables.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Valore rispetto a una scheda:** Collega quantità, fruibilità e domanda non misurata senza equiparare alunni localizzati a residenti.

## Invecchiamento, autonomia e assistenza

**Domanda centrale:** Quali bisogni degli anziani sono osservati e quali restano non misurati?

**Primo prodotto:** un percorso di contesto con capitoli fenomeno → servizi/risorse → limiti → istruttoria. Separare pressione demografica 85+, famiglie unipersonali e servizi ARS. Il tasso standardizzato ha benchmark ufficiali ma non va ponderato dai conteggi grezzi. Spesa sociale, utenti unici, intensità e domanda inevasa sono passaggi distinti verso la copertura del bisogno.

**Connessioni:** sanita, welfare, abitazione

**Lettura sostanziale verificabile:** Massarosa mostra una quota 85+ POSAS 2026 inferiore a Viareggio e un tasso domiciliare standardizzato ARS 2024 superiore. Gli ordinamenti differenti aprono un’istruttoria su domanda, accesso e intensità; non dimostrano copertura migliore o bisogno minore.

**Domande da verificare:** Quota degli 85+ e assistenza standardizzata sono confrontabili come copertura?; Quanti bisogni di autonomia e cura restano fuori dai dati?

**Competenze da coinvolgere:** Comune e organismi di zona/SdS: integrazione sociale; azienda sanitaria: assistenza territoriale; Regione: programmazione. Accordi gestionali locali da verificare.

**Opzioni istruttorie:** Approfondire presa in carico integrata, trasporto sociale e sostegno ai caregiver con responsabili e platee verificate.

**Monitoraggio proposto:** Utenti unici, ore, attese, continuità e bisogni non soddisfatti; stock demografico come contesto.

**Dati che impediscono la decisione:** Non autosufficienza, caregiver e bisogni non soddisfatti; Utenti unici, intensità/ore di assistenza e attese

**Criterio di accettazione:** le richieste seguenti e i rifiuti della matrice si riproducono; ogni numero mantiene la definizione; le lacune sono visibili nella conclusione. Nessuna decisione automatica.

### Esempio `age85_mass`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "ageDistribution",
      "dimension": "age:85+",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2026 | 4.095124414654302 | percent | resident population at January 1 |
| 046033 | 2026 | 4.853328938694792 | percent | resident population at January 1 |

**Fonte e metodo:** https://demo.istat.it/data/posas/POSAS_2026_it_046_Lucca.zip; Istat POSAS single-age additive counts.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `ars_total`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "elderlyHomeCare",
      "dimension": "sex:total",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2024 | 30.085 | per1000 | ARS elderly resident reference population totale |
| 046033 | 2024 | 20.0936 | per1000 | ARS elderly resident reference population totale |

**Fonte e metodo:** https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=260; ARS published age-standardized measure.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `ars_gap`

```json
{
  "operation": "benchmark_gap",
  "selectors": [
    {
      "metric": "elderlyHomeCare",
      "dimension": "sex:total",
      "towns": [
        "046018"
      ]
    }
  ],
  "benchmark": "versilia"
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2024 | 30.085 | per1000 | ARS elderly resident reference population totale |
| versilia | 2024 | 22.1027 | per1000 | ARS elderly resident reference population totale |

**Risultato dell’operazione:**

```json
{
  "value": 7.982300000000002,
  "unit": "per1000",
  "municipalValue": 30.085,
  "benchmarkValue": 22.1027,
  "geography": "046018",
  "benchmarkScope": "versilia",
  "period": "2024",
  "direction": "municipal minus benchmark"
}
```

**Fonte e metodo:** https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=260; ARS published age-standardized measure.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `social_spending_046018`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "socialSpendingPerResident",
      "towns": [
        "046018",
        "046005"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046005 | 2022 | 135.76 | eurPerResident | municipal social expenditure by Istat user-area perimeter, including early childhood |
| 046018 | 2022 | 97.69 | eurPerResident | municipal social expenditure by Istat user-area perimeter, including early childhood |

**Fonte e metodo:** https://www.istat.it/storage/misura-comune/10b-Servizi-sociali-per-abitante.xlsx; official inclusive nominal social expenditure / average resident; source precision retained.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Valore rispetto a una scheda:** Separa bisogno, accesso e intensità; non usa il tasso standardizzato come conteggio di utenti.

## Casa, affitti e ERP

**Domanda centrale:** Chi incontra difficoltà abitative e quali segnali possiamo osservare oggi?

**Primo prodotto:** un percorso di contesto con capitoli fenomeno → servizi/risorse → limiti → istruttoria. Mostrare vendita e affitto OMI con unità distinte e media semplice di zone; affiancare abitazioni non occupate e morosità ERP nei propri universi. Nessun rapporto OMI/MEF diventa onere dei nuclei: costo effettivo, redditi disponibili e domanda ERP restano fabbisogni istruttori.

**Connessioni:** redditi, turismo, suolo

**Lettura sostanziale verificabile:** Le medie semplici OMI 2025-S2 di Massarosa sono inferiori a quelle di Viareggio sia per vendita sia per affitto. Il confronto orienta l’approfondimento dei mercati locali; non dimostra che le famiglie di Massarosa possano sostenere il costo della casa.

**Domande da verificare:** Quotazioni di zona e redditi fiscali permettono di misurare l’onere familiare?; Abitazioni non occupate da residenti sono disponibili sul mercato?

**Competenze da coinvolgere:** Comune: politiche abitative locali e urbanistica; Regione e gestore ERP secondo atti/accordi da verificare; mercato privato non controllato dai conteggi.

**Opzioni istruttorie:** Approfondire accesso ERP, sostegno e uso del patrimonio, senza stimare un numero di alloggi necessari dai soli indicatori.

**Monitoraggio proposto:** Domanda/assegnazioni, attese, morosità con platee coerenti e onere abitativo reale.

**Dati che impediscono la decisione:** Canoni/transazioni effettivi, redditi disponibili e nuclei; Domanda ERP, sfratti, alloggi disponibili e seconde case

**Criterio di accettazione:** le richieste seguenti e i rifiuti della matrice si riproducono; ogni numero mantiene la definizione; le lacune sono visibili nella conclusione. Nessuna decisione automatica.

### Esempio `omi_total_046018`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "omiResidential",
      "dimension": "total",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2025-S2 | 1535.7142857142858 | eurm2 | displayed residential OMI zones; civil dwellings, normal state, public reference selection |
| 046033 | 2025-S2 | 2200.0 | eurm2 | displayed residential OMI zones; civil dwellings, normal state, public reference selection |

**Fonte e metodo:** https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.htm; arithmetic mean of published zone reference values; original OMI min/max ranges and selection records not replayed.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `omi_rentMean_046018`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "omiResidential",
      "dimension": "rentMean",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2025-S2 | 5.2 | eurm2month | displayed residential OMI zones; civil dwellings, normal state, public reference selection |
| 046033 | 2025-S2 | 7.2375 | eurm2month | displayed residential OMI zones; civil dwellings, normal state, public reference selection |

**Fonte e metodo:** https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.htm; arithmetic mean of published zone reference values; original OMI min/max ranges and selection records not replayed.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `census_vacancy`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "vacantHomes",
      "dimension": "total",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2023 | 17.9 | percent | censused homes including non-resident occupation |
| 046033 | 2023 | 27 | percent | censused homes including non-resident occupation |

**Fonte e metodo:** https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip; Istat published census carrier; explicit frozen source reconciliation.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `erp_public_046018_2020`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "erpArrears",
      "towns": [
        "046018",
        "046033"
      ],
      "periods": [
        "2020"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2020 | 3.8 | percent | ERP Lucca municipal cumulative billed amounts for rent and ancillary expenses |
| 046033 | 2020 | 11.51 | percent | ERP Lucca municipal cumulative billed amounts for rent and ancillary expenses |

**Fonte e metodo:** https://at.erplucca.it/default?path=75&t=1; public two-decimal rate from frozen four-decimal rate.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Valore rispetto a una scheda:** Rende visibile il limite delle proxy: OMI non è canone contrattuale, non occupato non significa vuoto.

## Mobilità quotidiana e collegamenti

**Domanda centrale:** Come collegare spostamenti per lavoro e offerta di trasporto senza inventare la domanda?

**Primo prodotto:** un percorso di contesto con capitoli fenomeno → servizi/risorse → limiti → istruttoria. Leggere residenti che lavorano fuori, addetti in entrata e autocontenimento con universo censuario esplicito. Il rapporto di somme autorizzato non ricostruisce attraversamenti del confine Versilia. TPL è una fotografia programmata separata: non misura passeggeri, regolarità o tempi porta a porta.

**Connessioni:** lavoro, infanzia, sanita

**Lettura sostanziale verificabile:** Nel confronto censuario 2021 selezionato, l’autocontenimento di Massarosa è inferiore a quello di Camaiore. È una domanda pertinente su collegamenti e opportunità localizzate; destinazioni, modalità e qualità dei viaggi restano da misurare.

**Domande da verificare:** I margini comunali descrivono attraversamenti del confine Versilia?; Orari programmati e fermate descrivono viaggi possibili e affidabili?

**Competenze da coinvolgere:** Comune: viabilità e servizi locali; Regione/enti competenti e gestori: programmazione TPL e collegamenti, verificando contratti e proprietà delle strade.

**Opzioni istruttorie:** Approfondire interscambi, accesso scolastico e servizio per fascia oraria con domanda e responsabilità documentate.

**Monitoraggio proposto:** Tempi, regolarità, uso, accessibilità e sicurezza; niente somma dei percorsi condivisi come itinerari unici.

**Dati che impediscono la decisione:** Matrice origine-destinazione e mobilità per studio; Tempi porta a porta, frequenze per fascia, passeggeri e regolarità

**Criterio di accettazione:** le richieste seguenti e i rifiuti della matrice si riproducono; ogni numero mantiene la definizione; le lacune sono visibili nella conclusione. Nessuna decisione automatica.

### Esempio `commuting_selfContainment`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "selfContainment",
      "towns": [
        "046005",
        "046018"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046005 | 2021 | 49.86773693332117 | percent | resident habitual work commuters |
| 046018 | 2021 | 28.615384615384613 | percent | resident habitual work commuters |

**Fonte e metodo:** https://esploradati.istat.it/databrowser/DWL/PERMPOP/MATPEN/matrix_pendoLAVORO_2021.zip; Istat frozen municipal marginals; ratios from exact components.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `commuting_pooled_selfContainment`

```json
{
  "operation": "weighted_ratio",
  "selectors": [
    {
      "metric": "selfContainment"
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046005 | 2021 | 49.86773693332117 | percent | resident habitual work commuters |
| 046013 | 2021 | 46.69358909641595 | percent | resident habitual work commuters |
| 046018 | 2021 | 28.615384615384613 | percent | resident habitual work commuters |
| 046024 | 2021 | 48.938428874734605 | percent | resident habitual work commuters |
| 046028 | 2021 | 36.95968916949976 | percent | resident habitual work commuters |
| 046030 | 2021 | 29.87736900780379 | percent | resident habitual work commuters |
| 046033 | 2021 | 62.73150392708232 | percent | resident habitual work commuters |

**Risultato dell’operazione:**

```json
{
  "value": 50.14929248344801,
  "unit": "percent",
  "numerator": 27041.0,
  "denominator": 53921.0,
  "scale": 100,
  "geographies": [
    "046005",
    "046013",
    "046018",
    "046024",
    "046028",
    "046030",
    "046033"
  ],
  "period": "2021",
  "aggregation": "ratio of sums; not mean of municipal ratios",
  "numeratorPeriod": "2021",
  "denominatorPeriod": "2021"
}
```

**Fonte e metodo:** https://esploradati.istat.it/databrowser/DWL/PERMPOP/MATPEN/matrix_pendoLAVORO_2021.zip; Istat frozen municipal marginals; ratios from exact components.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `tpl_scheduledTplTripsPer1000_total_046018`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "scheduledTplTripsPer1000",
      "dimension": "total",
      "towns": [
        "046018",
        "046013"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046013 | 2026-08-26 | 110 | number | municipal scheduled trip memberships |
| 046018 | 2026-08-26 | 106 | number | municipal scheduled trip memberships |

**Fonte e metodo:** https://dati.toscana.it/dataset/rt-oraritb; normalized frozen GTFS municipal count.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `commuting_inboundCommuters`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "inboundCommuters",
      "towns": [
        "046005",
        "046018"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046005 | 2021 | 5628 | number | habitual work commuters by destination |
| 046018 | 2021 | 1815 | number | habitual work commuters by destination |

**Fonte e metodo:** https://esploradati.istat.it/databrowser/DWL/PERMPOP/MATPEN/matrix_pendoLAVORO_2021.zip; Istat frozen municipal marginals; ratios from exact components.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Valore rispetto a una scheda:** Trasforma margini e inventari in domande sull’accessibilità, non in ordini di nuove corse.

## Bilanci e risultati dei servizi

**Domanda centrale:** Le risorse comunali sono sostenibili e quali risultati dei servizi possiamo verificare?

**Primo prodotto:** un percorso di contesto con capitoli fenomeno → servizi/risorse → limiti → istruttoria. Descrivere entrate di competenza, riscossione, rigidità, debito e cassa nei propri perimetri. Affiancare missioni e servizi senza equiparare impegni a prestazioni. Rapporti di somme solo se ammessi; tariffe standard non sono gettito o spesa effettiva familiare.

**Connessioni:** capacita, welfare, investimenti

**Lettura sostanziale verificabile:** Negli esempi 2025 Massarosa ha entrate correnti per residente e quota di spesa rigida inferiori a Viareggio. I valori aprono domande diverse sulla programmazione; vincoli, gestione e prestazioni impediscono di dedurne un margine libero o una graduatoria di efficienza.

**Domande da verificare:** Cassa, competenza e risorse vincolate raccontano lo stesso margine?; Più spesa significa più utenti o servizi migliori?

**Competenze da coinvolgere:** Comune: programmazione finanziaria e controllo; gestori/enti associati per servizi con perimetri distinti.

**Opzioni istruttorie:** Approfondire combinazioni di risorse e livelli di servizio, senza classifica di efficienza dalla spesa pro capite.

**Monitoraggio proposto:** Utenti, costi omogenei, tempi ed esiti; dati contabili come input, non prova di effetto.

**Dati che impediscono la decisione:** Costi e utenti per servizio, qualità ed esiti; Fabbisogni/costi standard confrontabili e perimetri gestionali

**Criterio di accettazione:** le richieste seguenti e i rifiuti della matrice si riproducono; ogni numero mantiene la definizione; le lacune sono visibili nella conclusione. Nessuna decisione automatica.

### Esempio `finance_revenue`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "currentRevenueAccruedPerResident",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2025 | 1446.8854737228287 | currency | municipal accounting perimeter; resident normalization is not beneficiaries |
| 046033 | 2025 | 1633.8676678544327 | currency | municipal accounting perimeter; resident normalization is not beneficiaries |

**Fonte e metodo:** https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/2025/2025_Rendiconto%20-%20Schemi%20di%20bilancio_TOSCANA.zip; Rendiconto accrual/commitment or year-end stock; resident denominator at exercise January 1.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `finance_rigid`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "rigidExpenditureShare",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2025 | 20.66 | percent | municipal accounting perimeter; resident normalization is not beneficiaries |
| 046033 | 2025 | 24.48 | percent | municipal accounting perimeter; resident normalization is not beneficiaries |

**Fonte e metodo:** https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/2025/2025_Rendiconto%20-%20Piano%20degli%20indicatori_TOSCANA.zip; Rendiconto official accounting ratio; no resident denominator.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `distinct_debt_current`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "financialDebtProfile",
      "dimension": "total",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2025 | 465.49354306154265 | currency | municipal accounting or project perimeter; normalization is not beneficiaries |
| 046033 | 2025 | 500.2012974693985 | currency | municipal accounting or project perimeter; normalization is not beneficiaries |

**Fonte e metodo:** https://openbdap.rgs.mef.gov.it/it/FET/Analizza; year-end D1 financing debt / exercise January 1 residents.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

### Esempio `finance_social`

```json
{
  "operation": "compare",
  "selectors": [
    {
      "metric": "socialMissionExpenditurePerResident",
      "towns": [
        "046018",
        "046033"
      ]
    }
  ]
}
```

| Territorio | Periodo | Valore | Unità | Universo |
|---|---|---:|---|---|
| 046018 | 2025 | 196.48336971475743 | currency | municipal accounting perimeter; resident normalization is not beneficiaries |
| 046033 | 2025 | 286.4576005476921 | currency | municipal accounting perimeter; resident normalization is not beneficiaries |

**Fonte e metodo:** https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/2025/2025_Rendiconto%20-%20Schemi%20di%20bilancio_TOSCANA.zip; Rendiconto accrual/commitment or year-end stock; resident denominator at exercise January 1.

**Limiti della risposta:** Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Valore rispetto a una scheda:** Rende leggibile la catena risorse–prestazioni–risultati e i suoi anelli mancanti.
