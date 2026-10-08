# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `aa1bc0f59febae822a4915973931d434f67bf5dd01e32deea44f0b98e94eb967`; domande `6d31f1aa6d5c52f2dafae73aceb3b8f569f7eaa7a5df61c9f66de5fcd53a5129`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "fragilityAdapterSha256": "b1b104bb69ebbb5dfecd9061955b6113b342f583746e43eb12986a719fefd76e", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 172.074 | 201.407 | 207.069 |
| ifc_municipalFragility_series · prima query, nuova istanza | 5 | 1.645 | 1.778 | 1.808 |
| ifc_municipalFragility_series · query con cache applicativa | 30 | 0.781 | 1.229 | 1.570 |
| ifc_access_tuscany_gap · prima query, nuova istanza | 5 | 12.824 | 16.574 | 17.452 |
| ifc_access_tuscany_gap · query con cache applicativa | 30 | 7.774 | 8.104 | 8.370 |
| ifc_lowProductivityEmployment_relative_change_refused · prima query, nuova istanza | 5 | 0.553 | 0.814 | 0.827 |
| ifc_lowProductivityEmployment_relative_change_refused · query con cache applicativa | 30 | 0.353 | 0.587 | 0.999 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 1.468 | 1.638 | 1.646 |
| hazard_flood_pooled · query con cache applicativa | 30 | 0.903 | 1.051 | 1.308 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 1.644 | 1.772 | 1.787 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 0.989 | 1.157 | 1.371 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 2.851 | 3.577 | 3.593 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 1.816 | 2.230 | 2.443 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 1.313 | 1.751 | 1.803 |
| territory_protected_pooled · query con cache applicativa | 30 | 0.529 | 0.607 | 1.023 |
| territory_network_pooled · prima query, nuova istanza | 5 | 1.221 | 1.580 | 1.660 |
| territory_network_pooled · query con cache applicativa | 30 | 0.505 | 0.868 | 1.154 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 2.615 | 2.772 | 2.793 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 1.657 | 1.983 | 2.149 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.390 | 1.606 | 1.610 |
| soil_stock_pooled · query con cache applicativa | 30 | 0.720 | 0.814 | 1.141 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.126 | 1.308 | 1.352 |
| soil_ucs_pooled · query con cache applicativa | 30 | 0.498 | 0.572 | 0.894 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 1.923 | 2.024 | 2.038 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.072 | 1.346 | 1.552 |
| geography_density_pooled · prima query, nuova istanza | 5 | 3.474 | 5.266 | 5.587 |
| geography_density_pooled · query con cache applicativa | 30 | 0.983 | 1.309 | 2.377 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.542 | 1.677 | 1.690 |
| geography_forest_pooled · query con cache applicativa | 30 | 0.968 | 1.003 | 1.415 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 1.892 | 1.960 | 1.970 |
| geography_mixed_reference · query con cache applicativa | 30 | 1.319 | 1.401 | 1.585 |
| population_current · prima query, nuova istanza | 5 | 2.479 | 4.602 | 5.062 |
| population_current · query con cache applicativa | 30 | 0.501 | 0.775 | 0.849 |
| female_weighted · prima query, nuova istanza | 5 | 1.460 | 1.593 | 1.622 |
| female_weighted · query con cache applicativa | 30 | 0.990 | 1.147 | 1.365 |
| ars_gap · prima query, nuova istanza | 5 | 3.498 | 8.942 | 10.187 |
| ars_gap · query con cache applicativa | 30 | 0.484 | 0.765 | 0.929 |
| aligned_association · prima query, nuova istanza | 5 | 3.096 | 7.894 | 8.916 |
| aligned_association · query con cache applicativa | 30 | 1.784 | 1.932 | 2.220 |
| mismatched_association · prima query, nuova istanza | 5 | 3.560 | 9.524 | 10.941 |
| mismatched_association · query con cache applicativa | 30 | 0.936 | 1.171 | 1.217 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 4.742 | 10.255 | 11.539 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.761 | 1.231 | 1.327 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 4.346 | 6.760 | 7.180 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.816 | 2.814 | 3.586 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 1.737 | 2.583 | 2.598 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 1.051 | 1.283 | 1.613 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.708 | 0.860 | 0.861 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.472 | 0.669 | 1.778 |
| census_young_employment · prima query, nuova istanza | 5 | 1.680 | 1.902 | 1.913 |
| census_young_employment · query con cache applicativa | 30 | 0.628 | 0.863 | 0.992 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.820 | 1.048 | 1.102 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.461 | 0.788 | 1.732 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 2.134 | 12.875 | 15.523 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.677 | 1.125 | 1.395 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 2.165 | 2.203 | 2.206 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.351 | 0.444 | 0.646 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.162 | 2.837 | 2.973 |
| distinct_debt_weighted · query con cache applicativa | 30 | 0.747 | 1.149 | 1.436 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.615 | 0.804 | 0.843 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.354 | 0.616 | 0.951 |
| demography_dependency · prima query, nuova istanza | 5 | 24.148 | 37.156 | 38.446 |
| demography_dependency · query con cache applicativa | 30 | 0.790 | 0.980 | 1.228 |
| school_class_size · prima query, nuova istanza | 5 | 21.083 | 32.554 | 35.214 |
| school_class_size · query con cache applicativa | 30 | 0.739 | 1.011 | 1.042 |
| demography_aligned_events · prima query, nuova istanza | 5 | 29.520 | 33.763 | 34.233 |
| demography_aligned_events · query con cache applicativa | 30 | 2.195 | 2.426 | 2.575 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.640 | 0.766 | 0.789 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.411 | 0.680 | 0.801 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 64.014 | 69.465 | 70.229 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 0.810 | 1.212 | 1.828 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 58.333 | 84.388 | 90.791 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 1.041 | 1.094 | 1.325 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 56.947 | 71.925 | 72.255 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 1.003 | 1.069 | 1.731 |
| environment_water_pooled · prima query, nuova istanza | 5 | 1.724 | 2.546 | 2.571 |
| environment_water_pooled · query con cache applicativa | 30 | 0.623 | 0.735 | 1.068 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 18.466 | 23.117 | 23.256 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.545 | 0.883 | 0.898 |
| environment_cost_gap · prima query, nuova istanza | 5 | 1.029 | 1.116 | 1.127 |
| environment_cost_gap · query con cache applicativa | 30 | 0.501 | 0.715 | 0.865 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.175 | 3.027 | 3.484 |
| agriculture_pooled_size · query con cache applicativa | 30 | 0.710 | 0.965 | 1.147 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.301 | 1.456 | 1.466 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 0.707 | 1.072 | 1.175 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.116 | 1.209 | 1.219 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 0.693 | 1.130 | 2.290 |

Allocazioni Python: picco 23.003 MiB; mantenute 21.629 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
