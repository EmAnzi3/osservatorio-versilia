# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `616d4e0237237675e25ee5969e94cf92f05cf5d37bda7170c96d034f479d7cb4`; domande `b5f92ce8b30083108e54fa98faede85c946069f324d7cfd92e16924f2cc5a76f`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 119.407 | 152.965 | 154.642 |
| population_current · prima query, nuova istanza | 5 | 1.925 | 6.322 | 7.413 |
| population_current · query con cache applicativa | 30 | 0.455 | 0.768 | 0.877 |
| female_weighted · prima query, nuova istanza | 5 | 0.965 | 1.082 | 1.087 |
| female_weighted · query con cache applicativa | 30 | 0.848 | 2.029 | 2.870 |
| ars_gap · prima query, nuova istanza | 5 | 4.594 | 6.692 | 7.157 |
| ars_gap · query con cache applicativa | 30 | 0.571 | 0.645 | 0.947 |
| aligned_association · prima query, nuova istanza | 5 | 2.375 | 5.180 | 5.857 |
| aligned_association · query con cache applicativa | 30 | 1.088 | 1.386 | 2.265 |
| mismatched_association · prima query, nuova istanza | 5 | 1.966 | 5.526 | 6.274 |
| mismatched_association · query con cache applicativa | 30 | 0.747 | 0.985 | 1.110 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 3.335 | 5.367 | 5.871 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.458 | 0.566 | 0.810 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.046 | 4.994 | 5.403 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.422 | 0.560 | 0.718 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 1.683 | 2.616 | 2.694 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 0.594 | 0.821 | 0.947 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.460 | 0.516 | 0.526 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.256 | 0.734 | 0.826 |
| census_young_employment · prima query, nuova istanza | 5 | 1.533 | 2.041 | 2.103 |
| census_young_employment · query con cache applicativa | 30 | 0.413 | 0.617 | 0.745 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.433 | 0.444 | 0.445 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.242 | 0.334 | 0.485 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 1.346 | 1.415 | 1.417 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.454 | 0.531 | 0.782 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.206 | 1.263 | 1.273 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.270 | 1.033 | 1.953 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 1.758 | 1.870 | 1.893 |
| distinct_debt_weighted · query con cache applicativa | 30 | 0.610 | 0.778 | 0.925 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.439 | 0.700 | 0.762 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.272 | 0.458 | 0.602 |
| demography_dependency · prima query, nuova istanza | 5 | 22.082 | 27.549 | 28.352 |
| demography_dependency · query con cache applicativa | 30 | 0.487 | 0.957 | 1.296 |
| school_class_size · prima query, nuova istanza | 5 | 18.612 | 23.062 | 24.054 |
| school_class_size · query con cache applicativa | 30 | 0.499 | 0.694 | 0.922 |
| demography_aligned_events · prima query, nuova istanza | 5 | 20.835 | 22.573 | 22.883 |
| demography_aligned_events · query con cache applicativa | 30 | 1.306 | 1.635 | 1.816 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.487 | 0.520 | 0.528 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.253 | 0.544 | 0.657 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 38.938 | 39.725 | 39.800 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 0.565 | 0.862 | 0.955 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 40.017 | 41.624 | 41.858 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 0.575 | 0.773 | 0.924 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 38.727 | 39.910 | 40.106 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 0.654 | 1.077 | 1.171 |
| environment_water_pooled · prima query, nuova istanza | 5 | 1.523 | 1.885 | 1.903 |
| environment_water_pooled · query con cache applicativa | 30 | 0.541 | 0.824 | 0.852 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 18.830 | 35.499 | 37.228 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.459 | 0.724 | 0.833 |
| environment_cost_gap · prima query, nuova istanza | 5 | 0.802 | 1.065 | 1.115 |
| environment_cost_gap · query con cache applicativa | 30 | 0.366 | 0.540 | 0.633 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.072 | 1.554 | 1.647 |
| agriculture_pooled_size · query con cache applicativa | 30 | 0.578 | 0.856 | 1.815 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.010 | 1.089 | 1.098 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 0.593 | 0.818 | 1.011 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 0.863 | 0.950 | 0.970 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 0.550 | 0.771 | 0.818 |

Allocazioni Python: picco 23.003 MiB; mantenute 20.553 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
