# Lotto A · Demografia v2

## Obiettivo

Completare le righe ad alta priorità del pacchetto candidati che risultano oggi solo parzialmente fruibili e rendere consultabili altri approfondimenti demografici senza moltiplicare inutilmente le card.

## Verifica dello stato attuale

- **Quota 80+ / 85+**: `80+` è già leggibile dentro `ageDistribution`; `85+` non è oggi esposto nel frontend.
- **Piramide per età e sesso**: il dettaglio POSAS 2026 per singola età e sesso è già acquisito nello snapshot della tranche Demografia, ma non esiste una visualizzazione pubblica.
- **Componenti della variazione demografica**: naturale, migrazione interna e migrazione con l'estero sono già disponibili in indicatori distinti, ma non esiste una lettura unificata collegata alla variazione della popolazione.
- **Stranieri per cittadinanza / paese di nascita**: la fonte Istat RCS è disponibile fino al 2025; questa tranche verifica lo schema reale dei download prima di esporre il dettaglio.

## Regola di promozione

Una riga del documento candidati viene marcata in verde solo quando il contenuto è realmente consultabile dal sito. Non è richiesta una card autonoma: sono ammessi selettori, disclosure, compositi e approfondimenti nelle schede comunali, purché siano leggibili e funzionali.

## Piano di implementazione

1. aggiornare `ageDistribution` con il POSAS 2026 e aggiungere una lettura esplicita `80+ / 85+`;
2. rendere disponibile una piramide per età e sesso nelle schede comunali, usando il dettaglio POSAS già acquisito;
3. aggiungere a `populationChange` un approfondimento sulle componenti naturale, interna ed estero sul più recente anno comune disponibile;
4. acquisire e rendere consultabile il dettaglio RCS 2025 per cittadinanza e paese di nascita, dopo probe strutturale 7/7;
5. mantenere il contratto globale di coerenza della #79 e i controlli desktop/mobile.
