# A6 — parco autovetture ACI v39

Due carrier già pubblicati diventano interrogabili: `motorization` e `pollutingCars`, copertura 7/7. Nessun dato, UI, snapshot o acquisizione cambia. Riferimento parco 2024; residenti al 1° gennaio 2026 per la motorizzazione, periodo ibrido dichiarato anche per Toscana/Italia. Non è un tasso su popolazione 2024.

## Valori e componenti

`total` conserva il valore comunale a un decimale. `nativeRatio` usa i conteggi interi del workbook ACI e il denominatore nativo: autovetture/residenti × 1.000 oppure Euro 0–3/autovetture totali × 100. Queste due viste non sono alias numerici. Le percentuali arrotondate non ricostruiscono conteggi o denominatori.

La motorizzazione Versilia pubblicata è il rapporto delle somme native. La quota Euro 0–3 Versilia pubblicata è invece la media delle percentuali comunali arrotondate ponderata per autovetture: 18,9725355433%. Il rapporto aggregato `nativeRatio` è 18,9911867112%, da 20.945/110.288 × 100. Entrambi sono riconciliati e distinti; il dato pubblico resta invariato. La media semplice dei valori comunali prodotta da `compare` è descrittiva e non è nessuno dei due aggregati.

## Operazioni e limiti

Confronto, rango numerico e gap Toscana/Italia ammessi sulle due viste 2024; il benchmark resta non arrotondato. Rapporto aggregato delle somme ammesso soltanto su `nativeRatio`, per Comuni distinti e stessi periodi delle componenti. Nessun pooling delle percentuali pubblicate. Nessuno storico ACI è congelato qui: serie, variazioni e trend rifiutati. Anche anomalie e correlazioni automatiche sono rifiutate in entrambi gli ordini dei selettori, inclusa l'associazione con popolazione e sicurezza stradale. Le classi Euro non dimostrano qualità dell'aria o emissioni effettive; iscrizione PRA/localizzazione amministrativa non equivale a traffico, utilizzo locale o proprietà dei residenti.

## Provenienza e verifiche

Snapshot `data/source-snapshots/a3-aci-vehicle-benchmark-2024.json`: SHA-256 `67834d9ef2dd5804dc5be39b05abc5afb8c9e6f6d7733aedcd059d2209e3eb9a`; workbook originale Base64 congelato con hash `700e7fbc0a1f3d68502aec979a11fc6d25f4c07ecc563fc356ee9d610b77dabc`. Il test usa soltanto la libreria standard Python (ZIP/XML OOXML), verificato anche con `python -S`, e rigioca 7.997 righe di localizzazione da quel workbook, propagando soltanto intestazioni geografiche di celle unite; null numerici conservati. L'audit fonte già governato riconcilia classi, totali provinciali/regionali/nazionale, benchmark e 7/7 valori comunali.

Pannello include localizzazioni non definite/estere pubblicate; totali geografici sono esclusi dalla somma delle localizzazioni. Denominatore include classi Euro non contemplate/non definite; nessun valore numerico nullo imputato. Numeratore Euro 0–3 usa quattro celle osservate distinte. Workbook congelato viene rigiocato, archivio ZIP originale è soltanto riferito con URL/hash, non riacquisito né rigiocato.

Residenti comunali da POSAS `istat-demography-lotto-a-2026-08.json`; benchmark da `a3-istat-demography-benchmark-2026.json`. Date e pointer di ciascuna componente sono esposti nella provenienza. Fingerprint completi degli snapshot e SHA/path delle cache verificati a ogni uso; cambi di periodo, formula, precisione, identità, valori, aggregati e benchmark rifiutati. Il pointer catalogo della vista nativa indica il valore pubblico di confronto, con `nativeRatioDistinct=true`; il valore calcolato deriva dai pointer nativi separati.

Fixture indipendenti: 14 celle pubbliche e 14 rapporti nativi distinti, 21 componenti fisse, 56 gap e due rapporti aggregati; 7.997 righe workbook rigiocate. Suite estesa di 140 domande, tutte le 1.710 precedenti invariate. Report derivati in `reports/a6-vehicles/`; microbenchmark descrittivo, senza promessa di latenza o punteggio di qualità.

A6.4 resta parziale, A6.5–A6.6 richiedono revisione metodologica; A7 non avviata. Nessun nuovo legame causale o nuova priorità politica.
