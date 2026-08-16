# Audit scale e tooltip grafici — v1.13

## Obiettivo

Verificare le famiglie di grafico dell’Osservatorio e correggere due problemi di leggibilità: scale percentuali inutilmente fissate a 0–100 e tooltip difficili da interrogare quando più serie comunali sono molto vicine.

## Esito dell’audit

### Confronti comunali correnti

Il motore `visual-grammar.js` distingueva già quattro casi:

- valori non negativi: origine a zero e massimo arrotondato;
- valori con segno: zero evidenziato e scala estesa sui due lati;
- prezzi carburanti (`€/l`): scala focalizzata con margine perché differenze di pochi centesimi sono informative;
- percentuali 0–100: scala sempre 0–100.

L’ultimo caso era troppo rigido. Con valori come 0,9–2,8% quasi tutta la superficie del grafico restava vuota.

La nuova regola mantiene **sempre lo zero** per le percentuali, per non amplificare artificialmente le differenze, ma usa il 100% come massimo solo quando il massimo osservato raggiunge almeno il 60%. Sotto quella soglia il limite superiore è calcolato dai dati, con un margine minimo e un arrotondamento a valori leggibili. Esempi sui dati v1.13:

- Famiglie coabitanti: 0–4%;
- Tasso di disoccupazione: 0–10%;
- Titolo terziario: 0–40%;
- Autovetture Euro 0–3: 0–30%.

Il regression test percorre automaticamente tutti gli indicatori percentuali non compositi con massimo inferiore al 60% e verifica che non ricadano più nella scala 0–100, che il massimo grafico non tronchi i dati e che resti inferiore al 100%.

### Valori assoluti, conteggi, euro e tassi

Resta l’origine a zero. In questi casi la lunghezza/distanza dal valore nullo conserva un significato quantitativo e una scala troncata rischierebbe di sovrastimare visivamente differenze piccole.

### Valori con segno

Resta la scala che include entrambi i lati dello zero, con zero evidenziato. È la soluzione corretta per saldi e variazioni positive/negative.

### Prezzi carburanti

Resta la scala focalizzata già esistente e dichiarata esplicitamente nell’interfaccia. Lo zero non è un riferimento utile per confrontare differenze di pochi centesimi al litro.

### Serie storiche comunali

Le serie storiche multi-anno usano già minimo e massimo osservati con margine dell’8%, evitando sia tagli sia grandi spazi inutilizzati. Le serie a due punti normalizzano il tratto sull’intervallo osservato e riportano i valori numerici ai due estremi. Non è stata introdotta un’ulteriore modifica di scala.

### Meteo e clima

Il layer climatico usa già scale focalizzate sul dominio dei dati con margine dedicato. Non viene modificato.

## Tooltip e selezione del Comune

Nel confronto storico generico la selezione di un Comune attenuava graficamente le altre serie, ma i loro punti restavano ancora sensibili a mouse, touch e tastiera. Il layer climatico aveva già una regola più coerente.

Il comportamento viene uniformato:

- senza Comune selezionato, tutti i punti restano interrogabili;
- con un Comune selezionato, solo i suoi punti possono aprire tooltip;
- i punti delle altre serie non intercettano il puntatore e vengono esclusi dal focus da tastiera;
- la navigazione con frecce resta confinata ai punti interrogabili;
- deselezionando il Comune, tutti i punti tornano disponibili.

Le altre serie rimangono visibili come contesto e possono continuare a essere scelte dalla legenda.

## Compatibilità del workflow v1.13

Il materializzatore della release Economia richiama ancora alcuni patcher storici. `patch_fuel_precision.py` è stato reso idempotente rispetto all’evoluzione successiva di `scaleFor`: se il ramo dedicato ai carburanti e l’etichetta della scala focalizzata sono già presenti, il patcher non richiede più che la funzione conservi la forma testuale della prima implementazione. In questo modo il workflow continua a verificare la release senza impedire evoluzioni legittime della grammatica grafica.

## Invarianti

L’intervento non modifica dati, formule, fonti, aggregati Versilia, conteggio indicatori o semantica delle metriche. Cambiano esclusivamente dominio grafico e hit-testing dei tooltip, più l’idempotenza del patcher di build già esistente.
