# A6 — domande con risultati verificati

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; manifest `8305df308acd70f5c392eae94e40c26a8cbf2c2c30d8624eda00ee54a2713c7b`. Esito: **PASS**.

Le aspettative sono versionate e controllate contro riferimenti aritmetici/record dichiarati; non vengono riscritte automaticamente con la risposta del motore. Le domande sono casi di prova riutilizzabili, non un interprete di linguaggio naturale.

| ID e domanda | Esito | Risultato verificato / motivo | Riferimento indipendente |
|---|---|---|---|
| population_current: Quanti residenti ha Massarosa al 1 gennaio 2026? | PASS | /observations/0/value: 21782 | POSAS 2026: record comunale 21782; snapshot demografico |
| population_change: Come cambiano i residenti di Massarosa dal 2019 al 2026? | PASS | /result/value: 86 | POSAS: 21782 − 21696 = 86 |
| income_change: Quanto cresce nominalmente l’imponibile medio 2011–2024 di Massarosa? | PASS | /result/value: 5174.989999999998 | Serie MEF pubblicata: differenza 5174,99 euro; archivi grezzi comunali non verificati dall’adapter |
| female_weighted: Qual è il tasso territoriale di occupazione femminile 2023? | PASS | /result/value: 55.26488943831874; /result/numerator: 27717.0; /result/denominator: 50153.0 | Conteggi censuari: 27717 occupate / 50153 donne 15–64 × 100 |
| female_pp: Come cambia l’occupazione femminile di Massarosa 2021–2023? | PASS | /result/value: 3.0524642426302933; /result/unit: percentage_points | Differenza dei rapporti censuari: +3,052464 punti; riferimento arrotondato a 6 decimali, tolleranza 1e-6 |
| female_benchmark: Quanto dista Massarosa dal tasso femminile toscano 2023? | PASS | /result/value: -5.771613481378452 | Rapporti censuari comunale e Toscana 2023: −5,771613 punti; tolleranza 1e-6 |
| housing_weighted: Quante abitazioni non occupate da residenti per 1000 abitanti nel territorio? | PASS | /result/value: 238.62673869261607 | 38034 abitazioni / 159387 residenti × 1000; non equivale a case vuote |
| age85_mass: Qual è la quota di residenti 85+ a Massarosa? | PASS | /observations/0/value: 4.095124414654302 | POSAS 2026 per età: 892 / 21782 × 100 |
| age85_weighted: Qual è la quota 85+ dei sette Comuni? | PASS | /result/value: 4.92997728993187 | Somme POSAS: 7815 / 158520 × 100 |
| sex_men: Quanti residenti uomini ha Massarosa nel 2026? | PASS | /observations/0/value: 10736 | Somma record POSAS per età/sesso: 10736 uomini |
| child_weighted: Qual è la ricettività educativa potenziale dei sette Comuni nel 2024/25? | PASS | /result/value: 46.504285069914296; /result/period: 2024/25 | 1031 posti potenziali / 2217 residenti 3–36 mesi × 100 |
| child_zero: Gli zero di ricettività a Seravezza e Stazzema sono dati effettivi? | PASS | /observations/0/value: 0.0; /observations/1/value: 0.0 | Riconciliazione regionale: 0/168 e 0/35, anno educativo 2024/25 |
| tour_change: Come cambiano le notti registrate di Massarosa dal 2023 al 2025? | PASS | /result/value: 2791 | Registro movimento senza locazioni: 37898 − 35107 = 2791 |
| tour_weighted: Qual è l’intensità turistica territoriale mantenendo i due periodi? | PASS | /result/value: 14.041963159222812; /result/numeratorPeriod: 2025; /result/denominatorPeriod: 2026 | 2225932 notti 2025 / 158520 residenti al 1 gennaio 2026 |
| ars_total: Qual è il tasso domiciliare standardizzato ARS di Massarosa? | PASS | /observations/0/value: 30.085 | Export ARS 260, totale 2024: 30,085 per mille standardizzato; non rapporto grezzo |
| ars_gap: Quanto dista il tasso ARS di Massarosa dal riferimento ufficiale Versilia? | PASS | /result/value: 7.982300000000002 | ARS 260 totale 2024: 30,085 − 22,1027 = 7,9823 per mille |
| aligned_association: Qual è l’associazione descrittiva residenti/imponibile nel 2024? | PASS | /result/coefficient: 0.4285714285714286; /result/n: 7 | Ranghi sui sette Comuni: Spearman 3/7; n=7, limiti stock/flusso e sensibilità conservati |
| mismatched_association: Si possono correlare automaticamente residenti 2026 e imponibile 2024? | PASS | paired_period_mismatch | Guardia di allineamento temporale: 2026 ≠ 2024 |
| child_italy_missing: È disponibile un benchmark Italia verificato per la ricettività? | PASS | benchmark_scope_not_available | Adapter regionale: solo Toscana; Italia non acquisita |
| child_year_conversion: Possiamo chiamare 2024 l’anno educativo 2024/25? | PASS | educational_year_token_required | Periodo educativo conservato, nessuna conversione implicita |
| ars_aggregate_refused: Possiamo ponderare i tassi ARS standardizzati usando i conteggi grezzi? | PASS | verified_ratio_adapter_required | I conteggi num/den descrivono il tasso grezzo, non quello standardizzato |
| age_history_missing: Possiamo ricostruire lo storico 85+ dalla fotografia corrente? | PASS | age_historical_dimension_not_available | Una fotografia POSAS per fascia non costituisce uno storico verificato |
| duplicate_towns: Possiamo contare due volte Massarosa in un aggregato? | PASS | unknown_or_duplicate_geography | Unicità delle geografie, nessun doppio conteggio |
| unknown_metric: Possiamo interrogare un indicatore inventato? | PASS | unknown_metric | Il catalogo canonico determina gli ID consentiti |
| fuel_adapter_missing: I carburanti pubblicati sono già interrogabili da questo motore? | PASS | adapter_not_implemented | Dati/archivio MIMIT presenti; adapter esterno mensile ancora mancante |
| ars_hypertension_current: Qual è il tasso standardizzato di ipertensione a Massarosa nel 2025? | PASS | /observations/0/value: 245.595; /observations/0/unit: per1000 | ARS 255, Massarosa/totale/tutte le età: misura_standardizzata 245,595; export congelato v1.40 |
| ars_hypertension_age: Qual è il tasso specifico di ipertensione tra i 65–84 anni a Massarosa nel 2025? | PASS | /observations/0/value: 681.808; /observations/0/evidence/1/ci95Low: None | ARS 255, Massarosa/65-84/totale: misura_grezza 681,808; standardized=0 strutturale, IC 0–0 non pubblicabile |
| ars_diabetes_gap: Quanto differisce il tasso standardizzato di diabete di Massarosa dalla Toscana nel 2025? | PASS | /result/value: 4.966799999999999; /result/benchmarkValue: 62.0662 | ARS 271: 67,0330 − 62,0662 = 4,9668 ogni 1.000; stessa misura e stesso periodo |
| ars_life_women_change: Come cambia la speranza di vita femminile di Massarosa tra 2008 e 2022? | PASS | /result/value: 1.7000000000000028; /result/unit: years | ARS 1290: serie pubblicata arrotondata 84,19 − 82,49 = 1,70 anni; dati grezzi 84,1899 e 82,4881 |
| ars_mortality_window_gap: Quanto differisce la mortalità standardizzata di Massarosa dalla Toscana nel periodo 2013–2022? | PASS | /result/value: 107.03399999999999; /result/period: 2013-2022 | ARS 1438: 945,211 − 838,177 = 107,034 ogni 100.000; intera finestra decennale |
| ars_rsa_change: Come cambia il tasso standardizzato di anziani assistiti in RSA a Massarosa dal 2016 al 2024? | PASS | /result/value: 1.79 | ARS 261: valori pubblicati arrotondati 6,11 − 4,32 = 1,79 ogni 1.000; uso del servizio, non bisogno insoddisfatto |
| ars_mortality_endpoint_refused: Posso usare il solo 2022 al posto del periodo di mortalità 2013–2022? | PASS | ars_history_period_not_available | Guardia: il dato decennale non diventa un dato annuale del suo anno finale |
| ars_window_trend_refused: Posso stimare un trend annuale dai periodi decennali sovrapposti della mortalità? | PASS | ars_window_trend_not_supported | Guardia: nessuna conversione implicita in anni indipendenti |
| ars_raw_weighting_refused: Posso aggregare i tassi grezzi per fascia d’età usando automaticamente i conteggi? | PASS | verified_ratio_adapter_required | Guardia: nessuna aggregazione di conteggi senza contratto di additività e universo verificati |
| ars_age_history_refused: Posso ottenere una serie storica 65–84 anni per ipertensione dai dati acquisiti? | PASS | ars_historical_dimension_not_available | Guardia: snapshot delle fasce è corrente; serie totale non sostituisce la fascia |

Il JSON conserva query, risultati, formula, fonti, periodi, copertura ed esclusioni. Un rifiuto atteso è una verifica riuscita del limite, non una capacità di risposta numerica. Nessuna conclusione causale o raccomandazione automatica.
