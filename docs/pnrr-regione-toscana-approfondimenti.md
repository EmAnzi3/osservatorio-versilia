# PNRR · approfondimenti estraibili da Regione Toscana

Bozza metodologica collegata alla PR #75. La fotografia analizzata è quella del **11 agosto 2026** e usa il perimetro validato: `area = PNRR` o `PNRR-PNC`, PNC puro escluso, Comune tra i sette soggetti attuatori, deduplicazione su `id_progetto`.

## Quadro validato

- 101 progetti PNRR/PNRR-PNC
- 74 in `fase_avanzamento_da_regis = 5. conclusione`
- 26 in `4. esecuzione`
- 1 in `3. stipula`
- € 36.683.107,64 di finanziamento PNRR censito

Il dataset consente molto più dei due indicatori oggi pubblicati, ma non tutto ciò che è disponibile va trasformato in un nuovo indicatore.

## Approfondimento consigliato: opere fisiche PNRR

Il campo `natura` permette di separare in modo netto i progetti che hanno per oggetto **lavori pubblici / opere e impiantistica** dai servizi digitali e dagli acquisti di beni.

Nella fotografia corrente risultano **22 opere fisiche**, per **€ 28.859.445,16 di quota PNRR**, pari al 78,7% delle risorse PNRR dei 101 progetti.

Per evitare di chiamare impropriamente “realizzata” un'opera solo perché il progetto è nella macrofase `5. conclusione`, il dettaglio più informativo è `fase_regis`:

| Stato di dettaglio ReGiS | Opere | Finanziamento PNRR |
|---|---:|---:|
| Collaudo completato | 7 | € 5.830.474,87 |
| Collaudo avviato | 12 | € 18.593.970,29 |
| Lavori in esecuzione | 1 | € 2.500.000,00 |
| Contratto stipulato | 1 | € 1.440.000,00 |
| Stipula in corso | 1 | € 495.000,00 |

Questa è una lettura migliore di un semplice “realizzate / non realizzate”: distingue le opere formalmente collaudate da quelle che hanno terminato la fase di realizzazione ma hanno ancora il collaudo in corso.

### Le 22 opere

| Comune | Opera | Stato ReGiS di dettaglio | Quota PNRR | CUP / ID progetto |
|---|---|---|---:|---|
| Camaiore | Efficientamento energetico del Teatro dell'Olivo | Collaudo completato | € 240.000,00 | `D34H22000110001` |
| Camaiore | Nuovo intervento per asili nido / prima infanzia | Contratto stipulato | € 1.440.000,00 | `D35E24000010006` |
| Camaiore | Cucina nido d'infanzia Mafalda | Collaudo avviato | € 170.000,00 | `D38H22000110006` |
| Forte dei Marmi | Nuova mensa scuola Don Milani | Collaudo avviato | € 304.640,00 | `F21B22000330008` |
| Forte dei Marmi | Nuovi spazi mensa scuola Guidi | Collaudo avviato | € 499.200,00 | `F25E22000440006` |
| Massarosa | Asilo nido Girotondo a Piano di Mommio | Collaudo avviato | € 1.374.750,00 | `C75E22000250006` |
| Massarosa | Piscina comunale G. Frati | Collaudo avviato | € 3.762.422,13 | `C78E22000040006` |
| Pietrasanta | Efficientamento Teatro Comunale | Collaudo avviato | € 250.000,00 | `G42H22000020001` |
| Pietrasanta | Nuovo polo scolastico Marina di Pietrasanta | Collaudo avviato | € 5.705.263,79 | `G43H17000050004` |
| Pietrasanta | Rigenerazione Ex-Camp | Collaudo avviato | € 2.803.289,07 | `G44E21000590004` |
| Seravezza | Nuova palestra scuole Frediani | Collaudo avviato | € 948.022,00 | `B81B22000710006` |
| Seravezza | Nuovo nido d'infanzia | Collaudo avviato | € 1.250.000,00 | `B81B22000730006` |
| Stazzema | Accessibilità Museo e Parco nazionale della Pace di Sant'Anna | Stipula in corso | € 495.000,00 | `H17B22000430006` |
| Stazzema | Mitigazione rischio idrogeologico Rio delle Vigne di Pomezzana | Collaudo completato | € 290.000,00 | `H17C20000010001` |
| Stazzema | Scuola materna Martiri di Mulina | Collaudo completato | € 1.080.000,00 | `H18E18000010001` |
| Viareggio | Recupero Stadio comunale dei Pini | Collaudo completato | € 2.249.875,73 | `B43D21001410004` |
| Viareggio | Riqualificazione Marina di Torre del Lago | Collaudo avviato | € 1.131.347,78 | `B43D21001420004` |
| Viareggio | Riqualificazione Belvedere Torre del Lago | Collaudo completato | € 570.606,86 | `B43D21001430004` |
| Viareggio | Recupero area pubblica via Mazzini | Collaudo completato | € 1.149.992,28 | `B43D21001440004` |
| Viareggio | Recupero piazza Piave | Collaudo avviato | € 395.035,52 | `B43D21001450004` |
| Viareggio | Efficientamento Teatro Jenco | Collaudo completato | € 250.000,00 | `B44J22000010005` |
| Viareggio | Nuova piscina comunale | Lavori in esecuzione | € 2.500.000,00 | `B45B22000200001` |

## Cosa aggiungerei al sito

### 1. Un approfondimento “Dentro il PNRR”, non nuovi indicatori

Per non aumentare il catalogo corrente di **138 indicatori**, i dati di dettaglio possono diventare un modulo collegato a `pnrrFunding` e `pnrrConcluded`:

- numero assoluto dei progetti oltre alla percentuale;
- ripartizione nelle macrofasi ReGiS;
- elenco dei 101 progetti con CUP, titolo, Comune, quota PNRR, natura e fase;
- filtro specifico “Opere fisiche” con i 22 lavori pubblici;
- mappa delle opere fisiche usando le coordinate del dataset regionale;
- scheda sintetica di ciascuna opera.

### 2. Stato delle opere fisiche

È il valore aggiunto più forte. Per le opere userei queste etichette pubbliche, sempre accompagnate dalla dicitura “stato ReGiS”:

- **Collaudo completato**;
- **Collaudo in corso**;
- **Lavori in esecuzione**;
- **Contratto stipulato / stipula in corso**.

Non userei la parola “realizzata” come sinonimo automatico di `5. conclusione`, perché 12 delle 19 opere in macrofase conclusione hanno ancora `COLLAUDO avviata`.

### 3. Temi dei progetti

Il campo `argomento_per_sito_web` è completo 101/101 e permette una lettura editoriale semplice: connettività, PA, scuole e istruzione, rigenerazione urbana, vulnerabilità, cultura, sport e tutela del territorio. È utile come filtro e come grafico di composizione, ma non merita un indicatore autonomo.

## Cosa non pubblicherei ancora come indicatore

### Avanzamento finanziario / pagamenti

Il feed espone `pagamenti_totali`, `impegni_totali` e piano dei costi quasi per tutti i progetti. Sono promettenti, ma prima di derivare una “percentuale spesa” va verificato in modo specifico il denominatore corretto e la comparabilità tra quota PNRR, costo totale del progetto e cofinanziamenti. Non va presentata come avanzamento fisico.

### Date di inizio e fine

Le date effettive sono troppo incomplete nella fotografia corrente e alcuni campi di collaudo contengono valori sentinella come `1899-12-30`. Non sono adatte a un indicatore pubblico senza ulteriore pulizia e validazione.

### Stato gare / CIG

Il riepilogo contratti è disponibile per 79 progetti su 101. Può diventare un secondo livello di dettaglio sfruttando anche il dataset correlato CIG della Regione, ma non lo userei adesso come metrica principale.

## Proposta

Prima iterazione consigliata:

1. adottare Regione Toscana per i due indicatori PNRR esistenti;
2. non aumentare il numero degli indicatori;
3. aggiungere in un secondo passaggio un approfondimento **Dentro il PNRR**;
4. partire dall'elenco progetto-per-progetto e dalla sezione **22 opere fisiche** con stato ReGiS e mappa;
5. lasciare pagamenti e CIG a una successiva validazione metodologica.
