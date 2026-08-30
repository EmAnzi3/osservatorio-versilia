# Lotto 4 · Ambiente e acqua — esito audit e contratto di implementazione

Data: 29 agosto 2026  
Release proposta: **v1.24.0**  
Collocazione: **Ambiente → Acqua e bonifiche**  
Temi complessivi: **11** (invariati)

## Decisione

Il lotto produce **3 nuovi indicatori canonici**:

1. `waterNetworkLosses` — **Perdite della rete idrica**;
2. `drinkingWaterQuality` — **Qualità dell’acqua potabile**;
3. `remediationProceedings` — **Siti oggetto di procedimento di bonifica**, con lettura `Iter attivi / Iter chiusi`.

Restano **rinviati**, senza proxy o stime:

- acqua erogata pro capite/giorno;
- copertura fognatura;
- copertura depurazione.

## Perdite della rete idrica

Fonte: Istat, dataflow comunale sulla distribuzione di acqua potabile.  
File verificato SHA-256: `337f83c658af4a92f9d677c880bf887a91a458b19aa57a0c47757651064790bf`.

Anni comunali pubblici disponibili per i sette Comuni: **2012, 2015, 2018**. Non si interpolano gli anni mancanti.

Formula comunale:

`(acqua immessa − acqua erogata per usi autorizzati) / acqua immessa × 100`

La Versilia è calcolata sul rapporto tra le somme dei volumi, **non** come media semplice delle sette percentuali. Nel 2018: acqua immessa 22.502 migliaia m³; acqua erogata 13.437 migliaia m³; perdite **40,2853%**.

Il sito deve indicare chiaramente che **2018 è l’ultimo dato comunale Istat pubblico disponibile** e non rappresenta una fotografia corrente del 2026.

## Qualità dell’acqua potabile

Fonte: GAIA S.p.A., Laboratorio Analisi.  
Estrazione principale SHA-256: `97d6dbe6a9f3549fe9d43c7bb2bf832ee2e1819effa2bf1b7b69fe46a37c83eb`.  
Recupero specifico Pian di Conca SHA-256: `fd938a487dccf6f9ed64325f2df855e36c2706c75ffd45cedd8c6ee607c612f3`.

Copertura: **7/7 Comuni, 70/70 località, 17 parametri per località, 1.190 valori**, tutti riferiti al **2° semestre 2025**.

Non viene costruita alcuna media comunale e nessun indice sintetico. La scheda comunale offre un selettore delle località GAIA e mostra per ogni parametro: unità, valore medio e limite/riferimento. Le diciture `valore consigliato` restano distinte dai limiti normativi; valori come `< 0,050` restano testuali.

## SISBON

Fonte: Regione Toscana / ARPAT, export pubblico SISBON collegato a GEOscopio.  
CSV SHA-256: `e5bd50e5b6a4a88b0f7bec0762b8719b69064ae1841bdbde925c5501e363dbcb`.  
ZIP geografico SHA-256: `3a12195db552d4a7101f1a598cb5cda4010100363e658b38d6f2db82582ed206`.

Il perimetro Versilia contiene **152 codici regionali univoci**: **56 iter attivi** e **96 iter chiusi**. La chiave di deduplicazione è `codice_regionale`; coordinate coincidenti non autorizzano a fondere procedimenti distinti.

Conteggi comunali attivi/chiusi: Camaiore 9/22; Forte dei Marmi 10/11; Massarosa 6/10; Pietrasanta 10/13; Seravezza 3/6; Stazzema 3/4; Viareggio 15/30.

La card usa la formulazione **“Siti oggetto di procedimento di bonifica”**: un procedimento SISBON non equivale automaticamente a un sito attualmente contaminato.

## Candidati rinviati

**Acqua erogata pro capite/giorno:** i volumi comunali sono disponibili fino al 2018, ma il lotto non congela un denominatore demografico 2018 senza una verifica dedicata della serie intercensuaria usata da Istat.

**Copertura fognatura:** non è disponibile un dataset pubblico omogeneo 7/7 con residenti serviti e denominatore comparabile. Non si usa il rapporto tra utenze fognarie e utenze acquedotto come proxy.

**Copertura depurazione:** non è disponibile un dataset pubblico omogeneo 7/7 con residenti serviti. Abitanti equivalenti e capacità degli impianti non sono sostituti ammessi.

## Regole UI e dati

- nessun testo o valore a meno di 14 px dai bordi dei nuovi pannelli;
- nessun contenuto tagliato o overflow orizzontale non gestito;
- percentuali espresse sempre con `%`, senza `punti`, `punti percentuali` o `p.p.`;
- `n.d.` non viene convertito in zero;
- nessuna interpolazione;
- aggregati percentuali ricostruiti sui numeratori/denominatori compatibili;
- snapshot e impronte delle fonti conservati in repository.
