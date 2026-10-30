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

## Fase successiva

Il motore è ancora una catena di sette strati che si sostituiscono funzioni a
vicenda (v04 → v041 … v044, daily, revalidated, resilient, stable, audit_fixed).
Dopo aver verificato sul campo la qualificazione automatica, la fase 2 sostituisce
la catena con una pipeline unica (scoperta → qualificazione → ciclo di vita →
pubblicazione), con i casi noti dei corpora curati trasformati in test di
regressione invece che in fonti di pubblicazione.
