# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `a3191eaac5e44a629c9e4607a10aed38cacf4d965e6b3436a29cf2d31d2c056f`; domande `66e25bf99cd890165147512f055882c4ac68c91745e46e9658d0e66c1b1e024a`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "bathingAdapterSha256": "562061699d57c58292c702e2598d883ee05348de649caad1c50f3719880285a4", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "coastAdapterSha256": "1ace0bf132cfa6200b65997dd397e9e3ad47ae5f083e1d4fae33f878572fea09", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "extractiveAdapterSha256": "4261110cd0fadd43b8691be3f2da2d40a23e98fcbe11942af311ddce98490972", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "fragilityAdapterSha256": "b1b104bb69ebbb5dfecd9061955b6113b342f583746e43eb12986a719fefd76e", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "maritimeAdapterSha256": "bced33dc09761daa64e54ca69c35822ba603bbaebc370c3f9923ccf1eb6dd3e2", "remediationAdapterSha256": "303269e55e8d4f5a2275b45a96833df27fc755cd61b035feb38052883a673368", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 113.825 | 118.135 | 118.911 |
| remediation_total · prima query, nuova istanza | 5 | 3.149 | 3.294 | 3.310 |
| remediation_total · query con cache applicativa | 30 | 1.939 | 2.433 | 2.628 |
| remediation_pooled · prima query, nuova istanza | 5 | 3.166 | 3.250 | 3.251 |
| remediation_pooled · query con cache applicativa | 30 | 1.882 | 2.213 | 2.320 |
| remediation_history_refused · prima query, nuova istanza | 5 | 0.667 | 0.732 | 0.748 |
| remediation_history_refused · query con cache applicativa | 30 | 0.402 | 0.548 | 0.716 |
| extractive_sites_active · prima query, nuova istanza | 5 | 2.166 | 2.443 | 2.456 |
| extractive_sites_active · query con cache applicativa | 30 | 1.183 | 1.458 | 1.617 |
| extractive_prc_pooled · prima query, nuova istanza | 5 | 3.468 | 3.741 | 3.792 |
| extractive_prc_pooled · query con cache applicativa | 30 | 2.433 | 4.798 | 4.953 |
| extractive_production_history · prima query, nuova istanza | 5 | 3.933 | 4.210 | 4.252 |
| extractive_production_history · query con cache applicativa | 30 | 2.525 | 3.172 | 3.445 |
| maritime_tourist_pooled · prima query, nuova istanza | 5 | 2.144 | 2.456 | 2.518 |
| maritime_tourist_pooled · query con cache applicativa | 30 | 1.429 | 1.749 | 1.891 |
| maritime_mean_due_pooled · prima query, nuova istanza | 5 | 2.003 | 2.172 | 2.190 |
| maritime_mean_due_pooled · query con cache applicativa | 30 | 1.781 | 2.507 | 2.786 |
| maritime_median_weighting_refused · prima query, nuova istanza | 5 | 0.722 | 0.863 | 0.872 |
| maritime_median_weighting_refused · query con cache applicativa | 30 | 0.432 | 0.692 | 0.750 |
| bathing_quality_pooled · prima query, nuova istanza | 5 | 1.373 | 1.469 | 1.471 |
| bathing_quality_pooled · query con cache applicativa | 30 | 0.828 | 1.102 | 1.206 |
| bathing_samples_pooled · prima query, nuova istanza | 5 | 1.386 | 1.437 | 1.449 |
| bathing_samples_pooled · query con cache applicativa | 30 | 0.799 | 1.560 | 1.632 |
| bathing_blue_history · prima query, nuova istanza | 5 | 2.050 | 4.079 | 4.511 |
| bathing_blue_history · query con cache applicativa | 30 | 1.220 | 1.585 | 1.668 |
| coast_protection_pooled · prima query, nuova istanza | 5 | 1.159 | 1.208 | 1.215 |
| coast_protection_pooled · query con cache applicativa | 30 | 0.630 | 0.929 | 1.152 |
| coast_dynamics_erosion_pooled · prima query, nuova istanza | 5 | 1.353 | 1.476 | 1.502 |
| coast_dynamics_erosion_pooled · query con cache applicativa | 30 | 0.708 | 1.053 | 1.123 |
| coast_mixed_universe_refused · prima query, nuova istanza | 5 | 0.672 | 0.707 | 0.715 |
| coast_mixed_universe_refused · query con cache applicativa | 30 | 0.432 | 0.718 | 0.816 |
| ifc_municipalFragility_series · prima query, nuova istanza | 5 | 1.363 | 1.788 | 1.835 |
| ifc_municipalFragility_series · query con cache applicativa | 30 | 0.727 | 0.883 | 1.749 |
| ifc_access_tuscany_gap · prima query, nuova istanza | 5 | 9.484 | 14.068 | 14.274 |
| ifc_access_tuscany_gap · query con cache applicativa | 30 | 5.125 | 6.342 | 7.224 |
| ifc_lowProductivityEmployment_relative_change_refused · prima query, nuova istanza | 5 | 0.738 | 0.988 | 1.006 |
| ifc_lowProductivityEmployment_relative_change_refused · query con cache applicativa | 30 | 0.403 | 0.520 | 0.686 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 1.244 | 1.588 | 1.665 |
| hazard_flood_pooled · query con cache applicativa | 30 | 0.698 | 0.937 | 1.061 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 1.272 | 1.420 | 1.448 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 0.713 | 0.890 | 1.109 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 2.491 | 2.919 | 3.004 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 2.797 | 3.764 | 5.219 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 1.483 | 1.554 | 1.571 |
| territory_protected_pooled · query con cache applicativa | 30 | 0.633 | 0.944 | 1.114 |
| territory_network_pooled · prima query, nuova istanza | 5 | 1.355 | 1.773 | 1.822 |
| territory_network_pooled · query con cache applicativa | 30 | 0.576 | 0.704 | 1.061 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 2.057 | 2.672 | 2.723 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 1.771 | 1.847 | 2.298 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.355 | 1.858 | 1.948 |
| soil_stock_pooled · query con cache applicativa | 30 | 0.584 | 0.935 | 0.975 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.131 | 1.350 | 1.393 |
| soil_ucs_pooled · query con cache applicativa | 30 | 0.606 | 0.769 | 1.079 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 1.942 | 2.117 | 2.153 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.061 | 1.314 | 1.481 |
| geography_density_pooled · prima query, nuova istanza | 5 | 2.354 | 4.754 | 5.337 |
| geography_density_pooled · query con cache applicativa | 30 | 0.841 | 1.025 | 1.375 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.266 | 1.316 | 1.323 |
| geography_forest_pooled · query con cache applicativa | 30 | 0.796 | 2.975 | 3.893 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 1.507 | 1.709 | 1.751 |
| geography_mixed_reference · query con cache applicativa | 30 | 0.985 | 1.225 | 1.540 |
| population_current · prima query, nuova istanza | 5 | 1.841 | 4.133 | 4.700 |
| population_current · query con cache applicativa | 30 | 0.595 | 0.734 | 0.939 |
| female_weighted · prima query, nuova istanza | 5 | 1.290 | 1.530 | 1.554 |
| female_weighted · query con cache applicativa | 30 | 0.817 | 1.193 | 1.385 |
| ars_gap · prima query, nuova istanza | 5 | 4.107 | 5.346 | 5.641 |
| ars_gap · query con cache applicativa | 30 | 0.555 | 0.712 | 1.006 |
| aligned_association · prima query, nuova istanza | 5 | 2.840 | 5.483 | 6.142 |
| aligned_association · query con cache applicativa | 30 | 1.284 | 1.695 | 1.766 |
| mismatched_association · prima query, nuova istanza | 5 | 3.185 | 4.453 | 4.659 |
| mismatched_association · query con cache applicativa | 30 | 1.413 | 1.561 | 1.939 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 3.234 | 5.563 | 5.991 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.636 | 0.865 | 1.030 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.452 | 7.899 | 8.608 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.870 | 1.973 | 4.114 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 2.859 | 3.052 | 3.090 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 1.172 | 1.344 | 1.732 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.856 | 0.969 | 0.979 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.427 | 0.581 | 0.750 |
| census_young_employment · prima query, nuova istanza | 5 | 1.672 | 1.747 | 1.749 |
| census_young_employment · query con cache applicativa | 30 | 0.603 | 0.781 | 1.148 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.755 | 0.790 | 0.794 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.418 | 0.738 | 1.193 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 2.119 | 2.380 | 2.430 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.628 | 0.894 | 1.086 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.532 | 1.645 | 1.652 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.489 | 0.730 | 1.000 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.263 | 2.438 | 2.445 |
| distinct_debt_weighted · query con cache applicativa | 30 | 1.197 | 2.279 | 3.056 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.941 | 1.101 | 1.132 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.415 | 0.524 | 0.679 |
| demography_dependency · prima query, nuova istanza | 5 | 19.758 | 29.734 | 31.126 |
| demography_dependency · query con cache applicativa | 30 | 0.618 | 0.915 | 1.082 |
| school_class_size · prima query, nuova istanza | 5 | 18.564 | 21.223 | 21.340 |
| school_class_size · query con cache applicativa | 30 | 0.676 | 0.949 | 1.109 |
| demography_aligned_events · prima query, nuova istanza | 5 | 19.468 | 24.565 | 25.475 |
| demography_aligned_events · query con cache applicativa | 30 | 1.600 | 2.068 | 2.194 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.824 | 0.886 | 0.901 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.435 | 0.596 | 0.786 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 38.806 | 41.348 | 41.628 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 0.729 | 0.873 | 1.198 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 39.867 | 49.673 | 51.723 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 0.810 | 1.147 | 1.255 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 39.423 | 41.771 | 42.037 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 0.845 | 1.037 | 1.469 |
| environment_water_pooled · prima query, nuova istanza | 5 | 1.816 | 2.020 | 2.028 |
| environment_water_pooled · query con cache applicativa | 30 | 0.703 | 0.947 | 1.024 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 17.311 | 19.473 | 19.680 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.586 | 0.761 | 0.902 |
| environment_cost_gap · prima query, nuova istanza | 5 | 1.097 | 1.189 | 1.211 |
| environment_cost_gap · query con cache applicativa | 30 | 0.593 | 0.922 | 2.425 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.303 | 2.068 | 2.213 |
| agriculture_pooled_size · query con cache applicativa | 30 | 0.764 | 0.960 | 1.338 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.262 | 1.659 | 1.737 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 0.803 | 1.144 | 1.469 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.184 | 1.232 | 1.242 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 0.731 | 0.963 | 1.099 |

Allocazioni Python: picco 23.570 MiB; mantenute 22.029 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
