# A6 — attestazione conclusiva e condizioni di efficacia

## Efficacia verificata — 13 ottobre 2026

**A6 DONE effettivo.** #428 mergiata dal proprietario, commit `d09d8e2f695a859e555cae28db69655f7b6d7130`, albero `c96760860332737c0532c1b532ed240e4857ed07` identico al candidato approvato. Build/deploy `38401356844` e controllo live `38403216866` SUCCESS sul commit integrato. Catalogo HTTP 225 indicatori e Atlante 20.325; replay post-merge 3.727/3.727 PASS, 225/225 adapter, 35+2 letture e zero residui inattesi. Report SHA `b3eeb39cdba5dad18bc3c111c3e19174173afb15dbd7bee89ab382a82673e3ea`. Attestazione dettagliata nella #428 e issue #330 chiusa. A7 NOT_STARTED come implementazione.

Le sezioni seguenti conservano la proposta e le condizioni verificate, senza riscrivere la cronologia delle evidenze.

## Stato e baseline della proposta

**A6 è IN_PROGRESS fino all'approvazione, al merge e alla verifica della PR amministrativa conclusiva.** Questo documento propone il passaggio a DONE sulle evidenze sotto elencate; non attesta come avvenuti eventi futuri. A7 è NOT_STARTED. Le verifiche tecniche degli step A6.1–A6.6 sono completate e integrate; l'efficacia della chiusura amministrativa resta condizionata.

Baseline integrata verificata: `cb73eadd9be1c46cc1196652d6068d41ae5d4363`, albero `ea4638204f636a520f9dae8080f926fa6c6a6185`. #423 completa gli adapter, #425 corregge Atlante, #427 integra il metodo v56. #424 Radar e le manutenzioni approvate restano preservate e fuori da questo lotto. La PR conclusiva modifica esclusivamente documentazione: nessun adapter, dato, asset, renderer, workflow, golden master o soglia.

## Evidenze A6.1–A6.6 e Definition of Done

| Step / criterio | Evidenza verificabile | Risultato e limite |
|---|---|---|
| A6.1 — modello | `validate_semantic_model_contract`, catalogo effettivo e registry materializzati dal preflight | 225 ID effettivi riconciliati; 166/181 sorgente è un perimetro distinto |
| A6.2 — operazioni | Contratto e regressioni A6.2; checker razionale indipendente | Formule verificabili, risultati o rifiuti motivati; presenza dell'adapter non autorizza ogni operazione |
| A6.3 — comparabilità | Guardie dei profili, preflight e matrice `contextsByDimension` / `benchmarkScopesByDimension` | Periodi, universi, unità, nominale/reale, scopi e classificazioni distinti; nessuna eredità implicita dalla vista primaria |
| A6.4 — motore e provenienza | `semantic_methodological_audit.py`, baseline congelata, suite dei profili | 225/225, zero carrier senza adapter; 3.359 viste dichiarate; fonti, periodi, formule, hash e puntatori controllati nei perimetri espliciti |
| A6.5 — letture | `semantic_territorial_readings.py`, revisione indipendente e report `readings.md` | Tutte le 35 letture e i due riepiloghi preservati e verificati; osservazioni, calcoli, associazioni, ipotesi e opzioni non approvate distinti |
| A6.6 — interpretazione | Coppie motivate, n effettivo, allineamento, leave-one-out e regressioni sulle avvertenze | Associazioni descrittive/ecologiche, senza causalità, previsione, p-value, effetti di politica o inferenze individuali |
| Domande multi-indicatore | `ci/a6-territorial-acceptance-questions.json`, `questions-and-gaps.md` e richieste nel JSON dell'audit | 7 supportate, 9 parzialmente supportate, 4 non determinabili; problema, fonti, operazioni, limiti, lacune e valore conoscitivo espliciti |
| Assenza di regressioni | Quick→Full sul candidato, browser/A4/Lighthouse, CI Quick→Full/A3 | I risultati della PR conclusiva sono registrati nella PR e nei relativi log, senza riutilizzare i gate delle precedenti PR come esito del nuovo candidato |

La Definition of Done è soddisfatta tecnicamente: le domande supportate e le componenti risolvibili delle domande parziali usano richieste strutturate, calcoli deterministici, dati e metodi citati. Le cinque ricette multi-indicatore consentono letture di contesto e calcoli ammessi; le relazioni non confrontabili sono rifiutate. Nessuna promessa di risposta universale o di decisione amministrativa automatica.

## Atlante: dato nativo, pubblicazione e conservazione

| ISTAT | Comune | Unità locali attive 2025 |
|---|---|---:|
| 046005 | Camaiore | 3.822 |
| 046013 | Forte dei Marmi | 1.556 |
| 046018 | Massarosa | 1.940 |
| 046024 | Pietrasanta | 3.327 |
| 046028 | Seravezza | 1.437 |
| 046030 | Stazzema | 245 |
| 046033 | Viareggio | 7.998 |
| — | Versilia | 20.325 |

La somma deriva da `tt[Comune][2025]` nel payload canonico compatto congelato. I 292 derivavano soltanto dai record diretti delle divisioni ATECO: non erano un totale territoriale. `materialize_economy_atlas_release.py` ora materializza i totali nativi, senza sommare livelli gerarchici. Registro Imprese, imprese ASIA, addetti e occupati restano universi distinti. Record ATECO, quantità artigiane, quote e LQ non sono sostituiti dal riepilogo.

Le regressioni controllano identità dei sette Comuni, 84 valori annuali 2014–2025, somma, duplicati, gerarchie, anni, null, zero e copertura; il replay specializzato verifica 111.832 celle compatte, incluse 56.238 null. Le ancore fisse esistevano già nella baseline #423. Non è replay dei CSV originari non conservati. L'implicit `total` resta rifiutato per richiedere la selezione esplicita dell'universo, non per la vecchia discrepanza.

Il catalogo HTTP pubblico è stato verificato dopo #425 e nuovamente dopo #427: 225 metriche, sette valori e aggregato 20.325 PASS. Il deploy di #427 `38372493679` e il controllo live `38374702463` sono SUCCESS sul commit integrato `cb73eadd`. Il motore Python è integrato nella repository; non viene presentato come API web o interfaccia conversazionale pubblicata.

## Riepiloghi, interpretazione e lacune

I sei rapporti dei due riepiloghi usano le componenti originali sommate. Il report mostra separatamente la media aritmetica comunale: non è intercambiabile con il rapporto di somme. Autocontenimento = lavoro nel proprio Comune; ingressi/uscite lordi includono movimenti interni al gruppo, senza ricostruire attraversamenti del confine Versilia. Denominatori 2021/2026 e anni scolastici conservano le date proprie.

Abitazione e bilanci sono approfondimenti supplementari del repertorio, non due dei cinque percorsi A6.5. Accessibilità economica familiare della casa, fabbisogno di scuole/nidi/corse e effetti degli interventi richiedono dati ulteriori. Il backlog informativo resta esplicito; tali lacune non diventano dati acquisiti né rifiuti eliminati per ottenere PASS.

Inventario, dimensioni dichiarate, confini delle operazioni non accoppiate, 3.727 risposte congelate e 35+2 letture sono verificati integralmente nel perimetro documentato. Combinazioni Comune × anno × vista, benchmark e correlazioni mantengono le query esatte eseguite: non tutte universalmente. I 4.926 probe computed, 32.358 not_computable, 2.844 not_supported e 515 requires_selected_pair non gonfiano la suite 3.727 (2.033 consultazioni/calcoli, 1.694 rifiuti).

I controlli di provenienza verificano i byte congelati effettivamente letti, hash e puntatori, con ricostruzione dichiarata dei frammenti INVALSI/affluenza. I profili distinguono replay nativo, normalizzato e solo catalogo; limiti legacy, EV, ospedali e dimensione familiare restano visibili. Non si certificano archivi originari non letti o disponibilità attuale delle fonti online. Nessuna acquisizione live o manutenzione Radar è inclusa.

## Riproduzione, gate e chiusura amministrativa

```bash
python scripts/preflight.py --quick
python scripts/preflight.py --full
python scripts/semantic_methodological_audit.py --catalog dist/data/site-data.json --output-dir /tmp/a6-final-audit
```

L'audit genera query, esiti, motivi, verifiche indipendenti, hash delle risposte e file realmente letti. `reports/a6-methodological-review/summary.json` conserva il report della #427 (SHA `31156feaa52744bf42281a63b2dc890a3cd53fc91d8a0815713e4d085ae5254f`); una nuova esecuzione può differire nei percorsi assoluti di provenienza, senza cambiare i valori. Il nuovo replay sulla main integrata ha esito PASS, zero residui inattesi, stessi conteggi e 129 file letti con byte/hash invariati rispetto alla #427. SHA del nuovo JSON: `1737e151ede3aba78c5b032b0f4bf4f543edbb1e4bed9625bd1ed804d1b7e84b`; riepilogo derivato `reports/a6-closure/summary.json`. Il report tecnico non può approvare o chiudere A6 automaticamente.

Gate #427 completati: locali Quick 1.173,36 s → Full 2.292,11 s sul medesimo albero; CI Quick `38365187212`, Full `38369132467`, A3 `38365187081` PASS. 40 golden, 578 controlli browser e quattro budget Lighthouse PASS. Questi sono evidenza della baseline integrata; **non sostituiscono i nuovi gate della PR conclusiva**. Camaiore congelata `5aaf159870912eb49bffbd044963549bfb920150` e tutte le soglie restano intatte.

La PR conclusiva deve avere propri Quick→Full locali sequenziali, CI Quick→Full e A3 sullo stesso candidato. Gli esiti, hash e limiti dell'ambiente sono registrati nella descrizione PR e nel pacchetto di log. Se un gate fallisce, l'esito rimane FAIL finché causa radice e nuovo candidato non sono verificati; niente soglie ridotte o PASS per verifiche interrotte.

**Condizioni congiunte per rendere efficace DONE:** approvazione esplicita del proprietario; merge della PR conclusiva; corrispondenza dell'albero integrato col candidato verificato; CI pertinenti SUCCESS; deploy del commit integrato e controllo live SUCCESS; valori pubblici Atlante e integrità delle route riconfermati. Fino a questi eventi lo stato effettivo è IN_PROGRESS, anche se i gate della proposta sono verdi. La verifica post-merge viene registrata nella PR conclusiva e nell'issue #330, senza nuovi dati o funzionalità.

Solo dopo l'efficacia della chiusura viene consegnato l'handoff A7: interfaccia Python/CLI e schemi effettivi, capacità per dimensione, ambiguità/rifiuti, citazioni e riproducibilità, separazione calcolo/interpretazione, limiti dell'hosting statico, requisiti di prestazione/sicurezza/verificabilità e repertorio di accettazione. Nessuna UI conversazionale, servizio esterno o modello linguistico è introdotto da questa PR.
