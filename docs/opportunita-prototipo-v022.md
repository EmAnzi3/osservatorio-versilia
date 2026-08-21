# Radar Opportunità Versilia — v0.2.2

## Obiettivo

La v0.2.2 consolida il prototipo dopo il collaudo umano della v0.2.1. Non amplia le fonti: lavora sulla qualità delle tre fonti già presenti e sulla corretta classificazione dei casi ambigui.

Restano invariati i vincoli del prototipo: nessuna route pubblica, nessuna modifica a `data/site-data.json`, nessuna modifica alla shell canonica del sito e nessuna pubblicazione automatica.

## Due livelli separati

La v0.2.2 distingue definitivamente:

1. **classificazione semantica** — il Comune può realmente lavorare l'opportunità, in quale ruolo e con quale geografia;
2. **quality gate** — anche un'opportunità semanticamente valida entra nell'output solo se i campi critici sono sufficientemente documentati.

Il quality gate richiede almeno:

- una regola documentale versionata (`rule_id`);
- un ruolo comunale operativo e non `unknown`/`none`;
- ambito e ammissibilità geografica documentati;
- pertinenza territoriale sufficiente;
- evidenza con URL della fonte;
- scadenza per la candidatura;
- almeno un Comune della Versilia `eligible` o `conditional`;
- fonte con freshness `current`;
- per gli elementi `conditional`, una condizione di progetto esplicita.

Un record che fallisce questi requisiti viene spostato in `qualityHold`: non viene confuso né con una vera opportunità né con la coda di incertezza semantica.

## Collaudo umano dei 16 casi v0.2.1

Tutti i 16 elementi presenti nella precedente `reviewQueue` sono stati verificati e classificati nel registro overlay `data/opportunity-rules-v022.json`.

### Recuperati come opportunità

1. **Toscanaincontemporanea 2026** — `conditional`, Comune `direct_applicant`: il bando ammette soggetti pubblici, ma il richiedente deve operare in ambito culturale e presentare un progetto coerente con la creatività contemporanea.
2. **Bando Sistemi museali 2026** — `conditional`, Comune `system_member`: il richiedente è il Sistema Museale, non il singolo Comune. Il Sistema Museale Territoriale della Provincia di Lucca documenta musei aderenti a Camaiore, Massarosa, Pietrasanta, Seravezza, Stazzema e Viareggio. Per Forte dei Marmi il prototipo non documenta un museo aderente nel corrente elenco e quindi non attribuisce un canale operativo.
3. **Risorse genetiche forestali 2026** — `conditional`, Comune `direct_applicant`: sono ammessi anche proprietari/possessori e titolari pubblici di superfici forestali o agricole; per ogni Comune deve però essere verificata la titolarità/possesso della superficie ammissibile.

### Esclusi dall'output operativo

- progetti culturali per la popolazione carceraria — manca nel campione un nesso documentato con un progetto/istituto rilevante per la Versilia;
- Blue Tongue — aziende agricole con allevamento;
- percorsi formativi negli undici settori strategici — soggetti formativi accreditati / ATI-ATS;
- costituzione di Organizzazioni di produttori — OP riconosciute o in corso di riconoscimento;
- cultura del riuso — enti del Terzo settore iscritti al RUNTS;
- premialità Poli Tecnici Professionali — candidatura riferita ai PTP;
- impianti di trattamento rifiuti — linea FESR per privati;
- Premio Impresa più sicura — formalmente accessibile anche a enti pubblici, ma premio non finanziario (targa/logo), quindi fuori dal perimetro del Radar finanziamenti;
- apprendistato duale — ATS dei soggetti educativi/formativi previsti dall'avviso;
- produzione spettacolo dal vivo 2026 — fase di candidatura conclusa; la data 2027 rilevata dalla pagina riguarda attuazione/rendicontazione, non nuove domande;
- voucher Just in Time — voucher individuali per persone disoccupate/inoccupate/inattive;
- Catalogo Just in Time — organismi formativi accreditati;
- elenco garanti BEI — Confidi/intermediari finanziari autorizzati.

Queste decisioni sono espresse tramite classi riutilizzabili (`non_municipal_applicant`, `indirect_system_membership`, `conditional_asset_holder`, `closed_application`, `non_financial`, `facility_specific_geography`) e non come logica speciale sparsa nel collector.

## Correzione scadenza Buoni scuola

La v0.2.1 riconosceva correttamente il Comune come `implementing_body`, ma non estraeva la scadenza comunale. La v0.2.2 registra la scadenza documentata del **25 settembre 2026** per l'adesione/candidatura dei Comuni, distinta dalle scadenze locali previste per le famiglie.

## Ciclo di vita della procedura

La v0.2.2 introduce `lifecycle_stage`. Una data futura presente nella pagina non viene considerata automaticamente una scadenza per nuove domande.

Caso di controllo: **Sostegno a progetti di produzione di spettacolo dal vivo 2026**. La candidatura è già chiusa e la data futura riguarda la fase di attuazione/rendicontazione: il record viene quindi escluso come `implementation_only`.

## Live probe — 21 agosto 2026

Workflow GitHub Actions, timezone `Europe/Rome`.

```text
Candidati                         42
Candidati operativi pre-gate      11
Quality pass                      11
  eligible                         6
  conditional                      5
Quality hold                       0
Review semantica                   0
Scartati / non operativi          31

Collaudo umano riconosciuto       16
  promossi                         3
  esclusi                         13
```

Per fonte:

| Fonte | Quality pass | Hold | Review | Freschezza |
| --- | ---: | ---: | ---: | --- |
| Regione Toscana | 9 | 0 | 0 | `current` — 19/08/2026 |
| Fondazione CR Lucca | 2 | 0 | 0 | `current` — 16/06/2026 |
| PA digitale 2026 | 0 | 0 | 0 | `stale` — 30/01/2026 |

La fonte PA digitale resta quindi tecnicamente raggiungibile ma non viene interpretata come fonte corrente sufficiente.

## Le 11 opportunità quality-pass

1. Bando Amianto Edifici Pubblici 2026 — `eligible`;
2. Nidi di qualità 2026-2027 — `eligible`;
3. Progett-Azioni — `conditional`, ruolo `partner`;
4. Progettare per il futuro – opere pubbliche — `eligible`;
5. Toscanaincontemporanea 2026 — `conditional`;
6. Bando Sistemi museali 2026 — `conditional`, ruolo `system_member`;
7. Buoni scuola 2026 — `eligible`, ruolo `implementing_body`, scadenza comunale 25/09/2026;
8. Risorse genetiche forestali 2026 — `conditional` sulla titolarità/possesso della superficie;
9. Toscana Diffusa – strutture di servizio pubbliche — matrice Comune-per-Comune;
10. Bando parcheggi 2026 — `eligible`;
11. Emergenza abitativa / residenza sociale — `conditional` sulle casistiche immobiliari.

## Test

Cinque suite tutte verdi:

```text
collector base        6/6
filtro qualità        2/2
resolver v0.2         6/6
resolver v0.2.1       8/8
resolver v0.2.2      11/11
Totale               33/33
```

I test v0.2.2 coprono, tra l'altro:

- merge overlay delle regole senza duplicare il registro v0.2.1;
- scadenza Buoni scuola;
- promozione condizionale di Toscanaincontemporanea e Risorse genetiche forestali;
- ruolo indiretto e matrice territoriale dei Sistemi museali;
- esclusione di premi non finanziari;
- distinzione tra scadenza di candidatura e fase di attuazione;
- blocco quality gate per deadline mancante;
- blocco per fonte stale;
- ammissione al gate di ruoli indiretti documentati.

## Interpretazione corretta dello zero review

`review = 0` vale **per i 42 candidati del campione live del 21 agosto 2026**. Non significa che il radar possa classificare senza verifica qualsiasi nuovo bando futuro.

La regola di sicurezza resta: un nuovo caso senza una regola documentale sufficiente torna in review, invece di essere promosso per analogia.

## Stato

**v0.2.2 validata tecnicamente sul campione corrente. Draft PR #82, nessun merge e nessuna pubblicazione.**
