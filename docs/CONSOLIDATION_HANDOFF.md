# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline verificata il 19 ottobre 2026

- Main `fed2a7c73f3ba480a153eea4748e7b874b2e8c28`: #448 integrata e pubblicata. Deploy `39171231146` e live `39172500248` attestano quella baseline.
- #451 OPEN/Ready, head `fd196e6681a75be3d4620d5155618a9f8568ebb4`, tree `8d30ba9dff733f38e1cde7a97901a47a5e819574`; Quick→Full `39178021176` e A3 `39178021175` PASS. Non integrata né pubblicata.
- #453 OPEN/Ready, head `be9fa6c6276cd6044fa2f5cc837a878ee5a2f946`, tree `5bf7dbde9937bd8a95c0d63501dc439be6273eef`; Quick e Full locali ordinari PASS, CI Quick→Full effettivo `39293987481` e A3 `39293987677` PASS sullo stesso albero. P2 riprodotto, corretto e risolto dopo i gate; preservata identità di categorie e anni nei puntatori. Evidenze `A7_PR453_be9fa6c_evidenze.zip`, SHA256 `822e9ff03d727bea59a87e420d5aeba77b856a5d9bff75daf31930da0f6e1ff6`. Non integrata né pubblicata.
- #443 editoriale lavoro/redditi OPEN/Ready, head `89127cac42bfc1a0877695fff60e0b9103e01e86`, con conflitti all'ultima verifica; separata. Radar e social fuori perimetro.
- A6 DONE: 225/225 adapter, 3.727 casi indipendenti, 35 letture e due riepiloghi, Atlante 20.325 unità locali native, 40 golden e Camaiore congelata. Nessuna modifica di dati/adapter/golden.
- Dossier #430: 17 ambiti, 45 sotto-dossier, 51 piani, sei specifiche e due dimostrazioni; non 51 dossier completi. Piloti editoriali ed esploratore generale distinti.

## Incremento corrente — A7 IN_PROGRESS

PR #454, branch `feature/a7-evidence-linkage`, derivato dall'albero verificato #453.
Le PR precedenti rimangono invariate. Nessun merge o deploy autorizzato.

L'audit schema 2 separa riferimenti acquisiti, prove native del workbench e prove
nel trasporto effettivo. Il resolver riusa il contratto companion A3 esistente,
legge gli operandi delle espressioni senza calcolarli, preserva categorie/anni e
richiede hash/payload coerenti per storage separati. I puntatori `published_benchmark`
sono riconosciuti tramite l'identità del catalogo; definizioni, valori uguali,
rifiuti o nomi di route non diventano automaticamente prove di accesso.

Le sette famiglie companion presenti sono lette dal contratto esistente, inclusi
campi target/canonici, parti e popolazione media. Le componenti temporali vengono
interrogate nei periodi del contratto; `metric_current` conserva il riferimento
nativo, senza inventare anni. I riferimenti compact riusano lo schema Atlante A3.
Sono accessi alle componenti, non formule nuove o trasferimenti automatici della
dimensione al target. Il ledger conserva
richieste, esiti, motivi e digest delle risposte originali; prove parziali e ponti
semantici non risolti restano distinti. Ogni risposta statica è rigiocata anche dal
workbench: la sua prova non può mancare dal ledger nativo. Identità JSON e cache
delle parti hanno regressioni negative specifiche. Metodo `docs/A7_ACCESSIBILITY_AUDIT.md`.

La precedente misura 150 puntatori / 596 acquisiti non provati riguardava i soli
percorsi semplici nel runtime; resta legacy, non viene spacciata per copertura
nativa o chiusura A3→A6→A7. Anche tutti gli operandi raggiunti provano percorsi,
non l'intera dimensione. Nessuno step A7 dichiarato DONE.

## Gate e seguito

Per questo nuovo albero: Quick locale ordinario prima del push; Full locale
ordinario, CI Quick→Full effettivo e A3 prima della prontezza al merge. Ricevute,
misure e limiti del candidato sono registrati nella relativa PR dopo i gate;
nessun verde delle PR precedenti si trasferisce alle modifiche correnti.
P2 #454 riprodotto: una build ranking senza shard includeva il dettaglio nei
massimi shard (2.896 byte grezzi / 642 gzip anziché zero). Il builder ora aggiorna
quei massimi soltanto per blocchi di risposta; test zero-shard e confronto con i
riferimenti effettivi degli shard. Totali gzip/detail e budget restano distinti.
Il Full della prima head #454 è stato interrotto; Quick/A3 di quella head non
attestano la correzione. Rigenerare runtime e prove con la nuova identità builder.

Nessun ampliamento del runtime, UI, menu o navigazione. Ranking resta opzionale,
default invariati. Pubblicazione atomica/ancora/errori definita nel metodo, ma
publisher pubblico ancora da implementare e verificare prima del rollout.
Seguono collegamenti semantici residui e dettagli oltre il perimetro delle prove,
poi periodi/selezioni e operazioni motivati dalla matrice, integrazione guidata,
grafici, citazioni/export e dossier/PDF. Non aumentare la raggiungibilità pubblica.
