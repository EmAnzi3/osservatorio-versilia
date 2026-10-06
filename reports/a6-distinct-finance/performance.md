# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `b2e3bc6a6da361705da3df84769810359b25b7d137f6428c09c5baa2cabffb8b`; domande `959466b0c41384db21621be0f132d4a41b81f461b5b1e09763e043554b4da811`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 139.126 | 204.886 | 219.026 |
| population_current · prima query, nuova istanza | 5 | 1.736 | 4.473 | 5.121 |
| population_current · query con cache applicativa | 50 | 0.360 | 0.582 | 0.712 |
| female_weighted · prima query, nuova istanza | 5 | 1.083 | 1.228 | 1.238 |
| female_weighted · query con cache applicativa | 50 | 0.724 | 1.300 | 1.367 |
| ars_gap · prima query, nuova istanza | 5 | 3.530 | 6.996 | 7.820 |
| ars_gap · query con cache applicativa | 50 | 0.327 | 0.474 | 0.604 |
| aligned_association · prima query, nuova istanza | 5 | 2.445 | 6.637 | 7.442 |
| aligned_association · query con cache applicativa | 50 | 1.560 | 1.653 | 1.839 |
| mismatched_association · prima query, nuova istanza | 5 | 3.199 | 6.096 | 6.625 |
| mismatched_association · query con cache applicativa | 50 | 1.040 | 1.106 | 1.422 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 4.725 | 6.518 | 6.876 |
| ars_hypertension_age · query con cache applicativa | 50 | 0.481 | 2.627 | 5.318 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.636 | 6.679 | 7.422 |
| ars_mortality_window_gap · query con cache applicativa | 50 | 0.498 | 0.557 | 0.940 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 2.017 | 2.336 | 2.371 |
| business_frame_industry_weighted · query con cache applicativa | 50 | 0.659 | 0.861 | 1.318 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.425 | 0.552 | 0.562 |
| business_endpoint_refused · query con cache applicativa | 50 | 0.165 | 0.334 | 0.468 |
| census_young_employment · prima query, nuova istanza | 5 | 1.470 | 1.992 | 2.068 |
| census_young_employment · query con cache applicativa | 50 | 0.352 | 2.314 | 2.879 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.463 | 0.492 | 0.499 |
| census_diploma_trend_refused · query con cache applicativa | 50 | 0.156 | 0.242 | 0.407 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 1.337 | 2.031 | 2.192 |
| finance_cash_weighted · query con cache applicativa | 50 | 0.553 | 0.611 | 0.967 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.895 | 3.637 | 4.038 |
| finance_benchmark_refused · query con cache applicativa | 50 | 0.248 | 0.313 | 0.551 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.655 | 2.762 | 2.783 |
| distinct_debt_weighted · query con cache applicativa | 50 | 0.630 | 0.969 | 1.056 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.403 | 0.493 | 0.493 |
| distinct_debt_osl_refused · query con cache applicativa | 50 | 0.183 | 0.336 | 0.408 |

Allocazioni Python: picco 23.003 MiB; mantenute 10.995 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
