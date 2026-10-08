# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `7f288b4c820eac6c0457801368d0550e1bc2c1540b14f85d77d6112a374447d7`; domande `a255bc28fa35368e5f1a4beaa8ce1b4bc35fa87fa47949fcce6e602f93be3177`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 125.825 | 154.002 | 154.568 |
| geography_density_pooled · prima query, nuova istanza | 5 | 3.131 | 3.274 | 3.284 |
| geography_density_pooled · query con cache applicativa | 30 | 0.716 | 1.146 | 1.460 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.329 | 1.483 | 1.490 |
| geography_forest_pooled · query con cache applicativa | 30 | 0.669 | 1.036 | 1.224 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 1.790 | 1.847 | 1.856 |
| geography_mixed_reference · query con cache applicativa | 30 | 1.245 | 1.344 | 1.673 |
| population_current · prima query, nuova istanza | 5 | 2.626 | 6.098 | 6.962 |
| population_current · query con cache applicativa | 30 | 0.617 | 0.680 | 0.973 |
| female_weighted · prima query, nuova istanza | 5 | 1.410 | 1.412 | 1.412 |
| female_weighted · query con cache applicativa | 30 | 0.596 | 0.834 | 0.929 |
| ars_gap · prima query, nuova istanza | 5 | 4.720 | 5.448 | 5.610 |
| ars_gap · query con cache applicativa | 30 | 0.431 | 0.668 | 0.760 |
| aligned_association · prima query, nuova istanza | 5 | 2.350 | 5.887 | 6.377 |
| aligned_association · query con cache applicativa | 30 | 1.765 | 1.897 | 2.206 |
| mismatched_association · prima query, nuova istanza | 5 | 3.267 | 7.600 | 8.618 |
| mismatched_association · query con cache applicativa | 30 | 1.205 | 1.281 | 1.642 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 5.253 | 7.347 | 7.779 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.731 | 0.806 | 1.163 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.824 | 8.285 | 9.126 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.528 | 0.808 | 0.837 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 1.988 | 2.238 | 2.239 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 0.801 | 1.317 | 1.464 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.562 | 0.788 | 0.801 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.275 | 0.599 | 0.747 |
| census_young_employment · prima query, nuova istanza | 5 | 1.848 | 2.193 | 2.201 |
| census_young_employment · query con cache applicativa | 30 | 0.483 | 0.775 | 1.016 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.478 | 0.636 | 0.673 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.301 | 0.440 | 0.501 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 1.607 | 2.089 | 2.092 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.490 | 0.846 | 0.870 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.310 | 1.917 | 2.003 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.285 | 0.558 | 0.666 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 1.898 | 2.226 | 2.269 |
| distinct_debt_weighted · query con cache applicativa | 30 | 1.002 | 1.121 | 1.482 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.466 | 0.643 | 0.677 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.256 | 0.296 | 0.476 |
| demography_dependency · prima query, nuova istanza | 5 | 19.914 | 21.801 | 22.192 |
| demography_dependency · query con cache applicativa | 30 | 0.474 | 0.711 | 0.818 |
| school_class_size · prima query, nuova istanza | 5 | 24.997 | 29.723 | 29.898 |
| school_class_size · query con cache applicativa | 30 | 0.806 | 0.857 | 1.153 |
| demography_aligned_events · prima query, nuova istanza | 5 | 19.358 | 22.102 | 22.267 |
| demography_aligned_events · query con cache applicativa | 30 | 1.375 | 1.702 | 1.782 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.498 | 0.646 | 0.676 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.399 | 0.452 | 0.670 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 41.833 | 46.445 | 46.631 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 0.655 | 0.976 | 1.276 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 46.277 | 63.141 | 66.800 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 0.610 | 0.750 | 1.003 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 40.360 | 42.506 | 43.038 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 0.697 | 0.997 | 1.334 |
| environment_water_pooled · prima query, nuova istanza | 5 | 1.809 | 2.326 | 2.327 |
| environment_water_pooled · query con cache applicativa | 30 | 0.668 | 0.947 | 1.205 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 18.344 | 20.918 | 20.972 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.436 | 0.653 | 0.733 |
| environment_cost_gap · prima query, nuova istanza | 5 | 0.840 | 0.909 | 0.915 |
| environment_cost_gap · query con cache applicativa | 30 | 0.427 | 0.732 | 1.125 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.046 | 1.348 | 1.415 |
| agriculture_pooled_size · query con cache applicativa | 30 | 0.592 | 0.705 | 0.979 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.227 | 1.436 | 1.437 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 0.937 | 1.049 | 1.480 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 0.971 | 2.139 | 2.425 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 0.576 | 0.807 | 1.108 |

Allocazioni Python: picco 23.003 MiB; mantenute 20.179 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
