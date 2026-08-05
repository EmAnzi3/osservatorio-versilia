# Audit dati comunali toscani e bilanci

Stato: ricerca tecnica su ramo separato. Nessuna modifica al sito pubblico.

## Perimetro

Comuni verificati:

- Camaiore — 046005
- Forte dei Marmi — 046013
- Massarosa — 046018
- Pietrasanta — 046024
- Seravezza — 046028
- Stazzema — 046030
- Viareggio — 046033

Criteri minimi per l'inserimento:

1. scala comunale reale;
2. copertura 7/7;
3. stessa definizione e stesso denominatore;
4. fonte ufficiale;
5. anno e metodo espliciti;
6. assenza di duplicazioni sostanziali con indicatori già pubblicati.

## Indicatori comunali regionali 2024

La batteria regionale contiene 20 indicatori. Nel file 2024, 19 hanno copertura 7/7 per l'Osservatorio; l'indicatore sulle unità locali di assistenza sanitaria è `nd` per tutti i sette Comuni.

### Candidati da implementare

| Tema | Indicatore | Serie | Esito |
|---|---|---:|---|
| Lavoro | Giovani 15–24 anni in altra condizione professionale | 2018–2024, escluso 2020 | accettato, con denominazione prudente: non è il tasso di disoccupazione e non coincide automaticamente con i NEET |
| Economia | Ditte individuali attive con conduttore nato all'estero | 2018–2024 | accettato |
| Economia | Imprese attive nei settori dell'innovazione | 2018–2024 | accettato, mantenendo la definizione Ateco regionale |
| Salute | Tempo di risposta del 118, 75° percentile | 2018–2024 | accettato; misura il valore entro cui ricade il 75% degli interventi, non una media |
| Salute | Persone 0–64 anni con disabilità anche grave ogni 1.000 residenti 0–64 | 2018–2024 | accettato; descrive riconoscimenti amministrativi, non la prevalenza sanitaria complessiva |
| Ambiente | Quota della SAU coltivata con metodo biologico | 2018–2024 | accettato |

### Candidati esclusi o rinviati

| Indicatore o fonte | Decisione | Motivo |
|---|---|---|
| Persone in cerca di occupazione sulle forze di lavoro 15+ | rinviato | valido e 7/7, ma molto vicino al tasso di disoccupazione 25–64 già presente; va evitata una doppia misura non immediatamente distinguibile |
| Individui 25–49 anni con titolo terziario | rinviato | sovrapposizione con l'indicatore sul titolo terziario già presente |
| Organizzazioni iscritte agli albi regionali | escluso | sostanziale sovrapposizione con gli enti RUNTS già pubblicati, sebbene gli universi non siano identici |
| Servizi comunali online al massimo livello | escluso | il valore ripetuto nel 2023 e 2024 è in realtà il dato definitivo 2022 |
| Unità locali di assistenza sanitaria | escluso | copertura 0/7 nel file regionale 2024 |
| Rischio ambientale sintetico | escluso | composito poco leggibile; il sito pubblica già separatamente suolo, alluvioni e frane |
| Pressione turistica | escluso | già coperta da indicatori comunali più dettagliati su presenze, posti letto e intensità turistica |

## Occupazione ASIA: limite territoriale

Il file regionale `occupazione_asia_2023.csv` distingue:

- dipendenti;
- indipendenti;
- esterni;
- interinali;
- quattro macro-settori.

Non è però comunale per tutti gli enti. Il campo territoriale contiene soltanto i dieci capoluoghi toscani e la voce aggregata `Altro comune della provincia`. Per la provincia di Lucca non permette quindi di distinguere Camaiore, Forte dei Marmi, Massarosa, Pietrasanta, Seravezza, Stazzema e Viareggio.

Questa fonte non può essere usata per attribuire ai sette Comuni quote di dipendenti, indipendenti o interinali.

## Infortuni sul lavoro

La Regione pubblica la tavola 2e con le denunce INAIL per Comune della provincia di Lucca, anni 2020–2024. La scala territoriale è corretta.

Prima dell'inserimento occorre ancora:

- acquisire il file allegato e verificare i sette valori;
- controllare eventuali piccoli numeri o soppressioni;
- evitare un tasso per occupato costruito con il denominatore ASIA, perché l'universo ASIA non coincide con quello INAIL.

L'indicatore utilizzabile, se la copertura sarà 7/7, è il numero di denunce e la relativa serie; non un indice di rischio comparativo non supportato dal denominatore.

# Bilanci comunali

## Fonte primaria: OpenBDAP

Per i bilanci armonizzati la fonte primaria proposta è OpenBDAP della Ragioneria generale dello Stato.

Documenti disponibili per singolo ente:

- bilancio di previsione;
- rendiconto della gestione;
- bilancio consolidato;
- piano degli indicatori e dei risultati attesi o conseguiti.

Serie armonizzata disponibile dal 2016. I dati antecedenti sono pubblicati separatamente come certificati preventivi e consuntivi, con schema non direttamente sovrapponibile.

### Grado di dettaglio

#### Spesa

- missione;
- programma;
- titolo;
- macroaggregato;
- piano dei conti integrato fino al massimo livello disponibile nel rendiconto.

#### Entrata

- titolo;
- tipologia;
- categoria;
- piano dei conti integrato fino al massimo livello disponibile nel rendiconto.

#### Grandezze contabili del rendiconto

- previsioni definitive;
- residui iniziali e finali;
- accertamenti per le entrate;
- impegni per le spese;
- incassi;
- pagamenti;
- gestione di competenza e gestione dei residui.

Il massimo dettaglio tecnico è molto elevato, ma non deve diventare il livello principale di lettura del sito: produrrebbe centinaia o migliaia di righe per Comune e anno.

## Fonte secondaria: SIFAL

SIFAL Regione Toscana resta utile per:

- serie storica lunga;
- controllo incrociato dei dati dei Comuni toscani;
- indicatori economico-finanziari regionali già calcolati;
- esportazioni CSV, XLS e PDF.

Non è la fonte primaria proposta perché l'interfaccia Pentaho è meno stabile per l'automazione e l'aggiornamento pubblico è meno trasparente rispetto a OpenBDAP.

## Anno di riferimento

OpenBDAP ha pubblicato il rendiconto 2025 dei Comuni, ma la copertura nazionale dichiarata è ancora superiore all'85%. Il rendiconto 2024 ha copertura superiore al 95%.

Regola proposta:

- usare il 2025 solo dopo verifica nominativa 7/7;
- in assenza di tutti i sette enti, pubblicare il 2024 come ultimo anno comune;
- aggiornare automaticamente al 2025 quando la copertura dei sette Comuni sarà completa.

## Architettura proposta nel sito

I bilanci meritano un tema autonomo, separato da `Comunità`, perché mescolare rendiconto, SIOPE, PNRR e terzo settore renderebbe la lettura poco chiara.

### Indicatori principali

1. entrate correnti pro capite;
2. spesa corrente pro capite;
3. spesa in conto capitale pro capite;
4. autonomia tributaria;
5. capacità di riscossione;
6. capacità di pagamento;
7. debito residuo pro capite;
8. risultato di amministrazione disponibile pro capite, se ricostruibile uniformemente.

### Dettagli di secondo livello

- spesa per missione;
- spesa per programma;
- entrate per titolo e tipologia;
- investimenti per missione;
- andamento annuale dal 2016;
- confronto tra competenza e cassa;
- dettaglio tecnico scaricabile, non mostrato come graduatoria principale.

### Regole metodologiche inderogabili

- non mescolare previsione e rendiconto;
- non chiamare `spesa` un pagamento di cassa senza specificarlo;
- non sommare gestione di competenza e residui senza indicarlo;
- non confrontare accertamenti con pagamenti;
- non usare il bilancio consolidato come se fosse il bilancio del solo Comune;
- non trasformare avanzo, risultato di amministrazione e cassa finale in concetti equivalenti.

## Prossime operazioni tecniche

1. verificare tramite API e file OpenBDAP la presenza nominativa dei sette rendiconti 2024 e 2025;
2. definire il dizionario dei codici BDAP e dei codici fiscali dei sette enti;
3. estrarre un dataset comunale normalizzato per entrate, spese, residui e indicatori;
4. validare le formule su almeno un rendiconto ufficiale pubblicato da ciascun Comune;
5. costruire anteprima privata del tema `Bilanci`;
6. mantenere il sito pubblico invariato fino alla verifica manuale e all'approvazione.
