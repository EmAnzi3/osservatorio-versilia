# Metodo dei dossier e riferimenti

Riferimenti primari consultati il 13 ottobre 2026; principi trasferibili, senza importare dataset o implementazioni. La verifica metodologica online è distinta dall’integrità degli snapshot locali.

| Riferimento | Principio utile | Applicazione locale e limite |
|---|---|---|
| [ONS Explore Local Statistics — QMI](https://www.ons.gov.uk/peoplepopulationandcommunity/healthandsocialcare/healthandwellbeing/methodologies/explorelocalstatisticsserviceqmi) e [metodo dei territori simili, marzo 2026](https://www.ons.gov.uk/peoplepopulationandcommunity/wellbeing/methodologies/clusteringsimilarlocalauthoritiesandstatisticalnearestneighboursintheuk) | Esplicitare qualità, geografia e criteri di somiglianza; confrontare territori coerenti | Documentare selezione dei confronti. Non trasferire cluster UK ai sette Comuni; non esiste oggi un pannello italiano di peer acquisito |
| [OpenCivitas — fabbisogni standard](https://www.opencivitas.it/portale/progetto/fabbisogni-standard) | Distinguere condizioni territoriali, fabbisogni, risorse e servizi | Un euro per residente non misura efficienza né servizio adeguato. Dati OpenCivitas individuati come riferimento, non acquisiti |
| [Urban Institute — Upward Mobility, metodologia](https://upward-mobility.urban.org/methodology) | Collegare condizioni, interventi e risultati con una teoria del cambiamento esplicita | Formulare ipotesi e indicatori di monitoraggio; risultati di ricerca USA non provano effetti locali né autorizzano previsione |
| [ISTAT — A misura di Comune](https://www.istat.it/statistica-sperimentale/aggiornamento-degli-indicatori-del-sistema-informativo-a-misura-di-comune/) | Integrare fonti territoriali, definizioni e periodi per la programmazione | Riutilizzare esclusivamente dati acquisiti e adapter ammessi; la presenza nel portale esterno non è disponibilità nel nostro motore |
| [Data Commons — modello](https://docs.datacommons.org/data_model.html) e [osservazioni/facets](https://docs.datacommons.org/api/rest/v2/observation.html) | Osservazione qualificata da entità, variabile, periodo e provenienza | Conservare ID canonici, dimensioni, metodi e snapshot nelle risposte. Non creare un grafo parallelo o assumere un’API esterna necessaria |

## Protocollo dei confronti

Prima viene definita la domanda: descrizione fra i sette Comuni, benchmark autorizzato, confronto con territori simili o valutazione di un intervento. Questi oggetti sono diversi. Un benchmark Toscana/Italia disponibile per una vista non è automaticamente un confronto fra Comuni simili.

Per un futuro pannello di peer occorre dichiarare unità amministrativa, periodo, dimensione demografica, struttura per età, assetto costa/entroterra, densità, turismo e organizzazione dei servizi, poi motivare i criteri pertinenti alla domanda. Le variabili usate per selezionare i peer non devono coincidere acriticamente con l’esito da giudicare. Si documentano esclusioni e sensibilità alla selezione; non si produce una graduatoria politica. Oggi questo pannello non è disponibile: il motore risponde solo sui territori e benchmark già certificati.

Per una composizione si affiancano richieste indipendenti conservando il periodo di ciascuna. Si calcola un nuovo rapporto solo quando esiste una composizione autorizzata con numeratore, denominatore, universo e periodo compatibili. Non si uniscono stock, flussi, anni scolastici, esercizi o fotografie con un anno artificiale comune. Medie semplici e rapporti delle somme sono oggetti distinti. Missing e copertura parziale rimangono dichiarati; non si deduce zero da assenza.

## Dall’osservazione alla politica

La struttura narrativa obbligatoria è: osservazione verificata → analisi ammessa → ipotesi da controllare → opzione amministrativa da approfondire. Ogni passaggio aggiunge assunzioni dichiarate, non nuovi numeri inventati. Associazioni ecologiche sui sette Comuni non consentono inferenze individuali; denominatori condivisi e outlier possono spiegare una relazione apparente. La presenza di due indicatori non rende automaticamente pertinente una correlazione.

Per valutare un intervento servono obiettivo, platea, attività, output, esito, calendario, baseline e un confronto che permetta di separare il cambiamento dagli altri fattori. Il monitoraggio descrittivo prima/dopo non basta ad attribuire causalità. Un dossier può specificare il disegno e il fabbisogno informativo; non dichiarare effetti che i dati attuali non identificano.

Le opzioni sono istruttorie: competenza dell’ente, destinatari, alternative, costi, vincoli, accesso ed eventuali effetti distributivi devono essere verificati prima di una decisione. Nessuna raccomandazione automatica viene prodotta.

## Competenze: livello e verifica locale

La mappa usa le [funzioni fondamentali comunali riepilogate dalla Regione Toscana](https://www.regione.toscana.it/it/-/elenco-funzioni-fondamentali), il [sistema regionale dei trasporti](https://www.regione.toscana.it/-/sistema-regionale-della-mobilita-dei-trasporti-e-della-logistica) e l’integrazione sociosanitaria della [legge regionale 40/2005, art. 71 bis](https://raccoltanormativa.consiglio.regione.toscana.it/articolo?anc=art71bis&dl_a=y&dl_id=&dl_t=text/xml&pr=idx,0%3Bartic,0%3Barticparziale,1&urndoc=urn:nir:regione.toscana:legge:2005-02-24%3B40+).

La distinzione generale per l’edilizia scolastica va verificata sulla [disciplina ufficiale e atti attuativi della legge 23/1996](https://www.gazzettaufficiale.it/atto/serie_generale/caricaArticoloDefault/originario?atto.codiceRedazionale=098A7441&atto.dataPubblicazioneGazzetta=1998-08-20&atto.tipoProvvedimento=CIRCOLARE). Non sono qui certificati deleghe, convenzioni, gestori o assetti locali correnti. Per scuola distinguere edilizia e servizi locali da didattica, organici e rete; per sanità distinguere programmazione/inclusione comunale dall’erogazione ASL; per TPL distinguere Regione, enti territoriali e operatori. Prima dell’istruttoria verificare l’assetto effettivo della zona sociosanitaria: il dossier non assume l’esistenza attuale di una specifica Società della Salute in Versilia.

## Gestione delle lacune

Ogni lacuna è collegata a una conclusione impedita e a un potenziale uso: utenti/attese per copertura, canoni e redditi dei nuclei per onere, matrici OD e tempi per accessibilità, prestazioni ed esiti per efficienza, collaudo e messa in esercizio per opere. Una fonte esterna da esplorare non diventa un valore in risposta. Un’eventuale acquisizione futura richiede priorità, licenza, geografie, periodi, definizioni e snapshot, attraverso il flusso ordinario; non appartiene a questa PR.

## Ammissione degli enrichment: guadagno conoscitivo

Ogni proposta deve dichiarare: domanda del dossier; risposta oggi sostenuta; risposta aggiuntiva ottenibile; dati acquisiti da riusare e integrazioni realmente necessarie; copertura di Comuni/periodi/definizioni, continuità e aggiornamento. La priorità dipende dal guadagno (distinguere capacità e utilizzo, mostrare una trasformazione, documentare un divario o una risorsa), non dal numero di indicatori. Perimetri, diritti di riuso, snapshot, componenti native e test indipendenti precedono una nuova evidenza pubblica. Non si modifica a mano la matrice A3 per dichiarare acquisizioni.

### Proposta successiva: domanda e utilizzo dei servizi 0–3

- **Domanda esistente da approfondire:** l'offerta educativa incontra le richieste delle famiglie? Collegamento al piano `infanzia-centrale`, senza duplicarlo o aggiungere domande per conteggio.
- **Oggi:** capacità potenziale 2024/25, posti e bambini 3–36 mesi; sette Comuni, componenti native e rapporto territoriale ponderato già acquisiti. Non sono iscritti, frequenza o bisogno insoddisfatto.
- **Guadagno atteso:** distinguere domanda espressa, accoglienza, attese e utilizzo della ricettività; separare aumento dei posti e diminuzione dei bambini. Sono obiettivi di verifica, non conclusioni già attribuite ai Comuni.
- **Fonte individuata:** Regione Toscana, [Uno sguardo sui servizi educativi 2024/25](https://www.regione.toscana.it/it/-/uno-sguardo-sui-servizi-educativi-anno-educativo-2024-2025), consultata il 17 ottobre 2026. La pagina ufficiale dichiara download a livello comunale, sezioni offerta/domanda e liste d'attesa, accoglienza e saturazione. [Catalogo prima infanzia](https://dati.toscana.it/dataset/serviziprimainfanzia): HTTP403 nel controllo online; nessuna osservazione acquisita o copertura 7/7 attestata da tale controllo.
- **Verifiche prima dell'ammissione:** campi effettivi e codici territoriali per tutti i sette Comuni; conteggio delle domande e possibili duplicazioni; differenze tra domanda, rinunce, attese e bambini unici; data della fotografia e universo 3–36 mesi; tipologie/gestioni; null/zeri; annualità recenti confrontabili e discontinuità. L'esistenza di annualità nel portale non certifica una serie locale.
- **Criterio di accettazione:** dati originali congelati e riconciliati con somme/componenti e controlli indipendenti; limiti e coperture dichiarati; uso nel dossier collegato alla domanda. Acquisizione tramite flusso ordinario in PR separata, dopo il lotto educativo territoriale. OpenCivitas resta un'integrazione successiva da valutare, non un pannello già acquisito.

Dopo l'educazione, lavoro/redditi può riutilizzare anzitutto occupazione per età/genere, redditi e struttura economica già acquisiti, mantenendo universi e periodi distinti. Gli altri piloti restano nel programma esistente: nessun inventario parallelo, graduatoria politica o fabbisogno di acquisizione fissato per volume.

Prima di nuove acquisizioni, le composizioni già ammesse possono affiancare tempo pieno/mensa e accessibilità/trasporto degli edifici, conservando unità e denominatori distinti (`docs/A6_DEMOGRAPHY_SCHOOL_ADAPTERS.md`). Sono capacità disponibili da valorizzare in un approfondimento mirato, non misure di capienza o accesso individuale. Lo storico MIM non è reso disponibile da questi collegamenti. Questo lotto non aggiunge tali confronti alla pagina educativa.
