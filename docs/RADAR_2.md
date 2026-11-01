# Radar Opportunità 2.0 — dal monitoraggio alla qualificazione automatica

Decisione del proprietario del 30 ottobre 2026: il Radar deve funzionare senza
correzioni bando per bando. Questo documento spiega perché finora non era così e
che cosa cambia.

## Diagnosi (snapshot del 30 ottobre 2026)

- **Le segnalazioni non diventavano mai schede.** Il discovery produceva 188
  segnalazioni (fra cui prevenzione sismica nelle scuole, Sport illumina, Fondo
  asili nido), ma la promozione documentale accettava un solo formato di avviso
  ministeriale e ne pubblicava zero. Delle 59 schede pubblicate, 39 venivano da
  corpora curati a mano (matrice comunale e audit), 16 da regole di copertura
  scritte per il singolo bando, 4 da regole dedicate.
- **Le fonti europee restituivano zero in silenzio.** La ricerca del portale
  Funding & Tenders è una pagina generata via JavaScript: scaricata come HTML è
  vuota, ma la fonte risultava «ok». La fonte CERV puntava alla presentazione del
  programma, senza elenco dei bandi. I due inviti CERV-DAPHNE aperti il 7 luglio
  2026 sono entrati il 28-29 ottobre solo grazie a un audit indipendente.
- **Nessuna misura del ritardo.** Il KPI di rilevazione era «in attesa di date
  documentate»; nell'audit la mediana fra pubblicazione e scoperta era 116 giorni.

## Che cosa cambia

1. **Qualificazione automatica** (`opportunity_qualifier.py`). Ogni segnalazione
   viene letta (pagina e fino a tre documenti ufficiali) e qualificata con regole
   generali: avviso e non notizia/esito; Comuni o enti locali fra i soggetti
   ammessi (frase citata); scadenza futura o sportello (frase citata); nessuna
   riserva per un'altra regione. Le schede qualificate sono pubblicate subito con
   l'etichetta «Requisiti da confermare» e le citazioni dei documenti; restano
   fino alla scadenza anche se un giorno la pagina non risponde.
2. **Fonte UE strutturata** (`opportunity_eu_calls.py`). Interfaccia di ricerca
   ufficiale del portale (chiave pubblica SEDIA) e schede JSON dei topic: tutti i
   topic aperti o in arrivo dei programmi a gestione diretta. Per i programmi UE
   servono menzioni esplicite di autorità locali, Comuni o città: «public
   bodies» da solo non basta. Una ricerca fallita è un errore, mai uno zero.
3. **Fonti da riparare.** Una fonte raggiunta che non produce segnalazioni viene
   contata giorno per giorno; pagine quasi vuote (probabile JavaScript) o 14 giorni
   di zeri finiscono nel rapporto fra le «Fonti da riparare».
4. **Ritardo di rilevazione.** Per le schede con data di pubblicazione il rapporto
   riporta la mediana fra pubblicazione e prima rilevazione negli ultimi 30 giorni
   ed elenca quelle oltre i 7 giorni.
5. **Rapporto sulle PR.** Le PR che toccano il Radar eseguono uno scan live: il
   rapporto viene pubblicato come commento, così l'effetto si verifica sulla PR.

## Verifica sul campo (30 ottobre 2026)

- **Fonte UE**: 1.211 topic aperti o in arrivo, 101 dei programmi pertinenti con
  scadenza futura. Qualificati i due CERV-DAPHNE (Comuni richiedenti diretti,
  scadenza 5 novembre 2026) e tre topic Horizon Missions in cui le città sono
  partner. Escluso il topic della European City Facility (un solo consorzio
  gestore: i Comuni ne sono destinatari).
- **Segnalazioni italiane** (137 lette): pubblicato il bando ANCI-CONAI per la
  comunicazione locale (domande entro il 13 novembre 2026); riconosciuti come già
  chiusi l'avviso MIM otto per mille (5-23 ottobre 2026), l'avviso antincendio
  scuole e gli altri avvisi scaduti; esclusi comunicati su rendiconti, riparti e
  conclusione dei lavori. La scadenza è sempre un termine per la domanda, mai un
  termine di esecuzione o di rendiconto.
- L'avviso MIM otto per mille era fra le segnalazioni dal 5 ottobre: con la
  qualificazione automatica sarebbe stato pubblicato il giorno stesso.

## Fonti bloccate ma coperte (31 ottobre 2026)

Il sito del GSE rifiuta i server della CI con il firewall (403, poi 401 anche
dalle vie alternative). Non si ripara dal codice. Decisione del proprietario: se
il blocco è del sito e almeno una fonte di copertura risponde (MASE · Bandi e
avvisi, ANCI, ANCI Toscana), il GSE non compare fra le «Fonti da riparare» ma
fra le «Fonti bloccate ma coperte». Le FAQ del portale di assistenza GSE restano
il controllo diretto. Un errore diverso (timeout, pagina cambiata) o l'assenza
di coperture lo riporta fra le fonti da riparare.

## Correzioni dopo il primo run di produzione (31 ottobre 2026)

Il run del 31 ottobre ha letto 120 segnalazioni senza qualificarne nessuna.
Due regole erano troppo strette per i topic UE:

- l'anno nel codice del topic (I3-2024-INV1) veniva letto come anno
  dell'avviso: con una scadenza strutturata futura ora decide la scadenza;
- «public authorities can be national, regional or local…» con l'autorità
  pubblica nel consorzio come beneficiaria è una partecipazione da partner;
  la frase sui soggetti può essere spezzata da note a piè di pagina, quindi nei
  topic UE la si cerca entro 1.200 caratteri. «Public authority» senza livello
  locale resta insufficiente.

Sui 101 topic UE in coda il risultato è CERV-2026-DAPHNE-PREVENTION e
CERV-2026-DAPHNE-PROTECTION come partner (scadenza 5 novembre 2026), oltre ai
due DAPHNE già pubblicati; nessun altro topic cambia esito.

Verifica sul testo (1° novembre 2026): i topic DAPHNE condividono un'unica call
fiche, quindi il qualificatore leggeva per tutti lo stesso documento e citava la
frase di un'altra priorità. Per PROTECTION (priorità 2) e PREVENTION
(priorità 3) la call fiche richiede un consorzio di almeno due beneficiari con
capofila non profit; gli enti pubblici possono essere beneficiari e il
coinvolgimento dell'autorità pubblica è raccomandato, non obbligatorio. Il ruolo
«partner» era corretto. Le due schede ora sono verificate come CONVENTION-DIR e
CHILDREN (call fiche + portale, nello stesso run) e, quando la verifica riesce,
sostituiscono quelle automatiche sullo stesso URL (`replacedAutoQualified`).
Se la verifica non riesce, la scheda automatica resta. Resta da correggere nel
qualificatore l'attribuzione dei requisiti quando più topic condividono un
documento.

## Fase successiva

Il motore è ancora una catena di sette strati che si sostituiscono funzioni a
vicenda (v04 → v041 … v044, daily, revalidated, resilient, stable, audit_fixed).
Dopo aver verificato sul campo la qualificazione automatica, la fase 2 sostituisce
la catena con una pipeline unica (scoperta → qualificazione → ciclo di vita →
pubblicazione), con i casi noti dei corpora curati trasformati in test di
regressione invece che in fonti di pubblicazione.
