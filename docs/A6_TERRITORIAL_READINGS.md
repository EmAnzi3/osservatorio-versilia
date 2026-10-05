# A6.5 — prototipo di letture territoriali

Tre domande riproducibili per ciascuno dei sette Comuni: invecchiamento/assistenza domiciliare; lavoro femminile/servizi per l’infanzia; turismo/organizzazione dei servizi. Le ricette selezionano il catalogo canonico, non duplicano indicatori o valori. Nessuna UI o conclusione di politica viene pubblicata.

Ogni record separa osservazioni, calcoli con formula e provenienza, associazione, ipotesi non verificata e opzione da valutare. Una proposta conserva destinatari, evidenze, indicatori di risultato da predisporre, dati mancanti, assunzioni, `approved: false` ed effetto atteso null. Nessuna graduatoria universale o raccomandazione automatica.

## Condizioni metodologiche

- Quota 85+ POSAS 2026 e assistenza ARS 2024 sono contesti affiancati. I loro benchmark sono verificati separatamente sui periodi propri; la correlazione viene rifiutata per `paired_period_mismatch`. Assistenza erogata non misura bisogno insoddisfatto.
- Occupazione femminile 2023 e ricettività potenziale 2024/25 hanno periodi e universi diversi. Correlazione rifiutata; anno educativo non convertito in anno solare. Occorrono domanda, liste d’attesa, costi, orari e accessi intercomunali prima di definire interventi.
- Le notti 2025 e l’intensità 2025/2026 condividono il numeratore: una correlazione non aggiungerebbe evidenza indipendente. Sono calcolati variazione 2023→2025 e confronto regionale dell’intensità con lo stesso denominatore temporale. Servono picchi, escursionisti e carichi effettivi dei servizi.

Ogni input essenziale mancante o incoerente rende la lettura `not_ready`; nessuna sostituzione con zero o dati precedenti. `ready_for_methodological_review` significa evidenza tecnica completa per la revisione, non politica approvata. Le letture sono descrittive comunali: non causalità o inferenza individuale.

## Riproduzione e gate

Dopo build:

```bash
python scripts/semantic_territorial_readings.py --format json --output /tmp/a6-readings.json
python scripts/semantic_territorial_readings.py --format markdown --output /tmp/a6-readings.md
```

Il JSON conserva la precisione e ogni risultato del motore, con Pointer e hash. Il Markdown arrotonda solo per lettura. Il report versionato usa il catalogo effettivo di #334, senza modificarlo. I test sono eseguiti nel gate generale post-build: 21 record, territorio/dimensione, risultati numerici indipendenti, rifiuti temporali, benchmark, tassi standardizzati, mancanti e alterazioni dei carrier. Nessun workflow nuovo.

A6.4 resta parziale: gli altri indicatori/dimensioni hanno motivi espliciti nella matrice derivata. A6.5 e A6.6 restano aperte fino alla revisione metodologica delle domande e del percorso dalle evidenze agli interventi. A7 non avviata.
