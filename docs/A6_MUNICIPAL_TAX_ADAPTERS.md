# A6 — fiscalità comunale standardizzata 2025

Tre carrier, 7/7 Comuni, senza acquisizioni o variazioni di dati/UI. Snapshot normalizzati già congelati: `costi-fiscalita-validated-2026-08.json` e `costi-fiscalita-redditi-draft-2026-08.json`. Byte e contenuto decodificato verificati con hash distinti; riconciliazione di ogni riga, scenario, companion e media pubblicata. I documenti amministrativi originali non sono rigiocati: la prova riguarda le estrazioni normalizzate versionate, con URL/provenienza originari conservati.

| Carrier | Dimensioni | Scenario e metodo |
|---|---|---|
| `tariStandardHousehold` | `total` | Domestica residente, 3 persone, 100 m², nessuna agevolazione personale. Base e TEFA 5% arrotondati separatamente ai centesimi, più 7,60 € ARERA. Stazzema usa la base ufficiale 340,68 €, senza inventare quota fissa/variabile. |
| `municipalImuStandard` | `total`, `ratePercent` | Seconda abitazione A/2, categoria Altri fabbricati, base imponibile IMU identica di 100.000 €. Non è il prezzo di mercato né una rendita catastale. Importo e aliquota distinti. |
| `municipalIrpef` | `total`, `income:20000`, `income:30000`, `income:50000`, `effectiveRate:20000` | `total` alias dello scenario 20.000 €. Se entro la soglia di esenzione, zero; superata la soglia, aliquota unica o scaglioni su tutto l’imponibile. Companion effettivo = importo / 20.000 × 100, distinto dall’aliquota marginale. |

Le aliquote IRPEF di Seravezza derivano dalla conferma comunale della deliberazione 63 del 28 novembre 2024 depositata nel Portale del federalismo fiscale: non si attribuisce alla riga pubblica MEF una prova che lo snapshot non contiene. Le soglie `null` di Seravezza/Stazzema non diventano un’affermazione generale sull’assenza di esenzioni: si riconciliano esclusivamente i tre importi congelati, senza esporre un calcolatore per redditi arbitrari.

Forte dei Marmi: zero a 20.000 € è valido. A 30.000 € il calcolo congelato è 28.000 × 0,5% + 2.000 × 0,65% = 153 €. Camaiore a 20.000 €: 15.000 × 0,35% + 5.000 × 0,6% = 82,50 €, senza sottrarre la soglia come franchigia. Escluse IRPEF statale/regionale, altre fattispecie IMU, riduzioni personali e scenari TARI differenti.

Confronto e graduatoria descrittivi per la medesima dimensione/scenario. Media aritmetica comunale: ogni Comune pesa uguale; non rappresenta famiglia media, gettito, pressione fiscale effettiva o qualità del servizio. Periodo unico 2025; anche la richiesta esplicita 2025 mantiene provenienza puntuale. Nessun riporto automatico al 2026. Serie, variazioni, trend, pooling, anomalie, benchmark geografici e coppie non revisionate rifiutati. Nessun giudizio causale o raccomandazione politica automatica.

Prove indipendenti: 56 celle fisse (incluso alias), stesso valore con periodo esplicito, zeri/pari merito/unità/puntatori; attacchi a anno, fonte, identità, valori booleani, formula, scenari, storico fittizio, companion, aggregato e hash. Corpus precedente di 1.850 domande invariato; 160 casi aggiuntivi. Audit e performance in `reports/a6-municipal-tax/`. Quick prima di push, Full completo locale e CI canonica prima della prontezza. A6.4 resta parziale; A6.5–A6.6 aperte, A7 non avviata.
