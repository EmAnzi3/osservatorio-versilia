# Metodo editoriale social

## La settimana tipo

La settimana ordinaria prevede **due contenuti autonomi su due temi diversi**.

| Giorno | Funzione | Regola |
|---|---|---|
| Martedì | Primo contenuto ordinario | Tema e indicatore assegnati dalla rotazione per singola uscita. |
| Venerdì | Secondo contenuto ordinario | Tema successivo della rotazione, diverso da quello del martedì. |

Non esiste più una settimana monotematica. Ogni uscita deve essere completa e comprensibile da sola; la varietà dei temi serve a distribuire nel tempo gli 11 ambiti dell’Osservatorio.

Le ricorrenze nazionali, internazionali o territoriali realmente pertinenti sono **aggiuntive** rispetto ai due contenuti ordinari. Se cadono nello stesso giorno di martedì o venerdì, il piano segnala la collisione per valutare lo spostamento dell’ordinario a un giorno libero vicino, senza eliminarlo automaticamente.

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

## Revisione umana

Il sistema impedisce molti errori strutturali, non sostituisce la responsabilità editoriale. Prima della pubblicazione si controllano:

- correttezza della domanda rispetto all’indicatore;
- eventuali limiti non rappresentabili nella card;
- leggibilità reale su smartphone;
- coerenza tra grafica, didascalia e pagina del sito;
- correttezza dei colori rispetto al tema canonico;
- opportunità della pubblicazione nel contesto del momento;
- pertinenza reale delle eventuali ricorrenze speciali.
