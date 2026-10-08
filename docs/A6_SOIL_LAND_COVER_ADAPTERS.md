# A6 — suolo ISPRA e copertura UCS

Il motore v15 aggiunge tre carrier effettivi già materializzati dalla build: stock di suolo consumato ISPRA, incremento lordo/netto ISPRA e uso/copertura UCS Regione Toscana. 125/225 effettivi, 85/181 sorgente; 100 residui, 35 ambientali. Le due vecchie righe sorgente ISPRA non sono il profilo effettivo multidimensionale: il motore non le certifica come adapter interrogabile. Nessuna modifica a dataset, asset, renderer, golden o workflow. A6.4 resta parziale, A6.5–A6.6 aperte e A7 non avviata.

## Fonti e misure

| Carrier | Snapshot nativo | Dimensioni e periodi |
|---|---|---|
| `landUse` | `territorio-v137-official.json`, ISPRA edizione 2025 | stock ha, % superficie ISPRA e m²/residente; 2006, 2012, 2015–2024; denominatori residenti solo 2019–2024 |
| `landUseChange` | medesima edizione ISPRA | lordo/netto ha; endpoint 2012, 2015–2024; netto negativo preservato |
| `landCoverProfile` | `territorio-ucs-v136.json`, UCS Toscana | cinque macroclassi e cinque dettagli, ha/% sul totale UCS; 2007, 2010, 2013, 2016, 2019 |

Ogni cella è riconciliata con gli input congelati e conserva hash, puntatori, periodo, unità e metodo. I residenti vengono dal record ISPRA dello stesso anno: non si usa POSAS corrente per riscrivere le normalizzazioni storiche. Nessuna imputazione prima del 2019.

Per lo stock ISPRA le percentuali ufficiali a tre decimali e i m²/residente a sei decimali restano in `publishedValue`; `value` espone il rapporto dei componenti nativi. La riconciliazione rispetta mezzo millesimo/mezzo milionesimo rispettivamente. I rapporti del gruppo usano le somme degli ettari sul proprio denominatore areale o dei m² sui residenti ISPRA; nessuna media di percentuali comunali e nessuna pretesa di precisione superiore agli input. Il sito resta invariato.

UCS usa il proprio totale cartografico. Non viene sostituito dalla superficie Istat, ISPRA o CFI. Le prime cinque categorie formano la partizione; boschi/seminaturale non forestale sono dettagli del gruppo boscato-seminaturale, seminativi/colture permanenti del gruppo agricolo e verde urbano cartografico dell'artificializzato. Non si sommano macroclassi e dettagli. I rapporti del gruppo riguardano una sola categoria selezionata su comuni distinti; gli ettari delle categorie restano consultabili, senza rapporto ponderato artificiale.

## Serie e limiti

Le serie sono consultabili nelle annualità effettivamente congelate, senza riempire 2007–2011 o 2013–2014 ISPRA. Non è acquisita una prova indipendente di continuità metodologica sufficiente per trend, variazioni o correlazioni temporali: questi calcoli vengono rifiutati. Gli endpoint degli incrementi 2012 e 2015 non attestano intervalli annuali uguali ai successivi. Nessuna annualizzazione automatica.

Netto negativo può riflettere ripristini o riclassificazioni: non certifica un effetto di una politica. Gli incrementi congelati non vengono ricostruiti dalla differenza degli stock arrotondati; per Camaiore 2024 il netto nativo è 1,10 ha, mentre la differenza dei due stock pubblicati è 1,00 ha.

Stock consumato ISPRA, copertura UCS e bosco CFI sono definizioni distinte. Il contesto nel grafo fra ISPRA 2024 e UCS 2019 conserva le osservazioni ma rifiuta la correlazione automatica per periodi diversi. Nessun indice sintetico ambientale, causalità o priorità politica generata.

Benchmark Toscana/Italia: solo quota ISPRA 2024 dal gate PASS di `a3-ispra-soil-benchmark-2024.json`. Non ci sono componenti regionali congelati per le altre viste. L'incremento netto regionale/nazionale è presente nella fonte, ma il confronto con un singolo comune su totali territoriali di dimensione diversa non è stato metodologicamente autorizzato per questo adapter: viene rifiutato, senza dichiararlo indisponibile. Nessun benchmark UCS acquisito.

## Verifiche

1.456 celle interrogate correnti/storiche contro input fissi trascritti dagli snapshot nativi, con aritmetica indipendente, aliquote territoriali, denominatori residenti, macroclassi/dettagli, netto negativo e prove avversarie su area, cohort, periodi e fonti. Il conteggio include alias e ripetizioni corrente/serie, non rappresenta 1.456 dati distinti. Suite cumulativa 214/214: 136 calcoli, 78 rifiuti attesi; 40 collegamenti tipizzati, 34 carichi di prestazione. Le 35 letture territoriali e due riepiloghi restano invariati.

```bash
python scripts/test_semantic_soil_adapters.py
python scripts/semantic_question_suite.py --output-dir /tmp/a6-soil
python scripts/semantic_engine_audit.py --output-dir /tmp/a6-soil
python scripts/semantic_engine_benchmark.py --output-dir /tmp/a6-soil
python scripts/preflight.py --full
```

Report in `reports/a6-soil/`. Gate locali e CI sul candidato; merge/pubblicazione con approvazione esplicita del proprietario.
