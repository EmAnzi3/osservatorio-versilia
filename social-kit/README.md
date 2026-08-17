# Social Kit — Osservatorio Versilia

Un sistema editoriale replicabile, non una raccolta di grafiche indipendenti.

## Metodo

Ogni settimana usa un solo indicatore e produce due post coordinati:

- **martedì — Il dato:** confronto alfabetico dei sette Comuni;
- **venerdì — Come leggerlo:** definizione, metodo, limiti ed eventuale benchmark omogeneo.

I due post usano la stessa griglia. Logo, fondo, margini, tipografia, blocco domanda e fonti sono bloccati dal file `config/design-system.json`. Il tema modifica soltanto il colore di accento.

La descrizione completa del flusso è in `METHOD.md`.

## Calendario e ricorrenze

Il ritmo ordinario resta di **due post a settimana**, ma il piano tiene conto delle giornate nazionali e internazionali realmente pertinenti ai dati dell’Osservatorio.

- `config/editorial-calendar.json` contiene la cadenza ordinaria e collega il piano annuale;
- `config/editorial-observances-2026-2027.json` contiene date, priorità, tema, dati suggeriti, limiti e fonte ufficiale delle ricorrenze dal 1 settembre 2026 al 31 agosto 2027;
- `EDITORIAL_CALENDAR_2026_2027.md` è la versione leggibile del calendario.

Le ricorrenze `anchor` sostituiscono uno dei due slot ordinari; le `conditional` diventano un post solo se esiste un dato realmente pertinente. Non si forza un contenuto per il solo fatto che esista una “giornata mondiale”. Le regole complete sono in `EDITORIAL_POLICY.md`.

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

