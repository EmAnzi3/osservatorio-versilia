# A3.3 — Audit fonte per fonte

A3.3 verifica il catalogo pubblico completo a livello di fonte dopo la chiusura strict di A3.2.

## Principio

L'audit non introduce un secondo inventario di indicatori o fonti.

Il perimetro deriva sempre da:

1. Effective Public Catalog materializzato dalla build;
2. matrice A3 strict indicatore x dimensione;
3. source registry esistente per i metadati operativi della fonte.

Il report A3.3 e quindi una vista derivata e rigenerabile.

## Unita di audit

L'unita e il source profile effettivamente risolto per almeno un indicatore pubblico.

Per ogni profilo il report verifica e rende leggibili:

- publisher;
- frequenza e release attesa;
- metodo di acquisizione;
- licenza;
- indicatori pubblici associati;
- numero di coppie indicatore x dimensione;
- conteggi per stato A3;
- origini della classificazione;
- dettaglio delle coppie AVAILABLE_MISSING;
- dettaglio delle coppie SOURCE_UNAVAILABLE;
- dettaglio delle coppie NOT_APPLICABLE.

Le coppie ACQUIRED restano conteggiate e verificabili nella matrice, senza duplicare nel report l'intera evidenza strutturale riga per riga.

## Invarianti

A3.3 fallisce se:

- la matrice A3 non e strict-complete;
- una metrica pubblica risolve su piu profili fonte;
- un profilo usato dal catalogo non esiste nel registry;
- un profilo usato manca dei metadati operativi obbligatori;
- il numero di metriche, profili o coppie diverge dalla matrice A3;
- una dimensione di un profilo non copre esattamente tutte le metriche associate;
- i conteggi degli stati divergono dalla matrice A3.

I profili registry non usati dal catalogo effettivo sono riportati come diagnostica, ma non entrano nel perimetro dell'audit pubblico.

## Output

Il workflow A3 genera due artifact:

- a3-source-audit.json — formato macchina;
- a3-source-audit.md — vista leggibile fonte per fonte.

Gli artifact sono output derivati del run e non vengono usati come fonti canoniche.

## Relazione con A3.4

A3.3 non ordina ne valuta le opportunita di arricchimento.

Le coppie AVAILABLE_MISSING vengono soltanto esposte per fonte. La successiva prioritizzazione per valore informativo e costo appartiene esclusivamente ad A3.4.
