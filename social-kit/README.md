# Social Kit — Osservatorio Versilia

Sistema replicabile per produrre due caroselli social alla settimana, sempre in bozza.

## Struttura

Ogni carosello contiene quattro immagini PNG 1080×1350:

1. dato attuale;
2. andamento storico;
3. confronto temporale tra i sette Comuni;
4. domande e invito a commentare e seguire la pagina.

Le stesse immagini vengono usate su Facebook, Instagram, LinkedIn e X. Non vengono generati PDF o storie.

La griglia è definita da `config/design-system.json`; i colori canonici dei temi da `config/themes.json`; le uscite da `config/editorial-calendar.json`; le ricorrenze ammissibili da `config/recurrences.json`.

## Preparazione programmata

Il workflow `Genera Social Kit` controlla ogni mattina il calendario editoriale usando il fuso `Europe/Rome`.

Se per la data corrente è prevista un'uscita, genera automaticamente il relativo pacchetto di pubblicazione in **bozza** e lo rende disponibile come artifact GitHub Actions. Il pacchetto comprende:

- 4 PNG 1080×1350;
- SVG sorgenti;
- copy distinti per Facebook, Instagram, LinkedIn e X;
- testi ALT;
- manifest e provenienza dei dati.

Il sistema **non pubblica, non programma e non invia contenuti ai social network**. La pubblicazione resta sempre manuale.

Nei giorni senza un'uscita prevista il workflow non genera alcun pacchetto social.

## Uso

```bash
python3 -m pip install -r social-kit/requirements.txt
python3 scripts/generate_social_kit.py
python3 scripts/test_social_kit.py
```

L’anteprima è `social-kit/dist/index.html`. Il pacchetto contiene solo bozze e non esegue alcuna pubblicazione.

Per il contenuto clima:

```bash
python3 scripts/generate_social_kit.py \
  --post-id 2026-08-14-clima-temperature-massime
```

Per individuare l'uscita prevista in una data:

```bash
python3 scripts/resolve_social_post.py --date 2026-08-14
```

Per controllare una settimana e le eventuali ricorrenze ufficiali:

```bash
python3 scripts/plan_social_week.py --date 2026-11-09
```

## Dove intervenire

- nuova uscita: aggiungere una voce a `config/editorial-calendar.json`;
- nuova ricorrenza: aggiungerla a `config/recurrences.json` con URL ufficiale e indicatori candidati;
- nuovo indicatore: approvarlo in `config/social-ready.json` dopo aver verificato fonte, copertura e comparabilità;
- modifica grafica strutturale: aggiornare il design system e i test, mai una singola tavola.

La procedura completa e i controlli editoriali sono in `METHOD.md` e `EDITORIAL_POLICY.md`.
