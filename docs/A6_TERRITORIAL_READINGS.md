# A6.5 — prototipo di letture territoriali

Cinque percorsi riproducibili per ciascuno dei sette Comuni: invecchiamento/assistenza domiciliare; lavoro femminile/servizi per l’infanzia; turismo/organizzazione dei servizi; pendolarismo per lavoro; organizzazione scolastica. Le ricette selezionano il catalogo canonico, non duplicano indicatori o valori. Nessuna UI o conclusione di politica viene pubblicata. Questa estensione dipende dagli adapter v11 della #349; non aumenta la copertura del motore né il numero di domande della suite generale.

Ogni record separa osservazioni, calcoli con formula e provenienza, associazione, ipotesi non verificata e opzione da valutare. Una proposta conserva destinatari, evidenze, indicatori di risultato da predisporre, dati mancanti, assunzioni, `approved: false` ed effetto atteso null. Nessuna graduatoria universale o raccomandazione automatica.

## Condizioni metodologiche

- Quota 85+ POSAS 2026 e assistenza ARS 2024 sono contesti affiancati. I loro benchmark sono verificati separatamente sui periodi propri; la correlazione viene rifiutata per `paired_period_mismatch`. Assistenza erogata non misura bisogno insoddisfatto.
- Occupazione femminile 2023 e ricettività potenziale 2024/25 hanno periodi e universi diversi. Correlazione rifiutata; anno educativo non convertito in anno solare. Occorrono domanda, liste d’attesa, costi, orari e accessi intercomunali prima di definire interventi.
- Le notti 2025 e l’intensità 2025/2026 condividono il numeratore: una correlazione non aggiungerebbe evidenza indipendente. Sono calcolati variazione 2023→2025 e confronto regionale dell’intensità con lo stesso denominatore temporale. Servono picchi, escursionisti e carichi effettivi dei servizi.
- Pendolarismo: ingressi, uscite, saldo e autocontenimento conservano l’universo Istat 2021. La correlazione descrittiva di Spearman fra autocontenimento e saldo riguarda tutti i sette comuni (`n=7`, coefficiente `9/14`), non una relazione entro ciascun comune. Componenti condivise, dimensione demografica e campione piccolo limitano l’interpretazione; nessun p-value, intervallo di confidenza o effetto causale viene stimato. Non si deducono corse necessarie, modi di trasporto, flussi di studio o domanda attuale.
- Scuola: alunni, alunni/classi e tempo pieno primaria conservano l’anno scolastico 2024/25. Il confronto con i residenti 0–14 del gennaio 2026 viene rifiutato per periodo incompatibile; anche con periodi allineati servirebbe verificare residenza, età e bacini degli iscritti. I valori non misurano copertura dei residenti, qualità scolastica o bisogno insoddisfatto.

## Riepiloghi del gruppo

Due riepiloghi dichiarano esplicitamente i sette codici comunali e ricostruiscono sei rapporti dalle componenti sommate, senza fare medie dei rapporti comunali:

| Rapporto | Numeratore | Denominatore | Scala | Periodi |
|---|---:|---:|---:|---|
| Alunni/classi | 15.168 | 807 | 1 | 2024/25 |
| Tempo pieno primaria | 2.428 | 5.422 | 100 | 2024/25 |
| Autocontenimento nel proprio comune | 27.041 | 53.921 | 100 | 2021 |
| Saldo per residenti | −1.898 | 160.755 | 1.000 | 2021 / 2021 |
| Ingressi per residenti | 24.982 | 158.520 | 1.000 | 2021 / 2026 |
| Uscite per residenti | 26.880 | 158.520 | 1.000 | 2021 / 2026 |

Le entrate/uscite sommate comprendono movimenti interni al gruppo e non sono flussi lordi al confine della Versilia. L’autocontenimento resta riferito al proprio comune, non all’intero gruppo. I denominatori 2021 e 2026 restano distinti.

Ogni input essenziale mancante o incoerente rende la lettura interessata `not_ready`; nessuna sostituzione con zero o dati precedenti. Le altre letture comunali valide restano disponibili. I riepiloghi richiedono tutti i sette comuni e rifiutano copertura incompleta. I controlli sulle associazioni richiedono il calcolo o il motivo di rifiuto atteso: un errore inatteso impedisce lo stato complessivo di revisione. `ready_for_methodological_review` significa evidenza tecnica completa per la revisione, non politica approvata. Le letture sono descrittive comunali: non causalità o inferenza individuale.

## Riproduzione e gate

Dopo build:

```bash
python scripts/semantic_territorial_readings.py --format json --output /tmp/a6-readings.json
python scripts/semantic_territorial_readings.py --format markdown --output /tmp/a6-readings.md
```

Il JSON schema v2 conserva la precisione e ogni risultato del motore, con Pointer, hash del catalogo e dell’implementazione delle letture. Il Markdown arrotonda solo per lettura e conserva tutte le provenienze distinte dei calcoli, benchmark e riepiloghi; un hash di snapshot non prova la disponibilità live. Il report versionato usa il catalogo effettivo v1.40.0, senza modificarlo. I test sono eseguiti nel gate generale post-build: 35 record e due riepiloghi, territorio/dimensione, componenti e risultati numerici indipendenti, rifiuti temporali, benchmark, tassi standardizzati, mancanti e alterazioni dei carrier. Nessun workflow nuovo.

A6.4 resta parziale: gli altri indicatori/dimensioni hanno motivi espliciti nella matrice derivata. A6.5 e A6.6 restano aperte fino alla revisione metodologica delle domande e del percorso dalle evidenze agli interventi. A7 non avviata.
