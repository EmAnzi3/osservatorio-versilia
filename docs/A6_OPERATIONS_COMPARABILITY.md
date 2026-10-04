# A6.2–A6.3 — operazioni e comparabilità

## Perimetro e stato

A6.1 è pubblicata con #301, main `5abab28dbb3b82fbb76eb9fee5ef4ca5c1a5f79c`, deploy `37235624195` SUCCESS. Questo lotto definisce il contratto delle operazioni e controlli eseguibili di **ammissibilità**, senza modificare dati o interfaccia. Non è il motore di calcolo A6.4 e non certifica automaticamente la comparabilità dei 225 indicatori effettivi. A6.5 e A7 devono attendere adapter e risultati riproducibili.

`ci/semantic-operations-contract.json` è il contratto; `scripts/semantic_operations.py` applica le precondizioni. `assess` restituisce ammissibilità, motivi, avvertenze, copertura, osservazioni originali, formula e policy. I riferimenti metodologici sono attestazioni esplicite del chiamante, da revisionare: una stringa presente o una pagina raggiungibile non ne verifica il contenuto.

## Osservazione e provenienza

Ogni osservazione indica chiave canonica dell'indicatore, dimensione selezionata, codice comunale, periodo dichiarato, unità, popolazione di riferimento, definizione, metodo, frequenza, valore, fonte e riferimento di evidenza. A6.4 dovrà aggiungere percorso preciso nel catalogo/snapshot, hash/versione, data di estrazione e adapter, mantenendo i riferimenti a componenti e fonti originali. Non dedurre definizione o popolazione dal nome dell'indicatore; non ricostruire denominatori da un tasso arrotondato.

Le unità `number`, `currency`, `percent` ecc. non bastano da sole: residenti e contribuenti sono universi diversi. Fonte identica non dimostra continuità metodologica. I periodi sono token opachi: `2024`, `2024/25`, `2024-09` e una data precisa non sono intercambiabili. Un riferimento normativo composito non è una serie cronologica. L'ordine temporale è esplicito; per una pendenza occorre anche un asse di tempo crescente con distanze effettive, senza comprimere anni mancanti.

## Operazioni consentite

| Operazione | Definizione | Condizioni aggiuntive |
|---|---|---|
| Confronto | Valori affiancati e copertura | Stesso indicatore, dimensione, periodo, unità, universo e metodo |
| Serie | Osservazioni dichiarate, senza interpolazione | Stesso territorio e contesto, ordine esplicito |
| Variazione assoluta | finale − iniziale | Due periodi ordinati, stesso territorio/contesto |
| Variazione relativa | (finale − iniziale) / iniziale × 100 | Base diversa da zero; significato della scala da validare nell'adapter |
| Punti percentuali | percentuale finale − iniziale | Entrambi in percentuale; 50→55 = +5 punti, +10% relativo |
| Scostamento benchmark | valore comunale − benchmark | Stesso periodo e definizione, attestazione specifica di comparabilità |
| Rango | Valori decrescenti, pari merito con salti | Stesso contesto; rango numerico non equivale a qualità |
| Trend | Pendenza OLS sul tempo esplicito | Almeno tre osservazioni, unità temporale dichiarata; non è previsione |
| Correlazione | Pearson o Spearman con ranghi medi per i pari | Due variabili scelte, asse esplicito, coppie allineate, almeno tre coppie non costanti |
| Anomalia | Regola rispetto a distribuzione dichiarata | Evidenza della distribuzione e regola esplicita; implementazione della regola in A6.4 |
| Rapporto aggregato | somma numeratori / somma denominatori × scala | Componenti coerenti col valore, denominatori positivi, popolazioni disgiunte attestate |

Il contratto non esegue queste formule: un esito ammissibile autorizza solo il passaggio a un futuro adapter/calcolatore verificato. Significato della scala, valuta nominale/reale, soglie d'anomalia, pesi e robustezza restano responsabilità esplicite del motore. Non usare una semplice media dei tassi per rappresentare il territorio.

## Mancanti e copertura

Null, dato non disponibile e non applicabile non diventano zero. Le esclusioni sono restituite con indici e copertura; risultati parziali richiedono opt-in esplicito. Nei confronti a coppie l'allineamento è per codice comunale o periodo, mai per posizione nell'array. A6.4 dovrà esporre anche elenco di coppie escluse, copertura attesa e motivi dettagliati, senza perdere i valori validi.

## Matrice derivata e adapter

`coverage_matrix(catalog)` produce una voce per **ogni** indicatore del catalogo fornito, senza inventario parallelo. Individua le serie years/values anche annidate, i contenitori benchmark (anche con nomi specializzati), rapporti, normalizzazioni, parti, sesso, lavoro e accountingSeries. Le operazioni restano `requires_explicit_context`; un carrier presente è input disponibile, non calcolo validato. Contenitori specializzati richiedono adapter e contesto. Una serie vuota resta vuota.

La matrice è un primo audit strutturale, non un inventario completo delle dimensioni semantiche: adapter di A6.4 devono espandere ogni contenitore e riconciliare l'intero catalogo effettivo, inclusi benchmark specializzati, archivi sesso e file esterni. Il MIMIT mensile esterno non compare magicamente nelle serie puntuali: occorre un adapter con manifest e hash. Il controllo sorgente è nel Quick; il controllo effettivo viene ripetuto dopo build in `test_site_consistency.py`.

## Esempi reali da rispettare

- Residenti Massarosa e Camaiore: confronto corrente ammesso con periodo e definizione POSAS condivisi. Il test usa i valori effettivamente presenti, senza modificarli.
- Residenti 2026 e reddito MEF 2024: non formano una fotografia temporale omogenea. Se si vuole studiare un'associazione, selezionare un anno realmente comune e documentare residenti/contribuenti, copertura e limiti.
- `femaleEmploymentRate`: valore principale 2023 e `a3LabourDimensions.year` 2024 non si possono trattare come dimensioni del medesimo dato corrente.
- Reddito: imponibile e complessivo non sono la stessa misura; nominale e reale non si mescolano. La nota della serie MEF supporta la definizione storica, non ogni possibile aggregazione.
- Carburanti: fotografie puntuali irregolari e medie mensili sono metodi/frequenze diversi; settembre 2026 ha 29/30 giorni, senza interpolazione del 5 settembre.
- Spesa rigida: anni 2019–2022 e 2025 non autorizzano a inventare 2023–2024 né a trattare ogni passo come un anno.

## Interpretazione territoriale e politiche

Ogni futura lettura distingue **osservazione**, **calcolo**, **associazione**, **ipotesi** e **proposta di politica**. Correlazione non prova causalità; aggregati comunali non descrivono automaticamente persone o quartieri. Sette comuni non costituiscono per default un campione indipendente. Il minimo di tre coppie è un limite tecnico di questo progetto, non una certificazione di potenza statistica: no significatività o causalità automatica.

Confronti tra variabili diverse possono avere unità e universi diversi, ma richiedono attestazione specifica del significato della coppia; dentro ogni variabile il contesto deve essere coerente. Ogni coppia condivide periodo e frequenza; nelle correlazioni temporali anche il territorio. Dichiarare metodo, n, copertura, valori estremi, denominatori condivisi, trend comuni e autocorrelazione per le serie. Niente scansione indiscriminata di correlazioni o graduatorie universali.

Prima lettura utile: bisogno territoriale → evidenza disponibile → destinatari/ipotesi → intervento proposto → indicatore di risultato → controllo nel tempo. Le priorità vanno discusse con chi conosce i territori, usando profili multidimensionali e verifiche di sensibilità, non un punteggio composito arbitrario. Scenari richiedono ipotesi e intervalli espliciti; non presentare una correlazione come effetto atteso dell'intervento.

## Verifica e sviluppo successivo

Regressioni: periodi annuali/scolastici/mensili/data/normativi, unità/definizioni/universi/metodi incompatibili, contesto assente, duplicati, null/NaN/bool, base zero, punti percentuali, componenti di rapporto incoerenti, ordine e distanze temporali, benchmark non attestato, pairing per chiave, variabili costanti, unità diverse ammesse nella correlazione, copertura parziale. Quick e Full canonici restano obbligatori.

A6.4: adapter versionati, normalizzazione senza perdita di dimensioni, calcolatori con test numerici indipendenti, output con provenienza completa, audit di copertura per dimensione/operazione, esclusioni dettagliate, robustezza e piccoli campioni. A6.5: poche domande territoriali concordate e verificabili prima di automatizzare narrazioni. A6.6: portare avvertenze e limiti dentro gli output pubblici, oltre a questo contratto.
