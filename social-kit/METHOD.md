# Metodo editoriale social

## La settimana tipo

Ogni settimana affronta **un solo tema attraverso un solo indicatore**.

| Giorno | Rubrica | Funzione |
|---|---|---|
| Martedì | Il dato | Confronta i sette Comuni, sempre in ordine alfabetico e con barre da zero. |
| Venerdì | Come leggerlo | Spiega definizione, metodo, limiti ed eventuale benchmark omogeneo. |

Il secondo post non introduce un argomento nuovo: completa il primo. In questo modo il pubblico riconosce una sequenza e l’Osservatorio costruisce continuità invece di pubblicare schede isolate.

## Cosa rimane sempre uguale

- formato e griglia;
- posizione e dimensione del logo;
- fondo, motivo grafico e margini;
- posizione di tema, titolo, contenuto, domanda e fonte;
- famiglia tipografica e gerarchie;
- ordine alfabetico dei Comuni;
- struttura delle didascalie;
- collocazione di anno, fonte e dominio.

Il tema modifica soltanto il colore di accento. Nessun template può spostare il logo o inventare un nuovo sfondo.

## Input minimo

Per produrre una settimana servono:

1. tema;
2. chiave dell’indicatore presente in `data/site-data.json`;
3. identificativo della settimana;
4. due domande approvate, oppure quelle predefinite nella banca editoriale;
5. scelta esplicita dell’eventuale misura normalizzata.

## Output automatico

Per ciascuno dei due post vengono prodotti:

- feed 1080×1350 in SVG e PNG;
- storia 1080×1920 in SVG e PNG;
- testo per Facebook, Instagram, LinkedIn e X;
- testo alternativo;
- file di provenienza con versione dati, valori, fonte e URL;
- anteprima nella galleria mensile.

## Comando

Il calendario configurato si genera con:

```bash
python3 scripts/generate_social_kit.py
```

Una nuova settimana si può provare senza modificare il calendario:

```bash
python3 scripts/generate_social_kit.py \
  --theme economia \
  --metric localUnits \
  --week-id prova-economia \
  --normalized
```

Le domande vengono prese dalla banca del tema. Possono essere sostituite con `--data-question` e `--context-question`.

## Revisione umana

Il generatore impedisce errori strutturali, non sostituisce la responsabilità editoriale. Prima della pubblicazione si controllano:

- correttezza della domanda rispetto all’indicatore;
- eventuali limiti non rappresentabili nella card;
- leggibilità reale su smartphone;
- coerenza tra grafica, didascalia e pagina del sito;
- opportunità della pubblicazione nel contesto del momento.

