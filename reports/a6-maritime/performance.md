# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `ca4e83462f381a99672ebf6335068b59d26ca27645a873eda20427b552cffe12`; domande `81d03266c9524dd3209371d2fc1498839b8d5af653b654e811fe15f3aed62bcb`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "bathingAdapterSha256": "562061699d57c58292c702e2598d883ee05348de649caad1c50f3719880285a4", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "coastAdapterSha256": "1ace0bf132cfa6200b65997dd397e9e3ad47ae5f083e1d4fae33f878572fea09", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "fragilityAdapterSha256": "b1b104bb69ebbb5dfecd9061955b6113b342f583746e43eb12986a719fefd76e", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "maritimeAdapterSha256": "bced33dc09761daa64e54ca69c35822ba603bbaebc370c3f9923ccf1eb6dd3e2", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 133.880 | 169.665 | 176.276 |
| maritime_tourist_pooled · prima query, nuova istanza | 5 | 2.190 | 2.768 | 2.865 |
| maritime_tourist_pooled · query con cache applicativa | 30 | 1.445 | 1.834 | 1.986 |
| maritime_mean_due_pooled · prima query, nuova istanza | 5 | 2.183 | 2.410 | 2.460 |
| maritime_mean_due_pooled · query con cache applicativa | 30 | 1.983 | 2.135 | 2.156 |
| maritime_median_weighting_refused · prima query, nuova istanza | 5 | 0.685 | 0.773 | 0.776 |
| maritime_median_weighting_refused · query con cache applicativa | 30 | 0.387 | 0.602 | 0.768 |
| bathing_quality_pooled · prima query, nuova istanza | 5 | 1.217 | 1.459 | 1.513 |
| bathing_quality_pooled · query con cache applicativa | 30 | 0.814 | 1.058 | 1.129 |
| bathing_samples_pooled · prima query, nuova istanza | 5 | 1.168 | 1.642 | 1.752 |
| bathing_samples_pooled · query con cache applicativa | 30 | 0.935 | 1.036 | 1.428 |
| bathing_blue_history · prima query, nuova istanza | 5 | 1.914 | 2.707 | 2.834 |
| bathing_blue_history · query con cache applicativa | 30 | 1.034 | 1.149 | 1.480 |
| coast_protection_pooled · prima query, nuova istanza | 5 | 1.096 | 1.165 | 1.172 |
| coast_protection_pooled · query con cache applicativa | 30 | 0.634 | 0.959 | 0.972 |
| coast_dynamics_erosion_pooled · prima query, nuova istanza | 5 | 1.210 | 1.470 | 1.524 |
| coast_dynamics_erosion_pooled · query con cache applicativa | 30 | 0.689 | 0.982 | 1.044 |
| coast_mixed_universe_refused · prima query, nuova istanza | 5 | 0.640 | 0.806 | 0.841 |
| coast_mixed_universe_refused · query con cache applicativa | 30 | 0.398 | 0.653 | 0.795 |
| ifc_municipalFragility_series · prima query, nuova istanza | 5 | 1.252 | 1.341 | 1.355 |
| ifc_municipalFragility_series · query con cache applicativa | 30 | 0.729 | 1.019 | 1.311 |
| ifc_access_tuscany_gap · prima query, nuova istanza | 5 | 8.670 | 10.512 | 10.878 |
| ifc_access_tuscany_gap · query con cache applicativa | 30 | 7.949 | 8.178 | 9.348 |
| ifc_lowProductivityEmployment_relative_change_refused · prima query, nuova istanza | 5 | 0.614 | 0.657 | 0.659 |
| ifc_lowProductivityEmployment_relative_change_refused · query con cache applicativa | 30 | 0.380 | 0.565 | 0.794 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 1.358 | 1.450 | 1.464 |
| hazard_flood_pooled · query con cache applicativa | 30 | 0.751 | 1.027 | 1.059 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 1.665 | 1.874 | 1.915 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 0.689 | 1.134 | 1.403 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 2.694 | 3.565 | 3.658 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 2.816 | 2.928 | 3.325 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 1.866 | 2.141 | 2.203 |
| territory_protected_pooled · query con cache applicativa | 30 | 0.580 | 0.627 | 1.006 |
| territory_network_pooled · prima query, nuova istanza | 5 | 1.331 | 1.811 | 1.821 |
| territory_network_pooled · query con cache applicativa | 30 | 0.538 | 0.792 | 0.922 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 1.979 | 2.227 | 2.247 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 1.218 | 1.486 | 1.611 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.487 | 1.568 | 1.585 |
| soil_stock_pooled · query con cache applicativa | 30 | 0.527 | 0.647 | 0.921 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.307 | 1.644 | 1.709 |
| soil_ucs_pooled · query con cache applicativa | 30 | 0.852 | 0.923 | 1.344 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 2.077 | 2.682 | 2.813 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.170 | 3.160 | 3.361 |
| geography_density_pooled · prima query, nuova istanza | 5 | 2.277 | 5.415 | 6.162 |
| geography_density_pooled · query con cache applicativa | 30 | 1.275 | 1.489 | 1.774 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.295 | 1.730 | 1.758 |
| geography_forest_pooled · query con cache applicativa | 30 | 1.046 | 1.112 | 1.511 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 1.702 | 2.178 | 2.199 |
| geography_mixed_reference · query con cache applicativa | 30 | 0.967 | 1.391 | 1.498 |
| population_current · prima query, nuova istanza | 5 | 1.907 | 4.725 | 5.399 |
| population_current · query con cache applicativa | 30 | 0.785 | 1.021 | 1.435 |
| female_weighted · prima query, nuova istanza | 5 | 1.158 | 1.194 | 1.200 |
| female_weighted · query con cache applicativa | 30 | 0.705 | 0.923 | 1.082 |
| ars_gap · prima query, nuova istanza | 5 | 3.805 | 5.776 | 6.109 |
| ars_gap · query con cache applicativa | 30 | 0.532 | 0.761 | 0.978 |
| aligned_association · prima query, nuova istanza | 5 | 2.729 | 7.478 | 8.338 |
| aligned_association · query con cache applicativa | 30 | 1.440 | 2.925 | 4.466 |
| mismatched_association · prima query, nuova istanza | 5 | 2.447 | 4.879 | 5.231 |
| mismatched_association · query con cache applicativa | 30 | 0.956 | 1.487 | 1.612 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 3.603 | 9.028 | 10.329 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.623 | 0.881 | 1.011 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.262 | 5.726 | 6.268 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.591 | 0.804 | 0.935 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 1.779 | 2.006 | 2.061 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 1.118 | 1.186 | 1.723 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.697 | 0.894 | 0.942 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.390 | 0.556 | 0.672 |
| census_young_employment · prima query, nuova istanza | 5 | 1.740 | 2.436 | 2.608 |
| census_young_employment · query con cache applicativa | 30 | 0.624 | 0.993 | 1.064 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.749 | 1.578 | 1.785 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.386 | 0.557 | 0.748 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 1.641 | 1.720 | 1.728 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.628 | 0.992 | 1.040 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.518 | 1.574 | 1.581 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.404 | 0.652 | 0.773 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.079 | 2.153 | 2.163 |
| distinct_debt_weighted · query con cache applicativa | 30 | 0.844 | 1.041 | 1.301 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.735 | 0.761 | 0.766 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.394 | 0.655 | 0.903 |
| demography_dependency · prima query, nuova istanza | 5 | 19.991 | 36.466 | 37.993 |
| demography_dependency · query con cache applicativa | 30 | 0.867 | 0.984 | 1.369 |
| school_class_size · prima query, nuova istanza | 5 | 18.515 | 28.116 | 29.684 |
| school_class_size · query con cache applicativa | 30 | 0.687 | 0.937 | 1.118 |
| demography_aligned_events · prima query, nuova istanza | 5 | 20.894 | 24.605 | 24.639 |
| demography_aligned_events · query con cache applicativa | 30 | 1.534 | 2.095 | 2.143 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.841 | 1.077 | 1.113 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.394 | 0.512 | 0.738 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 42.309 | 54.036 | 56.182 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 0.840 | 1.345 | 1.392 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 42.640 | 45.077 | 45.652 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 0.992 | 2.400 | 2.632 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 41.158 | 54.835 | 58.205 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 0.808 | 1.012 | 1.232 |
| environment_water_pooled · prima query, nuova istanza | 5 | 1.974 | 2.593 | 2.602 |
| environment_water_pooled · query con cache applicativa | 30 | 0.690 | 1.107 | 1.316 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 19.178 | 24.981 | 26.024 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.556 | 0.718 | 0.889 |
| environment_cost_gap · prima query, nuova istanza | 5 | 0.969 | 1.044 | 1.054 |
| environment_cost_gap · query con cache applicativa | 30 | 0.491 | 0.557 | 0.935 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.309 | 1.537 | 1.555 |
| agriculture_pooled_size · query con cache applicativa | 30 | 0.833 | 1.100 | 2.175 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.269 | 1.463 | 1.488 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 0.737 | 1.047 | 1.130 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.097 | 1.224 | 1.243 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 0.944 | 2.212 | 3.232 |

Allocazioni Python: picco 23.512 MiB; mantenute 22.231 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
