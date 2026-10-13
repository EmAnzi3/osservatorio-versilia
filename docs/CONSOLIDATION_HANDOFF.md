# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — candidato metodologico

- Main dopo merge del proprietario della #425: `37928e86a057c883f77b180175e681d87fad50da`, albero `8dd1048073b3d79aa2ed9fda0cbec5576054eb4a`; #423/#424 preservate; A6 IN_PROGRESS, issue #330, A7 NOT_STARTED.
- PR #425 `fix/a6-atlas-territorial-total`: riepilogo nativo 2025 pari a 20.325, distinto dai 292 delle sole divisioni dirette; invariati payload, classificazioni, storici e universi. Integrata dal proprietario. Quick/Full locali sequenziali PASS; CI Quick `38350927492`, Full `38354234979`, A3 `38350927459` PASS sul medesimo candidato. Deploy main `38357820460` e controllo live `38359296744` SUCCESS; non sostituiscono l'attestazione metodologica A6.
- Adapter completi 225/225 effettivi e 166/181 sorgente; baseline 3.727 casi, 2.033 consultazioni/calcoli e 1.694 rifiuti. Copertura non equivale a chiusura metodologica.
- A0–A5 DONE; A6.1–A6.3 integrate; A6.4–A6.6 restano aperte fino alla verifica e chiusura amministrata. Non modificare i 40 golden o Camaiore `5aaf159870912eb49bffbd044963549bfb920150`.

## Candidato PR 2

Branch locale `feat/a6-methodological-closure`, basato sulla main integrata della #425. Motore v56: contesti e benchmark per dimensione, senza nuove operazioni/adapter. Verificatore indipendente razionale di formule, pairing/campioni/sensibilità e provenienza (inclusi payload ricostruiti da frammenti). Audit di tutte le viste e rifiuti delle operazioni non dichiarate; nessuna scansione indiscriminata di coppie.

35 letture e due riepiloghi preservati, annotazioni esplicative e confronto rapporto di somme/media comunale separati. Repertorio di domande concrete con evidenze già verificate, classificazioni supportata/parziale/non determinabile e lacune informative. Abitazione e bilanci supplementari, non nuovi percorsi dentro i cinque A6.5. Metodo `docs/A6_METHODOLOGICAL_REVIEW.md`; CLI `scripts/semantic_methodological_audit.py`.

Verifiche analitiche locali preliminari PASS sui dati effettivi corretti; report con query, hash e limiti. Quick/Full canonici sequenziali, browser, CI Quick→Full/A3 sul medesimo candidato e integrazione approvata ancora necessari. Nessuna attestazione DONE, merge o deploy dell'assistente.

## Prossima azione

Concludere i gate del candidato metodologico, preparare PR 2 separata e integrare soltanto su approvazione del proprietario. PR amministrativa finale dopo integrazione/verifica delle precedenti; handoff A7 dopo chiusura A6.

## Perimetro escluso

Radar #424, monitor/acquisizioni live, nuove UI A7, modelli linguistici e servizi esterni separati. Snapshot, valori pubblici oltre alla correzione Atlante, asset, workflow e golden non riscritti dal lotto metodologico.
