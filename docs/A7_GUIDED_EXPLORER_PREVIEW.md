# A7 — anteprima dell’esploratore generale

Incremento di interazione guidata sopra il motore originale e il pacchetto
verificato. A6 resta DONE, A7 IN_PROGRESS. Non modifica la build pubblica,
la navigazione, gli adapter, i dati o i golden. Non pubblica nuove pagine.

## Esperienza verificabile

Il builder copia un `dist/` canonico in una nuova destinazione isolata e inserisce
l’esploratore in `/chiedi/`, prima dei percorsi editoriali conservati. La preview
riusa shell, banner, ricerca e font approvati; controlli e risultati hanno sfondo
bianco. Non installa il service worker del sito e dichiara `noindex,nofollow`.

Tema e indicatore provengono dal manifest derivato dal catalogo canonico. Solo
dopo la scelta dell’indicatore viene caricato il suo dettaglio; le viste e le
operazioni provengono dalle dichiarazioni A6 e dai riferimenti agli shard
effettivi. Non esiste un repertorio di domande o un inventario manuale parallelo.
I metadati di presentazione derivano dal medesimo catalogo, con SHA riconciliato;
non autorizzano operazioni né contengono copie di osservazioni numeriche.

Il filtro cerca soltanto fra le viste dichiarate dell’indicatore selezionato.
Il confronto usa esattamente i sette Comuni; lettura e serie usano un Comune.
Non sono selezionabili anni arbitrari o sottoinsiemi non materializzati. Il
riferimento omesso resta quello nativo, con periodo esposto per ogni osservazione.
Il ranking è consultabile soltanto se il pacchetto include il profilo opzionale:
posizioni e pari merito provengono dal risultato A6, senza ordinamento numerico
ricostruito dal browser. Nessun cambiamento dei tre profili predefiniti.

Un’operazione dichiarata ma senza shard è disabilitata e descritta come non
ancora consultabile nel trasporto. Questo non significa dato assente o divieto
metodologico. Un rifiuto originale resta un rifiuto. La copertura incompleta
richiede consenso prima di mostrare anche osservazioni conservate in un rifiuto;
accettare non aggiunge `allowPartial` alla richiesta né promuove il risultato.
Una modifica di tema, indicatore, filtro, vista, operazione o Comune revoca
risultati e consenso. Risposte tardive di selezioni precedenti vengono ignorate.

La tabella conserva periodi, valori, categorie, località GAIA, unità e link fonte;
non trasforma n.d. in zero. Le categorie non diventano quantità. Definizioni,
popolazioni, basi temporali, metodi e avvertenze originali sono consultabili nei
dettagli; il payload intero rimane integro nel pannello di verifica chiuso.
La traduzione generale dei testi metodologici originali resta da sviluppare
prima di una resa pubblica completa. Nessun giudizio amministrativo automatico.

Grafici soltanto per osservazioni numeriche non negative, complete e omogenee
nella stessa vista, con periodo comune oppure stesso Comune. Nessun grafico dei
codici categoriali, dei lookup GAIA o dei valori conservati nei rifiuti; nessuna
interpolazione. Le scale servono alla resa visiva, non producono nuovi risultati.
Tabella e grafico hanno pagine di massimo venti osservazioni, senza troncamento
del payload o carrellate illimitate. Periodi disomogenei restano leggibili nelle
righe originali, senza dichiarazioni di continuità.

## Artefatto e guasti

```bash
python scripts/build_a7_explorer_preview.py --dist dist \
  --runtime /tmp/a7-runtime --output-dir /tmp/a7-explorer-site
python -m http.server 8765 --directory /tmp/a7-explorer-site
```

Aprire `http://localhost:8765/chiedi/`. Runtime e catalogo devono corrispondere;
il confezionatore originale verifica l’intero grafo e tutti i produttori. Un
runtime parziale conserva `explicit_subset`, dichiarato anche dall’interfaccia.
L’output deve essere nuovo. Pagina, moduli di presentazione e pacchetto ancorato
sono preparati insieme in staging, poi finalizzati con una rinomina. Il percorso
del grafo deriva dagli hash dei suoi file. La pagina incorpora direttamente il
modulo della medesima release; nessun descrittore scaricato decide l’ancora fidata.

Import mancanti, manifest, dettagli o shard mancanti, corrotti o incompatibili
bloccano la consultazione: nessun dato sostitutivo. La selezione fallita perde
risultati e consenso. «Riprova» apre una nuova istanza della stessa release;
nessun servizio o aggiornamento automatico del riferimento. Le richieste restano
locali e non sono memorizzate. I link delle fonti si aprono soltanto su azione.

Questo dimostra una preview atomica locale. L’integrazione nel builder ordinario,
nell’unico artifact Pages e nel controllo live resta un incremento successivo,
dopo revisione visiva. Non è una pubblicazione né una dichiarazione di accesso
universale alle dimensioni A3.

## Gate e limiti

Il gate di trasporto esistente esegue anche `test_a7_explorer_preview.py` sul
proprio campione derivato dalle firme degli adapter, senza nuovi workflow.
Controlli nativi desktop/mobile: richieste esatte e risposte identiche al motore,
consenso e annullamento, categorie, filtro vuoto, caricamento selettivo, guasti
di manifest/blocchi con recupero della stessa release, revoca delle risposte
tardive, assenza di storage e richieste esterne, controlli bianchi e overflow.
Quick e Full locali ordinari e CI Quick→Full/A3 restano obbligatori sul nuovo
candidato. Le verifiche della preview non sostituiscono i 3.727 casi numerici A6.

La preview completa può riusare il runtime attestato solo dopo riconciliazione
degli input e verifica attuale dell’intero pacchetto. Nessuna nuova certificazione
numerica o del CDN è implicita. Browser desktop a 390 px diverso da telefono reale;
localhost diverso da rete mobile. Dossier, Radar, associazioni, ulteriori
aggregazioni, export generale e linguaggio naturale restano distinti.
