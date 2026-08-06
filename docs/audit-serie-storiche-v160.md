# Audit delle serie storiche — v1.6.0

## Stato del prototipo

La prima implementazione espone la vista storica solo quando il dataset locale contiene almeno due annualità omogenee per tutti e sette i Comuni. In questa fase risultano 28 indicatori storicizzabili.

Il numero non rappresenta il limite delle fonti pubbliche: rappresenta soltanto la copertura delle serie già materializzate nel file `site-data.json`.

## Prima fascia — recupero ad alta affidabilità

### Demografia
- quota residenti 0–14 anni;
- quota residenti 65 anni e oltre;
- serie più lunga di popolazione e indice di vecchiaia.

Fonte: Istat, `A misura di Comune` e popolazione residente.

### Redditi
- reddito medio per dichiarante;
- dichiaranti fino a 15.000 euro.

Fonte: Dipartimento delle Finanze, dataset comunali annuali IRPEF.

### Lavoro e istruzione
- occupazione, disoccupazione e attività;
- diploma o titolo superiore;
- titolo terziario;
- possibili serie di genere dopo verifica puntuale delle definizioni.

Fonte: Istat, `A misura di Comune`, serie dal 2014.

### Scuola
- sedi scolastiche;
- alunni;
- alunni per classe;
- tempo pieno nella primaria, previa verifica della continuità del flusso.

Fonte: MIM, open data annuali per scuola statale e paritaria.

### Turismo
- presenze e arrivi;
- quota straniera;
- permanenza media;
- stagionalità;
- intensità turistica;
- strutture e posti letto.

Fonte: Regione Toscana, tavole comunali annuali sul movimento e sull’offerta ricettiva.

### Mobilità e ambiente
- motorizzazione;
- quota di autovetture Euro 0–3;
- superficie totale di suolo consumato.

Fonti: ACI, serie comunali dal 2015; ISPRA, consumo di suolo.

### Bilanci
- estensione dal biennio 2024–2025 alla serie armonizzata 2016–2025 per gli indicatori di rendiconto;
- ricostruzione pluriennale dei cinque indicatori SIOPE di cassa;
- incidenza delle spese rigide solo negli anni privi di anomalie ufficiali.

Fonte: OpenBDAP e SIOPE.

## Seconda fascia — audit tecnico necessario

### Salute
Il portale ARS Toscana espone serie per numerosi indicatori comunali, ma l’estrazione automatica deve verificare:
- scala geografica realmente comunale;
- annualità disponibili;
- standardizzazione per età;
- eventuali periodi pluriennali;
- revisioni dell’ultimo anno.

### Imprese e valore aggiunto
ASIA e Frame SBS sono annuali, ma occorre verificare per ogni flusso:
- continuità della granularità comunale;
- stabilità delle classificazioni ATECO;
- copertura dei sette Comuni;
- distinzione tra unità locali, imprese e addetti.

### Abitare
Le annualità del Censimento permanente possono consentire serie ulteriori, ma vanno ricostruite con lo stesso tracciato e la stessa definizione per tutti gli anni.

## Indicatori che probabilmente resteranno puntuali

- pendolarismo comunale, finché non sarà disponibile una nuova matrice omogenea;
- esposizione ad alluvioni e frane, se riferita a un’unica fotografia territoriale;
- punti di ricarica elettrica, in assenza di snapshot ufficiali storici;
- PNRR, opere pubbliche e RUNTS, salvo costruzione di snapshot annuali verificabili.

## Obiettivo realistico

- prima fase: circa 45–50 indicatori con almeno due annualità comparabili;
- seconda fase: circa 55–65, solo se ARS, ASIA/Frame SBS e Censimento permanente superano la verifica 7/7 e di continuità metodologica.

Non devono essere create serie tramite interpolazioni, copie dell’ultimo dato o combinazioni di definizioni differenti.
