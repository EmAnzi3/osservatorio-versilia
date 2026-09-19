# A3.4 — Backlog enrichment

A3.4 trasforma tutte le coppie `AVAILABLE_MISSING` della matrice A3 strict in un backlog operativo ordinato, senza introdurre un inventario manuale parallelo.

## Perimetro

Il backlog deriva esclusivamente da:

1. matrice A3 strict dell'Effective Public Catalog;
2. audit fonte-per-fonte A3.3;
3. tassonomia A3 delle nove dimensioni.

Ogni coppia `AVAILABLE_MISSING` deve comparire esattamente una volta nel backlog. Nessuna coppia con altro stato può entrare nel backlog.

## Unità operativa

La singola coppia indicatore × dimensione resta l'unità di copertura, ma il backlog raggruppa il lavoro in pacchetti:

`sourceProfileId × dimensione`

Questo evita 872 task isolati e rappresenta meglio il lavoro reale: quando una fonte offre la stessa dimensione per più indicatori, l'acquisizione può essere progettata come un unico lotto con QA comune.

## Valore informativo

A3.4 introduce una policy esplicita e versionata. Non è un fatto della fonte e non pretende di essere una misura universale.

Valore per coppia:

- `serie_storica`: 5
- `dettaglio_territoriale`: 5
- `benchmark_toscana_italia`: 5
- `numeratore_denominatore`: 5
- `sesso`: 4
- `eta`: 4
- `assoluto_normalizzato`: 4
- `frequenza_infra_annuale`: 3
- `categorie_specifiche`: 3

Il valore del pacchetto è:

`informationValuePoints = valore_dimensione × numero_coppie`

## Costo di acquisizione

Il costo non è una stima di giorni, ore o euro. È un proxy deterministico su scala 1..5, calcolato solo da segnali già presenti nella matrice e nell'audit.

Base: 3.

Correzioni:

- -1 se sullo stesso profilo esiste già almeno una coppia `ACQUIRED` per la stessa dimensione;
- -1 se tutte le opportunità del pacchetto derivano da evidenza `source_profile`;
- +1 se almeno una opportunità richiede evidenza `metric_override`;
- +1 se il pacchetto usa più `sourceReference` distinti;
- risultato limitato a 1..5.

Questa euristica misura soprattutto riuso e frammentazione dell'acquisizione. Non sostituisce l'analisi tecnica che verrà fatta in A3.5 prima di integrare un lotto.

## Ordinamento

Per ogni pacchetto:

`priorityIndex = informationValuePoints / costPoints`

Ordinamento deterministico:

1. `priorityIndex` decrescente;
2. valore informativo decrescente;
3. costo crescente;
4. numero coppie decrescente;
5. profile ID e dimensione come tie-break stabili.

## Invarianti

A3.4 fallisce se:

- la matrice A3 non è strict-complete;
- la tassonomia delle nove dimensioni diverge dai pesi A3.4;
- A3.3 e la matrice non concordano sul numero o sull'identità degli `AVAILABLE_MISSING`;
- una coppia `AVAILABLE_MISSING` manca di `sourceReference`;
- una coppia viene duplicata o persa nel raggruppamento;
- il backlog non è riproducibile dalla matrice e dall'audit.

## Output

Il workflow A3 genera:

- `a3-enrichment-backlog.json` — formato macchina completo;
- `a3-enrichment-backlog.md` — vista leggibile e ordinata.

Gli artifact sono derivati e rigenerabili. Non diventano fonti canoniche.

## Relazione con A3.5

A3.4 ordina il lavoro ma non acquisisce nuovi dati.

A3.5 prende i pacchetti prioritari, verifica la fattibilità tecnica effettiva e integra nuove dimensioni in lotti controllati con QA e fonte dichiarata.
