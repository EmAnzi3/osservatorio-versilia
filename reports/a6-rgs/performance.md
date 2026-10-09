# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `7f377ea76a803df738c45ab457958a8a9b251c5cbe163bb7b22ccc8fd12466c9`; domande `f87e993713be3b481d521a75b30b31317a57e47587fafdbac97ec9308528af57`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "agricultureProfileAdapterSha256": "3b65fa2c02807e5454d7e59110ab6ba0990a7272ca11014ef625a6088a3f3b86", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "bathingAdapterSha256": "562061699d57c58292c702e2598d883ee05348de649caad1c50f3719880285a4", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "classificationAdapterSha256": "b1b480a0e46be5f6d87819a22120969ce1f80dc591c5622339ba4a4fac674a01", "climateAdapterSha256": "62a385a9a49a9ef9e91dc3e25f6f77b2be3a6a259c38950fc493dcc0713c886f", "coastAdapterSha256": "1ace0bf132cfa6200b65997dd397e9e3ad47ae5f083e1d4fae33f878572fea09", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "extractiveAdapterSha256": "4261110cd0fadd43b8691be3f2da2d40a23e98fcbe11942af311ddce98490972", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "fragilityAdapterSha256": "b1b104bb69ebbb5dfecd9061955b6113b342f583746e43eb12986a719fefd76e", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "maritimeAdapterSha256": "bced33dc09761daa64e54ca69c35822ba603bbaebc370c3f9923ccf1eb6dd3e2", "mefAdapterSha256": "119bfba1c853790b4ee3aa74e3b88d16d6019abd597e4471512092f528fe7496", "pabAdapterSha256": "fad0391a396cf4e9a6ee32e1ac965fe4a10f3684fccc5d0690efd7435452a1b8", "remediationAdapterSha256": "303269e55e8d4f5a2275b45a96833df27fc755cd61b035feb38052883a673368", "rgsAdapterSha256": "b7bd7fb6a1ea5d3b5a94d6bb6a4d879939471bb6f46f95d07fcd44dfaa80d5af", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97", "waterQualityAdapterSha256": "26a2406f232176661c63411a454bb051466af782a1d1c9db4e4ecf734ca394c7"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 157.754 | 229.729 | 245.712 |
| rgs_municipalStaffAgeStructure_age_age55plus_pooled · prima query, nuova istanza | 5 | 1.880 | 2.420 | 2.472 |
| rgs_municipalStaffAgeStructure_age_age55plus_pooled · query con cache applicativa | 30 | 1.539 | 2.613 | 2.680 |
| rgs_training_total_versilia · prima query, nuova istanza | 5 | 1.778 | 3.576 | 3.980 |
| rgs_training_total_versilia · query con cache applicativa | 30 | 1.312 | 2.000 | 2.841 |
| rgs_training_pooling_refused · prima query, nuova istanza | 5 | 0.953 | 1.721 | 1.814 |
| rgs_training_pooling_refused · query con cache applicativa | 30 | 0.790 | 1.131 | 2.449 |
| mef_incomeSourceProfile_source_employment_pooled · prima query, nuova istanza | 5 | 3.458 | 4.189 | 4.195 |
| mef_incomeSourceProfile_source_employment_pooled · query con cache applicativa | 30 | 3.004 | 4.057 | 5.565 |
| mef_taxpayersAdultPopulationRate_total_pooled · prima query, nuova istanza | 5 | 14.908 | 17.198 | 17.565 |
| mef_taxpayersAdultPopulationRate_total_pooled · query con cache applicativa | 30 | 11.941 | 16.138 | 19.348 |
| mef_incomeSourceProfile_pair_refused · prima query, nuova istanza | 5 | 4.148 | 6.085 | 6.565 |
| mef_incomeSourceProfile_pair_refused · query con cache applicativa | 30 | 1.005 | 1.428 | 1.485 |
| water_quality_case_rosse_5 · prima query, nuova istanza | 5 | 3.719 | 6.452 | 7.093 |
| water_quality_case_rosse_5 · query con cache applicativa | 30 | 2.087 | 2.890 | 2.994 |
| water_quality_localities_046030 · prima query, nuova istanza | 5 | 4.191 | 4.574 | 4.602 |
| water_quality_localities_046030 · query con cache applicativa | 30 | 2.855 | 3.999 | 4.443 |
| water_quality_weighted_ratio_refused · prima query, nuova istanza | 5 | 1.101 | 1.688 | 1.708 |
| water_quality_weighted_ratio_refused · query con cache applicativa | 30 | 0.843 | 1.179 | 1.317 |
| classification_part_coastalZone_046018 · prima query, nuova istanza | 5 | 1.871 | 2.970 | 3.186 |
| classification_part_coastalZone_046018 · query con cache applicativa | 30 | 1.543 | 2.328 | 2.482 |
| classification_total_rank_refused · prima query, nuova istanza | 5 | 1.039 | 1.262 | 1.313 |
| classification_total_rank_refused · query con cache applicativa | 30 | 0.818 | 1.547 | 2.350 |
| agriculture_profiles_female_pooled · prima query, nuova istanza | 5 | 2.783 | 4.153 | 4.401 |
| agriculture_profiles_female_pooled · query con cache applicativa | 30 | 2.340 | 4.171 | 4.957 |
| agriculture_profiles_organic_series · prima query, nuova istanza | 5 | 3.657 | 4.663 | 4.907 |
| agriculture_profiles_organic_series · query con cache applicativa | 30 | 3.711 | 8.950 | 10.813 |
| agriculture_profiles_organic_pooling_refused · prima query, nuova istanza | 5 | 1.062 | 1.382 | 1.403 |
| agriculture_profiles_organic_pooling_refused · query con cache applicativa | 30 | 1.017 | 1.807 | 1.943 |
| climate_temperature_current · prima query, nuova istanza | 5 | 3.960 | 8.788 | 9.210 |
| climate_temperature_current · query con cache applicativa | 30 | 2.926 | 4.808 | 6.013 |
| climate_tmin_annual_trend · prima query, nuova istanza | 5 | 5.882 | 6.769 | 6.854 |
| climate_tmin_annual_trend · query con cache applicativa | 30 | 4.309 | 6.354 | 7.152 |
| climate_precipitation_pooling_refused · prima query, nuova istanza | 5 | 1.060 | 1.171 | 1.196 |
| climate_precipitation_pooling_refused · query con cache applicativa | 30 | 0.705 | 1.180 | 1.385 |
| pab_pabProgrammedInterventions · prima query, nuova istanza | 5 | 26.562 | 29.603 | 30.157 |
| pab_pabProgrammedInterventions · query con cache applicativa | 30 | 8.338 | 11.606 | 13.963 |
| pab_pabInterventionsCompleted_share_pooled · prima query, nuova istanza | 5 | 29.887 | 41.086 | 43.706 |
| pab_pabInterventionsCompleted_share_pooled · query con cache applicativa | 30 | 8.342 | 9.527 | 15.910 |
| pab_approved_operational_refused · prima query, nuova istanza | 5 | 1.297 | 2.505 | 2.788 |
| pab_approved_operational_refused · query con cache applicativa | 30 | 0.805 | 3.747 | 4.998 |
| remediation_total · prima query, nuova istanza | 5 | 4.865 | 6.139 | 6.407 |
| remediation_total · query con cache applicativa | 30 | 3.050 | 4.094 | 5.786 |
| remediation_pooled · prima query, nuova istanza | 5 | 4.540 | 6.503 | 6.824 |
| remediation_pooled · query con cache applicativa | 30 | 3.313 | 4.203 | 4.530 |
| remediation_history_refused · prima query, nuova istanza | 5 | 1.299 | 1.385 | 1.400 |
| remediation_history_refused · query con cache applicativa | 30 | 0.737 | 1.120 | 1.467 |
| extractive_sites_active · prima query, nuova istanza | 5 | 3.025 | 3.665 | 3.779 |
| extractive_sites_active · query con cache applicativa | 30 | 1.929 | 3.095 | 3.945 |
| extractive_prc_pooled · prima query, nuova istanza | 5 | 5.147 | 7.140 | 7.468 |
| extractive_prc_pooled · query con cache applicativa | 30 | 3.376 | 4.815 | 5.491 |
| extractive_production_history · prima query, nuova istanza | 5 | 4.822 | 6.741 | 7.127 |
| extractive_production_history · query con cache applicativa | 30 | 3.618 | 5.280 | 6.677 |
| maritime_tourist_pooled · prima query, nuova istanza | 5 | 3.206 | 3.381 | 3.384 |
| maritime_tourist_pooled · query con cache applicativa | 30 | 2.166 | 3.581 | 4.162 |
| maritime_mean_due_pooled · prima query, nuova istanza | 5 | 2.894 | 3.712 | 3.803 |
| maritime_mean_due_pooled · query con cache applicativa | 30 | 2.407 | 3.528 | 4.339 |
| maritime_median_weighting_refused · prima query, nuova istanza | 5 | 1.367 | 1.579 | 1.630 |
| maritime_median_weighting_refused · query con cache applicativa | 30 | 0.856 | 1.422 | 1.618 |
| bathing_quality_pooled · prima query, nuova istanza | 5 | 1.873 | 2.065 | 2.108 |
| bathing_quality_pooled · query con cache applicativa | 30 | 1.430 | 2.289 | 2.678 |
| bathing_samples_pooled · prima query, nuova istanza | 5 | 1.762 | 2.109 | 2.118 |
| bathing_samples_pooled · query con cache applicativa | 30 | 1.525 | 2.331 | 4.120 |
| bathing_blue_history · prima query, nuova istanza | 5 | 3.729 | 4.279 | 4.302 |
| bathing_blue_history · query con cache applicativa | 30 | 1.914 | 2.645 | 3.324 |
| coast_protection_pooled · prima query, nuova istanza | 5 | 1.769 | 2.279 | 2.376 |
| coast_protection_pooled · query con cache applicativa | 30 | 1.199 | 1.834 | 1.954 |
| coast_dynamics_erosion_pooled · prima query, nuova istanza | 5 | 2.019 | 3.275 | 3.390 |
| coast_dynamics_erosion_pooled · query con cache applicativa | 30 | 1.350 | 2.449 | 3.394 |
| coast_mixed_universe_refused · prima query, nuova istanza | 5 | 1.190 | 1.290 | 1.296 |
| coast_mixed_universe_refused · query con cache applicativa | 30 | 0.814 | 1.060 | 1.218 |
| ifc_municipalFragility_series · prima query, nuova istanza | 5 | 2.162 | 2.782 | 2.793 |
| ifc_municipalFragility_series · query con cache applicativa | 30 | 1.499 | 5.158 | 8.287 |
| ifc_access_tuscany_gap · prima query, nuova istanza | 5 | 11.753 | 15.052 | 15.171 |
| ifc_access_tuscany_gap · query con cache applicativa | 30 | 7.338 | 9.488 | 12.732 |
| ifc_lowProductivityEmployment_relative_change_refused · prima query, nuova istanza | 5 | 1.407 | 1.451 | 1.459 |
| ifc_lowProductivityEmployment_relative_change_refused · query con cache applicativa | 30 | 0.787 | 2.025 | 3.795 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 1.888 | 2.181 | 2.238 |
| hazard_flood_pooled · query con cache applicativa | 30 | 1.322 | 2.209 | 7.968 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 2.021 | 2.392 | 2.456 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 1.242 | 1.614 | 1.875 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 3.402 | 3.919 | 3.987 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 2.908 | 6.832 | 8.938 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 2.060 | 2.326 | 2.376 |
| territory_protected_pooled · query con cache applicativa | 30 | 1.310 | 2.532 | 4.234 |
| territory_network_pooled · prima query, nuova istanza | 5 | 1.687 | 8.020 | 9.430 |
| territory_network_pooled · query con cache applicativa | 30 | 1.071 | 2.237 | 2.495 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 3.284 | 3.993 | 4.041 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 2.004 | 2.893 | 3.043 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.853 | 2.347 | 2.347 |
| soil_stock_pooled · query con cache applicativa | 30 | 1.050 | 1.563 | 1.811 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.669 | 2.033 | 2.036 |
| soil_ucs_pooled · query con cache applicativa | 30 | 1.096 | 1.643 | 2.335 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 2.794 | 4.568 | 5.010 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.794 | 2.404 | 4.646 |
| geography_density_pooled · prima query, nuova istanza | 5 | 3.324 | 6.099 | 6.791 |
| geography_density_pooled · query con cache applicativa | 30 | 1.446 | 2.092 | 2.396 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.646 | 4.488 | 5.165 |
| geography_forest_pooled · query con cache applicativa | 30 | 1.405 | 3.381 | 3.898 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 2.459 | 3.425 | 3.481 |
| geography_mixed_reference · query con cache applicativa | 30 | 1.661 | 2.281 | 2.579 |
| population_current · prima query, nuova istanza | 5 | 3.277 | 6.804 | 7.604 |
| population_current · query con cache applicativa | 30 | 1.006 | 1.322 | 1.702 |
| female_weighted · prima query, nuova istanza | 5 | 2.204 | 3.758 | 4.108 |
| female_weighted · query con cache applicativa | 30 | 1.272 | 2.119 | 3.246 |
| ars_gap · prima query, nuova istanza | 5 | 5.565 | 12.811 | 14.272 |
| ars_gap · query con cache applicativa | 30 | 1.088 | 1.443 | 1.517 |
| aligned_association · prima query, nuova istanza | 5 | 3.902 | 9.031 | 9.573 |
| aligned_association · query con cache applicativa | 30 | 2.182 | 5.019 | 6.048 |
| mismatched_association · prima query, nuova istanza | 5 | 3.323 | 7.939 | 8.926 |
| mismatched_association · query con cache applicativa | 30 | 1.604 | 2.274 | 3.957 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 5.442 | 9.327 | 10.139 |
| ars_hypertension_age · query con cache applicativa | 30 | 1.093 | 1.433 | 1.541 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 5.458 | 10.184 | 11.301 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 1.149 | 1.609 | 1.917 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 2.528 | 3.668 | 3.947 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 1.463 | 1.872 | 2.104 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 1.087 | 1.271 | 1.282 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.757 | 1.015 | 1.113 |
| census_young_employment · prima query, nuova istanza | 5 | 2.569 | 2.746 | 2.785 |
| census_young_employment · query con cache applicativa | 30 | 1.280 | 2.972 | 3.180 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 1.121 | 1.504 | 1.550 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.764 | 1.030 | 1.155 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 2.518 | 3.007 | 3.096 |
| finance_cash_weighted · query con cache applicativa | 30 | 1.281 | 1.952 | 2.229 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 2.083 | 2.352 | 2.357 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.815 | 1.704 | 1.732 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 3.438 | 3.595 | 3.604 |
| distinct_debt_weighted · query con cache applicativa | 30 | 1.319 | 1.718 | 2.949 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 1.025 | 1.391 | 1.461 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.829 | 1.173 | 1.318 |
| demography_dependency · prima query, nuova istanza | 5 | 30.296 | 32.824 | 33.378 |
| demography_dependency · query con cache applicativa | 30 | 1.221 | 2.696 | 3.437 |
| school_class_size · prima query, nuova istanza | 5 | 47.766 | 70.817 | 75.407 |
| school_class_size · query con cache applicativa | 30 | 1.322 | 1.992 | 2.880 |
| demography_aligned_events · prima query, nuova istanza | 5 | 31.101 | 36.804 | 38.185 |
| demography_aligned_events · query con cache applicativa | 30 | 2.443 | 3.117 | 3.421 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 1.299 | 1.632 | 1.683 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.841 | 1.116 | 1.129 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 54.860 | 61.722 | 62.497 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 1.196 | 1.864 | 3.134 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 54.483 | 57.588 | 57.872 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 1.392 | 1.998 | 2.774 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 57.056 | 69.412 | 72.210 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 1.581 | 2.587 | 3.487 |
| environment_water_pooled · prima query, nuova istanza | 5 | 2.921 | 3.322 | 3.399 |
| environment_water_pooled · query con cache applicativa | 30 | 1.326 | 2.458 | 2.655 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 26.367 | 29.711 | 30.378 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 1.166 | 1.809 | 2.612 |
| environment_cost_gap · prima query, nuova istanza | 5 | 1.440 | 2.856 | 3.079 |
| environment_cost_gap · query con cache applicativa | 30 | 0.931 | 1.495 | 2.169 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.871 | 2.047 | 2.049 |
| agriculture_pooled_size · query con cache applicativa | 30 | 1.475 | 2.820 | 5.082 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.730 | 1.876 | 1.879 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 1.202 | 1.456 | 1.722 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.633 | 1.831 | 1.850 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 1.316 | 1.993 | 7.087 |

Allocazioni Python: picco 27.476 MiB; mantenute 25.934 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
