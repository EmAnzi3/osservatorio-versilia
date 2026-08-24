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
2. andamento storico;
3. variazione territoriale o confronto temporale metodologicamente corretto;
4. domanda aperta, invito a commentare indicando il Comune e invito a seguire Osservatorio Versilia.

Il carosello è unico e viene utilizzato senza varianti su Facebook, Instagram, LinkedIn e X.

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
- testo per Facebook;
- testo per Instagram;
- testo per LinkedIn;
- testo per X;
- testo alternativo completo;
- provenienza con versione dati, valori, fonte e URL.

Non sono previsti PDF, storie o formati aggiuntivi nel pacchetto standard.

## Pianificazione

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
