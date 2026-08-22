# Radar Opportunità Versilia — prototipo

## Obiettivo

Verificare se un collettore automatico può individuare opportunità finanziarie realmente utilizzabili dai sette Comuni della Versilia senza introdurre rumore o false certezze.

Il prototipo è intenzionalmente separato dalla parte pubblica del sito: non crea route, non modifica `data/site-data.json`, non entra nella sitemap e non pubblica automaticamente opportunità.

## Perimetro v0.2

Comuni: Camaiore, Forte dei Marmi, Massarosa, Pietrasanta, Seravezza, Stazzema e Viareggio.

Fonti del campione:

1. Regione Toscana — bandi aperti;
2. Fondazione Cassa di Risparmio di Lucca — bandi in corso;
3. PA digitale 2026 — dataset open data degli avvisi selezionato nel prototipo.

La v0.2 aggiunge tre livelli di sicurezza rispetto alla v0.1:

- ammissibilità calcolata separatamente per ciascun Comune;
- separazione tra output operativo e coda interna `review`;
- controllo esplicito della freschezza delle fonti.

## Regola di sicurezza sull'ammissibilità

Il motore non usa inferenze generative per dichiarare ammissibile un Comune.

Per ciascuna opportunità e per ciascuno dei sette Comuni viene prodotto uno stato:

- `eligible`: il Comune risulta compreso nel perimetro rilevato;
- `conditional`: il Comune può essere ammissibile, ma esiste almeno una condizione documentale da verificare;
- `not_eligible`: una regola territoriale esplicita esclude il Comune;
- `review`: i dati disponibili non bastano per decidere in sicurezza.

Lo stato aggregato dell'opportunità non sostituisce la matrice Comune-per-Comune.

## Resolver territoriale v0.2

La prima regola territoriale strutturata implementata riguarda la **Toscana Diffusa**.

Il profilo configurato per i sette Comuni è:

| Comune | Toscana Diffusa | Trattamento v0.2 |
| --- | --- | --- |
| Camaiore | TD* / parziale | `conditional`: occorre verificare che l'intervento ricada nella porzione montana |
| Forte dei Marmi | no | `not_eligible` per bandi riservati alla Toscana Diffusa |
| Massarosa | no | `not_eligible` |
| Pietrasanta | no | `not_eligible` |
| Seravezza | sì | `eligible` |
| Stazzema | sì | `eligible` |
| Viareggio | no | `not_eligible` |

Il profilo è mantenuto in `data/opportunity-sources.json` con il riferimento alla classificazione regionale. La regola non viene estesa per analogia ad altri bandi: eventuali soglie demografiche, territoriali o di partenariato non riconosciute restano `conditional` o `review`.

## Output v0.2

L'output JSON è diviso in due insiemi:

- `opportunities`: opportunità operative con almeno un Comune `eligible` o `conditional`;
- `reviewQueue`: coda interna di elementi non abbastanza chiari da esporre.

Ogni opportunità operativa contiene `municipality_eligibility`, con stato e motivazione per ciascuno dei sette Comuni.

La coda `review` non è materiale destinato a una futura pagina pubblica: serve per affinare parser e regole senza mostrare rumore all'utente.

## Freschezza delle fonti

Ogni fonte ha una soglia `freshnessMaxDays`. Il probe rileva la data più recente disponibile nel feed/pagina e assegna uno stato:

- `current`: la fonte mostra attività entro la soglia;
- `stale`: la fonte è raggiungibile ma i dati risultano troppo vecchi;
- `unknown`: non è possibile ricavare una data attendibile.

Essere HTTP-raggiungibile non è quindi più sufficiente per considerare una fonte affidabile.

## Robustezza di rete

Il live probe applica timeout e retry limitati configurabili per fonte. Un errore persistente resta bloccante e rende rosso il job: il radar non riutilizza silenziosamente dati vecchi e non sostituisce una fonte non raggiungibile con inferenze.

## Collaudo live v0.2 — 21 agosto 2026

GitHub Actions, riferimento temporale `Europe/Rome`.

### Test automatici

Tre suite, tutte verdi:

- collector base: 6 test;
- filtro di qualità: 2 test;
- resolver v0.2: 6 test.

**Totale: 14 test verdi.**

### Live probe finale

- candidati raccolti: **42**;
- opportunità operative: **8**;
  - 7 `eligible`;
  - 1 `conditional`;
- coda interna `review`: **18**;
- casi non comunali scartati automaticamente: **16**.

Rispetto alla v0.1, che esponeva tutti i 42 elementi e ne lasciava 34 in `review`, la v0.2 limita l'output operativo a 8 elementi e dimezza quasi la coda di verifica.

### Fonti

| Fonte | Operative | Review interna | Scartate | Freschezza |
| --- | ---: | ---: | ---: | --- |
| Regione Toscana | 6 | 18 | 16 | `current` — dato più recente 19 agosto 2026 |
| Fondazione CR Lucca | 2 | 0 | 0 | `current` — dato più recente 16 giugno 2026 |
| PA digitale 2026 | 0 | 0 | 0 | `stale` — dato più recente 30 gennaio 2026 |

Il controllo di freschezza rende esplicito che il dataset PA digitale scelto per questo prototipo non è sufficiente come fonte corrente, pur essendo tecnicamente raggiungibile.

## Opportunità operative rilevate nel probe

1. **Bando Amianto Edifici Pubblici 2026** — Regione Toscana — tutti i sette Comuni `eligible` — scadenza 31 agosto 2026.
2. **Nidi di qualità 2026-2027** — Regione Toscana — tutti i sette Comuni `eligible` — scadenza 4 settembre 2026.
3. **Progett-Azioni** — Fondazione CR Lucca — tutti i sette Comuni `conditional` per il requisito di partenariato — scadenza 11 settembre 2026.
4. **Progettare per il futuro – opere pubbliche** — Fondazione CR Lucca — tutti i sette Comuni `eligible` — scadenza 11 settembre 2026.
5. **Sostegno a progetti dedicati a San Francesco, Collodi e Alluvione di Firenze** — Regione Toscana — destinatari comunali rilevati — scadenza 18 settembre 2026.
6. **Comuni Toscana Diffusa – strutture di servizio pubbliche** — Regione Toscana — Seravezza e Stazzema `eligible`, Camaiore `conditional`, Forte dei Marmi, Massarosa, Pietrasanta e Viareggio `not_eligible` — scadenza 30 ottobre 2026.
7. **Bando biotrituratori elettrici 2026** — Regione Toscana — destinatari comunali rilevati; scadenza non ancora estratta automaticamente.
8. **Buoni scuola anno 2026** — Regione Toscana — destinatari comunali rilevati; scadenza non ancora estratta automaticamente.

L'etichetta `eligible` indica qui l'ammissibilità del soggetto Comune rispetto alle regole rilevate. Non certifica automaticamente che ogni possibile progetto del Comune soddisfi tutte le condizioni tecniche, finanziarie o patrimoniali del bando.

## Limiti residui

### 1. Coda review ancora da ridurre

18 elementi restano da verificare internamente. È un miglioramento netto rispetto ai 34 della v0.1, ma prima di ampliare molto le fonti conviene classificare ulteriormente i pattern regionali più frequenti.

### 2. Requisiti di progetto

La v0.2 risolve già destinatario e alcune condizioni territoriali. Restano da strutturare, quando presenti:

- soglie di popolazione;
- proprietà o disponibilità dell'immobile;
- localizzazione puntuale dell'intervento;
- partenariati obbligatori;
- dimensioni e categorie dell'ente;
- cofinanziamento e massimali;
- requisiti tecnici specifici del progetto.

### 3. Scadenze non sempre esposte in formato uniforme

Alcune opportunità regionali vengono riconosciute come comunali ma la scadenza non è ancora estratta. Una futura esposizione pubblica non dovrà trattarle come complete finché questo campo non è verificato.

## Criteri per la v0.3

Prima della pagina pubblica `/opportunita/`:

1. ridurre ancora la coda `review` usando regole documentali, non euristiche aggressive;
2. aggiungere un livello `data_quality`/completezza per impedire la pubblicazione di opportunità con campi critici mancanti;
3. strutturare i requisiti di progetto più ricorrenti;
4. sostituire o affiancare la fonte PA digitale stale con una fonte corrente verificabile;
5. eseguire un backtest 60–90 giorni su opportunità note;
6. solo dopo ampliare a FESR/FSE+, GSE, ANCI, Ministeri, LIFE/UE e Interreg.

## Stato

**v0.2 validata come base tecnica nella Draft PR #82. Nessuna route pubblica, nessun merge e nessuna pubblicazione automatica.**
