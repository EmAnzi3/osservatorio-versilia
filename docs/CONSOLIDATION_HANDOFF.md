# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 11 ottobre 2026

- Baseline dopo merge manuale #409: main `bc2debb7a503488b43ae7cd3ba8108a081cf9b92`, albero `e8069f647bb898c7919b918bc0565ff4e7504df2`. Include grafo viario v46 e manutenzione fonti #407; non coincide con il solo albero PR #409 `c8c09d16f66d221a7e813701096abf83b5afba0d`. CI Quick→Full e A3 della #409 verdi; Quick locale verde, Full locale precedente interrotto senza ricevuta finale: non dichiarato GREEN. Copertura 211/225 effettivi, 154/181 sorgente, 14 residui, 2.712 domande.
- Catalogo effettivo corrente: 225 indicatori, 124 storici, 137 confronti, SHA `6fe570d5b0a4aec85810922dc4b177c772a709549d3b45fb73006353dec1767b`; registro SHA `02585646c1f50e9c59e65087cee91c7824be57d338b38dc3fdebbe2900346b35`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-slow-mobility-adapters`. A6.1–A6.3 pubblicate; A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

Inventario Percorsi v47: cinque carrier, dimensione totale, confronto/rango 7/7 Comuni. Fotografia editoriale 12 agosto 2026, A0/B1 come provenienza, modalità primaria; non inventario esaustivo né stato attuale di sicurezza/agibilità. 41 record pubblici e 68 appartenenze comunali sovrapposte. Replay delle cinque parti base64/gzip e riepiloghi, proprietà in cache; geometrie/intersezioni non rigiocate. Nessun pooling, benchmark, storia territoriale, chilometro comunale, rapporto, anomalia o coppia non revisionata. Metodo `docs/A6_SLOW_MOBILITY_ADAPTERS.md`.

35 conteggi fissi, record/ID condivisi, zeri/pari merito, puntatori e mutazioni ostili. 135 nuove domande e 2.712 della baseline corrente invariate; suite 2.847 PASS (1.567 letture/calcoli, 1.280 rifiuti). Copertura derivata 216/225 effettivi, 159/181 sorgente, nove residui. Report `reports/a6-slow-mobility/`; gate canonici da completare sul medesimo albero.

## Prossima azione

Quick canonico locale su clone pulito prima di ogni push; pubblicare la PR tecnica solo dopo GREEN. Full completo locale in clone freddo, poi identità degli alberi e CI Quick→Full/A3 prima della prontezza. Non eseguire i browser locali in parallelo: il precedente lotto ebbe timeout concorrenti, con test isolato e Quick sequenziale poi verdi. Ricevute/log nel fascicolo; merge riservato al proprietario. Residuo derivato, chiusura metodologica distinta dal numero degli adapter.

## Manutenzioni e monitor separati

#407: SISBON 2.0, 154 codici (58 attivi/96 chiusi), replay raw e adapter aggiornato; MIMIT puntuale 10 ottobre, storico/mensili fino a settembre conservati. RUNTS Excel 11 ottobre acquisito in sola lettura (465 sedi), candidato distinto dai tassi 2025 non riconciliati. ARS 120 secondi per richiesta su tutto il dominio e rotte derivate; ZIP 255 fornito dal proprietario, osservazioni 2015–2025 invariate. Stato dati separa periodo pubblicato e prove storiche. Radar #402 e PNRR 25 settembre conservati. #338 rapporto mensile, #329 ASIA/AGCOM e #117 watchdog separati; #306 archiviata. Nessuna nuova acquisizione nel lotto A6.
