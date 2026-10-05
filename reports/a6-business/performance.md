# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `72dec95a7d5ede047deaa8e44420d07aa53282ab53ced990db9ccb12f5621fbb`; domande `75efe3803e947f0b8f97efce9329fcd67f26ff8759ce07593f2f8239a0100822`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 164.620 | 217.075 | 229.865 |
| population_current · prima query, nuova istanza | 5 | 1.693 | 5.503 | 6.398 |
| population_current · query con cache applicativa | 50 | 0.250 | 0.408 | 0.546 |
| female_weighted · prima query, nuova istanza | 5 | 1.151 | 1.512 | 1.588 |
| female_weighted · query con cache applicativa | 50 | 0.549 | 0.810 | 1.301 |
| ars_gap · prima query, nuova istanza | 5 | 3.622 | 7.019 | 7.795 |
| ars_gap · query con cache applicativa | 50 | 0.278 | 0.489 | 0.661 |
| aligned_association · prima query, nuova istanza | 5 | 2.774 | 5.894 | 6.354 |
| aligned_association · query con cache applicativa | 50 | 1.190 | 1.442 | 1.595 |
| mismatched_association · prima query, nuova istanza | 5 | 2.182 | 4.753 | 5.247 |
| mismatched_association · query con cache applicativa | 50 | 0.619 | 0.728 | 0.914 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 3.944 | 6.814 | 7.512 |
| ars_hypertension_age · query con cache applicativa | 50 | 0.384 | 0.631 | 0.883 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.936 | 6.348 | 6.939 |
| ars_mortality_window_gap · query con cache applicativa | 50 | 0.327 | 0.480 | 0.658 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 1.923 | 2.114 | 2.140 |
| business_frame_industry_weighted · query con cache applicativa | 50 | 0.591 | 1.852 | 3.309 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.603 | 0.719 | 0.722 |
| business_endpoint_refused · query con cache applicativa | 50 | 0.136 | 0.267 | 0.453 |

Allocazioni Python: picco 23.003 MiB; mantenute 10.598 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
