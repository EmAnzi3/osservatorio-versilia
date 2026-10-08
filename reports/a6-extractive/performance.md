# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `3ceaadcb6f342f11758cdf711dc8c7330a95498664fd9ff08e4e0887e73d3114`; domande `58c2898af035bdf0de974c4ae72080c4e8a97abeed0610df30e4a86097c3a20f`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "bathingAdapterSha256": "562061699d57c58292c702e2598d883ee05348de649caad1c50f3719880285a4", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "coastAdapterSha256": "1ace0bf132cfa6200b65997dd397e9e3ad47ae5f083e1d4fae33f878572fea09", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "extractiveAdapterSha256": "4261110cd0fadd43b8691be3f2da2d40a23e98fcbe11942af311ddce98490972", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "fragilityAdapterSha256": "b1b104bb69ebbb5dfecd9061955b6113b342f583746e43eb12986a719fefd76e", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "maritimeAdapterSha256": "bced33dc09761daa64e54ca69c35822ba603bbaebc370c3f9923ccf1eb6dd3e2", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 116.184 | 120.680 | 121.547 |
| extractive_sites_active · prima query, nuova istanza | 5 | 2.240 | 2.736 | 2.838 |
| extractive_sites_active · query con cache applicativa | 30 | 1.393 | 1.732 | 1.899 |
| extractive_prc_pooled · prima query, nuova istanza | 5 | 3.415 | 3.914 | 4.024 |
| extractive_prc_pooled · query con cache applicativa | 30 | 2.486 | 2.833 | 2.859 |
| extractive_production_history · prima query, nuova istanza | 5 | 3.615 | 3.691 | 3.693 |
| extractive_production_history · query con cache applicativa | 30 | 2.367 | 2.610 | 2.804 |
| maritime_tourist_pooled · prima query, nuova istanza | 5 | 1.873 | 2.013 | 2.026 |
| maritime_tourist_pooled · query con cache applicativa | 30 | 1.323 | 1.720 | 1.761 |
| maritime_mean_due_pooled · prima query, nuova istanza | 5 | 1.917 | 2.762 | 2.954 |
| maritime_mean_due_pooled · query con cache applicativa | 30 | 1.535 | 1.854 | 1.982 |
| maritime_median_weighting_refused · prima query, nuova istanza | 5 | 0.627 | 0.656 | 0.660 |
| maritime_median_weighting_refused · query con cache applicativa | 30 | 0.433 | 0.662 | 0.767 |
| bathing_quality_pooled · prima query, nuova istanza | 5 | 1.273 | 1.650 | 1.725 |
| bathing_quality_pooled · query con cache applicativa | 30 | 0.779 | 1.129 | 2.220 |
| bathing_samples_pooled · prima query, nuova istanza | 5 | 1.150 | 1.175 | 1.176 |
| bathing_samples_pooled · query con cache applicativa | 30 | 0.692 | 0.878 | 1.088 |
| bathing_blue_history · prima query, nuova istanza | 5 | 1.857 | 1.884 | 1.886 |
| bathing_blue_history · query con cache applicativa | 30 | 1.035 | 1.332 | 1.493 |
| coast_protection_pooled · prima query, nuova istanza | 5 | 1.114 | 1.219 | 1.233 |
| coast_protection_pooled · query con cache applicativa | 30 | 0.665 | 0.894 | 1.089 |
| coast_dynamics_erosion_pooled · prima query, nuova istanza | 5 | 1.188 | 1.318 | 1.347 |
| coast_dynamics_erosion_pooled · query con cache applicativa | 30 | 0.679 | 0.798 | 1.231 |
| coast_mixed_universe_refused · prima query, nuova istanza | 5 | 0.689 | 0.813 | 0.823 |
| coast_mixed_universe_refused · query con cache applicativa | 30 | 0.394 | 0.581 | 0.724 |
| ifc_municipalFragility_series · prima query, nuova istanza | 5 | 1.571 | 1.815 | 1.842 |
| ifc_municipalFragility_series · query con cache applicativa | 30 | 0.714 | 1.204 | 1.277 |
| ifc_access_tuscany_gap · prima query, nuova istanza | 5 | 9.153 | 11.399 | 11.952 |
| ifc_access_tuscany_gap · query con cache applicativa | 30 | 6.894 | 8.424 | 8.867 |
| ifc_lowProductivityEmployment_relative_change_refused · prima query, nuova istanza | 5 | 0.779 | 0.851 | 0.869 |
| ifc_lowProductivityEmployment_relative_change_refused · query con cache applicativa | 30 | 0.569 | 0.703 | 0.846 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 1.559 | 1.660 | 1.683 |
| hazard_flood_pooled · query con cache applicativa | 30 | 0.652 | 0.800 | 0.940 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 1.257 | 1.342 | 1.361 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 0.713 | 1.027 | 1.122 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 2.389 | 3.482 | 3.725 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 2.061 | 2.671 | 3.130 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 1.621 | 2.154 | 2.225 |
| territory_protected_pooled · query con cache applicativa | 30 | 0.723 | 1.168 | 1.594 |
| territory_network_pooled · prima query, nuova istanza | 5 | 1.270 | 1.401 | 1.416 |
| territory_network_pooled · query con cache applicativa | 30 | 0.542 | 0.648 | 0.946 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 1.852 | 1.987 | 1.987 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 1.178 | 2.013 | 2.714 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.319 | 1.401 | 1.420 |
| soil_stock_pooled · query con cache applicativa | 30 | 0.594 | 0.930 | 1.063 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.088 | 1.128 | 1.132 |
| soil_ucs_pooled · query con cache applicativa | 30 | 0.584 | 0.678 | 0.974 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 1.898 | 2.703 | 2.901 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.044 | 1.222 | 1.458 |
| geography_density_pooled · prima query, nuova istanza | 5 | 2.225 | 4.364 | 4.863 |
| geography_density_pooled · query con cache applicativa | 30 | 0.852 | 0.954 | 1.361 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.181 | 1.288 | 1.302 |
| geography_forest_pooled · query con cache applicativa | 30 | 0.685 | 0.826 | 1.085 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 1.514 | 2.033 | 2.119 |
| geography_mixed_reference · query con cache applicativa | 30 | 1.453 | 1.639 | 3.399 |
| population_current · prima query, nuova istanza | 5 | 2.776 | 5.251 | 5.833 |
| population_current · query con cache applicativa | 30 | 0.579 | 0.954 | 1.789 |
| female_weighted · prima query, nuova istanza | 5 | 1.247 | 1.297 | 1.306 |
| female_weighted · query con cache applicativa | 30 | 0.732 | 1.415 | 1.797 |
| ars_gap · prima query, nuova istanza | 5 | 3.801 | 6.311 | 6.602 |
| ars_gap · query con cache applicativa | 30 | 0.812 | 0.860 | 1.256 |
| aligned_association · prima query, nuova istanza | 5 | 2.516 | 4.293 | 4.704 |
| aligned_association · query con cache applicativa | 30 | 1.228 | 1.357 | 1.618 |
| mismatched_association · prima query, nuova istanza | 5 | 3.211 | 9.773 | 11.016 |
| mismatched_association · query con cache applicativa | 30 | 1.289 | 1.424 | 1.853 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 3.386 | 6.112 | 6.780 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.678 | 1.131 | 4.706 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.688 | 7.020 | 7.530 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.595 | 0.796 | 0.970 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 2.086 | 2.500 | 2.559 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 0.749 | 0.835 | 1.274 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.778 | 1.059 | 1.092 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.412 | 0.524 | 1.119 |
| census_young_employment · prima query, nuova istanza | 5 | 1.650 | 1.925 | 1.993 |
| census_young_employment · query con cache applicativa | 30 | 0.629 | 0.941 | 0.949 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.751 | 0.903 | 0.913 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.441 | 0.632 | 0.712 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 1.694 | 2.122 | 2.194 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.651 | 1.028 | 1.272 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.691 | 1.825 | 1.841 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.448 | 0.593 | 0.877 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.174 | 4.887 | 5.532 |
| distinct_debt_weighted · query con cache applicativa | 30 | 0.830 | 1.090 | 2.207 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.740 | 0.928 | 0.974 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.403 | 0.554 | 2.407 |
| demography_dependency · prima query, nuova istanza | 5 | 21.850 | 25.023 | 25.425 |
| demography_dependency · query con cache applicativa | 30 | 0.624 | 0.810 | 0.982 |
| school_class_size · prima query, nuova istanza | 5 | 19.423 | 21.489 | 21.885 |
| school_class_size · query con cache applicativa | 30 | 0.662 | 0.976 | 1.398 |
| demography_aligned_events · prima query, nuova istanza | 5 | 21.164 | 24.826 | 25.600 |
| demography_aligned_events · query con cache applicativa | 30 | 1.571 | 1.991 | 2.364 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.746 | 0.883 | 0.905 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.416 | 0.469 | 0.711 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 41.219 | 43.944 | 43.978 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 0.743 | 1.131 | 1.483 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 42.782 | 58.305 | 61.600 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 0.831 | 1.063 | 1.346 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 41.849 | 42.706 | 42.757 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 0.865 | 1.230 | 1.652 |
| environment_water_pooled · prima query, nuova istanza | 5 | 1.702 | 2.302 | 2.389 |
| environment_water_pooled · query con cache applicativa | 30 | 0.674 | 0.873 | 0.949 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 17.183 | 20.206 | 20.930 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.566 | 0.726 | 0.927 |
| environment_cost_gap · prima query, nuova istanza | 5 | 1.157 | 1.313 | 1.349 |
| environment_cost_gap · query con cache applicativa | 30 | 0.514 | 0.740 | 0.905 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.220 | 1.319 | 1.340 |
| agriculture_pooled_size · query con cache applicativa | 30 | 0.745 | 0.930 | 1.122 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.299 | 1.421 | 1.429 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 0.749 | 0.868 | 1.186 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.162 | 1.451 | 1.486 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 0.703 | 0.954 | 1.071 |

Allocazioni Python: picco 23.672 MiB; mantenute 22.391 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
