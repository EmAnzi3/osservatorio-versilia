# A6 — personale comunale RGS, adapter v30

Quattro carrier già pubblicati diventano interrogabili. Nessuna acquisizione live, nuovo valore, modifica UI, golden, workflow o Radar. Le risposte espongono fonte, snapshot e SHA, record/puntatori, periodo, unità, universo, metodo e limiti. Gli ordinamenti sono numerici, senza graduatorie di qualità amministrativa.

| Carrier | Dimensioni e definizione | Operazioni certificate |
|---|---|---|
| `municipalEmployeesPer1000` | Organico comunale 31 dicembre 2024 / residenti Istat 1 gennaio 2024 × 1.000; organico e residenti distinti consultabili | Confronto, rango; rapporto aggregato solo dimensione totale; gap Toscana solo rapporto |
| `municipalStaffAgeStructure` | 55+, 40–54, meno di 40; conteggi / organico × 100; totale alias 55+ | Confronto, rango, rapporto da conteggi sommati della stessa classe |
| `municipalStaffTraining` | Medie totale/uomini/donne pubblicate RGS; giornate totali/uomini/donne; totale alias Media Totale RGS | Confronto, rango; gap rispetto alla selezione congiunta ufficiale Versilia; nessuna ponderazione |
| `municipalStaffTurnover` | (assunzioni nette − cessazioni nette) / organico di fine anno × 100; saldo e movimenti netti consultabili | Confronto, rango; rapporto aggregato solo dimensione totale |

Le dimensioni sono derivate dal modulo `scripts/semantic_query_rgs_adapters.py` e censite dall'audit del motore. La copertura del lotto è 7/7 Comuni. I codici istituzione RGS sono preservati e le righe sono riconciliate con nomi/codici/slugs del catalogo. Le Unioni non vengono aggiunte agli organici comunali; gli omonimi restano datori di lavoro diversi.

## Componenti e prove

- `rgs-amministrazione-2024.json`: organico, tre classi d'età, assunzioni e cessazioni nette, saldo. Le percentuali pubbliche sono riconciliate con i conteggi; il tasso arrotondato nello snapshot conserva la propria precisione, distinta dal rapporto non arrotondato. Seravezza ha saldo zero; saldi negativi restano negativi.
- `rgs-formazione-2024.json`: valori ufficiali delle giornate e delle medie. Nel payload congelato Media Totale RGS = (Media Uomini + Media Donne) / 2, nei sette Comuni e nella selezione congiunta. Non viene reinterpretata come giornate / organico. Nessun denominatore di genere retro-derivato. Il gap Versilia usa il valore restituito dall'API per i sette codici insieme, senza media delle medie comunali.
- `a3-rgs-staff-benchmark-2024.json`: archivio demografico nativo Istat e CSV integrale occupazione RGS, mappatura datore–comune e due prove PIAO di zero esplicito. L'adapter riusa il contratto nativo per certificare 273/273 Comuni toscani, 271 datori RGS e Londa/San Godenzo con organico nullo dichiarato al 31 dicembre 2024. Italia resta rifiutata per copertura non certificata.

Ogni snapshot è verificato tramite hash dei byte e hash strutturale anche quando proviene dalla cache del motore. Il pannello integrale RGS/Istat è verificato una volta per istanza e impronta del carrier, dopo verifica dello snapshot a ogni accesso: la cache non autorizza componenti pubbliche modificate. Il contratto certifica identità, anno, unità, panel, componenti, CRC e impronte delle fonti native. Età e turnover riusano l'estrazione comunale congelata: non attestano una nuova acquisizione o il replay dei CSV originari non inclusi.

## Limiti

Esternalizzazioni e gestioni associate influenzano la dotazione. Le classi d'età non autorizzano una stima dell'età media. Assunzioni e cessazioni escludono i passaggi tra amministrazioni: i conteggi sono netti, non assunzioni lorde; una sola persona modifica molto il rapporto nei piccoli organici. I movimenti dell'anno sono rapportati allo stock finale, non a un organico medio.

La fonte formazione espone annualità 2008–2024 ma nel perimetro congelato è acquisito il solo 2024. I singleton 2024 degli altri carrier non diventano storici. Serie, variazioni, trend, anomalie e correlazioni con questi carrier vengono rifiutati in entrambi gli ordini dei selettori. Anche somme/ponderazioni delle medie formazione restano rifiutate. Nessuna conclusione causale, qualità del personale o efficacia della formazione è dedotta.

## Validazione

Regressione governata dal Quick: 126 osservazioni correnti fisse, incluse alias (non nuove osservazioni indipendenti); cinque rapporti aggregati; otto riferimenti geografici pubblicati incluse alias. Riferimenti trascritti dagli snapshot, senza rivendicare una verifica live. Test avversari su identità, componenti, null/booleani, periodi, unità, parti, companion, aggregato ufficiale, snapshot/cache e hash; guardie metodologiche in entrambe le posizioni della coppia. Suite 872 domande: 415 consultazioni/calcoli e 457 rifiuti attesi.

Copertura derivata 169/225 effettivi, 118/181 sorgente, 56 residui e zero ambientali senza adapter. Report `reports/a6-rgs/`; 58 collegamenti tipizzati e 29 link companion conservati, 78 carichi descrittivi senza promessa di latenza di produzione. Quick locale prima del push, Full locale isolato e Quick/Full CI sul candidato prima della revisione per merge. A6.4 resta parziale, revisione A6.5–A6.6 aperta, A7 non avviata.
