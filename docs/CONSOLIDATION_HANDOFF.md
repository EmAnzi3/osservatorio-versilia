# Osservatorio Versilia — consolidation handoff

Questo file è il punto di ripartenza operativo per ogni nuova sessione dedicata al consolidamento. Deve restare breve: cronologia e dettagli appartengono a Git e alle pull request.

## Stato corrente

- **Programma:** consolidamento Osservatorio Versilia
- **Workstream attivo:** `A3 — Enrichment Audit globale`
- **Step attivo:** `A3.2` — classificazione indicatore × dimensione
- **Stato:** `IN_PROGRESS`
- **Main verificato:** `1d5c7a55e1f8fb0c86270805e9bdeafd1889258e` (merge `#249`)
- **Catalogo pubblico governato:** 225 indicatori
- **Matrice A3.2 post-#249:** 2.025 coppie; **1.829 classificate, 196 residue**
- **A3 final head #249:** run `35425030884` **GREEN**
- **Pages final head #249:** run `35425030885` **GREEN** (Quick + Full)
- **Pages post-merge #249:** run `35426730224` **GREEN**
- **Live status post-merge #249:** run `35427006980` **GREEN**
- **Bucket C:** **0**
- **Bucket D:** **196**
- **Branch corrente:** `chore/a3-2-frequency-evidence-batch`

## Residuo effettivo post-#249

Le **196** coppie residue coincidono con il bucket D. La dimensione più numerosa ancora aperta è `frequenza_infra_annuale`, con **41** coppie.

La verifica delle fonti ha mostrato che i nomi dei source profile non bastano per classificare: Demo Istat espone dati demografici mensili per alcuni stock/flussi e la rilevazione Istat sugli incidenti è mensile. Le classificazioni devono quindi seguire la disponibilità reale della fonte, non l'etichetta del profilo.

## Intervento corrente — batch D frequenza

Il batch classifica **31** coppie `frequenza_infra_annuale` in una sola PR:

- **19 ARS Toscana:** `SOURCE_UNAVAILABLE` a livello source-profile; il portale comunale espone ultimo anno disponibile e trend storico, con profilo annuale o pluriennale.
- **6 Demo Istat:** `AVAILABLE_MISSING` per `population`, `populationChange`, `naturalDemographicDynamics`, `internalResidentialMobility`, `foreignResidentialMobility`, `totalResidentialMobility`, perché il Bilancio demografico mensile espone a livello comunale le componenti necessarie.
- **3 Demo Istat:** `SOURCE_UNAVAILABLE` per `ageDistribution`, `dependencyIndices`, `foreignResidents`, perché età e cittadinanza sono diffuse negli stock annuali al 1° gennaio e non nel bilancio mensile equivalente.
- **`roadSafety`:** `AVAILABLE_MISSING`; la rilevazione Istat sugli incidenti è mensile e contiene la data dell'evento.
- **`roadFinesPerResident`:** `SOURCE_UNAVAILABLE`; la fonte governata espone la serie annuale dei proventi rendicontati.
- **`incomeVsInflation`:** `SOURCE_UNAVAILABLE`; il reddito comunale MEF è annuale e vincola la frequenza dell'indicatore combinato anche se il NIC esiste mensilmente.

**Esito atteso:** **1.860 classificate / 165 residue**.

## Decisioni vincolanti

1. `data/site-data.json` resta l'unico catalogo canonico sorgente.
2. Nessun secondo inventario manuale di indicatori.
3. `ACQUIRED` solo da evidenza strutturata o formula verificata.
4. `AVAILABLE_MISSING` / `SOURCE_UNAVAILABLE` solo con evidenza ufficiale verificabile.
5. `NOT_APPLICABLE` solo metric-specific e semanticamente dimostrabile.
6. Classificazioni source-profile solo se valide per tutto il profilo.
7. A3.2 non è chiuso finché `unclassifiedPairCount = 0`.
8. Nessun A3.3 prima dello zero.
9. Preferire batch sostanziosi verificati prima dell'apertura PR per evitare cicli CI ripetuti.
10. Nessun merge/pubblicazione senza A3, Quick e Full GREEN sul final head e approvazione esplicita del proprietario.

## Prossima azione esatta

1. Aprire una sola PR sul branch corrente.
2. Eseguire un solo ciclo A3 Enrichment Audit + Quick + Full sul final head.
3. Verificare nel log A3 il conteggio esatto **1.860 / 165** e le 31 classificazioni.
4. Fermarsi prima del merge.
5. Dopo merge autorizzato, ricostruire le 165 residue e preparare un altro batch sostanzioso, non una micro-tranche.
