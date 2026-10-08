# A6 — pericolosità ed esposizione ISPRA

Il motore v17 abilita due carrier dalle fonti congelate in `fragilita-comunale-v133.json`. Copertura 130/225 effettivi, 86/181 sorgente; 95 residui, di cui 30 ambientali. Dati pubblici, asset, renderer, golden e workflow conservati; nessuna acquisizione. A6.4 resta parziale, revisione A6.5–A6.6 aperta e A7 non avviata.

| Carrier | Mappa | Confini fonte | Residenti | Dimensioni |
|---|---|---|---|---|
| `floodExposure` | 2020 | 2024 | censimento 2011 | P3, P2, P1: residenti, quota residenti, km² e quota superficie; totale = residenti P2 |
| `landslideExposure` | 2024 | 2024 | censimento 2021 | P3+P4 ufficiale, P4, P3, P2, P1, AA: medesime quattro misure; totale = residenti P3+P4 |

I residenti esposti sono calcolati sulla popolazione censuaria della fonte, non su POSAS corrente. Numeratore e denominatore conservano i rispettivi periodi anche nei rapporti del gruppo. La superficie usa il denominatore municipale ISPRA dei confini 2024; nessuna sostituzione con Istat 2026, UCS, CFI o altri totali territoriali.

Ogni scenario selezionato restituisce componenti assolute oppure il rapporto nativo. `publishedValue` conserva la percentuale pubblicata a tre decimali; `value` usa i componenti della fonte. Riconciliazione entro mezzo millesimo di punto percentuale, in tutte le celle ammesse; nessuna nuova precisione geometrica viene attribuita agli input. I rapporti del gruppo usano somma degli esposti sul totale censuario o somma dei km² esposti sul totale areale, su Comuni disgiunti e sul medesimo scenario. Non una media delle percentuali.

P3/P2/P1 alluvionali sono scenari annidati, non categorie separate da sommare. Per le frane P3+P4 è un campo ufficiale: non viene ricostruito dalla somma delle percentuali o superfici arrotondate P3 e P4. Non si sommano classi per inventare un ulteriore indicatore complessivo. Pericolosità ed esposizione non sono probabilità di danno osservato, frequenza di eventi o effetti certificati di politiche.

## Storico e limiti

Solo `history:areaPct:P3+P4` delle frane espone le fotografie 2017, 2020 e 2024. La serie conserva la quota di superficie a due decimali: Massarosa 18,23; 18,57; 23,06. Il dato corrente di superficie nativo P3+P4 è pubblicato a tre decimali (23,064), e il rapporto dei componenti rimane separato. La riconciliazione dell’endpoint dello storico rispetta mezzo centesimo. Lo storico non contiene numeratori/denominatori nativi né residenti esposti per le edizioni precedenti: nessuna ponderazione storica o trasformazione di percentuali areali in residenti.

Serie consultabile non significa continuità delle mappe attestata. Trend, variazioni e correlazioni nel tempo vengono rifiutati. Alluvioni 2020 e frane 2024 mantengono anche censimenti diversi: il collegamento tipizzato è contesto e rifiuta il pairing automatico per periodi diversi. Non è congelato un benchmark ufficiale Toscana/Italia per questo adapter. Nessuna conclusione causale o priorità politica generata.

Le risposte conservano unità, scenario, definizione, metodo, periodi, provenienza con SHA-256 e puntatori ai record. Zero osservato distinto dal dato mancante; esclusioni richiedono opt-in. Guardie su riferimenti cartografici/censuari, identità, cohort, classi, componenti, precisione e anni dello storico. I vecchi carrier sorgente non sono il profilo effettivo revisionato: nessuna copertura sorgente artificiale.

## Verifiche

294 osservazioni contro input fissi trascritti dallo snapshot, con aritmetica indipendente; il conteggio include alias e ripetizioni corrente/storico. Suite 248/248: 153 calcoli e 95 rifiuti attesi; 42 collegamenti tipizzati, 40 carichi di prestazione. Le 35 letture territoriali e due riepiloghi restano invariati.

Report `reports/a6-hazards/`. Test integrati nel preflight generale per sorgente e catalogo effettivo; Quick locale prima del push, Full canonico isolato con Quick incluso e CI sul medesimo albero prima della revisione per merge. Merge/pubblicazione del proprietario. Il lavoro Radar già mergiato nella #351 è preservato nella baseline e resta fuori dal lotto.
