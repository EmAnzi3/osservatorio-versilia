# Audit copertura dati · Lotto A

Stato: **audit in corso — nessuna modifica al catalogo pubblico**  
Branch: `agent/data-audit-lotto-a`  
Base: `main` @ `07dcb687aad0f024f582a4730f9330a64dcdaada`

## Contratto di coerenza

Questo audit precede qualsiasi aggiunta al catalogo. Un candidato entra nel sito solo se supera sia la verifica della fonte sia il contratto tecnico dell’Osservatorio.

1. **Una sola sorgente canonica dei valori**: `data/site-data.json` + registry/stato fonti esistenti; nessun secondo sistema parallelo.
2. **Grafici esistenti = componenti esistenti**: serie storiche e confronti devono usare `OVUXHistory` (`assets/ux-history-core.js` / `assets/ux-history.js`). Non sono ammessi tooltip, renderer, palette o scale “simili” creati ad hoc.
3. **Tooltip unico**: dove è previsto un tooltip storico, va usato lo stesso `historyPointMarkup()` e lo stesso `wireHistoryTooltips()` del sito. Un indicatore nuovo non può introdurre un proprio tooltip.
4. **Formattazione unica**: unità e valori passano da `formatValue()` del toolkit canonico; eventuali nuove unità si aggiungono al formatter comune, non nelle singole pagine.
5. **Ordine dei Comuni alfabetico; nessun ranking/podio**.
6. **Copertura esplicita**: `n.d.` = dato pertinente ma non disponibile; `n.a.` = indicatore non applicabile al Comune (es. balneazione per Comune senza costa).
7. **Serie annuali complete**: niente YTD/periodi parziali presentati come anni completi.
8. **Nessun indicatore nuovo solo per riempire un rapporto**: deve avere senso autonomo nel catalogo oppure essere dichiarato dataset di approfondimento.
9. **Coerenza tematica**: nessuna variabile viene collocata in un tema solo per evitare di creare/ridefinire una struttura. I casi strutturali vengono decisi prima dell’implementazione.

## Stati audit

- **GO fonte**: fonte ufficiale, granularità e aggiornamento sono già adeguati; resta l’estrazione 7/7 e il test di integrazione.
- **VERIFY**: fonte promettente ma prima serve verificare copertura effettiva dei sette Comuni, definizione o stabilità della serie.
- **HOLD struttura**: il dato è valido, ma la collocazione nel catalogo richiede una decisione strutturale.
- **NO-GO**: non sufficientemente solido/comparabile; non si implementa.

## Matrice Lotto A

| # | Candidato | Tema proposto | Tipo | Fonte ufficiale | Ultimo riferimento verificato | Copertura prevista | Stato | Nota di implementazione |
|---|---|---|---|---|---|---|---|---|
| 1 | Natalità, mortalità e saldo naturale | Demografia | **Indicatore composito** | Istat Demo · bilancio/dinamica demografica | dati demografici comunali aggiornati annualmente | 7/7 | **GO fonte** | Un solo indicatore “Dinamica naturale”, non tre card separate; serie storiche con `OVUXHistory`. |
| 2 | Quota popolazione 80+ | Demografia | Indicatore | Istat Demo / A misura di Comune | 2024 in A misura di Comune; Demo più aggiornato per età | 7/7 | **GO fonte** | Nuova misura autonoma; non va mescolata alle fasce 0-14/15-64/65+ perché 80+ è un sottoinsieme di 65+. |
| 3 | Indice di dipendenza strutturale + dipendenza anziani | Demografia | **Indicatore composito** | Istat Demo / A misura di Comune | serie comunali disponibili | 7/7 | **GO fonte** | Due componenti nello stesso indicatore; formattazione `index`; storico canonico. |
| 4 | Contribuenti IRPEF rapportati alla popolazione adulta | Economia | Indicatore derivato | MEF dichiarazioni + Istat popolazione per età | a.i. 2024 (pubblicato 23/04/2026) | 7/7 | **VERIFY** | Definire prima il denominatore corretto (15+, 18+ o residenti totali). Non pubblicare una misura metodologicamente arbitraria. |
| 5 | Quota del reddito dichiarato proveniente da pensioni | Economia | Indicatore derivato | MEF · redditi e principali variabili IRPEF comunali | a.i. 2024 | 7/7 | **GO fonte** | Rapporto tra ammontare reddito da pensione e reddito complessivo; denominatore e formula espliciti. |
| 6 | Dipendenti comunali per 1.000 abitanti | da decidere: Istituzioni/servizi | Indicatore | RGS Conto Annuale | 2024 | 7/7 | **GO fonte / HOLD struttura** | RGS pubblica già lo stesso indicatore. Non forzarlo dentro “Bilanci” senza decisione sul perimetro del tema. |
| 7 | Turnover del personale comunale | da decidere: Istituzioni/servizi | Indicatore/composito | RGS Conto Annuale · assunti e cessati | 2024 | 7/7 attesa | **VERIFY / HOLD struttura** | Verificare la metrica più robusta per piccoli enti e casi con zero cessazioni; evitare rapporto instabile non interpretabile. |
| 8 | Età media / struttura per età del personale comunale | da decidere: Istituzioni/servizi | Indicatore/composito | RGS Conto Annuale · età | 2024 | 7/7 attesa | **VERIFY / HOLD struttura** | Preferibile un composito (età media + quota 55+/60+) se i microdati consentono copertura omogenea. |
| 9 | Servizi comunali disponibili integralmente online | da decidere: Istituzioni/servizi | Indicatore | Regione Toscana / Istat ICT PA | dato definitivo indicato dalla Regione: 2022 | 7/7 attesa | **VERIFY / HOLD struttura** | Fonte ufficiale ma aggiornamento troppo vecchio: cercare un rilascio più recente prima di implementare. |
| 10 | Edifici scolastici con agibilità/SCIA | Istruzione | Indicatore | MIM Open Data · sicurezza edifici scolastici | a.s. 2024/25, dataset pubblicato 06/08/2025 | 7/7 attesa | **GO fonte** | Aggregazione per edificio/comune; distinguere SI/NO/IN PARTE/NON DEFINITO. |
| 11 | Edifici scolastici con CPI o SCIA antincendio | Istruzione | Indicatore | MIM Open Data · sicurezza edifici scolastici | a.s. 2024/25 | 7/7 attesa | **GO fonte** | Definire “regolare antincendio” senza sommare impropriamente CPI e SCIA; conservare i due campi nel dataset di dettaglio. |
| 12 | Accessibilità degli edifici scolastici | Istruzione | Indicatore | MIM Open Data · barriere architettoniche | a.s. 2024/25 | 7/7 attesa | **GO fonte** | Percentuale edifici con accorgimenti; “NON DEFINITO” escluso dal denominatore o mostrato separatamente, da decidere in metodologia. |
| 13 | Spesa effettiva per servizi sociali per residente | Salute/Comunità: da decidere | Indicatore | Istat · Spesa dei Comuni per servizi sociali | 2022, tavole comunali pubblicate 24/09/2025 | 7/7 attesa | **GO fonte** | Non duplicare la missione sociale di bilancio: questa misura riguarda servizi/interventi sociali rilevati da Istat ed è concettualmente diversa. |
| 14 | Copertura servizi educativi 0–2 anni | Istruzione | Indicatore | Istat · nidi e servizi integrativi | a.e. 2023/24, pubblicato 03/02/2026 | da verificare | **VERIFY** | Il tasso nazionale di risposta comunale è 79,9%; verificare esplicitamente i sette Comuni prima del GO. |
| 15 | Popolazione insistente diurna per studio/lavoro | Mobilità e infrastrutture | Indicatore/composito | Istat · statistica sperimentale Popolazione insistente | 2021–2023, pubblicato 10/06/2026 | comunale | **GO fonte** | Valutare rapporto insistente/residenti e saldo utenti diurni; non confondere con pendolarismo già presente. |
| 16 | Aziende agricole | Ambiente · Agricoltura e territorio | Indicatore | Istat · Censimento Agricoltura | 2020 | 7/7 | **GO fonte** | Dato strutturale censuario; frequenza irregolare dichiarata. |
| 17 | SAU sul territorio / superficie agricola utilizzata | Ambiente · Agricoltura e territorio | Indicatore | Istat · Censimento Agricoltura | 2020 | 7/7 | **GO fonte** | Verificare se usare SAU assoluta, SAU/superficie comunale o entrambe come composito; non duplicare la quota biologica esistente. |
| 18 | Qualità delle acque di balneazione: quota aree/km “eccellenti” | Ambiente · Costa e mare | Indicatore | ARPAT | classificazione 2010–2024 | 4/7 applicabili | **GO fonte** | Camaiore, Forte dei Marmi, Pietrasanta, Viareggio = dato; Massarosa, Seravezza, Stazzema = **n.a.**. |
| 19 | Non conformità dei campionamenti di balneazione | Ambiente · Costa e mare | Indicatore | ARPAT | campionamenti disponibili fino alla stagione 2025 | 4/7 applicabili | **GO fonte** | Preferire “campioni non conformi / campioni effettuati” o evento di superamento, con denominatore esplicito; 3 Comuni n.a. |
| 20 | Prestiti bibliotecari per residente | nuovo possibile tema Cultura | Indicatore | Regione Toscana · monitoraggio biblioteche / indicatori IFLA | serie storica dal 1998, aggiornamento annuale | comunale | **GO fonte / HOLD struttura** | Non inserirlo in “Comunità” solo per comodità. Valutare se esistono abbastanza variabili culturali solide da aprire un tema Cultura coerente. |
| 21 | Piramide età × sesso | Demografia | **Dataset di approfondimento** | Istat Demo | 2019–2026 | 7/7 | **GO fonte** | Non nuova card: dataset per rapporti e approfondimenti, derivato dagli stessi dati demografici canonici. |
| 22 | Cittadinanze / paesi di nascita | Demografia | **Dataset di approfondimento** | Istat Demo | 2002–2025 | 7/7 | **GO fonte** | Non moltiplicare indicatori per nazionalità; dataset strutturato per breakdown e rapporti. |
| 23 | Redditi dichiarati per fonte e fasce complete | Economia | **Dataset di approfondimento** | MEF · Statistiche dichiarazioni | a.i. 2024 | 7/7 | **GO fonte** | Integrare l’attuale reddito/distribuzione; evitare card duplicate per ogni fonte reddituale. |

## Fonti verificate in questa fase

### Istat
- Demo — demografia in cifre: https://demo.istat.it/
- Popolazione residente per età, sesso e stato civile: https://demo.istat.it/app/?i=POS&l=it
- Popolazione per cittadinanza / paese di nascita: https://demo.istat.it/app/?i=RCS&l=it
- A misura di Comune, aggiornamento 26/05/2026: https://www.istat.it/statistica-sperimentale/aggiornamento-degli-indicatori-del-sistema-informativo-a-misura-di-comune/
- Popolazione insistente 2021–2023: https://www.istat.it/statistica-sperimentale/popolazione-insistente-per-studio-e-lavoro-aggiornamento-triennio-2021-2023/
- Spesa dei Comuni per servizi sociali 2022: https://www.istat.it/comunicato-stampa/la-spesa-dei-comuni-per-i-servizi-sociali-anno-2022/
- Nidi e servizi integrativi 2023/24: https://www.istat.it/comunicato-stampa/offerta-di-nidi-e-servizi-integrativi-per-la-prima-infanzia-anno-educativo-2023-2024/
- Censimento Agricoltura 2020: https://www.istat.it/notizia/censimento-agricoltura-2020-online-i-principali-dati/

### MEF / RGS
- MEF — Statistiche sulle dichiarazioni, redditi IRPEF comunali a.i. 2024: https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?opendata=yes
- RGS — Conto Annuale, dati pubblicati: https://contoannuale.rgs.mef.gov.it/web/sicosito/dati-pubblicati
- RGS — Dipendenti / abitanti per Comune: https://contoannuale.rgs.mef.gov.it/web/sicosito/dipendenti/abitanti-comune-acc
- RGS — Download microdati: https://contoannuale.rgs.mef.gov.it/web/sicosito/download

### MIM
- Open Data Edilizia scolastica: https://dati.istruzione.it/opendata/opendata/catalogo/elements1/?area=Edilizia+Scolastica
- Sicurezza edifici (agibilità, CPI, SCIA): https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?datasetId=DS0171EDICONSICUREZZASTA2021
- Barriere architettoniche: https://dati.istruzione.it/opendata/opendata/catalogo/elements1/leaf/?area=Edilizia+Scolastica&datasetId=DS0156EDISUPBARARCSTA2021

### Regione Toscana / ARPAT
- Indicatori comunali per le politiche locali, dati 2024: https://www.regione.toscana.it/statistiche/indicatori-comunali-per-le-politiche-locali
- Biblioteche e indicatori IFLA: https://www.regione.toscana.it/-/il-valore-delle-biblioteche-pubbliche-di-ente-locale-e-della-cooperazione-bibliotecaria
- ARPAT — classificazioni balneazione 2010–2024: https://www.arpat.toscana.it/datiemappe/aree-di-balneazione-classificazioni/
- ARPAT — dati campionamenti 2011–2025: https://www.arpat.toscana.it/datiemappe/balneazione-in-toscana-dati-relativi-alle-stagioni-precedenti/

## Prossimo gate prima dell’implementazione

Per ogni riga `GO fonte` / `VERIFY` va prodotta una matrice 7×N con:

- codice Comune;
- disponibilità effettiva del dato;
- ultimo anno;
- anni di serie storica realmente omogenei;
- unità;
- formula derivata, se presente;
- benchmark Toscana/Italia disponibile e omogeneo;
- gestione `n.d.` / `n.a.`;
- fonte primaria e licenza;
- modalità di aggiornamento;
- componente grafico canonico da riusare (`OVUXHistory` storico/confronto o componente composito già esistente).

**Nessuna modifica a `data/site-data.json` viene effettuata finché questo gate non è superato.**
