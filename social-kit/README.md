# Social Kit — Osservatorio Versilia

Un sistema editoriale replicabile, non una raccolta di grafiche indipendenti.

## Metodo

Ogni settimana usa un solo indicatore e produce due post coordinati:

- **martedì — Il dato:** confronto alfabetico dei sette Comuni;
- **venerdì — Come leggerlo:** definizione, metodo, limiti ed eventuale benchmark omogeneo.

I due post usano la stessa griglia. Logo, fondo, margini, tipografia, blocco domanda e fonti sono bloccati dal file `config/design-system.json`. Il tema modifica soltanto il colore di accento.

La descrizione completa del flusso è in `METHOD.md`.

## Generare il calendario

```bash
python3 -m pip install -r social-kit/requirements.txt
python3 scripts/generate_social_kit.py
python3 scripts/test_social_kit.py
```

La galleria viene creata in `social-kit/dist/index.html`.

## Generare una nuova settimana

```bash
python3 scripts/generate_social_kit.py \
  --theme economia \
  --metric localUnits \
  --week-id economia-unita-locali \
  --normalized
```

Per vedere gli indicatori già approvati:

```bash
python3 scripts/generate_social_kit.py --list-metrics
```

Le domande predefinite arrivano da `config/question-bank.json`. Si possono sostituire con:

```bash
--data-question "Domanda del primo post" \
--context-question "Domanda del secondo post"
```

## Output

Per ogni post:

- SVG e PNG feed 1080×1350;
- SVG e PNG storia 1080×1920;
- testi per Facebook, Instagram, LinkedIn e X;
- testo alternativo;
- provenienza completa;
- inserimento nel PDF LinkedIn e nella galleria.

Il workflow GitHub **Genera Social Kit** produce lo stesso pacchetto come artefatto di revisione. Non pubblica post e non modifica il sito.

