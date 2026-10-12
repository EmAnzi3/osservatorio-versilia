# A6 — Affluenza per consultazione

Un carrier effettivo `voterTurnout`, 26 viste, nessuna acquisizione. L'archivio già pubblico contiene 71 consultazioni sovracomunali con 7/7 Comuni: 19 Politiche Camera (1948–2022), 10 Europee (1979–2024), 12 Regionali Toscana (1970–2025), 30 quesiti referendari (1974–2026). Le date dell'archivio sono identificatori canonici e possono non descrivere l'intero intervallo di voto.

## Selezione e misure

`total` è il valore numerico corrente del carrier, referendum costituzionale `referendum-20260322-q1`, non arrotondato come la stringa UI. `nativeRatio` usa i suoi elettori e votanti. Solo per questi alias, `2026` identifica quella consultazione precisa; non un tasso annuale.

Le altre viste hanno forma `family:<famiglia>`, opzionalmente `|sex:men`/`|sex:women` e `|nativeRatio`. Famiglie ammesse: `politiche_camera`, `europee`, `regionali_toscana`, `referendum`. Senza periodo scelgono l'ultima consultazione della propria famiglia. I periodi espliciti usano gli ID dell'archivio, ad esempio `europee-20240609` o `referendum-20250608-q5`. I cinque quesiti del 2025 restano cinque identità: nessuna media/somma dei quesiti e nessun confronto di più periodi in una cross-section. Gli ID legacy `q1,00` sono conservati senza riscrivere il dato.

Le viste famiglia pubbliche conservano i tassi a quattro decimali. Quelle native calcolano `votanti / elettori × 100` dai conteggi interi; il pooling è ammesso soltanto nella vista nativa, per la stessa consultazione e sesso. Somma separatamente votanti ed elettori dei Comuni selezionati; non pondera con residenti né media semplicemente le percentuali.

| Famiglia corrente | Consultazione | Votanti Versilia | Elettori Versilia |
|---|---|---:|---:|
| Politiche Camera | 25 settembre 2022 | 84.841 | 131.004 |
| Europee | 9 giugno 2024, data archivio | 63.700 | 138.291 |
| Regionali Toscana | 12 ottobre 2025, data archivio | 58.618 | 141.670 |
| Referendum costituzionale | 22 marzo 2026, data archivio | 81.908 | 130.152 |

Elettori registrati diversi da residenti; votanti diversi da voti validi. La consistenza delle liste, il voto all'estero e le regole del corpo elettorale possono cambiare fra consultazioni: la continuità dei denominatori non è attestata da questo lotto. Il rango numerico non misura qualità civica o priorità politica.

## Storici e sesso

Le serie sono consultazioni irregolari, mai anni interpolati. Politiche Camera, Europee e Regionali sono consultabili separatamente. Variazioni, trend e punti percentuali sono rifiutati finché la continuità degli universi non è revisionata. Per i referendum non esiste una singola serie dello stesso quesito: ogni consultazione storica resta consultabile con il suo ID, mentre l'operazione `series` è rifiutata.

Il sesso è disponibile solo se entrambi i sessi hanno numeratore, denominatore positivo e tasso per tutti i sette Comuni. Le Regionali 1990 hanno `mfComplete=true` nell'archivio, ma le colonne femminili sono zero/null e quelle maschili replicano il totale: entrambi i dettagli sono esclusi come incompleti, senza correggere il dato pubblico né imputare zeri. Le osservazioni espongono separatamente `sourceSexCompletenessFlag` e `sexComponentsComplete`. Anche Regionali 2025 e referendum 2026 non hanno dettaglio per sesso.

Le serie con lacune richiedono `allowPartial=true`; i null sono conservati e gli indici esclusi sono espliciti. Per Massarosa/Europee maschili, 10 consultazioni richieste e cinque utilizzabili: le prime cinque restano null. Un denominatore zero nel dettaglio mancante non diventa un'affluenza zero.

## Replay e rifiuti

Le quattro parti `data/affluenza/archive-v2-00.b64`…`03.b64` vengono concatenate, decodificate base64/gzip e verificate con hash di ciascuna parte, hash dei byte JSON e fingerprint completo dopo cache. Il catalogo pubblico corrente è verificato separatamente e riconciliato con i conteggi della consultazione corrente. Ogni tasso disponibile, partizione per sesso e aggregato territoriale è controllato aritmeticamente.

Il replay riguarda i record comunali normalizzati dell'archivio; non i file DAIT originali, i singoli elettori o il precedente gate di acquisizione. `normalizedRecordReplayAvailable=true` e `nativeRecordReplayAvailable=false` dichiarano questa distinzione. Per i dati esterni al carrier corrente la provenienza usa il puntatore alla definizione del carrier e quello reale all'osservazione decodificata; le viste native conservano i puntatori ai conteggi e distinguono il tasso arrotondato dal risultato calcolato.

Le 53 consultazioni comunali non sono messe in un confronto delle “ultime” a date diverse: date/turni/fonti non sono revisionati per questa operazione. I 53 contesti referendari della provincia di Lucca non sono dati dei Comuni e non riempiono il vuoto comunale 1987–2006. Senato, benchmark Toscana/Italia/Versilia, anomalie e coppie con altri carrier restano rifiutati. Il rapporto Versilia è disponibile come pooling nativo esplicito.

## Verifiche e stato

28 coppie native correnti, 28 coppie per sesso e 41 coppie storiche Massarosa fissate indipendentemente. Replay distinto di 2.982 celle ammesse, incluse quelle mancanti: 71 consultazioni × sette Comuni × tre perimetri di sesso × due viste. Test di aggregazione, rango, quesito, alias, copertura parziale, provenienza e input ostili su byte/cache/definizioni.

260 domande aggiunte e 2.928 precedenti preservate esattamente; 3.188/3.188 PASS (1.758 calcoli, 1.430 rifiuti), report `reports/a6-turnout/`. Copertura derivata 218/225 effettivi, sette residui; sorgente 160/181 invariata perché il carrier è materializzato soltanto nella release effettiva. 157 carichi prestazionali descrittivi. Nessuna modifica a dati/UI/asset/golden/workflow/Radar o alle 35 letture e due riepiloghi.

Quick locale completo prima del push, Full locale completo e CI Quick→Full/A3 sullo stesso albero prima della prontezza. A6.4 resta parziale, A6.5–A6.6 aperte, A7 non avviata. Merge riservato al proprietario.
