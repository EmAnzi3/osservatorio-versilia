# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `aa83f7d08e110b16075b65328f88d2b69270f4d15f0e84ca71ffdd72e58194b1`; domande `8305df308acd70f5c392eae94e40c26a8cbf2c2c30d8624eda00ee54a2713c7b`.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 147.491 | 185.656 | 192.853 |
| population_current · prima query, nuova istanza | 5 | 2.281 | 7.381 | 7.549 |
| population_current · query con cache applicativa | 50 | 0.309 | 0.759 | 2.371 |
| female_weighted · prima query, nuova istanza | 5 | 0.891 | 1.032 | 1.052 |
| female_weighted · query con cache applicativa | 50 | 0.580 | 1.105 | 1.794 |
| ars_gap · prima query, nuova istanza | 5 | 4.882 | 8.163 | 8.871 |
| ars_gap · query con cache applicativa | 50 | 0.241 | 0.432 | 0.570 |
| aligned_association · prima query, nuova istanza | 5 | 2.833 | 7.694 | 8.547 |
| aligned_association · query con cache applicativa | 50 | 1.500 | 2.231 | 3.156 |
| mismatched_association · prima query, nuova istanza | 5 | 2.394 | 4.937 | 5.516 |
| mismatched_association · query con cache applicativa | 50 | 0.785 | 1.263 | 5.540 |
| ars_hypertension_age · prima query, nuova istanza | 5 | 4.563 | 19.516 | 22.263 |
| ars_hypertension_age · query con cache applicativa | 50 | 0.346 | 0.661 | 1.021 |
| ars_mortality_window_gap · prima query, nuova istanza | 5 | 4.628 | 8.352 | 9.106 |
| ars_mortality_window_gap · query con cache applicativa | 50 | 0.345 | 0.734 | 0.889 |

Allocazioni Python: picco 23.003 MiB; mantenute 10.688 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
