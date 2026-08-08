# Contribuire all’Osservatorio Versilia

Il repository pubblica dati civici: ogni modifica deve restare leggibile, verificabile e separata dalla pubblicazione.

## Flusso di lavoro

1. Parti dalla `main` aggiornata e crea un branch descrittivo (`feature/…`, `fix/…`, `data/…` o `agent/…`).
2. Mantieni nel branch un solo cambiamento logico. Evita commit temporanei (`tmp`, `noop`, `wip`) e fai squash prima della revisione finale.
3. Apri inizialmente una pull request in bozza. Il merge su `main` avviene soltanto dopo test riusciti e verifica manuale.
4. Non modificare direttamente artefatti in `dist/`: vengono rigenerati dalla build.

## Dati e fonti

Una modifica a valori, formule, copertura o metadati richiede:

- una fonte pubblica verificabile;
- lo snapshot leggibile in `data/source-snapshots/`, quando previsto;
- anno, unità, perimetro e formula dichiarati;
- aggiornamento dei test di copertura;
- nessuna stima per colmare dati ufficiali mancanti.

Le modifiche puramente grafiche non devono alterare `data/site-data.json` o le formule.

## Verifiche locali

Esegui almeno:

```bash
python scripts/build_static_brand.py
python scripts/test_static.py
python scripts/test_release_v170_compat.py
python scripts/test_mobile_interactions.py
node --check assets/app-core.js
```

Per interventi trasversali esegui l’intera suite elencata in `.github/workflows/pages.yml`.

## Pull request

Descrivi cosa cambia per l’utente, quali file di dati sono coinvolti, i test eseguiti e gli eventuali limiti. Per modifiche visive allega immagini desktop e mobile. Le pull request non pubblicano il sito; il deploy parte esclusivamente da `main` dopo il superamento dei controlli.
