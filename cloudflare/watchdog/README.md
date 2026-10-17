# Cloudflare Watchdog

Cloudflare Workers viene usato come scheduler/watchdog esterno per rendere resilienti le automazioni temporali di Osservatorio Versilia senza spostare fuori da GitHub la logica applicativa.

## Pianificazione

Il Worker dispone di un Cron Trigger Cloudflare:

```text
30 9 * * *
```

Cloudflare esegue i Cron Trigger in UTC. Il controllo parte quindi alle **09:30 UTC** ogni giorno (11:30 in Italia con ora legale, 10:30 con ora solare), oltre tre ore dopo il cron GitHub del Radar (`06:15 UTC`).

Il cron GitHub resta attivo come scheduler primario. Cloudflare è una rete di sicurezza indipendente.

## Cosa controlla a ogni esecuzione

### Radar Opportunità

- legge `data/opportunity-daily-public.json` da `main`;
- se `referenceDate` coincide con la data UTC corrente, non fa nulla;
- se lo snapshot è vecchio ma esiste già una run odierna in corso, non fa nulla;
- se lo snapshot è vecchio e non esiste una run in corso, invoca `workflow_dispatch` di `opportunity-radar-daily.yml`.

### Controllo mensile dati

- prima del giorno 5 del mese non fa nulla;
- dal giorno 5 in poi cerca una run `schedule` o `workflow_dispatch` completata con successo nel mese corrente;
- se una run è già in corso, non avvia duplicati;
- se manca un controllo mensile riuscito, invoca `workflow_dispatch` di `monthly-data-refresh.yml`;
- poiché il watchdog gira ogni giorno, un controllo mensile mancato il giorno 5 viene ritentato automaticamente nei giorni successivi finché non risulta una run riuscita.

## Endpoint manuali

### `GET /health`

Pubblico. Conferma che il codice dispone dell'handler schedulato.

### `GET /check`

Parametri:

- `target=daily` — controlla solo il Radar Opportunità;
- `target=monthly` — controlla solo il controllo mensile;
- `target=all` — controlla entrambi; è il default;
- senza `dispatch=1` — dry-run pubblico e di sola lettura;
- con `dispatch=1` — abilita il dispatch e richiede `Authorization: Bearer <WATCHDOG_KEY>`.

Esempio dry-run:

```bash
curl "https://<worker>.workers.dev/check?target=daily"
```

Esempio manuale con dispatch:

```bash
curl -H "Authorization: Bearer $WATCHDOG_KEY" \
  "https://<worker>.workers.dev/check?target=daily&dispatch=1"
```

Il Cron Trigger interno non usa `WATCHDOG_KEY`: viene invocato direttamente dalla piattaforma Cloudflare e usa il secret `GITHUB_TOKEN` per interagire con GitHub.

## Secret Cloudflare

### `WATCHDOG_KEY`

Chiave casuale lunga usata solo per autorizzare richieste HTTP manuali con `dispatch=1`.

### `GITHUB_TOKEN`

Fine-grained personal access token GitHub limitato a:

- repository: `EmAnzi3/osservatorio-versilia`;
- repository permission: **Actions — Read and write**.

Nessun secret deve essere versionato nel repository.

## Variabili non sensibili

- `GITHUB_OWNER=EmAnzi3`
- `GITHUB_REPO=osservatorio-versilia`
- `GITHUB_REF=main`

## Stati Daily

- `current` — snapshot del giorno già presente;
- `stale` — snapshot vecchio; in dry-run segnala che farebbe dispatch;
- `running` — esiste già una run odierna non completata;
- `dispatched` — è stato richiesto un nuovo `workflow_dispatch`;
- `error` — impossibile leggere lo snapshot.

## Stati Monthly

- `not_due` — prima del giorno 5;
- `completed` — controllo mensile riuscito già presente;
- `running` — controllo mensile già in corso;
- `missing` — dal giorno 5 non esiste ancora un controllo riuscito;
- `dispatched` — è stato richiesto il controllo mensile.

## Sicurezza e responsabilità

Cloudflare non modifica direttamente dati, Issue, PR o GitHub Pages. Può soltanto invocare due workflow GitHub esistenti. I workflow continuano a eseguire i propri test, controlli e regole prima di qualsiasi commit, PR, Issue o pubblicazione.
