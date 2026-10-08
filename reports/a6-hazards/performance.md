# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `eda81f13615158cd06184303e7b610ec777a450c05868c260341b98d8fc32ca2`; domande `1dc822e514f5a4038c91b8131cdedf11d5b08021963b4a594abb5aee3ff73bb2`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 117.621 | 157.964 | 167.633 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 1.607 | 4.282 | 4.945 |
| hazard_flood_pooled · query con cache applicativa | 30 | 0.643 | 0.980 | 1.938 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 1.494 | 1.656 | 1.681 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 0.664 | 0.986 | 1.105 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 2.583 | 2.769 | 2.802 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 1.740 | 1.983 | 2.326 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 1.220 | 1.250 | 1.255 |
| territory_protected_pooled · query con cache applicativa | 30 | 0.522 | 0.821 | 0.929 |
| territory_network_pooled · prima query, nuova istanza | 5 | 1.147 | 1.225 | 1.229 |
| territory_network_pooled · query con cache applicativa | 30 | 0.481 | 0.652 | 0.858 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 2.042 | 2.819 | 2.848 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 1.125 | 1.601 | 1.814 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.706 | 1.811 | 1.816 |
| soil_stock_pooled · query con cache applicativa | 30 | 0.707 | 0.892 | 1.222 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.059 | 1.739 | 1.809 |
| soil_ucs_pooled · query con cache applicativa | 30 | 0.568 | 0.854 | 1.074 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 2.118 | 2.799 | 2.830 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.036 | 1.287 | 1.417 |
| geography_density_pooled · prima query, nuova istanza | 5 | 2.494 | 5.208 | 5.726 |
| geography_density_pooled · query con cache applicativa | 30 | 0.781 | 1.031 | 1.355 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.185 | 1.288 | 1.308 |
| geography_forest_pooled · query con cache applicativa | 30 | 0.635 | 0.828 | 1.000 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 1.634 | 1.956 | 1.958 |
| geography_mixed_reference · query con cache applicativa | 30 | 0.899 | 1.350 | 1.575 |
| population_current · prima query, nuova istanza | 5 | 1.836 | 4.933 | 5.637 |
| population_current · query con cache applicativa | 30 | 0.495 | 0.738 | 0.955 |
| female_weighted · prima query, nuova istanza | 5 | 1.410 | 1.543 | 1.551 |
| female_weighted · query con cache applicativa | 30 | 0.705 | 1.137 | 1.205 |
| ars_gap · prima query, nuova istanza | 5 | 3.744 | 6.183 | 6.770 |
| ars_gap · query con cache applicativa | 30 | 0.514 | 0.644 | 0.838 |
| aligned_association · prima query, nuova istanza | 5 | 2.798 | 5.538 | 6.189 |
| aligned_association · query con cache applicativa | 30 | 1.207 | 1.526 | 1.756 |
| mismatched_association · prima query, nuova istanza | 5 | 2.472 | 7.573 | 8.587 |
| mismatched_association · query con cache applicativa | 30 | 0.971 | 1.299 | 1.436 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 3.340 | 5.984 | 6.406 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.549 | 0.929 | 0.988 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.330 | 8.471 | 9.650 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.542 | 1.524 | 3.564 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 1.629 | 1.736 | 1.756 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 0.651 | 0.706 | 1.062 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.652 | 0.824 | 0.839 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.458 | 0.523 | 0.832 |
| census_young_employment · prima query, nuova istanza | 5 | 2.404 | 2.461 | 2.466 |
| census_young_employment · query con cache applicativa | 30 | 0.730 | 0.888 | 1.163 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.824 | 1.040 | 1.094 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.467 | 0.541 | 0.848 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 2.369 | 2.498 | 2.499 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.789 | 0.880 | 1.262 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 2.173 | 2.418 | 2.470 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.338 | 0.522 | 0.648 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 3.141 | 3.245 | 3.256 |
| distinct_debt_weighted · query con cache applicativa | 30 | 0.733 | 1.099 | 1.178 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.796 | 0.904 | 0.926 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.461 | 0.618 | 1.094 |
| demography_dependency · prima query, nuova istanza | 5 | 36.035 | 44.870 | 46.868 |
| demography_dependency · query con cache applicativa | 30 | 0.778 | 1.023 | 1.345 |
| school_class_size · prima query, nuova istanza | 5 | 31.014 | 32.410 | 32.455 |
| school_class_size · query con cache applicativa | 30 | 0.915 | 1.153 | 1.410 |
| demography_aligned_events · prima query, nuova istanza | 5 | 33.537 | 34.450 | 34.607 |
| demography_aligned_events · query con cache applicativa | 30 | 1.746 | 2.954 | 3.586 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.937 | 1.017 | 1.035 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.481 | 0.612 | 0.861 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 63.963 | 87.679 | 88.134 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 1.043 | 1.549 | 2.724 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 59.360 | 82.426 | 82.543 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 0.929 | 1.245 | 3.404 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 67.207 | 89.892 | 90.940 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 0.887 | 1.438 | 2.111 |
| environment_water_pooled · prima query, nuova istanza | 5 | 1.715 | 3.506 | 3.819 |
| environment_water_pooled · query con cache applicativa | 30 | 0.616 | 1.109 | 1.526 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 18.446 | 21.266 | 21.905 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.513 | 0.791 | 0.836 |
| environment_cost_gap · prima query, nuova istanza | 5 | 1.219 | 1.492 | 1.538 |
| environment_cost_gap · query con cache applicativa | 30 | 0.705 | 1.042 | 1.213 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.365 | 1.616 | 1.632 |
| agriculture_pooled_size · query con cache applicativa | 30 | 0.655 | 0.939 | 1.175 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.583 | 1.843 | 1.890 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 1.003 | 1.222 | 1.468 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.033 | 1.111 | 1.111 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 0.625 | 0.905 | 1.325 |

Allocazioni Python: picco 23.003 MiB; mantenute 20.357 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
