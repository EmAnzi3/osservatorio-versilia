# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `8133982afc4a9335d9c0138035c8d1cc288f1654af41717123c551e754ad35a3`; domande `9d013206641a2898f7b6175e16a6ea43d4d0798f7a8e4b7cd5e39a48eae47bef`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "coastAdapterSha256": "1ace0bf132cfa6200b65997dd397e9e3ad47ae5f083e1d4fae33f878572fea09", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "fragilityAdapterSha256": "b1b104bb69ebbb5dfecd9061955b6113b342f583746e43eb12986a719fefd76e", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 136.654 | 194.002 | 204.720 |
| coast_protection_pooled · prima query, nuova istanza | 5 | 1.441 | 2.378 | 2.605 |
| coast_protection_pooled · query con cache applicativa | 30 | 0.659 | 1.996 | 2.708 |
| coast_dynamics_erosion_pooled · prima query, nuova istanza | 5 | 1.270 | 1.534 | 1.546 |
| coast_dynamics_erosion_pooled · query con cache applicativa | 30 | 0.621 | 0.952 | 1.030 |
| coast_mixed_universe_refused · prima query, nuova istanza | 5 | 0.583 | 0.761 | 0.798 |
| coast_mixed_universe_refused · query con cache applicativa | 30 | 0.342 | 0.582 | 0.614 |
| ifc_municipalFragility_series · prima query, nuova istanza | 5 | 1.703 | 1.925 | 1.980 |
| ifc_municipalFragility_series · query con cache applicativa | 30 | 0.728 | 0.974 | 1.130 |
| ifc_access_tuscany_gap · prima query, nuova istanza | 5 | 9.322 | 14.652 | 15.386 |
| ifc_access_tuscany_gap · query con cache applicativa | 30 | 7.908 | 10.250 | 12.344 |
| ifc_lowProductivityEmployment_relative_change_refused · prima query, nuova istanza | 5 | 0.696 | 0.767 | 0.778 |
| ifc_lowProductivityEmployment_relative_change_refused · query con cache applicativa | 30 | 0.513 | 0.603 | 0.676 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 1.388 | 1.550 | 1.566 |
| hazard_flood_pooled · query con cache applicativa | 30 | 0.608 | 0.937 | 0.998 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 1.372 | 1.558 | 1.603 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 1.006 | 1.049 | 1.472 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 2.569 | 3.477 | 3.696 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 1.714 | 2.087 | 2.249 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 1.272 | 1.549 | 1.590 |
| territory_protected_pooled · query con cache applicativa | 30 | 0.573 | 0.886 | 0.980 |
| territory_network_pooled · prima query, nuova istanza | 5 | 1.195 | 1.261 | 1.276 |
| territory_network_pooled · query con cache applicativa | 30 | 0.511 | 0.782 | 1.128 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 2.104 | 4.607 | 5.220 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 1.282 | 1.691 | 3.155 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.477 | 1.522 | 1.531 |
| soil_stock_pooled · query con cache applicativa | 30 | 0.600 | 0.838 | 1.109 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.066 | 1.547 | 1.666 |
| soil_ucs_pooled · query con cache applicativa | 30 | 0.544 | 0.799 | 0.925 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 1.894 | 2.125 | 2.152 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.034 | 1.440 | 2.684 |
| geography_density_pooled · prima query, nuova istanza | 5 | 2.590 | 6.094 | 6.524 |
| geography_density_pooled · query con cache applicativa | 30 | 0.853 | 1.109 | 1.335 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.358 | 1.650 | 1.684 |
| geography_forest_pooled · query con cache applicativa | 30 | 0.748 | 1.533 | 2.151 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 1.760 | 1.856 | 1.878 |
| geography_mixed_reference · query con cache applicativa | 30 | 1.025 | 1.401 | 1.798 |
| population_current · prima query, nuova istanza | 5 | 2.111 | 6.429 | 7.451 |
| population_current · query con cache applicativa | 30 | 0.583 | 0.888 | 1.411 |
| female_weighted · prima query, nuova istanza | 5 | 1.349 | 1.532 | 1.538 |
| female_weighted · query con cache applicativa | 30 | 0.723 | 1.212 | 1.330 |
| ars_gap · prima query, nuova istanza | 5 | 3.455 | 6.918 | 7.750 |
| ars_gap · query con cache applicativa | 30 | 0.505 | 0.881 | 0.996 |
| aligned_association · prima query, nuova istanza | 5 | 2.629 | 5.072 | 5.654 |
| aligned_association · query con cache applicativa | 30 | 1.281 | 1.497 | 1.857 |
| mismatched_association · prima query, nuova istanza | 5 | 2.397 | 5.721 | 6.530 |
| mismatched_association · query con cache applicativa | 30 | 0.952 | 1.473 | 1.812 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 3.394 | 7.552 | 8.588 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.827 | 1.182 | 1.513 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.542 | 6.828 | 7.536 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.640 | 1.044 | 1.207 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 1.977 | 2.210 | 2.228 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 0.794 | 1.077 | 1.148 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.668 | 0.892 | 0.920 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.382 | 0.675 | 0.746 |
| census_young_employment · prima query, nuova istanza | 5 | 1.797 | 2.017 | 2.048 |
| census_young_employment · query con cache applicativa | 30 | 0.530 | 0.808 | 1.004 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.672 | 0.731 | 0.733 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.355 | 0.598 | 0.720 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 1.697 | 1.759 | 1.769 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.602 | 0.719 | 1.136 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 2.017 | 2.488 | 2.554 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.510 | 0.596 | 1.113 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.864 | 3.002 | 3.007 |
| distinct_debt_weighted · query con cache applicativa | 30 | 1.082 | 1.246 | 1.612 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.855 | 0.874 | 0.874 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.466 | 0.618 | 0.806 |
| demography_dependency · prima query, nuova istanza | 5 | 32.206 | 38.681 | 40.201 |
| demography_dependency · query con cache applicativa | 30 | 0.819 | 1.241 | 1.814 |
| school_class_size · prima query, nuova istanza | 5 | 30.170 | 30.915 | 31.082 |
| school_class_size · query con cache applicativa | 30 | 0.679 | 0.888 | 1.235 |
| demography_aligned_events · prima query, nuova istanza | 5 | 21.625 | 41.619 | 43.372 |
| demography_aligned_events · query con cache applicativa | 30 | 2.354 | 2.507 | 3.069 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.766 | 0.897 | 0.905 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.389 | 1.843 | 4.130 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 70.688 | 77.698 | 78.339 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 1.046 | 1.219 | 1.611 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 70.098 | 71.001 | 71.058 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 0.818 | 1.168 | 1.329 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 68.510 | 78.773 | 80.149 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 1.236 | 1.308 | 1.749 |
| environment_water_pooled · prima query, nuova istanza | 5 | 2.921 | 3.046 | 3.048 |
| environment_water_pooled · query con cache applicativa | 30 | 0.969 | 1.145 | 1.463 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 29.869 | 30.633 | 30.707 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.795 | 0.863 | 1.205 |
| environment_cost_gap · prima query, nuova istanza | 5 | 1.275 | 1.421 | 1.427 |
| environment_cost_gap · query con cache applicativa | 30 | 0.508 | 0.674 | 1.014 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.418 | 1.758 | 1.779 |
| agriculture_pooled_size · query con cache applicativa | 30 | 1.095 | 1.282 | 1.595 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.211 | 1.554 | 1.634 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 1.062 | 1.252 | 1.496 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.127 | 1.232 | 1.246 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 0.659 | 1.029 | 1.095 |

Allocazioni Python: picco 23.003 MiB; mantenute 21.655 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
