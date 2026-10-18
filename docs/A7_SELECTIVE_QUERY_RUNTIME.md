# A7 — trasporto statico selettivo delle risposte

Prototipo tecnico isolato, senza integrazione nella build pubblica o nuova UI.
Estende il lavoro della #448; A6 resta DONE, A7 IN_PROGRESS. Il prossimo esploratore
deve interrogare capacità derivate dal catalogo, senza risposte scritte a mano e
senza un secondo motore numerico JavaScript.

## Decisione e confine

Per questa prova il Python originale esegue le richieste durante la build.
Il browser carica soltanto i blocchi necessari alla selezione e restituisce le
risposte originali, inclusi precisione, osservazioni escluse, motivi di rifiuto,
fonti, periodi, universi, componenti, puntatori e hash. Non ricalcola numeri,
non aggiunge associazioni e non genera spiegazioni amministrative.
L'unica normalizzazione riusa quella approvata nei dossier: il percorso locale
del catalogo, provato dal suo hash, diventa `sha256:<hash>`. Valori e tutti i
puntatori/metadati delle fonti restano intatti. Due build da cataloghi byte-identici
collocati in directory diverse devono produrre gli stessi artefatti.

Il lettore può comporre fino a 32 richieste indipendenti in un piano della #448.
Una composizione non autorizza correlazioni o aggregazioni fra i risultati.
Non esiste un catalogo canonico parallelo: dichiarazioni e dimensioni provengono
dal workbench, che le deriva dall'Effective Public Catalog e dagli adapter A6.
I file generati sono artefatti derivati, non nuovi input editoriali.

L'involucro iniziale comprende, dove dichiarati:

| Profilo | Richiesta precalcolata | Confine |
| --- | --- | --- |
| Corrente | `observe` o `lookup`, ciascuno dei sette Comuni | Riferimento predefinito nativo, non promessa dell'ultimo anno |
| Confronto | `compare` sui sette Comuni | Nessuna media/aggregazione Versilia implicita; categorie conservate |
| Storico | `series`, ciascuno dei sette Comuni | Solo serie già ammesse dall'adapter; periodi e discontinuità originali |

Operazioni ulteriori restano nelle dichiarazioni A6, ma non vengono falsamente
presentate come già materializzate. Periodo esplicito, sottoinsieme di Comuni,
benchmark, rango, aggregati, correlazioni e consenso `allowPartial` non vengono
riscritti per farli coincidere con una risposta presente. L'esito
`not_materialized/request_outside_static_envelope` è un limite di questo
trasporto, distinto da `not_computable` del motore e dall'assenza del dato.
Il prototipo non dimostra ancora interrogabilità universale di tutti i campi A3.

## Protocollo e integrità

`release.json` contiene versione, hash di catalogo/motore/workbench/builder/lettore,
Comuni, riepiloghi degli indicatori e riferimenti ai dettagli per indicatore.
Ogni dettaglio contiene le dichiarazioni complete e i riferimenti per vista e
profilo. I blocchi gzip hanno nomi derivati dal loro SHA256 e riferimenti con
dimensione/hash sia compressi sia non compressi. Non si scaricano tutti i blocchi
per iniziare la consultazione.

L'integrazione futura deve incorporare l'hash atteso di `release.json` nella
release del sito. Leggere un hash dal medesimo payload non crea una catena di
fiducia: `openRuntime` riceve l'ancora separatamente e verifica il testo prima
di accettarlo. Il caricamento dei blocchi è esclusivamente dalla stessa origine,
con redirect rifiutati e nomi content-addressed; nessun servizio esterno.
Il lettore verifica i byte prima e dopo decompressione e non riusa cache di altre
istanze/release. Limiti: manifest 2 MiB, singolo blocco 8 MiB compresso e 16 MiB
non compresso; cache al massimo otto blocchi e 16 MiB di byte JSON non compressi.
Questi sono limiti di trasporto, non una misura della memoria heap JavaScript.

Il piano intero è validato prima dei fetch. Risposte restituite come copie;
modificare una risposta ricevuta non altera la cache. La copertura parziale
richiede conferma prima di restituire anche le osservazioni numeriche conservate
in un rifiuto; la conferma non trasforma quel rifiuto in calcolo. Errori di rete,
integrità o versione non attivano fallback a vecchi dati o risultati fittizi.

## Riproduzione e perimetro delle prove

```bash
python scripts/build_a7_query_runtime.py --catalog dist/data/site-data.json \
  --output-dir /tmp/a7-runtime-release
python scripts/test_a7_query_runtime.py --catalog dist/data/site-data.json \
  --output /tmp/a7-runtime-transport.json
```

L'output deve essere nuovo/vuoto, per evitare mescolanza di release. Senza filtri
il builder percorre tutte le viste dichiarate. `--metric` e
`--max-views-per-metric` permettono misure circoscritte, marcate `explicit_subset`.
`measurement.json` contiene richieste, stati, byte, massimi e hash della release:
è deterministico come tutti gli altri file generati. Il tempo di esecuzione
è restituito soltanto come diagnostica al chiamante e nello stdout della CLI,
fuori dagli artefatti della release. Non certifica autonomamente la correttezza
numerica della fonte.

Il gate generale sceglie un carrier per ciascuna firma delle operazioni dichiarate,
aggiunge popolazione, classificazioni e Atlante come confini avversari e verifica
le prime due viste per carrier. È un test rappresentativo del trasporto, non
esaustivo dei dati: confronto dell'insieme e dei byte di tutti i file delle due
build (compreso `measurement.json`), parità Python di tutte le risposte di
quel campione, caricamento browser per carrier/profilo a 1440 e 390 px,
assenza di caricamento anticipato, cache/isolamento, rifiuti, consenso, input
alterati, rilascio/blocco corrotti, URL esterni e richieste non materializzate.
La suite indipendente di 3.727 casi A6 continua a verificare i risultati numerici.
Un viewport mobile non è un telefono reale; tempi localhost non sono latenze WAN.

## Prima del rollout pubblico

Occorrono ancora: misura completa di byte/tempi degli storici e costo della build;
audit A3→A6→A7 dei campi effettivamente interrogabili; estensione motivata
dell'involucro alle altre operazioni; gestione degli anni e delle selezioni
territoriali senza ricostruzioni JavaScript; contratto di pubblicazione atomica
e ancora d'integrità nella pagina; selettori e grafici pubblici con verifica
visiva desktop/mobile; CSV generale e collegamento ai dossier.
Il browser non deve vedere nomi tecnici, JSON o link GitHub come contenuto principale.

Runtime browser completo e servizio esterno restano alternative non implementate.
Il trasporto selettivo evita la duplicazione del motore e mantiene Pages, ma ha
un costo di preparazione e una copertura finita da misurare. Questa prova consente
di decidere sul rollout con evidenze; non dichiara conclusa A7 e non cambia le
interfacce approvate.
