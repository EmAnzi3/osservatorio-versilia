# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `a3eec825f5ca8bb6d093df3a4d2b9e3a2fbdb2a8dd8be92c86965daeee9e59d9`; domande `1643facb34bf9ec0c3cd32884e407cfbb7223ec75881c6c5ad048fbc04e7fd5d`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "bathingAdapterSha256": "562061699d57c58292c702e2598d883ee05348de649caad1c50f3719880285a4", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "climateAdapterSha256": "62a385a9a49a9ef9e91dc3e25f6f77b2be3a6a259c38950fc493dcc0713c886f", "coastAdapterSha256": "1ace0bf132cfa6200b65997dd397e9e3ad47ae5f083e1d4fae33f878572fea09", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "extractiveAdapterSha256": "4261110cd0fadd43b8691be3f2da2d40a23e98fcbe11942af311ddce98490972", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "fragilityAdapterSha256": "b1b104bb69ebbb5dfecd9061955b6113b342f583746e43eb12986a719fefd76e", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "maritimeAdapterSha256": "bced33dc09761daa64e54ca69c35822ba603bbaebc370c3f9923ccf1eb6dd3e2", "pabAdapterSha256": "fad0391a396cf4e9a6ee32e1ac965fe4a10f3684fccc5d0690efd7435452a1b8", "remediationAdapterSha256": "303269e55e8d4f5a2275b45a96833df27fc755cd61b035feb38052883a673368", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 169.867 | 250.848 | 269.050 |
| climate_temperature_current · prima query, nuova istanza | 5 | 2.046 | 2.296 | 2.345 |
| climate_temperature_current · query con cache applicativa | 30 | 1.628 | 2.329 | 2.483 |
| climate_tmin_annual_trend · prima query, nuova istanza | 5 | 3.603 | 6.120 | 6.674 |
| climate_tmin_annual_trend · query con cache applicativa | 30 | 3.269 | 4.826 | 5.328 |
| climate_precipitation_pooling_refused · prima query, nuova istanza | 5 | 0.947 | 1.337 | 1.429 |
| climate_precipitation_pooling_refused · query con cache applicativa | 30 | 0.633 | 1.732 | 3.239 |
| pab_pabProgrammedInterventions · prima query, nuova istanza | 5 | 29.627 | 39.064 | 40.466 |
| pab_pabProgrammedInterventions · query con cache applicativa | 30 | 7.316 | 9.699 | 11.869 |
| pab_pabInterventionsCompleted_share_pooled · prima query, nuova istanza | 5 | 22.493 | 28.948 | 30.353 |
| pab_pabInterventionsCompleted_share_pooled · query con cache applicativa | 30 | 7.948 | 11.613 | 24.732 |
| pab_approved_operational_refused · prima query, nuova istanza | 5 | 1.274 | 1.702 | 1.760 |
| pab_approved_operational_refused · query con cache applicativa | 30 | 0.600 | 0.861 | 1.145 |
| remediation_total · prima query, nuova istanza | 5 | 5.346 | 5.665 | 5.706 |
| remediation_total · query con cache applicativa | 30 | 2.851 | 3.604 | 4.504 |
| remediation_pooled · prima query, nuova istanza | 5 | 5.104 | 6.091 | 6.285 |
| remediation_pooled · query con cache applicativa | 30 | 2.587 | 3.172 | 3.292 |
| remediation_history_refused · prima query, nuova istanza | 5 | 1.062 | 1.437 | 1.528 |
| remediation_history_refused · query con cache applicativa | 30 | 0.545 | 0.845 | 1.195 |
| extractive_sites_active · prima query, nuova istanza | 5 | 3.635 | 5.429 | 5.817 |
| extractive_sites_active · query con cache applicativa | 30 | 1.754 | 2.452 | 2.731 |
| extractive_prc_pooled · prima query, nuova istanza | 5 | 4.610 | 5.410 | 5.565 |
| extractive_prc_pooled · query con cache applicativa | 30 | 3.386 | 8.298 | 13.843 |
| extractive_production_history · prima query, nuova istanza | 5 | 4.756 | 5.062 | 5.095 |
| extractive_production_history · query con cache applicativa | 30 | 3.419 | 4.342 | 4.667 |
| maritime_tourist_pooled · prima query, nuova istanza | 5 | 2.848 | 2.914 | 2.921 |
| maritime_tourist_pooled · query con cache applicativa | 30 | 2.076 | 2.584 | 2.715 |
| maritime_mean_due_pooled · prima query, nuova istanza | 5 | 3.056 | 3.844 | 3.935 |
| maritime_mean_due_pooled · query con cache applicativa | 30 | 2.102 | 2.684 | 2.713 |
| maritime_median_weighting_refused · prima query, nuova istanza | 5 | 1.050 | 1.125 | 1.138 |
| maritime_median_weighting_refused · query con cache applicativa | 30 | 0.628 | 1.173 | 1.535 |
| bathing_quality_pooled · prima query, nuova istanza | 5 | 1.810 | 2.272 | 2.306 |
| bathing_quality_pooled · query con cache applicativa | 30 | 1.355 | 6.119 | 15.846 |
| bathing_samples_pooled · prima query, nuova istanza | 5 | 2.169 | 2.755 | 2.802 |
| bathing_samples_pooled · query con cache applicativa | 30 | 1.167 | 1.859 | 2.016 |
| bathing_blue_history · prima query, nuova istanza | 5 | 4.402 | 7.492 | 8.170 |
| bathing_blue_history · query con cache applicativa | 30 | 1.952 | 4.155 | 5.668 |
| coast_protection_pooled · prima query, nuova istanza | 5 | 2.429 | 3.636 | 3.800 |
| coast_protection_pooled · query con cache applicativa | 30 | 0.940 | 1.840 | 2.283 |
| coast_dynamics_erosion_pooled · prima query, nuova istanza | 5 | 1.975 | 2.438 | 2.544 |
| coast_dynamics_erosion_pooled · query con cache applicativa | 30 | 1.391 | 5.327 | 6.337 |
| coast_mixed_universe_refused · prima query, nuova istanza | 5 | 0.961 | 5.071 | 6.024 |
| coast_mixed_universe_refused · query con cache applicativa | 30 | 0.595 | 1.273 | 2.558 |
| ifc_municipalFragility_series · prima query, nuova istanza | 5 | 1.906 | 5.064 | 5.772 |
| ifc_municipalFragility_series · query con cache applicativa | 30 | 1.067 | 1.564 | 1.610 |
| ifc_access_tuscany_gap · prima query, nuova istanza | 5 | 16.066 | 18.710 | 18.821 |
| ifc_access_tuscany_gap · query con cache applicativa | 30 | 7.549 | 13.754 | 17.543 |
| ifc_lowProductivityEmployment_relative_change_refused · prima query, nuova istanza | 5 | 1.779 | 3.175 | 3.264 |
| ifc_lowProductivityEmployment_relative_change_refused · query con cache applicativa | 30 | 0.573 | 1.257 | 1.661 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 2.093 | 2.827 | 2.947 |
| hazard_flood_pooled · query con cache applicativa | 30 | 1.377 | 2.615 | 4.598 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 1.691 | 2.643 | 2.746 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 1.048 | 1.890 | 2.833 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 3.690 | 8.212 | 9.165 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 2.574 | 4.592 | 7.182 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 1.833 | 2.455 | 2.535 |
| territory_protected_pooled · query con cache applicativa | 30 | 1.158 | 2.530 | 3.935 |
| territory_network_pooled · prima query, nuova istanza | 5 | 1.819 | 2.462 | 2.565 |
| territory_network_pooled · query con cache applicativa | 30 | 0.819 | 1.177 | 1.376 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 3.319 | 5.013 | 5.419 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 1.673 | 2.227 | 3.150 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.833 | 3.545 | 3.817 |
| soil_stock_pooled · query con cache applicativa | 30 | 0.839 | 1.206 | 1.232 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.711 | 2.157 | 2.229 |
| soil_ucs_pooled · query con cache applicativa | 30 | 1.014 | 1.755 | 3.248 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 4.329 | 5.423 | 5.591 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.480 | 2.956 | 4.673 |
| geography_density_pooled · prima query, nuova istanza | 5 | 3.368 | 6.346 | 6.965 |
| geography_density_pooled · query con cache applicativa | 30 | 1.232 | 1.777 | 1.837 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.885 | 2.651 | 2.776 |
| geography_forest_pooled · query con cache applicativa | 30 | 1.040 | 1.747 | 2.283 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 2.014 | 2.240 | 2.262 |
| geography_mixed_reference · query con cache applicativa | 30 | 1.459 | 2.233 | 2.495 |
| population_current · prima query, nuova istanza | 5 | 3.097 | 5.317 | 5.823 |
| population_current · query con cache applicativa | 30 | 0.768 | 1.195 | 4.110 |
| female_weighted · prima query, nuova istanza | 5 | 1.663 | 2.059 | 2.138 |
| female_weighted · query con cache applicativa | 30 | 1.017 | 2.153 | 2.962 |
| ars_gap · prima query, nuova istanza | 5 | 5.259 | 11.521 | 11.957 |
| ars_gap · query con cache applicativa | 30 | 0.913 | 1.329 | 1.664 |
| aligned_association · prima query, nuova istanza | 5 | 4.305 | 7.277 | 7.997 |
| aligned_association · query con cache applicativa | 30 | 1.920 | 2.516 | 3.774 |
| mismatched_association · prima query, nuova istanza | 5 | 3.558 | 6.269 | 6.924 |
| mismatched_association · query con cache applicativa | 30 | 1.440 | 2.431 | 3.696 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 5.347 | 7.521 | 7.915 |
| ars_hypertension_age · query con cache applicativa | 30 | 1.078 | 1.491 | 1.524 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 5.496 | 7.456 | 7.946 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.967 | 2.399 | 12.980 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 2.825 | 4.249 | 4.584 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 1.258 | 1.773 | 3.778 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 1.208 | 1.373 | 1.398 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.651 | 1.100 | 1.172 |
| census_young_employment · prima query, nuova istanza | 5 | 2.709 | 3.012 | 3.025 |
| census_young_employment · query con cache applicativa | 30 | 0.863 | 1.374 | 1.565 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 1.168 | 1.418 | 1.456 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.560 | 1.068 | 1.263 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 2.325 | 3.235 | 3.386 |
| finance_cash_weighted · query con cache applicativa | 30 | 1.268 | 3.217 | 3.762 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 2.330 | 2.871 | 2.920 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.712 | 1.659 | 1.805 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.912 | 5.368 | 5.963 |
| distinct_debt_weighted · query con cache applicativa | 30 | 1.255 | 3.909 | 4.560 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 1.188 | 1.484 | 1.543 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.564 | 0.839 | 0.967 |
| demography_dependency · prima query, nuova istanza | 5 | 30.780 | 34.038 | 34.327 |
| demography_dependency · query con cache applicativa | 30 | 0.973 | 1.382 | 1.757 |
| school_class_size · prima query, nuova istanza | 5 | 23.414 | 25.936 | 26.222 |
| school_class_size · query con cache applicativa | 30 | 1.036 | 1.351 | 1.590 |
| demography_aligned_events · prima query, nuova istanza | 5 | 28.636 | 31.722 | 32.044 |
| demography_aligned_events · query con cache applicativa | 30 | 2.266 | 2.840 | 3.214 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 1.071 | 1.332 | 1.357 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.576 | 0.870 | 0.982 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 50.915 | 52.353 | 52.571 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 1.053 | 1.404 | 2.269 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 53.588 | 68.264 | 71.568 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 1.182 | 1.621 | 1.893 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 51.102 | 63.691 | 65.952 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 1.173 | 2.031 | 3.462 |
| environment_water_pooled · prima query, nuova istanza | 5 | 2.619 | 2.921 | 2.959 |
| environment_water_pooled · query con cache applicativa | 30 | 1.189 | 1.884 | 2.312 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 23.964 | 27.199 | 27.462 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.944 | 1.545 | 2.101 |
| environment_cost_gap · prima query, nuova istanza | 5 | 1.551 | 1.826 | 1.892 |
| environment_cost_gap · query con cache applicativa | 30 | 0.788 | 1.134 | 1.602 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 2.106 | 2.199 | 2.220 |
| agriculture_pooled_size · query con cache applicativa | 30 | 1.120 | 2.582 | 3.387 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.700 | 4.281 | 4.902 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 1.084 | 2.467 | 3.265 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.487 | 1.817 | 1.843 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 0.994 | 1.880 | 4.065 |

Allocazioni Python: picco 27.733 MiB; mantenute 26.191 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
