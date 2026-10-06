# A6 v10 — demografia e scuola

Riutilizzo di 16 indicatori già pubblicati: 101/225 con adapter effettivo, 68/181 nel catalogo sorgente. Nessuna acquisizione, modifica ai numeri pubblici, UI, asset o golden. Gli adapter restituiscono il valore pubblicato e ne verificano le componenti congelate; un valore mancante rimane mancante anche se lo snapshot contiene componenti numeriche.

| Famiglia | Periodo nativo | Evidenze e operazioni |
|---|---|---|
| Dipendenza strutturale/anziani | Stock al 1 gennaio, 2019–2026 | POSAS; fasce 0–14, 15–64, 65+. Sesso soltanto nel 2026. Rapporto delle somme, non media degli indici. Popolazione in età lavorativa diversa da occupati. |
| Residenti non italiani | Stock al 1 gennaio, 2024–2025 | RCS: cittadinanza, diversa da luogo di nascita e origine dei trasferimenti. Quota e conteggio; conteggi per sesso solo 2025. Nessuna quota per sesso senza il suo denominatore residente. Paesi non adattati né incrociati. |
| Variazione demografica | Intervalli espliciti `2019-2019` … `2019-2026` | POSAS; base fissa gennaio 2019. Il solo endpoint `2026`, trend annuale e correlazioni temporali su finestre cumulate vengono rifiutati. |
| Dinamica naturale | Eventi annuali 2019–2025 | P02: nati, morti, saldo; popolazione media gennaio/dicembre. Flag provvisorio conservato. Non è il saldo complessivo della popolazione. |
| Trasferimenti interni/estero/totali | Eventi annuali 2019–2024 | Numeratori interni congelati nel composito; estero/totali correnti dal carrier canonico e popolazione media P02. Storia estero/totali normalizzata senza numeratori raw: leggibile, non ponderabile. Totali riconciliati a interno+estero, anche nella storia. |
| Sedi scolastiche | Stock etichettato 2025 | Carrier canonico; conteggio e normalizzazione pubblicata. Data precisa dello stock e del denominatore non attestata: niente ponderazione, storia o correlazione. Sedi diverse da edifici. |
| Alunni, alunni/classe, primaria tempo pieno | Anno scolastico `2024/25` | Conteggi LIA/MIM delle scuole localizzate: alunni/classi e primaria tempo pieno/totale primaria. Ponderazione solo dei rapporti con componenti; volume alunni comunale vs regionale non comparabile. Nessuna storia acquisita. |
| Documenti, accessibilità, dotazioni, età, trasporti edifici | Anno scolastico `2024/25`; dati al 6 agosto 2025 | 109 edifici unici. Quote sulle risposte definite per ciascun campo; quota non definita sul totale edifici. CPI, SCIA e rinnovo separati. Nessuna equiparazione di assenza, risposta sconosciuta e zero. |

## Acquisizione e provenienza

Ogni risposta conserva hash del catalogo e degli adapter, puntatore al valore/periodo, hash e puntatori degli snapshot, comune/codice e date o basi del numeratore/denominatore. L’identità territoriale viene confrontata con il carrier versionato. Le evidenze MIM includono il manifest dei download congelati: non attestano che il download live funzioni oggi. Nessuna chiamata di rete è necessaria per interrogare il motore.

I numeratori correnti dei trasferimenti con l’estero provengono dai conteggi già pubblicati, non da una nuova riconciliazione dell’archivio originario. Le serie normalizzate conservano questa limitazione. Gli aggregati dei trasferimenti sono eventi lordi comunali, comprendono movimenti tra comuni selezionati e non contano persone uniche. I rapporti aggregati non misurano attrattività o cause dello spostamento.

I benchmark vengono riconciliati a snapshot con componenti e periodo coerenti. Per edifici, CPI/SCIA/rinnovo, palestra e singoli TPL non hanno componenti regionali congelate: lo scostamento resta rifiutato. Gli alunni sono localizzati nella scuola, non necessariamente residenti nel comune; la presenza di mensa/trasporto/accessibilità non misura capienza, qualità o accesso individuale.

## Collegamenti e domande

Cinque collegamenti selezionati nella mappa derivata: saldo naturale/trasferimenti **2024** esplicito, cittadinanza/trasferimenti correnti (rifiuto per periodo), tempo pieno/mensa **2024/25**, accessibilità/trasporto edifici e sedi/alunni (rifiuto per date non attestate). Nessuna correlazione automatica o pretesa causale. I saldi naturale e migratorio non chiudono un bilancio demografico completo senza le rettifiche statistiche.

Suite cumulativa: **130 domande**, **81 calcoli** e **49 rifiuti attesi**. Il manifest conserva le aspettative aritmetiche indipendenti e le ragioni dei rifiuti. Le due nuove associazioni verificano copertura e avvertenze; non validano spiegazioni territoriali o effetti delle politiche. Regressioni: **1.379 osservazioni** su dimensioni, sette comuni e periodi nativi, riferimenti numerici trascritti dagli snapshot, denominatori alterati/mancanti, null, risposte nuove e identità incoerenti.

## Verifica e riproduzione

Il Quick generale include regressioni, audit e domande sul catalogo effettivo tramite `test_site_consistency.py`. Nessun nuovo workflow. Baseline separata in `reports/a6-demography-school/`: 19 carichi, inizializzazione, query su nuova istanza/con cache e allocazioni Python; niente rete, concorrenza, garanzia di cache disco fredda o SLO.

```bash
python scripts/test_semantic_demography_school_adapters.py
python scripts/semantic_engine_audit.py --output-dir /tmp/a6-demography-school
python scripts/semantic_question_suite.py --output-dir /tmp/a6-demography-school
python scripts/semantic_engine_benchmark.py --output-dir /tmp/a6-demography-school
python scripts/preflight.py --quick
python scripts/preflight.py --full
```

Recuperate le correzioni dei test ERP/PNRR rimaste soltanto nel checkout precedente alla pubblicazione #344: attendono DOM, contenuto richiesto e font caricati. La disponibilità di fotografie Wikimedia esterne non determina la prontezza del dato. Sono preservati controllo della risposta HTTP, timeout dei contenuti, verifiche geometriche, golden e richieste reali. I test corretti erano passati sia sul candidato precedente sia sulla baseline pubblicata. Nel primo Quick v10 completo, `test_visual_grammar.py` ha fallito una navigazione Diploma a 30 secondi in attesa di `networkidle`; il test originale ripetuto integralmente passa su baseline e candidato, senza riprodurre il timeout. Le richieste pendenti del tentativo originale non erano strumentate: nessun URL/esito HTTP remoto attribuito retroattivamente. Anche questo test ora verifica il rendering client dopo catalogo/clima, indicatore selezionato, scala e font: il solo DOM prerenderizzato non garantisce interazioni pronte. Tutte le asserzioni originali restano; test corretto integrale PASS su candidato e baseline (34,70/32,72 s osservati, non budget). Full locale e CI del lotto verificano l’integrazione.

A6.4 resta parziale (124 indicatori senza adapter); A6.5–A6.6 aperte, A7 non avviata. Passo successivo: scegliere dal backlog derivato un gruppo con dati acquisiti e componenti verificabili, quindi verificare le letture territoriali con domande trasversali. Le manutenzioni delle fonti rimangono nei loro lotti separati.
