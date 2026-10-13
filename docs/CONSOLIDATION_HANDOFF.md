# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente e proposta conclusiva

- Main verificata dopo merge del proprietario della #427: `cb73eadd9be1c46cc1196652d6068d41ae5d4363`, albero `ea4638204f636a520f9dae8080f926fa6c6a6185`. #423/#424/#425 preservate. Deploy `38372493679` e controllo live `38374702463` SUCCESS; catalogo pubblico 225 metriche e Atlante 20.325 riconfermati.
- **Stato effettivo A6 IN_PROGRESS, A7 NOT_STARTED.** La PR amministrativa propone DONE, efficace soltanto dopo approvazione, merge e verifica post-merge della stessa PR. Nessuna attestazione anticipata.
- A0–A5 DONE. A6.1–A6.6 tecnicamente integrate e verificate: 225/225 adapter, zero carrier scoperti; catalogo sorgente separato 166/181. Suite 3.727 PASS (2.033 consultazioni/calcoli, 1.694 rifiuti); 3.359 viste dichiarate. Copertura non autorizza tutte le operazioni.
- #425: totali territoriali nativi 2025, distinti dai 292 diretti ATECO; payload, classificazioni e storici preservati. #427: contesti/benchmark per dimensione, checker indipendente, provenienza, campioni/sensibilità e rifiuti; tutte le 35 letture e i due riepiloghi verificati e preservati.

## Evidenze integrate e candidato finale

Metodo `docs/A6_METHODOLOGICAL_REVIEW.md`; attestazione proposta e condizioni `docs/A6_CLOSURE_AUDIT.md`; report leggibili `reports/a6-methodological-review/`. Repertorio ragionato: 7 domande supportate, 9 parziali, 4 non determinabili, con fonti, richieste, limiti e dati mancanti. Abitazione/bilanci supplementari, non percorsi aggiunti alle 35 letture.

Gate #427: Quick→Full locali sequenziali PASS, CI Quick `38365187212`, Full `38369132467`, A3 `38365187081` PASS sul candidato integrato. Questi risultati non sono i gate della PR conclusiva: branch `docs/a6-final-closure`, modifica esclusivamente documentazione, nuovi Quick/Full locali e CI Quick→Full/A3 obbligatori sul medesimo albero. Esiti correnti e hash nei log e nella descrizione PR. Non modificare 40 golden, Camaiore congelata `5aaf159870912eb49bffbd044963549bfb920150`, controlli browser o budget Lighthouse.

## Prossima azione esatta

Completare i gate della PR conclusiva e richiedere al proprietario il suo merge. Dopo il merge verificare commit/albero, deploy, status live e valori pubblici; soltanto allora rendere efficace DONE e registrare l'attestazione nella PR/issue #330. Consegnare quindi l'handoff A7 senza avviarne UI o servizi. Nessun merge/deploy dell'assistente senza approvazione esplicita.

## Limiti e perimetro escluso

Dati congelati verificati nei perimetri dichiarati; niente certificazione della disponibilità online attuale o replay di originali non conservati. Le combinazioni temporali/benchmark e le coppie mantengono scope esplicito; nessuna causalità o inferenza individuale. Lacune informative e rifiuti restano validi. Radar, acquisizioni live, manutenzioni parallele, nuove UI A7, modelli e servizi esterni sono separati.
