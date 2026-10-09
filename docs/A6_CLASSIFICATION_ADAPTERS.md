# A6 — classificazioni territoriali

Lotto v27 dopo #375: main `f67145233d29066568a0d556d7ffcbb73a6ef6b5`, albero `3ab499480bb4e032082c5d61a6d1d9f7ef414d82`. Solo motore, test e documentazione; dati, UI, asset, golden, workflow, Radar, Camaiore e letture territoriali conservati.

## Attributi categoriali, non quantità

`territorialClassification` usa `data/source-snapshots/territorio-ucs-v136.json`, classificazioni comunali Istat congelate al riferimento 2021. La pubblicazione delle geografie funzionali del 17 marzo 2026 non costituisce una nuova classificazione 2026. Non vengono riacquisiti SITUAS, geometrie o microdati né validati nuovamente confini, distanza dalla costa o distribuzioni della popolazione.

| Dimensione | Lettura | Riferimenti fissi nei sette Comuni |
|---|---|---|
| `total` / `part:degurba` | Codice e denominazione DEGURBA; alias, non osservazioni nuove | Sei codici 2, densità intermedia; Stazzema 3, scarsamente popolata |
| `part:littoral` | Appartenenza ufficiale ai Comuni litoranei | Camaiore, Forte dei Marmi, Pietrasanta e Viareggio sì; gli altri no |
| `part:coastalZone` | Appartenenza ufficiale alla zona costiera | Sei sì, Stazzema no; Massarosa e Seravezza costieri senza essere litoranei |

`compare` restituisce osservazioni affiancate, etichettate come `category_lookup`. DEGURBA conserva il codice ufficiale. Le appartenenze mantengono `sourceValue` booleano e `categoryLabel` sì/no; `value` 0/1 è un codice esplicito necessario al contratto numerico del confronto, non una quantità misurata o una nuova variabile analitica. `unit=category_code`, definizioni, metodo e avvertenze esplicitano questa distinzione. `false` è appartenenza negativa ufficiale, non dato mancante. Litoraneità e zona costiera non sono intercambiabili e i loro gruppi non si sommano.

Non si producono medie, ranghi, variazioni, trend, quote ponderate, anomalie, gap geografici o correlazioni dei codici. Nessun indice ambientale o giudizio di qualità/urbanizzazione viene calcolato. Le guardie agiscono prima della selezione, anche con il carrier nella seconda variabile di una correlazione. Il minimo di due osservazioni di `compare` resta invariato: la selezione di un solo Comune non viene promossa a confronto valido.

## Riconciliazione e prova

SHA256 file `22211f2d42aa8a23957c05ec03f35038e6ebf58f89ba18b46e39e61a1a35697a`; digest strutturale `621307d00dc707043566f4c28dcacfd8321fb936f07de4f7d8cb3aae6849d895`. Entrambi controllati a ogni accesso, inclusa mutazione della cache. Coorte, identità, unità, periodo, tipo composito, valori primari, tre attributi, tipi booleani, denominazioni, assenza di storico e flag di disponibilità pubblici sono riconciliati alla fonte congelata. Ogni osservazione espone puntatore catalogo e record nativo; i codici di appartenenza hanno la loro codifica esplicita.

Fixture indipendenti per sette Comuni × quattro dimensioni: 28 verifiche, inclusi sette alias. Test avversari su nulli, tipo booleano sostituito da intero, denominazione, identità, unità, anno, storico inventato, flag di indisponibilità, hash e oggetti in cache. Suite 689 domande (313 letture/calcoli, 376 rifiuti), 59 collegamenti tipizzati, 69 carichi descrittivi. Copertura derivata 160/225 effettivi e 109/181 sorgente, 65 residui di cui un ambientale: `drinkingWaterQuality`.

L’acqua GAIA conserva 70 località, 17 parametri e stringhe censurate: i conteggi pubblici delle località non sono un adapter della qualità e non vengono usati per dichiararne la copertura. Richiede un lotto distinto per dettaglio, unità e qualificatori, senza medie comunali, indice sintetico o valutazioni sanitarie/normative automatiche. A6.4 resta parziale, A6.5–A6.6 aperte; 35 letture e due riepiloghi conservati, A7 non avviata. Quick locale prima del push; Full locale isolato e CI canonica prima del merge del proprietario.
