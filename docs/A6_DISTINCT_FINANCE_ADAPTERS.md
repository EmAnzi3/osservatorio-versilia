# A6 v9 — debito, opere, sicurezza e attività fiscale

Riutilizzo dei dati pubblicati, senza nuove acquisizioni o modifiche UI. Quattro carrier aggiuntivi: 85 indicatori con adapter e 140 senza su 225. `total` mantiene la lettura predefinita del carrier; le altre dimensioni sono scelte esplicite, non nuovi indicatori né punteggi territoriali.

| Carrier | Dimensioni | Evidenza / calcoli ammessi |
|---|---|---|
| Debito finanziario | `part:debtPerResident`, `part:interestShare`, `part:debtSustainability` | Snapshot salute-finanziaria v129, 2019–2025. D1 e interessi hanno componenti; rapporto delle somme ammesso solo per le prime due letture. |
| Recupero tributario | `part:recoveryPerResident`, `part:recoveryTotal`, `part:daitContribution` | Snapshot fiscal-lotto-b 2025. Rapporto delle somme solo per recupero locale/popolazione del dataset. Totale locale e contributo DAIT sono importi distinti. |
| Opere pubbliche | `total` | Stock monitorato etichettato 2026, carrier normalizzato canonico. Nessuna serie, ponderazione o somma di progetti senza importi congelati e prova di CUP/perimetri disgiunti. |
| Missione 03 | `total` | Carrier normalizzato canonico, 2024–2025. Variazione a due punti leggibile; trend richiede più osservazioni. Nessuna ponderazione da importi grezzi assenti. |

## Debito e perimetro storico

Il D1 è uno stock al 31 dicembre, normalizzato sui residenti al 1° gennaio dell'esercizio. Non include automaticamente debiti commerciali, fuori bilancio o passività della procedura OSL. Gli interessi sono impegni sul denominatore degli accertamenti correnti, non una quota della spesa. Importi nominali; aggregati comunali lordi, non conti territoriali consolidati.

Il PDI 10.3 conserva la provenienza annuale: valore ufficiale arrotondato; Camaiore 2023–2024 /100; Forte dei Marmi 2019 e 2023–2025 ricostruito dai componenti già congelati, zero verificato negli ultimi tre anni. Il motore riconcilia queste eccezioni ma non ricostruisce numeratori dai rapporti arrotondati e non pondera il PDI. Gli archivi v129 restano distinti dalle revisioni dello snapshot legacy bilanci: hash e provenienze non vengono fusi.

Massarosa: dissesto 2019 e gestione OSL introducono un perimetro separato. Le serie restano leggibili con avvertenza; variazioni, trend e correlazioni temporali del debito sono rifiutati finché non è attestata la continuità del perimetro. Il confronto corrente non diventa una graduatoria di salute finanziaria.

## Recupero locale e contributo DAIT

Recupero locale: somma dei codici SIOPE esplicitamente classificati come riscossi a seguito di verifica e controllo, cumulato dicembre 2025. Totale, categorie e singoli codici sono riconciliati. Il valore per residente usa `populationIstat` dello stesso dataset: per Massarosa 21.806, distinto dai 21.782 al gennaio 2026 usati da altri carrier di cassa. La data precisa di questa popolazione non è congelata; il motore non la deduce dalla coincidenza numerica né la sostituisce.

DAIT: contributo assegnato nel 2025 per riscossioni erariali 2024 generate da segnalazioni comunali. Espone separatamente periodo dell'assegnazione e dell'incasso sottostante. Gli zeri dei non beneficiari seguono la policy pubblicata dell'elenco completo, non significano assenza di evasione o di lavoro dell'ufficio tributi. La correlazione automatica DAIT/altre misure è rifiutata finché non esiste una regola di allineamento esplicita. Nessuno dei due carrier misura tasso di evasione o efficacia amministrativa.

## Limiti dell'evidenza

Opere e Missione 03 sono riconciliate al carrier normalizzato canonico con hash e puntatori; questa prova riguarda la lettura pubblicata, non l'estrazione grezza o il servizio live. Non si ottengono importi moltiplicando rapporti per popolazioni candidate. Opere monitorate non sono spesa annuale, avanzamento o effetti; Missione 03 comprende corrente/capitale e non misura reati, agenti, prestazioni o sicurezza percepita.

Benchmark pubblici conservati, `benchmark_gap` rifiutato senza componenti/perimetro congelati coerenti. Anni mancanti e null preservati, copertura parziale solo con opt-in. Snapshot riusciti non certificano disponibilità live. A6.4 resta parziale; A6.5–A6.6 aperte, A7 non avviata.

## Mappa, domande e verifica

Quattro contesti selezionati: D1/interessi, recupero locale/entrate correnti, opere/spesa capitale, Missione 03/spesa sociale. I primi, secondi e quarti permettono associazioni descrittive comunali con basi/denominatori espliciti; stock 2026/spesa 2025 rifiuta il calcolo congiunto. Nessuna ricerca indiscriminata di correlazioni, causalità o priorità politica automatica.

Regressioni su dimensioni, sette Comuni e periodi ammessi; numeri indipendenti, componenti/correzioni alterati, null, duplicati e cambi di denominatore. Suite cumulativa 103 domande (63 calcoli, 40 rifiuti attesi). Prestazioni separate in `reports/a6-distinct-finance/`, senza SLO, concorrenza o garanzia di cache disco fredda.

```bash
python scripts/test_semantic_distinct_finance_adapters.py
python scripts/semantic_engine_audit.py --output-dir /tmp/a6-distinct-audit
python scripts/semantic_question_suite.py --output-dir /tmp/a6-distinct-audit
python scripts/semantic_engine_benchmark.py --rounds 50 --output-dir /tmp/a6-distinct-performance
python scripts/preflight.py --quick
python scripts/preflight.py --full
```
