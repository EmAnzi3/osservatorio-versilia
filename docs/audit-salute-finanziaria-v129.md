# Audit Lotto 9 — Salute finanziaria e debito · v1.29.0

Data audit: 3 settembre 2026

Perimetro: Rendiconti OpenBDAP 2019–2025 dei sette Comuni dell’Osservatorio Versilia. Fonte primaria: Ragioneria generale dello Stato — OpenBDAP, **Schemi di bilancio** e **Piano degli indicatori** Toscana. Gli archivi effettivamente utilizzati e i relativi SHA-256 sono congelati in `data/source-snapshots/salute-finanziaria-v129.json`.

## Indicatori ammessi

La release introduce **una sola card composita** in `Bilanci comunali → Equilibri e capacità amministrativa`:

**Debito finanziario e costo degli interessi**

Selector:

1. **Debito finanziario pro capite** — ex indicatore 10.4: `D1 Debiti da finanziamento / popolazione residente al 1° gennaio`. Il valore è ricalcolato dai componenti ufficiali e non viene copiato dal campo PDI 10.4, risultato incoerente in più annualità.
2. **Interessi sulle entrate correnti** — indicatore 6.1: `impegni Macroaggregato 1.7 Interessi passivi / accertamenti Titoli 1+2+3 × 100`. È sempre ricalcolato dai componenti ufficiali.
3. **Sostenibilità dei debiti finanziari** — indicatore 10.3: si usa il PDI ufficiale quando disponibile; le sole eccezioni sono documentate nello snapshot.

L’indicatore 9.5 “Indicatore annuale di tempestività dei pagamenti” resta **fuori dalla v1.29.0** perché il dataset PDI presenta anomalie che non possono essere normalizzate con una regola unica e dimostrabile.

## Copertura

Copertura approvata: **7/7 Comuni per ciascuna annualità 2019–2025**.

L’assenza di un campo PDI non viene convertita automaticamente in zero. `0` è ammesso esclusivamente quando il numeratore ufficiale ricostruibile è verificato pari a zero; altrimenti il valore resta `n.d.`.

### Normalizzazioni 10.3

- **Camaiore 2023:** valore raw PDI `964` → `9,64%`.
- **Camaiore 2024:** valore raw PDI `1082` → `10,82%`.

La trasformazione `/100` è ammessa perché nelle stesse trasmissioni Camaiore perde sistematicamente il separatore decimale anche per altri indicatori percentuali; il 6.1 raw `346` riconcilia esattamente con `3,46%` quando ricostruito dagli Schemi.

### Forte dei Marmi 10.3

- **2019:** PDI assente; ricostruzione dai componenti ufficiali = `0,273416%`.
- **2020:** PDI `0,03%`.
- **2021:** PDI `0,26%`.
- **2022:** PDI `0,22%`.
- **2023–2025:** PDI assente; valore ricostruito = **`0,00%`**, perché interessi passivi, Titolo 4 rimborso prestiti e le specifiche entrate da sottrarre presenti nello snapshot portano a numeratore nullo.

Questi zeri sono quindi valori derivati, non sostituzioni di dati mancanti.

## Aggregati Versilia

Non viene usata la media aritmetica semplice dei sette Comuni.

- **Debito finanziario pro capite:** `Σ D1 / Σ popolazione`.
- **6.1:** `Σ interessi passivi / Σ entrate correnti × 100`.
- **10.3:** media ponderata dei rapporti comunali, con peso pari alle entrate correnti: `Σ(10.3_i × entrate correnti_i) / Σ entrate correnti_i`.

L’aggregato 10.3 è una **elaborazione territoriale dell’Osservatorio**, non un indicatore OpenBDAP ufficiale della Versilia.

## Massarosa e dissesto

Massarosa ha dichiarato il dissesto il **27 novembre 2019**. Nel periodo successivo una parte delle passività pregresse è stata gestita nel perimetro separato dell’OSL. Per questo la serie ordinaria del Rendiconto, in particolare la voce D1, non deve essere interpretata come misura dell’intero stock di passività della procedura di dissesto.

La card usa quindi il nome **“Debito finanziario pro capite”**, non “debito complessivo” o “indebitamento totale”, e mostra una nota contestuale nella scheda di Massarosa.

Il 6.1 di Massarosa nel 2025 è circa **4,38%** ed è confermato dai componenti contabili: non viene corretto né attenuato. La card mantiene polarità neutra e non traduce automaticamente aumenti o diminuzioni in un giudizio sulla qualità della gestione.

## UI e leggibilità

La nuova card usa i componenti compositi già consolidati. In particolare le tre letture correnti sono rese con `.composite-town-mobility article`, che nel CSS corrente ha **17 px di padding interno**. Non vengono introdotte card con testo a contatto con il bordo.

Il selector aggiorna valore comunale, confronto Versilia e **serie storica della lettura selezionata**. 6.1 e 10.3 usano due decimali per non trasformare valori come `0,03%` in `0,0%`.

## Tracciabilità

- Snapshot: `data/source-snapshots/salute-finanziaria-v129.json`
- Materializzatore: `scripts/apply_salute_finanziaria_v129.py`
- Test: `scripts/test_salute_finanziaria_v129.py`

Il test blocca regressioni su formule, copertura, normalizzazioni Camaiore, zeri ricostruiti di Forte dei Marmi, nota OSL di Massarosa, aggregati ponderati e padding delle card.
