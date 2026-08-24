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

- ogni **venerdì alle 06:15 UTC** pianifica automaticamente la settimana successiva;
- mantiene un budget massimo di due uscite;
- applica automaticamente le ricorrenze `anchor` sostituendo lo slot ordinario più vicino;
- segnala le `conditional` senza inserirle automaticamente;
- applica i blackout editoriali registrati;
- crea o aggiorna un'issue GitHub `Piano social · settimana YYYY-MM-DD` con piano e checklist;
- carica anche il piano come artifact del workflow;
- non pubblica mai automaticamente sui social.

## Consegna del materiale

Il workflow **Genera Social Kit settimanale** completa il piano:

- ogni **sabato alle 06:30 UTC** genera il pacchetto della settimana successiva;
- quando cambiano dati o componenti del Social Kit su `main`, rigenera anche il pacchetto della settimana corrente;
- legge direttamente `week.json`: date, temi e indicatori non sono duplicati in un secondo calendario;
- crea l'artifact `social-kit-YYYY-MM-DD`, conservato per **45 giorni**;
- aggiorna la stessa issue `Piano social · settimana YYYY-MM-DD` con stato del pacchetto e collegamento al run GitHub Actions;
- se una ricorrenza non ha una metrica esatta nel dataset, la segnala come intervento manuale invece di forzare un indicatore simile.

L'issue settimanale è quindi il **punto unico di accesso**: aprire la sezione **Materiale della settimana**, seguire il link al run e scaricare l'artifact `social-kit-YYYY-MM-DD` dalla sezione **Artifacts**.

Dentro lo ZIP, per ogni uscita, sono presenti:

- `cards/`: quattro PNG 1080×1350 e i corrispondenti SVG;
- `testi/`: copy `facebook.txt`, `instagram.txt`, `linkedin.txt`, `x.txt` e versione master;
- `alt/`: testo alternativo di ciascuna tavola;
- `provenienza.json`: versione dati, valori, fonte, metodo e URL;
- `manifest.json`: struttura del singolo carosello.

A livello di pacchetto sono inoltre presenti `README.md`, `week.json`, `manifest.json` e una galleria `index.html` per la revisione.

Per generare manualmente il pacchetto da un piano già costruito:

```bash
python3 scripts/generate_weekly_social_kit.py --plan social-kit/dist/editorial-plan/week.json
python3 scripts/test_weekly_social_kit.py
```

Per validare struttura, fonti, rotazione, budget e scenari noti del planner:

```bash
python3 scripts/test_social_calendar.py
```

## Struttura del carosello

Per ogni uscita il pacchetto editoriale prevede quattro immagini 1080×1350:

1. valore attuale o quadro iniziale;
2. andamento storico, quando disponibile, oppure definizione del dato;
3. variazione territoriale/temporale, quando disponibile, oppure limiti di lettura;
4. domanda aperta, invito a commentare indicando il Comune e invito a seguire Osservatorio Versilia.

A corredo vengono preparati:

- copy distinti per Facebook, Instagram, LinkedIn e X;
- testo alternativo completo;
- provenienza dei dati;
- URL della pagina pertinente;
- hashtag sobri.

Non sono previsti PDF, storie o formati grafici aggiuntivi nel pacchetto editoriale standard.
