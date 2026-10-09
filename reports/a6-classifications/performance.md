# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `1d470cef282c0476f851cf3243cab3379f3eeac5ca147dd2f2e8093638e52dfb`; domande `4198ade9b540083e1667125e5e65b97c45dfe94c18dff91d3a10726d435f5cf5`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "agricultureProfileAdapterSha256": "3b65fa2c02807e5454d7e59110ab6ba0990a7272ca11014ef625a6088a3f3b86", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "bathingAdapterSha256": "562061699d57c58292c702e2598d883ee05348de649caad1c50f3719880285a4", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "classificationAdapterSha256": "b1b480a0e46be5f6d87819a22120969ce1f80dc591c5622339ba4a4fac674a01", "climateAdapterSha256": "62a385a9a49a9ef9e91dc3e25f6f77b2be3a6a259c38950fc493dcc0713c886f", "coastAdapterSha256": "1ace0bf132cfa6200b65997dd397e9e3ad47ae5f083e1d4fae33f878572fea09", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "extractiveAdapterSha256": "4261110cd0fadd43b8691be3f2da2d40a23e98fcbe11942af311ddce98490972", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "fragilityAdapterSha256": "b1b104bb69ebbb5dfecd9061955b6113b342f583746e43eb12986a719fefd76e", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "maritimeAdapterSha256": "bced33dc09761daa64e54ca69c35822ba603bbaebc370c3f9923ccf1eb6dd3e2", "pabAdapterSha256": "fad0391a396cf4e9a6ee32e1ac965fe4a10f3684fccc5d0690efd7435452a1b8", "remediationAdapterSha256": "303269e55e8d4f5a2275b45a96833df27fc755cd61b035feb38052883a673368", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 157.453 | 325.716 | 350.473 |
| classification_part_coastalZone_046018 · prima query, nuova istanza | 5 | 2.320 | 4.009 | 4.419 |
| classification_part_coastalZone_046018 · query con cache applicativa | 30 | 1.458 | 1.869 | 1.955 |
| classification_total_rank_refused · prima query, nuova istanza | 5 | 0.954 | 1.471 | 1.498 |
| classification_total_rank_refused · query con cache applicativa | 30 | 0.620 | 0.977 | 1.145 |
| agriculture_profiles_female_pooled · prima query, nuova istanza | 5 | 2.618 | 2.695 | 2.710 |
| agriculture_profiles_female_pooled · query con cache applicativa | 30 | 1.949 | 2.670 | 3.430 |
| agriculture_profiles_organic_series · prima query, nuova istanza | 5 | 3.141 | 4.021 | 4.170 |
| agriculture_profiles_organic_series · query con cache applicativa | 30 | 2.469 | 6.278 | 8.931 |
| agriculture_profiles_organic_pooling_refused · prima query, nuova istanza | 5 | 0.881 | 0.960 | 0.978 |
| agriculture_profiles_organic_pooling_refused · query con cache applicativa | 30 | 0.661 | 1.254 | 1.418 |
| climate_temperature_current · prima query, nuova istanza | 5 | 2.368 | 5.649 | 6.465 |
| climate_temperature_current · query con cache applicativa | 30 | 1.608 | 2.743 | 4.052 |
| climate_tmin_annual_trend · prima query, nuova istanza | 5 | 3.512 | 4.665 | 4.723 |
| climate_tmin_annual_trend · query con cache applicativa | 30 | 3.004 | 4.020 | 13.070 |
| climate_precipitation_pooling_refused · prima query, nuova istanza | 5 | 0.969 | 1.158 | 1.198 |
| climate_precipitation_pooling_refused · query con cache applicativa | 30 | 0.681 | 1.714 | 2.486 |
| pab_pabProgrammedInterventions · prima query, nuova istanza | 5 | 22.722 | 27.211 | 27.696 |
| pab_pabProgrammedInterventions · query con cache applicativa | 30 | 7.433 | 10.276 | 11.557 |
| pab_pabInterventionsCompleted_share_pooled · prima query, nuova istanza | 5 | 22.488 | 30.495 | 32.416 |
| pab_pabInterventionsCompleted_share_pooled · query con cache applicativa | 30 | 7.268 | 10.659 | 14.328 |
| pab_approved_operational_refused · prima query, nuova istanza | 5 | 0.871 | 1.000 | 1.032 |
| pab_approved_operational_refused · query con cache applicativa | 30 | 0.674 | 1.361 | 1.518 |
| remediation_total · prima query, nuova istanza | 5 | 4.225 | 5.245 | 5.387 |
| remediation_total · query con cache applicativa | 30 | 2.777 | 3.531 | 4.568 |
| remediation_pooled · prima query, nuova istanza | 5 | 4.634 | 5.529 | 5.737 |
| remediation_pooled · query con cache applicativa | 30 | 3.032 | 3.843 | 4.309 |
| remediation_history_refused · prima query, nuova istanza | 5 | 0.944 | 0.979 | 0.985 |
| remediation_history_refused · query con cache applicativa | 30 | 0.577 | 0.960 | 1.593 |
| extractive_sites_active · prima query, nuova istanza | 5 | 2.874 | 3.115 | 3.127 |
| extractive_sites_active · query con cache applicativa | 30 | 1.916 | 3.456 | 12.285 |
| extractive_prc_pooled · prima query, nuova istanza | 5 | 4.707 | 7.664 | 7.980 |
| extractive_prc_pooled · query con cache applicativa | 30 | 3.441 | 5.998 | 6.833 |
| extractive_production_history · prima query, nuova istanza | 5 | 4.422 | 4.956 | 5.066 |
| extractive_production_history · query con cache applicativa | 30 | 3.516 | 4.181 | 4.960 |
| maritime_tourist_pooled · prima query, nuova istanza | 5 | 2.939 | 4.132 | 4.411 |
| maritime_tourist_pooled · query con cache applicativa | 30 | 2.222 | 3.092 | 3.523 |
| maritime_mean_due_pooled · prima query, nuova istanza | 5 | 2.835 | 3.968 | 4.166 |
| maritime_mean_due_pooled · query con cache applicativa | 30 | 1.909 | 2.695 | 2.994 |
| maritime_median_weighting_refused · prima query, nuova istanza | 5 | 0.976 | 1.239 | 1.299 |
| maritime_median_weighting_refused · query con cache applicativa | 30 | 0.598 | 1.170 | 1.801 |
| bathing_quality_pooled · prima query, nuova istanza | 5 | 1.846 | 2.263 | 2.355 |
| bathing_quality_pooled · query con cache applicativa | 30 | 1.330 | 2.172 | 4.334 |
| bathing_samples_pooled · prima query, nuova istanza | 5 | 1.829 | 2.425 | 2.464 |
| bathing_samples_pooled · query con cache applicativa | 30 | 0.968 | 1.498 | 1.716 |
| bathing_blue_history · prima query, nuova istanza | 5 | 2.461 | 3.257 | 3.372 |
| bathing_blue_history · query con cache applicativa | 30 | 1.615 | 2.597 | 4.546 |
| coast_protection_pooled · prima query, nuova istanza | 5 | 1.483 | 1.964 | 2.038 |
| coast_protection_pooled · query con cache applicativa | 30 | 0.930 | 1.412 | 1.586 |
| coast_dynamics_erosion_pooled · prima query, nuova istanza | 5 | 1.743 | 2.259 | 2.278 |
| coast_dynamics_erosion_pooled · query con cache applicativa | 30 | 1.009 | 1.400 | 1.843 |
| coast_mixed_universe_refused · prima query, nuova istanza | 5 | 0.893 | 1.078 | 1.106 |
| coast_mixed_universe_refused · query con cache applicativa | 30 | 0.656 | 1.143 | 1.481 |
| ifc_municipalFragility_series · prima query, nuova istanza | 5 | 1.999 | 2.405 | 2.482 |
| ifc_municipalFragility_series · query con cache applicativa | 30 | 1.119 | 1.709 | 1.918 |
| ifc_access_tuscany_gap · prima query, nuova istanza | 5 | 11.929 | 15.064 | 15.803 |
| ifc_access_tuscany_gap · query con cache applicativa | 30 | 7.958 | 14.120 | 17.667 |
| ifc_lowProductivityEmployment_relative_change_refused · prima query, nuova istanza | 5 | 1.003 | 1.087 | 1.107 |
| ifc_lowProductivityEmployment_relative_change_refused · query con cache applicativa | 30 | 0.583 | 0.915 | 1.121 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 1.877 | 2.111 | 2.143 |
| hazard_flood_pooled · query con cache applicativa | 30 | 1.071 | 1.470 | 1.489 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 1.870 | 3.575 | 3.971 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 1.225 | 1.580 | 1.733 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 3.138 | 3.992 | 4.088 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 2.466 | 3.080 | 3.739 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 1.807 | 4.432 | 5.026 |
| territory_protected_pooled · query con cache applicativa | 30 | 1.010 | 1.506 | 2.962 |
| territory_network_pooled · prima query, nuova istanza | 5 | 2.034 | 2.341 | 2.392 |
| territory_network_pooled · query con cache applicativa | 30 | 0.907 | 1.455 | 1.773 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 2.670 | 3.305 | 3.435 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 1.976 | 5.501 | 7.774 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.690 | 1.945 | 1.970 |
| soil_stock_pooled · query con cache applicativa | 30 | 0.899 | 1.352 | 1.473 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.377 | 1.466 | 1.470 |
| soil_ucs_pooled · query con cache applicativa | 30 | 1.089 | 1.765 | 1.890 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 2.887 | 3.223 | 3.237 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.669 | 2.234 | 2.558 |
| geography_density_pooled · prima query, nuova istanza | 5 | 3.982 | 5.930 | 6.095 |
| geography_density_pooled · query con cache applicativa | 30 | 1.285 | 1.883 | 2.075 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.860 | 2.437 | 2.566 |
| geography_forest_pooled · query con cache applicativa | 30 | 1.323 | 1.903 | 2.164 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 2.055 | 2.313 | 2.353 |
| geography_mixed_reference · query con cache applicativa | 30 | 1.518 | 2.760 | 3.242 |
| population_current · prima query, nuova istanza | 5 | 5.106 | 7.325 | 7.851 |
| population_current · query con cache applicativa | 30 | 1.093 | 1.934 | 5.061 |
| female_weighted · prima query, nuova istanza | 5 | 1.750 | 2.098 | 2.104 |
| female_weighted · query con cache applicativa | 30 | 1.392 | 9.005 | 11.907 |
| ars_gap · prima query, nuova istanza | 5 | 5.872 | 11.326 | 12.649 |
| ars_gap · query con cache applicativa | 30 | 0.891 | 1.363 | 2.080 |
| aligned_association · prima query, nuova istanza | 5 | 4.507 | 8.855 | 9.778 |
| aligned_association · query con cache applicativa | 30 | 1.998 | 3.929 | 7.610 |
| mismatched_association · prima query, nuova istanza | 5 | 4.960 | 6.801 | 6.858 |
| mismatched_association · query con cache applicativa | 30 | 1.558 | 2.583 | 3.725 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 7.235 | 7.924 | 7.945 |
| ars_hypertension_age · query con cache applicativa | 30 | 1.005 | 1.724 | 2.201 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 4.561 | 11.545 | 13.143 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 1.089 | 1.866 | 2.336 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 2.639 | 3.888 | 4.083 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 1.144 | 2.329 | 4.148 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 1.000 | 1.162 | 1.203 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.662 | 1.125 | 1.358 |
| census_young_employment · prima query, nuova istanza | 5 | 2.427 | 4.191 | 4.287 |
| census_young_employment · query con cache applicativa | 30 | 1.082 | 2.333 | 3.101 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 1.080 | 1.345 | 1.385 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.707 | 1.081 | 1.618 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 2.282 | 3.644 | 3.821 |
| finance_cash_weighted · query con cache applicativa | 30 | 1.086 | 1.864 | 2.710 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 2.227 | 2.365 | 2.369 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.643 | 1.273 | 1.429 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.881 | 3.858 | 3.899 |
| distinct_debt_weighted · query con cache applicativa | 30 | 1.325 | 1.725 | 1.874 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 1.372 | 1.476 | 1.491 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.644 | 0.922 | 1.131 |
| demography_dependency · prima query, nuova istanza | 5 | 26.158 | 32.039 | 32.180 |
| demography_dependency · query con cache applicativa | 30 | 1.071 | 1.974 | 3.282 |
| school_class_size · prima query, nuova istanza | 5 | 23.664 | 34.153 | 35.850 |
| school_class_size · query con cache applicativa | 30 | 1.146 | 2.485 | 2.940 |
| demography_aligned_events · prima query, nuova istanza | 5 | 26.814 | 31.677 | 32.699 |
| demography_aligned_events · query con cache applicativa | 30 | 2.180 | 2.828 | 3.178 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 1.129 | 1.254 | 1.277 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.629 | 1.006 | 2.909 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 75.510 | 135.219 | 148.595 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 1.220 | 6.163 | 11.139 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 58.853 | 83.846 | 90.040 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 1.351 | 3.817 | 3.943 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 56.634 | 69.111 | 69.542 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 1.359 | 3.609 | 4.632 |
| environment_water_pooled · prima query, nuova istanza | 5 | 2.793 | 4.554 | 4.908 |
| environment_water_pooled · query con cache applicativa | 30 | 1.029 | 1.545 | 1.607 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 22.902 | 36.762 | 38.629 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 1.111 | 2.513 | 3.290 |
| environment_cost_gap · prima query, nuova istanza | 5 | 1.652 | 4.547 | 5.197 |
| environment_cost_gap · query con cache applicativa | 30 | 1.320 | 2.599 | 3.369 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 2.128 | 2.505 | 2.535 |
| agriculture_pooled_size · query con cache applicativa | 30 | 1.220 | 2.361 | 2.640 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.635 | 1.784 | 1.791 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 1.244 | 1.652 | 1.918 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.696 | 1.858 | 1.867 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 1.006 | 1.583 | 1.745 |

Allocazioni Python: picco 27.403 MiB; mantenute 25.862 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
