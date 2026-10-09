# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `f2300394257117fae57c06f473cc8492e5bd1191cfd649da3575655d0faf434e`; domande `7f80211c30d575d110d43e88ee2a059c762859f92708fb3bc451d19cbbb2b705`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "agricultureProfileAdapterSha256": "3b65fa2c02807e5454d7e59110ab6ba0990a7272ca11014ef625a6088a3f3b86", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "bathingAdapterSha256": "562061699d57c58292c702e2598d883ee05348de649caad1c50f3719880285a4", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "classificationAdapterSha256": "b1b480a0e46be5f6d87819a22120969ce1f80dc591c5622339ba4a4fac674a01", "climateAdapterSha256": "62a385a9a49a9ef9e91dc3e25f6f77b2be3a6a259c38950fc493dcc0713c886f", "coastAdapterSha256": "1ace0bf132cfa6200b65997dd397e9e3ad47ae5f083e1d4fae33f878572fea09", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "extractiveAdapterSha256": "4261110cd0fadd43b8691be3f2da2d40a23e98fcbe11942af311ddce98490972", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "fragilityAdapterSha256": "b1b104bb69ebbb5dfecd9061955b6113b342f583746e43eb12986a719fefd76e", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "maritimeAdapterSha256": "bced33dc09761daa64e54ca69c35822ba603bbaebc370c3f9923ccf1eb6dd3e2", "pabAdapterSha256": "fad0391a396cf4e9a6ee32e1ac965fe4a10f3684fccc5d0690efd7435452a1b8", "remediationAdapterSha256": "303269e55e8d4f5a2275b45a96833df27fc755cd61b035feb38052883a673368", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97", "waterQualityAdapterSha256": "26a2406f232176661c63411a454bb051466af782a1d1c9db4e4ecf734ca394c7"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 180.366 | 218.076 | 225.341 |
| water_quality_case_rosse_5 · prima query, nuova istanza | 5 | 4.018 | 5.164 | 5.391 |
| water_quality_case_rosse_5 · query con cache applicativa | 30 | 1.960 | 3.194 | 4.545 |
| water_quality_localities_046030 · prima query, nuova istanza | 5 | 5.020 | 5.848 | 6.026 |
| water_quality_localities_046030 · query con cache applicativa | 30 | 4.038 | 6.325 | 9.312 |
| water_quality_weighted_ratio_refused · prima query, nuova istanza | 5 | 0.986 | 1.262 | 1.284 |
| water_quality_weighted_ratio_refused · query con cache applicativa | 30 | 0.631 | 1.275 | 1.440 |
| classification_part_coastalZone_046018 · prima query, nuova istanza | 5 | 2.610 | 3.691 | 3.742 |
| classification_part_coastalZone_046018 · query con cache applicativa | 30 | 2.444 | 3.045 | 11.545 |
| classification_total_rank_refused · prima query, nuova istanza | 5 | 1.244 | 2.137 | 2.349 |
| classification_total_rank_refused · query con cache applicativa | 30 | 0.959 | 1.488 | 1.864 |
| agriculture_profiles_female_pooled · prima query, nuova istanza | 5 | 4.120 | 5.411 | 5.730 |
| agriculture_profiles_female_pooled · query con cache applicativa | 30 | 4.099 | 5.997 | 15.957 |
| agriculture_profiles_organic_series · prima query, nuova istanza | 5 | 4.683 | 6.639 | 6.883 |
| agriculture_profiles_organic_series · query con cache applicativa | 30 | 4.319 | 9.612 | 15.490 |
| agriculture_profiles_organic_pooling_refused · prima query, nuova istanza | 5 | 1.303 | 1.528 | 1.569 |
| agriculture_profiles_organic_pooling_refused · query con cache applicativa | 30 | 1.008 | 1.464 | 2.453 |
| climate_temperature_current · prima query, nuova istanza | 5 | 3.804 | 5.284 | 5.411 |
| climate_temperature_current · query con cache applicativa | 30 | 2.859 | 7.018 | 17.761 |
| climate_tmin_annual_trend · prima query, nuova istanza | 5 | 10.338 | 29.982 | 31.712 |
| climate_tmin_annual_trend · query con cache applicativa | 30 | 7.227 | 10.240 | 11.871 |
| climate_precipitation_pooling_refused · prima query, nuova istanza | 5 | 1.420 | 2.913 | 3.259 |
| climate_precipitation_pooling_refused · query con cache applicativa | 30 | 1.001 | 1.630 | 2.415 |
| pab_pabProgrammedInterventions · prima query, nuova istanza | 5 | 51.476 | 81.207 | 87.139 |
| pab_pabProgrammedInterventions · query con cache applicativa | 30 | 15.624 | 24.105 | 29.291 |
| pab_pabInterventionsCompleted_share_pooled · prima query, nuova istanza | 5 | 40.843 | 133.334 | 154.832 |
| pab_pabInterventionsCompleted_share_pooled · query con cache applicativa | 30 | 13.637 | 19.935 | 22.880 |
| pab_approved_operational_refused · prima query, nuova istanza | 5 | 1.748 | 2.331 | 2.455 |
| pab_approved_operational_refused · query con cache applicativa | 30 | 0.582 | 1.021 | 1.264 |
| remediation_total · prima query, nuova istanza | 5 | 4.680 | 6.454 | 6.805 |
| remediation_total · query con cache applicativa | 30 | 4.633 | 9.338 | 11.828 |
| remediation_pooled · prima query, nuova istanza | 5 | 9.602 | 12.783 | 13.154 |
| remediation_pooled · query con cache applicativa | 30 | 3.551 | 6.452 | 6.776 |
| remediation_history_refused · prima query, nuova istanza | 5 | 1.027 | 1.660 | 1.775 |
| remediation_history_refused · query con cache applicativa | 30 | 0.735 | 1.123 | 1.668 |
| extractive_sites_active · prima query, nuova istanza | 5 | 4.602 | 5.875 | 6.026 |
| extractive_sites_active · query con cache applicativa | 30 | 1.989 | 2.980 | 4.635 |
| extractive_prc_pooled · prima query, nuova istanza | 5 | 5.824 | 7.227 | 7.518 |
| extractive_prc_pooled · query con cache applicativa | 30 | 3.839 | 7.546 | 11.994 |
| extractive_production_history · prima query, nuova istanza | 5 | 5.931 | 12.308 | 12.652 |
| extractive_production_history · query con cache applicativa | 30 | 4.205 | 8.278 | 9.086 |
| maritime_tourist_pooled · prima query, nuova istanza | 5 | 4.405 | 4.533 | 4.563 |
| maritime_tourist_pooled · query con cache applicativa | 30 | 3.624 | 4.666 | 5.186 |
| maritime_mean_due_pooled · prima query, nuova istanza | 5 | 4.741 | 6.575 | 7.020 |
| maritime_mean_due_pooled · query con cache applicativa | 30 | 3.690 | 4.649 | 4.838 |
| maritime_median_weighting_refused · prima query, nuova istanza | 5 | 1.412 | 20.294 | 24.589 |
| maritime_median_weighting_refused · query con cache applicativa | 30 | 1.107 | 8.032 | 39.209 |
| bathing_quality_pooled · prima query, nuova istanza | 5 | 7.767 | 19.565 | 20.914 |
| bathing_quality_pooled · query con cache applicativa | 30 | 11.926 | 52.411 | 61.814 |
| bathing_samples_pooled · prima query, nuova istanza | 5 | 3.277 | 21.569 | 26.007 |
| bathing_samples_pooled · query con cache applicativa | 30 | 1.794 | 4.145 | 9.226 |
| bathing_blue_history · prima query, nuova istanza | 5 | 4.356 | 5.416 | 5.494 |
| bathing_blue_history · query con cache applicativa | 30 | 2.854 | 3.975 | 4.115 |
| coast_protection_pooled · prima query, nuova istanza | 5 | 2.519 | 5.994 | 6.857 |
| coast_protection_pooled · query con cache applicativa | 30 | 1.961 | 2.738 | 3.447 |
| coast_dynamics_erosion_pooled · prima query, nuova istanza | 5 | 2.915 | 3.970 | 3.981 |
| coast_dynamics_erosion_pooled · query con cache applicativa | 30 | 1.621 | 2.446 | 2.626 |
| coast_mixed_universe_refused · prima query, nuova istanza | 5 | 1.485 | 2.477 | 2.502 |
| coast_mixed_universe_refused · query con cache applicativa | 30 | 0.670 | 1.185 | 1.616 |
| ifc_municipalFragility_series · prima query, nuova istanza | 5 | 1.779 | 2.167 | 2.191 |
| ifc_municipalFragility_series · query con cache applicativa | 30 | 1.217 | 2.015 | 2.428 |
| ifc_access_tuscany_gap · prima query, nuova istanza | 5 | 17.746 | 27.456 | 29.723 |
| ifc_access_tuscany_gap · query con cache applicativa | 30 | 8.624 | 18.335 | 29.642 |
| ifc_lowProductivityEmployment_relative_change_refused · prima query, nuova istanza | 5 | 1.222 | 2.951 | 3.233 |
| ifc_lowProductivityEmployment_relative_change_refused · query con cache applicativa | 30 | 0.764 | 1.217 | 1.526 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 1.908 | 4.130 | 4.613 |
| hazard_flood_pooled · query con cache applicativa | 30 | 7.710 | 18.025 | 23.453 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 1.898 | 3.628 | 4.013 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 1.759 | 3.037 | 4.667 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 6.860 | 7.870 | 7.966 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 13.050 | 28.805 | 45.291 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 2.525 | 11.932 | 14.238 |
| territory_protected_pooled · query con cache applicativa | 30 | 1.105 | 1.642 | 2.163 |
| territory_network_pooled · prima query, nuova istanza | 5 | 1.708 | 4.531 | 5.190 |
| territory_network_pooled · query con cache applicativa | 30 | 0.917 | 1.448 | 1.656 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 3.637 | 18.568 | 21.976 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 10.448 | 23.651 | 26.757 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.927 | 2.192 | 2.223 |
| soil_stock_pooled · query con cache applicativa | 30 | 1.148 | 2.088 | 2.730 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.950 | 2.055 | 2.057 |
| soil_ucs_pooled · query con cache applicativa | 30 | 1.121 | 2.153 | 2.787 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 6.087 | 19.020 | 22.231 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 2.977 | 4.184 | 4.331 |
| geography_density_pooled · prima query, nuova istanza | 5 | 6.413 | 8.854 | 9.033 |
| geography_density_pooled · query con cache applicativa | 30 | 2.553 | 18.392 | 21.674 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 3.811 | 17.796 | 18.382 |
| geography_forest_pooled · query con cache applicativa | 30 | 1.361 | 2.433 | 9.516 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 2.101 | 16.354 | 19.831 |
| geography_mixed_reference · query con cache applicativa | 30 | 1.840 | 2.692 | 5.645 |
| population_current · prima query, nuova istanza | 5 | 3.976 | 7.399 | 8.094 |
| population_current · query con cache applicativa | 30 | 1.057 | 1.772 | 1.875 |
| female_weighted · prima query, nuova istanza | 5 | 2.153 | 3.079 | 3.253 |
| female_weighted · query con cache applicativa | 30 | 1.906 | 3.331 | 3.970 |
| ars_gap · prima query, nuova istanza | 5 | 6.241 | 17.597 | 20.028 |
| ars_gap · query con cache applicativa | 30 | 1.191 | 1.931 | 2.380 |
| aligned_association · prima query, nuova istanza | 5 | 5.838 | 7.987 | 8.158 |
| aligned_association · query con cache applicativa | 30 | 2.092 | 2.917 | 3.170 |
| mismatched_association · prima query, nuova istanza | 5 | 5.498 | 16.902 | 18.173 |
| mismatched_association · query con cache applicativa | 30 | 1.654 | 3.782 | 6.248 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 6.438 | 8.993 | 9.564 |
| ars_hypertension_age · query con cache applicativa | 30 | 1.449 | 4.075 | 4.564 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 7.260 | 9.824 | 10.414 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 1.167 | 4.399 | 7.127 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 4.031 | 6.495 | 7.010 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 1.343 | 2.254 | 4.701 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 1.031 | 1.466 | 1.543 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.891 | 1.521 | 1.855 |
| census_young_employment · prima query, nuova istanza | 5 | 2.372 | 4.376 | 4.654 |
| census_young_employment · query con cache applicativa | 30 | 1.118 | 4.485 | 5.780 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 1.245 | 1.382 | 1.408 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.767 | 1.152 | 1.699 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 2.679 | 3.876 | 4.050 |
| finance_cash_weighted · query con cache applicativa | 30 | 1.046 | 1.885 | 3.822 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 2.208 | 2.654 | 2.694 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.818 | 1.630 | 2.662 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 3.421 | 4.451 | 4.631 |
| distinct_debt_weighted · query con cache applicativa | 30 | 1.309 | 2.321 | 2.611 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 1.363 | 1.693 | 1.741 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.662 | 0.964 | 1.103 |
| demography_dependency · prima query, nuova istanza | 5 | 26.573 | 30.739 | 31.198 |
| demography_dependency · query con cache applicativa | 30 | 1.092 | 1.417 | 1.731 |
| school_class_size · prima query, nuova istanza | 5 | 24.988 | 27.842 | 28.392 |
| school_class_size · query con cache applicativa | 30 | 1.212 | 1.632 | 2.115 |
| demography_aligned_events · prima query, nuova istanza | 5 | 27.067 | 28.388 | 28.464 |
| demography_aligned_events · query con cache applicativa | 30 | 2.333 | 3.042 | 3.269 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 1.224 | 3.137 | 3.589 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.709 | 1.044 | 1.228 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 52.018 | 56.997 | 57.723 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 1.149 | 2.464 | 2.839 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 53.860 | 70.544 | 74.240 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 1.238 | 1.554 | 2.420 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 53.652 | 71.163 | 72.656 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 1.318 | 2.038 | 2.110 |
| environment_water_pooled · prima query, nuova istanza | 5 | 3.069 | 3.110 | 3.112 |
| environment_water_pooled · query con cache applicativa | 30 | 1.149 | 1.891 | 2.263 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 25.752 | 56.313 | 61.699 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 1.025 | 2.482 | 5.208 |
| environment_cost_gap · prima query, nuova istanza | 5 | 1.694 | 2.319 | 2.459 |
| environment_cost_gap · query con cache applicativa | 30 | 0.826 | 1.100 | 1.272 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.876 | 2.184 | 2.216 |
| agriculture_pooled_size · query con cache applicativa | 30 | 1.467 | 6.751 | 7.889 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.878 | 4.682 | 5.351 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 1.153 | 1.473 | 2.019 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.574 | 2.112 | 2.218 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 1.078 | 1.589 | 2.681 |

Allocazioni Python: picco 27.404 MiB; mantenute 25.862 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
