# Consolidamento Osservatorio Versilia — handoff operativo

## Dossier «Ambiente e rischi in Versilia» (3 novembre 2026)

Branch `feature/dossier-ambiente`, ottavo dossier in forma di relazione, scelto dal
proprietario come primo dopo bilanci e mobilità (poi demografia e investimenti).
Sette capitoli, 361 risposte del motore in tutto il generatore:

1. alluvioni: residenti in pericolosità media (P2) ed elevata (P3), mappa ISPRA 2020,
   censimento 2011; scenari annidati, non sommati;
2. frane: residenti e territorio in pericolosità elevata e molto elevata (P3+P4),
   mappa 2024, censimento 2021;
3. clima: temperatura e pioggia 2025, delta OLS 1975-2025 (LaMMA/ERA5-Land); nessun
   valore Versilia né confronto con Toscana, che il motore rifiuta;
4. costa: dinamica della riva 2006-2020 e costa protetta da opere rigide (quattro
   Comuni costieri, `partial=True`; confronto con Toscana e Italia solo per le opere);
5. mare: aree di balneazione eccellenti 2022-2025, campioni di routine fuori limite
   2025 (non i campioni suppletivi, mirati), Bandiere Blu 2026 solo nel testo;
6. rifiuti e acqua: raccolta differenziata e rifiuti per abitante 2024, perdite
   idriche 2018; rimando al dossier bilanci per costo del servizio e TARI;
7. bonifiche: procedimenti SISBON aperti e totali.

Seguendo `ci/territorial-dossier-program.json` (scheda ambiente): pericolosità ed
esposizione distinte dal rischio, nessuna previsione per edificio, protezione rigida e
procedimento chiuso non descritti come efficacia o risanamento. Consumo di suolo e
agricoltura restano per il dossier «suolo».

Altre modifiche:
- `SOURCE_NAMES`: le voci specifiche (IdroGEO, LaMMA, ISPRA coste, ARPAT
  balneazione, FEE, catasto rifiuti per la produzione, censimento Istat delle
  acque, SISBON) stanno in testa, perché vince la prima corrispondenza;
- unità `celsius`, `celsiusdelta`, `mm`, `kg`; funzione `sul()` per «sull’87,8%»;
- frasi che citano montagna e quota solo se i valori estremi sono di Stazzema o
  Seravezza;
- `ci/content-contract.json`: `dossier/ambiente/index.html`; indice dei dossier
  aggiornato.

## Radar 2.0 — le schede automatiche si rileggono quando cambiano le regole (3 novembre 2026)

Branch `fix/radar-rilettura-schede-auto`: dopo il merge della #536 il run del 3/11 ha tenuto pubblicata GranFest (Fondazione CR Lucca), qualificata il 2/11 con le regole precedenti su una frase che cita il Comune solo come possibile finanziatore. Causa: `apply()` riportava le schede `auto_qualified` dei giorni precedenti fino alla scadenza senza rileggerle. Ora `VERSION` del qualificatore è `1.1` e una scheda con `auto_qualification_version` diversa torna in lettura per prima, anche se scartata di recente: se le regole attuali la qualificano viene ricostruita, se la respingono o è scaduta esce (conteggio `withdrawn`, «ritirate perché non superano più le regole» nel rapporto del run), se la pagina non si legge in quel run resta com'era. Ogni futura modifica alle regole di ammissibilità deve alzare `VERSION`. Test: `test_cards_from_older_rules_are_reread` (fallisce senza la correzione).


## Radar 2.0 — icone fonte per tutti i domini ufficiali (2 novembre 2026)

Branch `fix/radar-icona-anci-abruzzo`: il Radar del 2/11 su main non si pubblicava (`build_static_brand.py`: «Icone fonte incomplete: 161/162», scheda ANCI Abruzzo «Avviso MIM vulnerabilità sismica»). `materialize_opportunity_release_favicons.py` copre ora tutti i domini di `OFFICIAL_SUFFIXES` del qualificatore: alias ai favicon versionati (Sviluppo Toscana, Fondazione CR Lucca, GSE) e source-mark locali (ANCI, ANCI Toscana, ANCI Abruzzo, Invitalia, CDP, Italia Domani, Interreg Europe, URBACT, Interreg Marittimo). Il test `test_every_official_qualifier_host_has_a_source_icon` fallisce se si aggiunge un dominio ufficiale senza icona.
## Dossier «I conti dei Comuni» (2 novembre 2026)

Branch `feature/dossier-bilanci`, settimo dossier in forma di relazione e ultimo dei
due prioritari (dopo la mobilità). Sette capitoli dai rendiconti 2025 (OpenBDAP),
da SIOPE, dalle delibere MEF 2025 su addizionale IRPEF e TARI, dal costo ISPRA dei
rifiuti 2024, dal Conto annuale RGS 2024 e dall'indicatore regionale sui servizi
online (Istat ICT 2022):

1. entrate e riscossione;
2. spesa corrente, sociale e scuola;
3. investimenti impegnati e pagati;
4. risultato disponibile e spese rigide;
5. debito e interessi;
6. IRPEF e TARI su casi tipo, costo dei rifiuti;
7. personale e servizi online.

Gli aggregati Versilia sono quelli che il motore calcola (`weighted_ratio`).
Per spese rigide, risultato del Piano degli indicatori, TARI e IRPEF il motore non
ammette aggregati, quindi il testo cita solo i valori comunali. Toscana compare solo
dove il motore ha il confronto: dipendenti, servizi online, costo dei rifiuti.

Seguendo `ci/territorial-dossier-program.json` (scheda bilanci), il testo:
- non calcola margini disponibili;
- non equipara la spesa ai servizi ricevuti;
- avverte che i valori per residente dei Comuni turistici sono gonfiati da chi non
  vi risiede.

Altre modifiche:
- nuova funzione `money()` e unità `eurc`, per gli euro con i centesimi solo quando
  servono (IRPEF di Camaiore 144,50);
- l'articolo si apostrofa anche davanti a 1 («l'1,7%»);
- nuovi nomi di fonte: SIOPE, Conto annuale, BDAP open data, delibere MEF, ISPRA,
  indicatori comunali regionali.

## Abitare in terracotta (2 novembre 2026)

Branch `feature/abitare-terracotta`, su richiesta del proprietario. Il viola di
Abitare (#6d5ca6) era quasi identico a quello di Istruzione (#7357a8, distanza
percettiva ΔE 6). Nuova palette DS2 di Abitare: accento #8e5a46, scuro #734637,
fondo #fbf4f1, linea #e6d3ca. Contrasto sul bianco 5,7:1; ΔE minimo dagli altri
temi 23 (Sicurezza). Una terracotta più accesa (#b5653f) sarebbe finita a ΔE 8
da Sicurezza e 15 da Demografia ed è stata scartata. File toccati: fidelity.css
(tema, pillole del contesto, pilota municipale), dossier-report.css,
secondary-pages-ui.css (card della home, ora coerente col marrone delle icone).
Le baseline visive (golden lock tematico e municipale, visual-regression
themes) si aggiornano in una PR successiva secondo docs/A5_GOLDEN_MASTERS.md.

## Dossier «Muoversi in Versilia» e icone dei temi (1° novembre 2026)

Branch `feature/dossier-mobilita`, su richiesta del proprietario (proseguire con
gli altri dossier; alla pubblicazione icone e colori dei temi del sito). Sesto
dossier in forma di relazione, primo dei due prioritari rimasti (poi bilanci e
servizi): occupati che lavorano fuori Comune e pendolari in uscita e in entrata,
corse di autobus e treni, ampiezza della giornata di servizio e fermate (GTFS,
un giorno feriale d’estate), automobili ed Euro 0-3, punti di ricarica, fibra
fino all’edificio (AGCOM), percorsi a piedi e in bici. Saldo e autocontenimento
restano nel dossier lavoro, con rimando. Nessun aggregato Versilia dove il
motore lo rifiuta (TPL, veicoli, ricarica, fibra, percorsi). Le date dei periodi
(`AAAA-MM-GG`) sono scritte per esteso; lo zero prende l’articolo «lo»; la fonte
GTFS ha un nome proprio prima della regola generica `dati.toscana.it`, che
l’avrebbe chiamata «servizi per la prima infanzia».

Icone e colori: ogni dossier e ogni scheda dell’indice portano l’icona del tema
del sito (tracciati letti da `themeSvgPaths` in `assets/app-parts/00.txt`, non
duplicati) e la palette DS2 delle pagine tematiche (`--ds-theme-accent`); il
turismo usa il colore di Economia con un’icona propria (ombrellone). Barre,
riquadri e numeri del dossier prendono il colore del tema.

## Workflow superati — primo lotto (1° novembre 2026)

Branch `chore/retire-obsolete-workflows`, su decisione del proprietario (pulizia
caso per caso). Ritirati `invalsi-v138-preview` e `biometria-comune-preview`:
anteprime di rilasci già in produzione, ultimo run il 13/9 fallito. I loro gate
di sorgente (`test_invalsi_v138.py`, `test_biometria_comune_release.py`, offline,
meno di un secondo) passano ora nei quickChecks canonici, quindi la copertura
non cala. Restano attivi, con motivazione: le acquisizioni
`meteo-poc`, `climate-minmax-extend` e `probe-istat-lavoro-istruzione` sono
l'unica via documentata per rigenerare quei dati; lo shadow
`opportunity-radar-daily-v2-shadow` esce con la fase 2 del Radar insieme a
`opportunity-radar-v044-ci`, che ne esegue il test.

## Radar 2.0 — coda interna letta dal qualificatore (2 novembre 2026)

- Origine: audit indipendente del 2 novembre. FUORILUOGO (Fondazione CR Lucca, Comuni richiedenti diretti, scadenza 11/12/2026) era stato trovato ma restava in `reviewQueue` con «Manca una regola documentale v0.2.1»: il qualificatore automatico leggeva solo `discoveryQueue`.
- Ora `opportunity_qualifier.apply` legge anche le schede in `reviewQueue` delle fonti primarie (`review_candidates`), con le stesse regole generali e l'etichetta «Requisiti da confermare»; le schede pubblicate escono dalla coda interna. Escluse le prefetture (`REVIEW_EXCLUDED_SOURCES`), che hanno filtri dedicati.
- Nessun doppione delle schede curate con titolo diverso: se almeno l'80% delle parole significative del titolo in coda compare in un titolo pubblicato della stessa fonte, la scheda è saltata (caso BELLA LÌ).
- Prova sul vivo dalla coda del 2/11: oltre a FUORILUOGO si sblocca «Contributi agli enti locali per lo sviluppo di progettualità sui dati» (Regione Toscana, Comuni toscani, a sportello dal 22/10). Concorsi, selezioni di personale e bandi per imprese restano scartati.
- Due correzioni emerse dalla prova: «beni comuni», «spazi comuni» e simili non valgono come Comuni richiedenti; le sezioni «Varianti/Esecutivi» non sono avvisi.
- SRA31: nessun difetto, la proroga al 13/11 era già nello snapshot del 2/11 ore 07:36; l'audit aveva letto la pagina del 30/10.
- GSE: resta «bloccata e coperta» (firewall sui server della CI); nessuna modifica in questa PR.
- Correzione dopo il primo giro reale (#533): GranFest 2027 era pubblicato come partnership, ma la scheda dice «riservata a soli soggetti privati» (il Comune compariva solo fra i possibili finanziatori). Il bando regionale sui dati era già pubblicato con altro titolo e il controllo dei doppioni lo ha saltato correttamente.

## Radar 2.0 — chi può candidarsi si legge nella voce dei destinatari (2 novembre 2026)

- Decisione del proprietario: la voce dei destinatari del bando è l'unica base per stabilire se il Comune può candidarsi. Niente più ricerca della parola «Comune» in tutta la pagina.
- `find_beneficiaries` legge prima la scheda, poi i documenti: voci «Beneficiari», «Soggetti ammessi/beneficiari/richiedenti…», «Chi può partecipare», «Possono presentare domanda…», «Domanda presentata da», «Requisiti di ammissibilità», «Eligible applicants». Decide la prima voce sui richiedenti; «Destinatari» da solo può indicare il pubblico delle attività (cittadini, scuole) e quindi include ma non esclude.
- Prevalgono sempre «riservata a soli soggetti privati» e l'esclusione espressa degli enti pubblici. Il Comune come finanziatore, patrocinatore o luogo del progetto non è un richiedente. Contano anche «enti pubblici», «soggetti pubblici o privati», «enti di diritto pubblico» e l'etichetta regionale «Destinatari: Enti».
- Nessuna voce trovata: la scheda resta in coda, non si pubblica. La scheda pubblicata cita la voce.
- I topic UE (`strict_municipal`) mantengono le regole dedicate EU_LEAD/EU_PARTNER.
- Seconda decisione del proprietario: resta fuori solo il bando in cui il Comune non c'entra in alcun modo. Se può partecipare in qualsiasi forma (richiedente, partner, consorzio, associazione, collaborazione con accordo) il bando va bene. Nel qualificatore la prima frase della voce decide chi presenta; le frasi successive contano se ammettono il Comune (`LATER_ADMISSION`, `LIST_ITEM_PUBLIC`) o lo fanno collaborare (`MUNICIPAL_AS_COLLABORATOR`, ruolo partner); patrocinio, sostegno, parere o nulla osta del Comune non sono partecipazione (`MUNICIPAL_AS_SUPPORTER`). Le schede curate Pro Loco (Comune partner con accordo formalizzato) e Spreco alimentare (Comune partner operativo) restano quindi valide.
- Prova sulla coda live del 2/11 (282 segnalazioni lette): escono servizio civile regionale (destinatari: giovani 18-29 anni) e una pagina indice «Avvisi pubblici e premi»; entra Sport e Salute «Fabbrica Spazi Civici» come partnership («al partenariato possono aggiungersi anche enti pubblici»). Sui 58 pubblicati nessun cambio.

## Lancio di «Chiedi» e «Dossier» (31 ottobre 2026)

Branch `feature/launch-chiedi-dossier`, su decisione del proprietario: nel menu
principale «Dossier» e «Chiedi» dopo «Comuni» (contratto `HEADER_LINK_LABELS`,
coerenza, fixture e browser test aggiornati; voce attiva calcolata dal percorso);
in home un riquadro dopo i Temi con i link a `/dossier/` e `/chiedi/`. Dossier e
indice senza `noindex` e registrati nella sitemap da `build_dossier_reports.py`;
`/chiedi/` era già indicizzabile. `materialize_opportunity_public_shell.py`
riconosce la voce Opportunità già materializzata anche con le nuove voci. Su
mobile, sotto 440 px, l’header mostra solo il marchio OV senza la scritta
(prima sotto 380 px), così «Opportunità» resta visibile nel menu; fra 701 e
940 px il menu scorre in orizzontale come su mobile (con 8 voci l’header
sforava di ~60 px a 768). `test_site_chrome_browser.py` verifica la scritta
nascosta sotto 440 px invece di misurarne la geometria.

## Radar 2.0 — fonti bloccate ma coperte (31 ottobre 2026)

Branch `fix/radar-gse-blocked-covered`: il GSE blocca la CI con il firewall;
se MASE, ANCI o ANCI Toscana rispondono, il rapporto lo elenca fra le «Fonti
bloccate ma coperte» invece che fra quelle da riparare (`COVERED_WHEN_BLOCKED`
in `opportunity_qualifier.py`). Dettagli in `docs/RADAR_2.md`.

## Radar 2.0 — correzioni del qualificatore (31 ottobre 2026)

Branch `fix/radar-qualifier-eu-topics`: il primo run di produzione del
qualificatore non ha pubblicato nulla. L'anno nel codice di un topic UE non lo
scarta più se la scadenza strutturata è futura; un'autorità pubblica locale nel
consorzio come beneficiaria vale come partecipazione da partner. Dettagli in
`docs/RADAR_2.md`. Fase 2 (pipeline unica) ancora da fare.

## Radar 2.0 — qualificazione automatica (31 ottobre 2026)

Branch `feature/radar-discovery-overhaul`, presa in carico su richiesta del
proprietario dopo l’issue #511 (CERV-DAPHNE aperti a luglio, rilevati a fine
ottobre). Diagnosi e piano in `docs/RADAR_2.md`. Questa fase: qualificazione
automatica delle segnalazioni con etichetta «Requisiti da confermare»
(`opportunity_qualifier.py`), fonte UE dall’interfaccia ufficiale Funding &
Tenders (`opportunity_eu_calls.py`), fonti da riparare, ritardo di rilevazione nel
rapporto e rapporto come commento sulle PR del Radar. Fase 2: pipeline unica al
posto dei sette strati.

## A7.5.6 — riorganizzazione di «Chiedi» (30 ottobre 2026)

Branch `feature/a7-chiedi-reorg`. Su decisione del proprietario `/chiedi/` non
pubblica più le domande guidate del pilota (offerta educativa, percorsi
Massarosa): la pagina è hero, esploratore e rimando a `/dossier/`.
`build_a7_public_page.py` genera la pagina senza rilascio del pilota;
`validate_public_site.py` richiede esploratore e link ai dossier; ritirati
`a7_public_release.py`, `a7_education_editorial.py`,
`test_a7_education_editorial.py` e `verify_public_page`. Il pilota resta
verificato come esperimento. Dopo la revisione dell’anteprima resta il lancio.

## A7.5.5 — riuso dei risultati di «Chiedi» (30 ottobre 2026)

Branch `feature/a7-reuse-export`. Ogni risultato dell’esploratore offre: «Copia
il link» (indicatore, dettaglio, domanda, Comune e riferimento nel frammento
`#esplora&…`, letto una sola volta e poi rimosso dall’indirizzo), «Scarica i dati
(CSV)» con i valori esatti delle risposte A6 (separatore `;`, virgola decimale) e
la riga del risultato nativo, «Stampa o salva in PDF» con una copia del solo
risultato. Nessun nuovo calcolo nel browser. Restano A7.5.6 (riorganizzazione
della pagina) e il lancio di «Chiedi» e «Dossier» in navigazione.

## Dossier — pagina indice (29 ottobre 2026)

`dist/dossier/index.html`: una scheda per dossier con tema, presentazione, primo
dato della sintesi, link a pagina, PDF e CSV; il percorso di ogni dossier porta
all’indice. Tutte le pagine restano `noindex` e fuori da menu e sitemap: il
lancio (menu, home, indicizzazione) insieme a «Chiedi» richiede l’approvazione
del proprietario.

## Dossier come relazione — «Crescere in Versilia» (29 ottobre 2026)

Quinto dossier `dist/dossier/scuola/`: posti nei servizi per la prima infanzia,
tempo pieno e alunni per classe, età degli edifici e mense, INVALSI di quinta
primaria (copertura parziale dichiarata: Stazzema non pubblicato), adulti con
almeno il diploma, spesa comunale per l’istruzione. Il generatore accetta misure
a copertura parziale (`allowPartial`), con nota nel grafico e frase per Comune.
Restano la pagina indice `/dossier/` e il lancio.

## Dossier come relazione — «Invecchiare in Versilia» (29 ottobre 2026)

Quarto dossier `dist/dossier/anziani/`: indice di vecchiaia e sua variazione,
anziani per 100 persone in età da lavoro, grandi anziani (85+), saldo naturale e
variazione della popolazione, speranza di vita (ARS), assistenza domiciliare e
farmacie, spesa sociale dei Comuni. Costruito sopra il ramo del turismo (#501).

## Dossier come relazione — «La Versilia dei turisti» (29 ottobre 2026)

Terzo dossier `dist/dossier/turismo/`: presenze e intensità turistica,
variazione delle presenze fra il primo e l’ultimo anno disponibili (una
`relative_change` A6 per Comune), permanenza e turisti residenti all’estero,
stagionalità, posti letto e strutture, spesa comunale per il turismo. Il
generatore aggiunge le misure di variazione per Comune e i nomi pubblici di
Regione Toscana e OpenBDAP; il gate abbina ogni grafico alla sua misura.

## Dossier come relazione — «Lavorare in Versilia» (28 ottobre 2026)

Formato approvato dal proprietario con la #495 (casa). Secondo dossier
`dist/dossier/lavoro/`: occupazione e disoccupazione 25-64 anni, giovani e donne,
addetti e dimensione delle imprese, pendolari 2021, retribuzioni e valore
aggiunto, redditi da lavoro e pensioni. Il generatore ora gestisce valori negativi
(saldo pendolare), nomi delle fonti per tipo di rilevazione e articoli italiani
davanti alle cifre. Chiuse su decisione del proprietario le PR superate #494, #443,
#338 e #117. Pagine ancora `noindex` e fuori dal menu; manca una pagina indice
`/dossier/` prima del lancio.

## Dossier come relazione — prototipo «Abitare in Versilia» (27 ottobre 2026)

Il proprietario ha respinto i dossier come elenco di evidenze (#494, in pausa):
un dossier deve dare valore al dato, in forma di relazione divulgativa
(riferimenti Openpolis, ONS, Dove vanno i nostri soldi), senza rimandi a
GitHub né JSON scaricabili. Scelte: tema «Casa e affitti», punto di vista
«Versilia + scegli il tuo Comune», tono divulgativo. Branch
`feature/dossier-report-casa`: `scripts/build_dossier_reports.py` genera
`dist/dossier/casa/` (sintesi, sei capitoli con domanda, grafici, «Perché
conta», versione per Comune, «Cosa non sappiamo», fonti e note), un PDF della
versione Versilia e un CSV per Excel. Ogni cifra viene da una risposta calcolata
dal motore A6; le frasi sono modelli fissi senza cause. Pagina `noindex` e fuori
dalla navigazione fino all’approvazione. Gate `test_dossier_reports.py`. Prossimo
passo: revisione del proprietario, poi estensione agli altri temi.

## A7 — perimetro della prima versione e valori fuori scala (26 ottobre 2026)

Decisione del proprietario: la prima versione guidata di «Chiedi» comprende le
domande su una misura, il riuso delle analisi (CSV/PDF) e il consolidamento; gli
incroci (A7.5.4) sono rinviati. Il lancio in navigazione avviene solo a
perimetro completo. Branch `feature/a7-outlier-values`, base main #489: espone
l’operazione A6 `anomaly` come «Valori fuori scala fra i sette Comuni»
(profilo `outliers`, regola di Tukey, interfaccia v8). 515 viste ammesse, 503
calcolate. Metodo `A7_OUTLIER_VALUES.md`. Con questo incremento tutte le
operazioni su una misura ammesse da A6 sono presentate, salvo 9 viste con
riferimento «Versilia», escluse per scelta. Restano A7.5.5 riuso e A7.5.6
consolidamento.

## A7.5.4 — perimetro degli incroci misurato e rivisto (26 ottobre 2026)

Branch `feature/a7-association-perimeter`, base main #488. Delle 202
associazioni fra le domande verificate A6, 6 sono calcolate e 196 rifiutate
(175 per coppia non rivista congiuntamente). Il costo non è il vincolo: 32
componenti aggiungono +0,10% di gzip al runtime pubblico completo. Decisione del
proprietario: perimetro = le 6 associazioni calcolabili, con motivi in italiano
come nuove richieste esatte dai risultati invariati. Piano
`ci/a7-association-perimeter.json`, gate `test_a7_association_perimeter.py` nei
controlli sul catalogo effettivo, metodo `A7_ASSOCIATION_PERIMETER.md`.
Nessun rollout: il divieto `public=True, associations=True` resta invariato.
Prossimo passo, da approvare: rollout pubblico del solo piano rivisto.

## Main verificata il 24 ottobre 2026 — #476 integrata e pubblicata

Merge del proprietario `d5c8fc2870869a23b3fe0640428e682931503655`, albero
`4c1c060d5328b5b17ebf1164bd56f7ce12582473`, identico alla head #476
`cb5af9084f9435f695d96be4bf308c571f552d52`. Nessun merge/deploy dell’assistente.
Pubblicazione: Pages push `40092635164` (#4238) SUCCESS, reporter live
`40094663950` SUCCESS. Questa verifica legge soltanto gli esiti pubblici dei run:
log, job Quick→Full della PR e A3 non sono stati riletti in questa sessione e
non vengono attestati qui. L’anteprima degli incroci resta opt-in e isolata.

Prossimo incremento A7.5.4: misura e revisione del perimetro preparato degli
incroci prima di qualunque rollout pubblico. La misura richiede la build
pubblica completa (`public_dist_required`) e quindi Chromium: va eseguita con
Quick/Full locali ordinari, non stimata. Restano invariati i divieti
`public=True, associations=True`, whitelist di domande e coppie scelte dal
coefficiente.

## Main precedente — #474 integrata e pubblicata

Merge del proprietario `c5386a38f4a5c490b0e10e0bfa1ca50d20c77a1c`, albero
`7a2afdac9b425cf6b52686325a3a226ae1510a1b`, identico alla head #474
`7c766b417215da9a41deb6aa157e12ffbe8425be`. Nessun merge/deploy dell’assistente.
CI Quick→Full effettivo nello stesso run `40032825527`, job `120685009917`
e `120698490944`, SUCCESS; A3 `40032825514`, job `120685007265`, SUCCESS.
Checkout effettivo `6d24726c` con il medesimo albero. Quick e Full locali
ordinari eseguiti PASS; il Full termina il 23 ottobre alle 23:34 UTC.
La conservazione del suo log è incompleta: ricevuta e rapporti disponibili,
quattro log completi su cinque. Non è un’attestazione archivistica completa;
limite e tentativi distinti nella #474, senza trasferimento di verdi.
Evidenze #474 `A7_EXPLICIT_ASSOCIATIONS_e6d52b0_evidenze.zip`, SHA256
`958c9cfeb9f8e706b92db512c7b80eb39cf39aceed345e99230ce64cdb2324c9`.

Pubblicazione verificata separatamente: Pages push `40070233147`, build
`120801890630` e deploy `120806424596` SUCCESS. Reporter `40071753266`, job
`120806501424` SUCCESS; checkout effettivo del merge nei log build/live.
Integrità Chiedi asset/hash, `ov-public-routes` e `ov-pages-live` PASS;
log live SHA256 `b9e998ad7e2d6a69e02c03cb5dbca3e34ed5044b2a65d537ce8b0200b7e26cec`.
Quick/Full skipped del push non sono nuovi gate. Il reporter è un campione
live di disponibilità/integrità, non certifica tutte le richieste numeriche.

A6 DONE: 225/225 adapter, 3.727 casi indipendenti, 35 letture e due riepiloghi,
Atlante 20.325 unità locali native, 40 golden e Camaiore congelata. A7
IN_PROGRESS. La #473 espone la tendenza nativa; la #474 integra il trasporto
opzionale dei piani di associazione, senza abilitarli nella build pubblica.
Ultima misura approvata dei profili pubblici: 50.523 richieste,
28.422 computed / 22.101 rifiuti, 127.146.205 byte gzip. Misura di trasporto,
non nuovi casi numerici indipendenti. Nessuna promozione in navigazione.

## Incremento integrato con la #476 — anteprima degli incroci guidati

Branch `feature/a7-guided-pair-selection`, base main #474. A7.5.4 resta aperta.
`build_a7_explorer_preview.py --associations` aggiunge nella stessa pagina due
variabili, asse, metodo, motivo/copertura, risultato e coppie originali A6.
Selezioni derivate dal piano ancorato, nomi/unità dal catalogo canonico:
nessuna whitelist di domande o coppia scelta dal coefficiente. Il grafico
proietta soltanto le coppie native; tabelle e fonti conservano periodi e unità.
Nessun coefficiente sostitutivo nei rifiuti, consenso esplicito e revoca dei
risultati superati durante il fetch. Metodo `A7_GUIDED_ASSOCIATION_PREVIEW.md`.

È un’opzione isolata: `public=True, associations=True` è vietato. Default,
materializzatore pubblico e interfaccia v6 restano invariati; soltanto questa
anteprima usa v7 e i due nuovi asset. Prima del rollout restano misura e
revisione del perimetro preparato. Non è interrogabilità universale né un
ampliamento automatico del runtime. Il motivo non viene riscritto: una modifica
richiede un’altra richiesta esatta e la sua materializzazione originale A6.

Il gate di trasporto esistente verifica anche la UI sulla shell canonica,
1440/390/320 px, parità nativa, selettori invertiti, rifiuto temporale A6,
testo ostile, consenso, cache, guasti/ripresa e selezione superata. Gli otto
casi originali del lettore conservano il proprio budget; tredici casi UI in
runtime separato, comprese omissioni di asse/metodo in gruppi sparsi e
allineamento delle coppie agli estremi etichettati delle scale; grafico
leggibile su colonne strette con scorrimento da tastiera e caratteri effettivi
controllati dopo la scala SVG. La prova preliminare del componente non certifica la pagina
completa. Preview reale, Quick/Full locali ordinari e CI Quick→Full/A3 richiesti
sul nuovo candidato; nessun verde della #474 trasferito. Evidenze nella PR.

Restano incroci pubblici, perimetro generale, riuso/CSV/PDF e consolidamento.
Dossier e Radar separati; nessuna acquisizione, modifica di adapter/dati/golden,
modello esterno, backend o costo ricorrente. Merge e deploy restano del proprietario.
