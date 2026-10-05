# A6 — Rendiconto e SIOPE, motore v8

Lotto sui dati già pubblicati e snapshot versionati. Nessuna acquisizione live, modifica dati o UI. Il catalogo resta canonico; gli elenchi nel codice definiscono regole di adattamento, non un inventario pubblico parallelo. Le operazioni restano soggette alle guardie A6.2–A6.3.

| Gruppo | Indicatori | Evidenza e operazioni |
|---|---|---|
| Rendiconto con componenti | Entrate correnti, spesa corrente/capitale, entrate proprie, riscossione/pagamento corrente, risultato disponibile, missioni istruzione/sociale/ambiente/mobilità/cultura+sport/turismo+sviluppo/sviluppo | 14 carrier; raw `bilanci-v1.6.0.json`, rapporti riconciliati, rapporto delle somme ammesso |
| Piano indicatori | Spese rigide | PDI 01.01 ufficiale arrotondato; nessuna ponderazione implicita |
| Estensione Rendiconto | FCDE, fondo cassa finale, servizi generali, assetto territorio, soccorso civile | 5 carrier/serie normalizzate `bilanci-v139.json`; importi originali non congelati, nessun numeratore ricostruito o rapporto ponderato |
| SIOPE | Pagamenti complessivi/correnti/capitale, incassi, saldo annuale | 5 carrier; raw `siope-history-v1.6.0.json`, rapporto delle somme ammesso |

## Periodi e universi

Rendiconto: esercizio 2019–2025, residenti al 1° gennaio dello stesso anno. SIOPE: movimenti cumulati a dicembre, residenti al 1° gennaio successivo; la popolazione ISTAT nel CSV SIOPE è distinta dal denominatore adottato. Il risultato e le osservazioni espongono `numeratorPeriod`, `denominatorPeriod` e data del denominatore quando applicabile. Quote contabili usano invece accertamenti/impegni, non residenti.

Spese rigide hanno nel carrier solo 2019, 2020, 2021, 2022 e 2025. Soccorso civile solo 2021–2025. Gli anni non pubblicati non vengono aggiunti anche se un altro snapshot contiene numeri candidati. Nessuna riga assente è trasformata in zero. Valori negativi del risultato disponibile o saldo annuale sono conservati. Copertura parziale richiede opt-in; nessuna imputazione.

La somma dei conti comunali è lorda: non elimina eventuali trasferimenti fra enti e non rappresenta un conto territoriale consolidato. Le missioni comprendono impegni correnti e in conto capitale. Non misurano destinatari, accessibilità, prestazioni effettivamente erogate o impatto di una politica. Incassi/pagamenti di cassa possono includere residui; non coincidono con accertamenti/impegni di competenza. Il saldo annuale incassi meno pagamenti è un flusso; il fondo cassa finale è uno stock, anche vincolato. FCDE è accantonamento prudenziale, non evasione o perdita osservata. Importi in euro nominali: trend e variazioni non indicano crescita reale.

## Provenienza e revisioni

Ogni osservazione include puntatori del catalogo, hash snapshot, record sorgente e URL dell'archivio/download annuale. Gli hash originali sono attestazioni dell'estrazione congelata: gli ZIP/CSV non vengono scaricati o riletti dal motore. Snapshot/build riusciti non provano disponibilità live.

L'estensione v139 dichiara revisioni dei contenitori e dei file selezionati rispetto alla baseline v1.6.0. Il motore conserva gli hash distinti e segnala la revisione; non pretende identità di rilascio né ricalcola i carrier precedenti da un archivio più recente. Per i cinque carrier normalizzati la riconciliazione riguarda l'estrazione congelata, **non** un importo grezzo assente. Nessuna ponderazione ottenuta moltiplicando una quota pubblicata per un denominatore candidato.

## Benchmark e residui

`benchmark_gap` è rifiutato in questo lotto. Il candidato Rendiconto Toscana 2025 è già `CANDIDATE_REJECTED` (271/273 Comuni); non viene promosso. I tre benchmark SIOPE pubblici restano intatti: il relativo snapshot espone valori e copertura, senza importi regionali congelati sufficienti per la riconciliazione raw adottata qui. Italia non acquisita. Nessun benchmark o valore pubblico viene cancellato.

Debito composito, opere pubbliche BDAP-MOP, sicurezza e recupero fiscale hanno carrier e perimetri distinti: restano nel backlog, senza essere assorbiti automaticamente dal profilo finanziario. Non è attestata copertura completa del motore.

## Collegamenti e verifica

Il saldo annuale è verificato come incassi per residente meno pagamenti per residente, con identiche date del denominatore. È una dipendenza matematica, non evidenza statistica indipendente. Due coppie contestuali selezionate: incassi/entrate accertate e impegni istruzione/politiche sociali. Associazioni descrittive su sette Comuni, denominatori condivisi e perimetri contabili espliciti; nessuna causalità, graduatoria di qualità o priorità politica automatica.

Regressioni: tutti i carrier ammessi, sette Comuni e tutti gli anni pubblicati; numeri indipendenti, componenti alterati, anni assenti, date residenti cambiate, missioni mancanti, null, rifiuti di ponderazioni/benchmark. Suite domande cumulativa, audit completo e baseline separata con cache. Comandi:

```bash
python scripts/test_semantic_finance_adapters.py
python scripts/semantic_engine_audit.py --output-dir /tmp/a6-finance-audit
python scripts/semantic_question_suite.py --output-dir /tmp/a6-finance-audit
python scripts/semantic_engine_benchmark.py --rounds 50 --output-dir /tmp/a6-finance-performance
python scripts/preflight.py --quick
python scripts/preflight.py --full
```
