# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `64f5c7f86f3890697b5efd102c0c82ede7ec677a3bd2ce73f26ac0f80f016ce6`; domande `28a533536802700304b81b4f95e1a0f19a8f9c169da47d236b2f48c3443aa35c`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 119.827 | 180.269 | 186.684 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 1.351 | 1.759 | 1.769 |
| territory_protected_pooled · query con cache applicativa | 30 | 0.625 | 1.103 | 1.301 |
| territory_network_pooled · prima query, nuova istanza | 5 | 1.485 | 1.621 | 1.649 |
| territory_network_pooled · query con cache applicativa | 30 | 0.472 | 0.675 | 0.964 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 2.583 | 3.157 | 3.288 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 1.644 | 1.793 | 2.158 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.644 | 1.732 | 1.734 |
| soil_stock_pooled · query con cache applicativa | 30 | 0.672 | 0.727 | 1.169 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.022 | 1.318 | 1.371 |
| soil_ucs_pooled · query con cache applicativa | 30 | 0.476 | 0.757 | 0.838 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 1.893 | 1.977 | 1.990 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 0.981 | 1.365 | 1.419 |
| geography_density_pooled · prima query, nuova istanza | 5 | 2.447 | 5.888 | 6.677 |
| geography_density_pooled · query con cache applicativa | 30 | 0.817 | 1.122 | 1.327 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.116 | 1.586 | 1.601 |
| geography_forest_pooled · query con cache applicativa | 30 | 0.622 | 0.906 | 1.656 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 1.401 | 1.911 | 2.012 |
| geography_mixed_reference · query con cache applicativa | 30 | 1.314 | 1.478 | 1.887 |
| population_current · prima query, nuova istanza | 5 | 1.932 | 5.598 | 6.479 |
| population_current · query con cache applicativa | 30 | 0.484 | 0.657 | 1.851 |
| female_weighted · prima query, nuova istanza | 5 | 1.156 | 1.337 | 1.352 |
| female_weighted · query con cache applicativa | 30 | 0.626 | 0.741 | 0.990 |
| ars_gap · prima query, nuova istanza | 5 | 3.927 | 6.062 | 6.516 |
| ars_gap · query con cache applicativa | 30 | 0.448 | 0.736 | 0.807 |
| aligned_association · prima query, nuova istanza | 5 | 2.824 | 7.384 | 8.189 |
| aligned_association · query con cache applicativa | 30 | 1.443 | 3.120 | 4.375 |
| mismatched_association · prima query, nuova istanza | 5 | 2.336 | 10.002 | 11.837 |
| mismatched_association · query con cache applicativa | 30 | 1.298 | 1.593 | 1.850 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 3.806 | 9.577 | 10.671 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.522 | 1.181 | 2.215 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.623 | 6.245 | 6.714 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.486 | 0.752 | 0.943 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 1.640 | 2.526 | 2.577 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 0.874 | 1.074 | 1.389 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.572 | 0.664 | 0.686 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.315 | 0.469 | 0.631 |
| census_young_employment · prima query, nuova istanza | 5 | 1.878 | 2.021 | 2.049 |
| census_young_employment · query con cache applicativa | 30 | 0.505 | 0.723 | 1.005 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.620 | 0.702 | 0.718 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.310 | 0.574 | 0.638 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 1.555 | 1.987 | 2.080 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.523 | 0.857 | 1.090 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.598 | 2.132 | 2.172 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.428 | 0.503 | 0.843 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.090 | 2.434 | 2.503 |
| distinct_debt_weighted · query con cache applicativa | 30 | 0.823 | 1.107 | 1.276 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.609 | 0.728 | 0.736 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.353 | 0.714 | 0.827 |
| demography_dependency · prima query, nuova istanza | 5 | 23.858 | 33.763 | 34.421 |
| demography_dependency · query con cache applicativa | 30 | 0.596 | 2.122 | 3.802 |
| school_class_size · prima query, nuova istanza | 5 | 22.497 | 26.996 | 27.576 |
| school_class_size · query con cache applicativa | 30 | 0.586 | 0.975 | 1.145 |
| demography_aligned_events · prima query, nuova istanza | 5 | 25.546 | 28.122 | 28.600 |
| demography_aligned_events · query con cache applicativa | 30 | 1.746 | 14.742 | 26.311 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.731 | 0.959 | 0.997 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.396 | 0.672 | 1.103 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 47.926 | 52.738 | 53.845 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 0.676 | 1.005 | 1.373 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 51.158 | 63.361 | 64.140 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 0.705 | 1.056 | 1.189 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 51.823 | 56.774 | 57.811 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 0.909 | 1.893 | 2.127 |
| environment_water_pooled · prima query, nuova istanza | 5 | 2.081 | 2.437 | 2.485 |
| environment_water_pooled · query con cache applicativa | 30 | 0.621 | 1.798 | 2.185 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 20.258 | 24.518 | 24.786 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.474 | 0.767 | 0.900 |
| environment_cost_gap · prima query, nuova istanza | 5 | 1.079 | 2.108 | 2.331 |
| environment_cost_gap · query con cache applicativa | 30 | 0.420 | 0.712 | 0.806 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.098 | 1.193 | 1.215 |
| agriculture_pooled_size · query con cache applicativa | 30 | 0.662 | 0.983 | 1.104 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.242 | 3.599 | 4.168 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 0.726 | 1.087 | 1.847 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.259 | 1.378 | 1.383 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 0.607 | 1.960 | 2.776 |

Allocazioni Python: picco 23.003 MiB; mantenute 20.301 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
