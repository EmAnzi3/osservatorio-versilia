# Repertorio ragionato delle domande

Le domande sostanziali sono distinte dai controlli metodologici. Ogni nuova domanda ha un piano esplicito: richieste necessarie → risultati → confine dell’interpretazione → informazioni mancanti. I risultati di contesto non certificano bisogni, efficacia o causalità.

Le risposte numeriche sono verificate contro aspettative A6 indipendenti o ancore pubbliche dichiarate. Le interpretazioni sono una revisione editoriale, non un risultato automaticamente certificato dal software. Precisione integrale, puntatori, hash e richieste complete restano in `evidence.json` riproducibile.

## Le 20 domande A6: baseline conservata

Autorità: `ci/a6-territorial-acceptance-questions.json`, immutato. I riferimenti includono casi fuori dalla selezione editoriale: la suite A6 ne conserva la verifica.

### lavoro-residenti — supported

Qual è il tasso di occupazione dei residenti 25–64 anni nei Comuni confrontati?

**Fenomeno:** Occupazione residente e differenze di età.

**Risposta oggi:** Confronti dei tassi nel 2024, con la fascia esplicita per i giovani.

**Query verificate A6:** `census_employment_primary`, `census_young_employment`

**Conclusioni escluse:** Non misura i posti di lavoro localizzati né descrive il 2026.

**Dati mancanti:** Dati più recenti per decisioni attuali

**Valore:** Distingue le persone residenti dall’attività economica presente nel territorio.

### attivita-locali — supported

La base delle attività economiche è cresciuta rispetto al 2018?

**Fenomeno:** Evoluzione delle unità locali e consistenza degli addetti ASIA.

**Risposta oggi:** Variazione cumulata delle unità locali 2018–2023 e addetti nel periodo proprio.

**Query verificate A6:** `business_asia_cumulative`, `business_asia_employment`

**Conclusioni escluse:** Unità locali non sono imprese, e addetti sul luogo di lavoro non sono occupati residenti.

**Dati mancanti:** Nessun dato aggiuntivo per questo confronto storico; servono anni recenti per la congiuntura

**Valore:** Offre una base verificabile per discutere lo sviluppo produttivo senza confondere crescita delle sedi e occupazione.

### trasformazione-produttiva — partially_supported

Il territorio si sta spostando dall’industria ai servizi?

**Fenomeno:** Composizione e cambiamenti produttivi.

**Risposta oggi:** Valore aggiunto industriale, variazione nominale dei servizi e retribuzione industriale nei perimetri acquisiti.

**Query verificate A6:** `business_frame_industry_va`, `business_frame_services_history`, `business_frame_industry_wages`

**Conclusioni escluse:** Questi esempi non dimostrano spostamenti di lavoratori fra settori o crescita reale.

**Dati mancanti:** Pannello settoriale con prezzi costanti; Transizioni individuali e profili professionali; Dati recenti e domanda delle aziende

**Valore:** Separa produzione nominale, specializzazione e lavoro; orienta il fabbisogno di analisi professionali.

### nidi-lavoro — not_determinable

Più posti nei nidi farebbero aumentare l’occupazione femminile?

**Fenomeno:** Conciliazione fra lavoro e servizi educativi.

**Risposta oggi:** Il motore descrive occupazione e ricettività potenziale; la lettura dedicata conserva periodi e universi differenti.

**Query verificate A6:** `female_weighted`, `child_weighted`

**Conclusioni escluse:** Nessun effetto causale o numero di posti necessari è stimabile dai due indicatori.

**Dati mancanti:** Domanda e liste d’attesa; Costi, orari e accessi intercomunali; Occupazione dei genitori; Disegno di valutazione dell’intervento

**Valore:** Trasforma uno slogan causale in una domanda di servizio e valutazione misurabile.

### organizzazione-scolastica — supported

Come differiscono dimensione delle classi e tempo pieno della primaria?

**Fenomeno:** Organizzazione scolastica nell’anno 2024/25.

**Risposta oggi:** Rapporto alunni/classi e quota primaria a tempo pieno, con denominatori distinti.

**Query verificate A6:** `school_class_size`, `school_full_time`

**Conclusioni escluse:** Non equivale a qualità didattica o copertura di tutti i bambini residenti.

**Dati mancanti:** Nessun dato aggiuntivo per le misure definite; dettagli per sede per interventi locali

**Valore:** Permette un confronto preciso dell’offerta osservata.

### rete-scolastica — partially_supported

Le scuole sono poche, troppe o mal distribuite?

**Fenomeno:** Adeguatezza territoriale della rete scolastica.

**Risposta oggi:** Alunni localizzati, classi e accessibilità dichiarata sono contesto verificabile.

**Query verificate A6:** `school_students`, `school_class_size`, `school_access_defined`

**Conclusioni escluse:** Non autorizzano automaticamente aperture, chiusure o una graduatoria di adeguatezza.

**Dati mancanti:** Iscritti per residenza ed età; Bacini e spostamenti intercomunali; Capienza e domanda per sede; Proiezioni demografiche con assunzioni

**Valore:** Identifica quali dati servono prima di intervenire su sedi e classi.

### esiti-educativi — partially_supported

Quali differenze emergono nelle prove di italiano della seconda primaria?

**Fenomeno:** Esiti educativi nel perimetro scolastico osservato.

**Risposta oggi:** Punteggi del grado e materia selezionati, copertura e gap verso Toscana per Viareggio.

**Query verificate A6:** `invalsi_invalsiResults_g2-italiano_current`, `invalsi_invalsiResults_g2-italiano_tuscany`

**Conclusioni escluse:** Plesso nel Comune non significa residenza dell’alunno; nessuna classifica generale di qualità.

**Dati mancanti:** Copertura e partecipazione dei singoli plessi; Composizione e condizioni degli alunni; Altre materie e gradi per un quadro più ampio

**Valore:** Consente di individuare domande da approfondire evitando un voto universale alle scuole.

### invecchiamento-assistenza — partially_supported

L’assistenza domiciliare risponde ai bisogni degli anziani?

**Fenomeno:** Invecchiamento e adeguatezza dell’assistenza.

**Risposta oggi:** Le 7 letture invecchiamento/assistenza affiancano quota 85+ POSAS 2026 e tasso standardizzato ARS 2024 con benchmark separati.

**Query verificate A6:** `age85_mass`, `ars_total`, `ars_gap`

**Conclusioni escluse:** Il tasso erogato non misura bisogno insoddisfatto; non aggregare tassi standardizzati dai conteggi grezzi.

**Dati mancanti:** Bisogni accertati e domanda inevasa; Intensità, attese e accessibilità dei servizi; Allineamento temporale

**Valore:** Distingue pressione demografica, servizio registrato e bisogno da accertare.

### fragilita-sociale — partially_supported

Quante famiglie unipersonali indicano una possibile fragilità sociale?

**Fenomeno:** Struttura familiare e vulnerabilità.

**Risposta oggi:** Quote unipersonali e indice di vecchiaia nei periodi dichiarati.

**Query verificate A6:** `census_single`, `census_ageing`

**Conclusioni escluse:** Famiglia unipersonale non prova solitudine, età anziana, povertà o non autosufficienza.

**Dati mancanti:** Incrocio età e composizione familiare; Reti di supporto, redditi e bisogni accertati

**Valore:** Evita di trasformare un dato demografico in una diagnosi sociale individuale.

### spesa-sociale — partially_supported

Quali priorità mostrano le risorse sociali e quali bisogni restano scoperti?

**Fenomeno:** Risorse sociali Istat e missione di bilancio, universi distinti.

**Risposta oggi:** Spesa Istat 2022, quote di utenza e impegni della missione sociale sono descritti separatamente.

**Query verificate A6:** `social_spending_046018`, `social_area_disability`, `finance_social`

**Conclusioni escluse:** Missione contabile e spesa sociale statistica non sono la stessa misura; maggiore spesa non prova efficacia.

**Dati mancanti:** Utenti, domanda inevasa, costi unitari e prestazioni; Perimetri e periodi comuni per confronti congiunti

**Valore:** Collega risorse e futuri indicatori di servizio senza stimare risultati inesistenti.

### quotazioni-casa — supported

Come si confrontano le quotazioni residenziali di vendita e affitto?

**Fenomeno:** Livelli delle quotazioni di riferimento.

**Risposta oggi:** Medie semplici delle zone mostrate, vendita €/m² e affitto €/m²/mese, secondo semestre 2025.

**Query verificate A6:** `omi_total_046018`, `omi_rentMean_046018`

**Conclusioni escluse:** Non sono prezzi delle transazioni o canoni effettivi; media comunale diversa dalla media di tutte le zone.

**Dati mancanti:** Nessun dato aggiuntivo per il confronto delle quotazioni pubblicate

**Valore:** Offre un confronto trasparente senza inventare pesi di abitazioni o compravendite.

### accessibilita-casa — not_determinable

Le famiglie possono permettersi una casa nel proprio Comune?

**Fenomeno:** Accessibilità economica dell’abitazione.

**Risposta oggi:** Quotazioni e imponibile medio individuale restano contesti separati.

**Query verificate A6:** `omi_rentMean_046018`, `income_change`, `omi_rentMean_pair_False_refused`

**Conclusioni escluse:** Un rapporto fra media OMI e reddito fiscale individuale non misura lo sforzo abitativo familiare.

**Dati mancanti:** Reddito disponibile e composizione delle famiglie; Canoni e prezzi effettivi; Superfici, mutui e costi abitativi; Distribuzioni congiunte e periodi omogenei

**Valore:** Definisce la base informativa necessaria per politiche abitative fondate.

### abitazioni-non-residenti — partially_supported

Le abitazioni non occupate da residenti sono disponibili per nuove famiglie?

**Fenomeno:** Patrimonio abitativo e usi.

**Risposta oggi:** Quota censuaria delle abitazioni non occupate da residenti nel 2023.

**Query verificate A6:** `census_vacancy`

**Conclusioni escluse:** Non significa case vuote, inutilizzate o disponibili sul mercato.

**Dati mancanti:** Uso da non residenti, locazioni e seconde case; Disponibilità, condizioni e vincoli degli immobili

**Valore:** Separa il patrimonio statistico dall’offerta effettivamente mobilitabile.

### pendolarismo — supported

Quali Comuni attraggono o perdono pendolari per lavoro nel 2021?

**Fenomeno:** Margini comunali del pendolarismo abituale per lavoro.

**Risposta oggi:** Ingressi, uscite e saldo 2021; le 7 letture e il riepilogo mantengono il perimetro.

**Query verificate A6:** `commuting_inboundCommuters`, `commuting_outboundCommuters`, `commuting_commuterBalance`

**Conclusioni escluse:** La somma degli ingressi comunali non è il flusso al confine Versilia; non descrive lo studio o il 2026.

**Dati mancanti:** Nessun dato aggiuntivo per i margini; matrice origine-destinazione per flussi al confine

**Valore:** Rende leggibili ruoli territoriali diversi senza doppie contabilizzazioni.

### adeguatezza-tpl — not_determinable

Le corse programmate bastano per raggiungere lavoro, scuola e servizi?

**Fenomeno:** Accessibilità e domanda di mobilità.

**Risposta oggi:** Fotografia delle corse programmate e pendolarismo storico, con date proprie.

**Query verificate A6:** `tpl_scheduledTplTripsPer1000_total_046018`, `commuting_outboundCommuters`

**Conclusioni escluse:** Trip-comune non è corsa territoriale unica; quantità programmata non prova affidabilità o adeguatezza.

**Dati mancanti:** Origini, destinazioni, modi, orari e carichi; Tempi di viaggio e coincidenze; Esecuzione e affidabilità delle corse; Domanda aggiornata e flussi scolastici

**Valore:** Indica cosa misurare prima di proporre linee o frequenze.

### risorse-comunali — supported

Come si distinguono risorse accertate, incassi e margini del bilancio?

**Fenomeno:** Conti comunali con basi differenti.

**Risposta oggi:** Valori per residente e rigidità nel periodo contabile proprio, con date del denominatore esplicite.

**Query verificate A6:** `finance_revenue`, `finance_cash_date`, `finance_rigid`, `finance_balance`

**Conclusioni escluse:** Flusso di cassa non è competenza o fondo finale; somme comunali lorde non sono bilancio territoriale consolidato.

**Dati mancanti:** Nessun dato aggiuntivo per le misure contabili; consolidamento per trasferimenti fra enti

**Valore:** Impedisce confronti contabili impropri e rende verificabili le risorse descritte.

### risorse-risultati — not_determinable

Un Comune che spende di più offre servizi migliori?

**Fenomeno:** Relazione fra risorse e risultati.

**Risposta oggi:** Il motore descrive impegni, offerta scolastica e spesa sociale nei rispettivi periodi.

**Query verificate A6:** `finance_social`, `school_full_time`, `social_spending_046018`

**Conclusioni escluse:** Nessun effetto causale o giudizio di efficienza è deducibile da questi confronti.

**Dati mancanti:** Prestazioni, qualità, beneficiari, tempi e domanda; Costi omogenei e fattori di contesto; Valutazione dell’intervento

**Valore:** Fornisce una traccia di indicatori di risultato da affiancare ai conti.

### turismo-servizi — partially_supported

Come è cambiato il movimento turistico e quale pressione potenziale descrive?

**Fenomeno:** Flussi turistici e servizi.

**Risposta oggi:** Le letture turismo calcolano notti 2023–2025 e intensità 2025/residenti 2026; arrivi e presenze restano distinti.

**Query verificate A6:** `tour_change`, `tour_weighted`, `tourism_tourismArrivals_current`

**Conclusioni escluse:** Notti non sono persone uniche o presenze giornaliere; intensità non misura i carichi effettivi.

**Dati mancanti:** Escursionisti e locazioni escluse; Picchi giornalieri e carichi/costi dei servizi

**Valore:** Orienta misurazioni stagionali senza convertire flussi annui in fabbisogni automatici.

### atlante-registro — supported

Quante unità locali attive registra l’Atlante nei sette Comuni nel 2025?

**Fenomeno:** Consistenza territoriale e attività specifica del Registro Imprese.

**Risposta oggi:** Totali nativi comunali e confronto del record diretto ristorazione selezionato; totale territoriale 20.325.

**Query verificate A6:** `atlas_territory_2025`, `atlas_I_561011_active_2025`

**Conclusioni escluse:** Record ATECO non è branca esaustiva; 292 dalle sole divisioni non è il totale; Registro Imprese diverso da ASIA.

**Dati mancanti:** Nessun dato aggiuntivo per i conteggi congelati; omogeneità classificatoria per variazioni

**Valore:** Corregge l’immagine del tessuto produttivo e conserva le differenze fra universi.

### erp-morosita — partially_supported

Come si distribuisce la morosità ERP e cosa dice sulla difficoltà delle famiglie?

**Fenomeno:** Morosità degli importi emessi e fragilità abitativa.

**Risposta oggi:** Rapporto morosità cumulata/emesso cumulato ERP Lucca nel 2024; importi in euro, non famiglie.

**Query verificate A6:** `erp_native_046018_2024`

**Conclusioni escluse:** Non misura quante famiglie siano in difficoltà o l’efficacia della gestione; discontinuità dei prospetti esplicite.

**Dati mancanti:** Numero e caratteristiche dei nuclei; Canoni correnti, transizioni e motivi della morosità; Domanda abitativa non soddisfatta

**Valore:** Consente di separare un problema contabile dall’accertamento del bisogno abitativo.

## Approfondimenti del programma

Non sommare formulazioni, query e dossier come se fossero analisi complete. Le domande centrali sono programmi di indagine; le nuove domande restano parziali o non determinabili dove mancano le evidenze decisionali. I sotto-dossier sono descritti in [MODULES.md](MODULES.md).

### Famiglie, natalità e ricambio

**Competenze da verificare negli atti vigenti:** Comune: anagrafe e pianificazione dei servizi; programmazione sovracomunale da coordinare.

**Domande A6 riusate e approfondite, non nuove certificazioni:** fragilita-sociale

**Opzioni da approfondire:** Scenari di dimensionamento dei servizi e consultazione delle frazioni, senza proiezioni inventate.

**Monitoraggio:** Coorti, saldi e composizione familiare; registrare definizioni e confini a ogni aggiornamento.

#### demografia-centrale — partially_supported

Quali dinamiche demografiche cambiano la domanda di servizi?

**Risposta oggi e interpretazione consentita:** Affiancare stock POSAS, saldo naturale, migrazioni e famiglie nei periodi propri. Separare contributi osservati da scenari di domanda futura: una somma di flussi richiede stesso periodo e definizioni; proiezioni richiedono assunzioni ulteriori.

**Informazioni mancanti:** Proiezioni per frazione e coorte; Composizione e bisogni dei nuclei, residenti effettivi; Serie armonizzate per età e frazione; Proiezioni con scenari e assunzioni; Età e condizioni delle persone sole; Reti di cura e domanda espressa

**Valore aggiunto:** Separa stock, flussi e domanda futura; non trasforma il calo dei residenti in una previsione.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `demography_natural`, `demography_internal`, `demography_foreign_events`, `census_single`, `census_size`

#### demografia-1 — partially_supported

Quali componenti del ricambio demografico devono entrare nella programmazione dei servizi?

**Risposta oggi e interpretazione consentita:** Separare nascite e decessi dalle iscrizioni e cancellazioni interne ed estere nel periodo osservato; non attribuire i cambiamenti a una sola causa.

**Informazioni mancanti:** Serie armonizzate per età e frazione; Proiezioni con scenari e assunzioni

**Valore aggiunto:** Separa stock, flussi e domanda futura; non trasforma il calo dei residenti in una previsione.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `demography_natural` — `compare`; esito `computed`.

**Risultati:** Massarosa 2025: -7,3 per1000; Viareggio 2025: -7,3 per1000

**Universi e definizioni:** resident population; native reference dates and components explicit — balance annual events / arithmetic mean January 1 and December 31 residents * 1000

**Fonti:** [https://demo.istat.it/](https://demo.istat.it/)

**Avvertenze:** births_minus_deaths_not_total_population_change, istat_demographic_information_flag:p, population_change_also_contains_migration_and_statistical_adjustments

**Componente della risposta**

Richiesta `demography_internal` — `compare`; esito `computed`.

**Risultati:** Massarosa 2024: 2,9 per1000; Viareggio 2024: 3,2 per1000

**Universi e definizioni:** resident population; native reference dates and components explicit — internalResidentialMobility balance residence-registration events / mean resident population * 1000

**Fonti:** [https://demo.istat.it/](https://demo.istat.it/)

**Avvertenze:** gross_municipal_transfer_flows_include_moves_within_selected_towns, residence_registration_events_not_unique_people_or_non_italian_citizens

**Componente della risposta**

Richiesta `demography_foreign_events` — `compare`; esito `computed`.

**Risultati:** Massarosa 2024: 1,7 per1000; Viareggio 2024: 1,9 per1000

**Universi e definizioni:** resident population; native reference dates and components explicit — foreignResidentialMobility balance residence-registration events / mean resident population * 1000

**Fonti:** [https://demo.istat.it/](https://demo.istat.it/)

**Avvertenze:** gross_municipal_transfer_flows_include_moves_within_selected_towns, published_foreign_transfer_counts_not_original_archive_reconciliation, residence_registration_events_not_unique_people_or_non_italian_citizens

#### demografia-2 — partially_supported

La struttura delle famiglie segnala esigenze diverse di sostegno e prossimità?

**Risposta oggi e interpretazione consentita:** Descrivere famiglie unipersonali e dimensione media nei rispettivi universi; vivere soli non equivale a isolamento o bisogno assistenziale.

**Informazioni mancanti:** Età e condizioni delle persone sole; Reti di cura e domanda espressa

**Valore aggiunto:** Separa stock, flussi e domanda futura; non trasforma il calo dei residenti in una previsione.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `census_single` — `compare`; esito `computed`.

**Risultati:** Massarosa 2023: 29,2 %; Viareggio 2023: 41,3 %

**Universi e definizioni:** resident households — PF3 / PF1 * 100

**Fonti:** [https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip](https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip)

**Avvertenze:** published_rounding_preserved_no_implicit_weighting, single_household_not_direct_measure_of_loneliness

**Componente della risposta**

Richiesta `census_size` — `compare`; esito `computed`.

**Risultati:** Massarosa 2023: 2,4 decimal; Viareggio 2023: 2,1 decimal

**Universi e definizioni:** resident households — householdSize; total

**Fonti:** [https://www.istat.it/statistiche-per-temi/censimenti/popolazione-e-abitazioni/risultati/](https://www.istat.it/statistiche-per-temi/censimenti/popolazione-e-abitazioni/risultati/)

**Avvertenze:** household_size_raw_components_not_reconciled

#### Controlli metodologici, separati dalle domande territoriali

- Il saldo naturale e la mobilità raccontano lo stesso fenomeno? No: saldo naturale e mobilità sono flussi differenti, nei periodi 2025 e 2024 delle viste eseguite; non descrivono un’identica variazione né permettono una previsione.
- Quali famiglie restano invisibili nella media comunale? Non determinabile dai dati acquisiti: Composizione e bisogni dei nuclei, residenti effettivi. Nessuna stima sostitutiva è autorizzata.

### Lavoro e trasformazioni produttive

**Competenze da verificare negli atti vigenti:** Comune: pianificazione e servizi locali; Regione: lavoro/formazione; imprese e parti sociali come interlocutori, non decisori comunali sostitutivi.

**Domande A6 riusate e approfondite, non nuove certificazioni:** lavoro-residenti, attivita-locali, trasformazione-produttiva, atlante-registro

**Opzioni da approfondire:** Approfondire formazione, accessibilità delle aree produttive e sportelli, previa analisi di domanda e competenze.

**Monitoraggio:** Occupazione residente per coorte, addetti localizzati e risultati dei programmi con denominatori separati.

#### lavoro-centrale — partially_supported

La crescita economica localizzata si accompagna a opportunità per i residenti?

**Risposta oggi e interpretazione consentita:** Aprire con occupazione dei residenti per fascia/sesso, poi addetti e unità locali ASIA, composizione Frame e Atlante Registro Imprese. Gli storici rimangono interni a ciascuna fonte: le basi non formano una serie unica. Affiancare retribuzioni e redditi con platee esplicite, distinguendo nominale e indicatore reale autorizzato.

**Informazioni mancanti:** Transizioni professionali e qualità dei contratti; Pannello settoriale a prezzi costanti e dati recenti; Serie omogenee contemporanee di occupazione e attività; Transizioni dei residenti, contratti e profili richiesti; Pannello settoriale comparabile a prezzi costanti; Transizioni professionali e domanda delle imprese

**Valore aggiunto:** Evita di scambiare unità locali per imprese o addetti per occupati residenti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `census_employment_primary`, `business_asia_cumulative`, `business_asia_employment`, `business_frame_industry_va`, `business_frame_industry_wages`, `business_frame_services_history`

#### lavoro-1 — partially_supported

A Massarosa la crescita delle attività locali si accompagna a maggiore occupazione dei residenti rispetto a Viareggio?

**Risposta oggi e interpretazione consentita:** Confrontare occupazione residente 2024, crescita cumulata ASIA 2018–2023 e addetti localizzati 2023 separatamente. Non è una verifica di accompagnamento nel tempo o di causa.

**Informazioni mancanti:** Serie omogenee contemporanee di occupazione e attività; Transizioni dei residenti, contratti e profili richiesti

**Valore aggiunto:** Evita di scambiare unità locali per imprese o addetti per occupati residenti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `census_employment_primary` — `compare`; esito `computed`.

**Risultati:** Massarosa 2024: 73,4 %; Viareggio 2024: 71,9 %

**Universi e definizioni:** resident population; 25–64 total residents — employed / resident population * 100; 25–64 total residents

**Fonti:** [https://esploradati.istat.it/SDMXWS/rest](https://esploradati.istat.it/SDMXWS/rest)

**Avvertenze:** frozen_derived_components_no_implicit_weighting, published_rounding_preserved_no_implicit_weighting, resident_employment_not_workplace_jobs

**Componente della risposta**

Richiesta `business_asia_cumulative` — `compare`; esito `computed`.

**Risultati:** Massarosa 2018-2023: 7,0 %; Viareggio 2018-2023: 9,2 %

**Universi e definizioni:** ASIA active local units; annual average employment at workplace; ASIA total — localUnitsChange; ASIA published measure; cumulative change from fixed 2018 baseline

**Fonti:** [https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500DICA,1.0/DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7](https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500DICA,1.0/DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7)

**Avvertenze:** cumulative_baseline_change_not_year_on_year, workplace_activity_not_resident_employment

**Componente della risposta**

Richiesta `business_asia_employment` — `compare`; esito `computed`.

**Risultati:** Massarosa 2023: 4.938,3 persone/addetti secondo definizione; Viareggio 2023: 22.358,3 persone/addetti secondo definizione

**Universi e definizioni:** ASIA active local units; annual average employment at workplace; ASIA total — localEmployees; ASIA published measure

**Fonti:** [https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500DICA,1.0/DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7](https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500DICA,1.0/DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7)

**Avvertenze:** workplace_activity_not_resident_employment

#### lavoro-2 — partially_supported

Che cosa mostrano produzione industriale, retribuzioni e cambiamento nominale dei servizi a Massarosa?

**Risposta oggi e interpretazione consentita:** Affiancare industria 2023 e variazione nominale dei servizi 2015–2023. Non dimostra passaggi di lavoratori fra settori né crescita reale.

**Informazioni mancanti:** Pannello settoriale comparabile a prezzi costanti; Transizioni professionali e domanda delle imprese

**Valore aggiunto:** Evita di scambiare unità locali per imprese o addetti per occupati residenti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `business_frame_industry_va` — `compare`; esito `computed`.

**Risultati:** Massarosa 2023: 92,8 milioni €; Viareggio 2023: 524,1 milioni €

**Universi e definizioni:** Frame SBS local units of industry and services; industry — businessValueAdded; industry; published nominal measure

**Fonti:** [https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/](https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/)

**Avvertenze:** frame_and_asia_universes_differ, frame_value_added_not_municipal_gdp, nominal_economic_values_not_real_growth, workplace_activity_not_resident_employment

**Componente della risposta**

Richiesta `business_frame_industry_wages` — `compare`; esito `computed`.

**Risultati:** Massarosa 2023: 31.226,0 €; Viareggio 2023: 30.393,0 €

**Universi e definizioni:** Frame SBS local units of industry and services; industry — averageGrossRemunerationPerEmployee; industry; published nominal measure

**Fonti:** [https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/](https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/)

**Avvertenze:** frame_and_asia_universes_differ, frame_value_added_not_municipal_gdp, nominal_economic_values_not_real_growth, official_rounded_measure_preserved_no_implicit_weighting, workplace_activity_not_resident_employment

**Componente della risposta**

Richiesta `business_frame_services_history` — `absolute_change`; esito `computed`.

**Risultati:** Massarosa 2015: 94,0 milioni €; Massarosa 2023: 165,9 milioni €

Risultato dell’operazione: 71,9 milioni €.

**Universi e definizioni:** Frame SBS local units of industry and services; services — businessValueAdded; services; published nominal measure

**Fonti:** [https://www.istat.it/comunicato-stampa/risultati-economici-delle-imprese-a-livello-territoriale-ampliamento-del-dettaglio-di-analisi-anno-2015/](https://www.istat.it/comunicato-stampa/risultati-economici-delle-imprese-a-livello-territoriale-ampliamento-del-dettaglio-di-analisi-anno-2015/); [https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/](https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/)

**Avvertenze:** frame_and_asia_universes_differ, frame_value_added_not_municipal_gdp, nominal_economic_values_not_real_growth, workplace_activity_not_resident_employment

#### Controlli metodologici, separati dalle domande territoriali

- La composizione industria/servizi cambia nei periodi realmente confrontabili? Le viste settoriali e storiche eseguite descrivono quote e variazioni nei propri periodi; non misurano transizioni di lavoratori o crescita reale.
- Produzione nominale, addetti e redditi dei dichiaranti descrivono la stessa popolazione? Gli universi sono esplicitamente differenti: addetti localizzati, residenti occupati e dichiaranti fiscali; non esiste identità autorizzata fra le tre platee.

### Redditi e vulnerabilità economica

**Competenze da verificare negli atti vigenti:** Comune: servizi sociali e tributi locali; prestazioni fiscali/previdenziali nazionali non di competenza comunale.

**Domande A6 riusate e approfondite, non nuove certificazioni:** accessibilita-casa

**Opzioni da approfondire:** Verificare accesso alle misure e informazione sui diritti, prima di definire soglie o platee.

**Monitoraggio:** Accessi, esclusioni e tempi delle misure; redditi fiscali come contesto, non risultato attribuito.

#### redditi-centrale — partially_supported

Quali segnali economici giustificano approfondire il bisogno di sostegno?

**Risposta oggi e interpretazione consentita:** Comporre risposte deterministiche separate, preservando periodi, universi, fonti, missing e rifiuti; nessuna fusione causale o aritmetica non autorizzata.

**Informazioni mancanti:** ISEE, reddito disponibile familiare e patrimonio; Costi essenziali e persone non dichiaranti; Redditi disponibili equivalenti e composizione dei nuclei; Costi essenziali, patrimonio e accesso ai sostegni; Spese dei nuclei e differenze distributive nel tempo

**Valore aggiunto:** Trasforma medie fiscali in domande sulla distribuzione senza stimare povertà da una proxy.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `mef_incomeDistribution_total`, `mef_incomeSourceProfile_total`, `real_income_total_series_046018`, `mef_pensionIncomeShare_history`

#### redditi-1 — partially_supported

La distribuzione dei redditi dichiarati individua gruppi da approfondire per le politiche di sostegno?

**Risposta oggi e interpretazione consentita:** Descrivere distribuzione e composizione degli imponibili, non povertà dei nuclei o reddito disponibile.

**Informazioni mancanti:** Redditi disponibili equivalenti e composizione dei nuclei; Costi essenziali, patrimonio e accesso ai sostegni

**Valore aggiunto:** Trasforma medie fiscali in domande sulla distribuzione senza stimare povertà da una proxy.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `mef_incomeDistribution_total` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 37,2 %; Forte dei Marmi 2024: 33,4 %; Massarosa 2024: 34,5 %; Pietrasanta 2024: 37,2 %; Seravezza 2024: 37,0 %; Stazzema 2024: 40,5 %; Viareggio 2024: 34,6 %

**Universi e definizioni:** known class frequencies only — known published class frequencies / sum of known class frequencies

**Fonti:** [https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800](https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800)

**Avvertenze:** mef_bands_not_current_tax_brackets, mef_frozen_extraction_not_new_live_acquisition, mef_income_source_frequencies_overlap_do_not_sum_people, mef_macro_known_cells_denominator_differs_from_eight_band_total_denominator, mef_missing_band_cells_not_zero_or_redistributed, mef_nominal_declared_income_not_disposable_income

**Componente della risposta**

Richiesta `mef_incomeSourceProfile_total` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 23.025,2 €; Forte dei Marmi 2024: 41.732,9 €; Massarosa 2024: 22.217,5 €; Pietrasanta 2024: 23.873,7 €; Seravezza 2024: 21.167,5 €; Stazzema 2024: 20.783,9 €; Viareggio 2024: 23.561,9 €

**Universi e definizioni:** municipal fiscal records; selected income-source declarants — nominal income amount / declarant frequency for source employment; frequencies overlap across income sources

**Fonti:** [https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800](https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800)

**Avvertenze:** mef_frozen_extraction_not_new_live_acquisition, mef_income_source_frequencies_overlap_do_not_sum_people, mef_nominal_declared_income_not_disposable_income

#### redditi-2 — partially_supported

Come cambia il potere di acquisto misurabile e quanto pesa il reddito da pensione?

**Risposta oggi e interpretazione consentita:** Leggere separatamente il deflazionamento autorizzato e la quota fiscale delle pensioni. Una quota di reddito non conta i pensionati.

**Informazioni mancanti:** Spese dei nuclei e differenze distributive nel tempo

**Valore aggiunto:** Trasforma medie fiscali in domande sulla distribuzione senza stimare povertà da una proxy.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `real_income_total_series_046018` — `series`; esito `computed`.

**Risultati:** Massarosa 2016: 0,0 %; Massarosa 2017: -0,9 %; Massarosa 2018: 0,1 %; Massarosa 2019: 1,1 %; Massarosa 2020: 0,4 %; Massarosa 2021: 3,4 %; Massarosa 2022: 1,0 %; Massarosa 2023: -0,6 %; Massarosa 2024: 3,4 %

**Universi e definizioni:** MEF municipal declarants with taxable income; changing yearly populations, not a household cohort — cumulative taxable mean income change relative to 2016 deflated by national NIC chained annual rates

**Fonti:** [https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php](https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php)

**Avvertenze:** real_income_cumulative_2016_baseline_not_annual_growth, real_income_intermediate_history_catalog_only_native_endpoint_panels_2016_2024, real_income_national_nic_not_local_prices_or_individual_purchasing_power, real_income_normalized_panels_reconciled_original_archives_not_replayed, real_income_numerical_rank_not_quality_or_causal_inference, real_income_taxable_mean_not_disposable_household_income

**Componente della risposta**

Richiesta `mef_pensionIncomeShare_history` — `series`; esito `computed`.

**Risultati:** Camaiore 2023: 27,8 %; Camaiore 2024: 27,9 %

**Universi e definizioni:** municipal declared income amounts — pension income amount / total income amount; not share of pensioners

**Fonti:** [https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2023.zip?d=1615465800](https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2023.zip?d=1615465800); [https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800](https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800)

**Avvertenze:** mef_frozen_extraction_not_new_live_acquisition, mef_income_source_frequencies_overlap_do_not_sum_people, mef_nominal_declared_income_not_disposable_income

#### Controlli metodologici, separati dalle domande territoriali

- Il reddito medio nasconde composizioni diverse dei dichiaranti? I risultati selezionati descrivono il contesto; ISEE, reddito disponibile familiare e patrimonio impedisce di rispondere integralmente alla domanda.
- Quali redditi non sono misurati dall’imponibile MEF? Non determinabile dai dati acquisiti: Costi essenziali e persone non dichiaranti. Nessuna stima sostitutiva è autorizzata.

### Infanzia, scuola e giovani

**Competenze da verificare negli atti vigenti:** Comune: servizi scolastici ed edilizia non provinciale; Provincia: edilizia secondaria superiore; scuole autonome/Regione per offerta e programmazione.

**Domande A6 riusate e approfondite, non nuove certificazioni:** nidi-lavoro, organizzazione-scolastica, rete-scolastica, esiti-educativi

**Opzioni da approfondire:** Approfondire orari, trasporto, accessibilità e uso degli edifici; nessuna conclusione automatica scuole troppe/poche.

**Monitoraggio:** Attese, frequenza, accessibilità, tempi e risultati per coorte; evitare attribuzione causale ai soli indicatori INVALSI.

#### infanzia-centrale — partially_supported

L’offerta educativa risponde ai bisogni delle famiglie e dei giovani?

**Risposta oggi e interpretazione consentita:** Descrivere ricettività potenziale e denominatore 3–36 mesi, poi classi, tempo pieno, edifici e perimetro scolastico. Affiancare lavoro femminile come contesto con periodo proprio. Richiedere bacini, domanda, frequenza e attese prima di dimensionare posti o sedi.

**Informazioni mancanti:** Utenti residenti, domanda inevasa, tariffe e orari; Bacini degli alunni, capienza effettiva e tempi di percorso; Liste di attesa e domanda per età e zona; Orari, tariffe, occupazione effettiva e accessi intercomunali; Bacini e capacità per plesso; Partecipazione alle prove e contesto degli alunni; Transizioni scuola–formazione–lavoro

**Valore aggiunto:** Collega quantità, fruibilità e domanda non misurata senza equiparare alunni localizzati a residenti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `child_weighted`, `child_zero`, `school_students`, `school_class_size`, `school_full_time`, `school_access_defined`, `invalsi_invalsiImplicitDispersion_g8_current`

#### infanzia-1 — partially_supported

Dove la ricettività educativa potenziale 2024/25 è più limitata, e basta per decidere nuovi posti?

**Risposta oggi e interpretazione consentita:** Confrontare posti potenziali e bambini residenti di 3–36 mesi nei sette Comuni; disponibilità locale non misura utenti, domanda insoddisfatta o accessi fuori Comune.

**Informazioni mancanti:** Liste di attesa e domanda per età e zona; Orari, tariffe, occupazione effettiva e accessi intercomunali

**Valore aggiunto:** Collega quantità, fruibilità e domanda non misurata senza equiparare alunni localizzati a residenti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `child_weighted` — `weighted_ratio`; esito `computed`.

**Risultati:** Camaiore 2024/25: 40,6 %; Forte dei Marmi 2024/25: 84,0 %; Massarosa 2024/25: 29,3 %; Pietrasanta 2024/25: 74,9 %; Seravezza 2024/25: 0,0 %; Stazzema 2024/25: 0,0 %; Viareggio 2024/25: 53,0 %

Risultato dell’operazione: 46,5 %.

**Universi e definizioni:** resident children aged 3–36 months — potential local educational places / resident children aged 3–36 months * 100

**Fonti:** [https://dati.toscana.it/dataset/98ee6064-b61a-45e2-a790-86c55b278574/resource/01588909-8f0b-4b80-8af7-1749bab80a5e/download/opendata-_-da-pubblicare-24-25.csv](https://dati.toscana.it/dataset/98ee6064-b61a-45e2-a790-86c55b278574/resource/01588909-8f0b-4b80-8af7-1749bab80a5e/download/opendata-_-da-pubblicare-24-25.csv)

**Avvertenze:** cross_boundary_use_waiting_lists_and_quality_not_measured, disjoint_populations_must_be_attested, potential_capacity_not_attendance_or_access

**Componente della risposta**

Richiesta `child_zero` — `compare`; esito `computed`.

**Risultati:** Seravezza 2024/25: 0,0 %; Stazzema 2024/25: 0,0 %

**Universi e definizioni:** resident children aged 3–36 months — potential local educational places / resident children aged 3–36 months * 100

**Fonti:** [https://dati.toscana.it/dataset/98ee6064-b61a-45e2-a790-86c55b278574/resource/01588909-8f0b-4b80-8af7-1749bab80a5e/download/opendata-_-da-pubblicare-24-25.csv](https://dati.toscana.it/dataset/98ee6064-b61a-45e2-a790-86c55b278574/resource/01588909-8f0b-4b80-8af7-1749bab80a5e/download/opendata-_-da-pubblicare-24-25.csv)

**Avvertenze:** cross_boundary_use_waiting_lists_and_quality_not_measured, potential_capacity_not_attendance_or_access

#### infanzia-2 — partially_supported

Che cosa distingue l’organizzazione scolastica di Massarosa e quali risultati educativi richiedono approfondimento?

**Risposta oggi e interpretazione consentita:** Affiancare alunni, classi e tempo pieno 2024/25 alla dispersione implicita del grado 8 con copertura parziale. Non collegare causalmente bambini della primaria e studenti testati.

**Informazioni mancanti:** Bacini e capacità per plesso; Partecipazione alle prove e contesto degli alunni; Transizioni scuola–formazione–lavoro

**Valore aggiunto:** Collega quantità, fruibilità e domanda non misurata senza equiparare alunni localizzati a residenti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `school_students` — `compare`; esito `computed`.

**Risultati:** Massarosa 2024/25: 1.282,0 persone/addetti secondo definizione; Viareggio 2024/25: 7.508,0 persone/addetti secondo definizione

**Universi e definizioni:** pupils in state and private schools located in the municipality; not resident children — located-school pupil count

**Fonti:** [https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti](https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti)

**Avvertenze:** classes_not_buildings_or_sites, full_time_classification_not_service_quality_or_parental_employment_effect, located_school_pupils_not_resident_children_or_service_coverage, school_year_not_calendar_year

**Componente della risposta**

Richiesta `school_class_size` — `compare`; esito `computed`.

**Risultati:** Massarosa 2024/25: 17,8 alunni/classe; Viareggio 2024/25: 19,4 alunni/classe

**Universi e definizioni:** pupils in state and private schools located in the municipality; not resident children — located-school pupils / classes

**Fonti:** [https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti](https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti)

**Avvertenze:** classes_not_buildings_or_sites, full_time_classification_not_service_quality_or_parental_employment_effect, located_school_pupils_not_resident_children_or_service_coverage, school_year_not_calendar_year

**Componente della risposta**

Richiesta `school_full_time` — `compare`; esito `computed`.

**Risultati:** Massarosa 2024/25: 55,3 %; Viareggio 2024/25: 46,8 %

**Universi e definizioni:** pupils in state and private schools located in the municipality; not resident children — primary full-time pupils / all primary pupils * 100

**Fonti:** [https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti](https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Studenti)

**Avvertenze:** classes_not_buildings_or_sites, full_time_classification_not_service_quality_or_parental_employment_effect, located_school_pupils_not_resident_children_or_service_coverage, school_year_not_calendar_year

**Componente della risposta**

Richiesta `school_access_defined` — `compare`; esito `computed`.

**Risultati:** Massarosa 2024/25: 100,0 %; Viareggio 2024/25: 92,1 %

**Universi e definizioni:** unique MIM school buildings; accessibilita defined responses, or all responses for undefined share — accessibilita/yes count / corresponding response denominator * 100

**Fonti:** [https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?datasetId=DS0156EDISUPBARARCSTA2021](https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?datasetId=DS0156EDISUPBARARCSTA2021)

**Avvertenze:** declared_building_attributes_not_certification_quality_capacity_or_pupil_access, response_denominator_varies_by_field, undefined_responses_not_no_or_zero

**Componente della risposta**

Richiesta `invalsi_invalsiImplicitDispersion_g8_current` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024-25: 12,9 %; Forte dei Marmi 2024-25: non disponibile %; Massarosa 2024-25: 14,4 %; Pietrasanta 2024-25: 8,4 %; Seravezza 2024-25: non disponibile %; Stazzema 2024-25: non disponibile %; Viareggio 2024-25: 11,3 %

**Universi e definizioni:** tested students by municipality of school location, official Totale aggregation — implicitDispersion/g8/published value

**Fonti:** [https://serviziostatistico.invalsi.it/invalsi_ss_data/eccellenza-accademica-e-dispersione-scolastica-implicita-valori-percentuali/](https://serviziostatistico.invalsi.it/invalsi_ss_data/eccellenza-accademica-e-dispersione-scolastica-implicita-valori-percentuali/)

**Avvertenze:** invalsi_2019_20_tests_not_conducted_gap_preserved, invalsi_aggregation_totale_same_grade_subject_academic_year, invalsi_comune_plesso_not_student_residence, invalsi_missing_or_suppressed_cells_not_zero_or_absence_of_schools, invalsi_numeric_rank_not_school_quality_or_policy_priority, invalsi_participation_and_coverage_percentages_not_valid_student_denominators, invalsi_published_precision_retained_no_versilia_mean, partial_coverage

#### Controlli metodologici, separati dalle domande territoriali

- Posti potenziali, utenti effettivi e liste d’attesa sono distinti? Le definizioni distinguono capacità potenziale da utenti e domanda inevasa: solo la prima è calcolata negli esempi. La differenza quantitativa richiede altri dati.
- Le scuole localizzate nel Comune servono quali bacini? Non determinabile dai dati acquisiti: Bacini degli alunni, capienza effettiva e tempi di percorso. Nessuna stima sostitutiva è autorizzata.

### Invecchiamento, autonomia e assistenza

**Competenze da verificare negli atti vigenti:** Comune e organismi di zona/SdS: integrazione sociale; azienda sanitaria: assistenza territoriale; Regione: programmazione. Accordi gestionali locali da verificare.

**Domande A6 riusate e approfondite, non nuove certificazioni:** invecchiamento-assistenza, fragilita-sociale

**Opzioni da approfondire:** Approfondire presa in carico integrata, trasporto sociale e sostegno ai caregiver con responsabili e platee verificate.

**Monitoraggio:** Utenti unici, ore, attese, continuità e bisogni non soddisfatti; stock demografico come contesto.

#### anziani-centrale — partially_supported

Quali bisogni degli anziani sono osservati e quali restano non misurati?

**Risposta oggi e interpretazione consentita:** Separare pressione demografica 85+, famiglie unipersonali e servizi ARS. Il tasso standardizzato ha benchmark ufficiali ma non va ponderato dai conteggi grezzi. Spesa sociale, utenti unici, intensità e domanda inevasa sono passaggi distinti verso la copertura del bisogno.

**Informazioni mancanti:** Non autosufficienza, caregiver e bisogni non soddisfatti; Utenti unici, intensità/ore di assistenza e attese; Utenti e non utenti per età, bisogno e intensità; Domanda insoddisfatta e tempi di accesso; Persone anziane sole, autonomia e caregiver; Prestazioni, accessi e risultati individuali anonimizzati

**Valore aggiunto:** Separa bisogno, accesso e intensità; non usa il tasso standardizzato come conteggio di utenti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `age85_mass`, `ars_total`, `census_single`, `dossier_primary_dementia`, `social_spending_history`

#### anziani-1 — partially_supported

Come differiscono invecchiamento e assistenza domiciliare fra Massarosa e Viareggio?

**Risposta oggi e interpretazione consentita:** Affiancare quota 85+ del 2026 e tasso standardizzato di assistenza del 2024; non calcolare copertura degli ultraottantacinquenni da universi diversi.

**Informazioni mancanti:** Utenti e non utenti per età, bisogno e intensità; Domanda insoddisfatta e tempi di accesso

**Valore aggiunto:** Separa bisogno, accesso e intensità; non usa il tasso standardizzato come conteggio di utenti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `age85_mass` — `compare`; esito `computed`.

**Risultati:** Massarosa 2026: 4,1 %; Viareggio 2026: 4,9 %

**Universi e definizioni:** resident population at January 1 — residents age:85+ / all residents * 100

**Fonti:** [https://demo.istat.it/data/posas/POSAS_2026_it_046_Lucca.zip](https://demo.istat.it/data/posas/POSAS_2026_it_046_Lucca.zip)

**Avvertenze:** nessuna aggiuntiva

**Componente della risposta**

Richiesta `ars_total` — `compare`; esito `computed`.

**Risultati:** Massarosa 2024: 30,1 per1000; Viareggio 2024: 20,1 per1000

**Universi e definizioni:** ARS elderly resident reference population totale — ARS 260 age-standardized home care rate; not crude num/den

**Fonti:** [https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=260](https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=260)

**Avvertenze:** care_delivery_not_unmet_need_or_quality, standardized_rate_not_crude_ratio

#### anziani-2 — partially_supported

Quali segnali di solitudine e fragilità orientano un’indagine sui bisogni di cura?

**Risposta oggi e interpretazione consentita:** Usare famiglie unipersonali, misura sanitaria e spesa come segnali distinti; non contare persone fragili dalla loro combinazione.

**Informazioni mancanti:** Persone anziane sole, autonomia e caregiver; Prestazioni, accessi e risultati individuali anonimizzati

**Valore aggiunto:** Separa bisogno, accesso e intensità; non usa il tasso standardizzato come conteggio di utenti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `census_single` — `compare`; esito `computed`.

**Risultati:** Massarosa 2023: 29,2 %; Viareggio 2023: 41,3 %

**Universi e definizioni:** resident households — PF3 / PF1 * 100

**Fonti:** [https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip](https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip)

**Avvertenze:** published_rounding_preserved_no_implicit_weighting, single_household_not_direct_measure_of_loneliness

**Componente della risposta**

Richiesta `dossier_primary_dementia` — `compare`; esito `computed`.

**Risultati:** Camaiore 2025: 10,9 per1000; Forte dei Marmi 2025: 7,8 per1000; Massarosa 2025: 10,8 per1000; Pietrasanta 2025: 11,3 per1000; Seravezza 2025: 12,7 per1000; Stazzema 2025: 13,4 per1000; Viareggio 2025: 10,8 per1000

**Universi e definizioni:** ARS dementia source reference universe; age totale; sex totale — ARS 270 dementia; standardized published measure; age totale; sex totale

**Fonti:** [https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=270](https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=270)

**Avvertenze:** administrative_detection_not_total_population_need, health_indicator_not_cause_or_policy_priority, snapshot_is_not_live_source_verification, standardized_rate_not_crude_ratio

**Componente della risposta**

Richiesta `social_spending_history` — `series`; esito `computed`.

**Risultati:** Camaiore 2014: 148,4 eurPerResident; Camaiore 2015: 152,7 eurPerResident; Camaiore 2016: 167,7 eurPerResident; Camaiore 2017: 142,8 eurPerResident; Camaiore 2018: 139,8 eurPerResident; Camaiore 2019: 131,0 eurPerResident; Camaiore 2020: 150,6 eurPerResident; Camaiore 2021: 151,9 eurPerResident; Camaiore 2022: 135,8 eurPerResident

**Universi e definizioni:** municipal social expenditure by Istat user-area perimeter, including early childhood — nominal municipal social expenditure per average resident, including early-childhood educational services

**Fonti:** [https://www.istat.it/storage/misura-comune/10b-Servizi-sociali-per-abitante.xlsx](https://www.istat.it/storage/misura-comune/10b-Servizi-sociali-per-abitante.xlsx)

**Avvertenze:** social_2014_2022_includes_early_childhood_no_excluded_scope_concatenation, social_municipal_arithmetic_means_not_consolidated_versilia, social_native_denominators_unavailable_no_pooling_or_reverse_derived_counts, social_nominal_euros_no_inflation_adjustment, social_spending_not_need_quality_effectiveness_or_policy_priority

#### Controlli metodologici, separati dalle domande territoriali

- Quota degli 85+ e assistenza standardizzata sono confrontabili come copertura? No: quota anagrafica e tasso standardizzato sanitario hanno denominatori, metodi e periodi propri. Le definizioni consentono di escludere il rapporto di copertura.
- Quanti bisogni di autonomia e cura restano fuori dai dati? Non determinabile dai dati acquisiti: Utenti unici, intensità/ore di assistenza e attese. Nessuna stima sostitutiva è autorizzata.

### Inclusione e servizi sociali

**Competenze da verificare negli atti vigenti:** Comune e servizi sociali associati/organismi di zona; enti del terzo settore come interlocutori, sedi legali non servizi erogati.

**Domande A6 riusate e approfondite, non nuove certificazioni:** spesa-sociale, fragilita-sociale

**Opzioni da approfondire:** Approfondire punti di accesso, coordinamento e inclusione, verificando copertura e costo dei servizi.

**Monitoraggio:** Accessi, rinunce, attese ed esiti; separare classificazioni ordinali da quantità cardinali.

#### welfare-centrale — partially_supported

Come collegare fragilità, accesso ai servizi e risorse senza dedurre gli esiti dalla spesa?

**Risposta oggi e interpretazione consentita:** Comporre risposte deterministiche separate, preservando periodi, universi, fonti, missing e rifiuti; nessuna fusione causale o aritmetica non autorizzata.

**Informazioni mancanti:** Platee eleggibili, utenti e domanda inevasa; Tempi, continuità, esiti e accesso per sottogruppo; Utenti eleggibili, domande respinte e attese; Costi e prestazioni con lo stesso perimetro; Accessibilità, attività e beneficiari per servizio; Copertura dei gruppi non raggiunti

**Valore aggiunto:** Non produce una graduatoria politica dalla fragilità o dalla sola spesa.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `ifc_municipalFragility_current`, `social_spending_046018`, `social_area_families-minors`, `regional_disability064Per1000_current`, `demography_citizenship`, `runts_total_046018`

#### welfare-1 — partially_supported

Dove fragilità territoriale e risorse sociali suggeriscono di approfondire l’accesso ai servizi?

**Risposta oggi e interpretazione consentita:** Affiancare indice composito, spesa per residente e destinazione per area. Non dedurre bisogno o qualità dalla spesa.

**Informazioni mancanti:** Utenti eleggibili, domande respinte e attese; Costi e prestazioni con lo stesso perimetro

**Valore aggiunto:** Non produce una graduatoria politica dalla fragilità o dalla sola spesa.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `ifc_municipalFragility_current` — `compare`; esito `computed`.

**Risultati:** Massarosa 2022: 4,0 decile; Viareggio 2022: 2,0 decile

**Universi e definizioni:** municipalities; each ordinal class is a relative position, not an amount — IFC COMP_FRAG_INDEX_DECILE ordinal class; unequal intervals cannot be assumed

**Fonti:** [https://www.istat.it/comunicato-stampa/la-fragilita-dei-comuni-italiani-anno-2022/](https://www.istat.it/comunicato-stampa/la-fragilita-dei-comuni-italiani-anno-2022/)

**Avvertenze:** ordinal_classes_not_amounts_no_mean_changes_or_rank

**Componente della risposta**

Richiesta `social_spending_046018` — `compare`; esito `computed`.

**Risultati:** Camaiore 2022: 135,8 eurPerResident; Massarosa 2022: 97,7 eurPerResident

**Universi e definizioni:** municipal social expenditure by Istat user-area perimeter, including early childhood — nominal municipal social expenditure per average resident, including early-childhood educational services

**Fonti:** [https://www.istat.it/storage/misura-comune/10b-Servizi-sociali-per-abitante.xlsx](https://www.istat.it/storage/misura-comune/10b-Servizi-sociali-per-abitante.xlsx)

**Avvertenze:** social_2014_2022_includes_early_childhood_no_excluded_scope_concatenation, social_municipal_arithmetic_means_not_consolidated_versilia, social_native_denominators_unavailable_no_pooling_or_reverse_derived_counts, social_nominal_euros_no_inflation_adjustment, social_spending_not_need_quality_effectiveness_or_policy_priority

**Componente della risposta**

Richiesta `social_area_families-minors` — `compare`; esito `computed`.

**Risultati:** Camaiore 2022: 44,6 %; Forte dei Marmi 2022: 50,6 %; Massarosa 2022: 29,0 %; Pietrasanta 2022: 45,0 %; Seravezza 2022: 23,2 %; Stazzema 2022: 26,3 %; Viareggio 2022: 45,7 %

**Universi e definizioni:** municipal social expenditure by Istat user-area perimeter, including early childhood — municipal social expenditure share: Famiglia e minori

**Fonti:** [https://www.istat.it/storage/misura-comune/10a-Servizi-sociali-per-tipologia-di-utenza.xlsx](https://www.istat.it/storage/misura-comune/10a-Servizi-sociali-per-tipologia-di-utenza.xlsx)

**Avvertenze:** social_area_zero_not_absence_of_need_or_health_services, social_municipal_arithmetic_means_not_consolidated_versilia, social_native_denominators_unavailable_no_pooling_or_reverse_derived_counts, social_spending_not_need_quality_effectiveness_or_policy_priority, social_summary_eur_per_resident_not_area_percent, social_total_alias_families_minors_not_sum

#### welfare-2 — partially_supported

Quali risorse comunitarie e barriere all’inclusione sono osservabili?

**Risposta oggi e interpretazione consentita:** Descrivere indicatori di contesto e sedi legali RUNTS separatamente; sedi di enti non misurano servizi erogati né inclusione.

**Informazioni mancanti:** Accessibilità, attività e beneficiari per servizio; Copertura dei gruppi non raggiunti

**Valore aggiunto:** Non produce una graduatoria politica dalla fragilità o dalla sola spesa.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `regional_disability064Per1000_current` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 6,6 per1000; Massarosa 2024: 8,7 per1000

**Universi e definizioni:** recognized disability, including severe, aged 0–64 / residents aged 0–64 — recognized disabled people 0–64 / residents 0–64 × 1000

**Fonti:** [https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali](https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali)

**Avvertenze:** regional_administrative_recognition_not_health_prevalence, regional_historical_release_continuity_not_attested, regional_municipal_summary_not_official_versilia, regional_no_reverse_derived_counts_or_population_weights, regional_published_values_no_native_counts_or_joint_distribution

**Componente della risposta**

Richiesta `demography_citizenship` — `compare`; esito `computed`.

**Risultati:** Massarosa 2025: 4,7 %; Viareggio 2025: 8,3 %

**Universi e definizioni:** RCS residents by citizenship; not foreign-born residents — non-Italian citizens at January 1 / all residents * 100

**Fonti:** [https://demo.istat.it/](https://demo.istat.it/)

**Avvertenze:** citizenship_not_country_of_birth_or_residential_transfer_origin, country_breakdowns_not_adapted_no_citizenship_birth_country_cross_tab, sex_counts_not_shares_without_sex_specific_resident_denominators

**Componente della risposta**

Richiesta `runts_total_046018` — `compare`; esito `computed`.

**Risultati:** Camaiore 2026-10-11: 2,7 per1000; Massarosa 2026-10-11: 2,4 per1000

**Universi e definizioni:** RUNTS entities assigned once by current legal municipality, all registered sections — registered entities by legal seat / resident population × 1000

**Fonti:** [https://servizi.lavoro.gov.it/runts/it-it/Lista-enti](https://servizi.lavoro.gov.it/runts/it-it/Lista-enti)

**Avvertenze:** third_sector_all_registered_sections_not_all_local_associations, third_sector_legal_seat_not_activity_services_or_volunteer_count, third_sector_no_reconstructed_2025_history_or_seat_transfers, third_sector_normalized_snapshot_not_original_excel_entity_replay, third_sector_numeric_rank_not_quality_or_policy_priority, third_sector_register_20261011_population_20260101_distinct_dates

#### Controlli metodologici, separati dalle domande territoriali

- Quali dimensioni del bisogno sono misurate e quali sono proxy? I risultati selezionati descrivono il contesto; Platee eleggibili, utenti e domanda inevasa impedisce di rispondere integralmente alla domanda.
- La distribuzione delle risorse coincide con l’accesso alle prestazioni? Non determinabile dai dati acquisiti: Tempi, continuità, esiti e accesso per sottogruppo. Nessuna stima sostitutiva è autorizzata.

### Salute e accessibilità delle cure

**Competenze da verificare negli atti vigenti:** Azienda sanitaria e Regione: cure e programmazione; Comune/organismi di zona: integrazione sociale e accessibilità locale.

**Domande A6 riusate e approfondite, non nuove certificazioni:** invecchiamento-assistenza

**Opzioni da approfondire:** Approfondire raccordo territoriale, trasporti e informazione; nessuna prescrizione clinica o decisione sulla rete da soli conteggi.

**Monitoraggio:** Attese, rinunce, presa in carico e tempi per bacino; distinguere percentile da media.

#### sanita-centrale — partially_supported

I dati descrivono la salute, l’uso dei servizi o la loro accessibilità?

**Risposta oggi e interpretazione consentita:** Comporre risposte deterministiche separate, preservando periodi, universi, fonti, missing e rifiuti; nessuna fusione causale o aritmetica non autorizzata.

**Informazioni mancanti:** Tempi di attesa e capacità operativa per servizio; Percorsi effettivi, rinunce e bacini di utenza; Bisogni non soddisfatti e rinuncia alle cure; Tempi di attesa e distribuzione per frazione; Capacità, orari, accesso economico e prenotazioni; Tempi di viaggio con diversi mezzi

**Valore aggiunto:** Evita di interpretare più accessi come migliore salute o strutture come posti disponibili.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `dossier_primary_chronicTotal`, `dossier_primary_emergencyAccess`, `regional_emsResponseTimeP75_current`, `health_pharmaciesPer1000_046005`, `health_accreditedRsaCount_046005`, `ifc_access_current`

#### sanita-1 — partially_supported

Quali differenze tra condizioni di salute, utilizzo delle cure e tempi di soccorso meritano approfondimento?

**Risposta oggi e interpretazione consentita:** Presentare morbosità, accessi e percentile dei tempi con i propri universi, senza identificare utilizzo con accessibilità.

**Informazioni mancanti:** Bisogni non soddisfatti e rinuncia alle cure; Tempi di attesa e distribuzione per frazione

**Valore aggiunto:** Evita di interpretare più accessi come migliore salute o strutture come posti disponibili.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `dossier_primary_chronicTotal` — `compare`; esito `computed`.

**Risultati:** Camaiore 2025: 315,4 per1000; Forte dei Marmi 2025: 296,5 per1000; Massarosa 2025: 317,1 per1000; Pietrasanta 2025: 313,6 per1000; Seravezza 2025: 321,3 per1000; Stazzema 2025: 339,7 per1000; Viareggio 2025: 318,8 per1000

**Universi e definizioni:** ARS chronicTotal source reference universe; age totale; sex totale — ARS 275 chronicTotal; standardized published measure; age totale; sex totale

**Fonti:** [https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=275](https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=275)

**Avvertenze:** administrative_detection_not_total_population_need, health_indicator_not_cause_or_policy_priority, snapshot_is_not_live_source_verification, standardized_rate_not_crude_ratio

**Componente della risposta**

Richiesta `dossier_primary_emergencyAccess` — `compare`; esito `computed`.

**Risultati:** Camaiore 2025: 43,3 per100; Forte dei Marmi 2025: 31,5 per100; Massarosa 2025: 41,1 per100; Pietrasanta 2025: 39,8 per100; Seravezza 2025: 42,0 per100; Stazzema 2025: 42,5 per100; Viareggio 2025: 43,7 per100

**Universi e definizioni:** ARS emergencyAccess source reference universe; age totale; sex totale — ARS 1657 emergencyAccess; standardized published measure; age totale; sex totale

**Fonti:** [https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=1657](https://www.ars.toscana.it/banche-dati/actions/esporta.php?indicatore=1657)

**Avvertenze:** health_indicator_not_cause_or_policy_priority, snapshot_is_not_live_source_verification, standardized_rate_not_crude_ratio

**Componente della risposta**

Richiesta `regional_emsResponseTimeP75_current` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 10,8 minutes; Massarosa 2024: 13,8 minutes

**Universi e definizioni:** NSIS P3 call-to-first-rescue-arrival intervals; native municipal distribution — 75th percentile of call-to-first-rescue-arrival interval distribution, minutes

**Fonti:** [https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali](https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali)

**Avvertenze:** regional_historical_release_continuity_not_attested, regional_municipal_summary_not_official_versilia, regional_no_reverse_derived_counts_or_population_weights, regional_p75_not_mean_or_pooled_percentile, regional_published_values_no_native_counts_or_joint_distribution, regional_small_intervention_counts_not_frozen

#### sanita-2 — partially_supported

I punti di servizio osservabili bastano a descrivere l’accesso effettivo alle cure?

**Risposta oggi e interpretazione consentita:** Offrire densità, strutture e indicatore composito come contesto; non stimare posti disponibili o tempi di viaggio da un conteggio.

**Informazioni mancanti:** Capacità, orari, accesso economico e prenotazioni; Tempi di viaggio con diversi mezzi

**Valore aggiunto:** Evita di interpretare più accessi come migliore salute o strutture come posti disponibili.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `health_pharmaciesPer1000_046005` — `compare`; esito `computed`.

**Risultati:** Camaiore 2025: 0,3 per1000; Forte dei Marmi 2025: 0,8 per1000; Massarosa 2025: 0,3 per1000; Pietrasanta 2025: 0,4 per1000; Seravezza 2025: 0,3 per1000; Stazzema 2025: 0,4 per1000; Viareggio 2025: 0,3 per1000

**Universi e definizioni:** localized public pharmacy sites, including branches and dispensaries — valid unique ministerial site at 31 December 2025 / estimated residents 1 January 2026 × 1000

**Fonti:** [https://www.dati.salute.gov.it/sites/default/files/opendata/FRM_FARMA_5_20251231.csv](https://www.dati.salute.gov.it/sites/default/files/opendata/FRM_FARMA_5_20251231.csv)

**Avvertenze:** health_facilities_no_automatic_relation_to_resident_health_outcomes, health_facilities_presence_not_access_capacity_quality_or_policy_priority, health_facilities_zero_is_local_presence_not_absence_of_services, health_pharmacies_2025_stock_2026_resident_estimate, health_pharmacies_branches_and_seasonal_dispensaries_included, health_pharmacies_public_two_decimals_benchmark_unrounded

**Componente della risposta**

Richiesta `health_accreditedRsaCount_046005` — `compare`; esito `computed`.

**Risultati:** Camaiore 2025: 5,0 count; Forte dei Marmi 2025: 0,0 count; Massarosa 2025: 0,0 count; Pietrasanta 2025: 2,0 count; Seravezza 2025: 2,0 count; Stazzema 2025: 0,0 count; Viareggio 2025: 4,0 count

**Universi e definizioni:** localized accredited RSA structures, not residents assisted or beds — unique accredited RSA structures present at 31 December 2025

**Fonti:** [https://www.regione.toscana.it/documents/d/guest/elenco-strutture-del-sistema-sociale-integrato-accreditate-al-31-dicembre-2025](https://www.regione.toscana.it/documents/d/guest/elenco-strutture-del-sistema-sociale-integrato-accreditate-al-31-dicembre-2025)

**Avvertenze:** health_facilities_no_automatic_relation_to_resident_health_outcomes, health_facilities_presence_not_access_capacity_quality_or_policy_priority, health_facilities_zero_is_local_presence_not_absence_of_services, health_rsa_accredited_not_contracted_beds_or_residents_assisted, health_rsa_tuscany_336_not_a_comparable_municipal_rate

**Componente della risposta**

Richiesta `ifc_access_current` — `compare`; esito `computed`.

**Risultati:** Massarosa 2019: 17,1 minutes; Viareggio 2019: 0,0 minutes

**Universi e definizioni:** municipal center to nearest Polo/Polo intercomunale; not resident travel times — car journey time from municipal center to nearest essential-service pole

**Fonti:** [https://www.istat.it/comunicato-stampa/la-fragilita-dei-comuni-italiani-anno-2022/](https://www.istat.it/comunicato-stampa/la-fragilita-dei-comuni-italiani-anno-2022/)

**Avvertenze:** accessibility_2019_not_2022_no_repeated_export_history, municipal_center_time_not_resident_population_mean, zero_minutes_is_valid_pole_location

#### Controlli metodologici, separati dalle domande territoriali

- Una struttura censita corrisponde a capacità disponibile? No: una struttura censita indica dotazione, non capacità operativa o appuntamenti disponibili.
- I tempi e gli accessi indicano un bisogno soddisfatto? Non determinabile dai dati acquisiti: Percorsi effettivi, rinunce e bacini di utenza. Nessuna stima sostitutiva è autorizzata.

### Casa, affitti e ERP

**Competenze da verificare negli atti vigenti:** Comune: politiche abitative locali e urbanistica; Regione e gestore ERP secondo atti/accordi da verificare; mercato privato non controllato dai conteggi.

**Domande A6 riusate e approfondite, non nuove certificazioni:** quotazioni-casa, accessibilita-casa, abitazioni-non-residenti, erp-morosita

**Opzioni da approfondire:** Approfondire accesso ERP, sostegno e uso del patrimonio, senza stimare un numero di alloggi necessari dai soli indicatori.

**Monitoraggio:** Domanda/assegnazioni, attese, morosità con platee coerenti e onere abitativo reale.

#### abitazione-centrale — partially_supported

Chi incontra difficoltà abitative e quali segnali possiamo osservare oggi?

**Risposta oggi e interpretazione consentita:** Mostrare vendita e affitto OMI con unità distinte e media semplice di zone; affiancare abitazioni non occupate e morosità ERP nei propri universi. Nessun rapporto OMI/MEF diventa onere dei nuclei: costo effettivo, redditi disponibili e domanda ERP restano fabbisogni istruttori.

**Informazioni mancanti:** Canoni/transazioni effettivi, redditi disponibili e nuclei; Domanda ERP, sfratti, alloggi disponibili e seconde case; Canoni contrattuali, redditi e dimensione dei nuclei; Dimensioni e disponibilità effettiva degli alloggi; Uso stagionale, proprietà e stato degli alloggi; Domanda ERP, graduatorie e assegnazioni aggiornate

**Valore aggiunto:** Rende visibile il limite delle proxy: OMI non è canone contrattuale, non occupato non significa vuoto.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `omi_total_046018`, `omi_rentMean_046018`, `mef_incomeDistribution_total`, `census_vacancy`, `housing_weighted`, `erp_public_046018_2020`

#### abitazione-1 — partially_supported

Come differiscono i segnali del mercato abitativo di Massarosa e Viareggio e che cosa dicono sull’accessibilità?

**Risposta oggi e interpretazione consentita:** Mostrare quotazioni medie semplici di zone OMI e redditi individuali come contesti distinti; non costruire un rapporto affitto/reddito familiare.

**Informazioni mancanti:** Canoni contrattuali, redditi e dimensione dei nuclei; Dimensioni e disponibilità effettiva degli alloggi

**Valore aggiunto:** Rende visibile il limite delle proxy: OMI non è canone contrattuale, non occupato non significa vuoto.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `omi_total_046018` — `compare`; esito `computed`.

**Risultati:** Massarosa 2025-S2: 1.535,7 eurm2; Viareggio 2025-S2: 2.200,0 eurm2

**Universi e definizioni:** displayed residential OMI zones; civil dwellings, normal state, public reference selection — unweighted municipal mean of displayed residential zone sale reference quotations

**Fonti:** [https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.htm](https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.htm)

**Avvertenze:** omi_municipal_mean_is_unweighted_mean_of_displayed_zones_not_official_municipal_omi_mean, omi_numerical_rank_not_affordability_or_policy_priority, omi_public_zone_values_replayed_original_omi_ranges_and_files_not_frozen, omi_reference_quotations_not_transaction_prices_or_registered_rents, omi_sale_euro_per_m2_and_rent_euro_per_m2_per_month_are_distinct, omi_second_semester_2025_not_current_2026_or_full_year_average, omi_versilia_mean_of_seven_municipal_means_not_transaction_or_dwelling_weighted, omi_zone_codes_are_local_to_each_municipality_not_comparable_neighbourhoods

**Componente della risposta**

Richiesta `omi_rentMean_046018` — `compare`; esito `computed`.

**Risultati:** Massarosa 2025-S2: 5,2 eurm2month; Viareggio 2025-S2: 7,2 eurm2month

**Universi e definizioni:** displayed residential OMI zones; civil dwellings, normal state, public reference selection — unweighted municipal mean of displayed residential zone rental reference quotations

**Fonti:** [https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.htm](https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/index.htm)

**Avvertenze:** omi_municipal_mean_is_unweighted_mean_of_displayed_zones_not_official_municipal_omi_mean, omi_numerical_rank_not_affordability_or_policy_priority, omi_public_zone_values_replayed_original_omi_ranges_and_files_not_frozen, omi_reference_quotations_not_transaction_prices_or_registered_rents, omi_sale_euro_per_m2_and_rent_euro_per_m2_per_month_are_distinct, omi_second_semester_2025_not_current_2026_or_full_year_average, omi_versilia_mean_of_seven_municipal_means_not_transaction_or_dwelling_weighted, omi_zone_codes_are_local_to_each_municipality_not_comparable_neighbourhoods

**Componente della risposta**

Richiesta `mef_incomeDistribution_total` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 37,2 %; Forte dei Marmi 2024: 33,4 %; Massarosa 2024: 34,5 %; Pietrasanta 2024: 37,2 %; Seravezza 2024: 37,0 %; Stazzema 2024: 40,5 %; Viareggio 2024: 34,6 %

**Universi e definizioni:** known class frequencies only — known published class frequencies / sum of known class frequencies

**Fonti:** [https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800](https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800)

**Avvertenze:** mef_bands_not_current_tax_brackets, mef_frozen_extraction_not_new_live_acquisition, mef_income_source_frequencies_overlap_do_not_sum_people, mef_macro_known_cells_denominator_differs_from_eight_band_total_denominator, mef_missing_band_cells_not_zero_or_redistributed, mef_nominal_declared_income_not_disposable_income

#### abitazione-2 — partially_supported

Alloggi non occupati ed ERP possono spiegare dove intervenire sull’offerta?

**Risposta oggi e interpretazione consentita:** Descrivere stock e morosità ERP nei periodi propri; alloggi non occupati non equivalgono ad abitazioni immediatamente disponibili.

**Informazioni mancanti:** Uso stagionale, proprietà e stato degli alloggi; Domanda ERP, graduatorie e assegnazioni aggiornate

**Valore aggiunto:** Rende visibile il limite delle proxy: OMI non è canone contrattuale, non occupato non significa vuoto.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `census_vacancy` — `compare`; esito `computed`.

**Risultati:** Massarosa 2023: 17,9 %; Viareggio 2023: 27,0 %

**Universi e definizioni:** censused homes including non-resident occupation — A3 / A8 * 100

**Fonti:** [https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip](https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip)

**Avvertenze:** non_resident_occupied_homes_are_not_necessarily_vacant, published_rounding_preserved_no_implicit_weighting

**Componente della risposta**

Richiesta `housing_weighted` — `weighted_ratio`; esito `computed`.

**Risultati:** Camaiore 2023: 260,1 per1000; Forte dei Marmi 2023: 758,4 per1000; Massarosa 2023: 90,3 per1000; Pietrasanta 2023: 348,9 per1000; Seravezza 2023: 163,8 per1000; Stazzema 2023: 742,0 per1000; Viareggio 2023: 172,7 per1000

Risultato dell’operazione: 238,6 per1000.

**Universi e definizioni:** resident population — A3 / P1 * 1000

**Fonti:** [https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip](https://esploradati.istat.it/databrowser/DWL/PERMPOP/SUBCOM/Dati_regionali_2023.zip)

**Avvertenze:** disjoint_populations_must_be_attested, non_resident_occupied_homes_are_not_necessarily_vacant

**Componente della risposta**

Richiesta `erp_public_046018_2020` — `compare`; esito `computed`.

**Risultati:** Massarosa 2020: 3,8 %; Viareggio 2020: 11,5 %

**Universi e definizioni:** ERP Lucca municipal cumulative billed amounts for rent and ancillary expenses — cumulative arrears / cumulative issued amounts × 100

**Fonti:** [https://at.erplucca.it/default?path=75&t=1](https://at.erplucca.it/default?path=75&t=1)

**Avvertenze:** erp_2022_header_mismatch_2023_printed_percentages_not_used, erp_cumulative_accounting_not_annual_unpaid_rent_or_household_share, erp_massarosa_2023_issued_discontinuity_retained_no_interpolation, erp_no_automatic_causal_quality_or_policy_priority_inference, erp_snapshot_reconciled_original_balance_sheet_pdfs_not_replayed

#### Controlli metodologici, separati dalle domande territoriali

- Quotazioni di zona e redditi fiscali permettono di misurare l’onere familiare? No: medie OMI di zona e redditi individuali dei dichiaranti non identificano spesa e reddito disponibile dei nuclei.
- Abitazioni non occupate da residenti sono disponibili sul mercato? Non determinabile dai dati acquisiti: Domanda ERP, sfratti, alloggi disponibili e seconde case. Nessuna stima sostitutiva è autorizzata.

### Mobilità quotidiana e collegamenti

**Competenze da verificare negli atti vigenti:** Comune: viabilità e servizi locali; Regione/enti competenti e gestori: programmazione TPL e collegamenti, verificando contratti e proprietà delle strade.

**Domande A6 riusate e approfondite, non nuove certificazioni:** pendolarismo, adeguatezza-tpl

**Opzioni da approfondire:** Approfondire interscambi, accesso scolastico e servizio per fascia oraria con domanda e responsabilità documentate.

**Monitoraggio:** Tempi, regolarità, uso, accessibilità e sicurezza; niente somma dei percorsi condivisi come itinerari unici.

#### mobilita-centrale — partially_supported

Come collegare spostamenti per lavoro e offerta di trasporto senza inventare la domanda?

**Risposta oggi e interpretazione consentita:** Leggere residenti che lavorano fuori, addetti in entrata e autocontenimento con universo censuario esplicito. Il rapporto di somme autorizzato non ricostruisce attraversamenti del confine Versilia. TPL è una fotografia programmata separata: non misura passeggeri, regolarità o tempi porta a porta.

**Informazioni mancanti:** Matrice origine-destinazione e mobilità per studio; Tempi porta a porta, frequenze per fascia, passeggeri e regolarità; Origini–destinazioni e orari dei pendolari; Percorrenze reali, affidabilità e tempi porta a porta; Localizzazione e gravità degli incidenti; Esposizione al traffico, stato e continuità dei percorsi

**Valore aggiunto:** Trasforma margini e inventari in domande sull’accessibilità, non in ordini di nuove corse.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `commuting_selfContainment`, `outside_046018`, `tpl_scheduledTplTripsPer1000_total_046018`, `road_roadSafety_measure_incidents_history_046018`, `slow_slowMobilityRoutes_total_046005`

#### mobilita-1 — partially_supported

Quanto il lavoro dei residenti dipende da spostamenti fuori Comune e che cosa offre il TPL?

**Risposta oggi e interpretazione consentita:** Affiancare pendolarismo 2021 e offerta programmata TPL nella fotografia propria; non stimare un bacino o una quota modale.

**Informazioni mancanti:** Origini–destinazioni e orari dei pendolari; Percorrenze reali, affidabilità e tempi porta a porta

**Valore aggiunto:** Trasforma margini e inventari in domande sull’accessibilità, non in ordini di nuove corse.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `commuting_selfContainment` — `compare`; esito `computed`.

**Risultati:** Camaiore 2021: 49,9 %; Massarosa 2021: 28,6 %

**Universi e definizioni:** resident habitual work commuters — within own municipality / resident habitual work commuters * 100

**Fonti:** [https://esploradati.istat.it/databrowser/DWL/PERMPOP/MATPEN/matrix_pendoLAVORO_2021.zip](https://esploradati.istat.it/databrowser/DWL/PERMPOP/MATPEN/matrix_pendoLAVORO_2021.zip)

**Avvertenze:** commuting_counts_and_ratios_share_components_and_population_size, commuting_is_not_transport_mode_capacity_quality_or_causal_policy_effect, gross_municipal_flows_include_moves_within_selected_group, habitual_work_commuters_not_all_daily_trips_or_jobs, municipal_marginals_do_not_identify_origin_destination_pairs, outside_municipality_census_share_not_complement_of_work_matrix_retention, pooled_same_municipality_retention_not_retention_within_selected_group, ratio_from_exact_components_published_share_rounded_to_one_decimal, single_2021_snapshot_not_current_mobility

**Componente della risposta**

Richiesta `outside_046018` — `compare`; esito `computed`.

**Risultati:** Massarosa 2021: 62,9 %; Viareggio 2021: 31,8 %

**Universi e definizioni:** resident employed persons in the published census indicator; not work-matrix daily commuters — published share of resident workers whose workplace is in another municipality

**Fonti:** [https://www.istat.it/statistiche-per-temi/censimenti/popolazione-e-abitazioni/risultati/](https://www.istat.it/statistiche-per-temi/censimenti/popolazione-e-abitazioni/risultati/)

**Avvertenze:** outside_2021_reference_not_current_daily_travel_or_study_mobility, outside_census_resident_worker_share_not_work_matrix_commuter_universe, outside_native_numerator_denominator_not_frozen_no_count_reconstruction, outside_not_complement_of_matrix_self_containment, outside_numerical_rank_not_transport_need_or_policy_priority, outside_public_catalog_replay_not_original_census_records, outside_seven_town_simple_mean_not_versilia_worker_share, outside_work_in_other_municipality_not_outside_versilia

**Componente della risposta**

Richiesta `tpl_scheduledTplTripsPer1000_total_046018` — `compare`; esito `computed`.

**Risultati:** Forte dei Marmi 2026-08-26: 110,0 number; Massarosa 2026-08-26: 106,0 number

**Universi e definizioni:** municipal scheduled trip memberships — count of trips serving at least one usable geolocated access ID, deduplicated within municipality

**Fonti:** [https://dati.toscana.it/dataset/rt-oraritb](https://dati.toscana.it/dataset/rt-oraritb)

**Avvertenze:** tpl_feed_stop_ids_not_unique_physical_stops_or_walk_access, tpl_gtfs_calendar_spatial_join_and_raw_feeds_not_replayed, tpl_municipal_trip_memberships_not_unique_territorial_trips, tpl_no_automatic_causal_or_policy_priority_inference, tpl_scheduled_summer_weekday_not_actual_service_reliability_capacity_or_passengers, tpl_span_not_frequency_or_continuous_service

#### mobilita-2 — partially_supported

Quali problemi di sicurezza e possibilità di mobilità lenta richiedono un’indagine locale?

**Risposta oggi e interpretazione consentita:** Usare incidenti e inventario editoriale dei percorsi come contesti; conteggi di itinerari non certificano sicurezza o continuità della rete.

**Informazioni mancanti:** Localizzazione e gravità degli incidenti; Esposizione al traffico, stato e continuità dei percorsi

**Valore aggiunto:** Trasforma margini e inventari in domande sull’accessibilità, non in ordini di nuove corse.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `road_roadSafety_measure_incidents_history_046018` — `series`; esito `computed`.

**Risultati:** Massarosa 2014: 3,5 per1000; Massarosa 2015: 3,5 per1000; Massarosa 2016: 4,0 per1000; Massarosa 2017: 3,2 per1000; Massarosa 2018: 3,7 per1000; Massarosa 2019: 4,5 per1000; Massarosa 2020: 3,1 per1000; Massarosa 2021: 3,3 per1000; Massarosa 2022: 3,6 per1000; Massarosa 2023: 4,2 per1000; Massarosa 2024: 4,4 per1000

**Universi e definizioni:** annual average resident population; incidents localized to municipality — Incidenti con lesioni; annual average resident population; incidents localized to municipality

**Fonti:** [https://www.istat.it/storage/misura-comune/15a-Infrastrutture-e-mobilita-incidenti-stradali.xlsx](https://www.istat.it/storage/misura-comune/15a-Infrastrutture-e-mobilita-incidenti-stradali.xlsx)

**Avvertenze:** road_accident_location_not_injured_residence_or_resident_risk, road_mortality_and_injury_indices_per100_incidents_not_population_percentages, road_municipal_mean_not_pooled_versilia_rate, road_published_rates_no_reverse_derived_counts_or_denominators, road_temporal_continuity_and_pairs_not_reviewed, road_traffic_tourism_and_small_counts_preclude_automatic_policy_ranking

**Componente della risposta**

Richiesta `slow_slowMobilityRoutes_total_046005` — `compare`; esito `computed`.

**Risultati:** Camaiore 2026-08-12: 11,0 count; Massarosa 2026-08-12: 5,0 count

**Universi e definizioni:** public A0/B1 route records with frozen municipal membership — count distinct route IDs assigned to municipality; all primary modes

**Fonti:** [https://osservatorioversilia.it/percorsi/metodo.html](https://osservatorioversilia.it/percorsi/metodo.html)

**Avvertenze:** slow_mobility_A0_B1_provenance_not_accessibility_quality, slow_mobility_inventory_20260812_not_current_route_status, slow_mobility_inventory_not_exhaustive_or_current_safety, slow_mobility_membership_replay_not_geometry_intersection_replay, slow_mobility_municipal_memberships_overlap_not_additive_unique_routes, slow_mobility_no_municipal_lengths_or_reverse_derived_rates, slow_mobility_numeric_rank_not_policy_priority, slow_mobility_primary_mode_not_all_possible_activities

#### Controlli metodologici, separati dalle domande territoriali

- I margini comunali descrivono attraversamenti del confine Versilia? No: i margini comunali non identificano le coppie origine-destinazione. Serve la matrice OD per quantificare attraversamenti del confine Versilia.
- Orari programmati e fermate descrivono viaggi possibili e affidabili? Non determinabile dai dati acquisiti: Tempi porta a porta, frequenze per fascia, passeggeri e regolarità. Nessuna stima sostitutiva è autorizzata.

### Turismo e pressione sui servizi

**Competenze da verificare negli atti vigenti:** Comune: servizi locali e gestione territoriale; Regione e gestori competenti per reti e programmazione; imprese come interlocutori.

**Domande A6 riusate e approfondite, non nuove certificazioni:** turismo-servizi

**Opzioni da approfondire:** Approfondire gestione stagionale e interscambio, separando domanda osservata e ipotesi.

**Monitoraggio:** Carichi per mese/giorno, regolarità e costi di servizio; presenze come contesto.

#### turismo-centrale — partially_supported

Come cambia l’uso del territorio turistico e quali carichi dei servizi restano ignoti?

**Risposta oggi e interpretazione consentita:** Comporre risposte deterministiche separate, preservando periodi, universi, fonti, missing e rifiuti; nessuna fusione causale o aritmetica non autorizzata.

**Informazioni mancanti:** Escursionisti, popolazione giornaliera e picchi; Consumi/rifiuti per mese e area, capacità dei servizi; Escursionismo e occupazione giornaliera; Domanda oraria e stagionale dei servizi; Volumi e costi mensili per bacino; Popolazione effettivamente servita e usi non turistici

**Valore aggiunto:** Non scambia pernottamenti per persone né pressione potenziale per carico misurato.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `tourism_tourismPresences_history`, `seasonality_compare_046005`, `tourism_tourismBedsPer1000_current`, `environment_waste_current`, `environment_water_current`, `tourism_tourismPresences_current`

#### turismo-1 — partially_supported

Quali periodi concentrano la presenza turistica e quali servizi vanno approfonditi?

**Risposta oggi e interpretazione consentita:** Descrivere pernottamenti, concentrazione stagionale e ricettività; non ricostruire presenze giornaliere o escursionisti.

**Informazioni mancanti:** Escursionismo e occupazione giornaliera; Domanda oraria e stagionale dei servizi

**Valore aggiunto:** Non scambia pernottamenti per persone né pressione potenziale per carico misurato.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `tourism_tourismPresences_history` — `series`; esito `computed`.

**Risultati:** Camaiore 2023: 507.072,0 number; Camaiore 2024: 530.713,0 number; Camaiore 2025: 528.521,0 number

**Universi e definizioni:** registered accommodation movement net of rentals; foreign means residence abroad, not citizenship — registered accommodation nights

**Fonti:** [https://www.regione.toscana.it/documents/10180/11976751/Movimento%2Bper%2Bcomune%2B2023.xlsx/68162001-ccd5-6879-81c9-99639ee947bb?t=1709731593776](https://www.regione.toscana.it/documents/10180/11976751/Movimento%2Bper%2Bcomune%2B2023.xlsx/68162001-ccd5-6879-81c9-99639ee947bb?t=1709731593776); [https://www.regione.toscana.it/documents/d/guest/2-movimento-per-comune-2024-ods](https://www.regione.toscana.it/documents/d/guest/2-movimento-per-comune-2024-ods); [https://www.regione.toscana.it/documents/d/guest/2-movimento-per-comune-2025-agg-maggio-2026-](https://www.regione.toscana.it/documents/d/guest/2-movimento-per-comune-2025-agg-maggio-2026-)

**Avvertenze:** tourism_arrivals_not_unique_people, tourism_existing_presences_operations_preserved, tourism_frozen_extraction_not_new_live_acquisition, tourism_movement_net_of_rentals_provisional, tourism_numerical_rank_not_destination_quality

**Componente della risposta**

Richiesta `seasonality_compare_046005` — `compare`; esito `computed`.

**Risultati:** Camaiore 2025: 55,7 %; Massarosa 2025: 50,9 %

**Universi e definizioni:** recorded tourist overnight stays in reporting accommodation establishments — share of annual overnight stays in the three months with the most overnight stays, independently selected per geography

**Fonti:** [https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025%C2%A0](https://www.regione.toscana.it/-/arrivi-e-presenze-nelle-strutture-ricettive-e-struttura-dell-offerta-dati-2025%C2%A0)

**Avvertenze:** seasonality_annual_measure_not_monthly_time_series, seasonality_concentration_not_volume_quality_or_policy_priority, seasonality_public_replay_not_native_monthly_panel, seasonality_sum_of_local_top_three_not_regional_top_three, seasonality_top_three_months_not_fixed_summer_quarter

**Componente della risposta**

Richiesta `tourism_tourismBedsPer1000_current` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 222,0 per1000; Massarosa 2024: 39,8 per1000

**Universi e definizioni:** Istat hotel and non-hotel capacity 2024; private non-business accommodation expansion 2025 excluded — Istat beds 2024 / Istat estimated residents 1 January 2026 × 1000

**Fonti:** [https://esploradati.istat.it/databrowser/DWL/Servizi/DCSC%20Capacity%20of%20tourist%20accommodation%20municipal.zip](https://esploradati.istat.it/databrowser/DWL/Servizi/DCSC%20Capacity%20of%20tourist%20accommodation%20municipal.zip)

**Avvertenze:** tourism_capacity_2024_residents_2026_distinct, tourism_capacity_2025_scope_expansion_excluded, tourism_frozen_extraction_not_new_live_acquisition, tourism_native_7899_municipal_records_not_new_workbook_replay, tourism_numerical_rank_not_destination_quality, tourism_posas_2026_estimate

#### turismo-2 — partially_supported

Acqua e rifiuti mostrano carichi attribuibili al turismo?

**Risposta oggi e interpretazione consentita:** Affiancare indicatori annuali nei rispettivi anni. Nessuna attribuzione causale o ripartizione dei costi per visitatore.

**Informazioni mancanti:** Volumi e costi mensili per bacino; Popolazione effettivamente servita e usi non turistici

**Valore aggiunto:** Non scambia pernottamenti per persone né pressione potenziale per carico misurato.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `environment_waste_current` — `compare`; esito `computed`.

**Risultati:** Massarosa 2024: 603,0 kg; Viareggio 2024: 707,0 kg

**Universi e definizioni:** municipal urban waste accounting; resident normalization is not individual consumption — official rounded municipal urban waste kg per resident; not visitor production

**Fonti:** [https://www.catasto-rifiuti.isprambiente.it/index.php?pg=findComune](https://www.catasto-rifiuti.isprambiente.it/index.php?pg=findComune)

**Avvertenze:** waste_historical_series_does_not_attest_methodological_continuity, waste_raw_municipal_quantities_not_frozen_no_implicit_weighting, waste_resident_denominator_not_population_present_or_tourist_production

**Componente della risposta**

Richiesta `environment_water_current` — `compare`; esito `computed`.

**Risultati:** Massarosa 2018: 42,0 %; Viareggio 2018: 35,9 %

**Universi e definizioni:** municipal distribution network water volumes — (water input - authorized delivered water) / water input * 100

**Fonti:** [https://esploradati.istat.it/](https://esploradati.istat.it/)

**Avvertenze:** water_census_snapshot_not_current_network_condition, water_loss_components_not_split_in_snapshot

**Componente della risposta**

Richiesta `tourism_tourismPresences_current` — `compare`; esito `computed`.

**Risultati:** Camaiore 2025: 528.521,0 number; Massarosa 2025: 37.898,0 number

**Universi e definizioni:** registered accommodation movement net of rentals; foreign means residence abroad, not citizenship — registered accommodation nights

**Fonti:** [https://www.regione.toscana.it/documents/d/guest/2-movimento-per-comune-2025-agg-maggio-2026-](https://www.regione.toscana.it/documents/d/guest/2-movimento-per-comune-2025-agg-maggio-2026-)

**Avvertenze:** tourism_arrivals_not_unique_people, tourism_existing_presences_operations_preserved, tourism_frozen_extraction_not_new_live_acquisition, tourism_movement_net_of_rentals_provisional, tourism_numerical_rank_not_destination_quality

#### Controlli metodologici, separati dalle domande territoriali

- Pernottamenti annuali misurano i picchi giornalieri? No: pernottamenti sono un flusso; picchi giornalieri e escursionisti richiedono informazioni diverse.
- I rapporti per residente descrivono utenti effettivi dei servizi? Non determinabile dai dati acquisiti: Consumi/rifiuti per mese e area, capacità dei servizi. Nessuna stima sostitutiva è autorizzata.

### Ambiente, clima e rischio

**Competenze da verificare negli atti vigenti:** Comune: urbanistica/protezione civile e servizi; Regione, enti di bacino e gestori secondo competenze di ciascun intervento da verificare.

**Domande A6 riusate e approfondite, non nuove certificazioni:** nessuna corrispondenza diretta

**Opzioni da approfondire:** Approfondire vulnerabilità, manutenzione e piani di protezione; non sommare scenari annidati.

**Monitoraggio:** Esposizioni coerenti, danni, continuità dei servizi ed esiti degli interventi con baseline.

#### ambiente-centrale — partially_supported

Quali esposizioni e trasformazioni richiedono verifiche di protezione e adattamento?

**Risposta oggi e interpretazione consentita:** Comporre risposte deterministiche separate, preservando periodi, universi, fonti, missing e rifiuti; nessuna fusione causale o aritmetica non autorizzata.

**Informazioni mancanti:** Vulnerabilità, danni ed efficacia delle opere; Geometrie e scenari locali aggiornati, qualità dell’aria dove non misurata; Vulnerabilità di persone e infrastrutture; Scenari, eventi e misure di adattamento localizzate; Monitoraggi degli effetti delle opere costiere; Stato operativo, contaminanti e risultati delle bonifiche

**Valore aggiunto:** Separa classificazioni, esposizioni e risultati, senza trasformare una mappa in previsione individuale.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `hazard_flood_current`, `hazard_landslide_current`, `climate_temperature_series`, `climate_precipitation_series`, `coast_dynamics_erosion`, `coast_protection_current`, `remediation_total`

#### ambiente-1 — partially_supported

Quali esposizioni a frane e alluvioni e quali tendenze climatiche orientano verifiche di adattamento?

**Risposta oggi e interpretazione consentita:** Distinguere esposizione cartografica, tendenza climatica e rischio; non prevedere danni o eventi per singolo immobile.

**Informazioni mancanti:** Vulnerabilità di persone e infrastrutture; Scenari, eventi e misure di adattamento localizzate

**Valore aggiunto:** Separa classificazioni, esposizioni e risultati, senza trasformare una mappa in previsione individuale.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `hazard_flood_current` — `compare`; esito `computed`.

**Risultati:** Camaiore 2020: 29,7 %; Forte dei Marmi 2020: 6,9 %; Massarosa 2020: 71,8 %; Pietrasanta 2020: 14,7 %; Seravezza 2020: 6,0 %; Stazzema 2020: 0,5 %; Viareggio 2020: 14,6 %

**Universi e definizioni:** ISPRA map 2020; municipal limits 2024; census residents 2011 — flood P2 residentsPct from official source scenario, not sums of classes

**Fonti:** [https://idrogeo.isprambiente.it/](https://idrogeo.isprambiente.it/)

**Avvertenze:** hazard_flood_scenarios_nested_do_not_sum, hazard_maps_are_not_observed_damage_probabilities_or_policy_effects, hazard_native_ratios_and_published_three_decimal_percent_kept_separate, hazard_residents_are_frozen_census_population_not_current_posas

**Componente della risposta**

Richiesta `hazard_landslide_current` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 5.750,0 number; Forte dei Marmi 2024: 0,0 number; Massarosa 2024: 3.534,0 number; Pietrasanta 2024: 1.202,0 number; Seravezza 2024: 492,0 number; Stazzema 2024: 1.600,0 number; Viareggio 2024: 6,0 number

**Universi e definizioni:** ISPRA map 2024; municipal limits 2024; census residents 2021 — landslide P3+P4 residents from official source scenario, not sums of classes

**Fonti:** [https://idrogeo.isprambiente.it/](https://idrogeo.isprambiente.it/)

**Avvertenze:** hazard_maps_are_not_observed_damage_probabilities_or_policy_effects, hazard_native_ratios_and_published_three_decimal_percent_kept_separate, hazard_p3_p4_combined_official_field_not_sum_of_rounded_classes, hazard_residents_are_frozen_census_population_not_current_posas

**Componente della risposta**

Richiesta `climate_temperature_series` — `series`; esito `computed`.

**Risultati:** Massarosa 1950: 15,3 celsius; Massarosa 1951: 15,0 celsius; Massarosa 1952: 15,0 celsius; Massarosa 1953: 14,8 celsius; Massarosa 1954: 14,0 celsius; Massarosa 1955: 15,0 celsius; Massarosa 1956: 13,5 celsius; Massarosa 1957: 14,5 celsius; Massarosa 1958: 14,8 celsius; Massarosa 1959: 15,1 celsius; Massarosa 1960: 14,7 celsius; Massarosa 1961: 15,3 celsius; Massarosa 1962: 14,5 celsius; Massarosa 1963: 14,2 celsius; Massarosa 1964: 15,0 celsius; Massarosa 1965: 14,3 celsius; Massarosa 1966: 14,6 celsius; Massarosa 1967: 14,9 celsius; Massarosa 1968: 14,5 celsius; Massarosa 1969: 14,5 celsius; Massarosa 1970: 14,7 celsius; Massarosa 1971: 14,6 celsius; Massarosa 1972: 14,3 celsius; Massarosa 1973: 14,6 celsius; Massarosa 1974: 14,5 celsius; Massarosa 1975: 14,6 celsius; Massarosa 1976: 14,3 celsius; Massarosa 1977: 14,6 celsius; Massarosa 1978: 14,0 celsius; Massarosa 1979: 14,6 celsius; Massarosa 1980: 13,7 celsius; Massarosa 1981: 14,4 celsius; Massarosa 1982: 15,1 celsius; Massarosa 1983: 14,9 celsius; Massarosa 1984: 14,0 celsius; Massarosa 1985: 14,8 celsius; Massarosa 1986: 14,9 celsius; Massarosa 1987: 14,7 celsius; Massarosa 1988: 15,1 celsius; Massarosa 1989: 14,9 celsius; Massarosa 1990: 15,3 celsius; Massarosa 1991: 14,5 celsius; Massarosa 1992: 15,2 celsius; Massarosa 1993: 14,9 celsius; Massarosa 1994: 15,8 celsius; Massarosa 1995: 14,6 celsius; Massarosa 1996: 14,6 celsius; Massarosa 1997: 15,5 celsius; Massarosa 1998: 15,0 celsius; Massarosa 1999: 15,1 celsius; Massarosa 2000: 15,4 celsius; Massarosa 2001: 15,3 celsius; Massarosa 2002: 15,2 celsius; Massarosa 2003: 15,6 celsius; Massarosa 2004: 14,8 celsius; Massarosa 2005: 14,5 celsius; Massarosa 2006: 15,2 celsius; Massarosa 2007: 15,3 celsius; Massarosa 2008: 15,4 celsius; Massarosa 2009: 15,7 celsius; Massarosa 2010: 14,7 celsius; Massarosa 2011: 15,7 celsius; Massarosa 2012: 15,5 celsius; Massarosa 2013: 15,3 celsius; Massarosa 2014: 16,2 celsius; Massarosa 2015: 16,2 celsius; Massarosa 2016: 15,9 celsius; Massarosa 2017: 15,8 celsius; Massarosa 2018: 16,3 celsius; Massarosa 2019: 16,2 celsius; Massarosa 2020: 16,0 celsius; Massarosa 2021: 15,6 celsius; Massarosa 2022: 16,9 celsius; Massarosa 2023: 16,7 celsius; Massarosa 2024: 16,7 celsius; Massarosa 2025: 16,6 celsius

**Universi e definizioni:** municipal territory, fractionally weighted raster cells on Istat 2026 boundaries; not station observations or resident exposure — municipal territorial annual mean temperature

**Fonti:** [https://dati.lamma.toscana.it/](https://dati.lamma.toscana.it/)

**Avvertenze:** climate_draft_named_input_already_used_by_public_runtime, climate_frozen_reconstruction_not_live_or_station_record, climate_legacy_catalog_label_not_primary_annual_definition, climate_no_areal_or_population_pooled_average, climate_ols_descriptive_no_significance_forecast_or_causality, climate_raw_grids_calibration_validation_not_replayed, climate_stitched_observations_and_calibrated_reanalysis

**Componente della risposta**

Richiesta `climate_precipitation_series` — `series`; esito `computed`.

**Risultati:** Massarosa 1950: 1.010,6 mm; Massarosa 1951: 1.520,7 mm; Massarosa 1952: 1.192,5 mm; Massarosa 1953: 802,7 mm; Massarosa 1954: 989,5 mm; Massarosa 1955: 1.126,5 mm; Massarosa 1956: 964,4 mm; Massarosa 1957: 1.127,4 mm; Massarosa 1958: 1.205,4 mm; Massarosa 1959: 1.205,1 mm; Massarosa 1960: 1.906,4 mm; Massarosa 1961: 1.140,1 mm; Massarosa 1962: 997,4 mm; Massarosa 1963: 1.314,7 mm; Massarosa 1964: 1.141,2 mm; Massarosa 1965: 1.567,5 mm; Massarosa 1966: 1.440,2 mm; Massarosa 1967: 1.129,4 mm; Massarosa 1968: 1.537,0 mm; Massarosa 1969: 1.227,4 mm; Massarosa 1970: 1.146,9 mm; Massarosa 1971: 1.200,2 mm; Massarosa 1972: 1.368,6 mm; Massarosa 1973: 989,8 mm; Massarosa 1974: 1.080,1 mm; Massarosa 1975: 1.176,7 mm; Massarosa 1976: 1.378,5 mm; Massarosa 1977: 1.531,4 mm; Massarosa 1978: 1.259,0 mm; Massarosa 1979: 1.501,5 mm; Massarosa 1980: 1.260,7 mm; Massarosa 1981: 1.190,2 mm; Massarosa 1982: 1.173,0 mm; Massarosa 1983: 950,1 mm; Massarosa 1984: 1.412,2 mm; Massarosa 1985: 941,1 mm; Massarosa 1986: 984,0 mm; Massarosa 1987: 1.182,5 mm; Massarosa 1988: 998,0 mm; Massarosa 1989: 1.073,0 mm; Massarosa 1990: 1.033,3 mm; Massarosa 1991: 1.004,6 mm; Massarosa 1992: 1.249,6 mm; Massarosa 1993: 1.026,0 mm; Massarosa 1994: 947,9 mm; Massarosa 1995: 1.072,8 mm; Massarosa 1996: 1.211,5 mm; Massarosa 1997: 786,4 mm; Massarosa 1998: 964,2 mm; Massarosa 1999: 1.282,2 mm; Massarosa 2000: 1.379,8 mm; Massarosa 2001: 918,3 mm; Massarosa 2002: 1.260,6 mm; Massarosa 2003: 819,5 mm; Massarosa 2004: 1.168,9 mm; Massarosa 2005: 860,3 mm; Massarosa 2006: 711,5 mm; Massarosa 2007: 687,3 mm; Massarosa 2008: 1.307,6 mm; Massarosa 2009: 1.323,4 mm; Massarosa 2010: 1.621,3 mm; Massarosa 2011: 811,8 mm; Massarosa 2012: 1.105,1 mm; Massarosa 2013: 1.345,6 mm; Massarosa 2014: 1.711,4 mm; Massarosa 2015: 991,6 mm; Massarosa 2016: 1.268,9 mm; Massarosa 2017: 1.015,1 mm; Massarosa 2018: 1.097,7 mm; Massarosa 2019: 1.254,6 mm; Massarosa 2020: 1.198,8 mm; Massarosa 2021: 1.166,1 mm; Massarosa 2022: 871,7 mm; Massarosa 2023: 1.275,4 mm; Massarosa 2024: 1.374,8 mm; Massarosa 2025: 1.336,5 mm

**Universi e definizioni:** municipal territory, fractionally weighted raster cells on Istat 2026 boundaries; not station observations or resident exposure — municipal territorial annual precipitation total in mm, not municipal total water volume

**Fonti:** [https://dati.lamma.toscana.it/](https://dati.lamma.toscana.it/)

**Avvertenze:** climate_draft_named_input_already_used_by_public_runtime, climate_frozen_reconstruction_not_live_or_station_record, climate_legacy_catalog_label_not_primary_annual_definition, climate_no_areal_or_population_pooled_average, climate_ols_descriptive_no_significance_forecast_or_causality, climate_raw_grids_calibration_validation_not_replayed, climate_stitched_observations_and_calibrated_reanalysis

#### ambiente-2 — partially_supported

Che cosa mostrano costa e bonifiche e quali interventi richiedono evidenze ulteriori?

**Risposta oggi e interpretazione consentita:** Descrivere tratti costieri e procedimenti nelle fotografie proprie; protezione rigida e procedimento non misurano efficacia o risanamento concluso.

**Informazioni mancanti:** Monitoraggi degli effetti delle opere costiere; Stato operativo, contaminanti e risultati delle bonifiche

**Valore aggiunto:** Separa classificazioni, esposizioni e risultati, senza trasformare una mappa in previsione individuale.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `coast_dynamics_erosion` — `compare`; esito `computed`.

**Risultati:** Camaiore 2006-2020: 0,3 %; Viareggio 2006-2020: 1,5 %

**Universi e definizioni:** ISPRA natural low coast analysed 2006–2020; displacement threshold 5 metres — ISPRA natural low coast analysed 2006–2020; displacement threshold 5 metres; erosionShare

**Fonti:** [https://indicatoriambientali.isprambiente.it/it/coste/dinamica-litoranea](https://indicatoriambientali.isprambiente.it/it/coste/dinamica-litoranea)

**Avvertenze:** coast_four_littoral_three_not_applicable, coast_source_universes_not_interchangeable, shoreline_interval_not_annual_rate, shoreline_natural_low_coast_threshold_five_metres

**Componente della risposta**

Richiesta `coast_protection_current` — `compare`; esito `computed`.

**Risultati:** Camaiore 2020: 7,2 %; Viareggio 2020: 0,0 %

**Universi e definizioni:** ISPRA 2020 coastal universe; rigid defence excludes nourishment — ISPRA 2020 coastal universe; rigid defence excludes nourishment; protectedShare

**Fonti:** [https://indicatoriambientali.isprambiente.it/it/coste/costa-protetta](https://indicatoriambientali.isprambiente.it/it/coste/costa-protetta)

**Avvertenze:** coast_four_littoral_three_not_applicable, coast_source_universes_not_interchangeable, rigid_defence_excludes_nourishment_not_effectiveness_or_damage_risk

**Componente della risposta**

Richiesta `remediation_total` — `compare`; esito `computed`.

**Risultati:** Camaiore 2026-10-11: 10,0 number; Forte dei Marmi 2026-10-11: 10,0 number; Massarosa 2026-10-11: 6,0 number; Pietrasanta 2026-10-11: 10,0 number; Seravezza 2026-10-11: 3,0 number; Stazzema 2026-10-11: 4,0 number; Viareggio 2026-10-11: 15,0 number

**Universi e definizioni:** distinct regional SISBON proceedings assigned to municipality in frozen snapshot — active administrative proceedings; not currently contaminated sites, risk or remediation effectiveness

**Fonti:** [https://sisbon.regione.toscana.it/api/v1/sisbon/map_public?format=csv](https://sisbon.regione.toscana.it/api/v1/sisbon/map_public?format=csv)

**Avvertenze:** sisbon_active_share_not_remediation_effectiveness, sisbon_administrative_stock_not_annual_flow, sisbon_closed_not_necessarily_remediated, sisbon_proceeding_not_current_contamination_or_risk, sisbon_regional_id_not_coordinates_is_identity

#### Controlli metodologici, separati dalle domande territoriali

- Pericolosità, esposizione e rischio sono distinti? Le definizioni degli adapter separano esposizione da probabilità/danno: non producono un indice universale di rischio.
- Serie ricostruite e opere censite dimostrano efficacia degli interventi? Non determinabile dai dati acquisiti: Geometrie e scenari locali aggiornati, qualità dell’aria dove non misurata. Nessuna stima sostitutiva è autorizzata.

### Suolo, agricoltura e biodiversità

**Competenze da verificare negli atti vigenti:** Comune: pianificazione locale; Regione/enti gestori: pianificazione e tutela di settore; imprese agricole come interlocutori.

**Domande A6 riusate e approfondite, non nuove certificazioni:** nessuna corrispondenza diretta

**Opzioni da approfondire:** Approfondire riuso del suolo e supporto alle filiere, senza dedurre biodiversità da ettari protetti.

**Monitoraggio:** Superfici omogenee, habitat e pressioni; categorie sovrapposte non additive.

#### suolo-centrale — partially_supported

Quali trasformazioni del territorio incidono sulle risorse naturali e produttive?

**Risposta oggi e interpretazione consentita:** Comporre risposte deterministiche separate, preservando periodi, universi, fonti, missing e rifiuti; nessuna fusione causale o aritmetica non autorizzata.

**Informazioni mancanti:** Habitat/specie e stato ecologico; Continuità metodologica, uso effettivo e qualità del suolo; Habitat, specie e qualità ecologica; Dettaglio territoriale dei nuovi interventi; Redditività e domanda di lavoro; Transizioni, accesso alla terra e successioni

**Valore aggiunto:** Collega produzione e risorse naturali preservando geografie e classificazioni.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `soil_stock_current`, `soil_flow_gross`, `soil_ucs_forest`, `territory_protected_union`, `agriculture_localized`, `agriculture_profiles_agriculturalRenewalAndLeadership_total`, `agriculture_profiles_organicAgriculturalAreaShare_total`

#### suolo-1 — partially_supported

Dove consumo di suolo e usi del territorio cambiano il patrimonio naturale?

**Risposta oggi e interpretazione consentita:** Distinguere stock, flussi e unione di aree protette; superficie tutelata non misura stato della biodiversità.

**Informazioni mancanti:** Habitat, specie e qualità ecologica; Dettaglio territoriale dei nuovi interventi

**Valore aggiunto:** Collega produzione e risorse naturali preservando geografie e classificazioni.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `soil_stock_current` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 14,2 %; Forte dei Marmi 2024: 46,2 %; Massarosa 2024: 13,4 %; Pietrasanta 2024: 24,7 %; Seravezza 2024: 12,2 %; Stazzema 2024: 3,0 %; Viareggio 2024: 38,5 %

**Universi e definizioni:** municipal cartographic territory; UCS and ISPRA surfaces are not interchangeable — ISPRA frozen percent soil consumption stock

**Fonti:** [https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/suolo/il-consumo-di-suolo/i-dati-sul-consumo-di-suolo](https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/suolo/il-consumo-di-suolo/i-dati-sul-consumo-di-suolo)

**Avvertenze:** soil_history_readable_comparability_not_attested, soil_ispra_consumption_ucs_cover_and_cfi_forest_are_distinct, soil_published_percent_three_decimals_native_pooled_ratio_may_differ

**Componente della risposta**

Richiesta `soil_flow_gross` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 1,1 hectares; Forte dei Marmi 2024: 0,2 hectares; Massarosa 2024: 0,0 hectares; Pietrasanta 2024: 0,3 hectares; Seravezza 2024: 0,1 hectares; Stazzema 2024: 0,0 hectares; Viareggio 2024: 0,6 hectares

**Universi e definizioni:** municipal cartographic territory; UCS and ISPRA surfaces are not interchangeable — ISPRA frozen gross soil consumption increment; endpoint labels do not attest equal observation intervals

**Fonti:** [https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/suolo/il-consumo-di-suolo/i-dati-sul-consumo-di-suolo](https://www.isprambiente.gov.it/it/attivita/suolo-e-territorio/suolo/il-consumo-di-suolo/i-dati-sul-consumo-di-suolo)

**Avvertenze:** soil_flow_not_difference_of_rounded_stocks_or_annualized_irregular_intervals, soil_history_readable_comparability_not_attested, soil_ispra_consumption_ucs_cover_and_cfi_forest_are_distinct, soil_net_can_be_negative_not_a_certified_restoration_effect

**Componente della risposta**

Richiesta `soil_ucs_forest` — `compare`; esito `computed`.

**Risultati:** Camaiore 2019: 47,0 %; Forte dei Marmi 2019: 2,1 %; Massarosa 2019: 19,5 %; Pietrasanta 2019: 23,1 %; Seravezza 2019: 50,6 %; Stazzema 2019: 72,0 %; Viareggio 2019: 14,0 %

**Universi e definizioni:** municipal cartographic territory; UCS and ISPRA surfaces are not interchangeable — UCS forest: cartographic cover class; hierarchical details overlap macroclasses

**Fonti:** [https://www502.regione.toscana.it/geonetwork/srv/api/records/r_toscan:0d4d6640-9a1c-47a4-9a5d-a85cdb36927c](https://www502.regione.toscana.it/geonetwork/srv/api/records/r_toscan:0d4d6640-9a1c-47a4-9a5d-a85cdb36927c)

**Avvertenze:** soil_history_readable_comparability_not_attested, soil_ispra_consumption_ucs_cover_and_cfi_forest_are_distinct, ucs_detail_classes_overlap_macroclasses_do_not_sum, ucs_total_surface_not_istat_or_ispra_municipal_surface

**Componente della risposta**

Richiesta `territory_protected_union` — `compare`; esito `computed`.

**Risultati:** Camaiore 2026-09-12: 28,7 %; Forte dei Marmi 2026-09-12: 0,5 %; Massarosa 2026-09-12: 33,4 %; Pietrasanta 2026-09-12: 2,1 %; Seravezza 2026-09-12: 76,4 %; Stazzema 2026-09-12: 99,9 %; Viareggio 2026-09-12: 39,8 %

**Universi e definizioni:** municipal territory clipped with Istat 1 January 2026 boundaries — protected surface total; total is geometric union, categories overlap

**Fonti:** [https://www.regione.toscana.it/sistema-aree-naturali-protette](https://www.regione.toscana.it/sistema-aree-naturali-protette)

**Avvertenze:** anpil_transitional_status_not_new_designation, protected_categories_overlap_total_is_native_geometric_union_not_category_sum, protected_consultation_date_not_uniform_layer_reference_year, territory_single_frozen_edition_no_temporal_inference

#### suolo-2 — partially_supported

Quali caratteristiche dell’agricoltura aiutano a discutere il ricambio produttivo?

**Risposta oggi e interpretazione consentita:** Descrivere superficie secondo localizzazione/attribuzione della fonte e profili aziendali; non dedurre produttività o rinnovo individuale.

**Informazioni mancanti:** Redditività e domanda di lavoro; Transizioni, accesso alla terra e successioni

**Valore aggiunto:** Collega produzione e risorse naturali preservando geografie e classificazioni.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `agriculture_localized` — `compare`; esito `computed`.

**Risultati:** Massarosa 2020: 1.370,6 hectares; Pietrasanta 2020: 329,3 hectares

**Universi e definizioni:** physically localized agricultural land — ARU/ALL/TOT: physically localized agricultural area in hectares

**Fonti:** [https://www.istat.it/statistiche-per-temi/censimenti/agricoltura/7-censimento-generale/risultati/](https://www.istat.it/statistiche-per-temi/censimenti/agricoltura/7-censimento-generale/risultati/)

**Avvertenze:** agriculture_census_2020_not_current_2026_conditions, agriculture_not_productivity_income_water_volume_or_policy_effect, farm_center_attribution_not_physical_location_of_all_land, pooled_farm_center_land_may_extend_outside_selected_municipalities, selected_crop_categories_not_exhaustive_partition

**Componente della risposta**

Richiesta `agriculture_profiles_agriculturalRenewalAndLeadership_total` — `compare`; esito `computed`.

**Risultati:** Forte dei Marmi 2020: 28,6 %; Massarosa 2020: 7,8 %

**Universi e definizioni:** excludingCollectiveProperties; holdings attributed to the frozen municipal census code — holdings with farm manager aged up to 40, excluding collective properties; separate numerator/denominator universe; no composite score

**Fonti:** [https://www.istat.it/statistiche-per-temi/censimenti/agricoltura/7-censimento-generale/risultati/](https://www.istat.it/statistiche-per-temi/censimenti/agricoltura/7-censimento-generale/risultati/)

**Avvertenze:** agriculture_profiles_2020_census_not_current_conditions, agriculture_profiles_manager_not_holder, agriculture_profiles_no_individual_holding_or_unique_person_replay, agriculture_profiles_not_policy_effect_or_synthetic_index, agriculture_profiles_overlapping_characteristics_not_additive

**Componente della risposta**

Richiesta `agriculture_profiles_organicAgriculturalAreaShare_total` — `compare`; esito `computed`.

**Risultati:** Forte dei Marmi 2024: 1,5 %; Massarosa 2024: 4,3 %

**Universi e definizioni:** agricultural utilized area in regional municipal indicator ind20; frozen published denominator not acquired — published share of utilized agricultural area cultivated organically; not share of farms

**Fonti:** [https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali](https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali)

**Avvertenze:** agriculture_profiles_2020_census_not_current_conditions, agriculture_profiles_manager_not_holder, agriculture_profiles_municipal_median_not_territorial_share, agriculture_profiles_no_individual_holding_or_unique_person_replay, agriculture_profiles_no_organic_hectares_or_pooled_share, agriculture_profiles_not_policy_effect_or_synthetic_index, agriculture_profiles_overlapping_characteristics_not_additive, agriculture_profiles_rounded_early_annual_values_no_temporal_change_review

#### Controlli metodologici, separati dalle domande territoriali

- Coperture e aree protette misurano lo stato della biodiversità? Copertura del suolo e vincolo territoriale descrivono superfici, non stato di habitat o specie.
- Centro aziendale e superfici localizzate sono lo stesso perimetro? I metadati agricoli esplicitano il perimetro aziendale/localizzazione: non è autorizzata l’identità fra centro aziendale e superficie nel Comune.

### Energia e transizione accessibile

**Competenze da verificare negli atti vigenti:** Comune: patrimonio e pianificazione nel proprio ambito; autorità e gestori energetici da identificare per ogni progetto; competenze autorizzative non inferite dai dati.

**Domande A6 riusate e approfondite, non nuove certificazioni:** nessuna corrispondenza diretta

**Opzioni da approfondire:** Approfondire accesso e uso del patrimonio energetico; fattibilità tecnica/economica e autorizzazioni da verificare separatamente.

**Monitoraggio:** Consumi, costi, produzione e accesso per platea; non dedurre numero di connettori dalla densità EV.

#### energia-centrale — partially_supported

Che cosa sappiamo della transizione energetica e dei suoi costi per le famiglie?

**Risposta oggi e interpretazione consentita:** Comporre risposte deterministiche separate, preservando periodi, universi, fonti, missing e rifiuti; nessuna fusione causale o aritmetica non autorizzata.

**Informazioni mancanti:** Consumi, bollette, potenza e uso degli impianti; Produzione rinnovabile, reti e nuclei vulnerabili; Potenza e disponibilità reale delle colonnine; Consumi, percorrenze e utilizzatori; Consumi e curve di carico, costi energetici dei nuclei; Patrimonio edilizio pubblico, vincoli e impianti; Produzione rinnovabile e perimetri delle cabine

**Valore aggiunto:** Evita promesse sulla povertà energetica basate su proxy non sufficienti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `energy_ev_046018`, `energy_fuel_fuel:benzina_series`

#### energia-1 — partially_supported

Dove colonnine e prezzi dei carburanti descrivono condizioni della mobilità energetica?

**Risposta oggi e interpretazione consentita:** Descrivere punti inventariati e prezzi nei propri periodi. Non misurare utilizzo, potenza disponibile o povertà energetica.

**Informazioni mancanti:** Potenza e disponibilità reale delle colonnine; Consumi, percorrenze e utilizzatori

**Valore aggiunto:** Evita promesse sulla povertà energetica basate su proxy non sufficienti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `energy_ev_046018` — `compare`; esito `computed`.

**Risultati:** Massarosa 2026: 0,5 per1000; Viareggio 2026: 0,8 per1000

**Universi e definizioni:** published public active charging-point density; point/connector identity not certified from native rows — published rounded density per 1000 residents; components not frozen

**Fonti:** [https://www.piattaformaunicanazionale.it/idr](https://www.piattaformaunicanazionale.it/idr)

**Avvertenze:** ev_generic_commuting_caveat_not_ev_reference_evidence, ev_no_power_accessibility_availability_or_charging_quality_inference, ev_point_connector_station_identity_and_exact_reference_date_unresolved, ev_published_rounded_density_only_no_native_point_count_reconstruction

**Componente della risposta**

Richiesta `energy_fuel_fuel:benzina_series` — `series`; esito `computed`.

**Risultati:** Massarosa 2026-08-14: 2,0 eurliter; Massarosa 2026-08-27: 2,0 eurliter; Massarosa 2026-08-28: 2,0 eurliter; Massarosa 2026-10-03: 2,1 eurliter; Massarosa 2026-10-10: 2,1 eurliter

**Universi e definizioni:** self-service benzina reported at active MIMIT municipal stations; changing reporting universe — municipal station-price median on selected snapshot date

**Fonti:** [https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv](https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv)

**Avvertenze:** fuel_changing_station_reporting_universe_not_fixed_station_panel, fuel_mean_of_municipal_medians_not_versilia_station_median, fuel_monthly_days_observed_not_all_calendar_days, fuel_normalized_summary_replay_not_original_csv_tar_or_station_records, fuel_observed_price_not_volume_weighted_or_actual_household_spend, fuel_snapshot_median_not_monthly_mean_of_daily_medians, fuel_stazzema_missing_price_not_zero_or_all_future_absence

#### energia-2 — not_determinable

Quali edifici e famiglie potrebbero beneficiare di efficienza energetica, rinnovabili o comunità energetiche?

**Risposta oggi e interpretazione consentita:** Non determinabile: colonnine, carburanti e redditi fiscali non identificano consumi elettrici, superfici utilizzabili o condivisione in una CER.

**Informazioni mancanti:** Consumi e curve di carico, costi energetici dei nuclei; Patrimonio edilizio pubblico, vincoli e impianti; Produzione rinnovabile e perimetri delle cabine

**Valore aggiunto:** Evita promesse sulla povertà energetica basate su proxy non sufficienti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

Nessuna richiesta del catalogo attuale misura le variabili necessarie. Le eventuali richieste seguenti sono soltanto contesto.

**Solo contesto**

Richiesta `energy_ev_046018` — `compare`; esito `computed`.

**Risultati:** Massarosa 2026: 0,5 per1000; Viareggio 2026: 0,8 per1000

**Universi e definizioni:** published public active charging-point density; point/connector identity not certified from native rows — published rounded density per 1000 residents; components not frozen

**Fonti:** [https://www.piattaformaunicanazionale.it/idr](https://www.piattaformaunicanazionale.it/idr)

**Avvertenze:** ev_generic_commuting_caveat_not_ev_reference_evidence, ev_no_power_accessibility_availability_or_charging_quality_inference, ev_point_connector_station_identity_and_exact_reference_date_unresolved, ev_published_rounded_density_only_no_native_point_count_reconstruction

**Solo contesto**

Richiesta `mef_incomeDistribution_total` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 37,2 %; Forte dei Marmi 2024: 33,4 %; Massarosa 2024: 34,5 %; Pietrasanta 2024: 37,2 %; Seravezza 2024: 37,0 %; Stazzema 2024: 40,5 %; Viareggio 2024: 34,6 %

**Universi e definizioni:** known class frequencies only — known published class frequencies / sum of known class frequencies

**Fonti:** [https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800](https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800)

**Avvertenze:** mef_bands_not_current_tax_brackets, mef_frozen_extraction_not_new_live_acquisition, mef_income_source_frequencies_overlap_do_not_sum_people, mef_macro_known_cells_denominator_differs_from_eight_band_total_denominator, mef_missing_band_cells_not_zero_or_redistributed, mef_nominal_declared_income_not_disposable_income

#### Controlli metodologici, separati dalle domande territoriali

- Densità EV permette di conoscere capacità e uso della ricarica? Il censimento dei punti descrive dotazione, non potenza, utilizzo o accessibilità effettiva.
- Prezzi carburanti misurano spesa o povertà energetica? Non determinabile dai dati acquisiti: Produzione rinnovabile, reti e nuclei vulnerabili. Nessuna stima sostitutiva è autorizzata.

### Bilanci e risultati dei servizi

**Competenze da verificare negli atti vigenti:** Comune: programmazione finanziaria e controllo; gestori/enti associati per servizi con perimetri distinti.

**Domande A6 riusate e approfondite, non nuove certificazioni:** risorse-comunali, risorse-risultati

**Opzioni da approfondire:** Approfondire combinazioni di risorse e livelli di servizio, senza classifica di efficienza dalla spesa pro capite.

**Monitoraggio:** Utenti, costi omogenei, tempi ed esiti; dati contabili come input, non prova di effetto.

#### bilanci-centrale — partially_supported

Le risorse comunali sono sostenibili e quali risultati dei servizi possiamo verificare?

**Risposta oggi e interpretazione consentita:** Descrivere entrate di competenza, riscossione, rigidità, debito e cassa nei propri perimetri. Affiancare missioni e servizi senza equiparare impegni a prestazioni. Rapporti di somme solo se ammessi; tariffe standard non sono gettito o spesa effettiva familiare.

**Informazioni mancanti:** Costi e utenti per servizio, qualità ed esiti; Fabbisogni/costi standard confrontabili e perimetri gestionali; Vincoli, residui, FCDE e cronoprogrammi; Serie armonizzate delle risorse disponibili; Fabbisogni, utenti e standard di servizio comparabili; Costi, qualità, accesso e risultati per prestazione

**Valore aggiunto:** Rende leggibile la catena risorse–prestazioni–risultati e i suoi anelli mancanti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `finance_revenue`, `finance_rigid`, `distinct_debt_current`, `finance_balance`, `finance_social`, `dossier_primary_educationMissionExpenditurePerResident`, `environment_cost_current`, `tax_tariStandardHousehold_total_046018`

#### bilanci-1 — partially_supported

Quali risorse e vincoli finanziari osservabili distinguono Massarosa e Viareggio?

**Risposta oggi e interpretazione consentita:** Descrivere accertamenti, rigidità, debito e cassa con basi separate; non calcolare margine disponibile per nuovi interventi.

**Informazioni mancanti:** Vincoli, residui, FCDE e cronoprogrammi; Serie armonizzate delle risorse disponibili

**Valore aggiunto:** Rende leggibile la catena risorse–prestazioni–risultati e i suoi anelli mancanti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `finance_revenue` — `compare`; esito `computed`.

**Risultati:** Massarosa 2025: 1.446,9 €; Viareggio 2025: 1.633,9 €

**Universi e definizioni:** municipal accounting perimeter; resident normalization is not beneficiaries — current_revenue_accruals_titles_1_2_3 / exercise January 1 residents

**Fonti:** [https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/2025/2025_Rendiconto%20-%20Schemi%20di%20bilancio_TOSCANA.zip](https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/2025/2025_Rendiconto%20-%20Schemi%20di%20bilancio_TOSCANA.zip)

**Avvertenze:** gross_municipal_amounts_not_consolidated_for_interentity_transfers, municipal_accounting_perimeter_not_service_quality_or_policy_effect, nominal_finance_values_not_real_growth

**Componente della risposta**

Richiesta `finance_rigid` — `compare`; esito `computed`.

**Risultati:** Massarosa 2025: 20,7 %; Viareggio 2025: 24,5 %

**Universi e definizioni:** municipal accounting perimeter; resident normalization is not beneficiaries — official PDI 01.01 rigid expenditure share; rounded published measure

**Fonti:** [https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/2025/2025_Rendiconto%20-%20Piano%20degli%20indicatori_TOSCANA.zip](https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/2025/2025_Rendiconto%20-%20Piano%20degli%20indicatori_TOSCANA.zip)

**Avvertenze:** gross_municipal_amounts_not_consolidated_for_interentity_transfers, municipal_accounting_perimeter_not_service_quality_or_policy_effect, official_rounded_pdi_no_implicit_weighting

**Componente della risposta**

Richiesta `distinct_debt_current` — `compare`; esito `computed`.

**Risultati:** Massarosa 2025: 465,5 €; Viareggio 2025: 500,2 €

**Universi e definizioni:** municipal accounting or project perimeter; normalization is not beneficiaries — year-end D1 financing debt / exercise January 1 residents

**Fonti:** [https://openbdap.rgs.mef.gov.it/it/FET/Analizza](https://openbdap.rgs.mef.gov.it/it/FET/Analizza)

**Avvertenze:** d1_financing_debt_not_all_municipal_liabilities, debt_snapshot_archives_distinct_from_legacy_finance_release, gross_municipal_amounts_not_consolidated_for_interentity_transfers, massarosa_2019_distress_osl_liabilities_outside_ordinary_accounting_perimeter, municipal_accounting_or_project_carrier_not_policy_effect, nominal_finance_values_not_real_growth

**Componente della risposta**

Richiesta `finance_balance` — `compare`; esito `computed`.

**Risultati:** Massarosa 2025: -109,1 €; Viareggio 2025: -261,5 €

**Universi e definizioni:** municipal accounting perimeter; resident normalization is not beneficiaries — cash_balance / next January 1 residents

**Fonti:** [https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/datastore/dump/74533d22-b1c2-4d89-b1b9-b98e6c9713ff.csv](https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/datastore/dump/74533d22-b1c2-4d89-b1b9-b98e6c9713ff.csv)

**Avvertenze:** annual_cash_balance_not_year_end_cash_stock, cash_including_residual_payments_not_accrual_or_commitments, gross_municipal_amounts_not_consolidated_for_interentity_transfers, municipal_accounting_perimeter_not_service_quality_or_policy_effect, nominal_finance_values_not_real_growth, siope_next_year_resident_denominator

#### bilanci-2 — partially_supported

Spesa per servizi e fiscalità aiutano a capire adeguatezza e sostenibilità?

**Risposta oggi e interpretazione consentita:** Affiancare missioni, costi del servizio e tariffa convenzionale; non equiparare spesa di missione a costo unitario o risultato.

**Informazioni mancanti:** Fabbisogni, utenti e standard di servizio comparabili; Costi, qualità, accesso e risultati per prestazione

**Valore aggiunto:** Rende leggibile la catena risorse–prestazioni–risultati e i suoi anelli mancanti.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `finance_social` — `compare`; esito `computed`.

**Risultati:** Massarosa 2025: 196,5 €; Viareggio 2025: 286,5 €

**Universi e definizioni:** municipal accounting perimeter; resident normalization is not beneficiaries — mission commitments 12 / exercise January 1 residents

**Fonti:** [https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/2025/2025_Rendiconto%20-%20Schemi%20di%20bilancio_TOSCANA.zip](https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/2025/2025_Rendiconto%20-%20Schemi%20di%20bilancio_TOSCANA.zip)

**Avvertenze:** gross_municipal_amounts_not_consolidated_for_interentity_transfers, mission_commitments_include_current_and_capital_not_delivered_services, municipal_accounting_perimeter_not_service_quality_or_policy_effect, nominal_finance_values_not_real_growth

**Componente della risposta**

Richiesta `dossier_primary_educationMissionExpenditurePerResident` — `compare`; esito `computed`.

**Risultati:** Camaiore 2025: 171,7 €; Forte dei Marmi 2025: 974,5 €; Massarosa 2025: 201,8 €; Pietrasanta 2025: 315,4 €; Seravezza 2025: 90,7 €; Stazzema 2025: 152,2 €; Viareggio 2025: 68,7 €

**Universi e definizioni:** municipal accounting perimeter; resident normalization is not beneficiaries — mission commitments 04 / exercise January 1 residents

**Fonti:** [https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/2025/2025_Rendiconto%20-%20Schemi%20di%20bilancio_TOSCANA.zip](https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/2025/2025_Rendiconto%20-%20Schemi%20di%20bilancio_TOSCANA.zip)

**Avvertenze:** gross_municipal_amounts_not_consolidated_for_interentity_transfers, mission_commitments_include_current_and_capital_not_delivered_services, municipal_accounting_perimeter_not_service_quality_or_policy_effect, nominal_finance_values_not_real_growth

**Componente della risposta**

Richiesta `environment_cost_current` — `compare`; esito `computed`.

**Risultati:** Massarosa 2024: 275,6 eurPerResident; Viareggio 2024: 348,2 eurPerResident

**Universi e definizioni:** municipal urban waste accounting; resident normalization is not individual consumption — official CTOTab euro per inhabitant; municipality count = 1; not household TARI

**Fonti:** [https://www.catasto-rifiuti.isprambiente.it/index.php?pg=costicomuneproc&reg1=Toscana&regid=09&regid2=09](https://www.catasto-rifiuti.isprambiente.it/index.php?pg=costicomuneproc&reg1=Toscana&regid=09&regid2=09)

**Avvertenze:** cost_benchmark_is_reported_sample_not_full_territory_cost, service_cost_not_household_tax_or_service_quality

**Componente della risposta**

Richiesta `tax_tariStandardHousehold_total_046018` — `compare`; esito `computed`.

**Risultati:** Camaiore 2025: 422,9 currency2; Massarosa 2025: 542,5 currency2

**Universi e definizioni:** one identical theoretical tax scenario per municipality — resident domestic user, 3 people / 100 square metres, no personal concessions; TEFA 5% and ARERA 7.60 euro included

**Fonti:** [https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_at/](https://www1.finanze.gov.it/finanze2/dipartimentopolitichefiscali/fiscalitalocale/nuova_at/)

**Avvertenze:** municipal_tax_arithmetic_mean_each_municipality_equal_weight, municipal_tax_not_service_quality_or_household_burden, municipal_tax_single_2025_snapshot_not_current_tax_advice, municipal_tax_source_normalized_snapshot_not_raw_document_replay, municipal_tax_standard_scenarios_not_personal_bill_or_revenue, municipal_tax_tari_stazzema_official_base_not_reconstructed_fixed_variable

#### Controlli metodologici, separati dalle domande territoriali

- Cassa, competenza e risorse vincolate raccontano lo stesso margine? I metadati distinguono flussi di competenza, incassi e stock: non autorizzano una somma come disponibilità discrezionale.
- Più spesa significa più utenti o servizi migliori? Non determinabile dai dati acquisiti: Fabbisogni/costi standard confrontabili e perimetri gestionali. Nessuna stima sostitutiva è autorizzata.

### Investimenti, PNRR e opere

**Competenze da verificare negli atti vigenti:** Ente attuatore e proprietario/gestore dell’opera da identificare per progetto; Comune: monitoraggio locale e programmazione di competenza.

**Domande A6 riusate e approfondite, non nuove certificazioni:** risorse-risultati

**Opzioni da approfondire:** Approfondire schede progetto e baseline dei risultati, senza sommare due volte spesa e finanziamento.

**Monitoraggio:** Milestone, apertura, uso, qualità e manutenzione; distinguere importi programmati, impegnati, pagati e conclusi.

#### investimenti-centrale — partially_supported

Quali investimenti sono osservati e quali risultati delle opere non sono ancora misurabili?

**Risposta oggi e interpretazione consentita:** Comporre risposte deterministiche separate, preservando periodi, universi, fonti, missing e rifiuti; nessuna fusione causale o aritmetica non autorizzata.

**Informazioni mancanti:** CUP e localizzazioni riconciliati, costi finali e cronoprogrammi; Collaudi, messa in esercizio, utenti e risultati; Avanzamento fisico, tempi, costi e collaudi per opera; Messa in esercizio, utilizzo e manutenzione; Indicatori prima/dopo e disegno di valutazione

**Valore aggiunto:** Sposta la lettura dal finanziamento al servizio effettivamente prodotto.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `pnrr_pnrrFunding_total_046018`, `pnrr_pnrrConcluded_total_046018`, `distinct_works_current`; solo contesto: `pab_pabInterventionsCompleted`, `dossier_primary_capitalExpenditureCommittedPerResident`

#### investimenti-1 — partially_supported

Quali finanziamenti e stati amministrativi delle opere sono osservabili?

**Risposta oggi e interpretazione consentita:** Descrivere finanziamenti e conclusioni amministrative nelle fotografie di monitoraggio; non attribuire importi ai risultati o ai residenti beneficiari.

**Informazioni mancanti:** Avanzamento fisico, tempi, costi e collaudi per opera

**Valore aggiunto:** Sposta la lettura dal finanziamento al servizio effettivamente prodotto.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `pnrr_pnrrFunding_total_046018` — `compare`; esito `computed`.

**Risultati:** Massarosa 2026-09-25: 273,9 currency_per_resident; Viareggio 2026-09-25: 199,3 currency_per_resident

**Universi e definizioni:** PNRR or PNRR-PNC, pure PNC excluded; municipal implementing body; globally unique id_progetto — assigned PNRR amount / resident population

**Fonti:** [https://www301.regione.toscana.it/bancadati/pnrrPerSitoWeb/getOpenData_v6.csv](https://www301.regione.toscana.it/bancadati/pnrrPerSitoWeb/getOpenData_v6.csv)

**Avvertenze:** pnrr_funding_not_paid_spent_total_cost_or_annual_flow, pnrr_municipal_implementing_body_not_all_projects_located_in_town, pnrr_numeric_rank_not_effectiveness_or_policy_priority, pnrr_old_snapshot_perTown_comparisons_not_current_catalog_values, pnrr_regis_macro_phase_5_not_completed_testing_or_service_opening, pnrr_selected_normalized_records_not_full_original_csv_replay, pnrr_snapshot_20260925_population_20260101_distinct_dates

**Componente della risposta**

Richiesta `pnrr_pnrrConcluded_total_046018` — `compare`; esito `computed`.

**Risultati:** Massarosa 2026-09-25: 90,9 %; Viareggio 2026-09-25: 75,0 %

**Universi e definizioni:** PNRR or PNRR-PNC, pure PNC excluded; municipal implementing body; globally unique id_progetto — ReGiS macro-phase 5 projects / selected projects × 100

**Fonti:** [https://www301.regione.toscana.it/bancadati/pnrrPerSitoWeb/getOpenData_v6.csv](https://www301.regione.toscana.it/bancadati/pnrrPerSitoWeb/getOpenData_v6.csv)

**Avvertenze:** pnrr_funding_not_paid_spent_total_cost_or_annual_flow, pnrr_municipal_implementing_body_not_all_projects_located_in_town, pnrr_numeric_rank_not_effectiveness_or_policy_priority, pnrr_old_snapshot_perTown_comparisons_not_current_catalog_values, pnrr_regis_macro_phase_5_not_completed_testing_or_service_opening, pnrr_selected_normalized_records_not_full_original_csv_replay, pnrr_snapshot_20260925_population_20260101_distinct_dates

**Componente della risposta**

Richiesta `distinct_works_current` — `compare`; esito `computed`.

**Risultati:** Massarosa 2026: 1.409,3 €; Viareggio 2026: 576,6 €

**Universi e definizioni:** municipal accounting or project perimeter; normalization is not beneficiaries — monitored BDAP-MOP project stock per resident; not annual spending

**Fonti:** [https://openbdap.rgs.mef.gov.it/it/FET/Analizza](https://openbdap.rgs.mef.gov.it/it/FET/Analizza)

**Avvertenze:** gross_municipal_amounts_not_consolidated_for_interentity_transfers, monitored_projects_not_annual_spend_progress_or_disjoint_cups, municipal_accounting_or_project_carrier_not_policy_effect, nominal_finance_values_not_real_growth, published_normalized_carrier_no_frozen_raw_components_or_weighting

#### investimenti-2 — not_determinable

Le opere concluse e la spesa in conto capitale producono miglioramenti misurabili?

**Risposta oggi e interpretazione consentita:** Le evidenze descrivono completamento e impegni, non effetti: occorre definire risultati e baseline per singola opera.

**Informazioni mancanti:** Messa in esercizio, utilizzo e manutenzione; Indicatori prima/dopo e disegno di valutazione

**Valore aggiunto:** Sposta la lettura dal finanziamento al servizio effettivamente prodotto.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

Nessuna richiesta del catalogo attuale misura le variabili necessarie. Le eventuali richieste seguenti sono soltanto contesto.

**Solo contesto**

Richiesta `pab_pabInterventionsCompleted` — `compare`; esito `computed`.

**Risultati:** Camaiore 2026-08-31: 150,0 number; Forte dei Marmi 2026-08-31: 13,0 number; Massarosa 2026-08-31: 1,0 number; Pietrasanta 2026-08-31: 68,0 number; Seravezza 2026-08-31: 7,0 number; Stazzema 2026-08-31: 9,0 number; Viareggio 2026-08-31: 0,0 number

**Universi e definizioni:** municipal export matched WFS cb_pmo_lineare operational features; alternative punctual representation excluded — completato operational feature counts

**Fonti:** [https://cbtoscananord.it/comunicazione/pmo-manutenzione-mappa-navigabile/](https://cbtoscananord.it/comunicazione/pmo-manutenzione-mappa-navigabile/)

**Avvertenze:** pab_activity_km_not_unique_physical_network, pab_approved_codes_not_operational_features, pab_missing_geometry_no_physical_maintenance_share, pab_operational_gross_not_approved_budget_or_paid_spending, pab_operational_share_not_approved_plan_execution_or_risk_reduction, pab_punctual_representation_not_additive, pab_status_aggregate_without_individual_id_date_replay, pab_status_snapshot_not_live_or_year_end

**Solo contesto**

Richiesta `dossier_primary_capitalExpenditureCommittedPerResident` — `compare`; esito `computed`.

**Risultati:** Camaiore 2025: 755,8 €; Forte dei Marmi 2025: 1.958,5 €; Massarosa 2025: 207,7 €; Pietrasanta 2025: 696,1 €; Seravezza 2025: 611,0 €; Stazzema 2025: 261,3 €; Viareggio 2025: 370,8 €

**Universi e definizioni:** municipal accounting perimeter; resident normalization is not beneficiaries — capital_expenditure_commitments_title_2 / exercise January 1 residents

**Fonti:** [https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/2025/2025_Rendiconto%20-%20Schemi%20di%20bilancio_TOSCANA.zip](https://openbdap.rgs.mef.gov.it/Datasets_FET/Rendiconto/2025/2025_Rendiconto%20-%20Schemi%20di%20bilancio_TOSCANA.zip)

**Avvertenze:** gross_municipal_amounts_not_consolidated_for_interentity_transfers, municipal_accounting_perimeter_not_service_quality_or_policy_effect, nominal_finance_values_not_real_growth

#### Controlli metodologici, separati dalle domande territoriali

- Comune attuatore e localizzazione dell’opera coincidono? I risultati selezionati descrivono il contesto; CUP e localizzazioni riconciliati, costi finali e cronoprogrammi impedisce di rispondere integralmente alla domanda.
- Macro-fase conclusa prova apertura o beneficio del servizio? Non determinabile dai dati acquisiti: Collaudi, messa in esercizio, utenti e risultati. Nessuna stima sostitutiva è autorizzata.

### Capacità amministrativa e digitale

**Competenze da verificare negli atti vigenti:** Comune: organizzazione e servizi locali; gestioni associate/fornitori nei rispettivi contratti, senza attribuire automaticamente responsabilità dai tassi.

**Domande A6 riusate e approfondite, non nuove certificazioni:** risorse-risultati

**Opzioni da approfondire:** Approfondire semplificazione e accesso assistito prima di dedurre fabbisogni di organico.

**Monitoraggio:** Tempi, completamenti, errori e soddisfazione per servizio; stock del personale come contesto.

#### capacita-centrale — partially_supported

Quali condizioni organizzative aiutano a rendere accessibili i servizi pubblici?

**Risposta oggi e interpretazione consentita:** Comporre risposte deterministiche separate, preservando periodi, universi, fonti, missing e rifiuti; nessuna fusione causale o aritmetica non autorizzata.

**Informazioni mancanti:** Carichi per funzione, tempi, competenze e gestione associata; Utenti, completamenti, abbandoni e barriere digitali; Carichi, competenze e tempi dei procedimenti; Reclutamento e uscite per funzione; Utenti, abbandoni, assistenza e accessibilità; Tempi/esiti delle pratiche e copertura effettiva

**Valore aggiunto:** Collega risorse organizzative e esperienza del cittadino senza assimilare personale a produttività.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `rgs_municipalEmployeesPer1000_total`, `rgs_municipalStaffAgeStructure_total`, `rgs_municipalStaffTurnover_total`, `regional_municipalOnlineServicesAdvanced_current`, `connectivity_ftthCoverageDesi_046005`

#### capacita-1 — partially_supported

Dotazione, età e ricambio del personale segnalano capacità amministrative da approfondire?

**Risposta oggi e interpretazione consentita:** Descrivere dotazione e struttura del personale solo nei periodi acquisiti; non dedurre produttività o qualità del lavoro.

**Informazioni mancanti:** Carichi, competenze e tempi dei procedimenti; Reclutamento e uscite per funzione

**Valore aggiunto:** Collega risorse organizzative e esperienza del cittadino senza assimilare personale a produttività.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `rgs_municipalEmployeesPer1000_total` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 5,9 per1000; Forte dei Marmi 2024: 20,4 per1000; Massarosa 2024: 4,0 per1000; Pietrasanta 2024: 7,4 per1000; Seravezza 2024: 5,1 per1000; Stazzema 2024: 4,5 per1000; Viareggio 2024: 6,8 per1000

**Universi e definizioni:** employees of distinct municipal employers; unions excluded — municipal employer staff 31 December 2024 / residents 1 January 2024 × 1000

**Fonti:** [https://bdap-opendata.rgs.mef.gov.it/export/csv/2024---Dipendenti-Pubblici---Occupazione-e-Turnover---Dati-analitici-per-Ente.csv](https://bdap-opendata.rgs.mef.gov.it/export/csv/2024---Dipendenti-Pubblici---Occupazione-e-Turnover---Dati-analitici-per-Ente.csv)

**Avvertenze:** rgs_frozen_extraction_not_new_live_acquisition, rgs_numerical_rank_not_administrative_quality, rgs_outsourcing_and_joint_services_affect_staffing, rgs_stock_2024_december_population_2024_january_distinct

**Componente della risposta**

Richiesta `rgs_municipalStaffAgeStructure_total` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 40,4 %; Forte dei Marmi 2024: 47,8 %; Massarosa 2024: 44,8 %; Pietrasanta 2024: 38,7 %; Seravezza 2024: 36,5 %; Stazzema 2024: 30,8 %; Viareggio 2024: 36,4 %

**Universi e definizioni:** employees of distinct municipal employers; unions excluded — RGS age band age55plus / total municipal employer staff × 100; no midpoint mean age

**Fonti:** [https://bdap-opendata.rgs.mef.gov.it/export/csv/2024---Dipendenti-Pubblici---Anzianita---Dati-analitici-per-Ente.csv](https://bdap-opendata.rgs.mef.gov.it/export/csv/2024---Dipendenti-Pubblici---Anzianita---Dati-analitici-per-Ente.csv)

**Avvertenze:** rgs_age_classes_not_mean_age_or_staff_quality, rgs_frozen_extraction_not_new_live_acquisition, rgs_numerical_rank_not_administrative_quality

**Componente della risposta**

Richiesta `rgs_municipalStaffTurnover_total` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: -1,1 %; Forte dei Marmi 2024: -2,9 %; Massarosa 2024: -1,1 %; Pietrasanta 2024: 0,6 %; Seravezza 2024: 0,0 %; Stazzema 2024: -7,7 %; Viareggio 2024: 4,6 %

**Universi e definizioni:** employees of distinct municipal employers; unions excluded — net hires minus net cessations, excluding inter-administration transfers, / end-year staff × 100

**Fonti:** [https://bdap-opendata.rgs.mef.gov.it/export/csv/2024---Dipendenti-Pubblici---Occupazione-e-Turnover---Dati-analitici-per-Ente.csv](https://bdap-opendata.rgs.mef.gov.it/export/csv/2024---Dipendenti-Pubblici---Occupazione-e-Turnover---Dati-analitici-per-Ente.csv)

**Avvertenze:** rgs_frozen_extraction_not_new_live_acquisition, rgs_numerical_rank_not_administrative_quality, rgs_small_staff_one_person_large_percentage, rgs_transfers_excluded_net_flows_not_gross_hiring

#### capacita-2 — partially_supported

Quali offerte digitali e condizioni di connettività sono osservabili, e che cosa manca per verificarne l’accessibilità?

**Risposta oggi e interpretazione consentita:** Affiancare livello dei servizi online e copertura FTTH nello snapshot proprio. Sono condizioni di offerta: non misurano utilizzo, inclusione o riduzione dei tempi.

**Informazioni mancanti:** Utenti, abbandoni, assistenza e accessibilità; Tempi/esiti delle pratiche e copertura effettiva

**Valore aggiunto:** Collega risorse organizzative e esperienza del cittadino senza assimilare personale a produttività.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `regional_municipalOnlineServicesAdvanced_current` — `compare`; esito `computed`.

**Risultati:** Camaiore 2022: 75,0 %; Massarosa 2022: 33,3 %

**Universi e definizioni:** services offered by each municipality in Istat ICT local public administration survey; levels 3 and 4 — services offered online at levels 3 or 4 / relevant offered services in survey × 100

**Fonti:** [https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali](https://www.regione.toscana.it/it/statistiche/indicatori-comunali-per-le-politiche-locali)

**Avvertenze:** regional_historical_release_continuity_not_attested, regional_municipal_summary_not_official_versilia, regional_no_reverse_derived_counts_or_population_weights, regional_online_basket_24_to_27_not_homogeneous, regional_online_effective_2022_not_release_2024, regional_published_values_no_native_counts_or_joint_distribution

**Componente della risposta**

Richiesta `connectivity_ftthCoverageDesi_046005` — `compare`; esito `computed`.

**Risultati:** Camaiore 2026-07-06: 91,3 %; Massarosa 2026-07-06: 47,0 %

**Universi e definizioni:** AGCOM resident households; declared network availability, not active contracts — copertura_ftth_desi_pct

**Fonti:** [https://geo.agcom.it/arcgis/sharing/rest/content/items/25830559c5784c1eb5eb1cf748889f4c/data](https://geo.agcom.it/arcgis/sharing/rest/content/items/25830559c5784c1eb5eb1cf748889f4c/data)

**Avvertenze:** connectivity_declared_network_not_subscriptions_speed_or_civic_activation, connectivity_no_automatic_causal_or_policy_priority_claim, connectivity_official_reference_2026_correction_not_new_acquisition, connectivity_percentages_and_counts_independent_no_reverse_derivation, connectivity_public_aggregate_weights_rounded_percentages_not_native_count_ratio

#### Controlli metodologici, separati dalle domande territoriali

- Quantità e formazione del personale descrivono capacità per funzione? I risultati selezionati descrivono il contesto; Carichi per funzione, tempi, competenze e gestione associata impedisce di rispondere integralmente alla domanda.
- Disponibilità online significa uso, accessibilità e completamento? Non determinabile dai dati acquisiti: Utenti, completamenti, abbandoni e barriere digitali. Nessuna stima sostitutiva è autorizzata.

### Partecipazione, cultura e vita quotidiana

**Competenze da verificare negli atti vigenti:** Comune: servizi culturali e spazi di competenza; enti culturali/terzo settore e comunità come interlocutori, non campione automaticamente rappresentativo.

**Domande A6 riusate e approfondite, non nuove certificazioni:** risorse-risultati

**Opzioni da approfondire:** Approfondire accesso a biblioteche, spazi e consultazioni senza dedurre consenso politico dai servizi.

**Monitoraggio:** Accessi e partecipazione per platea, barriere e qualità percepita; non aggregare quesiti o enti condivisi impropriamente.

#### partecipazione-centrale — partially_supported

Quali forme di partecipazione e accesso culturale sono osservabili?

**Risposta oggi e interpretazione consentita:** Comporre risposte deterministiche separate, preservando periodi, universi, fonti, missing e rifiuti; nessuna fusione causale o aritmetica non autorizzata.

**Informazioni mancanti:** Partecipazione non elettorale, accesso e barriere; Qualità percepita, uso degli spazi e copertura di gruppi; Partecipazione a processi e barriere di accesso; Condizioni di vita e domanda culturale; Attività e beneficiari, tariffe e accessibilità; Indagini imparziali sulla soddisfazione e inclusione

**Valore aggiunto:** Distingue uso, partecipazione e qualità della vita senza un indice politico sintetico.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Piano centrale, dettagliato nelle domande seguenti:** `turnout_total_046018`, `library_libraryLoansPerResident_current`, `runts_total_046018`, `library_libraryWeeklyOpeningHours_current`

#### partecipazione-1 — partially_supported

Quali segnali di partecipazione elettorale e accesso alla cultura sono osservabili?

**Risposta oggi e interpretazione consentita:** Tenere separati consultazioni e corpi elettorali da prestiti bibliotecari e utenti; non sintetizzare qualità della vita in un punteggio.

**Informazioni mancanti:** Partecipazione a processi e barriere di accesso; Condizioni di vita e domanda culturale

**Valore aggiunto:** Distingue uso, partecipazione e qualità della vita senza un indice politico sintetico.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `turnout_total_046018` — `compare`; esito `computed`.

**Risultati:** Camaiore referendum-20260322-q1: 62,6 %; Massarosa referendum-20260322-q1: 62,7 %

**Universi e definizioni:** referendum electorate registered for selected consultation; all sexes — voters / registered electors × 100; same consultation, question and sex

**Fonti:** [https://elezionistorico.interno.gov.it/eligendo/opendata.php](https://elezionistorico.interno.gov.it/eligendo/opendata.php)

**Avvertenze:** turnout_electors_not_resident_population_or_valid_votes, turnout_irregular_history_not_annual_series_or_continuity_attestation, turnout_municipal_latest_different_dates_and_province_context_excluded, turnout_normalized_archive_replay_not_original_DAIT_files, turnout_numerical_rank_not_civic_quality_or_policy_priority, turnout_same_consultation_question_and_electoral_universe_required, turnout_sex_only_when_both_native_components_complete_no_imputation

**Componente della risposta**

Richiesta `library_libraryLoansPerResident_current` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 0,2 decimal; Forte dei Marmi 2024: 0,9 decimal; Massarosa 2024: non disponibile decimal; Pietrasanta 2024: 0,2 decimal; Seravezza 2024: 0,2 decimal; Stazzema 2024: non disponibile decimal; Viareggio 2024: 0,1 decimal

**Universi e definizioni:** municipal public library services included in regional annual monitoring — Indice di prestito Comunale

**Fonti:** [https://dati.toscana.it/dataset/rt-monit-bibi-ente-locale](https://dati.toscana.it/dataset/rt-monit-bibi-ente-locale)

**Avvertenze:** library_available_municipal_mean_not_official_versilia, library_current_coverage_5_of_7_no_imputation_or_last_value_carry, library_historical_release_continuity_not_reviewed, library_loans_are_transactions_not_unique_readers, library_pandemic_2020_context_not_automatic_anomaly, library_published_rounded_indices_not_reconstructed_native_ratios, partial_coverage

#### partecipazione-2 — partially_supported

La rete civica e l’apertura dei servizi culturali bastano a descrivere la vita comunitaria?

**Risposta oggi e interpretazione consentita:** Sedi legali e orari descrivono risorse potenziali; non misurano attività, beneficiari o soddisfazione.

**Informazioni mancanti:** Attività e beneficiari, tariffe e accessibilità; Indagini imparziali sulla soddisfazione e inclusione

**Valore aggiunto:** Distingue uso, partecipazione e qualità della vita senza un indice politico sintetico.

Associazione descrittiva e contesto non provano causalità o effetto di politica. Nessuna inferenza individuale da dati aggregati.

**Componente della risposta**

Richiesta `runts_total_046018` — `compare`; esito `computed`.

**Risultati:** Camaiore 2026-10-11: 2,7 per1000; Massarosa 2026-10-11: 2,4 per1000

**Universi e definizioni:** RUNTS entities assigned once by current legal municipality, all registered sections — registered entities by legal seat / resident population × 1000

**Fonti:** [https://servizi.lavoro.gov.it/runts/it-it/Lista-enti](https://servizi.lavoro.gov.it/runts/it-it/Lista-enti)

**Avvertenze:** third_sector_all_registered_sections_not_all_local_associations, third_sector_legal_seat_not_activity_services_or_volunteer_count, third_sector_no_reconstructed_2025_history_or_seat_transfers, third_sector_normalized_snapshot_not_original_excel_entity_replay, third_sector_numeric_rank_not_quality_or_policy_priority, third_sector_register_20261011_population_20260101_distinct_dates

**Componente della risposta**

Richiesta `library_libraryWeeklyOpeningHours_current` — `compare`; esito `computed`.

**Risultati:** Camaiore 2024: 56,0 hours; Forte dei Marmi 2024: 62,0 hours; Massarosa 2024: non disponibile hours; Pietrasanta 2024: 48,0 hours; Seravezza 2024: 40,6 hours; Stazzema 2024: non disponibile hours; Viareggio 2024: 63,8 hours

**Universi e definizioni:** municipal public library services included in regional annual monitoring — Ore medie di apertura settimanale Comunale

**Fonti:** [https://dati.toscana.it/dataset/rt-monit-bibi-ente-locale](https://dati.toscana.it/dataset/rt-monit-bibi-ente-locale)

**Avvertenze:** library_available_municipal_mean_not_official_versilia, library_current_coverage_5_of_7_no_imputation_or_last_value_carry, library_historical_release_continuity_not_reviewed, library_hours_history_starts_2022_no_pre2022_substitution, library_pandemic_2020_context_not_automatic_anomaly, library_published_rounded_indices_not_reconstructed_native_ratios, library_weekly_hours_not_opening_index_or_annual_hours, partial_coverage

#### Controlli metodologici, separati dalle domande territoriali

- Affluenza a consultazioni diverse è una stessa serie? No: il periodo è un identificativo di consultazione/quesito; elezioni e referendum diversi non costituiscono automaticamente una serie omogenea.
- Sedi di enti e prestiti rappresentano inclusione o benessere? Non determinabile dai dati acquisiti: Qualità percepita, uso degli spazi e copertura di gruppi. Nessuna stima sostitutiva è autorizzata.
