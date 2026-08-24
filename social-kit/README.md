# Social Kit — Osservatorio Versilia

Un sistema editoriale replicabile, non una raccolta di grafiche indipendenti.

## Metodo

Il budget editoriale prevede normalmente **massimo due uscite a settimana**:

- **martedì:** primo slot;
- **venerdì:** secondo slot.

In assenza di ricorrenze o blackout entrambi gli slot sono ordinari e usano temi diversi. La rotazione assegna un tema a ogni singolo slot di calendario; se una ricorrenza sostituisce uno slot, il tema ordinario previsto per quello slot non viene recuperato automaticamente.

Ogni contenuto usa un carosello di quattro immagini PNG 1080×1350, riutilizzabile senza varianti su Facebook, Instagram, LinkedIn e X. Logo, fondo, margini, tipografia, gerarchie e fonti restano coerenti; il colore di accento segue il tema canonico del sito.

La descrizione completa del flusso è in `METHOD.md`.

## Calendario e ricorrenze

Il tetto resta di **due post a settimana**. Le giornate nazionali e internazionali realmente pertinenti ai dati dell’Osservatorio **sostituiscono** uno degli slot ordinari invece di sommarsi automaticamente.

- `config/editorial-cadence.json` definisce budget, slot, blackout e comportamento delle ricorrenze;
- `config/editorial-observances-2026-2027.json` contiene date, priorità, tema, dati suggeriti, limiti e fonte ufficiale delle ricorrenze dal 1 settembre 2026 al 31 agosto 2027;
- `config/editorial-rotation.json` definisce la rotazione dei temi e gli slot martedì/venerdì;
- `EDITORIAL_CALENDAR_2026_2027.md` contiene il calendario leggibile e il piano operativo fino al 31 dicembre 2026.

Le ricorrenze `anchor` entrano nel piano salvo indisponibilità o inadeguatezza del dato; le `conditional` diventano un post solo dopo decisione editoriale esplicita e se esiste un dato realmente pertinente. Non si forza un contenuto per il solo fatto che esista una “giornata mondiale”.

## Piano esecutivo settimanale

Il planner combina rotazione ordinaria, ricorrenze e blackout, rispettando il budget massimo di due contenuti:

```bash
python3 scripts/plan_social_week.py --date 2026-11-09
```

Per promuovere esplicitamente una ricorrenza `conditional`:

```bash
python3 scripts/plan_social_week.py \
  --date 2026-12-07 \
  --conditional-id mountain-2026
```

Gli output vengono scritti in `social-kit/dist/editorial-plan/week.md` e `week.json`.

Il workflow GitHub **Piano editoriale social settimanale** rende il calendario operativo:

- ogni **venerdì** pianifica automaticamente la settimana successiva, prima della preparazione del kit nel weekend;
- mantiene un budget massimo di due uscite;
- applica automaticamente le ricorrenze `anchor` sostituendo lo slot ordinario più vicino;
- segnala le `conditional` senza inserirle automaticamente;
- applica i blackout editoriali registrati;
- crea o aggiorna un'issue GitHub `Piano social · settimana YYYY-MM-DD` con piano e checklist;
- carica anche il piano come artifact del workflow;
- non pubblica mai automaticamente sui social.

Il workflow può essere eseguito anche manualmente indicando una data e, se necessario, l'ID di una ricorrenza `conditional` da promuovere.

Per validare struttura, fonti, rotazione, budget e scenari noti:

```bash
python3 scripts/test_social_calendar.py
```

## Struttura del carosello

Per ogni uscita il pacchetto editoriale prevede quattro immagini 1080×1350:

1. valore attuale o quadro iniziale;
2. andamento storico;
3. variazione territoriale o confronto temporale metodologicamente corretto;
4. domanda aperta, invito a commentare indicando il Comune e invito a seguire Osservatorio Versilia.

A corredo vengono preparati:

- copy distinti per Facebook, Instagram, LinkedIn e X;
- testo alternativo completo;
- provenienza dei dati;
- URL della pagina pertinente;
- hashtag sobri.

Non sono previsti PDF, storie o formati grafici aggiuntivi nel pacchetto editoriale standard.
