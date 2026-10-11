# A6 — Concentrazione turistica, adapter v45

`tourismSeasonality`, dimensione `total`, legge la quota delle presenze annuali 2025 nei tre mesi con più pernottamenti. Sono ammessi confronto, rango numerico e scostamento dalla Toscana in punti percentuali. Copertura comunale 7/7. I tre mesi sono scelti separatamente per ciascuna geografia: non sono necessariamente giugno–agosto e non sono un trimestre fisso. La quota misura concentrazione, non volume turistico, qualità o priorità politica.

## Evidenze e limiti

L'adapter riconcilia sette valori pubblici del catalogo e il benchmark regionale già congelato in `data/source-snapshots/a3-regione-toscana-tourism-benchmark-2025.json`. Fonte Regione Toscana, movimento turistico 2025, aggiornamento maggio 2026. Ogni osservazione riporta percorso, hash e puntatore; il confronto regionale cita anche l'URL mensile del materiale A3. Fingerprint completi di definizione/valori e snapshot sono ricontrollati dopo ogni accesso, inclusa la cache. Il catalogo sorgente ed effettivo hanno lo stesso carrier revisionato.

Il repository conserva risultati annuali e un pannello di movimento **annuale** 2023–2025, ma non i dodici conteggi mensili comunali/regionali né l'identità dei tre mesi selezionati. Lo snapshot A3 attesta una precedente riconciliazione, non permette di ripetere oggi il calcolo dai mesi originari. Il replay dichiarato riguarda esclusivamente il catalogo pubblico e il risultato A3, non i workbook mensili. Nessun numeratore viene ricostruito moltiplicando una percentuale per un totale annuale.

Il pooling è rifiutato: scegliere i tre massimi non commuta con la somma territoriale. Se un Comune concentra 10 presenze in gennaio, febbraio e marzo e un altro 10 in aprile, maggio e giugno, i numeratori comunali sommano a 60; i tre massimi del pannello aggregato sommano a 30. Anche ponderare le quote con presenze annuali sarebbe quindi scorretto. L'aggregato Versilia già pubblicato rimane nel catalogo ma non diventa una query aggregata verificata o un benchmark dell'adapter.

L'anno 2025 identifica una misura annuale: non viene esposto come una serie mensile. Sono rifiutati serie/trend/variazioni, benchmark Italia/Versilia, componenti, dimensioni mensili, normalizzazioni non presenti, anomalie e correlazioni non revisionate. Le presenze annuali 2023–2025 non colmano lo storico mancante della concentrazione.

## Verifica e perimetro

`test_semantic_seasonality_adapters.py` contiene riferimenti fissi indipendenti dalle risposte del motore: sette quote, sette scostamenti regionali, rango, puntatori, mutazioni ostili del carrier/snapshot dopo cache, periodi/dimensioni/operazioni rifiutati e il controesempio di aggregazione. La suite aggiunge 34 domande conservando le 2.476 precedenti: 2.510 PASS, 1.429 letture/calcoli e 1.081 rifiuti.

Copertura derivata 210/225 effettivi, 154/181 sorgente, 15 residui. Audit, collegamenti e baseline prestazionale sono generati in `reports/a6-seasonality/`; i conteggi non chiudono A6.4–A6.6. Nessuna acquisizione nuova o modifica a dati, interfaccia, asset, golden, workflow, Radar, checkpoint Camaiore, 35 letture territoriali e due riepiloghi. Quick locale obbligatorio prima del push; Full completo locale e CI Quick→Full sul medesimo albero prima della prontezza al merge del proprietario.
