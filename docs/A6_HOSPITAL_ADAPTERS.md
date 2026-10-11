# A6 — Strutture ospedaliere, adapter v44

Il carrier `hospitals` offre due letture distinte al riferimento pubblico 2025, per tutti i sette Comuni: `total` conta i presidi localizzati; `view:normalized` legge i posti letto ogni 10.000 residenti. Il secondo valore non è il numero di presidi rapportato alla popolazione. Il conteggio pubblico comprende tre presidi: uno ciascuno a Camaiore, Forte dei Marmi e Viareggio. Gli zeri negli altri Comuni descrivono localizzazione, non assenza di assistenza sanitaria.

Sono ammessi `compare` e `rank`, come confronti numerici descrittivi. Ordinamento e pari merito non misurano accessibilità, qualità delle cure, fabbisogno o priorità politica. L'etichetta 2025 è il riferimento del catalogo: data esatta dello stock e data del denominatore dei posti letto non sono attestati separatamente dal materiale congelato.

## Prova e limiti

L'adapter legge esclusivamente i valori già pubblicati dal catalogo governato, con puntatore, percorso e hash del catalogo in ogni osservazione. Due fingerprint revisionati distinguono il catalogo sorgente e quello effettivo: la materializzazione aggiunge metadati di confronto, senza modificare le osservazioni. L'intera definizione del carrier è ricontrollata a ogni accesso, anche dopo aver usato la cache. Nessun nuovo download o cambiamento di dati, pagine, asset, baseline visive o workflow.

Questa è una riconciliazione dei valori pubblici, **non** un replay dei record ministeriali dei singoli presidi. Nel repository non è disponibile un pannello originario congelato che consenta di verificare identità/deduplicazione dei presidi o numeratore e denominatore dei tassi. I componenti non vengono ricostruiti dal rapporto. Anche l'aggregato pubblico dei tassi resta fuori dalle query: non viene presentato come pooling verificato.

Sono rifiutati `weighted_ratio`, benchmark Toscana/Italia/Versilia, serie e analisi temporali, anomalie e correlazioni in entrambe le direzioni. Dimensioni di genere, conteggi dei posti letto, numeratore e denominatore non acquisiti restano non interrogabili. Le avvertenze sul perimetro e sulle date accompagnano entrambe le letture.

## Verifica

Il test conserva 14 riferimenti pubblici indipendenti: sette conteggi e sette tassi. Verifica zeri, ordinamento e pari merito, unità, periodo e puntatori; prova modifiche ostili a dati/definizioni dopo la prima query, geografie e rifiuti metodologici. Non dichiara controlli sui documenti originari assenti.

49 nuove domande con aspettative versionate preservano integralmente le 2.427 precedenti. Suite, copertura e collegamenti sono derivati dagli script generali in `reports/a6-hospitals/`; tre nuovi carichi descrittivi coprono lettura, ordinamento normalizzato e rifiuto del pooling. I tempi non sono un limite garantito di produzione. A6.4 rimane parziale, A6.5–A6.6 aperte, A7 non avviata. Gate canonici locali e CI prima della prontezza al merge del proprietario.
