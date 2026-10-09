# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `6a35f7d8e483a43045768415f30c4d857879508bae4a234521841389fdfa6e50`; domande `17fca297b28c36756db8ccd9102339fd499796ed237f3fe286b967670adf7eb3`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "bathingAdapterSha256": "562061699d57c58292c702e2598d883ee05348de649caad1c50f3719880285a4", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "coastAdapterSha256": "1ace0bf132cfa6200b65997dd397e9e3ad47ae5f083e1d4fae33f878572fea09", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "extractiveAdapterSha256": "4261110cd0fadd43b8691be3f2da2d40a23e98fcbe11942af311ddce98490972", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "fragilityAdapterSha256": "b1b104bb69ebbb5dfecd9061955b6113b342f583746e43eb12986a719fefd76e", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "maritimeAdapterSha256": "bced33dc09761daa64e54ca69c35822ba603bbaebc370c3f9923ccf1eb6dd3e2", "pabAdapterSha256": "fad0391a396cf4e9a6ee32e1ac965fe4a10f3684fccc5d0690efd7435452a1b8", "remediationAdapterSha256": "303269e55e8d4f5a2275b45a96833df27fc755cd61b035feb38052883a673368", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 131.980 | 139.349 | 140.036 |
| pab_pabProgrammedInterventions · prima query, nuova istanza | 5 | 18.102 | 40.153 | 45.093 |
| pab_pabProgrammedInterventions · query con cache applicativa | 30 | 6.468 | 7.604 | 7.768 |
| pab_pabInterventionsCompleted_share_pooled · prima query, nuova istanza | 5 | 19.186 | 21.586 | 21.967 |
| pab_pabInterventionsCompleted_share_pooled · query con cache applicativa | 30 | 6.831 | 14.047 | 15.973 |
| pab_approved_operational_refused · prima query, nuova istanza | 5 | 0.771 | 1.510 | 1.647 |
| pab_approved_operational_refused · query con cache applicativa | 30 | 0.529 | 0.830 | 1.037 |
| remediation_total · prima query, nuova istanza | 5 | 4.240 | 5.803 | 5.982 |
| remediation_total · query con cache applicativa | 30 | 2.479 | 3.137 | 4.023 |
| remediation_pooled · prima query, nuova istanza | 5 | 3.946 | 4.352 | 4.407 |
| remediation_pooled · query con cache applicativa | 30 | 2.331 | 3.514 | 3.912 |
| remediation_history_refused · prima query, nuova istanza | 5 | 0.753 | 1.233 | 1.347 |
| remediation_history_refused · query con cache applicativa | 30 | 0.501 | 0.617 | 0.808 |
| extractive_sites_active · prima query, nuova istanza | 5 | 3.029 | 3.620 | 3.661 |
| extractive_sites_active · query con cache applicativa | 30 | 1.639 | 3.032 | 4.763 |
| extractive_prc_pooled · prima query, nuova istanza | 5 | 4.251 | 4.928 | 5.031 |
| extractive_prc_pooled · query con cache applicativa | 30 | 3.360 | 6.258 | 6.535 |
| extractive_production_history · prima query, nuova istanza | 5 | 4.140 | 5.396 | 5.495 |
| extractive_production_history · query con cache applicativa | 30 | 3.332 | 7.116 | 10.191 |
| maritime_tourist_pooled · prima query, nuova istanza | 5 | 2.566 | 2.812 | 2.839 |
| maritime_tourist_pooled · query con cache applicativa | 30 | 1.705 | 2.162 | 2.300 |
| maritime_mean_due_pooled · prima query, nuova istanza | 5 | 2.359 | 2.549 | 2.563 |
| maritime_mean_due_pooled · query con cache applicativa | 30 | 1.815 | 2.411 | 2.593 |
| maritime_median_weighting_refused · prima query, nuova istanza | 5 | 0.838 | 0.906 | 0.917 |
| maritime_median_weighting_refused · query con cache applicativa | 30 | 0.506 | 0.524 | 0.783 |
| bathing_quality_pooled · prima query, nuova istanza | 5 | 1.514 | 1.921 | 1.970 |
| bathing_quality_pooled · query con cache applicativa | 30 | 1.043 | 1.292 | 1.568 |
| bathing_samples_pooled · prima query, nuova istanza | 5 | 1.761 | 1.924 | 1.935 |
| bathing_samples_pooled · query con cache applicativa | 30 | 0.931 | 1.775 | 2.190 |
| bathing_blue_history · prima query, nuova istanza | 5 | 2.183 | 2.554 | 2.620 |
| bathing_blue_history · query con cache applicativa | 30 | 1.413 | 1.936 | 2.049 |
| coast_protection_pooled · prima query, nuova istanza | 5 | 1.433 | 1.658 | 1.714 |
| coast_protection_pooled · query con cache applicativa | 30 | 0.864 | 1.332 | 1.508 |
| coast_dynamics_erosion_pooled · prima query, nuova istanza | 5 | 1.347 | 1.714 | 1.793 |
| coast_dynamics_erosion_pooled · query con cache applicativa | 30 | 0.870 | 1.348 | 1.542 |
| coast_mixed_universe_refused · prima query, nuova istanza | 5 | 0.771 | 0.843 | 0.860 |
| coast_mixed_universe_refused · query con cache applicativa | 30 | 0.527 | 0.835 | 1.208 |
| ifc_municipalFragility_series · prima query, nuova istanza | 5 | 1.733 | 2.077 | 2.107 |
| ifc_municipalFragility_series · query con cache applicativa | 30 | 1.122 | 1.578 | 2.409 |
| ifc_access_tuscany_gap · prima query, nuova istanza | 5 | 11.040 | 13.108 | 13.113 |
| ifc_access_tuscany_gap · query con cache applicativa | 30 | 6.393 | 8.148 | 8.724 |
| ifc_lowProductivityEmployment_relative_change_refused · prima query, nuova istanza | 5 | 0.922 | 4.123 | 4.436 |
| ifc_lowProductivityEmployment_relative_change_refused · query con cache applicativa | 30 | 0.514 | 0.691 | 0.902 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 1.547 | 2.048 | 2.109 |
| hazard_flood_pooled · query con cache applicativa | 30 | 0.891 | 1.689 | 2.433 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 1.514 | 3.382 | 3.840 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 0.947 | 1.392 | 1.649 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 3.479 | 4.245 | 4.304 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 2.387 | 3.734 | 4.325 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 1.686 | 1.922 | 1.944 |
| territory_protected_pooled · query con cache applicativa | 30 | 0.808 | 1.060 | 1.426 |
| territory_network_pooled · prima query, nuova istanza | 5 | 1.741 | 1.937 | 1.982 |
| territory_network_pooled · query con cache applicativa | 30 | 0.704 | 1.881 | 3.108 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 2.533 | 2.625 | 2.648 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 1.499 | 1.922 | 2.756 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.661 | 1.792 | 1.816 |
| soil_stock_pooled · query con cache applicativa | 30 | 0.823 | 1.803 | 2.684 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.289 | 1.719 | 1.796 |
| soil_ucs_pooled · query con cache applicativa | 30 | 0.810 | 1.171 | 1.515 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 2.857 | 4.217 | 4.546 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.593 | 3.489 | 4.317 |
| geography_density_pooled · prima query, nuova istanza | 5 | 2.801 | 5.932 | 6.545 |
| geography_density_pooled · query con cache applicativa | 30 | 1.035 | 1.489 | 1.614 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.447 | 2.367 | 2.389 |
| geography_forest_pooled · query con cache applicativa | 30 | 1.099 | 1.835 | 3.692 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 2.119 | 4.631 | 5.237 |
| geography_mixed_reference · query con cache applicativa | 30 | 1.191 | 1.453 | 1.665 |
| population_current · prima query, nuova istanza | 5 | 2.351 | 5.332 | 6.044 |
| population_current · query con cache applicativa | 30 | 0.843 | 1.689 | 2.611 |
| female_weighted · prima query, nuova istanza | 5 | 1.418 | 2.827 | 3.151 |
| female_weighted · query con cache applicativa | 30 | 0.938 | 1.292 | 1.488 |
| ars_gap · prima query, nuova istanza | 5 | 4.185 | 7.111 | 7.823 |
| ars_gap · query con cache applicativa | 30 | 0.754 | 1.044 | 1.472 |
| aligned_association · prima query, nuova istanza | 5 | 3.334 | 5.663 | 6.101 |
| aligned_association · query con cache applicativa | 30 | 1.701 | 1.969 | 2.989 |
| mismatched_association · prima query, nuova istanza | 5 | 3.068 | 5.010 | 5.441 |
| mismatched_association · query con cache applicativa | 30 | 1.137 | 1.382 | 2.215 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 4.630 | 7.254 | 7.468 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.871 | 1.199 | 1.238 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 4.224 | 6.526 | 7.100 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.821 | 1.107 | 1.180 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 2.138 | 2.514 | 2.604 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 1.107 | 1.680 | 2.084 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 1.022 | 1.113 | 1.121 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.559 | 0.946 | 1.086 |
| census_young_employment · prima query, nuova istanza | 5 | 2.198 | 4.076 | 4.403 |
| census_young_employment · query con cache applicativa | 30 | 0.799 | 1.151 | 1.178 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.830 | 1.253 | 1.345 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.525 | 0.762 | 0.977 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 2.252 | 2.566 | 2.594 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.804 | 1.177 | 1.261 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.811 | 2.135 | 2.187 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.564 | 0.853 | 0.909 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.507 | 2.753 | 2.768 |
| distinct_debt_weighted · query con cache applicativa | 30 | 1.021 | 1.880 | 1.992 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.837 | 1.126 | 1.180 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.583 | 1.023 | 1.145 |
| demography_dependency · prima query, nuova istanza | 5 | 23.448 | 25.372 | 25.738 |
| demography_dependency · query con cache applicativa | 30 | 0.779 | 1.062 | 1.297 |
| school_class_size · prima query, nuova istanza | 5 | 20.865 | 22.455 | 22.785 |
| school_class_size · query con cache applicativa | 30 | 0.992 | 1.301 | 1.397 |
| demography_aligned_events · prima query, nuova istanza | 5 | 22.850 | 27.507 | 28.521 |
| demography_aligned_events · query con cache applicativa | 30 | 2.180 | 2.873 | 4.157 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.915 | 3.158 | 3.697 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.529 | 0.688 | 0.843 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 47.991 | 48.871 | 48.973 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 0.956 | 1.198 | 1.362 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 45.645 | 56.479 | 58.756 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 1.070 | 1.631 | 1.898 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 51.595 | 53.780 | 53.901 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 1.179 | 1.969 | 2.198 |
| environment_water_pooled · prima query, nuova istanza | 5 | 2.370 | 4.105 | 4.389 |
| environment_water_pooled · query con cache applicativa | 30 | 0.910 | 1.386 | 2.054 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 21.579 | 25.049 | 25.544 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.949 | 2.904 | 4.001 |
| environment_cost_gap · prima query, nuova istanza | 5 | 1.331 | 1.412 | 1.427 |
| environment_cost_gap · query con cache applicativa | 30 | 0.711 | 1.101 | 1.153 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.594 | 2.017 | 2.102 |
| agriculture_pooled_size · query con cache applicativa | 30 | 1.069 | 1.420 | 1.472 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.846 | 1.944 | 1.954 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 1.042 | 1.323 | 1.379 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.286 | 1.504 | 1.529 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 0.926 | 1.356 | 2.463 |

Allocazioni Python: picco 27.620 MiB; mantenute 26.078 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
