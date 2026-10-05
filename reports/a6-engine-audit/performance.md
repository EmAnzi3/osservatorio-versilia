# A6 — baseline delle prestazioni

Catalogo `b9fd34b5cf0f81a84579efefc7554b71b2b515810a53d4fca036fa51d8935dc4`; motore `c1f8eef297a89ef7b532dc669a3614ac188d646113c851e3d520f879818cfcc6`; domande `d713c80aaebb844a166ea24e880a8a192b2ddee723df912ce5496a3bbf4d094f`.

Ambiente: Python 3.12.14 CPython, Linux-6.18.44-x86_64-with-glibc2.39, x86_64; CPU visibili 9, quota cgroup `800000 100000`.

Suite di correttezza PASS prima delle misure. Millisecondi; p95 interpolato. Esecuzione sequenziale locale: non è uno stress test o una promessa di latenza in produzione. Cache filesystem non controllata.

| Carico | Campioni | Mediana ms | p95 ms | Massimo ms |
|---|---|---|---|---|
| Costruzione/validazione motore | 5 | 120.344 | 127.906 | 129.125 |
| population_current · prima query, nuova istanza | 5 | 1.519 | 1.850 | 1.917 |
| population_current · query con cache applicativa | 50 | 0.215 | 0.474 | 0.618 |
| female_weighted · prima query, nuova istanza | 5 | 0.819 | 0.960 | 0.983 |
| female_weighted · query con cache applicativa | 50 | 0.395 | 0.646 | 0.713 |
| ars_gap · prima query, nuova istanza | 5 | 2.924 | 4.482 | 4.854 |
| ars_gap · query con cache applicativa | 50 | 0.186 | 0.321 | 0.412 |
| aligned_association · prima query, nuova istanza | 5 | 2.071 | 3.719 | 4.119 |
| aligned_association · query con cache applicativa | 50 | 0.814 | 0.911 | 1.195 |
| mismatched_association · prima query, nuova istanza | 5 | 1.797 | 3.750 | 4.224 |
| mismatched_association · query con cache applicativa | 50 | 0.533 | 0.840 | 0.903 |

Allocazioni Python: picco 23.003 MiB; mantenute 10.292 MiB. Misura separata dai tempi; non include memoria nativa o RSS totale.

I carichi comprendono confronto, rapporto ponderato, benchmark ARS, associazione descrittiva e rifiuto temporale. Non attestano le prestazioni di tutti i carrier, di un server concorrente o del futuro interprete linguistico. Prima di ottimizzare o fissare budget occorre ripetere su ambiente di esecuzione stabile.
