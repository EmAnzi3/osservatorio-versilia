# A3 — Enrichment Audit globale

Questo documento definisce la tassonomia comune usata dal workstream `A3` per verificare, in modo sistematico, quanto del contenuto informativo disponibile presso le fonti venga effettivamente acquisito e pubblicato dall'Osservatorio.

Non è un secondo catalogo canonico e non contiene un inventario manuale degli indicatori. Il perimetro degli indicatori deve essere sempre derivato da `data/site-data.json` e dall'Effective Public Catalog.

## A3.1 — Dimensioni comuni di enrichment

Le dimensioni seguenti costituiscono il vocabolario minimo dell'audit. Una fonte può offrire ulteriori dimensioni specifiche: in quel caso vanno ricondotte a `categorie_specifiche` e descritte senza creare nuove categorie globali se non strettamente necessario.

| ID | Dimensione | Definizione operativa |
| --- | --- | --- |
| `serie_storica` | Serie storica | Disponibilità di più periodi confrontabili per lo stesso indicatore e la stessa metodologia. |
| `sesso` | Sesso | Disaggregazione almeno per sesso/genere quando prevista dalla fonte ufficiale. |
| `eta` | Età | Disaggregazione per classi di età o età puntuale disponibile alla fonte. |
| `dettaglio_territoriale` | Dettaglio territoriale | Granularità più fine o più ampia rispetto al Comune: frazione/sezione, provincia, area vasta, regione, ripartizione, Italia o altra geografia ufficiale utile. |
| `benchmark_toscana_italia` | Benchmark Toscana/Italia | Valori comparabili per Toscana e/o Italia prodotti con definizione e periodo coerenti con il dato comunale. |
| `assoluto_normalizzato` | Assoluto/normalizzato | Disponibilità congiunta del valore assoluto e di una misura normalizzata coerente, per esempio per abitante, per 1.000 residenti, per famiglia, per superficie o percentuale. |
| `frequenza_infra_annuale` | Frequenza infra-annuale | Disponibilità di osservazioni mensili, trimestrali, semestrali o comunque più frequenti dell'anno. |
| `numeratore_denominatore` | Numeratore/denominatore | Disponibilità delle componenti che generano un rapporto, tasso, quota o indice pubblicato. |
| `categorie_specifiche` | Categorie specifiche | Disaggregazioni proprie del dominio della fonte, per esempio tipologia di reato, classe ATECO, classe di potenza, ordine scolastico, modalità di trasporto, specie o classe ambientale. |

## Stati ammessi per ogni coppia indicatore/dimensione

Ogni coppia `indicatore × dimensione` deve ricevere esattamente uno dei seguenti stati:

- `ACQUIRED`: la dimensione è disponibile alla fonte ed è già acquisita in forma strutturata dalla pipeline dell'Osservatorio, anche se non necessariamente esposta in ogni visualizzazione.
- `AVAILABLE_MISSING`: la dimensione è disponibile presso una fonte ufficiale compatibile con l'indicatore ma non viene ancora acquisita dalla pipeline.
- `SOURCE_UNAVAILABLE`: la dimensione sarebbe informativamente pertinente, ma la fonte ufficiale utilizzata non la rende disponibile oppure non la rende disponibile con definizione/periodo/granularità sufficientemente comparabili.
- `NOT_APPLICABLE`: la dimensione non ha significato per quell'indicatore o non è metodologicamente pertinente. Non va usato per mascherare una mancata acquisizione.

## Regole di classificazione

1. `ACQUIRED` richiede evidenza nella pipeline o nei dati strutturati, non soltanto presenza visuale o testuale nel sito.
2. `AVAILABLE_MISSING` richiede evidenza verificabile che la fonte ufficiale esponga realmente la dimensione con compatibilità metodologica sufficiente.
3. `SOURCE_UNAVAILABLE` deve descrivere l'assenza o la non comparabilità alla fonte; un endpoint temporaneamente irraggiungibile non basta a classificare la dimensione come indisponibile.
4. `NOT_APPLICABLE` è una decisione semantica sull'indicatore, non una scorciatoia operativa.
5. La disponibilità di benchmark, serie o disaggregazioni non implica automaticamente che sia corretto pubblicarle: A3 misura il potenziale informativo; integrazione e QA restano responsabilità di A3.4–A3.5.
6. Nessuno stato deve essere dedotto da conteggi hard-coded: indicatori, fonti e relazioni devono essere derivati dalle strutture canoniche già esistenti.

## Unità di audit

L'unità minima è la coppia:

`indicatore pubblico × dimensione enrichment`

L'audit A3.2 deve essere derivato dal catalogo pubblico effettivo e produrre per ogni coppia almeno:

- ID indicatore;
- fonte/policy sorgente risolta;
- dimensione;
- stato;
- evidenza o motivazione sintetica;
- riferimento alla fonte quando necessario per distinguere `AVAILABLE_MISSING` da `SOURCE_UNAVAILABLE`.

## A3.2 — Matrice derivata di classificazione

`scripts/enrichment_audit_matrix.py` costruisce una vista derivata dell'Effective Public Catalog senza enumerare manualmente gli indicatori. Per ogni indicatore pubblico genera esattamente una riga per ciascuna delle nove dimensioni A3.

La risoluzione segue questo ordine:

1. **evidenza strutturata nel catalogo pubblico** → `ACQUIRED`;
2. **override della metrica** in `metricOverrides[*].enrichmentDimensions` → stato esplicito per eccezioni semantiche o disponibilità specifica;
3. **profilo fonte** in `sourceProfiles[*].enrichmentDimensions` → disponibilità o indisponibilità documentata a livello di fonte;
4. in assenza di evidenza sufficiente la coppia resta operativamente **non classificata** con `state: null`.

`state: null` non è un quinto stato A3: è esclusivamente un indicatore di lavoro incompleto. La modalità strict rifiuta qualunque matrice che contenga coppie non classificate, per impedire di dichiarare A3.2 concluso sulla base di assunzioni.

Vincoli delle annotazioni:

- `ACQUIRED` non può essere dichiarato manualmente: deve essere rilevato da dati strutturati;
- `AVAILABLE_MISSING` e `SOURCE_UNAVAILABLE` richiedono sia una motivazione sia un riferimento verificabile alla fonte;
- `NOT_APPLICABLE` è ammesso solo come override della singola metrica, non come default di un intero profilo fonte;
- le annotazioni sono eccezioni/evidenze nel registry esistente, non un secondo catalogo degli indicatori.

Il Full preflight verifica la matrice sull'Effective Public Catalog realmente materializzato e controlla che il numero di coppie sia sempre `indicatori pubblici × 9`, derivato a runtime.

## Criterio A3.1

A3.1 è completo quando questa tassonomia è adottata come vocabolario unico del workstream e le successive classificazioni non introducono stati o dimensioni parallele senza una modifica esplicita di questo contratto metodologico.

## Criterio A3.2

A3.2 è completo soltanto quando la stessa matrice derivata passa la validazione strict con `unclassifiedPairCount = 0`. Fino a quel momento il conteggio delle coppie non classificate misura il lavoro residuo di raccolta delle evidenze, senza trasformare l'assenza di informazione in `SOURCE_UNAVAILABLE` o `NOT_APPLICABLE`.
