# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 12 ottobre 2026

- Baseline dopo merge manuale #413: main `6c6822cc2dc4279b84cfe1797adef6fc04ecb6bc`, albero `a856ad505667fd26aa0c715c7b370a49a85711a0`. Include #409, #407, #411 e la separazione del refresh live AGCOM #413. Dati e adapter invariati rispetto alla #411. La #412 è aperta; il precedente albero `db3e6b45382b58cd7871db2c864456c16c0aead6` ha Quick/Full locali completi e CI Quick→Full/A3 verdi. Riallineamento alla #413 in verifica. Copertura baseline 211/225 effettivi, 154/181 sorgente, 14 residui, 2.712 domande.
- Catalogo effettivo corrente: 225 indicatori, 124 storici, 137 confronti, SHA `d9fea44f9cf3e56309e1193bf63b5cfe32bfbc3ba088860843db8d14b9c12278`; registro SHA `261304eb74262058ba42f38d0b4584a3038f184e3bc602ab8e0b5d9eb9d13d5c`.
- A0–A5 DONE; A6 attiva, issue #330, branch `feat/a6-slow-mobility-adapters`. A6.1–A6.3 pubblicate; A6.4 parziale, A6.5–A6.6 aperte; A7 non avviata.
- Camaiore protetta al checkpoint `5aaf159870912eb49bffbd044963549bfb920150`; dati/UI/asset/golden/workflow/Radar, 35 letture e due riepiloghi conservati.

## Lotto in verifica

Inventario Percorsi v47: cinque carrier, dimensione totale, confronto/rango 7/7 Comuni. Fotografia editoriale 12 agosto 2026, A0/B1 come provenienza, modalità primaria; non inventario esaustivo né stato attuale di sicurezza/agibilità. 41 record pubblici e 68 appartenenze comunali sovrapposte. Replay delle cinque parti base64/gzip e riepiloghi, proprietà in cache; geometrie/intersezioni non rigiocate. Nessun pooling, benchmark, storia territoriale, chilometro comunale, rapporto, anomalia o coppia non revisionata. Metodo `docs/A6_SLOW_MOBILITY_ADAPTERS.md`.

35 conteggi fissi, record/ID condivisi, zeri/pari merito, puntatori e mutazioni ostili. 135 nuove domande e 2.712 della baseline #411 invariate (incluse le 110 connettività riallineate su main); suite 2.847 PASS (1.567 letture/calcoli, 1.280 rifiuti). Copertura derivata 216/225 effettivi, 159/181 sorgente, nove residui. Report `reports/a6-slow-mobility/`; gate canonici da completare sul medesimo albero.

## Prossima azione

Quick canonico locale su clone pulito prima di ogni push; aggiornare il branch della #412 solo dopo GREEN. Full completo locale in clone freddo, poi identità degli alberi e CI Quick→Full/A3 prima della prontezza. Non eseguire i browser locali in parallelo: il precedente lotto ebbe timeout concorrenti, con test isolato e Quick sequenziale poi verdi. Ricevute/log nel fascicolo; merge riservato al proprietario. Residuo derivato, chiusura metodologica distinta dal numero degli adapter.

## Manutenzioni e monitor separati

#407: SISBON 2.0, 154 codici (58 attivi/96 chiusi), replay raw e adapter aggiornato; MIMIT puntuale 10 ottobre, storico/mensili fino a settembre conservati. RUNTS Excel 11 ottobre acquisito in sola lettura (465 sedi), candidato distinto dai tassi 2025 non riconciliati. ARS 120 secondi per richiesta su tutto il dominio e rotte derivate; ZIP 255 fornito dal proprietario, osservazioni 2015–2025 invariate. Stato dati separa periodo pubblicato e prove storiche. Radar #402 e PNRR 25 settembre conservati. #338 rapporto mensile, #329 ASIA/AGCOM e #117 watchdog separati; #306 archiviata. Nessuna nuova acquisizione nel lotto A6.

Manutenzione AGCOM/RUNTS: mergiata nella #411, main `5e0ac39`. RUNTS 11 ottobre verificato nuovamente contro Excel ufficiale (SHA invariato): 465 enti per sede legale, densità con popolazione Istat 1 gennaio 2026; nessuna storia retrocostruita. AGCOM: periodi validati dinamicamente e coerenti 7/7 negli shard; import primario lega il CSV al catalogo ufficiale datato. Corretta l’etichetta 2025 dei valori già congelati e dei benchmark dello stesso CSV: consistenze ufficiali 6 luglio 2026, revisione 14 luglio; date di acquisizione preservate. Solo 110 domande connettività riallineate nei riferimenti, altre 2.602 invariate. Nessun nuovo CSV acquisito: ArcGIS restituisce errore interno. Aggiornamento acquisito dalla baseline corrente; la #412 conserva le sue verifiche e richiede nuovi gate sul proprio albero. Nessuna modifica grafica, merge riservato al proprietario.

Refresh ASIA/AGCOM dopo #411: base main `5e0ac39`. Il run post-merge `38179383613` fallisce sul CSV primario, che restituisce HTML; nessuna nuova acquisizione dichiarata. Il refresh live viene separato dal merge: solo dispatch e comando esplicito del proprietario, test offline nel Quick canonico già esistente. Il contratto verifica i trigger consentiti. Nessun cambio a dati, parser, soglie, UI o deploy.
