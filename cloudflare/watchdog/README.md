# Cloudflare Watchdog · PoC manuale

Questo PoC usa Cloudflare Workers come watchdog esterno per le automazioni temporali di Osservatorio Versilia.

In questa fase **non esiste alcun Cron Trigger Cloudflare**: il Worker espone soltanto endpoint manuali per verificare il comportamento prima di automatizzarlo.

## Obiettivi

- verificare se lo snapshot giornaliero del Radar Opportunità è aggiornato alla data UTC corrente;
- se lo snapshot è vecchio, poter avviare `opportunity-radar-daily.yml` tramite `workflow_dispatch`;
- dal giorno 5 del mese, verificare se `monthly-data-refresh.yml` è già stato eseguito nel mese corrente;
- evitare un nuovo dispatch se il workflow pertinente risulta già in esecuzione;
- non conservare token o chiavi nel repository.

## Endpoint

### `GET /health`

Pubblico. Restituisce soltanto lo stato del Worker e conferma che il PoC è in modalità manuale senza cron.

### `GET /check`

Protetto da header:

```text
Authorization: Bearer <WATCHDOG_KEY>
```

Parametri:

- `target=daily` — controlla solo il Radar Opportunità;
- `target=monthly` — controlla solo il controllo mensile;
- `target=all` — controlla entrambi; è il default;
- senza `dispatch=1` — dry-run, non avvia nulla;
- con `dispatch=1` — avvia il workflow soltanto se il controllo stabilisce che è necessario.

Esempio dry-run:

```bash
curl -H "Authorization: Bearer $WATCHDOG_KEY" \
  "https://<worker>.workers.dev/check?target=daily"
```

Esempio con dispatch abilitato:

```bash
curl -H "Authorization: Bearer $WATCHDOG_KEY" \
  "https://<worker>.workers.dev/check?target=daily&dispatch=1"
```

## Secret Cloudflare richiesti

### `WATCHDOG_KEY`

Chiave casuale lunga usata esclusivamente per proteggere `/check`.

### `GITHUB_TOKEN`

Fine-grained personal access token GitHub limitato a:

- repository: `EmAnzi3/osservatorio-versilia`;
- repository permission: **Actions — Read and write**.

Il token serve per il `workflow_dispatch`. Il controllo dello snapshot pubblico può funzionare anche senza token, ma il dispatch no.

## Variabili non sensibili

Sono già definite in `wrangler.jsonc`:

- `GITHUB_OWNER=EmAnzi3`
- `GITHUB_REPO=osservatorio-versilia`
- `GITHUB_REF=main`

## Sequenza di collaudo

1. Creare il Worker `osservatorio-versilia-watchdog` in Cloudflare.
2. Inserire `worker.js` come codice del Worker.
3. Configurare i secret `WATCHDOG_KEY` e `GITHUB_TOKEN`.
4. Aprire `/health` e verificare `cronEnabled: false`.
5. Chiamare `/check?target=daily` senza `dispatch=1` e verificare che il risultato sia `current` oppure `stale`.
6. Se il risultato è `stale`, ripetere con `dispatch=1`.
7. Verificare in GitHub Actions che sia comparsa una nuova esecuzione `workflow_dispatch` di `Radar Opportunità · refresh giornaliero`.
8. Attendere il completamento e ripetere il dry-run: il risultato deve diventare `current`.
9. Solo dopo questo collaudo aggiungere il Cron Trigger Cloudflare e testare il controllo mensile.

## Stati attesi

### Daily

- `current` — snapshot di oggi già presente;
- `stale` — snapshot vecchio, il dry-run segnala che farebbe dispatch;
- `running` — esiste già un run odierno non completato;
- `dispatched` — il Worker ha richiesto un nuovo `workflow_dispatch`;
- `error` — impossibile leggere lo snapshot.

### Monthly

- `not_due` — siamo prima del giorno 5;
- `completed` — un controllo mensile `schedule` o `workflow_dispatch` è già stato completato nel mese;
- `running` — il controllo mensile è già in corso;
- `missing` — dal giorno 5 in poi non risulta alcuna esecuzione mensile completata;
- `dispatched` — il Worker ha richiesto il controllo mensile.

## Sicurezza

Il Worker non modifica direttamente dati, issue, PR o pagine pubbliche. Può soltanto avviare due workflow GitHub già esistenti, e soltanto quando viene chiamato con la chiave `WATCHDOG_KEY` e con `dispatch=1`.

Il repository non deve mai contenere `WATCHDOG_KEY` o `GITHUB_TOKEN`.
