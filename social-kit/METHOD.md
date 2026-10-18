# Metodo editoriale social

## La settimana tipo

Il budget editoriale è di **massimo due contenuti a settimana**.

| Giorno | Funzione | Regola |
|---|---|---|
| Martedì | Primo slot editoriale | Tema ordinario assegnato dalla rotazione, salvo ricorrenza che sostituisca lo slot. |
| Venerdì | Secondo slot editoriale | Tema ordinario successivo, salvo ricorrenza o blackout. |

In una settimana senza ricorrenze o blackout i due contenuti sono autonomi e appartengono a temi diversi. Non esiste una settimana monotematica: ogni uscita deve essere completa e comprensibile da sola.

Le ricorrenze nazionali, internazionali o territoriali realmente pertinenti **non sono additive**. Una `anchor` occupa uno dei due posti e sostituisce lo slot ordinario più vicino alla propria data editoriale. Una `conditional` fa lo stesso soltanto dopo promozione esplicita. Lo slot sostituito non viene recuperato automaticamente.

Le date di blackout editoriale non producono un post ordinario e non vengono recuperate automaticamente. Il planner non può superare due contenuti nella stessa settimana.

## Struttura di ogni contenuto

Ogni uscita usa un carosello di quattro immagini PNG 1080×1350:

1. valore attuale o quadro iniziale;
2. andamento storico dei singoli Comuni, mai aggregato della Versilia;
3. variazione territoriale o confronto temporale metodologicamente corretto, con testi e grafici in corsie non sovrapponibili;
4. domanda aperta, invito a commentare indicando il Comune e invito a seguire Osservatorio Versilia.

Il carosello è unico e viene utilizzato senza varianti su Facebook, Instagram, LinkedIn e X. Se l'indicatore principale non dispone di storico, le tavole 2 e 3 usano altri indicatori pertinenti soltanto quando la relazione è dichiarata nella configurazione editoriale e i dati hanno copertura 7/7. Servono sia una serie storica comunale sia un secondo dato di contesto; in caso contrario il pacchetto resta da gestire manualmente, senza riempitivi generici.

La relazione tecnica fra gli indicatori non entra mai nel contenuto pubblico: sono vietate formule come “dato affine”, “indicatore di supporto” o “per completare la lettura”. Card, copy e ALT parlano esclusivamente del fenomeno osservato.

Ogni valore deve essere interpretabile senza conoscere il catalogo: titolo o sottotitolo spiegano che cosa viene contato o quale universo rappresenta una percentuale. Il solo nome sintetico dell’indicatore non basta. Il copy segue una storia leggibile — dato attuale, evoluzione nel tempo, significato dell’eventuale terzo indicatore e domanda al lettore — mentre i dettagli tecnici restano nella provenienza, salvo quelli indispensabili per capire il numero.

## Cosa rimane sempre uguale

- formato 1080×1350 e griglia;
- posizione e dimensione del logo;
- fondo, motivo grafico e margini;
- posizione di tema, titolo, contenuto, domanda e fonte;
- famiglia tipografica e gerarchie;
- ordine alfabetico dei Comuni quando applicabile;
- struttura delle didascalie;
- collocazione di anno, fonte e dominio;
- nessun testo fuori dai box.

Il tema modifica gli elementi cromatici usando esclusivamente i colori canonici assegnati allo stesso tema nel sito. Nessun template può spostare il logo, inventare un nuovo sfondo o introdurre palette parallele.

## Input minimo

Per produrre un contenuto servono:

1. tema;
2. chiave dell’indicatore presente in `data/site-data.json`;
3. data prevista di pubblicazione;
4. domanda finale neutrale;
5. eventuale confronto normalizzato metodologicamente compatibile;
6. fonte e URL della pagina pertinente.

## Output

Per ciascun contenuto vengono prodotti:

- quattro PNG 1080×1350;
- un unico testo condiviso per Facebook, Instagram e LinkedIn, con icone di lettura e hashtag dei sette Comuni;
- testo per X;
- testo alternativo completo;
- provenienza con versione dati, valori, fonte e URL.

Non sono previsti PDF, storie o formati aggiuntivi nel pacchetto standard.

## Pianificazione

### Registro annuale delle pubblicazioni

`config/publication-history.json` conserva solo post effettivamente pubblicati: ID,
anno, indicatori di tutte le card, prova (permalink o conferma del proprietario),
data della conferma e data di pubblicazione se nota. Una data sconosciuta resta
null: non si ricava da un vecchio calendario. Il registro dichiara per ciascun
anno se la ricostruzione è parziale o completa; finché è parziale, il piano lo
segnala e non certifica come inediti gli argomenti assenti.

La generazione di un kit non aggiorna questo registro. Dopo la pubblicazione
manuale si registra esplicitamente il post, includendo gli indicatori secondari:

```bash
python3 scripts/plan_social_week.py --record-published ID_POST \
  --publication-year 2026 --published-on 2026-10-20 \
  --provenance PERCORSO/provenienza.json --evidence URL_POST_PUBBLICATO
```

In alternativa a `--provenance`, `--published-metric` è ripetibile; omettere
`--published-on` se la data è ignota. Conservare il registro nel repository
tramite branch/PR come gli altri file editoriali. Non inserire segreti o dati
personali. Prima dell'uscita successiva integrare le nuove conferme.

Il planner esclude gli indicatori già pubblicati nel medesimo anno, sceglie il
successivo indicatore featured del tema e rende visibili le esclusioni. Se sono
esauriti, richiede una scelta editoriale e non ripiega sul doppione. Le ricorrenze
usano soltanto candidati non ancora pubblicati; in assenza di candidati restano
da trattare manualmente. Il generatore ricontrolla il registro prima di usare
un piano salvato e prima di disegnare ogni carosello, anche per le card secondarie.
Cambiare titolo o rigenerare le immagini non azzera l'uso annuale; l'anno nuovo
riapre la disponibilità. Il registro non modifica dati o fonti dell'Osservatorio.

Il calendario settimanale si genera con:

```bash
python3 scripts/plan_social_week.py --date YYYY-MM-DD
```

La cadenza è definita in `config/editorial-cadence.json`; la rotazione dei temi in `config/editorial-rotation.json`; le ricorrenze in `config/editorial-observances-2026-2027.json`.

Il planner assegna ogni ricorrenza selezionata allo slot ordinario più vicino, mostra quale tema è stato sostituito, espone gli eventuali blackout e rifiuta piani che superano il budget settimanale.

## Revisione umana

Il sistema impedisce molti errori strutturali, non sostituisce la responsabilità editoriale. Prima della pubblicazione si controllano:

- correttezza della domanda rispetto all’indicatore;
- eventuali limiti non rappresentabili nella card;
- leggibilità reale su smartphone;
- coerenza tra grafica, didascalia e pagina del sito;
- correttezza dei colori rispetto al tema canonico;
- opportunità della pubblicazione nel contesto del momento;
- pertinenza reale delle eventuali ricorrenze speciali;
- rispetto del budget massimo di due uscite.
