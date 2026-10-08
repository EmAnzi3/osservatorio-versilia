# A6 — tutele naturali, reticolo e opere censite

Il motore v16 aggiunge tre adapter territoriali dagli snapshot regionali già congelati. Copertura effettiva 128/225, sorgente 86/181; 97 residui, di cui 32 ambientali. Nessuna acquisizione, modifica di dati pubblici, renderer, asset, golden o workflow. A6.4 resta parziale; revisione metodologica A6.5–A6.6 aperta e A7 non avviata.

| Carrier | Riferimenti | Dimensioni |
|---|---|---|
| `protectedNaturalAreas` | `territorio-v137-official.json`; dieci layer Regione Toscana consultati 12 settembre 2026, clipping Istat 2026 | % e ha: unione totale, parchi/riserve, ANPIL, Natura 2000, ZSC, ZPS, Ramsar |
| `managedReticulumLength` | stesso snapshot, DCRT 24/2025, clipping Istat 1 gennaio 2026 | km complessivi, km in gestione, densità km/km² |
| `hydraulicWorksCensusElements` | `bonifica-rischio-v126-gis.json`; DGRT 1155/2021, clipping Istat 2026 | presenze totali e per layer areale/lineare/puntuale |

Il periodo mantiene separati consultazione, edizione della fonte e confini di clipping: nessuna equivalenza con una misurazione annuale 2026. Nessuno storico congelato per questo lotto; serie, variazioni, trend e correlazioni temporali rifiutati. La consultazione non è la data di istituzione delle tutele. ANPIL mantiene lo stato transitorio dichiarato dalla fonte.

Per le tutele il totale è l’unione geometrica nativa, non la somma delle categorie; ZSC/ZPS sono dettagli sovrapposti di Natura 2000. A Massarosa Natura 2000, ZSC e ZPS misurano ciascuno 1.568,073761 ha: sommarli triplicherebbe quella superficie. Le quote di una categoria selezionata per un gruppo di Comuni usano somma degli ettari su somma del proprio denominatore areale, dopo riconciliazione con l’unione territoriale congelata.

Il reticolo in gestione è un sottoinsieme del complessivo, non un addendo. La densità usa lunghezze ricalcolate sulle geometrie ritagliate e superficie della stessa fonte; nessun peso sulla popolazione. `publishedValue` conserva la densità a sei decimali e `value` il rapporto nativo. Riconciliazione entro mezzo milionesimo, senza modificare il sito. Le somme territoriali sono riconciliate con le unioni congelate entro 0,00001 nelle unità native, per la precisione geometrica degli input. Non si attribuisce precisione ulteriore alle geometrie.

Le opere censite sono feature sorgente che intersecano il Comune, non cantieri, interventi conclusi o strutture fisiche indipendenti. Un elemento può attraversare più Comuni: 298 presenze comunali corrispondono a 265 feature distinte nell’unione Versilia, già deduplicate dalla fonte. L’adapter espone confronti comunali e layer; non introduce un’operazione di somma per ricostruire feature uniche. Il totale regionale di 3.666 elementi è disponibile come contesto pubblico, ma un gap comune/Toscana fra questi totali di scala diversa non è un confronto metodologicamente autorizzato e viene rifiutato. Nessuna falsa dichiarazione di indisponibilità del dato.

Ogni risposta conserva unità, definizione, metodo, periodo, file e SHA-256, puntatori ai record. Zero osservato resta distinto da dato mancante; esclusioni richiedono opt-in. Le fonti, i riferimenti, le identità dei Comuni, i componenti, la gerarchia e le unioni sono verificati prima del calcolo. Le relazioni tra fotografie di tutele e reticolo sono contesto, non correlazioni automatiche fra periodi diversi o causalità.

161 osservazioni contro input fissi trascritti dalle fonti, con aritmetica indipendente e prove avversarie. Il conteggio include alias delle dimensioni, non 161 dati distinti. Suite cumulativa 230/230: 144 calcoli e 86 rifiuti attesi; 41 collegamenti tipizzati, 37 carichi di prestazione. Le 35 letture territoriali e due riepiloghi restano invariati.

Report `reports/a6-territory/`; gate nel preflight canonico per sorgente e catalogo effettivo. Quick locale prima del push; Full locale isolato e CI Quick→Full sul medesimo candidato prima della revisione per merge. Merge e pubblicazione richiedono approvazione esplicita del proprietario.
