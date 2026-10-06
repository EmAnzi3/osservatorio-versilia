# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `125a75cd5804984abd7aba6720fbb0992e4b749445927de47274ddf96c455c5a`; domande `e69b8963dd297f3d0cec0cb32f691e04885a14422abeff3b752ded7bcdf92ef0`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 146.722 | 202.593 | 210.261 |
| population_current · prima query, nuova istanza | 5 | 2.697 | 5.590 | 5.838 |
| population_current · query con cache applicativa | 30 | 0.454 | 0.812 | 0.885 |
| female_weighted · prima query, nuova istanza | 5 | 1.093 | 4.029 | 4.762 |
| female_weighted · query con cache applicativa | 30 | 0.577 | 0.847 | 0.914 |
| ars_gap · prima query, nuova istanza | 5 | 5.712 | 7.645 | 7.988 |
| ars_gap · query con cache applicativa | 30 | 0.341 | 0.603 | 0.824 |
| aligned_association · prima query, nuova istanza | 5 | 3.200 | 8.073 | 8.980 |
| aligned_association · query con cache applicativa | 30 | 1.272 | 1.939 | 2.196 |
| mismatched_association · prima query, nuova istanza | 5 | 2.508 | 6.730 | 7.737 |
| mismatched_association · query con cache applicativa | 30 | 0.832 | 1.017 | 1.437 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 4.108 | 7.192 | 7.776 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.504 | 0.615 | 1.168 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 5.161 | 12.469 | 14.255 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.441 | 0.766 | 0.895 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 1.912 | 2.243 | 2.252 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 0.671 | 1.537 | 2.201 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.579 | 1.044 | 1.092 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.244 | 0.417 | 0.450 |
| census_young_employment · prima query, nuova istanza | 5 | 1.870 | 2.287 | 2.365 |
| census_young_employment · query con cache applicativa | 30 | 0.429 | 0.888 | 1.978 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.518 | 0.542 | 0.546 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.246 | 0.392 | 0.496 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 1.818 | 2.362 | 2.424 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.636 | 0.938 | 1.327 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.555 | 2.162 | 2.192 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.219 | 0.487 | 0.601 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.176 | 3.098 | 3.328 |
| distinct_debt_weighted · query con cache applicativa | 30 | 0.830 | 1.296 | 1.418 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.703 | 1.060 | 1.119 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.217 | 0.499 | 1.168 |
| demography_dependency · prima query, nuova istanza | 5 | 25.797 | 29.838 | 29.992 |
| demography_dependency · query con cache applicativa | 30 | 0.510 | 1.013 | 1.378 |
| school_class_size · prima query, nuova istanza | 5 | 22.222 | 29.388 | 30.675 |
| school_class_size · query con cache applicativa | 30 | 0.488 | 0.644 | 0.989 |
| demography_aligned_events · prima query, nuova istanza | 5 | 25.574 | 30.409 | 31.408 |
| demography_aligned_events · query con cache applicativa | 30 | 1.518 | 1.865 | 1.959 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.527 | 0.774 | 0.812 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.261 | 0.564 | 0.801 |

Allocazioni Python: picco 23.003 MiB; mantenute 15.091 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
