# Audit v1.39.0 — Bilanci: liquidità, accantonamenti e missioni

Data audit: 13 settembre 2026

Baseline: `main` al commit `2592a4694c89fc80f30fd643e0efc6acb67e30d5` (merge PR #181, release pubblicata v1.38.0).

Questa tranche estende il tema Bilanci senza ridefinire gli indicatori esistenti. In particolare resta invariato `tourismDevelopmentMissionExpenditurePerResident`, che rappresenta la somma degli impegni delle Missioni 07 e 14 rapportata ai residenti.

## Stato attuale del tema Bilanci

La pipeline storica v1.6.0 usa Rendiconto OpenBDAP e SIOPE, con storico 2019–2025 e copertura 7/7 per il perimetro già pubblicato. Le missioni già materializzate sono 04, 05+06, 07+14, 09, 10 e 12. La v1.29.0 aggiunge il profilo finanziario/debito con letture 10.4 ricostruita, 6.1 e 10.3.

La v1.39 deve estendere gli snapshot/materializzatori esistenti, non creare una pipeline parallela.

## FCDE

Fonte primaria: Rendiconto OpenBDAP, Schemi di bilancio.

Valore principale: riga `Fondo crediti di dubbia esigibilità al 31/12/N` nella parte accantonata dell'`Allegato a) — Prospetto dimostrativo del risultato di amministrazione`.

Controllo di riconciliazione: il valore deve corrispondere al totale FCDE dell'`Allegato a/1 — Elenco analitico delle risorse accantonate` e al totale generale del fondo nel prospetto `Allegato c) — Fondo crediti di dubbia esigibilità`, quando i relativi quadri sono disponibili nel dataset OpenBDAP.

Metrica proposta: **FCDE per residente**. Il valore assoluto resta disponibile come dettaglio. Non viene introdotto in questa tranche alcun rapporto FCDE/crediti finché non viene individuato un denominatore unico, omogeneo e metodologicamente difendibile.

Il FCDE è un accantonamento del risultato di amministrazione a presidio del rischio di mancata riscossione dei crediti di dubbia e difficile esazione; non deve essere descritto come quota di crediti che l'ente “sa di non incassare”.

Stato: **GO**, subordinato alla riconciliazione automatica 7/7 sul raw ufficiale.

## Liquidità e anticipazioni

### PDI 3.1 — Utilizzo medio anticipazioni di tesoreria

Fonte: Rendiconto OpenBDAP, Piano degli indicatori, tipologia 03 / indicatore 01.

Definizione ufficiale: sommatoria degli utilizzi giornalieri delle anticipazioni nell'esercizio / `(365 × massimo previsto dalla norma)`.

È preferibile ai flussi lordi annuali di entrata/uscita perché misura l'intensità media di utilizzo rispetto al limite disponibile e non confonde automaticamente più cicli di utilizzo/rimborso con uno stock di liquidità.

Stato: **GO**, con controllo fail-closed su presenza 7/7, scala percentuale e valori anomali.

### PDI 3.2 — Anticipazioni chiuse solo contabilmente

Fonte: Rendiconto OpenBDAP, Piano degli indicatori, tipologia 03 / indicatore 02.

Definizione ufficiale: anticipazione di tesoreria all'inizio dell'esercizio successivo / massimo previsto dalla norma.

È una lettura complementare al 3.1 e non viene interpretata da sola come giudizio complessivo sulla salute finanziaria.

Stato: **GO**, come lettura secondaria della card composita di liquidità.

## Cassa vincolata

### Stock SIOPE 1450/1400 — escluso

Il codice SIOPE/OPI 1450 ha etichetta sintetica “quota vincolata” del fondo cassa 1400, ma il Vademecum OPI vigente chiarisce che riguarda le giacenze del conto di tesoreria vincolate per pignoramenti. Non rappresenta quindi l'intera cassa vincolata dell'ente ai sensi della disciplina contabile/TUEL.

Per questo **non viene pubblicato** il rapporto `1450 / 1400` con l'etichetta “quota di cassa vincolata”.

Le disponibilità 2200/2400 riguardano fondi vincolati presso conti diversi dal conto ordinario di tesoreria e non risolvono il problema di ricostruire uno stock generale omogeneo della cassa vincolata.

Stato: **NO-GO** per la metrica stock richiesta originariamente.

### Utilizzo degli incassi vincolati ex art. 195 TUEL — candidato utile

SIOPE registra invece in modo strutturato i flussi di gestione della cassa vincolata:

- `U.7.01.99.06.001` — Utilizzo incassi vincolati ai sensi dell'art. 195 TUEL;
- `E.9.01.99.06.001` — Destinazione incassi vincolati a spese correnti ai sensi dell'art. 195 TUEL;
- `U.7.01.99.06.002` — Destinazione incassi liberi al reintegro incassi vincolati;
- `E.9.01.99.06.002` — Reintegro incassi vincolati ai sensi dell'art. 195 TUEL.

Questi flussi descrivono il ricorso temporaneo a risorse vincolate per esigenze correnti e il successivo reintegro. Non misurano lo stock di cassa vincolata e il volume lordo può riflettere più cicli nel corso dell'anno.

Proposta: il valore `U.7.01.99.06.001 / residenti` può essere usato come terza lettura descrittiva della card composita di liquidità **solo se** l'estrazione centrale SIOPE Toscana conferma copertura 7/7 e storico omogeneo. Il reintegro viene conservato nello snapshot e mostrato nel dettaglio/tooltip come controllo contestuale, non trasformato in una pagella.

Non viene creato un rapporto artificiale con la spesa corrente né un saldo interpretato automaticamente come crisi di liquidità.

Stato: **GO CON RISERVA**, da chiudere con probe centrale SIOPE.

## Missioni da aggiungere

Fonte: `Rendiconto SDB Spese Riepilogo Missioni_TOSCANA.csv`, campo `Impegni`, popolazione residente al 1° gennaio già usata dalla pipeline Bilanci.

Nuove missioni candidate:

- Missione 01 — Servizi istituzionali, generali e di gestione;
- Missione 08 — Assetto del territorio ed edilizia abitativa;
- Missione 11 — Soccorso civile;
- Missione 14 — Sviluppo economico e competitività;
- Missione 17 — Energia e diversificazione delle fonti energetiche.

Formula comune: `impegni della missione / popolazione residente`.

La Missione 14 viene aggiunta come indicatore autonomo senza modificare, rinominare o ricostruire la serie legacy 07+14. La Missione 17 è descrittiva: un valore nullo o basso non implica assenza di politiche energetiche, perché interventi energetici e di efficientamento possono essere classificati in altre missioni/programmi.

Il nuovo estrattore deve distinguere riga presente con importo zero, riga assente e campo non valorizzato. Questa correzione viene applicata al nuovo perimetro senza riscrivere retroattivamente i valori v1.6 già pubblicati.

Stato: **GO**, subordinato al probe raw 7/7 per ogni annualità pubblicata.

## Perimetro minimo v1.39.0

La tranche target contiene 7 nuove metriche:

1. `fcdePerResident` — FCDE per residente;
2. `liquidityManagementProfile` — card composita con PDI 3.1, PDI 3.2 e, se supera il gate 7/7, utilizzo incassi vincolati ex art. 195 TUEL per residente;
3. `generalAdministrationMissionExpenditurePerResident` — Missione 01;
4. `territorialPlanningMissionExpenditurePerResident` — Missione 08;
5. `civilProtectionMissionExpenditurePerResident` — Missione 11;
6. `economicDevelopmentMissionExpenditurePerResident` — Missione 14;
7. `energyMissionExpenditurePerResident` — Missione 17.

Se il flusso SIOPE art. 195 non supera il gate, non viene sostituito con proxy o stime: la card `liquidityManagementProfile` resta limitata alle letture PDI 3.1 e 3.2 e il gap viene documentato.

## Esclusioni v1.39

Restano fuori: rapporto 1450/1400 come cassa vincolata generale; fiscalità locale; indicatore di tempestività dei pagamenti se non emerge una fonte centrale PCC/RGS pubblica, strutturata e riproducibile; generici aggregati di “tasse comunali”; nuove interpretazioni qualitative automatiche della Missione 01.

## Contratto CI per la Fase 2

Prima del browser QA devono passare:

- inventory dei workflow e rispetto di `ci/workflow-contract.json`;
- required checks canonici `quick` e `full`;
- build smoke canonico;
- audit `paths` dei workflow specializzati;
- controllo build non mutante;
- test di retrocompatibilità v1.6 e v1.29;
- gate 7/7 e zero-vs-n.d. per il nuovo perimetro;
- verifica dei file che il materializzatore può modificare;
- nessun indebolimento dei gate esistenti.

Le eccezioni, se necessarie, devono essere specifiche, documentate e fail-closed.
