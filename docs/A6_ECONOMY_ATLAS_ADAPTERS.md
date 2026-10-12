# A6 — Atlante attività economiche, valori diretti e totali distinti

Il lotto v54 abilita il carrier `economyActivityAtlas`, presente soltanto nel catalogo effettivo. La copertura degli adapter arriva a 225/225 effettivi; il catalogo sorgente resta 166/181 perché l’Atlante è materializzato dalla pipeline pubblica. Copertura non significa che ogni operazione o dimensione A3 sia ammessa, né chiusura metodologica di A6.

## Fonte e perimetro

Regione Toscana — Banca dati Imprese / Registro Imprese InfoCamere: https://www.regione.toscana.it/-/banca-dati-imprese-toscana . Sono riusati esclusivamente metadata, dieci chunk `atlas-*.b64` e cinque chunk della tassonomia ATECO già versionati in `data/economy-atlas/`. Metadata: versione 4 settembre 2026, 1.228 righe dirette, tassonomia Istat ATECO2007 aggiornamento 2022; runtime 2014–2025. Le impronte degli originali censite nei metadata sono provenienza dell’acquisizione, non replay dei CSV originali. Il lotto rigioca il payload compatto normalizzato. Nessuna acquisizione o modifica dati/UI.

Il conteggio riguarda unità locali registrate, non numero di imprese, addetti o occupati residenti. Istat ASIA resta un altro universo. Le righe a differenti livelli della gerarchia non sono una partizione additiva da sommare automaticamente: un valore registrato direttamente in un nodo non è il totale esaustivo della sua intera branca. Le ricostruzioni dei discendenti nell’interfaccia rimangono distinte e non sono abilitate come query A6. Alias testuali, codici con punti, nomi simili o sezioni senza record diretto non vengono trasformati in selezioni implicite.

## Viste ammesse

- `territoryTotal`: totale territoriale delle UL attive da `tt`, consultabile 7/7 dal 2014 al 2025.
- `ateco:C 3012|active` (esempio): conteggio diretto dello specifico record ATECO, dal 2014 al 2025. Disponibili tutti i 1.228 codici esatti.
- `ateco:C 3012|artisan` (esempio): conteggio artigiano dello specifico record, soltanto 2025. Non si ricostruisce una serie artigiana.

Totale 2.457 viste esplicite. Confronto/rango e, solo per i conteggi attivi, serie consultabili; zeri e null conservati. Il confronto parziale richiede `allowPartial` e almeno due osservazioni utilizzabili. La serie non certifica continuità classificatoria: variazioni, trend e differenze in punti percentuali sono rifiutati. Quote artigiane, LQ, peso regionale e aggregazioni gerarchiche richiedono una riconciliazione dei rispettivi universi e non sono abilitate. Il valore regionale del medesimo record è solo contesto, non un benchmark municipale. Pooling, anomalie e coppie non revisionate rifiutati.

## Divergenza del carrier pubblico

Il materializzatore `latest_town_totals` somma soltanto le righe dirette di divisione: (58, 13, 31, 43, 25, 2, 120), totale 292. Il payload conserva invece i totali territoriali 2025 (3.822, 1.556, 1.940, 3.327, 1.437, 245, 7.998), totale 20.325. Il primo non riconcilia il totale delle UL territoriali. Il lotto non riscrive il carrier o l’interfaccia: `total` implicito è rifiutato con `atlas_explicit_view_required_unreconciled_scalar_carrier`; occorre scegliere `territoryTotal` o un codice/misura espliciti. Nessuna sostituzione silenziosa del292. La divergenza deve essere risolta nel lavoro di qualità dei dati prima della chiusura metodologica A6, con i gate dei dati/UI applicabili; non viene nascosta dal conteggio225/225.

## Evidenze e cache

Ogni osservazione indica codice/etichetta, misura, periodo, valore, stato mancante, contesto regionale, fonti, hash dei 16 file e puntatore nella concatenazione decodificata dei dieci chunk. I puntatori sono riferiti al JSON decodificato, non a un singolo file base64. Cache indicizzata da byte immutabili e alberi ricorsivamente immutabili; file riletto e hash verificato anche dopo cache. Fingerprint del carrier e identità dei sette Comuni controllati a ogni accesso. Nessuna prova sui record originali dichiarata.

119 riferimenti fissi: sette totali correnti e sette iniziali, cinque categorie × sette Comuni × conteggio attivo 2014/2025 e artigiano 2025. Rango, serie Massarosa completa, zeri/null, periodi/voci impropri, pooling e coppie verificati. Replay separato di 111.832 celle comunali compatte, incluse 56.238 null: 1.228×7×12 attive +1.228×7 artigiane +7×12 totali territoriali. Non è un test query per ogni cella. Prove su file freddi/modificati dopo cache e immutabilità. 184 domande nuove, tutte le 3.543 precedenti conservate; report `reports/a6-economy-atlas/`. Baseline prestazionale locale descrittiva, nessuna garanzia di latenza di produzione.

Quick canonico completo prima del push; Full locale completo sequenziale e CI Quick→Full/A3 sullo stesso albero prima del merge del proprietario. A6.4 parziale, A6.5–A6.6 aperte, A7 non avviata.
