# Radar Opportunità · routine giornaliera

## Frequenza

Il workflow `Radar Opportunità · refresh giornaliero` viene eseguito ogni giorno alle **06:15 UTC** e può essere avviato anche manualmente.

## Regola di pubblicazione

La scansione è automatica, la pubblicazione non è cieca. Lo snapshot giornaliero può sostituire quello pubblico soltanto se:

- non esistono `continuityHold`;
- non esistono opportunità verificate finite in `coverageHold`;
- il backtest del classificatore è verde;
- l'audit di copertura è verde;
- la completezza di Regione Toscana non presenta candidati comunali irrisolti oltre la finestra di revisione;
- le sentinelle correnti Sport/LIFE risultano risolte;
- la pagina pubblica viene materializzata e supera il collaudo browser desktop, laptop e mobile.

I canali di puro discovery non possono pubblicare da soli una scheda: un candidato deve essere ricondotto a una fonte primaria e a un ruolo comunale documentato.

## Safety net Regione Toscana

Il collector principale di Regione Toscana resta il canale che classifica e pubblica le opportunità. In aggiunta, la routine giornaliera esegue un secondo controllo sui bandi regionali recenti e aperti.

Quando la fonte primaria indica esplicitamente tra i possibili richiedenti **Enti locali o Comuni**:

- se il bando è già pubblico nel Radar, non viene riesaminato;
- se è già in review/hold/discovery, viene contabilizzato come irrisolto;
- se non compare in nessuno stato del flusso principale, viene aggiunto alla `discoveryQueue` come safety net e non viene pubblicato automaticamente;
- se resta irrisolto per oltre **7 giorni** dalla pubblicazione, genera un `coverageHold` e blocca la pubblicazione del nuovo snapshot finché non viene qualificato o escluso documentalmente.

Il controllo usa una finestra mobile di **21 giorni** sui bandi regionali recenti. Un errore transitorio del safety net viene segnalato come stato `degraded`, senza sostituire o aggirare i gate del collector principale.

## Blind test permanente

Il blind test del **25 agosto 2026**, costruito a partire da una newsletter esterna usata come set di verità indipendente, è stato incorporato nel backtest documentale. I sei casi comunali già coperti restano nella fixture e il caso `Celebrazioni storiche 2026` è stato aggiunto come regressione obbligatoria.

Il bando sulle celebrazioni è classificato come opportunità **condizionata dal tema progettuale**: non è territorialmente dedicato alla Versilia, ma gli Enti locali della Toscana possono presentare direttamente iniziative realizzate in Toscana e dedicate a una delle tre ricorrenze previste dall'avviso.

## Novità

Ogni opportunità pubblicabile riceve una data `first_seen_at` al primo ingresso nel Radar. Le schede rilevate da meno di **7 giorni** sono marcate `is_new=true` e mostrano il badge **Nuova**. Alla scadenza della finestra il badge scompare automaticamente, senza alterare lo stato del bando.

Le opportunità già presenti prima dell'introduzione del `first_seen_at` non vengono retroattivamente etichettate come nuove.

## Notifica personale dei nuovi bandi

Dopo che il nuovo snapshot è stato validato, committato su `main` e la pubblicazione Pages è stata avviata, il workflow confronta lo snapshot corrente con quello precedente.

Se esistono **nuove identità pubblicabili**, viene creata automaticamente una GitHub Issue con titolo `Nuove opportunità Radar · GG/MM/AAAA` e assegnata al proprietario del repository. La Issue riporta, per ciascuna nuova opportunità:

- titolo;
- scadenza;
- Comuni della Versilia ammissibili o condizionali;
- modalità di accesso;
- collegamento alla fonte ufficiale;
- collegamento al Radar pubblico.

Se non ci sono nuove identità non viene creata alcuna Issue. Ogni notifica contiene un fingerprint deterministico: un rerun dello stesso aggiornamento riconosce la Issue già esistente e non genera duplicati.

L'assegnazione al proprietario rende la notifica visibile nelle **GitHub Notifications**; l'invio anche via email dipende dalle impostazioni personali delle notifiche GitHub dell'account.

## Persistenza e deploy

Il workflow salva lo snapshot verificato in `data/opportunity-daily-public.json`. Il file deve avere `referenceDate` uguale alla data UTC del run; in caso contrario il workflow fallisce esplicitamente.

La build pubblica usa `opportunity-daily-public.json` quando esiste ed è almeno aggiornato quanto la baseline, non contiene hold bloccanti e conserva backtest/audit verdi. `data/opportunity-release.json` resta il fallback congelato per build senza uno snapshot giornaliero valido.

Prima del commit, il workflow ricostruisce `/opportunita/` e verifica che la data e il numero di card della pagina coincidano con lo snapshot giornaliero. Se il file cambia, effettua un commit su `main` e avvia esplicitamente il workflow Pages: i push effettuati dal `GITHUB_TOKEN` non vengono usati come unico meccanismo di attivazione del deploy.

## Copertura v0.4.4

La v0.4.4 estende in particolare:

- **PCM · Dipartimento per lo Sport**, includendo il portale bandi generale e gli eventi sportivi nazionali/internazionali;
- **CINEA · LIFE**, con discovery sulle call 2026 e verifica topic-by-topic. HEATCOOLPLAN, PDA, ENERCOM ed EMPOWER sono qualificati per la pubblicazione condizionata; ENERPOV resta in discovery finché il ruolo comunale non è qualificato con sufficiente evidenza.

L'hardening `0.4.4-h1` aggiunge il blind test esterno, la safety net Regione Toscana, la sentinella di freschezza dello snapshot, il collegamento esplicito fra snapshot giornaliero e build pubblica e la notifica GitHub Issue per le nuove identità pubblicabili.
