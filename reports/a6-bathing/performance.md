# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `b6da147b0b11e533224ffd0199b3924da8c7f201355b4995ef26b63417164b2c`; domande `0946b422a87e5df5f329105612dafc1de62df4540bc393f3e87b3ce7858fdb54`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "agricultureAdapterSha256": "558a510c662ff1c21d93d90d3ece81f19423bffee4aef2032640a74f424de5b2", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "bathingAdapterSha256": "562061699d57c58292c702e2598d883ee05348de649caad1c50f3719880285a4", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "coastAdapterSha256": "1ace0bf132cfa6200b65997dd397e9e3ad47ae5f083e1d4fae33f878572fea09", "commutingAdapterSha256": "98385b92c620a8e08c0d3d70d8bb52c60d62929f4b8afce38a59a064ada634b6", "demographySchoolAdapterSha256": "c4631a7c742db0286882c3489e681188a2da42744094727a218fb442b43a7bcf", "distinctFinanceAdapterSha256": "3f8e6f31da9ee9d54ab2853d2130c50ea3a021bda48b255b81ed669a3937418c", "environmentAdapterSha256": "49fc8bb55c5dc18efa32d5398a87cd6d471e90a9913d00a22a12e075e8d7c793", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "fragilityAdapterSha256": "b1b104bb69ebbb5dfecd9061955b6113b342f583746e43eb12986a719fefd76e", "geographyAdapterSha256": "a06095ad1f650d060880fb66ae88bf37a71709a77e2a5d2992aee92e996e6d71", "hazardAdapterSha256": "750c4833fcd93ebc03c7ff32b4c585861e35d231b545cf0aefc77453f3dfc8af", "soilAdapterSha256": "13f5119f1a87111b8f2e689f4901b3ec6c6900a4425fbc0de899bec363d3ed50", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465", "territoryAdapterSha256": "ad447b28f098f32d6d15169300b843df24ee8e1d3f9e06d028cc6f1aa91d9e97"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 115.549 | 118.091 | 118.097 |
| bathing_quality_pooled · prima query, nuova istanza | 5 | 1.255 | 1.666 | 1.747 |
| bathing_quality_pooled · query con cache applicativa | 30 | 0.870 | 1.270 | 1.549 |
| bathing_samples_pooled · prima query, nuova istanza | 5 | 1.217 | 1.523 | 1.590 |
| bathing_samples_pooled · query con cache applicativa | 30 | 0.813 | 1.083 | 1.144 |
| bathing_blue_history · prima query, nuova istanza | 5 | 2.110 | 2.767 | 2.930 |
| bathing_blue_history · query con cache applicativa | 30 | 1.196 | 1.841 | 3.127 |
| coast_protection_pooled · prima query, nuova istanza | 5 | 1.209 | 1.371 | 1.393 |
| coast_protection_pooled · query con cache applicativa | 30 | 0.560 | 0.655 | 0.956 |
| coast_dynamics_erosion_pooled · prima query, nuova istanza | 5 | 1.168 | 1.422 | 1.475 |
| coast_dynamics_erosion_pooled · query con cache applicativa | 30 | 0.673 | 1.050 | 1.421 |
| coast_mixed_universe_refused · prima query, nuova istanza | 5 | 0.644 | 0.881 | 0.913 |
| coast_mixed_universe_refused · query con cache applicativa | 30 | 0.352 | 0.572 | 0.776 |
| ifc_municipalFragility_series · prima query, nuova istanza | 5 | 1.253 | 1.263 | 1.264 |
| ifc_municipalFragility_series · query con cache applicativa | 30 | 0.729 | 1.051 | 1.124 |
| ifc_access_tuscany_gap · prima query, nuova istanza | 5 | 10.972 | 14.734 | 15.227 |
| ifc_access_tuscany_gap · query con cache applicativa | 30 | 5.185 | 6.370 | 7.251 |
| ifc_lowProductivityEmployment_relative_change_refused · prima query, nuova istanza | 5 | 0.652 | 0.818 | 0.847 |
| ifc_lowProductivityEmployment_relative_change_refused · query con cache applicativa | 30 | 0.351 | 0.436 | 0.627 |
| hazard_flood_pooled · prima query, nuova istanza | 5 | 1.184 | 1.247 | 1.251 |
| hazard_flood_pooled · query con cache applicativa | 30 | 0.615 | 0.815 | 1.057 |
| hazard_landslide_pooled_area · prima query, nuova istanza | 5 | 1.266 | 1.380 | 1.391 |
| hazard_landslide_pooled_area · query con cache applicativa | 30 | 0.684 | 0.958 | 1.183 |
| hazard_mixed_maps_refused · prima query, nuova istanza | 5 | 2.327 | 2.410 | 2.415 |
| hazard_mixed_maps_refused · query con cache applicativa | 30 | 1.687 | 1.828 | 2.240 |
| territory_protected_pooled · prima query, nuova istanza | 5 | 1.461 | 2.080 | 2.191 |
| territory_protected_pooled · query con cache applicativa | 30 | 0.754 | 1.670 | 2.331 |
| territory_network_pooled · prima query, nuova istanza | 5 | 1.397 | 1.727 | 1.744 |
| territory_network_pooled · query con cache applicativa | 30 | 0.637 | 0.960 | 0.970 |
| territory_mixed_reference_refused · prima query, nuova istanza | 5 | 2.396 | 3.068 | 3.178 |
| territory_mixed_reference_refused · query con cache applicativa | 30 | 1.731 | 1.889 | 2.240 |
| soil_stock_pooled · prima query, nuova istanza | 5 | 1.275 | 1.739 | 1.803 |
| soil_stock_pooled · query con cache applicativa | 30 | 0.556 | 0.811 | 1.028 |
| soil_ucs_pooled · prima query, nuova istanza | 5 | 1.038 | 2.361 | 2.690 |
| soil_ucs_pooled · query con cache applicativa | 30 | 0.667 | 1.039 | 1.168 |
| soil_mixed_edition_refused · prima query, nuova istanza | 5 | 2.084 | 2.478 | 2.515 |
| soil_mixed_edition_refused · query con cache applicativa | 30 | 1.133 | 1.618 | 1.849 |
| geography_density_pooled · prima query, nuova istanza | 5 | 2.492 | 5.457 | 6.168 |
| geography_density_pooled · query con cache applicativa | 30 | 0.838 | 1.165 | 1.297 |
| geography_forest_pooled · prima query, nuova istanza | 5 | 1.209 | 1.352 | 1.385 |
| geography_forest_pooled · query con cache applicativa | 30 | 0.651 | 1.085 | 1.107 |
| geography_mixed_reference · prima query, nuova istanza | 5 | 1.688 | 1.966 | 1.994 |
| geography_mixed_reference · query con cache applicativa | 30 | 0.915 | 1.376 | 1.547 |
| population_current · prima query, nuova istanza | 5 | 1.860 | 5.206 | 6.003 |
| population_current · query con cache applicativa | 30 | 0.515 | 0.623 | 0.899 |
| female_weighted · prima query, nuova istanza | 5 | 1.246 | 1.339 | 1.353 |
| female_weighted · query con cache applicativa | 30 | 0.700 | 0.852 | 1.071 |
| ars_gap · prima query, nuova istanza | 5 | 3.533 | 6.509 | 7.224 |
| ars_gap · query con cache applicativa | 30 | 0.498 | 0.746 | 1.033 |
| aligned_association · prima query, nuova istanza | 5 | 2.609 | 4.765 | 5.297 |
| aligned_association · query con cache applicativa | 30 | 1.216 | 1.567 | 1.632 |
| mismatched_association · prima query, nuova istanza | 5 | 2.423 | 5.098 | 5.608 |
| mismatched_association · query con cache applicativa | 30 | 1.102 | 1.354 | 1.670 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 3.954 | 7.453 | 7.928 |
| ars_hypertension_age · query con cache applicativa | 30 | 0.890 | 1.069 | 1.295 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.247 | 5.839 | 6.484 |
| ars_mortality_window_gap · query con cache applicativa | 30 | 0.568 | 0.765 | 0.934 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 1.782 | 2.086 | 2.155 |
| business_frame_industry_weighted · query con cache applicativa | 30 | 0.748 | 0.955 | 1.315 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.820 | 0.911 | 0.929 |
| business_endpoint_refused · query con cache applicativa | 30 | 0.374 | 0.510 | 0.676 |
| census_young_employment · prima query, nuova istanza | 5 | 1.602 | 2.797 | 3.037 |
| census_young_employment · query con cache applicativa | 30 | 0.831 | 1.115 | 1.526 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.629 | 0.852 | 0.904 |
| census_diploma_trend_refused · query con cache applicativa | 30 | 0.364 | 0.566 | 0.638 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 1.622 | 1.762 | 1.794 |
| finance_cash_weighted · query con cache applicativa | 30 | 0.572 | 0.713 | 0.963 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.410 | 1.468 | 1.471 |
| finance_benchmark_refused · query con cache applicativa | 30 | 0.386 | 0.506 | 0.683 |
| distinct_debt_weighted · prima query, nuova istanza | 5 | 2.043 | 2.164 | 2.182 |
| distinct_debt_weighted · query con cache applicativa | 30 | 0.719 | 1.050 | 1.135 |
| distinct_debt_osl_refused · prima query, nuova istanza | 5 | 0.652 | 0.817 | 0.847 |
| distinct_debt_osl_refused · query con cache applicativa | 30 | 0.534 | 0.600 | 0.858 |
| demography_dependency · prima query, nuova istanza | 5 | 19.009 | 21.244 | 21.704 |
| demography_dependency · query con cache applicativa | 30 | 0.573 | 0.760 | 0.990 |
| school_class_size · prima query, nuova istanza | 5 | 18.330 | 21.744 | 22.543 |
| school_class_size · query con cache applicativa | 30 | 0.650 | 0.761 | 1.127 |
| demography_aligned_events · prima query, nuova istanza | 5 | 20.537 | 25.942 | 26.841 |
| demography_aligned_events · query con cache applicativa | 30 | 1.683 | 3.159 | 3.659 |
| school_calendar_year_refused · prima query, nuova istanza | 5 | 0.762 | 0.876 | 0.896 |
| school_calendar_year_refused · query con cache applicativa | 30 | 0.390 | 0.671 | 0.722 |
| commuting_pooled_selfContainment · prima query, nuova istanza | 5 | 40.879 | 62.871 | 67.497 |
| commuting_pooled_selfContainment · query con cache applicativa | 30 | 0.807 | 1.088 | 1.243 |
| commuting_pooled_commuterBalanceRate · prima query, nuova istanza | 5 | 43.732 | 65.269 | 70.380 |
| commuting_pooled_commuterBalanceRate · query con cache applicativa | 30 | 0.774 | 1.443 | 1.548 |
| commuting_hybrid_pair_refused · prima query, nuova istanza | 5 | 43.057 | 52.335 | 53.268 |
| commuting_hybrid_pair_refused · query con cache applicativa | 30 | 0.915 | 1.149 | 1.724 |
| environment_water_pooled · prima query, nuova istanza | 5 | 1.934 | 2.064 | 2.076 |
| environment_water_pooled · query con cache applicativa | 30 | 0.660 | 0.818 | 1.097 |
| environment_rd_weighting_refused · prima query, nuova istanza | 5 | 18.944 | 22.453 | 23.119 |
| environment_rd_weighting_refused · query con cache applicativa | 30 | 0.601 | 0.856 | 0.900 |
| environment_cost_gap · prima query, nuova istanza | 5 | 1.019 | 1.473 | 1.501 |
| environment_cost_gap · query con cache applicativa | 30 | 0.532 | 0.757 | 0.912 |
| agriculture_pooled_size · prima query, nuova istanza | 5 | 1.174 | 1.294 | 1.323 |
| agriculture_pooled_size · query con cache applicativa | 30 | 0.711 | 0.933 | 1.104 |
| agriculture_pooled_irrigated · prima query, nuova istanza | 5 | 1.190 | 1.364 | 1.381 |
| agriculture_pooled_irrigated · query con cache applicativa | 30 | 0.718 | 1.029 | 1.157 |
| agriculture_mixed_scope_refused · prima query, nuova istanza | 5 | 1.258 | 1.420 | 1.451 |
| agriculture_mixed_scope_refused · query con cache applicativa | 30 | 0.701 | 0.984 | 1.189 |

Allocazioni Python: picco 23.065 MiB; mantenute 21.784 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
