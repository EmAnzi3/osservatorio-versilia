# A6 — Sicurezza stradale e proventi rendicontati

Il lotto v38 abilita `roadSafety` e `roadFinesPerResident`, riusando soltanto carrier e snapshot già versionati. Riferimento corrente 2024, distinto dalla pubblicazione/acquisizione. Nessuna modifica a dati, UI, asset, golden, workflow, Radar o alle letture territoriali esistenti.

## Misure, universi e provenienza

| Carrier / dimensione | Unità | Denominatore | Serie consultabile | Benchmark 2024 |
|---|---|---|---|---|
| roadSafety / total, measure:incidents | incidenti ogni 1.000 | residenti medi annui | 2014–2024 | Toscana / Italia |
| roadSafety / measure:mortality | morti ogni 100 incidenti | incidenti con lesioni | 2014–2024 | Toscana / Italia |
| roadSafety / measure:injury | feriti ogni 100 incidenti | incidenti con lesioni | 2014–2024 | Toscana / Italia |
| roadSafety / measure:injured | feriti ogni 10.000 residenti | popolazione del tasso legacy Istat | 2020–2024 | non congelato |
| roadFinesPerResident / total | €/abitante nominali | residenti medi annui | 2021–2024 | Toscana / Italia |

`total` è un alias della sola incidentalità: non somma le quattro misure. Mortalità e lesività sono indici per 100 incidenti, non percentuali della popolazione; lesività può superare 100. Il luogo dell’incidente non identifica la residenza delle persone coinvolte. Turismo, traffico di attraversamento e piccoli conteggi rendono impropria una graduatoria automatica di rischio dei residenti o qualità delle politiche.

Le prime tre letture stradali e i proventi derivano dallo snapshot `data/source-snapshots/sicurezza-territorio-draft-2026-08.json`, che conserva serie comunali e righe ufficiali Toscana/Italia delle tavole Istat 15a/15c, con URL e SHA dei workbook originari. Il lotto controlla SHA dei byte e impronta del JSON congelato, identità dei Comuni, periodi e riconciliazione del catalogo. I workbook e i pannelli nazionali originali non sono incorporati: nessuna dichiarazione di replay raw. Le quattro righe benchmark sono quelle ufficiali della fonte, non medie dei Comuni.

La lettura Feriti ha provenienza distinta: è il carrier legacy Istat già pubblicato in `data/site-data.json`, conservato con impronta dei sette componentSeries e SHA del catalogo sorgente. L’adapter riconcilia questo carrier nella vista effettiva; il workbook originario e i conteggi/denominatori nativi non sono congelati in uno snapshot separato. Le risposte espongono `canonical_legacy_carrier`, puntatore e limite esplicito; non lo presentano come nuova estrazione raw.

## Lacune, aggregati e rifiuti

Stazzema 2017 è `null` nello snapshot per incidenti, mortalità e lesività. La serie pubblica omette quelle celle: l’adapter conserva il periodo con dato mancante e provenienza nativa, senza sostituirlo con zero o interpolazione. L’accesso alla serie che include la lacuna richiede `allowPartial`; restano validi i minimi comuni di osservazioni. Gli zeri ufficiali di mortalità sono valori osservati.

Confronto, rango numerico, consultazione delle serie e gap correnti revisionati sono ammessi. I cinque aggregati pubblici sono riconciliati come medie semplici dei sette Comuni: non sono tassi territoriali pooled né totali ufficiali Versilia. Numeratori e denominatori non si ricostruiscono dai rapporti; pooling rifiutato. Non vengono introdotti nuovi companion o collegamenti.

La continuità metodologica fra release e le coppie statistiche non sono certificate da questo lotto: variazioni, punti percentuali, trend, anomalie e correlazioni automatiche in entrambi gli ordini dei selettori sono rifiutati. Benchmark soltanto nel 2024 e negli scope revisionati; nessun benchmark dei Feriti o equivalenza fra i quattro denominatori. Sesso, età e quote sanzioni per velocità non sono abilitati.

I proventi DAIT sono importi nominali rendicontati per abitante: non contano i verbali e non misurano da soli controlli, riscossione, sicurezza o efficacia. La quota proventi da limiti di velocità rimane intenzionalmente non pubblicata; le tavole regionali di Polizia locale restano aggregate e non diventano osservazioni comunali.

## Verifica

Fixture indipendenti: 35 celle correnti, sette alias primari, 35 ancore storiche, 56 gap correnti e cinque medie pubbliche. Replay separato di 294 celle storiche distinte, incluse tre celle native mancanti e 35 celle Feriti del carrier legacy. Le 77 osservazioni storiche dell’alias Incidenti non sono conteggiate come nuovi dati. Verificati zero/mancante, puntatori sorgente/catalogo, copertura parziale, periodi e mutazioni avverse di catalogo, cache e impronte.

Corpus: 198 nuove domande e tutte le 1.512 precedenti conservate. Totale 1.710 PASS, 876 letture/calcoli e 834 rifiuti. Copertura derivata attesa 198/225 effettivi, 142/181 sorgente, 27 residui. Report preliminari `reports/a6-road/` sul catalogo effettivo #390, SHA conservato; base Git riallineata alla #389 Radar con le sue 14 modifiche byte per byte, fuori dal diff A6; Quick e Full freddi devono ricostruire e riconciliare la stessa vista. 58 collegamenti tipizzati, 29 companion e 105 carichi descrittivi, senza soglie di latenza o promesse di produzione.

A6.4 resta parziale; A6.5–A6.6 aperte alla revisione metodologica; A7 non avviata. Gate canonici obbligatori prima della prontezza al merge manuale.
