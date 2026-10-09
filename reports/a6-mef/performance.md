# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `c73930fac33c527373e97bf90ea754a1f31fc5565c3c99b504f97f77faab0687`; domande `06cee5ec3ba31db1a6ac1e937c49c6529ab556eea84cd04fcbaf776ab2c4ae67`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "agricultureProfileAdapterSha256": "3b65fa2c02807e5454d7e59110ab6ba0990a7272ca11014ef625a6088a3f3b86", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "bathingAdapterSha256": "562061699d57c58292c702e2598d883ee05348de649caad1c50f3719880285a4", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "classificationAdapterSha256": "b1b480a0e46be5f6d87819a22120969ce1f80dc591c5622339ba4a4fac674a01", "climateAdapterSha256": "62a385a9a49a9ef9e91dc3e25f6f77b2be3a6a259c38950fc493dcc0713c886f", "coastAdapterSha256": "1ace0bf132cfa6200b65997dd397e9e3ad47ae5f083e1d4fae33f878572fea09", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "extractiveAdapterSha256": "4261110cd0fadd43b8691be3f2da2d40a23e98fcbe11942af311ddce98490972", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "fragilityAdapterSha256": "b1b104bb69ebbb5dfecd9061955b6113b342f583746e43eb12986a719fefd76e", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "maritimeAdapterSha256": "bced33dc09761daa64e54ca69c35822ba603bbaebc370c3f9923ccf1eb6dd3e2", "mefAdapterSha256": "119bfba1c853790b4ee3aa74e3b88d16d6019abd597e4471512092f528fe7496", "pabAdapterSha256": "fad0391a396cf4e9a6ee32e1ac965fe4a10f3684fccc5d0690efd7435452a1b8", "remediationAdapterSha256": "303269e55e8d4f5a2275b45a96833df27fc755cd61b035feb38052883a673368", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97", "waterQualityAdapterSha256": "26a2406f232176661c63411a454bb051466af782a1d1c9db4e4ecf734ca394c7"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 159.817 | 198.835 | 207.495 |
| mef_incomeSourceProfile_source_employment_pooled · prima query, nuova istanza | 5 | 3.507 | 4.050 | 4.099 |
| mef_incomeSourceProfile_source_employment_pooled · query con cache applicativa | 30 | 2.769 | 4.319 | 5.805 |
| mef_taxpayersAdultPopulationRate_total_pooled · prima query, nuova istanza | 5 | 13.277 | 26.261 | 27.728 |
| mef_taxpayersAdultPopulationRate_total_pooled · query con cache applicativa | 30 | 10.107 | 11.768 | 20.601 |
| mef_incomeSourceProfile_pair_refused · prima query, nuova istanza | 5 | 2.887 | 5.059 | 5.601 |
| mef_incomeSourceProfile_pair_refused · query con cache applicativa | 30 | 0.890 | 1.246 | 1.447 |
| water_quality_case_rosse_5 · prima query, nuova istanza | 5 | 3.941 | 8.357 | 9.358 |
| water_quality_case_rosse_5 · query con cache applicativa | 30 | 2.064 | 3.112 | 3.375 |
| water_quality_localities_046030 · prima query, nuova istanza | 5 | 3.970 | 4.812 | 4.878 |
| water_quality_localities_046030 · query con cache applicativa | 30 | 2.437 | 3.419 | 4.973 |
| water_quality_weighted_ratio_refused · prima query, nuova istanza | 5 | 1.006 | 1.799 | 1.989 |
| water_quality_weighted_ratio_refused · query con cache applicativa | 30 | 0.698 | 0.978 | 1.299 |
| classification_part_coastalZone_046018 · prima query, nuova istanza | 5 | 1.988 | 2.563 | 2.700 |
| classification_part_coastalZone_046018 · query con cache applicativa | 30 | 1.384 | 1.990 | 2.365 |
| classification_total_rank_refused · prima query, nuova istanza | 5 | 1.581 | 4.018 | 4.253 |
| classification_total_rank_refused · query con cache applicativa | 30 | 0.732 | 1.121 | 1.851 |
| agriculture_profiles_female_pooled · prima query, nuova istanza | 5 | 2.618 | 3.703 | 3.712 |
| agriculture_profiles_female_pooled · query con cache applicativa | 30 | 2.129 | 2.886 | 3.043 |
| agriculture_profiles_organic_series · prima query, nuova istanza | 5 | 4.267 | 5.671 | 5.788 |
| agriculture_profiles_organic_series · query con cache applicativa | 30 | 2.782 | 4.006 | 4.590 |
| agriculture_profiles_organic_pooling_refused · prima query, nuova istanza | 5 | 1.741 | 8.359 | 9.980 |
| agriculture_profiles_organic_pooling_refused · query con cache applicativa | 30 | 0.647 | 0.955 | 1.092 |
| climate_temperature_current · prima query, nuova istanza | 5 | 2.744 | 5.764 | 6.069 |
| climate_temperature_current · query con cache applicativa | 30 | 1.629 | 2.942 | 3.422 |
| climate_tmin_annual_trend · prima query, nuova istanza | 5 | 4.172 | 4.791 | 4.812 |
| climate_tmin_annual_trend · query con cache applicativa | 30 | 3.352 | 4.441 | 4.835 |
| climate_precipitation_pooling_refused · prima query, nuova istanza | 5 | 2.002 | 2.548 | 2.628 |
| climate_precipitation_pooling_refused · query con cache applicativa | 30 | 0.641 | 1.100 | 1.379 |
| pab_pabProgrammedInterventions · prima query, nuova istanza | 5 | 30.015 | 38.670 | 40.540 |
| pab_pabProgrammedInterventions · query con cache applicativa | 30 | 7.721 | 13.578 | 17.150 |
| pab_pabInterventionsCompleted_share_pooled · prima query, nuova istanza | 5 | 22.930 | 99.462 | 117.333 |
| pab_pabInterventionsCompleted_share_pooled · query con cache applicativa | 30 | 7.500 | 10.694 | 12.711 |
| pab_approved_operational_refused · prima query, nuova istanza | 5 | 1.114 | 1.377 | 1.416 |
| pab_approved_operational_refused · query con cache applicativa | 30 | 0.774 | 2.074 | 2.425 |
| remediation_total · prima query, nuova istanza | 5 | 4.960 | 6.270 | 6.550 |
| remediation_total · query con cache applicativa | 30 | 3.268 | 4.680 | 5.750 |
| remediation_pooled · prima query, nuova istanza | 5 | 5.193 | 6.360 | 6.435 |
| remediation_pooled · query con cache applicativa | 30 | 2.857 | 4.950 | 5.114 |
| remediation_history_refused · prima query, nuova istanza | 5 | 0.942 | 1.180 | 1.213 |
| remediation_history_refused · query con cache applicativa | 30 | 0.677 | 1.421 | 1.550 |
| extractive_sites_active · prima query, nuova istanza | 5 | 3.322 | 4.364 | 4.455 |
| extractive_sites_active · query con cache applicativa | 30 | 2.183 | 3.087 | 4.509 |
| extractive_prc_pooled · prima query, nuova istanza | 5 | 5.183 | 5.193 | 5.194 |
| extractive_prc_pooled · query con cache applicativa | 30 | 5.381 | 12.879 | 13.165 |
| extractive_production_history · prima query, nuova istanza | 5 | 4.745 | 6.166 | 6.508 |
| extractive_production_history · query con cache applicativa | 30 | 3.620 | 4.197 | 4.306 |
| maritime_tourist_pooled · prima query, nuova istanza | 5 | 3.198 | 4.036 | 4.229 |
| maritime_tourist_pooled · query con cache applicativa | 30 | 2.172 | 2.809 | 3.284 |
| maritime_mean_due_pooled · prima query, nuova istanza | 5 | 2.987 | 3.440 | 3.542 |
| maritime_mean_due_pooled · query con cache applicativa | 30 | 2.168 | 2.894 | 3.097 |
| maritime_median_weighting_refused · prima query, nuova istanza | 5 | 1.130 | 1.802 | 1.817 |
| maritime_median_weighting_refused · query con cache applicativa | 30 | 0.670 | 0.924 | 1.165 |
| bathing_quality_pooled · prima query, nuova istanza | 5 | 2.094 | 2.293 | 2.339 |
| bathing_quality_pooled · query con cache applicativa | 30 | 1.326 | 1.731 | 1.944 |
| bathing_samples_pooled · prima query, nuova istanza | 5 | 2.006 | 2.746 | 2.854 |
| bathing_samples_pooled · query con cache applicativa | 30 | 1.124 | 1.956 | 3.301 |
| bathing_blue_history · prima query, nuova istanza | 5 | 2.735 | 3.199 | 3.265 |
| bathing_blue_history · query con cache applicativa | 30 | 1.704 | 2.220 | 2.819 |
| coast_protection_pooled · prima query, nuova istanza | 5 | 1.825 | 4.300 | 4.887 |
| coast_protection_pooled · query con cache applicativa | 30 | 1.219 | 3.532 | 4.532 |
| coast_dynamics_erosion_pooled · prima query, nuova istanza | 5 | 1.653 | 1.683 | 1.690 |
| coast_dynamics_erosion_pooled · query con cache applicativa | 30 | 1.220 | 1.616 | 1.991 |
| coast_mixed_universe_refused · prima query, nuova istanza | 5 | 1.026 | 1.062 | 1.067 |
| coast_mixed_universe_refused · query con cache applicativa | 30 | 0.686 | 0.949 | 1.018 |
| ifc_municipalFragility_series · prima query, nuova istanza | 5 | 2.193 | 2.523 | 2.572 |
| ifc_municipalFragility_series · query con cache applicativa | 30 | 1.159 | 2.039 | 2.176 |
| ifc_access_tuscany_gap · prima query, nuova istanza | 5 | 12.100 | 15.792 | 16.537 |
| ifc_access_tuscany_gap · query con cache applicativa | 30 | 7.313 | 8.798 | 13.060 |
| ifc_lowProductivityEmployment_relative_change_refused · prima query, nuova istanza | 5 | 1.040 | 1.256 | 1.277 |
| ifc_lowProductivityEmployment_relative_change_refused · query con cache applicativa | 30 | 0.662 | 1.032 | 1.174 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 2.247 | 4.082 | 4.476 |
| hazard_flood_pooled · query con cache applicativa | 30 | 1.116 | 1.651 | 1.786 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 2.002 | 2.557 | 2.675 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 1.288 | 1.975 | 2.011 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 4.031 | 4.520 | 4.628 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 2.715 | 3.385 | 4.895 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 2.341 | 4.606 | 4.620 |
| territory_protected_pooled · query con cache applicativa | 30 | 1.157 | 2.032 | 2.649 |
| territory_network_pooled · prima query, nuova istanza | 5 | 2.089 | 2.350 | 2.409 |
| territory_network_pooled · query con cache applicativa | 30 | 1.032 | 1.608 | 1.762 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 2.963 | 3.743 | 3.886 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 2.044 | 2.738 | 3.366 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 2.440 | 3.070 | 3.094 |
| soil_stock_pooled · query con cache applicativa | 30 | 1.068 | 1.801 | 1.893 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 2.113 | 2.386 | 2.394 |
| soil_ucs_pooled · query con cache applicativa | 30 | 1.026 | 1.573 | 1.807 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 2.940 | 3.151 | 3.189 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.698 | 2.158 | 2.749 |
| geography_density_pooled · prima query, nuova istanza | 5 | 3.574 | 7.606 | 8.487 |
| geography_density_pooled · query con cache applicativa | 30 | 1.506 | 4.078 | 4.600 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 2.184 | 2.962 | 3.051 |
| geography_forest_pooled · query con cache applicativa | 30 | 1.248 | 1.666 | 1.964 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 2.147 | 2.330 | 2.373 |
| geography_mixed_reference · query con cache applicativa | 30 | 1.667 | 2.242 | 2.437 |
| population_current · prima query, nuova istanza | 5 | 3.126 | 6.661 | 7.504 |
| population_current · query con cache applicativa | 30 | 1.077 | 2.425 | 2.864 |
| female_weighted · prima query, nuova istanza | 5 | 1.903 | 2.041 | 2.052 |
| female_weighted · query con cache applicativa | 30 | 1.367 | 2.585 | 3.900 |
| ars_gap · prima query, nuova istanza | 5 | 4.667 | 8.798 | 9.273 |
| ars_gap · query con cache applicativa | 30 | 1.068 | 1.800 | 2.142 |
| aligned_association · prima query, nuova istanza | 5 | 3.782 | 8.844 | 9.963 |
| aligned_association · query con cache applicativa | 30 | 2.217 | 3.070 | 4.208 |
| mismatched_association · prima query, nuova istanza | 5 | 3.791 | 7.518 | 7.804 |
| mismatched_association · query con cache applicativa | 30 | 1.778 | 8.422 | 13.675 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 6.088 | 9.474 | 10.254 |
| ars_hypertension_age · query con cache applicativa | 30 | 1.061 | 1.714 | 1.945 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 6.600 | 7.584 | 7.784 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.951 | 1.237 | 1.324 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 2.677 | 3.804 | 4.053 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 1.350 | 2.155 | 2.766 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 1.094 | 2.074 | 2.250 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.794 | 1.184 | 1.269 |
| census_young_employment · prima query, nuova istanza | 5 | 3.232 | 5.162 | 5.585 |
| census_young_employment · query con cache applicativa | 30 | 1.057 | 2.196 | 3.274 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 1.228 | 1.571 | 1.635 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.704 | 1.137 | 1.648 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 2.397 | 5.246 | 5.931 |
| finance_cash_weighted · query con cache applicativa | 30 | 1.307 | 4.305 | 6.648 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 2.584 | 4.745 | 5.028 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.764 | 1.334 | 1.846 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 3.214 | 9.046 | 10.460 |
| distinct_debt_weighted · query con cache applicativa | 30 | 1.409 | 2.062 | 2.664 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 1.010 | 1.127 | 1.147 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.668 | 0.904 | 1.328 |
| demography_dependency · prima query, nuova istanza | 5 | 39.694 | 58.395 | 62.494 |
| demography_dependency · query con cache applicativa | 30 | 1.623 | 2.279 | 3.285 |
| school_class_size · prima query, nuova istanza | 5 | 25.119 | 39.864 | 42.213 |
| school_class_size · query con cache applicativa | 30 | 1.192 | 2.792 | 4.557 |
| demography_aligned_events · prima query, nuova istanza | 5 | 26.072 | 35.923 | 36.981 |
| demography_aligned_events · query con cache applicativa | 30 | 2.297 | 3.250 | 3.860 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 1.032 | 1.347 | 1.399 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.743 | 1.313 | 2.009 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 50.181 | 53.657 | 53.722 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 1.213 | 2.216 | 2.671 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 54.239 | 56.530 | 57.095 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 1.333 | 1.715 | 2.838 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 54.578 | 55.451 | 55.529 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 1.339 | 1.919 | 1.974 |
| environment_water_pooled · prima query, nuova istanza | 5 | 2.979 | 3.916 | 4.075 |
| environment_water_pooled · query con cache applicativa | 30 | 1.237 | 1.816 | 2.391 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 25.838 | 40.129 | 42.225 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.948 | 1.418 | 3.083 |
| environment_cost_gap · prima query, nuova istanza | 5 | 1.857 | 2.065 | 2.090 |
| environment_cost_gap · query con cache applicativa | 30 | 0.956 | 1.464 | 1.720 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.871 | 2.036 | 2.063 |
| agriculture_pooled_size · query con cache applicativa | 30 | 1.247 | 1.655 | 2.218 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 2.111 | 2.552 | 2.628 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 1.179 | 1.979 | 2.675 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.895 | 2.109 | 2.155 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 1.226 | 2.475 | 7.986 |

Allocazioni Python: picco 27.459 MiB; mantenute 25.917 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
