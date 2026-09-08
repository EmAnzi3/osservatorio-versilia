# Radar Opportunita - matrice di rilevanza comunale v1

Data audit: 8 settembre 2026

## Perche questa matrice

Il corpus di saturazione contiene opportunita molto diverse: bandi diretti, assistenza tecnica, strumenti finanziari, premi, call Horizon/Interreg in partenariato e route nazionali. Per evitare che il numero pubblico del Radar confonda un bando direttamente presentabile da un Comune con una semplice possibilita di entrare in un consorzio, il conteggio viene separato per ruolo municipale.

Questa e solo documentazione di audit. Non modifica il motore, la discovery o la pubblicazione.

## Regola del numero principale

Nel numero principale del Radar entrano solo:

- **DIRECT** - il Comune e applicant esplicito;
- **DIRECT_CONDITIONAL** - il Comune puo candidarsi direttamente se possiede il progetto, asset, ruolo settoriale, accreditamento o altro requisito documentato;
- **SUPPORT_FINANCE** - il Comune puo chiedere direttamente assistenza tecnica, finanziamento agevolato, trasferimento di asset, matchmaking o capacity building strutturato;
- **ROUTED** - il Comune puo originare o ricevere il supporto, ma la presentazione formale passa da un'autorita nazionale.

Le opportunita **PARTNER** sono reali e vengono monitorate, ma non entrano nel headline count. Devono essere mostrate in una sezione distinta con badge esplicito `Partner / consorzio`.

I casi **REVIEW_EXCLUDE** restano interni finche il ruolo comunale non e dimostrato in modo sufficiente.

## Conteggi

Snapshot di riferimento del 7 settembre 2026:

- 29 schede pubbliche;
- 25 `application_open`;
- 2 `rolling_open`;
- 2 `announced_upcoming`.

Classificazione deduplicata dei finding correnti/rolling emersi nell'audit:

| Classe | Nuove card-equivalent | Nel numero principale? |
| --- | ---: | :---: |
| DIRECT | 1 | si |
| DIRECT_CONDITIONAL | 31 | si |
| SUPPORT_FINANCE | 18 | si |
| ROUTED | 2 | si |
| PARTNER | 37 | no |
| REVIEW_EXCLUDE | 3 | no |
| **Totale classificato** | **92** | |

Ne consegue:

- **79 opportunita open/rolling nel corpus comunale principale** = 27 open/rolling gia pubbliche + 52 nuove strettamente comunali;
- **81 schede nel corpus comunale principale** se si mantengono anche le 2 `upcoming` gia presenti nello snapshot;
- **116 opportunita open/rolling nel perimetro esteso** se si aggiungono le 37 `PARTNER`;
- **118** nel perimetro esteso includendo anche le 2 upcoming gia pubbliche.

Quindi il numero da comunicare come `opportunita per i Comuni` non e 100-110: con il criterio severo e oggi **79 open/rolling** (81 con le upcoming gia presenti). Le opportunita di partenariato costituiscono un secondo livello informativo e non devono gonfiare il dato principale.

## Esempi per classe

### DIRECT

- European Capitals of Small Retail 2027: candidatura della city administration, con soglia demografica e requisiti del premio.

### DIRECT_CONDITIONAL

Esempi: Natura 2000 Award, European Digital Connectivity Awards, #BeActive EU Sport Awards, SUNDANSE, diverse azioni LIFE 2026, Erasmus+, SPACE4Cities, UMX, Marchio del patrimonio europeo, Tirocini/Dottorati InPA, MiC Progetti speciali cinema, trasferimento gratuito Demanio, IRISCC e Blue Climathons.

La condizione non rende la scheda meno comunale: significa che il Comune deve possedere un progetto/asset/servizio o una competenza coerente prima di candidarsi.

### SUPPORT_FINANCE

Esempi: ELENA, Citizen Energy Advisory Hub, Smart Cities Marketplace, EIB ADAPT e C3, SINFI, Cultura Missione Comune, Sport Missione Comune, MIP4Adapt Hotline e Roster, Green Assist, eeef, InvestEU Portal e CEB.

Queste schede devono indicare chiaramente il tipo di beneficio: `TA`, `prestito/finanza`, `matchmaking`, `asset`, `capacity building`. Non devono essere presentate come contributi a fondo perduto.

CO-WATERS Coalition resta in questa classe perche la membership da accesso a servizi strutturati: capacity building, supporto stakeholder, guidance su funding/financing, supporto al Mission Label e call dedicate come i Blue Climathons. EIT Culture & Creativity Cities & Regions Network resta perche la route delegate e associata a peer learning, pilot e collaborative policy action, non a una semplice newsletter.

### ROUTED

- AMIF Integration at Local Level;
- Technical Support Instrument 2027.

La scheda deve spiegare chi presenta formalmente la richiesta e quale azione concreta puo compiere il Comune italiano. Se la route nazionale non e documentabile, la scheda non deve apparire come candidatura diretta UE.

### PARTNER

Qui ricadono soprattutto Interreg, Horizon, NEB, I3 e alcuni LIFE. Il Comune deve avere un ruolo operativo documentato - beneficiario, demo city, public procurer, asset owner, practitioner o partner territoriale - e non solo essere citato tra stakeholder/end user.

Esempi forti: Horizon CIRCBIO-04 richiede autorita regionali/locali beneficiarie; diversi topic Cities Mission richiedono citta beneficiarie; Co-create NEB richiede almeno un Comune/regione/ente affiliato nel consorzio; EIT NEB Academy Skills Infrastructure richiede un'autorita pubblica nel partenariato.

Questi casi sono utili per il Radar ma vanno tenuti distinti dal numero principale.

## Casi non conteggiati

Tre casi emersi come actionable in passaggi intermedi restano fuori dal conteggio pubblico:

- DUT Call 2026: la call richiede un'autorita urbana, ma l'Italia non figura nel current participating funding-country set; per un Comune italiano resta al massimo un ruolo di cooperation partner non finanziato;
- Horizon CL3 DRS-04: la rilevanza locale non dimostra che il Comune soddisfi la definizione del beneficiary richiesto;
- NEB REGEN-03: possibile ruolo comunale come asset/regulatory/demo partner, ma non abbastanza esplicito per la pubblicazione automatica.

Altri `scope_review` gia documentati nelle wave restano analogamente fuori finche non superano la stessa soglia probatoria.

## Conseguenza per l'hardening

Il replay post-hardening deve produrre almeno quattro numeri separati:

1. `municipal_current` = DIRECT + DIRECT_CONDITIONAL + SUPPORT_FINANCE + ROUTED aperte/rolling;
2. `municipal_upcoming` = stesse classi, ma non ancora aperte;
3. `partner_current` = PARTNER aperte/rolling;
4. `internal_review` = casi non ancora sufficientemente risolti.

La home deve usare `municipal_current` come numero principale. `partner_current` puo essere mostrato come secondo indicatore, ma non sommato nel headline.

## Stato attuale certificato dalla matrice

- **municipal_current stimato sul corpus documentato: 79**;
- **municipal_public incluso upcoming gia canonico: 81**;
- **partner_current: 37**;
- **extended_current: 116**.

Il replay del motore resta necessario per il numero definitivo post-hardening: puo ridurre il totale per deduplica canonica o variazioni di lifecycle, ma non puo aumentare il numero principale spostando arbitrariamente schede `PARTNER` nelle classi comunali dirette.
