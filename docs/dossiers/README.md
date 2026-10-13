# Programma dei dossier territoriali

Proposta editoriale separata da A6 e dall’implementazione A7. Baseline integrata: `d09d8e2f695a859e555cae28db69655f7b6d7130` (#428), albero `c96760860332737c0532c1b532ed240e4857ed07`. A6 DONE dopo approvazione/merge del proprietario, verifiche post-merge e attestazione nella #428/issue #330. Questa proposta editoriale non estende A6 e non avvia infrastrutture o interfacce conversazionali.

Il punto di partenza è una decisione da comprendere, non un indicatore da pubblicare. I dossier collegano fenomeni, domanda di servizi, risorse, attività e risultati, rendendo visibile dove la catena conoscitiva si interrompe. Un amministratore può usarli per chiedere un approfondimento; un cittadino per controllare una spiegazione; un ricercatore per formulare ipotesi verificabili; un giornalista per distinguere numeri osservati e promesse.

## Artefatti e autorità

- [Programma e matrice di fattibilità](../../reports/territorial-dossiers/program-and-feasibility.md): per ogni dossier problema, domande, fonti e periodi eseguiti, capacità, composizione, lacune, competenze, opzioni, monitoraggio e relazioni.
- [Sotto-dossier e lacune](MODULES.md): articolazione del programma, componenti disponibili e dati necessari, senza nuove acquisizioni.
- [Dimostrazione lavoro — Massarosa](MASSAROSA_LAVORO.md) e [dimostrazione infanzia/scuola — Massarosa](MASSAROSA_INFANZIA_SCUOLA.md): due analisi leggibili, con fonti e richieste riproducibili.
- [Repertorio](QUESTIONS.md): valorizzazione delle 20 domande A6 e nuove domande motivate; classificazione riferita alla domanda esatta.
- [Specifiche pilota](PILOTS.md): percorso di analisi, query effettivamente eseguite e risposte nel loro perimetro.
- [Metodo e riferimenti](METHOD.md): principi trasferibili e protocollo per confronti, interpretazioni e valutazione.
- `ci/territorial-dossier-program.json`: riferimenti editoriali agli ID canonici, senza valori, definizioni, route o catalogo duplicato.
- `scripts/build_territorial_dossier_evidence.py`: risolve tali riferimenti e produce evidenze dai dati effettivi e dalle aspettative numeriche già approvate.

Il catalogo canonico resta `data/site-data.json`, materializzato secondo i contratti esistenti. Dimensioni e operazioni si ricavano dal motore e dai report A6, non da un secondo inventario editoriale. Le tabelle generate riportano solo le viste interrogate: non attestano l’esecuzione di ogni combinazione possibile. La copertura generale rimane responsabilità delle suite A6 approvate.

## Mappa delle relazioni

| Problema | Collegamenti necessari | Errore da evitare |
|---|---|---|
| Opportunità economiche dei residenti | Lavoro ↔ redditi ↔ mobilità ↔ infanzia | Confondere addetti localizzati, occupati residenti e reddito delle famiglie |
| Continuità educativa | Demografia ↔ infanzia/scuola ↔ mobilità ↔ bilanci | Dedurre bacini e domanda dal solo Comune della scuola |
| Autonomia e cura | Anziani ↔ welfare ↔ sanità ↔ abitazione | Identificare bisogno con prestazioni erogate |
| Accesso alla casa | Abitazione ↔ redditi ↔ turismo ↔ suolo | Calcolare oneri familiari da OMI e imponibile individuale |
| Pressione sui servizi | Turismo ↔ ambiente ↔ mobilità ↔ bilanci | Trattare presenze annuali come popolazione giornaliera |
| Risultati dell’azione pubblica | Bilanci ↔ investimenti ↔ capacità ↔ partecipazione | Trasformare spesa o conclusione amministrativa in efficacia |
| Transizione territoriale | Ambiente ↔ suolo/agricoltura ↔ energia ↔ lavoro | Attribuire variazioni a interventi senza disegno di valutazione |

## Priorità motivate

Si sviluppano prima lavoro, infanzia/scuola, anziani, mobilità e bilanci/servizi: esistono query riconciliate, collegamenti fra fenomeni e competenze amministrative identificabili. La prima versione deve essere un dossier descrittivo verificabile, con esplicita sezione sulle risposte ancora impossibili. L’abitazione ha pari rilevanza pubblica ma richiede un pilota esplorativo: la priorità del problema non elimina la lacuna sull’onere dei nuclei. Gli altri ambiti rimangono un programma organico, senza numero-obiettivo né obbligo di riempire pagine prive di evidenza.

La valutazione è qualitativa, senza punteggio sintetico dei Comuni. I criteri sono rilevanza, solidità, connessioni, confronti ammissibili, competenze e monitorabilità. Nessun pilota autorizza automaticamente una politica; nessuna lacuna comporta ora un’acquisizione.

## Riproduzione

Dopo la build ordinaria, sul catalogo effettivo prodotto dai contratti:

```bash
python scripts/build_territorial_dossier_evidence.py --catalog dist/data/site-data.json --output-dir /tmp/territorial-dossiers
```

Il JSON conserva richieste complete, aspettative, risposta, provenienza, operazioni della vista e motivi di rifiuto; il Markdown permette la revisione editoriale. Le aspettative congelate provengono da `ci/semantic-verified-questions.json`. Per le poche viste senza una domanda numerica in quel repertorio si controllano gli anchor del catalogo effettivo, separando precisione nativa ARS e arrotondamento delle schede: questa verifica aggiuntiva non sostituisce la riconciliazione agli snapshot già effettuata da A6.

Gli hash e il riepilogo dell’esecuzione candidata sono in `reports/territorial-dossiers/summary.json`. Sono verificati gli input congelati; la consultazione dei riferimenti metodologici online non certifica la disponibilità corrente di tutte le fonti statistiche. I dati ulteriori indicati sono fabbisogni informativi, non dati acquisiti.

## Criteri di consegna di un dossier

Una versione pubblicabile deve avere domanda esatta, richieste riproducibili, copertura territoriale e temporale, valori con fonti e universi, distinzione osservazione/analisi/ipotesi/opzione, lacune e monitoraggio. La redazione e la verifica dei dati precedono una futura PR UI con preview e browser. Questi documenti non modificano dati, adapter, 35 letture, due riepiloghi, 20 domande originarie, golden o interfacce.

## Domande e verifiche editoriali

Ogni domanda centrale e secondaria dichiara richieste necessarie, eventuale contesto che non risponde alla domanda, risposta circoscritta e informazioni mancanti. Le domande originarie A6 sono referenziate per evitare di presentare approfondimenti come nuove analisi indipendenti. I vecchi quesiti sulla comparabilità sono conservati come controlli metodologici separati.

Le due dimostrazioni sono documenti editoriali in Markdown, non nuove pagine del sito. Gli altri quattro piloti restano specifiche; gli altri ambiti restano un programma. Non sono 17 dossier già completati, né 71 analisi certificate. Il numero di query descrive richieste eseguite, non domande utili.

Quick verifica il contratto dei piani e, dopo la build, riesegue le richieste e confronta tutti i documenti generati byte per byte. I test ostili impediscono riferimenti inesistenti, rifiuti usati come risposte, dichiarazioni di completezza con lacune, perdita di dati nelle dimostrazioni, confronti testuali diventati falsi e medie comunali scambiate per rapporti aggregati. La correttezza editoriale delle interpretazioni richiede comunque revisione umana; non è certificata automaticamente da un PASS.
