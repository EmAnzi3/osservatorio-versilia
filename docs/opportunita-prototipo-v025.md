# Radar Opportunità Versilia — v0.2.5

La v0.2.5 è una fase di **hardening**. Non aggiunge nuove fonti live e non modifica la UI v0.2.4: rende misurabile e più resistente il motore prima della v0.3.

## Obiettivi

1. backtest curato sugli ultimi 90 giorni;
2. deduplicazione deterministica;
3. continuità e archivio senza sparizioni silenziose;
4. matrice di copertura/health delle fonti;
5. baseline quantitativa prima di ampliare il bacino di ricerca.

## Backtest 90 giorni

`data/opportunity-backtest-v025.json` contiene casi documentati delle fonti già integrate, con fonte ufficiale e verità attesa (`operational` / `non_operational`). Il test misura la capacità decisionale sui candidati osservabili nelle fonti integrate; non viene presentato come misura della completezza dell'intero web.

Soglie minime iniziali: precision >= 95%; recall >= 85%.

Il caso `Bando per contributo a musei ed ecomusei di rilevanza regionale 2026` resta deliberatamente nel dataset come controllo di falso negativo: la rilevanza territoriale è concreta almeno per Viareggio, ma manca ancora una mappa strutturata tra titolarità comunale e musei/ecomusei accreditati. Il caso deve emergere nel report, non essere nascosto.

La v0.2.5 aggiunge la regola storica per `Sistema integrato 0-6 anni 2026-2027`: la Regione ammette i Comuni/Unioni capofila delle Conferenze zonali e la documentazione territoriale identifica Camaiore come capofila della Zona Versilia; gli altri sei Comuni partecipano tramite la programmazione zonale.

## Deduplicazione

I candidati operativi sono raggruppati tramite titolo normalizzato + scadenza. Prevale la fonte con priorità più alta, si conserva `also_seen_in` e la matrice comunale viene unita senza degradare uno stato più forte. Stesso titolo con scadenze differenti non viene collassato.

## Continuità e archivio

Se un'opportunità era presente nel run precedente ma non è più rilevata e la scadenza è ancora futura, entra in `continuityHold` e il comando termina con codice 2. Se la scadenza è passata viene archiviata. Se un'opportunità archiviata ricompare come attiva viene rimossa dall'archivio.

## Copertura fonti

Monitorate: Regione Toscana (`active`), Fondazione Cassa di Risparmio di Lucca (`active`), PA Digitale 2026 (`degraded`, dataset stale e solo accessorio).

Pianificate per v0.3: PR Toscana FESR/FSE+, GSE, ANCI/ANCI Toscana, Ministeri e Dipartimenti. Pianificate per v0.4: Interreg e programmi UE diretti.

## Persistenza

Il workflow recupera l'ultimo artifact v0.2.5 dello stesso branch, con fallback al precedente v0.2.4 per la prima migrazione. La retention passa a 90 giorni. Per la futura v1.0 la persistenza dovrà essere spostata su storage/versionamento dedicato.

## Vincoli

Nessuna nuova fonte live, nessuna nuova route pubblica, nessuna modifica alla sitemap, nessun merge e nessuna pubblicazione. La UI resta v0.2.4; il motore/output diventano v0.2.5.
