// Public wording and layout only. The original reader, answer and export stay intact.
import {loadEducation,presentEducation} from './education.mjs';
let sourceCommit, education;
const node=(tag,text,className)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;};
const list=items=>{const ul=node('ul');for(const item of items)ul.append(node('li',item));return ul;};
const fold=(title,child,technical=false)=>{const el=node('details');if(technical)el.dataset.a7Technical='true';el.append(node('summary',title),child);return el;};
const introductions={
 'lavoro-centrale':'Vivere e lavorare a Massarosa: due prospettive per leggere il cambiamento. Il confronto con Viareggio affianca l’occupazione dei residenti, le attività economiche e gli addetti presenti sul territorio.',
 'lavoro-1':'Che cosa cambia tra Massarosa e Viareggio? Guardiamo quante persone lavorano fra i residenti e come sono cambiate le unità locali: ogni confronto mantiene il proprio periodo di riferimento.',
 'lavoro-2':'Industria e servizi raccontano due volti dell’economia di Massarosa. I grafici affiancano valore aggiunto e retribuzioni nell’industria e mostrano i due anni disponibili per i servizi.',
 'infanzia-centrale':'Dai primi anni di vita alla scuola: come si presenta la rete dei servizi? Partiamo dalla capacità dei servizi educativi, dagli alunni e dalle classi per mettere a fuoco la situazione di Massarosa.',
 'infanzia-1':'Quale capacità offrono i servizi per la prima infanzia rispetto ai bambini residenti? Il confronto fra i Comuni aiuta a leggere differenze e dotazioni potenziali.',
 'infanzia-2':'Una scuola è fatta di alunni, tempo, spazi e opportunità. Affianchiamo dimensione delle classi, tempo pieno e caratteristiche degli edifici; i risultati educativi restano una prospettiva distinta.',
 'abitazione-centrale':'Quanto costa la casa e chi rischia di restarne escluso? Mettiamo insieme prezzi e affitti delle zone OMI, redditi dichiarati, case non abitate e morosità nelle case popolari: ognuno racconta un pezzo diverso del problema.',
 'abitazione-1':'Comprare o affittare a Massarosa e a Viareggio: quanto costa al metro quadro e che redditi dichiarano i contribuenti? Due informazioni da leggere affiancate, non da dividere fra loro.',
 'abitazione-2':'Ci sono case vuote e case popolari con difficoltà di pagamento: possono indicare dove agire? Vediamo quante abitazioni non sono abitate da residenti e come cambia la morosità ERP.',
 'anziani-centrale':'Una popolazione che invecchia chiede più cura. Guardiamo quanti sono i grandi anziani, chi è assistito a casa, chi vive da solo, le persone seguite per demenza e la spesa sociale.',
 'anziani-1':'Massarosa e Viareggio a confronto: quanti residenti hanno più di 85 anni e quanti anziani ricevono assistenza a domicilio.',
 'anziani-2':'Vivere soli, la demenza, la spesa per i servizi sociali: tre segnali da leggere insieme per capire dove serve più attenzione.',
 'redditi-centrale':'Quali segnali economici meritano attenzione? Guardiamo come si distribuiscono i redditi dichiarati, da dove provengono, come è cambiato il loro potere d’acquisto e quanto pesano le pensioni.',
 'redditi-1':'Quanti contribuenti stanno nelle fasce di reddito più basse e da che cosa vivono? Distribuzione per fasce e tipo di reddito dichiarato.',
 'redditi-2':'I redditi sono cresciuti più o meno dei prezzi? E quanto pesano le pensioni sul reddito complessivo dichiarato?',
 'turismo-centrale':'Il turismo cambia il territorio durante l’anno. Vediamo presenze, stagionalità, posti letto e, accanto, acqua e rifiuti: i servizi che sentono di più il peso dei visitatori.',
 'turismo-1':'Quando arrivano i turisti e quanti posti letto ci sono? Presenze negli anni, mesi di maggiore concentrazione e ricettività per residente.',
 'turismo-2':'Acqua e rifiuti crescono dove il turismo è più intenso? Affianchiamo i dati, senza attribuire al turismo una quota precisa.',
 'mobilita-centrale':'Come ci si sposta per lavoro e che cosa offre il trasporto pubblico? Guardiamo pendolari, chi lavora fuori Comune, corse di autobus programmate, incidenti stradali e percorsi per la mobilità lenta.',
 'mobilita-1':'Quanti residenti lavorano fuori dal proprio Comune e quante corse di autobus sono programmate? Due fotografie da leggere affiancate.',
 'mobilita-2':'Incidenti stradali e percorsi a piedi o in bicicletta: dove servono verifiche sulla sicurezza e sulla mobilità lenta?'
};
const boundaries={
 'redditi-centrale':'Ogni dato resta con il proprio anno e la propria platea. I redditi dichiarati non sono il reddito disponibile delle famiglie e non misurano la povertà.',
 'turismo-centrale':'Ogni dato resta con il proprio anno. Acqua e rifiuti dipendono anche dai residenti: il confronto non dice quanto pesi il turismo.',
 'abitazione-centrale':'Prezzi e affitti OMI sono valori di riferimento, non contratti reali. Non calcoliamo quanto una famiglia spende per la casa: mancano redditi familiari e affitti effettivi.',
 'abitazione-1':'Quotazioni OMI e redditi dichiarati vanno letti separatamente: non si ricava quanto pesi l’affitto su una famiglia.',
 'abitazione-2':'Una casa non abitata da residenti non è per forza disponibile: può essere seconda casa o affitto turistico.',
 'anziani-centrale':'Ogni segnale ha una sua platea e un suo anno. Messi insieme non dicono quante persone hanno bisogno di cura né se il bisogno è coperto.',
 'anziani-1':'Quota di grandi anziani e assistenza domiciliare si riferiscono ad anni e gruppi diversi: non si calcola una «copertura».',
 'anziani-2':'Sono segnali distinti: combinarli non permette di contare le persone fragili.',
 'redditi-1':'Si descrivono i redditi imponibili dichiarati, non la povertà delle famiglie.',
 'redditi-2':'Il potere d’acquisto usa l’inflazione nazionale. Il peso delle pensioni è una quota di reddito, non il numero di pensionati.',
 'mobilita-centrale':'I dati sul pendolarismo sono del censimento 2021; le corse di autobus sono quelle programmate, non i passeggeri né la puntualità.',
 'mobilita-1':'Non si stima quante persone usano l’autobus: pendolarismo e offerta sono due fotografie separate.',
 'mobilita-2':'Il numero di percorsi non dice se sono sicuri o continui.',
 'turismo-1':'Si contano i pernottamenti registrati, non gli escursionisti in giornata né le presenze giorno per giorno.',
 'turismo-2':'Ogni dato ha il suo anno. Non si attribuisce al turismo una parte dei consumi o dei costi.'
};
const headings={lavoro:'Lavoro e attività: le due facce del territorio',infanzia:'Bambini, servizi e scuole: il territorio a confronto',abitazione:'Casa: prezzi, affitti e abitazioni',anziani:'Anziani: bisogni e assistenza',redditi:'Redditi: come si distribuiscono e cosa comprano',turismo:'Turismo e servizi del territorio',mobilita:'Spostamenti e collegamenti'};
const populations={
 'resident population; 25–64 total residents':'Residenti tra 25 e 64 anni.',
 'ASIA active local units; annual average employment at workplace; ASIA total':'Unità locali attive e addetti localizzati nel territorio (ASIA). Gli addetti sono una media annua e possono risiedere altrove.',
 'Frame SBS local units of industry and services; industry':'Unità locali dell’industria rilevate da ISTAT (Frame SBS).',
 'Frame SBS local units of industry and services; services':'Unità locali dei servizi rilevate da ISTAT (Frame SBS).',
 'resident children aged 3–36 months':'Bambini residenti tra 3 e 36 mesi; la capacità è potenziale, non misura le presenze effettive.',
 'tested students by municipality of school location, official Totale aggregation':'Alunni che hanno svolto le prove, attribuiti al Comune della scuola, non a quello di residenza.',
 'unique MIM school buildings; accessibilita defined responses, or all responses for undefined share':'Edifici scolastici censiti dal Ministero: la quota di accessibilità considera le risposte definite, non quelle mancanti.',
 'pupils in state and private schools located in the municipality; not resident children':'Alunni nelle scuole statali e paritarie del Comune; possono risiedere in altri Comuni.',
 'ARS dementia source reference universe; age totale; sex totale':'Persone seguite per demenza secondo l’Agenzia regionale di sanità, tutte le età.',
 'ARS elderly resident reference population totale':'Anziani residenti assistiti a domicilio, in rapporto alla popolazione anziana.',
 'ERP Lucca municipal cumulative billed amounts for rent and ancillary expenses':'Canoni e spese delle case popolari fatturati e non pagati, cumulati negli anni.',
 'Istat hotel and non-hotel capacity 2024; private non-business accommodation expansion 2025 excluded':'Posti letto in alberghi e altre strutture ricettive (2024).',
 'MEF municipal declarants with taxable income; changing yearly populations, not a household cohort':'Contribuenti con reddito imponibile; il gruppo cambia di anno in anno.',
 'annual average resident population; incidents localized to municipality':'Incidenti avvenuti nel Comune, in rapporto ai residenti.',
 'censused homes including non-resident occupation':'Abitazioni censite, comprese quelle non abitate da residenti.',
 'displayed residential OMI zones; civil dwellings, normal state, public reference selection':'Quotazioni medie delle zone residenziali OMI per abitazioni civili in stato normale.',
 'known class frequencies only':'Contribuenti nelle fasce di reddito disponibili.',
 'municipal declared income amounts':'Redditi dichiarati nel Comune.',
 'municipal distribution network water volumes':'Acqua immessa nella rete di distribuzione del Comune.',
 'municipal fiscal records; selected income-source declarants':'Contribuenti per tipo di reddito dichiarato.',
 'municipal scheduled trip memberships':'Corse di autobus programmate che servono il Comune.',
 'municipal social expenditure by Istat user-area perimeter, including early childhood':'Spesa del Comune per servizi sociali, compresi i servizi per la prima infanzia.',
 'municipal urban waste accounting; resident normalization is not individual consumption':'Rifiuti urbani del Comune divisi per i residenti; non è la produzione di ciascuna persona.',
 'public A0/B1 route records with frozen municipal membership':'Percorsi pubblici (escursionistici, ciclabili, cammini) che attraversano il Comune.',
 'recorded tourist overnight stays in reporting accommodation establishments':'Pernottamenti registrati nelle strutture ricettive.',
 'registered accommodation movement net of rentals; foreign means residence abroad, not citizenship':'Arrivi e presenze nelle strutture ricettive, esclusi gli affitti brevi; «straniero» significa residente all’estero.',
 'resident employed persons in the published census indicator; not work-matrix daily commuters':'Residenti occupati che lavorano fuori dal proprio Comune (censimento).',
 'resident habitual work commuters':'Residenti che si spostano abitualmente per lavoro.',
 'resident households':'Famiglie residenti.',
 'resident population':'Popolazione residente.',
 'resident population at January 1':'Popolazione residente al 1° gennaio.'
};
const warnings={
 classes_not_buildings_or_sites:'Il dato riguarda le classi, non il numero di edifici o sedi scolastiche.',
 cross_boundary_use_waiting_lists_and_quality_not_measured:'Spostamenti tra Comuni, liste d’attesa e qualità del servizio non sono misurati.',
 cumulative_baseline_change_not_year_on_year:'La variazione riguarda l’intero intervallo indicato, non il solo ultimo anno.',
 declared_building_attributes_not_certification_quality_capacity_or_pupil_access:'Le caratteristiche dichiarate degli edifici non certificano qualità, capacità o accessibilità effettiva per ogni alunno.',
 disjoint_populations_must_be_attested:'Un totale è ammissibile soltanto per gruppi che non si sovrappongono.',
 frame_and_asia_universes_differ:'Frame SBS e ASIA hanno perimetri differenti: non vanno trattati come una fonte unica.',
 frame_value_added_not_municipal_gdp:'Il valore aggiunto delle unità locali non è il PIL del Comune.',
 frozen_derived_components_no_implicit_weighting:'Le componenti provengono dai dati conservati; non si ricostruiscono pesi mancanti.',
 full_time_classification_not_service_quality_or_parental_employment_effect:'Il tempo pieno non misura la qualità del servizio né il suo effetto sull’occupazione dei genitori.',
 invalsi_2019_20_tests_not_conducted_gap_preserved:'Le prove INVALSI non si sono svolte nell’anno scolastico 2019/20; quel vuoto non viene colmato.',
 invalsi_aggregation_totale_same_grade_subject_academic_year:'Il confronto INVALSI mantiene uguali grado, materia, anno scolastico e aggregazione ufficiale.',
 invalsi_comune_plesso_not_student_residence:'Il territorio è quello della scuola, non la residenza degli alunni.',
 invalsi_missing_or_suppressed_cells_not_zero_or_absence_of_schools:'I valori mancanti o non pubblicati non significano zero né assenza di scuole.',
 invalsi_numeric_rank_not_school_quality_or_policy_priority:'L’ordine dei valori non è una graduatoria della qualità delle scuole o delle priorità amministrative.',
 invalsi_participation_and_coverage_percentages_not_valid_student_denominators:'Le percentuali di partecipazione e copertura non consentono di ricostruire il numero degli alunni.',
 invalsi_published_precision_retained_no_versilia_mean:'Si conserva la precisione pubblicata, senza ricostruire una media della Versilia.',
 located_school_pupils_not_resident_children_or_service_coverage:'Gli iscritti nelle scuole del Comune non coincidono con i bambini residenti né misurano la copertura dei servizi.',
 nominal_economic_values_not_real_growth:'Gli importi sono nominali: la variazione non misura la crescita reale al netto dell’inflazione.',
 official_rounded_measure_preserved_no_implicit_weighting:'Si conserva il valore arrotondato pubblicato, senza ricostruire pesi non disponibili.',
 partial_coverage:'Non sono disponibili tutti i dati richiesti per il confronto.',
 potential_capacity_not_attendance_or_access:'La capacità potenziale non misura frequenza effettiva o accesso delle famiglie.',
 published_rounding_preserved_no_implicit_weighting:'Gli arrotondamenti pubblicati restano invariati; non si introducono pesi mancanti.',
 resident_employment_not_workplace_jobs:'Si misura l’occupazione dei residenti, non i posti di lavoro localizzati nel Comune.',
 response_denominator_varies_by_field:'La base di calcolo cambia secondo la caratteristica rilevata: va letta insieme al singolo dato.',
 school_year_not_calendar_year:'L’anno scolastico è distinto dall’anno solare.',
 undefined_responses_not_no_or_zero:'Una risposta non definita non equivale a un no o a uno zero.',
 workplace_activity_not_resident_employment:'L’attività economica localizzata non misura direttamente l’occupazione dei residenti.',
 administrative_detection_not_total_population_need:'Il dato conta i casi registrati dai servizi, non tutto il bisogno reale della popolazione.',
 care_delivery_not_unmet_need_or_quality:'Le prestazioni erogate non misurano il bisogno non coperto né la qualità.',
 commuting_counts_and_ratios_share_components_and_population_size:'Conteggi e tassi del pendolarismo condividono le stesse componenti e la dimensione del Comune.',
 commuting_is_not_transport_mode_capacity_quality_or_causal_policy_effect:'Il pendolarismo non indica mezzo di trasporto, capacità, qualità né effetto delle politiche.',
 erp_2022_header_mismatch_2023_printed_percentages_not_used:'Le percentuali stampate nel documento 2023 non sono usate per un’incongruenza nelle intestazioni.',
 erp_cumulative_accounting_not_annual_unpaid_rent_or_household_share:'La morosità è cumulata negli anni: non è l’affitto non pagato nell’anno né la quota di famiglie.',
 erp_massarosa_2023_issued_discontinuity_retained_no_interpolation:'La discontinuità di Massarosa nel 2023 è mantenuta, senza stime intermedie.',
 erp_no_automatic_causal_quality_or_policy_priority_inference:'I dati sull’edilizia pubblica non indicano cause, qualità né priorità.',
 erp_snapshot_reconciled_original_balance_sheet_pdfs_not_replayed:'I dati sono verificati sul riepilogo, non ricontrollati sui bilanci originali.',
 gross_municipal_flows_include_moves_within_selected_group:'I flussi lordi includono anche gli spostamenti fra i Comuni selezionati.',
 habitual_work_commuters_not_all_daily_trips_or_jobs:'Sono i pendolari abituali per lavoro, non tutti gli spostamenti quotidiani né tutti i posti di lavoro.',
 health_indicator_not_cause_or_policy_priority:'L’indicatore di salute descrive una situazione: non ne spiega le cause e non indica priorità.',
 mef_bands_not_current_tax_brackets:'Le fasce di reddito sono statistiche, non gli scaglioni fiscali attuali.',
 mef_frozen_extraction_not_new_live_acquisition:'I dati MEF sono un’estrazione fissata a una data, non un aggiornamento in tempo reale.',
 mef_income_source_frequencies_overlap_do_not_sum_people:'Una persona può avere più fonti di reddito: i conteggi non si sommano.',
 mef_macro_known_cells_denominator_differs_from_eight_band_total_denominator:'Le macro-fasce usano una base diversa dal totale delle otto fasce.',
 mef_missing_band_cells_not_zero_or_redistributed:'Una fascia mancante non è zero e non viene redistribuita.',
 mef_nominal_declared_income_not_disposable_income:'È il reddito dichiarato in valori nominali, non il reddito disponibile.',
 municipal_marginals_do_not_identify_origin_destination_pairs:'I totali comunali non dicono da dove a dove ci si sposta.',
 non_resident_occupied_homes_are_not_necessarily_vacant:'Le case non occupate da residenti non sono necessariamente vuote.',
 omi_municipal_mean_is_unweighted_mean_of_displayed_zones_not_official_municipal_omi_mean:'La media comunale è la media semplice delle zone OMI, non un valore ufficiale dell’Agenzia.',
 omi_numerical_rank_not_affordability_or_policy_priority:'L’ordine numerico non misura quanto le case siano accessibili né indica priorità.',
 omi_public_zone_values_replayed_original_omi_ranges_and_files_not_frozen:'Si usano i valori pubblicati per zona, non gli intervalli e i file originali dell’OMI.',
 omi_reference_quotations_not_transaction_prices_or_registered_rents:'Le quotazioni OMI sono valori di riferimento, non prezzi di vendita reali né affitti registrati.',
 omi_sale_euro_per_m2_and_rent_euro_per_m2_per_month_are_distinct:'Vendita (€/m²) e affitto (€/m² al mese) sono misure diverse.',
 omi_second_semester_2025_not_current_2026_or_full_year_average:'Le quotazioni sono del secondo semestre 2025, non di oggi né una media annua.',
 omi_versilia_mean_of_seven_municipal_means_not_transaction_or_dwelling_weighted:'La media della Versilia è la media dei sette Comuni, non pesata su compravendite o abitazioni.',
 omi_zone_codes_are_local_to_each_municipality_not_comparable_neighbourhoods:'Le zone OMI sono definite Comune per Comune e non sono quartieri confrontabili.',
 outside_2021_reference_not_current_daily_travel_or_study_mobility:'Il dato è del 2021 e riguarda solo il lavoro, non lo studio né gli spostamenti di oggi.',
 outside_census_resident_worker_share_not_work_matrix_commuter_universe:'La quota di lavoratori fuori Comune viene dal censimento, diverso dai dati sul pendolarismo.',
 outside_municipality_census_share_not_complement_of_work_matrix_retention:'La quota di chi lavora fuori Comune non è il complemento dell’autocontenimento.',
 outside_native_numerator_denominator_not_frozen_no_count_reconstruction:'Non si ricostruiscono i conteggi di partenza.',
 outside_not_complement_of_matrix_self_containment:'Non è il complemento dell’autocontenimento del lavoro.',
 outside_numerical_rank_not_transport_need_or_policy_priority:'L’ordine numerico non misura il bisogno di trasporto né indica priorità.',
 outside_public_catalog_replay_not_original_census_records:'I dati derivano dal catalogo pubblicato, non dai dati originali del censimento.',
 outside_seven_town_simple_mean_not_versilia_worker_share:'La media semplice dei sette Comuni non è la quota della Versilia.',
 outside_work_in_other_municipality_not_outside_versilia:'Lavorare in un altro Comune non significa lavorare fuori dalla Versilia.',
 pooled_same_municipality_retention_not_retention_within_selected_group:'Chi lavora nel proprio Comune non coincide con chi lavora dentro il gruppo selezionato.',
 ratio_from_exact_components_published_share_rounded_to_one_decimal:'Il rapporto è calcolato dai valori esatti; la quota pubblicata è arrotondata a un decimale.',
 real_income_cumulative_2016_baseline_not_annual_growth:'La variazione è rispetto al 2016, non annua.',
 real_income_intermediate_history_catalog_only_native_endpoint_panels_2016_2024:'Il confronto ufficiale riguarda il 2016 e il 2024; gli anni intermedi sono indicativi.',
 real_income_national_nic_not_local_prices_or_individual_purchasing_power:'L’inflazione usata è quella nazionale, non i prezzi locali né il potere d’acquisto individuale.',
 real_income_normalized_panels_reconciled_original_archives_not_replayed:'I dati derivano da copie normalizzate e verificate, non dai file originali.',
 real_income_numerical_rank_not_quality_or_causal_inference:'L’ordine numerico non misura qualità né indica cause.',
 real_income_taxable_mean_not_disposable_household_income:'È il reddito imponibile medio, non il reddito disponibile delle famiglie.',
 road_accident_location_not_injured_residence_or_resident_risk:'Gli incidenti sono attribuiti al luogo dove avvengono, non alla residenza dei feriti.',
 road_mortality_and_injury_indices_per100_incidents_not_population_percentages:'Mortalità e lesività sono calcolate ogni 100 incidenti, non sulla popolazione.',
 road_municipal_mean_not_pooled_versilia_rate:'La media dei Comuni non è il tasso complessivo della Versilia.',
 road_published_rates_no_reverse_derived_counts_or_denominators:'Si usano i tassi pubblicati, senza ricostruire conteggi o basi.',
 road_temporal_continuity_and_pairs_not_reviewed:'La continuità nel tempo dei dati stradali non è stata verificata.',
 road_traffic_tourism_and_small_counts_preclude_automatic_policy_ranking:'Traffico, turismo e numeri piccoli impediscono classifiche automatiche fra Comuni.',
 seasonality_annual_measure_not_monthly_time_series:'La stagionalità è una misura annuale, non una serie mensile.',
 seasonality_concentration_not_volume_quality_or_policy_priority:'La concentrazione stagionale non misura volumi, qualità né priorità.',
 seasonality_public_replay_not_native_monthly_panel:'Si usano i valori pubblicati, non i dati mensili originali.',
 seasonality_sum_of_local_top_three_not_regional_top_three:'I tre mesi principali sono quelli di ciascun Comune, non della regione.',
 seasonality_top_three_months_not_fixed_summer_quarter:'I tre mesi principali non sono per forza giugno, luglio e agosto.',
 single_2021_snapshot_not_current_mobility:'È una fotografia del 2021, non la mobilità di oggi.',
 single_household_not_direct_measure_of_loneliness:'Vivere da soli non misura direttamente la solitudine.',
 slow_mobility_A0_B1_provenance_not_accessibility_quality:'La provenienza dei percorsi non indica accessibilità né qualità.',
 slow_mobility_inventory_20260812_not_current_route_status:'L’elenco dei percorsi è aggiornato al 12 agosto 2026, non indica lo stato attuale.',
 slow_mobility_inventory_not_exhaustive_or_current_safety:'L’elenco dei percorsi non è completo e non indica la sicurezza attuale.',
 slow_mobility_membership_replay_not_geometry_intersection_replay:'L’appartenenza dei percorsi ai Comuni non è ricalcolata sulle geometrie.',
 slow_mobility_municipal_memberships_overlap_not_additive_unique_routes:'Un percorso può attraversare più Comuni: i conteggi non si sommano.',
 slow_mobility_no_municipal_lengths_or_reverse_derived_rates:'Non sono disponibili le lunghezze per Comune.',
 slow_mobility_numeric_rank_not_policy_priority:'L’ordine numerico non indica priorità.',
 slow_mobility_primary_mode_not_all_possible_activities:'Il tipo indicato è quello principale, non tutte le attività possibili sul percorso.',
 snapshot_is_not_live_source_verification:'È una fotografia dei dati alla data indicata, non una verifica in tempo reale della fonte.',
 social_2014_2022_includes_early_childhood_no_excluded_scope_concatenation:'La serie 2014–2022 include i servizi per la prima infanzia.',
 social_municipal_arithmetic_means_not_consolidated_versilia:'La media dei Comuni non è il dato complessivo della Versilia.',
 social_native_denominators_unavailable_no_pooling_or_reverse_derived_counts:'Mancano le basi di calcolo originali: non si aggregano né si ricostruiscono i conteggi.',
 social_nominal_euros_no_inflation_adjustment:'Gli importi sono in euro nominali, senza correzione per l’inflazione.',
 social_spending_not_need_quality_effectiveness_or_policy_priority:'La spesa sociale non misura bisogno, qualità, efficacia né priorità.',
 standardized_rate_not_crude_ratio:'È un tasso standardizzato per età, diverso dal semplice rapporto casi/abitanti.',
 tourism_arrivals_not_unique_people:'Gli arrivi contano i soggiorni, non persone distinte.',
 tourism_capacity_2024_residents_2026_distinct:'I posti letto sono del 2024, i residenti del 2026.',
 tourism_capacity_2025_scope_expansion_excluded:'L’ampliamento del perimetro delle strutture nel 2025 è escluso dal confronto.',
 tourism_existing_presences_operations_preserved:'Le presenze turistiche già pubblicate restano invariate.',
 tourism_frozen_extraction_not_new_live_acquisition:'I dati sul turismo sono un’estrazione fissata a una data, non un aggiornamento in tempo reale.',
 tourism_movement_net_of_rentals_provisional:'I movimenti turistici escludono gli affitti brevi e sono provvisori.',
 tourism_native_7899_municipal_records_not_new_workbook_replay:'I dati turistici sono quelli comunali già acquisiti, non una nuova estrazione.',
 tourism_numerical_rank_not_destination_quality:'L’ordine numerico non misura la qualità della destinazione turistica.',
 tourism_posas_2026_estimate:'La popolazione 2026 usata come base è una stima.',
 tpl_feed_stop_ids_not_unique_physical_stops_or_walk_access:'I punti di fermata del trasporto pubblico non coincidono con fermate fisiche distinte né misurano l’accessibilità a piedi.',
 tpl_gtfs_calendar_spatial_join_and_raw_feeds_not_replayed:'Gli orari e le fermate originali non sono stati ricontrollati.',
 tpl_municipal_trip_memberships_not_unique_territorial_trips:'Una stessa corsa può attraversare più Comuni: i conteggi non si sommano.',
 tpl_no_automatic_causal_or_policy_priority_inference:'I dati sul trasporto pubblico non indicano cause né priorità.',
 tpl_scheduled_summer_weekday_not_actual_service_reliability_capacity_or_passengers:'Sono corse programmate in un giorno feriale estivo, non il servizio reale, la puntualità o i passeggeri.',
 tpl_span_not_frequency_or_continuous_service:'L’ampiezza oraria non indica la frequenza né un servizio continuo.',
 waste_historical_series_does_not_attest_methodological_continuity:'La serie sui rifiuti non garantisce che il metodo sia rimasto lo stesso nel tempo.',
 waste_raw_municipal_quantities_not_frozen_no_implicit_weighting:'Le quantità di rifiuti sono quelle originali, senza ponderazioni aggiunte.',
 waste_resident_denominator_not_population_present_or_tourist_production:'Il calcolo per residente non tiene conto di turisti e presenze stagionali.',
 water_census_snapshot_not_current_network_condition:'Il dato sulla rete idrica è una fotografia del censimento, non lo stato attuale.',
 water_loss_components_not_split_in_snapshot:'Le perdite idriche non sono distinte per tipo.'
};
function source(source){
 const p=node('p',undefined,'a7-source');
 try{
  const url=new URL(source);const names={'esploradati.istat.it':'ISTAT','www.istat.it':'ISTAT','demo.istat.it':'ISTAT','dati.toscana.it':'Regione Toscana','www.regione.toscana.it':'Regione Toscana','serviziostatistico.invalsi.it':'INVALSI','dati.istruzione.it':'Ministero dell’Istruzione e del Merito','www.ars.toscana.it':'Agenzia regionale di sanità','at.erplucca.it':'ERP Lucca','www.catasto-rifiuti.isprambiente.it':'ISPRA','www1.agenziaentrate.gov.it':'Agenzia delle Entrate (OMI)','www1.finanze.gov.it':'Ministero dell’Economia e delle Finanze','osservatorioversilia.it':'Osservatorio Versilia'};
  if(url.protocol==='https:'&&names[url.hostname]){const a=node('a',names[url.hostname]);a.href=url.href;p.append(node('span','Fonte: '),a);return p;}
 }catch{}
 p.textContent='Fonte indicata nei dati scaricabili.';return p;
}
function selectedQuestion(){const el=document.getElementById('a7-selected-question');if(el)el.textContent=document.getElementById('domanda').selectedOptions[0]?.textContent||'';}
function presentPublic(out,answer){
 selectedQuestion();
 const q=answer.questionPlan;
 out.classList.remove('edu-answer');
 document.getElementById('a7-guided').classList.toggle('education-reading',q.id==='infanzia-centrale');
 if(q.id==='infanzia-centrale'){presentEducation(out,answer,education);return;}
 out.append(node('p','La tua domanda','eyebrow'),node('h2',q.question));
 out.append(node('p',introductions[q.id]||q.interpretationLimit,'a7-answer-intro'),node('h3',headings[q.dossierId]||headings[q.id.split('-')[0]]||'Il territorio a confronto'));
 for(const c of answer.components){
  const section=node('section',undefined,'component');section.setAttribute('aria-label','Dati della lettura');
  const first=c.facts[0];const title=first?first.text.split(' — ')[0]:'Un confronto che non possiamo calcolare';
  section.append(node('h4',title,'a7-indicator-title'));
  if(c.response.coverage && c.response.coverage.usable<c.response.coverage.requested)section.append(node('p',`Dati disponibili per ${c.response.coverage.usable} delle ${c.response.coverage.requested} osservazioni richieste. I mancanti restano esclusi.`, 'a7-coverage'));
  if(c.response.status!=='computed')section.append(node('p','I dati disponibili non permettono questo calcolo. Il consenso a leggere risultati parziali non cambia questo limite.'));
  // Plot only comparable observations already returned by the certified reader.
  // Results/pooled totals remain text: never mix them into territorial bars.
  const observations=c.facts.filter(f=>f.kind==='observation');
  const base=observations[0];
  const comparable=base&&observations.length>1&&observations.every(f=>
   f.unit===base.unit&&f.definition===base.definition&&f.dimension===base.dimension&&f.population===base.population&&f.method===base.method&&(f.source===base.source||(f.geography===base.geography&&new URL(f.source).origin===new URL(base.source).origin)))&&
   (observations.every(f=>f.period===base.period)||observations.every(f=>f.geography===base.geography));
  const numeric=observations.filter(f=>typeof f.value==='number'&&Number.isFinite(f.value));
  const plot=comparable&&numeric.length>0&&numeric.every(f=>f.value>=0);
  const maximum=plot?(base.unit==='percent'&&numeric.every(f=>f.value<=100)&&!base.definition.includes('cumulative')?100:Math.max(...numeric.map(f=>f.value))||1):1;
  if(plot){section.dataset.a7Chart='bars';section.append(node('p',`Confronto visivo · ${base.unit==='percent'?'scala percentuale':base.unit==='millionCurrency'?'milioni di euro':base.unit==='currency'?'euro':base.unit==='studentsPerClass'?'alunni per classe':'persone'} · da 0 a ${new Intl.NumberFormat('it-IT',{maximumFractionDigits:2}).format(maximum)}. ${observations.every(f=>f.period===base.period)?'Periodo: '+base.period:'Anni osservati: '+observations.map(f=>f.period).join(' e ')+'. Importi nominali; non è un andamento annuale.'}`,'meta'));}
  const ul=node('ul',undefined,'facts');
  for(const f of c.facts){
   const li=node('li');
   // The measure is named once in the component heading. Keep canonical
   // wording, periods and precision in export; shorten only matching labels.
   const prefix=title+' — ';
   const label=f.text.startsWith(prefix)?f.text.slice(prefix.length):f.text;
   li.append(node('p',label.replace('persone/addetti secondo definizione.','persone.'),'a7-fact'));
   if(plot&&f.kind==='observation'){
    if(typeof f.value==='number'&&Number.isFinite(f.value)){
     const track=node('div',undefined,'a7-bar-track');track.setAttribute('aria-hidden','true');
     const bar=node('span',undefined,'a7-bar');bar.style.width=(100*f.value/maximum)+'%';
     bar.dataset.value=String(f.value);bar.dataset.maximum=String(maximum);bar.dataset.geography=f.geography;bar.dataset.period=f.period;
     if(f.geography==='046018')bar.classList.add('a7-bar-focus');track.append(bar);li.append(track);
    }else li.append(node('p','Dato non disponibile: nessuna barra e nessun valore zero attribuito.','meta'));
   }
   if(f.period!==undefined)li.append(node('p','Periodo: '+f.period,'meta'));
   if(f.population!==undefined&&populations[f.population])li.append(node('p',populations[f.population],'a7-scope'));
   li.append(source(f.source));ul.append(li);
  }
  section.append(ul);
  if(c.response.warnings.length)section.append(fold('Come leggere questo dato',list([...new Set(c.response.warnings.map(w=>warnings[w]||'Sono presenti ulteriori limiti metodologici, conservati nei dettagli di verifica.'))])));
  out.append(section);
 }
 out.append(node('h3','Per interpretare i confronti'),node('p',boundaries[q.id]||q.answerBoundary,'a7-answer-boundary'));
 out.append(node('h3','Che cosa ci racconta questo confronto'),node('p',q.interpretationLimit));
 out.append(fold('Quali dati mancano per decidere?',list(q.missingData)));
 const docs=node('p');const a=node('a','Approfondisci nel dossier');
 // The canonical source path and pinned commit are validated before publishing.
 const commit=sourceCommit;
 if(/^[a-f0-9]{40}$/u.test(commit||'')&&/^docs\/[A-Za-z0-9_./-]+$/u.test(q.dossierPath)&&!q.dossierPath.split('/').includes('..')){a.href=`https://github.com/EmAnzi3/osservatorio-versilia/blob/${commit}/${q.dossierPath}`;docs.append(a);out.append(docs);}
 const verification=node('div');const snapshots=node('ul');const seen=new Set();
 for(const c of answer.components)for(const f of c.facts)for(const e of f.evidence){
  if(!/^[a-f0-9]{40}$/u.test(sourceCommit||'')||!/^data\/[A-Za-z0-9_./-]+$/u.test(e.path||'')||e.path.split('/').includes('..')||seen.has(e.path))continue;
  seen.add(e.path);const li=node('li');const link=node('a','Dati della fonte conservati');
  link.href=`https://github.com/EmAnzi3/osservatorio-versilia/${e.encoding==='concatenate_ascii_base64_gzip_json'?'tree':'blob'}/${sourceCommit}/${e.path}`;li.append(link);snapshots.append(li);
 }
 const evidence=node('pre',JSON.stringify(answer,null,2));evidence.hidden=true;evidence.style.display='none';
 verification.append(snapshots,evidence);
 out.append(fold('Scarica e verifica i dati',verification,true));
}
new MutationObserver(()=>{if(document.getElementById('risposta').hidden)document.getElementById('a7-guided').classList.remove('education-reading');}).observe(document.getElementById('risposta'),{attributes:true,attributeFilter:['hidden']});
document.getElementById('a7-guided').addEventListener('focusin',event=>{
 const target=event.target;if(!['risposta','titolo-chiarimento'].includes(target.id))return;
 requestAnimationFrame(()=>{if(document.activeElement===target&&!target.closest('[hidden]'))target.scrollIntoView({block:'start',behavior:'instant'});});
});
try{
 const {default:release}=await import('./release.mjs');sourceCommit=release.repositoryCommit;
 education=await loadEducation(release);
 const ui=await import('./preview.mjs');
 ui.setAnswerPresentation(presentPublic);
 const choice=document.getElementById('domanda');const description=node('p',undefined,'a7-selected-question');description.id='a7-selected-question';choice.after(description);choice.setAttribute('aria-describedby',description.id);
 for(const id of ['domanda','dossier'])document.getElementById(id).addEventListener('change',selectedQuestion);selectedQuestion();
 if(new URLSearchParams(location.search).get('lettura')==='educazione'){
  document.getElementById('dossier').value='infanzia';document.getElementById('dossier').dispatchEvent(new Event('change'));
  document.getElementById('domanda').value='infanzia-centrale';selectedQuestion();document.getElementById('mostra').click();
 }
}catch(error){
 document.getElementById('stato').textContent='Evidenze non disponibili o non verificabili. Nessun risultato mostrato. Ricarica la pagina.';
 for(const id of ['dossier','domanda','mostra','domanda-testo','verifica-testo'])document.getElementById(id).disabled=true;
 document.getElementById('risposta').hidden=true;document.getElementById('risposta').replaceChildren();
}
