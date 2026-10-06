# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `829729571daaaaa3052aa549f72ecd14562838c57345e12ff645ce5e6be5eeca`; domande `1faf84e7cac1ab4164fde22b4769ac572fa86b93df420cb7c3fa6be72b502440`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 144.444 | 168.136 | 171.373 |
| population_current · prima query, nuova istanza | 5 | 1.694 | 1.813 | 1.826 |
| population_current · query con cache applicativa | 30 | 0.375 | 0.539 | 0.693 |
| female_weighted · prima query, nuova istanza | 5 | 0.948 | 1.037 | 1.051 |
| female_weighted · query con cache applicativa | 30 | 0.532 | 0.708 | 0.944 |
| ars_gap · prima query, nuova istanza | 5 | 3.279 | 4.876 | 4.908 |
| ars_gap · query con cache applicativa | 30 | 0.357 | 0.409 | 0.683 |
| aligned_association · prima query, nuova istanza | 5 | 2.309 | 3.926 | 4.318 |
| aligned_association · query con cache applicativa | 30 | 1.027 | 1.079 | 1.454 |
| mismatched_association · prima query, nuova istanza | 5 | 1.934 | 4.602 | 4.652 |
| mismatched_association · query con cache applicativa | 30 | 0.707 | 0.847 | 1.073 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 3.131 | 6.205 | 6.606 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.451 | 0.711 | 1.067 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.112 | 5.175 | 5.659 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.398 | 0.661 | 0.717 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 1.513 | 1.591 | 1.603 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 0.582 | 0.754 | 0.940 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.474 | 0.483 | 0.484 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.240 | 0.466 | 0.514 |
| census_young_employment · prima query, nuova istanza | 5 | 1.682 | 2.151 | 2.211 |
| census_young_employment · query con cache applicativa | 30 | 0.600 | 0.670 | 0.979 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.438 | 0.585 | 0.606 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.230 | 0.318 | 0.469 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 1.583 | 1.836 | 1.888 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.653 | 0.723 | 3.655 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.283 | 2.088 | 2.116 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.248 | 0.300 | 0.588 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.088 | 2.201 | 2.211 |
| distinct_debt_weighted · query con cache applicativa | 30 | 0.707 | 2.292 | 2.900 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.472 | 0.614 | 0.647 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.233 | 0.462 | 0.777 |
| demography_dependency · prima query, nuova istanza | 5 | 21.768 | 37.326 | 38.713 |
| demography_dependency · query con cache applicativa | 30 | 0.411 | 0.509 | 0.804 |
| school_class_size · prima query, nuova istanza | 5 | 20.771 | 29.172 | 30.449 |
| school_class_size · query con cache applicativa | 30 | 0.582 | 0.757 | 0.922 |
| demography_aligned_events · prima query, nuova istanza | 5 | 22.052 | 33.607 | 34.938 |
| demography_aligned_events · query con cache applicativa | 30 | 2.042 | 2.095 | 2.485 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.513 | 0.657 | 0.687 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.234 | 0.291 | 0.507 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 39.941 | 47.710 | 48.862 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 0.618 | 1.035 | 1.309 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 40.511 | 45.454 | 45.795 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 0.580 | 0.947 | 1.279 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 43.580 | 47.125 | 47.260 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 0.767 | 1.687 | 2.378 |
| environment_water_pooled · prima query, nuova istanza | 5 | 1.667 | 1.907 | 1.957 |
| environment_water_pooled · query con cache applicativa | 30 | 0.773 | 0.815 | 1.197 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 18.510 | 21.152 | 21.759 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.419 | 0.815 | 0.876 |
| environment_cost_gap · prima query, nuova istanza | 5 | 0.847 | 0.960 | 0.965 |
| environment_cost_gap · query con cache applicativa | 30 | 0.331 | 0.446 | 0.699 |

Allocazioni Python: picco 23.003 MiB; mantenute 20.133 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
