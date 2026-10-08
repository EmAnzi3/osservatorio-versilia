# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `062c03ae279527b97a9f13f32b7a46c28350ee9aa9d36b2b1fb74875609a1957`; domande `2f37b92816c2db2768d8dd0c850cf365a841d10fd21476c9c4248a15b2306afd`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 123.052 | 139.288 | 142.236 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.070 | 1.289 | 1.301 |
| soil_stock_pooled · query con cache applicativa | 30 | 0.438 | 0.618 | 0.762 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.005 | 1.216 | 1.267 |
| soil_ucs_pooled · query con cache applicativa | 30 | 0.467 | 0.674 | 0.816 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 1.807 | 5.553 | 6.465 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.144 | 1.602 | 1.720 |
| geography_density_pooled · prima query, nuova istanza | 5 | 2.461 | 5.063 | 5.594 |
| geography_density_pooled · query con cache applicativa | 30 | 0.863 | 1.088 | 1.498 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.212 | 1.604 | 1.656 |
| geography_forest_pooled · query con cache applicativa | 30 | 0.590 | 0.934 | 0.961 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 1.646 | 3.066 | 3.230 |
| geography_mixed_reference · query con cache applicativa | 30 | 0.821 | 1.090 | 1.315 |
| population_current · prima query, nuova istanza | 5 | 1.793 | 5.293 | 5.994 |
| population_current · query con cache applicativa | 30 | 0.475 | 0.719 | 0.823 |
| female_weighted · prima query, nuova istanza | 5 | 1.201 | 1.600 | 1.606 |
| female_weighted · query con cache applicativa | 30 | 0.600 | 0.915 | 1.050 |
| ars_gap · prima query, nuova istanza | 5 | 4.462 | 7.872 | 8.517 |
| ars_gap · query con cache applicativa | 30 | 0.448 | 0.686 | 0.777 |
| aligned_association · prima query, nuova istanza | 5 | 2.555 | 9.737 | 11.491 |
| aligned_association · query con cache applicativa | 30 | 1.656 | 2.222 | 2.573 |
| mismatched_association · prima query, nuova istanza | 5 | 2.979 | 5.797 | 6.494 |
| mismatched_association · query con cache applicativa | 30 | 0.932 | 1.364 | 1.773 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 5.113 | 6.309 | 6.418 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.516 | 0.651 | 0.938 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.075 | 6.072 | 6.306 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.474 | 0.621 | 0.903 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 1.553 | 1.821 | 1.849 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 0.621 | 0.744 | 1.027 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.550 | 0.766 | 0.793 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.368 | 0.631 | 0.925 |
| census_young_employment · prima query, nuova istanza | 5 | 1.746 | 4.019 | 4.556 |
| census_young_employment · query con cache applicativa | 30 | 0.591 | 1.297 | 1.836 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.579 | 0.797 | 0.847 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.291 | 0.539 | 0.611 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 1.673 | 1.894 | 1.915 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.673 | 0.956 | 1.149 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.439 | 1.670 | 1.727 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.312 | 0.589 | 1.251 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.032 | 2.557 | 2.614 |
| distinct_debt_weighted · query con cache applicativa | 30 | 0.634 | 0.683 | 1.011 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.620 | 0.685 | 0.690 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.282 | 0.379 | 0.552 |
| demography_dependency · prima query, nuova istanza | 5 | 19.918 | 23.302 | 23.623 |
| demography_dependency · query con cache applicativa | 30 | 0.467 | 0.524 | 0.846 |
| school_class_size · prima query, nuova istanza | 5 | 21.127 | 21.872 | 22.001 |
| school_class_size · query con cache applicativa | 30 | 0.581 | 0.740 | 0.954 |
| demography_aligned_events · prima query, nuova istanza | 5 | 20.596 | 25.044 | 25.231 |
| demography_aligned_events · query con cache applicativa | 30 | 1.665 | 2.728 | 2.949 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.578 | 0.849 | 0.909 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.300 | 0.396 | 0.583 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 41.134 | 48.344 | 49.490 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 0.745 | 1.169 | 1.254 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 44.577 | 64.968 | 69.745 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 0.644 | 1.013 | 2.191 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 41.220 | 41.848 | 41.910 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 0.759 | 1.077 | 1.266 |
| environment_water_pooled · prima query, nuova istanza | 5 | 1.720 | 2.381 | 2.487 |
| environment_water_pooled · query con cache applicativa | 30 | 0.563 | 0.781 | 0.946 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 18.944 | 21.446 | 22.069 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.489 | 0.802 | 0.837 |
| environment_cost_gap · prima query, nuova istanza | 5 | 0.888 | 0.972 | 0.987 |
| environment_cost_gap · query con cache applicativa | 30 | 0.422 | 0.631 | 0.917 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.138 | 1.528 | 1.587 |
| agriculture_pooled_size · query con cache applicativa | 30 | 0.752 | 0.958 | 1.327 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.085 | 1.315 | 1.363 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 0.764 | 1.242 | 2.066 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.087 | 1.460 | 1.551 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 0.569 | 0.820 | 1.002 |

Allocazioni Python: picco 23.003 MiB; mantenute 20.301 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
