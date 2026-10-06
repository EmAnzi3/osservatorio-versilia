# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `5985ee4cf6b4526c8678ccd5696afa86c47ecef2e166245facea037c3ad9fdcd`; domande `43307cdc83567b307a1affdc1ea1a4f00bf429f8be0bee994035270d6d0a2b6e`.

Hash degli adapter: {"adapterImplementationSha256": "988d1d32a0a754c0707a8c7b0acc4c3af1218bb7548ea824fd2ab6df71a1ff52", "arsAdapterSha256": "6b13af3d84f9313adf9aff0b39f6338fc2a227981053ca7748d54d348b47ef6f", "businessAdapterSha256": "5b1f9c79a0558523cadc802e16060fb98558d0bac1a665e6a230b0ce161e6523", "censusAdapterSha256": "528c7e1e2e66c2490eeef4419dd08f2d05790fc13ca58bfdf34cb369495bd96e", "financeAdapterSha256": "dfac1ca93eeb990105fc188bffc5d76d6c32bb0d021da832b11d65bec3b98879", "territorialAdapterSha256": "403f4143cf5557763af3b90f0b122afe33ee6db8d3270a3299e51e482576b465"}.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 134.865 | 189.446 | 200.645 |
| population_current · prima query, nuova istanza | 5 | 2.103 | 3.279 | 3.488 |
| population_current · query con cache applicativa | 50 | 0.297 | 0.493 | 0.648 |
| female_weighted · prima query, nuova istanza | 5 | 1.025 | 1.233 | 1.238 |
| female_weighted · query con cache applicativa | 50 | 0.477 | 0.764 | 0.884 |
| ars_gap · prima query, nuova istanza | 5 | 3.432 | 6.808 | 7.643 |
| ars_gap · query con cache applicativa | 50 | 0.353 | 2.535 | 46.582 |
| aligned_association · prima query, nuova istanza | 5 | 4.194 | 6.793 | 7.293 |
| aligned_association · query con cache applicativa | 50 | 1.076 | 1.322 | 1.656 |
| mismatched_association · prima query, nuova istanza | 5 | 2.171 | 6.312 | 7.242 |
| mismatched_association · query con cache applicativa | 50 | 0.634 | 1.012 | 10.596 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 3.949 | 7.003 | 7.573 |
| ars_hypertension_age · query con cache applicativa | 50 | 0.532 | 1.057 | 2.235 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 3.496 | 6.752 | 7.447 |
| ars_mortality_window_gap · query con cache applicativa | 50 | 0.370 | 0.555 | 0.810 |
| business_frame_industry_weighted · prima query, nuova istanza | 5 | 1.757 | 2.110 | 2.176 |
| business_frame_industry_weighted · query con cache applicativa | 50 | 0.746 | 1.100 | 1.587 |
| business_endpoint_refused · prima query, nuova istanza | 5 | 0.414 | 0.710 | 0.771 |
| business_endpoint_refused · query con cache applicativa | 50 | 0.142 | 0.279 | 0.412 |
| census_young_employment · prima query, nuova istanza | 5 | 1.483 | 2.276 | 2.399 |
| census_young_employment · query con cache applicativa | 50 | 0.410 | 0.665 | 0.968 |
| census_diploma_trend_refused · prima query, nuova istanza | 5 | 0.363 | 0.511 | 0.544 |
| census_diploma_trend_refused · query con cache applicativa | 50 | 0.148 | 0.323 | 0.834 |
| finance_cash_weighted · prima query, nuova istanza | 5 | 1.443 | 1.878 | 1.913 |
| finance_cash_weighted · query con cache applicativa | 50 | 0.664 | 1.066 | 1.728 |
| finance_benchmark_refused · prima query, nuova istanza | 5 | 1.476 | 1.589 | 1.606 |
| finance_benchmark_refused · query con cache applicativa | 50 | 0.175 | 0.307 | 0.594 |

Allocazioni Python: picco 23.003 MiB; mantenute 10.953 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
