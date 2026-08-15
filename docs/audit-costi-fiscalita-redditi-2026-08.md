# Audit dati — costi, fiscalità, inflazione e redditi

Data audit: **15 agosto 2026**  
Base: `main` @ `4c6f978043c98f34e1f1b186c4483d8be6e0f910` — **v1.12.0**, 121 indicatori (117 inline + 4 climatici esterni).

## Esito sintetico

| Candidato | Copertura | Annualità | Fonte primaria | Storico | Esito |
|---|---:|---|---|---|---|
| Addizionale comunale IRPEF effettiva | 7/7 | 2025 | MEF — Dipartimento Finanze; Comune di Seravezza per conferma 2025 | disponibile | **PROMOSSO** |
| TARI, 3 persone / 100 m² | 5/7 materializzati | 2025 | Comuni / MEF + ARERA | potenziale pluriennale | **DA VALUTARE** |
| IMU, seconda abitazione standard | metodo definito; matrice 7/7 non chiusa | 2025 | MEF / Comuni | pluriennale | **DA VALUTARE** |
| Prezzi carburanti | 6/7 | fotografia 14/08/2026 | MIMIT — Osservaprezzi | trimestrale dal 2015 | **ESCLUSO** |
| Mensa scolastica | audit incompleto 7/7 | 2025/26 | Comuni | da verificare | **DA VALUTARE** |
| Costo gestione rifiuti CTOTab | variabile valida; righe 7/7 da materializzare | 2024 | ISPRA — Catasto Rifiuti | 2011–2024 | **DA VALUTARE** |
| Inflazione NIC | sovracomunale | serie annuale | ISTAT | dal 1996 | **PROMOSSO** |
| Storico reddito medio | 7/7 sulla definizione | obiettivo 2011–2024 | MEF — dichiarazioni IRPEF | annuale | **PROMOSSO** |
| Reddito a prezzi costanti | dipende dalle due serie precedenti | — | elaborazione Osservatorio su MEF + ISTAT | — | **DA VALUTARE** |

## 1. Addizionale comunale IRPEF — PROMOSSO

L'indicatore non confronta l'aliquota massima, ma l'**importo annuo dovuto** applicando aliquote, scaglioni ed esenzioni allo stesso reddito imponibile teorico.

Scenari: **20.000 € / 30.000 € / 50.000 €**. Sono abbastanza distanti da mostrare sia l'effetto delle soglie di esenzione sia quello delle strutture progressive senza trasformare le viste in indicatori separati.

### Importo calcolato, 2025

| Comune | 20.000 € | 30.000 € | 50.000 € |
|---|---:|---:|---:|
| Camaiore | 82,50 € | 144,50 € | 284,50 € |
| Forte dei Marmi | 0,00 € | 153,00 € | 283,00 € |
| Massarosa | 160,00 € | 240,00 € | 400,00 € |
| Pietrasanta | 150,00 € | 225,00 € | 375,00 € |
| Seravezza | 160,00 € | 240,00 € | 400,00 € |
| Stazzema | 160,00 € | 240,00 € | 400,00 € |
| Viareggio | 150,00 € | 225,00 € | 375,00 € |

Regola di calcolo: se l'imponibile non supera la soglia di esenzione l'addizionale è zero; superata la soglia, l'imposta si applica all'intero imponibile secondo l'aliquota unica o gli scaglioni del Comune.

Fonte principale: Dipartimento delle Finanze — banca dati dell'Addizionale comunale all'IRPEF. Per **Seravezza** l'interfaccia pubblica MEF non espone la riga 2025 nello stesso modo degli altri sei Comuni: la continuità per il 2025 è verificata sulla comunicazione ufficiale del Comune che conferma le aliquote IRPEF e sulla deliberazione consiliare n. 63 del 28/11/2024 depositata nel Portale del federalismo fiscale. L'eccezione di provenienza è conservata anche nello snapshot versionato.

## 2. TARI — DA VALUTARE

Lo standard **3 componenti + 100 m²** è metodologicamente valido e l'annualità comune individuata è il **2025**. La spesa deve includere quota fissa, quota variabile, **TEFA 5%** e componenti perequative ARERA 2025 (`UR1 + UR2 + UR3 = 7,60 € per utenza/anno`), evitando agevolazioni personali.

Tariffe 2025 già materializzate da fonti ufficiali:

- Camaiore: QF 0,969 €/m² + QV 298,664 €/anno;
- Viareggio: QF 1,0646 €/m² + QV 284,2633 €/anno;
- Massarosa: QF 1,297705857 €/m² + QV 379,6698985 €/anno;
- Seravezza: QF 1,14427 €/m² + QV 356,63966 €/anno;
- Stazzema: il prospetto ufficiale riporta 340,68 € per 3 persone / 100 m² prima di TEFA e componenti perequative.

Ulteriore verifica del 15 agosto: il Comune di Pietrasanta conferma una delibera tariffaria TARI 2025 e pubblica proprio l'esempio “100 m² con 3 persone”; l'HTML accessibile non espone però i coefficienti o il totale 2025 necessari a una ricostruzione verificabile. A Forte dei Marmi è confermata l'approvazione delle tariffe TARI 2025 in Consiglio comunale, ma non è stato ancora materializzato il prospetto numerico primario.

**Blocco:** per Forte dei Marmi e Pietrasanta non è stata ancora materializzata nel repository una tariffa 2025 primaria e riproducibile. L'indicatore non entra finché non è 7/7.

## 3. IMU — DA VALUTARE

La casa principale ordinaria è esclusa dal confronto. Per evitare di inventare una rendita catastale “tipica”, lo standard proposto è:

> **Seconda abitazione A/2 — base imponibile IMU standardizzata 100.000 €**

La base è identica nei sette Comuni e serve esclusivamente come benchmark di pressione fiscale. Il valore dell'indicatore sarebbe `100.000 € × aliquota comunale applicabile alla fattispecie standard`.

L'archivio MEF 2025 conferma che i prospetti IMU ufficiali sono disponibili per i Comuni verificati, compresi Forte dei Marmi e Stazzema; questo risolve il dubbio sulla disponibilità della fonte, non ancora quello sulla corretta selezione automatica della specifica fattispecie “seconda abitazione A/2” nei sette prospetti.

**Blocco:** prima della pubblicazione va chiusa la matrice ufficiale 2025 7/7 della specifica fattispecie. Nessuna aliquota viene dedotta per analogia o da annualità diverse.

## 4. Carburanti — ESCLUSO

La fonte MIMIT è adatta e consente uno storico trimestrale dal 2015, ma il perimetro comunale non supera il requisito di copertura. Alla fotografia del **14 agosto 2026**, Stazzema non presenta impianti attivi nell'anagrafica MIMIT; gli altri sei Comuni hanno campioni utilizzabili.

Non si pubblica quindi una mediana comunale 6/7, né si attribuisce a Stazzema un prezzo di un Comune vicino.

## 5. Mensa scolastica — DA VALUTARE

Le tariffe ufficiali già controllate mostrano strutture ISEE, esenzioni, sconti fratelli e condizioni residenti/non residenti molto diverse. L'audit 2025/26 non è ancora completo 7/7.

Il dato resterà fuori finché non sarà possibile costruire la **stessa famiglia teorica** nei sette Comuni senza forzature.

## 6. Costo del servizio rifiuti — DA VALUTARE

La variabile ISPRA corretta è **CTOTab — costo totale del servizio di igiene urbana, €/abitante/anno**. Il Catasto Rifiuti espone il periodo **2011–2024**.

La fonte specifica tuttavia che le statistiche di costo sono riferite al campione di Comuni. Prima di integrare il dato devono essere materializzate sette righe riferite al singolo Comune, non aggregazioni territoriali. La vista alternativa €/kg potrà essere uno switch dello stesso indicatore, non un indicatore aggiuntivo.

## 7. Inflazione — PROMOSSO, serie da materializzare

ISTAT rileva il NIC anche a livello subnazionale. **Lucca è un Comune capoluogo di rilevazione, non una serie della Provincia di Lucca.**

La dicitura corretta sarà quindi:

**Inflazione — Lucca città / Toscana / Italia**

Per il confronto annuale si userà la **variazione media annua del NIC**. Per deflazionare il reddito medio dei sette Comuni, il riferimento territoriale preferibile è **NIC Toscana**, perché Lucca città non è un proxy provinciale della Versilia.

La serie non entra nel draft finché i valori annuali non sono materializzati e verificati dopo il passaggio alla classificazione ECOICOP v2.

## 8. Storico redditi — PROMOSSO, estrazione da materializzare

La definizione corrente del sito è stata verificata nel catalogo canonico:

**reddito complessivo dichiarato / numero di dichiaranti con reddito complessivo**.

Non risultano trasformazioni ulteriori. Lo storico MEF dovrà usare anno per anno le stesse due variabili. Obiettivo: **2011–2024**, fermando o marcando la serie in caso di una rottura definitoria reale.

## 9. Reddito reale — DA VALUTARE

Solo dopo aver materializzato e validato entrambe le serie verrà valutato lo switch:

**Nominale | A prezzi costanti**

La seconda vista sarà denominata **Reddito medio dichiarato a prezzi costanti**, con NIC Toscana, anno base e formula esplicitati. Non sarà conteggiata come indicatore autonomo e non sarà chiamata “potere d'acquisto delle famiglie”.

## Decisione di implementazione del draft

In questa prima materializzazione entra **un solo nuovo indicatore**: `municipalIrpef`.

TARI, IMU, mensa e CTOTab restano esclusi dal codice pubblico finché non superano il 7/7. Carburanti è escluso metodologicamente. Inflazione e storico redditi sono promossi ma attendono la materializzazione completa delle serie ufficiali prima di essere integrati.
