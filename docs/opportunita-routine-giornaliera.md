# Radar Opportunità · routine giornaliera

## Frequenza

Il workflow `Radar Opportunità · refresh giornaliero` viene eseguito ogni giorno alle **06:15 UTC** e può essere avviato anche manualmente.

## Regola di pubblicazione

La scansione è automatica, la pubblicazione non è cieca. Lo snapshot giornaliero può sostituire quello pubblico soltanto se:

- non esistono `continuityHold`;
- non esistono opportunità verificate finite in `coverageHold`;
- il backtest del classificatore è verde;
- l'audit di copertura è verde;
- le sentinelle correnti Sport/LIFE risultano risolte;
- la pagina pubblica viene materializzata e supera il collaudo browser desktop, laptop e mobile.

I canali di puro discovery non possono pubblicare da soli una scheda: un candidato deve essere ricondotto a una fonte primaria e a un ruolo comunale documentato.

## Novità

Ogni opportunità pubblicabile riceve una data `first_seen_at` al primo ingresso nel Radar. Le schede rilevate da meno di **7 giorni** sono marcate `is_new=true` e mostrano il badge **Nuova**. Alla scadenza della finestra il badge scompare automaticamente, senza alterare lo stato del bando.

Le opportunità già presenti prima dell'introduzione del `first_seen_at` non vengono retroattivamente etichettate come nuove.

## Persistenza e deploy

Il workflow salva lo snapshot verificato in `data/opportunity-daily-public.json`. Se il file cambia, effettua un commit su `main` e avvia esplicitamente il workflow Pages: i push effettuati dal `GITHUB_TOKEN` non vengono usati come unico meccanismo di attivazione del deploy.

## Copertura v0.4.4

La v0.4.4 estende in particolare:

- **PCM · Dipartimento per lo Sport**, includendo il portale bandi generale e gli eventi sportivi nazionali/internazionali;
- **CINEA · LIFE**, con discovery sulle call 2026 e verifica topic-by-topic. HEATCOOLPLAN, PDA, ENERCOM ed EMPOWER sono qualificati per la pubblicazione condizionata; ENERPOV resta in discovery finché il ruolo comunale non è qualificato con sufficiente evidenza.
