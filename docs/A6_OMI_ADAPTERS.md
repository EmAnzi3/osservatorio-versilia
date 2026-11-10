# A6 — Quotazioni residenziali OMI

Un carrier `omiResidential`, tre viste comunali: `total` (alias vendita), `saleMean` (€/m²) e `rentMean` (€/m² al mese). Consultazione, confronto e rango descrittivo sui sette Comuni. Periodo preciso `2025-S2`; il token pubblico `2° semestre 2025` è riconosciuto, mentre l'anno intero `2025` è rifiutato. Nessun dato acquisito o modificato.

## Perimetro e metodo

Il catalogo pubblicato espone 46 zone residenziali e 92 valori di riferimento vendita/affitto. Ogni media comunale è la media aritmetica semplice delle zone mostrate; il riferimento Versilia è la media semplice dei sette valori comunali. Sono elaborazioni dell'Osservatorio, senza ponderazione per transazioni, abitazioni, superfici o residenti. La media delle 46 zone non coincide con la media dei sette Comuni. L'alias `total` non introduce una terza misura.

Le quotazioni di riferimento non sono prezzi effettivi di compravendita né canoni dei contratti registrati. Il replay riguarda esclusivamente i valori delle zone già pubblicate nel catalogo: intervalli originali OMI min/max, file sorgente e record di selezione della tipologia non sono congelati separatamente e non vengono dichiarati rigiocati. La selezione pubblica indica abitazioni civili, stato normale; questo lotto ne conserva la definizione senza affermare una nuova verifica dei file originali.

I codici di zona sono locali a ogni Comune: `B1` in due Comuni non certifica frazioni o quartieri equivalenti. Le zone non coincidono necessariamente con le frazioni. Le query del lotto sono comunali; una dimensione arbitraria di zona, min/max o prezzo annualizzato viene rifiutata. I puntatori alle zone attestano la riconciliazione delle medie, non un nuovo selettore geografico.

## Limiti e controlli

Nessuno storico comparabile congelato: serie, variazioni e trend rifiutati. Mancano pesi di transazioni/abitazioni: pooling rifiutato. Benchmark geografici, anomalie e coppie con reddito o altri carrier non revisionate rifiutati. Un rango di quotazioni non misura accessibilità economica, qualità abitativa o priorità politica; servirebbero basi e universi omogenei ulteriori.

14 riferimenti comunali fissi trascritti, alias vendita, pari merito, 92 valori di zona riconciliati, contrapposizione tra media per Comune e per zona, unità e semestri espliciti, puntatori e prove ostili dopo cache su identità, valori, definizioni, zone e aggregati. Fingerprint dell'intero carrier verificato a ogni accesso, senza fiducia implicita nella cache. 63 domande aggiunte conservando tutte le 3.439 precedenti del main dopo #420; nessuna aspettativa ricavata automaticamente dalle risposte del motore. Report derivati in `reports/a6-omi/`; prestazioni locali descrittive.

Quick completo prima del push e Full completo locale/CI Quick→Full/A3 sullo stesso albero prima della prontezza al merge del proprietario. A6.4 resta parziale, A6.5–A6.6 aperte, A7 non avviata. Dati/UI/asset/golden/workflow/Radar e letture territoriali preservati.

## Aggiornamento al 1° semestre 2026 (10 novembre 2026)

Il periodo preciso passa a `2026-S1` (token pubblico `1° semestre 2026`); `2025-S2` e `2° semestre 2025` ora sono rifiutati come gli altri semestri. I dati arrivano da `update_source_data.py omi-residential --semester 2026-S1`, che prima rigioca dalla consultazione OMI il semestre pubblicato: il valore di zona è il punto medio min/max della riga «Abitazioni civili NORMALE» per vendita e locazione, e le zone senza quella riga sono escluse. Gli intervalli e tutte le righe della fonte sono ora congelati in `data/source-snapshots/omi-residential-2026-S1.json`; la nota `omi_public_zone_values_replayed_original_omi_ranges_and_files_not_frozen` diventa `omi_zone_values_midpoints_of_source_ranges_frozen_in_semester_snapshot` e quella sul periodo diventa `omi_first_semester_2026_not_current_market_or_full_year_average`. Il motore continua a non rigiocare la fonte (`nativeRecordReplayAvailable` resta falso).

Il replay ha trovato tre differenze del catalogo dalla fonte, accettate come correzioni riviste e registrate nella fotografia (`catalogCorrections`): Viareggio D2 (1.750 → 2.025 €/m² nel 2° semestre 2025), Seravezza E3 (1.450 → 1.125 €/m²) e la zonizzazione di Stazzema, che nella fonte ha 3 zone (B1, E7, R2) invece delle 11 del catalogo, ora ricostruite con le etichette della fonte. Le zone pubblicate passano da 46 a 38 (76 valori); anchor dei test e 63 domande verificate aggiornati, più 3 rifiuti espliciti di `2025-S2`. Il pari merito vendita Camaiore/Viareggio non c'è più: il test controlla ranghi distinti. Pin `omi#1` ripinnato.
