# Pubblicazione automatica delle nuove segnalazioni

Il refresh giornaliero promuove i nuovi avvisi MIM di edilizia scolastica prima della riconciliazione della continuità, dei gate di pubblicabilità e dell’attribuzione della prima rilevazione. Le schede così ottenute seguono il normale percorso automatico di build e pubblicazione del Radar; non richiedono l’inserimento in `verifiedEntries`.

## Contratto attualmente supportato

Avvisi ministeriali integrali per otto per mille e verifiche di vulnerabilità sismica, con articoli su finalità, soggetti/requisiti e modalità di candidatura, ammissibilità esplicita di tutti gli enti locali, ruolo sull’edificio scolastico di propria competenza e una sola finestra di candidatura completa. I requisiti specifici sono conservati nel payload e riassunti nella scheda; tutti i Comuni sono indicati come candidabili con requisiti, senza presumere il possesso di un progetto o edificio ammissibile.

Le segnalazioni possono arrivare dai canali esistenti o dal feed istituzionale ANCI Abruzzo. Si acquisisce il PDF allegato tramite HTTPS diretto su host consentiti, con controllo dei redirect, impronta SHA-256, limite di byte/pagine e il budget condiviso del trasporto. Le fixture di test non sono un fallback del runtime. Il recupero di una copia dell’avviso non dichiara sano il trasporto dell’endpoint MIM originale.

## Continuità e diagnostica

L’identità della call deriva dal titolo ministeriale e dalla finestra ricavata nel documento, indipendentemente dalla copia PDF. Le schede già pubblicate vengono riconfermate anche se la segnalazione esce dal feed; i termini scaduti passano all’archivio. Se il documento non viene acquisito, non viene prodotta una nuova verifica e restano applicabili gli attuali gate/fallback di continuità.

`documentPromotion` distingue schede aggiunte, riconfermate e archiviate e conserva gli esiti dei tentativi. `counts.documentAutomaticallyAdded` e il rapporto giornaliero separano le nuove schede verificate dal numero di segnalazioni interne. Le date annuali e i singoli protocolli degli avvisi non sono censiti nel codice.

Gli altri formati, i documenti ambigui, le restrizioni territoriali e le risposte non PDF restano in discovery con una motivazione. Questo contratto non certifica una copertura completa di tutte le opportunità: altre famiglie documentali richiedono un adattatore verificabile.

## Verifiche richieste, senza ricerca manuale degli allegati

Il rapporto giornaliero e la notifica GitHub espongono subito le **Verifiche richieste**. Ogni segnalazione da controllare contiene pagina sorgente, collegamenti diretti ai documenti individuati, motivo del blocco e controllo da svolgere. Se il documento non è stato trovato, se la ricerca non è ancora stata eseguita o se è disponibile solo un riferimento precedente, viene dichiarato esplicitamente. I problemi di trasporto e di budget sono distinti dalle verifiche di persona: il Radar li ritenta automaticamente.

La ricerca degli allegati riusa le pagine già acquisite; per le altre usa HTTPS diretto su host del registro fonti, con verifica TLS e redirect controllati. È limitata a 24 pagine e 90 secondi, entro il budget globale del run; ciascuna nuova richiesta ha un limite di 8 secondi. I risultati sono conservati con data e riesaminati dopo sette giorni. Le pagine mai esaminate hanno priorità rispetto ai ritentativi, per evitare che il limite lasci sempre indietro gli stessi avvisi. L'individuazione di un allegato non certifica l'ammissibilità e non promuove da sola una scheda.

Una segnalazione ancora priva di verifica documentale rimane tra i tentativi automatici finché la ricerca degli allegati non è stata eseguita. Solo dopo quel tentativo il rapporto può richiedere una verifica di persona, con i documenti individuati oppure con l’esplicita indicazione che la ricerca non ha trovato l’allegato.

Il lettore MIM supporta anche collegamenti diretti ai PDF, intestazioni `Articolo` e separatori diversi. Articoli ripetuti o finestre discordanti richiedono verifica. Un PDF senza testo viene segnalato come scansionato, senza pubblicazione da una lettura incompleta. Le approvazioni di graduatorie senza una riapertura documentata sono distinte dalle nuove candidature; i termini conclusi sono classificati soltanto da date strutturate o da una finestra ministeriale integrale.

Le segnalazioni sono raggruppate per riferimento esatto, conservando la contabilità delle ripetizioni. Pagine di navigazione, riferimenti già associati a schede pubblicate e termini conclusi sono visibili separatamente. La coda grezza resta conservata: la vista operativa non è una cancellazione delle evidenze né una certificazione di tutte le opportunità mancanti. I cambiamenti delle verifiche richieste entrano nell'impronta della notifica, anche quando il numero delle schede pubbliche non cambia.

I rapporti che superano il limite di un corpo GitHub proseguono automaticamente nei commenti della stessa segnalazione, con tabelle e collegamenti diretti. Un ritentativo completa le parti mancanti senza duplicare la segnalazione o le parti già inviate.
