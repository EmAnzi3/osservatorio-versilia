# Radar Opportunità Versilia — v0.2.1

## Perché nasce la v0.2.1

Il collaudo umano della v0.2 ha mostrato che la sola presenza dei Comuni tra i soggetti ammessi non basta a definire una vera opportunità per la Versilia.

Una segnalazione operativa deve superare quattro verifiche distinte:

1. **ammissibilità del richiedente** — il Comune può presentare domanda o aderire?
2. **ruolo del Comune** — richiedente diretto, partner, soggetto attuatore/intermediario oppure nessun ruolo?
3. **ammissibilità geografica** — il territorio del Comune rientra nel perimetro del bando?
4. **pertinenza territoriale** — l'oggetto finanziato ha un nesso concreto con la Versilia?

La v0.2.1 non usa inferenze generative per risolvere questi punti. Le eccezioni validate sono registrate in `data/opportunity-rules-v021.json`, con regola, evidenza e URL della fonte.

## Nuovi campi

Per le opportunità validate vengono mantenuti, oltre alla matrice Comune-per-Comune:

- `applicant_eligibility`;
- `applicant_type`;
- `municipality_role`;
- `final_beneficiaries`;
- `partnership_required`;
- `project_requirements`;
- `geographic_scope`;
- `geographic_eligibility`;
- `territorial_relevance`;
- `actionable_for_municipality`;
- `eligibility_evidence`;
- `rule_id`.

Un nuovo caso che il parser considera genericamente `eligible` o `conditional` **non entra più automaticamente nell'output operativo** se manca una regola documentale v0.2.1 su ruolo/geografia. Resta nella `reviewQueue` interna.

## Casi guida del collaudo umano

### Bando parcheggi 2026 — falso negativo corretto

La v0.2 lo lasciava in `review`. L'atto regionale indica invece esplicitamente i **Comuni toscani** come soggetti beneficiari.

Trattamento v0.2.1:

- richiedente: Comune;
- ruolo: `direct_applicant`;
- geografia: Toscana;
- pertinenza: `direct`;
- esito: `eligible` per tutti i sette Comuni, fermo restando il rispetto dei requisiti progettuali.

### Emergenza abitativa / residenza sociale — falso negativo corretto

L'avviso contiene una linea effettivamente lavorabile dai Comuni, ma subordinata alle specifiche casistiche immobiliari previste.

Trattamento v0.2.1:

- ruolo: `direct_applicant`;
- esito: `conditional`;
- geografia: Toscana;
- pertinenza: `direct`.

### Biotrituratori elettrici 2026 — falso positivo corretto

I beneficiari sono cittadini proprietari/comproprietari di terreni con specifici requisiti. Inoltre nessuno dei sette Comuni della Versilia rientra nei 31 territori ammessi.

Trattamento v0.2.1:

- ruolo Comune: `none`;
- `applicant_eligibility`: `not_eligible`;
- `geographic_eligibility`: `not_eligible`;
- `territorial_relevance`: `none`;
- fuori dall'output operativo.

### San Francesco / Collodi / Alluvione di Firenze — pertinenza geografico-tematica

Il fatto che un ente toscano possa essere formalmente ammesso non rende automaticamente il bando una vera opportunità Versilia. La linea è dedicata a tre ricorrenze specifiche e, in assenza di un nesso documentato con uno dei sette Comuni, non deve occupare l'output operativo.

Trattamento v0.2.1:

- l'ammissibilità formale del richiedente resta separata;
- `territorial_relevance`: `none` senza un nesso Versilia;
- `actionable_for_municipality`: `false`;
- il caso può riemergere solo se viene documentato un collegamento concreto con Versilia o con uno dei sette Comuni.

### Buoni scuola 2026 — beneficiario finale diverso dal ruolo comunale

Le famiglie sono i beneficiari finali, ma il Comune/Unione è soggetto proponente e attuatore previsto dall'avviso.

Trattamento v0.2.1:

- `municipality_role`: `implementing_body`;
- `final_beneficiaries`: famiglie;
- opportunità operativa per l'amministrazione.

### Toscana Diffusa

Resta valida la matrice della v0.2:

- Seravezza: `eligible`;
- Stazzema: `eligible`;
- Camaiore: `conditional` perché TD*, limitatamente alla porzione montana;
- Forte dei Marmi, Massarosa, Pietrasanta e Viareggio: `not_eligible`.

## Collaudo automatico

La v0.2.1 aggiunge 8 test specifici ai 14 già presenti:

- promozione documentale del Bando parcheggi;
- esclusione Biotrituratori per ruolo e geografia;
- esclusione del bando celebrativo senza nesso Versilia;
- riattivazione del bando celebrativo in presenza di nesso documentato;
- distinzione tra soggetto attuatore e beneficiario finale per Buoni scuola;
- promozione condizionata dell'avviso sull'emergenza abitativa;
- ruolo di partner per Progett-Azioni;
- ritorno in review dei nuovi casi privi di regola documentale.

Totale suite: **22 test**.

## Live probe del 21 agosto 2026

Il primo probe v0.2.1 completo ha prodotto:

- candidati: **42**;
- output operativo: **8**;
  - 6 `eligible`;
  - 2 `conditional`;
- review interna: **16**;
- scartati/non operativi: **18**;
- regole v0.2.1 applicate: **10**;
- promossi dalla review: **2**;
- esclusi per ruolo: **1**;
- esclusi per pertinenza geografica: **1**.

Per fonte:

| Fonte | Operative | Review | Scartate/non operative | Freschezza |
| --- | ---: | ---: | ---: | --- |
| Regione Toscana | 6 | 16 | 18 | `current` — 19/08/2026 |
| Fondazione CR Lucca | 2 | 0 | 0 | `current` — 16/06/2026 |
| PA digitale 2026 | 0 | 0 | 0 | `stale` — 30/01/2026 |

## Otto opportunità operative dopo il collaudo umano

1. Bando Amianto Edifici Pubblici 2026 — `direct_applicant`;
2. Nidi di qualità 2026-2027 — `direct_applicant`;
3. Progett-Azioni — `partner`, `conditional`;
4. Progettare per il futuro – opere pubbliche — `direct_applicant`;
5. Comuni Toscana Diffusa – strutture di servizio pubbliche — matrice territoriale Comune-per-Comune;
6. Bando parcheggi 2026 — `direct_applicant`, recuperato dalla review;
7. Emergenza abitativa / residenza sociale — `direct_applicant`, `conditional`, recuperato dalla review;
8. Buoni scuola 2026 — `implementing_body`, con famiglie come beneficiari finali.

Sono invece esclusi dall'output operativo i due casi che avevano evidenziato i limiti della v0.2:

- Biotrituratori elettrici 2026 — ruolo/geografia incompatibili;
- San Francesco / Collodi / Alluvione di Firenze — nessun nesso Versilia documentato nel caso corrente.

## Limiti residui

La v0.2.1 non pretende ancora di risolvere tutti i 16 elementi della review. Il principio è deliberatamente conservativo: meglio una review interna che una falsa opportunità.

Restano da sviluppare soprattutto:

- estrazione strutturata delle sezioni `Beneficiari`, `Destinatari`, `Soggetti proponenti`, `Chi può presentare domanda`;
- requisiti patrimoniali e proprietà/disponibilità degli immobili;
- soglie demografiche;
- cofinanziamenti e massimali;
- qualità/completezza dei campi critici, inclusa la scadenza;
- sostituzione o affiancamento della fonte PA digitale attualmente stale;
- backtest storico prima della pagina pubblica.

## Stato

**v0.2.1 resta un prototipo nella Draft PR #82. Non crea route pubbliche, non modifica la shell del sito e non pubblica automaticamente alcuna opportunità.**
