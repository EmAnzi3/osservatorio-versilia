# Pubblicazione automatica delle nuove segnalazioni

Il refresh giornaliero promuove i nuovi avvisi MIM di edilizia scolastica prima della riconciliazione della continuità, dei gate di pubblicabilità e dell’attribuzione della prima rilevazione. Le schede così ottenute seguono il normale percorso automatico di build e pubblicazione del Radar; non richiedono l’inserimento in `verifiedEntries`.

## Contratto attualmente supportato

Avvisi ministeriali integrali per otto per mille e verifiche di vulnerabilità sismica, con articoli su finalità, soggetti/requisiti e modalità di candidatura, ammissibilità esplicita di tutti gli enti locali, ruolo sull’edificio scolastico di propria competenza e una sola finestra di candidatura completa. I requisiti specifici sono conservati nel payload e riassunti nella scheda; tutti i Comuni sono indicati come candidabili con requisiti, senza presumere il possesso di un progetto o edificio ammissibile.

Le segnalazioni possono arrivare dai canali esistenti o dal feed istituzionale ANCI Abruzzo. Si acquisisce il PDF allegato tramite HTTPS diretto su host consentiti, con controllo dei redirect, impronta SHA-256, limite di byte/pagine e il budget condiviso del trasporto. Le fixture di test non sono un fallback del runtime. Il recupero di una copia dell’avviso non dichiara sano il trasporto dell’endpoint MIM originale.

## Continuità e diagnostica

L’identità della call deriva dal titolo ministeriale e dalla finestra ricavata nel documento, indipendentemente dalla copia PDF. Le schede già pubblicate vengono riconfermate anche se la segnalazione esce dal feed; i termini scaduti passano all’archivio. Se il documento non viene acquisito, non viene prodotta una nuova verifica e restano applicabili gli attuali gate/fallback di continuità.

`documentPromotion` distingue schede aggiunte, riconfermate e archiviate e conserva gli esiti dei tentativi. `counts.documentAutomaticallyAdded` e il rapporto giornaliero separano le nuove schede verificate dal numero di segnalazioni interne. Le date annuali e i singoli protocolli degli avvisi non sono censiti nel codice.

Gli altri formati, i documenti ambigui, le restrizioni territoriali e le risposte non PDF restano in discovery con una motivazione. Questo contratto non certifica una copertura completa di tutte le opportunità: altre famiglie documentali richiedono un adattatore verificabile.
