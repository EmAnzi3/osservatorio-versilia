# A6 — Quotazioni residenziali OMI

Un carrier `omiResidential`, tre viste comunali: `total` (alias vendita), `saleMean` (€/m²) e `rentMean` (€/m² al mese). Consultazione, confronto e rango descrittivo sui sette Comuni. Periodo preciso `2025-S2`; il token pubblico `2° semestre 2025` è riconosciuto, mentre l'anno intero `2025` è rifiutato. Nessun dato acquisito o modificato.

## Perimetro e metodo

Il catalogo pubblicato espone 46 zone residenziali e 92 valori di riferimento vendita/affitto. Ogni media comunale è la media aritmetica semplice delle zone mostrate; il riferimento Versilia è la media semplice dei sette valori comunali. Sono elaborazioni dell'Osservatorio, senza ponderazione per transazioni, abitazioni, superfici o residenti. La media delle 46 zone non coincide con la media dei sette Comuni. L'alias `total` non introduce una terza misura.

Le quotazioni di riferimento non sono prezzi effettivi di compravendita né canoni dei contratti registrati. Il replay riguarda esclusivamente i valori delle zone già pubblicate nel catalogo: intervalli originali OMI min/max, file sorgente e record di selezione della tipologia non sono congelati separatamente e non vengono dichiarati rigiocati. La selezione pubblica indica abitazioni civili, stato normale; questo lotto ne conserva la definizione senza affermare una nuova verifica dei file originali.

I codici di zona sono locali a ogni Comune: `B1` in due Comuni non certifica frazioni o quartieri equivalenti. Le zone non coincidono necessariamente con le frazioni. Le query del lotto sono comunali; una dimensione arbitraria di zona, min/max o prezzo annualizzato viene rifiutata. I puntatori alle zone attestano la riconciliazione delle medie, non un nuovo selettore geografico.

## Limiti e controlli

Nessuno storico comparabile congelato: serie, variazioni e trend rifiutati. Mancano pesi di transazioni/abitazioni: pooling rifiutato. Benchmark geografici, anomalie e coppie con reddito o altri carrier non revisionate rifiutati. Un rango di quotazioni non misura accessibilità economica, qualità abitativa o priorità politica; servirebbero basi e universi omogenei ulteriori.

14 riferimenti comunali fissi trascritti, alias vendita, pari merito, 92 valori di zona riconciliati, contrapposizione tra media per Comune e per zona, unità e semestri espliciti, puntatori e prove ostili dopo cache su identità, valori, definizioni, zone e aggregati. Fingerprint dell'intero carrier verificato a ogni accesso, senza fiducia implicita nella cache. 63 domande aggiunte conservando tutte le 3.322 precedenti; nessuna aspettativa ricavata automaticamente dalle risposte del motore. Report derivati in `reports/a6-omi/`; prestazioni locali descrittive.

Quick completo prima del push e Full completo locale/CI Quick→Full/A3 sullo stesso albero prima della prontezza al merge del proprietario. A6.4 resta parziale, A6.5–A6.6 aperte, A7 non avviata. Dati/UI/asset/golden/workflow/Radar e letture territoriali preservati.
