# Massarosa: attività economiche e opportunità per i residenti

A Massarosa i dati descrivono un territorio con una base di attività locali cresciuta tra 2018 e 2023 e un tasso di occupazione residente 2024 superiore a quello di Viareggio. Le due informazioni sono utili insieme, ma riguardano periodi e popolazioni differenti: non dimostrano che la crescita delle attività abbia creato lavoro per i residenti.

## Che cosa osserviamo

| Misura | Periodo | Massarosa | Viareggio |
|---|---|---:|---:|
| Occupati fra i residenti di 25–64 anni | 2024 | 73,4% | 71,9% |
| Crescita cumulata delle unità locali ASIA rispetto al 2018 | 2018–2023 | +7,0% | +9,2% |
| Addetti medi annui nelle unità locali ASIA, sul luogo di lavoro | 2023 | 4.938,33 | 22.358,35 |
| Valore aggiunto industriale nominale | 2023 | 92,85 milioni € | 524,10 milioni € |
| Retribuzione lorda media per dipendente nell’industria | 2023 | 31.226 € | 30.393 € |

Il tasso di occupazione di Massarosa supera quello di Viareggio di 1,5 punti percentuali. La crescita cumulata delle unità locali ASIA è invece inferiore. Questo confronto rende visibili due dimensioni dello sviluppo: le condizioni dei residenti e l’attività localizzata. Non produce una graduatoria complessiva dei Comuni.

Gli addetti ASIA sono una media annua: per questo il valore può avere decimali. Non sono il numero dei residenti occupati. Gli importi industriali assoluti risentono anche della diversa dimensione delle economie locali; non sono misure di produttività per abitante.

## Una trasformazione osservabile nei servizi

A Massarosa il valore aggiunto dei servizi passa, in termini nominali, da 94,02 milioni di euro nel 2015 a 165,94 milioni nel 2023. La differenza verificata è 71,92 milioni.

È un segnale di cambiamento della produzione monetaria dei servizi. Non è crescita a prezzi costanti e non dimostra che lavoratori siano passati dall’industria ai servizi. Per rispondere a quella domanda occorrono un pannello settoriale omogeneo e informazioni sulle transizioni professionali. La retribuzione industriale media non descrive reddito disponibile, distribuzione dei salari o qualità dei contratti.

## Perché interessa chi deve decidere

Queste evidenze suggeriscono quali domande porre a imprese, servizi per il lavoro e formazione: quali professionalità vengono richieste? Quali residenti incontrano barriere di accesso? Gli spostamenti, gli orari e i servizi alle famiglie limitano alcune opportunità? Sono ipotesi di approfondimento; dai dati presentati non deriva automaticamente un programma di formazione, una nuova area produttiva o un incentivo.

Il Comune può approfondire accessibilità delle aree e servizi locali; politiche del lavoro e formazione richiedono il coinvolgimento regionale e degli attori competenti. Competenze e deleghe vanno verificate negli atti vigenti prima di definire un intervento.

## Che cosa manca e come seguire un eventuale intervento

Mancano dati recenti e contemporanei, transizioni dei residenti, profili richiesti, qualità e durata dei contratti. Non possiamo descrivere la congiuntura del 2026 con il solo dato ASIA 2023.

Per un programma specifico andrebbero definiti destinatari, accessi, completamenti e risultati occupazionali a distanza di tempo, mantenendo distinti partecipanti e popolazione residente. Una variazione comunale dopo l’intervento non ne dimostra l’effetto: servono un disegno di valutazione e un confronto appropriato.

## Il perimetro di questa dimostrazione

Viareggio è un confronto interno alla Versilia con dati compatibili per ciascuna misura, non un territorio certificato come simile a Massarosa. Differenze di dimensione, settori e pendolarismo vanno considerate; non è stato acquisito un pannello di territori comparabili.

L’Atlante Registro Imprese 2025 resta un universo distinto da ASIA: le sue 20.325 unità locali nei sette Comuni non possono essere aggiunte agli stock ASIA o usate come prosecuzione della stessa serie. Il totale è riconciliato dalla query `atlas_territory_2025`; nessuna somma dei livelli ATECO entra nelle misure sopra.

## Fonti e riproducibilità

I valori esposti sono arrotondati per la lettura. Il JSON riproducibile conserva tutta la precisione, richieste, risultati, hash degli snapshot e puntatori. Le fonti sotto sono quelle delle osservazioni acquisite, non una verifica della loro disponibilità online oggi.

Catalogo congelato `1416209ca86f27b4eaeede51e59a90edd0b24167f75c60e5157df4583678d710`; motore `93c83970aaac371cda2d595eb2f73cc03a4848f12c1c98d54bdf1c7785240afe`.

- `census_employment_primary`: `compare`, `employmentRate`, dimensione `total`; periodi 2024. [https://esploradati.istat.it/SDMXWS/rest](https://esploradati.istat.it/SDMXWS/rest)
- `business_asia_cumulative`: `compare`, `localUnitsChange`, dimensione `total`; periodi 2018-2023. [https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500DICA,1.0/DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7](https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500DICA,1.0/DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7)
- `business_asia_employment`: `compare`, `localEmployees`, dimensione `total`; periodi 2023. [https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500DICA,1.0/DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7](https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500DICA,1.0/DICA_ASIA/DICA_ASIAULP/183_1163_DF_DICA_ASIAULP_TERRIFDATA_7)
- `business_frame_industry_va`: `compare`, `businessValueAdded`, dimensione `sector:industry`; periodi 2023. [https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/](https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/)
- `business_frame_industry_wages`: `compare`, `averageGrossRemunerationPerEmployee`, dimensione `sector:industry`; periodi 2023. [https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/](https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/)
- `business_frame_services_history`: `absolute_change`, `businessValueAdded`, dimensione `sector:services`; periodi 2015, 2023. [https://www.istat.it/comunicato-stampa/risultati-economici-delle-imprese-a-livello-territoriale-ampliamento-del-dettaglio-di-analisi-anno-2015/](https://www.istat.it/comunicato-stampa/risultati-economici-delle-imprese-a-livello-territoriale-ampliamento-del-dettaglio-di-analisi-anno-2015/); [https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/](https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/)
- `atlas_territory_2025`: `compare`, `economyActivityAtlas`, dimensione `territoryTotal`; periodi 2025. [https://www.regione.toscana.it/-/banca-dati-imprese-toscana](https://www.regione.toscana.it/-/banca-dati-imprese-toscana)

Rigenerazione:

```bash
python scripts/build_territorial_dossier_evidence.py --catalog dist/data/site-data.json --output-dir /tmp/territorial-dossiers
```

Riferimenti editoriali: [domande](QUESTIONS.md), [sotto-dossier](MODULES.md), [metodo](METHOD.md). Nessun nuovo dato, adapter o intervento pubblico è introdotto da questa analisi.
