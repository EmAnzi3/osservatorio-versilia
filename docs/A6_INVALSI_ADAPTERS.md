# A6 — adapter INVALSI v34

Quattro carrier del catalogo effettivo: risultati WLE, traguardi/livelli di competenza, dispersione implicita ed eccellenza accademica. Nessuna nuova acquisizione, modifica di dati, interfaccia, golden, workflow o Radar. La base è lo snapshot ufficiale v1.38 già usato dalla build; metodo sorgente in `docs/invalsi-v138-methodology.md`.

## Selezioni e operazioni

`total` è un alias della vista pubblicata predefinita, **non** una somma o media fra gradi/prove: classe V Italiano per risultati, classe V Inglese Reading per competenza, grado 8 per dispersione/eccellenza. Le dimensioni `view:<chiave>` distinguono 16 prove risultati, 12 prove competenza e due gradi per ciascuno degli altri carrier.

Confronto, rango numerico descrittivo, serie consultabile e gap con Toscana/Italia sono ammessi soltanto a parità di vista e anno scolastico. I benchmark sono aggregazioni ufficiali Totale dello stesso dataset, anche nelle annate storiche disponibili; non medie comunali. Il Comune è quello del **plesso**, non la residenza dello studente. Nessun rango di qualità scolastica o priorità amministrativa.

Per competenza, `view:<chiave>|level:level-<n>` seleziona la percentuale nella categoria ufficiale, con etichetta conservata: livelli 1–5 o QCER secondo grado/prova. Sono ammesse consultazioni correnti, ranghi e benchmark; le serie dei livelli sono rifiutate perché il catalogo pubblica solo la distribuzione corrente. La serie del traguardo rimane distinta dalla distribuzione: non viene ricostruita sommando percentuali arrotondate. Dispersione ed eccellenza non sono complementi né una partizione da sommare.

## Periodi, assenze e limiti

I periodi richiedono il token scolastico esatto `AAAA-AA`, con secondo anno consecutivo. `2025` e `2024/25` sono rifiutati. Le finestre sono quelle dello snapshot: primaria Italiano/Matematica dal 2018–19; Inglese primaria e grado 8 dal 2017–18; grado 10 dal 2017–18 senza 2020–21; grado 13 dal 2018–19. Il 2019–20 manca perché le prove non si svolsero: nessuna interpolazione o annata inventata.

I null ufficiali restano indisponibilità (celle assenti/soppresse), mai zeri, non applicabilità o prova dell'assenza di scuole. Le consultazioni incomplete richiedono `allowPartial: true`; restano i minimi di osservazioni del contratto generale. La precisione pubblicata è conservata. Le percentuali di partecipazione/copertura non sono denominatori di studenti/prove valide: pooling, media Versilia e ricostruzione dei conteggi sono rifiutati.

Variazioni, trend, anomalie e correlazioni sono rifiutati: la disponibilità di una serie non certifica continuità metodologica o una coppia analitica. Il guard della correlazione si applica a entrambi i selettori. A6.4 resta parziale; A6.5–A6.6 richiedono revisione, A7 non avviata.

## Provenienza riproducibile

Lo snapshot JSON è ricostruito concatenando i cinque file **persistenti** `data/source-snapshots/invalsi-v138-b64/part-00.b64` … `part-04.b64`, decodificando Base64 e gzip. Non viene dichiarato un file JSON temporaneo inesistente. Ogni osservazione conserva:

- puntatore alla cella numerica/null nel catalogo effettivo e SHA del catalogo;
- puntatore al record nel JSON ricostruito, elenco dei frammenti reali e rispettivi SHA;
- SHA dei byte JSON decodificati, `sha256Basis=decoded_json_bytes`, encoding e contesto di selezione.

Byte JSON: `bee5b0021704b2053277aa19df35d77ed0aa4b9e2cfc4dfa3d64c16a61c1fd65`. Fingerprint JSON canonico: `e3b6fbe41f8dd4090b85a5ddc74904137c1c65f4597e63e2f8a7d29924b16b46`. Il primo accesso verifica i frammenti; gli accessi successivi verificano contenuto e metadati della cache. Le informazioni sorgente e le scelte native sono protette dal fingerprint. Nessuna acquisizione di rete durante la query.

L'adapter riconcilia tutte le celle pubbliche, serie e assi, grado/prova, coperture, categorie, alias predefiniti, identità comunali e benchmark con lo snapshot. Rifiuta mutazioni, imputazioni, componenti inventate e normalizzazioni non revisionate.

## Verifica

`test_semantic_invalsi_adapters.py` distingue 28 celle correnti e 21 storiche trascritte, otto benchmark e due valori QCER fissi (incluso lo zero) dal replay indipendente di tutti i record congelati, benchmark e categorie. Il decoder del test non usa l'adapter per costruire aspettative. Verifica anche i puntatori, hash dei frammenti, periodi esclusi, minimi, selezioni incomparabili e mutazioni ostili del catalogo/cache/file.

184 nuove domande versionate in `ci/semantic-verified-questions.json`; le aspettative sono record sorgente indipendenti dalle risposte del motore. Report derivati in `reports/a6-invalsi/`, quattro nuovi carichi nel benchmark descrittivo. I report preliminari usano il catalogo congelato della baseline #384 con SHA invariato; i gate canonici in cloni freddi verificano che la build candidata produca lo stesso catalogo. Le ricevute finali locali e CI sono consegnate nella PR e nell'archivio delle evidenze.
