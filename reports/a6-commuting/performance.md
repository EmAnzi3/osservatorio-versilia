# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `8460471b538a3d7d0a54022e70c0bbf5a0ed9cb2c8459528c7bd2588158ac7c5`; domande `28ab2ef82dcd10396fa9cc613adae1b1ed3edc173a64ca205ae6213c139bee2c`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 186.674 | 270.758 | 291.324 |
| population_current · prima query, nuova istanza | 5 | 2.070 | 5.975 | 6.204 |
| population_current · query con cache applicativa | 30 | 0.548 | 1.289 | 1.304 |
| female_weighted · prima query, nuova istanza | 5 | 1.358 | 1.383 | 1.387 |
| female_weighted · query con cache applicativa | 30 | 0.709 | 0.788 | 1.161 |
| ars_gap · prima query, nuova istanza | 5 | 5.071 | 83.517 | 99.433 |
| ars_gap · query con cache applicativa | 30 | 0.512 | 0.780 | 0.987 |
| aligned_association · prima query, nuova istanza | 5 | 3.278 | 7.216 | 8.101 |
| aligned_association · query con cache applicativa | 30 | 1.671 | 2.077 | 2.157 |
| mismatched_association · prima query, nuova istanza | 5 | 3.274 | 12.060 | 12.868 |
| mismatched_association · query con cache applicativa | 30 | 0.827 | 1.069 | 1.257 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 4.287 | 14.683 | 17.200 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.683 | 1.553 | 2.651 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 4.794 | 47.506 | 57.942 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.560 | 0.984 | 1.700 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 2.040 | 3.207 | 3.344 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 0.733 | 1.253 | 1.433 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.747 | 2.218 | 2.550 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.305 | 0.361 | 0.648 |
| census_young_employment · prima query, nuova istanza | 5 | 2.127 | 2.396 | 2.427 |
| census_young_employment · query con cache applicativa | 30 | 0.432 | 0.639 | 1.029 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.628 | 0.689 | 0.695 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.212 | 0.352 | 0.585 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 3.119 | 4.223 | 4.377 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.631 | 0.710 | 0.945 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.979 | 2.202 | 2.218 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.280 | 0.845 | 0.907 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.846 | 5.923 | 6.683 |
| distinct_debt_weighted · query con cache applicativa | 30 | 0.891 | 1.081 | 1.529 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.625 | 0.707 | 0.716 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.264 | 0.334 | 2.755 |
| demography_dependency · prima query, nuova istanza | 5 | 31.392 | 32.581 | 32.603 |
| demography_dependency · query con cache applicativa | 30 | 0.449 | 0.726 | 0.907 |
| school_class_size · prima query, nuova istanza | 5 | 28.382 | 35.667 | 37.368 |
| school_class_size · query con cache applicativa | 30 | 0.647 | 1.075 | 7.389 |
| demography_aligned_events · prima query, nuova istanza | 5 | 34.391 | 36.544 | 36.962 |
| demography_aligned_events · query con cache applicativa | 30 | 1.608 | 2.073 | 2.196 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.838 | 0.913 | 0.915 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.327 | 0.469 | 0.639 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 50.424 | 57.055 | 57.858 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 0.787 | 0.938 | 1.220 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 62.398 | 74.219 | 75.485 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 0.712 | 1.078 | 1.404 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 66.874 | 69.947 | 70.426 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 0.980 | 1.384 | 4.326 |

Allocazioni Python: picco 23.003 MiB; mantenute 19.850 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
