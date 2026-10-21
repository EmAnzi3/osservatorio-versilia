# Consolidamento Osservatorio Versilia — handoff operativo

## Baseline verificata il 21 ottobre 2026

- Main `9ec855ff263c9ace7fabf957a12889dc58155f71`: marker #458 integrato; #448 resta l’ultima integrazione A7 qui attestata come pubblicata. Nessuna pubblicazione dedotta dai verdi delle PR.
- #459 OPEN, head `6902431be6692b78a6072367023235fbc309c618`, albero `8c774524bf3f0e92dc11fe52b2b8b906aef3eb66`. Include la sequenza A7 #451/#453/#454/#455/#457; stato ed evidenze storiche nelle rispettive PR. Non integrata in main né pubblicata.
- Sull’albero #459: Quick locale ordinario PASS (log SHA256 `b2c2e5a2ae6812f407b1c2689ea0b35e44e31d530a89a3da7a30f6208159b95e`); Full locale ordinario senza skip PASS (`003e0a36e88a28055464cfff0020de46c5d73ff7df7ecb28e51623d0d3c23e5d`). Zero modifiche tracciate; tentativi falliti conservati separatamente, non contati come PASS.
- CI Quick→Full effettivo `39563969537`: job `119101671369` e `119115744583` SUCCESS; A3 `39563969561`, job `119101671438` SUCCESS. Tutti i log attestano checkout `b8507751f6d10d7977db905416ab8c025b425c6c`, albero identico al candidato. Build/deploy SKIPPED. Home Lighthouse CI 100 con soglia 70 invariata.
- A6 DONE: 225/225 adapter, 3.727 casi indipendenti (2.033 calcoli / 1.694 rifiuti), 35 letture e due riepiloghi, Atlante 20.325 unità locali native, 40 golden e Camaiore congelata. Nessuna modifica di dati, adapter o golden.
- #443 editoriale e Radar restano filoni separati; il loro stato corrente va verificato prima di riprenderli. Dossier #430: 17 ambiti, 45 sotto-dossier, 51 piani, sei specifiche e due dimostrazioni; non 51 dossier completi.

## A7 IN_PROGRESS — metodo e capacità

La matrice schema 3 deriva acquisizione, capacità native, trasporto e UI dai
contratti, dal catalogo e dall’artifact verificato. La pubblicazione effettiva
resta distinta. Ultima misura dei collegamenti: 746 riferimenti acquisiti
risolti; percorsi richiesti interamente provati per 275 coppie nel workbench e
187 nel trasporto, non intere dimensioni certificate. Le 88 coppie con prove
native complete ma non statiche comprendono 49 benchmark e 39 dettagli
territoriali. Le 442 coppie senza prova nativa nel perimetro non sono dichiarate
dati assenti. Metodo: `docs/A7_ACCESSIBILITY_AUDIT.md`.

L’esploratore generale deriva tema, indicatore, vista, operazione e Comune dal
catalogo, conserva risposte e rifiuti A6, periodi, fonti, consenso e revoca.
Il runtime pubblico mantiene i tre profili originali sui riferimenti nativi:
osservazione/lookup comunale, confronto dei sette Comuni e serie comunale dove
ammesse. Nessun periodo arbitrario, aggregato generico, ranking aggiuntivo o
associazione inferita. 225 indicatori / 3.359 viste; 37.880 richieste, 21.283
computed / 16.597 rifiuti originali, 100.804.953 byte gzip. È una misura del
trasporto, non un nuovo corpus numerico indipendente. Manifest
`f554516cb141788b6612d7ed8229351771834d228e16189221b552e089282fe3`.

Pagina e grafo sono validati in staging e finalizzati insieme nell’unico
artifact Pages. Ancora e moduli vincolati alla release; fallimenti d’integrità,
budget o disponibilità non producono numeri sostitutivi. Il verificatore live
controlla la release e un campione nativo, distinguendo Content-Encoding HTTP
dai gzip applicativi. Nessun aumento della navigazione, nuovo backend o modello.
Metodo: `docs/A7_ATOMIC_RUNTIME_PACKAGE.md`, `docs/A7_GUIDED_EXPLORER_PREVIEW.md`
e `docs/A7_PUBLIC_EXPLORER_INTEGRATION.md`.

## Incremento locale corrente — leggibilità mobile

Durante la verifica visiva conclusiva è stato riprodotto un difetto a 390 px:
nel confronto popolazione sei valori su sette venivano spezzati su due righe,
pur senza overflow della pagina. La tabella A7 mantiene ora una larghezza
leggibile e scorre soltanto nel proprio contenitore; nomi e numeri non sono
forzati a spezzarsi fra caratteri. La regione è raggiungibile da tastiera e una
nota mobile spiega lo scorrimento. Dati, risposta completa, grafico e controlli
restano originali; CSS limitato all’esploratore.

Il gate browser esistente controlla che ogni valore numerico visibile occupi
una sola riga, oltre alla parità nativa già presente; verifica lo scorrimento da
tastiera sul viewport mobile. Il caso reale riproduce il rosso prima della
correzione e passa dopo, desktop/mobile, senza overflow della pagina. Non sono
state cambiate soglie, adapter o golden. I verdi della baseline 6902431 non si
trasferiscono a questa modifica: servono nuovi Quick/Full locali ordinari e
CI Quick→Full/A3 sul candidato corretto prima della prontezza al merge.

## Ambiente e prossima azione

Chrome Headless Shell ufficiale 151.0.7922.34 (SHA256 eseguibile
`e11fc9ce65c96313476f7ee9844b6fb6a9220fb048693cfe9eee00acf4170a9f`),
Playwright nativo 1.62.0 e Lighthouse canonico 13.4.1. Il workflow installa la
versione dichiarata nel gate e conserva i report Lighthouse nell’artifact
diagnostico esistente. Cache Python separate per modalità.

Il browser locale non raggiunge Unpkg: soltanto Percorsi riproduce i due file
originali Leaflet 1.9.4 verificati contro SRI. Le route restano sulle medesime
pagine dopo Percorsi e ne disabilitano la cache; Lighthouse usa sessioni
separate non intercettate. La riproduzione CDN non modifica DOM, dati, golden o soglie;
disponibilità corrente CDN e telefono fisico non certificati. Worktree nuovi
senza dist incompleti di build interrotte.

Preview e browser locali del nuovo incremento conclusi. Prossima azione: completare i gate,
aggiornare la stessa #459 e le evidenze. Nessun merge o deploy autorizzato.
A7 non è DONE; ulteriori operazioni, selezioni, export generale e dossier
restano incrementi motivati dalla matrice. Il rollout pubblico richiede
approvazione del proprietario e controllo del deploy effettivo.
