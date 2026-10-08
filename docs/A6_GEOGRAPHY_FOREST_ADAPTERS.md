# A6 — geografia comunale e copertura forestale

Il motore v14 aggiunge quattro carrier dell'Effective Public Catalog: superficie comunale, densità abitativa, profilo altimetrico e copertura forestale. Copertura derivata: 122/225 effettivi, 85/181 sorgente; 103 residui, 38 ambientali. I quattro carrier sono materializzati dalla build, non presenti nel catalogo sorgente. Nessuna nuova acquisizione o modifica a dataset, renderer, asset, golden e workflow. A6.4 resta parziale; A6.5–A6.6 e revisione metodologica restano aperte.

## Fonti, date e precisione

| Carrier | Base congelata | Dimensioni e limiti |
|---|---|---|
| Superficie comunale | Istat 31/12/2021, `biometria-comune-v135.json` | km²; nessuna serie territoriale ricostruita |
| Densità | POSAS 1/1/2026 / superficie Istat 31/12/2021 | Residenti per km²; componenti, hash e date espliciti. Non presenza giornaliera né domanda di servizi |
| Profilo altimetrico | Istat 31/12/2021, otto fasce e quote min/media/max verificate | Sintesi >=300 m a un decimale, otto parti a quattro decimali; quote in metri, anche negative. Nessun ettaro retro-derivato dalle percentuali |
| Copertura forestale | CFI nominale 2020, aggiornata al 2024; rapporto giugno 2026 | Indice e superficie forestale in ettari. Data del rapporto distinta dalla carta; nessuna serie con Boschi UCS |

Ogni carrier è riconciliato per comune, unità, data e valore alla fonte congelata. La popolazione della densità passa attraverso l'adapter POSAS con riconciliazione nativa; il denominatore forestale è riconciliato alla superficie Istat 2021. I valori pubblici mancanti restano mancanti.

Due rapporti del gruppo ammessi: `populationDensity/total` e `forestCoverIndex/total`, entrambi come rapporto delle somme delle componenti native. Per il bosco `value` è il rapporto derivato dagli ettari congelati, mentre `publishedValue` conserva l'indice ufficiale a tre decimali, riconciliato entro mezzo millesimo. Il catalogo pubblico non viene modificato e il rapporto derivato non implica precisione maggiore dei suoi input. Nessuna media delle percentuali comunali.

Per l'altimetria il riepilogo arrotondato resta quello pubblicato. Minimo, media e massimo non vengono aggregati fra comuni; l'esistenza di quote percentuali e superficie comunale non viene usata per inventare componenti native delle fasce. `weighted_ratio` rifiutato. Nessun trend o cambio temporale per i quattro carrier: una sola base congelata, benché alcune date siano composte.

## Benchmark e relazioni

Toscana/Italia da `a3-istat-geography-benchmark-2021.json`, gate PASS, 273/7.904 comuni e riconciliazione 7/7. La superficie di riferimento è la **superficie media per comune**, non il totale regionale/nazionale. Il motore conserva questa distinzione nel risultato. La densità usa popolazione aggregata 2026 / superficie aggregata 2021, con verifica del benchmark POSAS; il profilo altimetrico confronta la sintesi comunale arrotondata >=300 m con la quota territoriale regionale/nazionale. Nessun benchmark delle singole fasce o delle quote min/media/max; nessun benchmark forestale congelato, quindi rifiutato.

Il grafo aggiunge due contesti: superficie 2021/densità 2026 e altimetria 2021/carta forestale 2020–2024. Le osservazioni sono disponibili, ma la correlazione è rifiutata per periodi diversi. Nessuna concatenazione di fotografie, lettura ecologica causale, priorità politica o giudizio automatico di qualità. La superficie condivisa fra indici può creare dipendenze matematiche, non effetti indipendenti.

## Verifiche riproducibili

118 osservazioni indipendenti: 112 celle comunali/dimensioni e sei benchmark. Riferimenti trascritti, due rapporti del gruppo, date miste, indice forestale arrotondato, fasce, altitudini negative, null, denominatori non validi e modifiche avversarie alle fonti. Suite cumulativa: 197 domande, 125 calcoli e 72 rifiuti attesi; 39 collegamenti tipizzati, 31 carichi di prestazione. Le 35 letture territoriali e i due riepiloghi restano invariati.

```bash
python scripts/test_semantic_geography_adapters.py
python scripts/semantic_engine_audit.py --output-dir /tmp/a6-geography
python scripts/semantic_question_suite.py --output-dir /tmp/a6-geography
python scripts/semantic_engine_benchmark.py --output-dir /tmp/a6-geography
python scripts/preflight.py --full
```

Report in `reports/a6-geography/`. Prestazioni sequenziali locali, non promessa di latenza produttiva. Quick/Full locali e CI sul candidato prima della revisione per merge; merge/pubblicazione con approvazione esplicita del proprietario.
