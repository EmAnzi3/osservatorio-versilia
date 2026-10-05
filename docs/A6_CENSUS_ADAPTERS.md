# A6 — censimento, lavoro/istruzione e famiglie

Base #341 pubblicata, main `58f67993`. Motore v7: 11 indicatori aggiuntivi, **56 con adapter / 169 senza su 225** effettivi. Il Source Catalog non materializzato ha copertura separata. Nessun dato pubblico, UI, renderer, asset, golden o workflow modificato.

| Famiglia | Indicatori nuovi | Letture ammesse | Evidenza e limiti |
|---|---|---|---|
| Lavoro residente | employmentRate, unemploymentRate, activityRate | corrente 2024: iniziale 25–64 arrotondato e 18 combinazioni età/sesso; storico nativo 15+ totale | Snapshot SDMX congelato; storici `5-Lavoro.xlsx` nei soli anni acquisiti. Componenti derivati, non certificati come conteggi additivi per ponderazioni |
| Istruzione | diplomaPlus, tertiary | corrente 2024: iniziale 25–64 e 18 combinazioni; storico nativo 25–49 totale | Snapshot SDMX e `4-Istruzione.xlsx`. Diploma 25–64: 1991/2001/2011 tradizionali e 2024 permanente consultabili, senza trend, correlazioni temporali o variazioni attraverso la discontinuità |
| Abitazioni/famiglie | vacantHomes, singleHouseholds, cohabitingHouseholds | quote 2023; prime due anche 2021 | Sezioni censuarie e LIA congelati. Case non occupate da residenti possono essere occupate da non residenti; famiglia unipersonale non misura direttamente solitudine |
| Divario di genere | employmentGenderGap | totale 15–64, 2021/2023 | Differenza dei tassi maschile meno femminile riconciliata: punti percentuali, non percentuale relativa. Dettagli A3 2024 non sostituiscono il totale 2023 |
| Dimensione familiare | householdSize | valore ufficiale pubblicato 2023 | Componenti comunali non riconciliati: evidenza del catalogo e nota di metodo, nessun conteggio ricostruito, storico o ponderazione. Non certificato contro raw comunale |
| Vecchiaia | oldAgeIndex | POSAS 2019–2026 | Fonte effettiva POSAS distinta dal profilo censuario del catalogo; anziani 65+ ogni 100 giovani 0–14, non quota degli anziani sul totale. Benchmark pubblico 2024 non abbinato al corrente 2026 |

## Dimensioni, precisione e periodi

`total` conserva il valore iniziale e la precisione pubblicata. `age:<fascia>|sex:<total/men/women>` legge esclusivamente la parte esplicita, con pointer e universo: il totale iniziale non sostituisce tutte le fasce. Nessuna fusione di età sovrapposte, popolazioni o anni. La dimensione primaria 25–64 e il genere totale sono controllati nei metadati.

Correnti primari 2024, quote case/famiglie 2023 e indice di vecchiaia hanno arrotondamento di un decimale: riconciliazione entro 0,0500001 nelle rispettive unità. Parti esplicite, storici nativi e gap si riconciliano entro 1e-8. Queste tolleranze sono locali all'adapter, non modificano le precondizioni generali. I valori pubblicati rimangono invariati, compresi null; letture parziali richiedono `allowPartial`. Nessuna imputazione dai raw quando il carrier è mancante.

Le serie delle parti sono lette da righe/celle native e riconciliate al carrier. Il tasso di attività storico è la trasformazione dichiarata `100 - tasso di inattività nativo`. Le ultime osservazioni 2024 sono riconciliate al nuovo snapshot. Le date irregolari restano irregolari; nessuna interpolazione annuale. Per il diploma storico tradizionale sono decodificati CSV incorporati, verificati SHA-256, Comune, indicatore e anno. Gli hash XLSX sono dichiarati nell'estrazione congelata: i workbook originali non vengono riletti. Una verifica di snapshot non prova disponibilità live.

## Ponderazione, benchmark e relazioni

Nuova ponderazione ammessa solo per famiglie coabitanti: somma PF9 / somma PF1 ×100 in Comuni distinti, con componenti LIA. Percentuali arrotondate e componenti SDMX derivati non autorizzano ponderazioni implicite. I precedenti adapter e le loro ponderazioni rimangono attivi.

Benchmark totali correnti Toscana/Italia: lavoro e titolo terziario 2024, case/famiglie e gap 2023; record regionali/nazionali e carrier pubblico riconciliati con fonti separate. Nessun benchmark storico o di fascia/sesso. Il diploma regionale da indagine forze di lavoro resta pubblicato come riferimento statistico, ma l'adapter lo rifiuta per differenza di metodo; non è un benchmark censuario verificato. Dimensione familiare, vecchiaia e aggregate Versilia restano fuori da `benchmark_gap` in questo lotto. Nessuna cancellazione A3.

La mappa aggiunge una dipendenza aritmetica del divario dai tassi maschile/femminile e due collegamenti di contesto: istruzione/occupazione e famiglie/abitazioni. Le associazioni su sette Comuni sono descrittive, con pairing, periodi, sensibilità e avvertenze ecologiche: nessuna causalità, disponibilità di case, bisogno assistenziale o priorità politica automatica.

## Gate e residui

**69 domande: 43 calcoli + 26 rifiuti attesi**, con trascrizioni/formule indipendenti. Regressioni su tutte le parti correnti e sette Comuni, serie ammesse, benchmark, duplicati, carrier/componenti alterati, hash CSV, cambio di universo, null e letture parziali. Gate nel preflight generale esistente, senza nuovo workflow.

Report aggiornati: `reports/a6-engine-audit/`; baseline separata a 11 carichi: `reports/a6-census/`. Misure locali sequenziali con cache dichiarata: non SLO né prova concorrente. Riproduzione:

```bash
python scripts/test_semantic_census_adapters.py
python scripts/semantic_engine_audit.py --catalog dist/data/site-data.json --output-dir /tmp/a6-census-audit
python scripts/semantic_question_suite.py --catalog dist/data/site-data.json --output-dir /tmp/a6-census-questions
python scripts/semantic_engine_benchmark.py --catalog dist/data/site-data.json --rounds 50 --output-dir /tmp/a6-census-performance
```

A6.4 resta parziale; A6.5–A6.6 aperte alla revisione; A7 non avviata. Prossimi carrier OpenBDAP. Residui: ponderazioni SDMX e quote arrotondate, benchmark dettagliati/storici, materia prima familiare comunale non riconciliata, continuità diploma tradizionale/permanente. Nessuna acquisizione o ricostruzione onerosa. Blocchi browser locali già riprodotti sulla baseline #341/#339 non incorporati in questo lotto backend; esiti Quick/Full riportati nella PR. Merge solo su istruzione specifica del proprietario.
