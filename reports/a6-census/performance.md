# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `36c832f96814d7f7bda181363e4c9a95d6e7700bfe9d117e089d391bc14df832`; domande `af548709f0360bb2523642399e962ba7c0041fa8544c8870ceba2356f5407aaa`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 147.341 | 195.806 | 207.227 |
| population_current · prima query, nuova istanza | 5 | 1.884 | 2.237 | 2.273 |
| population_current · query con cache applicativa | 50 | 0.326 | 0.580 | 0.844 |
| female_weighted · prima query, nuova istanza | 5 | 1.083 | 1.167 | 1.175 |
| female_weighted · query con cache applicativa | 50 | 0.521 | 0.774 | 0.997 |
| ars_gap · prima query, nuova istanza | 5 | 3.415 | 6.852 | 7.703 |
| ars_gap · query con cache applicativa | 50 | 0.276 | 0.476 | 0.593 |
| aligned_association · prima query, nuova istanza | 5 | 3.161 | 9.608 | 11.060 |
| aligned_association · query con cache applicativa | 50 | 1.170 | 1.570 | 1.939 |
| mismatched_association · prima query, nuova istanza | 5 | 2.396 | 5.357 | 5.986 |
| mismatched_association · query con cache applicativa | 50 | 0.860 | 1.136 | 1.323 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 3.748 | 7.823 | 8.729 |
| ars_hypertension_age · query con cache applicativa | 50 | 0.482 | 0.715 | 0.842 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 4.236 | 8.093 | 8.980 |
| ars_mortality_window_gap · query con cache applicativa | 50 | 0.362 | 0.657 | 1.011 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 2.003 | 2.261 | 2.298 |
| business_frame_industry_weighted · query con cache applicativa | 50 | 0.678 | 1.287 | 2.202 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.468 | 0.701 | 0.706 |
| business_endpoint_refused · query con cache applicativa | 50 | 0.140 | 0.346 | 0.450 |
| census_young_employment · prima query, nuova istanza | 5 | 1.976 | 2.294 | 2.361 |
| census_young_employment · query con cache applicativa | 50 | 0.383 | 0.602 | 0.687 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.378 | 0.692 | 0.711 |
| census_diploma_trend_refused · query con cache applicativa | 50 | 0.126 | 0.247 | 0.416 |

Allocazioni Python: picco 23.003 MiB; mantenute 10.702 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
