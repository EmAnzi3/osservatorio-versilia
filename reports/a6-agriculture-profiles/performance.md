# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `b893b9516c90100bb05126bb274de59c8be0c7aa0133e9dda38e3a8727b442fb`; domande `5226194349c3166750284b05b6e75ccf0ab3c0ea6c24229773635c631fd829a3`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "agricultureProfileAdapterSha256": "3b65fa2c02807e5454d7e59110ab6ba0990a7272ca11014ef625a6088a3f3b86", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "bathingAdapterSha256": "562061699d57c58292c702e2598d883ee05348de649caad1c50f3719880285a4", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "climateAdapterSha256": "62a385a9a49a9ef9e91dc3e25f6f77b2be3a6a259c38950fc493dcc0713c886f", "coastAdapterSha256": "1ace0bf132cfa6200b65997dd397e9e3ad47ae5f083e1d4fae33f878572fea09", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "extractiveAdapterSha256": "4261110cd0fadd43b8691be3f2da2d40a23e98fcbe11942af311ddce98490972", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "fragilityAdapterSha256": "b1b104bb69ebbb5dfecd9061955b6113b342f583746e43eb12986a719fefd76e", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "maritimeAdapterSha256": "bced33dc09761daa64e54ca69c35822ba603bbaebc370c3f9923ccf1eb6dd3e2", "pabAdapterSha256": "fad0391a396cf4e9a6ee32e1ac965fe4a10f3684fccc5d0690efd7435452a1b8", "remediationAdapterSha256": "303269e55e8d4f5a2275b45a96833df27fc755cd61b035feb38052883a673368", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 288.136 | 310.588 | 312.550 |
| agriculture_profiles_female_pooled · prima query, nuova istanza | 5 | 3.968 | 11.971 | 13.781 |
| agriculture_profiles_female_pooled · query con cache applicativa | 30 | 2.491 | 3.290 | 3.677 |
| agriculture_profiles_organic_series · prima query, nuova istanza | 5 | 3.199 | 7.633 | 8.573 |
| agriculture_profiles_organic_series · query con cache applicativa | 30 | 3.172 | 25.638 | 46.190 |
| agriculture_profiles_organic_pooling_refused · prima query, nuova istanza | 5 | 1.131 | 1.699 | 1.787 |
| agriculture_profiles_organic_pooling_refused · query con cache applicativa | 30 | 0.548 | 0.969 | 1.165 |
| climate_temperature_current · prima query, nuova istanza | 5 | 2.357 | 2.498 | 2.525 |
| climate_temperature_current · query con cache applicativa | 30 | 3.085 | 6.398 | 7.322 |
| climate_tmin_annual_trend · prima query, nuova istanza | 5 | 6.616 | 6.946 | 6.979 |
| climate_tmin_annual_trend · query con cache applicativa | 30 | 4.794 | 7.270 | 7.646 |
| climate_precipitation_pooling_refused · prima query, nuova istanza | 5 | 0.969 | 1.264 | 1.324 |
| climate_precipitation_pooling_refused · query con cache applicativa | 30 | 1.064 | 2.654 | 3.425 |
| pab_pabProgrammedInterventions · prima query, nuova istanza | 5 | 22.687 | 24.585 | 24.710 |
| pab_pabProgrammedInterventions · query con cache applicativa | 30 | 7.122 | 11.305 | 15.999 |
| pab_pabInterventionsCompleted_share_pooled · prima query, nuova istanza | 5 | 21.670 | 23.954 | 24.467 |
| pab_pabInterventionsCompleted_share_pooled · query con cache applicativa | 30 | 7.867 | 11.612 | 11.968 |
| pab_approved_operational_refused · prima query, nuova istanza | 5 | 1.359 | 1.544 | 1.579 |
| pab_approved_operational_refused · query con cache applicativa | 30 | 0.596 | 0.786 | 0.905 |
| remediation_total · prima query, nuova istanza | 5 | 7.902 | 9.577 | 9.878 |
| remediation_total · query con cache applicativa | 30 | 5.222 | 7.801 | 11.647 |
| remediation_pooled · prima query, nuova istanza | 5 | 5.647 | 7.661 | 7.675 |
| remediation_pooled · query con cache applicativa | 30 | 3.346 | 12.227 | 17.009 |
| remediation_history_refused · prima query, nuova istanza | 5 | 0.972 | 1.386 | 1.395 |
| remediation_history_refused · query con cache applicativa | 30 | 0.627 | 0.981 | 1.180 |
| extractive_sites_active · prima query, nuova istanza | 5 | 2.805 | 4.021 | 4.078 |
| extractive_sites_active · query con cache applicativa | 30 | 1.770 | 2.128 | 2.228 |
| extractive_prc_pooled · prima query, nuova istanza | 5 | 4.101 | 5.246 | 5.370 |
| extractive_prc_pooled · query con cache applicativa | 30 | 3.138 | 3.857 | 4.105 |
| extractive_production_history · prima query, nuova istanza | 5 | 4.596 | 4.929 | 4.970 |
| extractive_production_history · query con cache applicativa | 30 | 3.209 | 4.046 | 4.119 |
| maritime_tourist_pooled · prima query, nuova istanza | 5 | 2.434 | 3.371 | 3.589 |
| maritime_tourist_pooled · query con cache applicativa | 30 | 2.058 | 2.728 | 2.829 |
| maritime_mean_due_pooled · prima query, nuova istanza | 5 | 2.858 | 3.243 | 3.268 |
| maritime_mean_due_pooled · query con cache applicativa | 30 | 7.648 | 13.603 | 15.792 |
| maritime_median_weighting_refused · prima query, nuova istanza | 5 | 0.943 | 2.087 | 2.369 |
| maritime_median_weighting_refused · query con cache applicativa | 30 | 0.565 | 1.088 | 1.565 |
| bathing_quality_pooled · prima query, nuova istanza | 5 | 2.077 | 2.242 | 2.282 |
| bathing_quality_pooled · query con cache applicativa | 30 | 1.261 | 2.249 | 2.648 |
| bathing_samples_pooled · prima query, nuova istanza | 5 | 1.868 | 4.712 | 4.909 |
| bathing_samples_pooled · query con cache applicativa | 30 | 1.029 | 2.265 | 2.780 |
| bathing_blue_history · prima query, nuova istanza | 5 | 2.979 | 21.395 | 25.406 |
| bathing_blue_history · query con cache applicativa | 30 | 2.901 | 7.164 | 9.793 |
| coast_protection_pooled · prima query, nuova istanza | 5 | 1.526 | 2.878 | 2.970 |
| coast_protection_pooled · query con cache applicativa | 30 | 0.906 | 2.602 | 4.840 |
| coast_dynamics_erosion_pooled · prima query, nuova istanza | 5 | 1.573 | 4.368 | 5.037 |
| coast_dynamics_erosion_pooled · query con cache applicativa | 30 | 1.697 | 5.293 | 5.470 |
| coast_mixed_universe_refused · prima query, nuova istanza | 5 | 0.967 | 2.200 | 2.373 |
| coast_mixed_universe_refused · query con cache applicativa | 30 | 0.808 | 5.337 | 7.472 |
| ifc_municipalFragility_series · prima query, nuova istanza | 5 | 2.320 | 5.781 | 6.018 |
| ifc_municipalFragility_series · query con cache applicativa | 30 | 1.041 | 1.867 | 2.213 |
| ifc_access_tuscany_gap · prima query, nuova istanza | 5 | 29.333 | 38.344 | 40.093 |
| ifc_access_tuscany_gap · query con cache applicativa | 30 | 13.739 | 28.068 | 28.216 |
| ifc_lowProductivityEmployment_relative_change_refused · prima query, nuova istanza | 5 | 0.945 | 3.039 | 3.207 |
| ifc_lowProductivityEmployment_relative_change_refused · query con cache applicativa | 30 | 1.067 | 5.294 | 6.321 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 3.272 | 14.302 | 14.459 |
| hazard_flood_pooled · query con cache applicativa | 30 | 4.265 | 10.200 | 12.974 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 4.659 | 14.209 | 16.223 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 2.465 | 5.242 | 20.802 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 13.909 | 29.986 | 33.755 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 15.885 | 23.134 | 24.613 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 8.798 | 12.323 | 13.091 |
| territory_protected_pooled · query con cache applicativa | 30 | 2.683 | 10.075 | 13.183 |
| territory_network_pooled · prima query, nuova istanza | 5 | 2.272 | 6.366 | 7.193 |
| territory_network_pooled · query con cache applicativa | 30 | 0.961 | 2.135 | 3.843 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 3.357 | 5.717 | 6.141 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 2.472 | 5.124 | 5.299 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 2.940 | 4.686 | 4.720 |
| soil_stock_pooled · query con cache applicativa | 30 | 1.174 | 2.911 | 4.928 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 2.218 | 2.971 | 3.106 |
| soil_ucs_pooled · query con cache applicativa | 30 | 1.986 | 4.111 | 4.965 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 3.835 | 13.221 | 14.190 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.775 | 3.034 | 3.794 |
| geography_density_pooled · prima query, nuova istanza | 5 | 4.079 | 7.794 | 8.548 |
| geography_density_pooled · query con cache applicativa | 30 | 1.393 | 2.456 | 3.862 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 2.094 | 3.067 | 3.110 |
| geography_forest_pooled · query con cache applicativa | 30 | 1.603 | 3.522 | 7.377 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 2.435 | 3.222 | 3.391 |
| geography_mixed_reference · query con cache applicativa | 30 | 1.775 | 2.809 | 4.107 |
| population_current · prima query, nuova istanza | 5 | 3.467 | 9.862 | 11.402 |
| population_current · query con cache applicativa | 30 | 0.962 | 2.250 | 3.301 |
| female_weighted · prima query, nuova istanza | 5 | 1.666 | 2.046 | 2.115 |
| female_weighted · query con cache applicativa | 30 | 1.274 | 2.019 | 2.278 |
| ars_gap · prima query, nuova istanza | 5 | 5.522 | 13.855 | 14.027 |
| ars_gap · query con cache applicativa | 30 | 0.966 | 1.998 | 2.115 |
| aligned_association · prima query, nuova istanza | 5 | 4.497 | 11.867 | 12.025 |
| aligned_association · query con cache applicativa | 30 | 3.505 | 7.707 | 12.027 |
| mismatched_association · prima query, nuova istanza | 5 | 6.040 | 11.426 | 11.926 |
| mismatched_association · query con cache applicativa | 30 | 2.075 | 5.290 | 6.925 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 7.275 | 11.514 | 11.730 |
| ars_hypertension_age · query con cache applicativa | 30 | 1.156 | 2.221 | 2.738 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 6.854 | 9.334 | 9.789 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 1.062 | 1.858 | 2.205 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 2.810 | 3.446 | 3.589 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 1.478 | 2.326 | 2.794 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 1.360 | 2.229 | 2.432 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.762 | 1.649 | 1.964 |
| census_young_employment · prima query, nuova istanza | 5 | 5.995 | 8.873 | 9.323 |
| census_young_employment · query con cache applicativa | 30 | 1.339 | 2.878 | 3.028 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 1.186 | 2.219 | 2.345 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.609 | 0.994 | 1.288 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 2.596 | 4.903 | 5.462 |
| finance_cash_weighted · query con cache applicativa | 30 | 1.041 | 1.396 | 2.034 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 2.266 | 2.708 | 2.749 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.895 | 1.964 | 2.623 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 3.279 | 5.616 | 6.124 |
| distinct_debt_weighted · query con cache applicativa | 30 | 1.260 | 2.803 | 3.274 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 1.039 | 1.246 | 1.282 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.788 | 1.451 | 1.877 |
| demography_dependency · prima query, nuova istanza | 5 | 31.193 | 33.206 | 33.606 |
| demography_dependency · query con cache applicativa | 30 | 1.295 | 2.200 | 3.256 |
| school_class_size · prima query, nuova istanza | 5 | 25.154 | 35.561 | 37.386 |
| school_class_size · query con cache applicativa | 30 | 1.217 | 2.215 | 4.420 |
| demography_aligned_events · prima query, nuova istanza | 5 | 38.707 | 57.978 | 60.579 |
| demography_aligned_events · query con cache applicativa | 30 | 2.846 | 4.518 | 5.617 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 1.286 | 4.158 | 4.873 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.626 | 1.190 | 1.305 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 77.601 | 132.935 | 135.246 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 1.675 | 3.865 | 4.409 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 67.444 | 83.093 | 85.375 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 1.618 | 2.512 | 2.657 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 198.687 | 240.043 | 248.679 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 3.591 | 7.489 | 7.561 |
| environment_water_pooled · prima query, nuova istanza | 5 | 3.094 | 6.920 | 7.067 |
| environment_water_pooled · query con cache applicativa | 30 | 1.793 | 5.673 | 7.464 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 52.624 | 96.525 | 104.999 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 1.770 | 8.753 | 12.112 |
| environment_cost_gap · prima query, nuova istanza | 5 | 5.243 | 8.767 | 9.196 |
| environment_cost_gap · query con cache applicativa | 30 | 0.934 | 1.745 | 2.288 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 2.767 | 4.039 | 4.233 |
| agriculture_pooled_size · query con cache applicativa | 30 | 1.341 | 2.211 | 3.761 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 2.497 | 3.810 | 4.128 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 2.751 | 5.642 | 7.129 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 3.908 | 7.814 | 8.056 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 3.434 | 8.281 | 11.137 |

Allocazioni Python: picco 27.403 MiB; mantenute 25.862 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
