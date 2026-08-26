# Copertura delle serie storiche

## Stato della v1.8.0

- 106 indicatori complessivi;
- 43 indicatori con almeno due annualità comunali;
- 63 indicatori senza una serie comunale omogenea già verificata;
- nessuna interpolazione o stima dei valori mancanti.

## Primo lotto v1.8.0

I dati per sezione del Censimento permanente Istat permettono un confronto
omogeneo tra 2021 e 2023 per sette indicatori:

- tasso di occupazione femminile 15–64 anni;
- tasso di occupazione maschile 15–64 anni;
- divario occupazionale di genere 15–64 anni;
- abitazioni ogni 1.000 residenti;
- abitazioni non occupate ogni 1.000 residenti;
- abitazioni non occupate sul totale delle abitazioni.
- famiglie composte da una sola persona sul totale delle famiglie residenti.

Per ogni Comune il valore 2023 è stato ricalcolato dalle variabili elementari e
confrontato con quello già pubblicato. La serie è stata accettata soltanto dopo
la coincidenza dei risultati, entro la precisione pubblicata, nei sette Comuni.

“Famiglie coabitanti” resta privo di serie: la variabile PF9 usata nel 2023 non
compare nel tracciato 2021. Il dato 2021 non viene sostituito con proxy.

“Componenti medi per famiglia” resta privo di serie: il tracciato raggruppa
insieme le famiglie con sei o più componenti e non consente di ricostruire con
esattezza il valore pubblicato. Non viene introdotta un'approssimazione.

## Criterio per i prossimi lotti

Una serie viene aggiunta soltanto se:

1. la fonte è istituzionale e la scala comunale è esplicita;
2. definizione, universo, unità e formula sono omogenei fra le annualità;
3. tutti i sette Comuni sono coperti, salvo eccezioni dichiarate prima della pubblicazione;
4. lo snapshot conserva valori elementari, URL e impronte dei file sorgente;
5. i test automatici verificano che l'ultimo punto coincida con il valore corrente.


## Lotto Agricoltura e territorio v1.20.0

Il 7° Censimento generale dell'Agricoltura Istat 2020 è usato come ultima base comunale censuaria omogenea. Aziende, dimensione media e irrigazione sono attribuite per centro aziendale; SAU territoriale e profilo colture usano invece il Comune di localizzazione dei terreni. La quota di SAU sulla superficie comunale usa come denominatore SITUAS al 31 dicembre 2020.

La copertura è 7/7 per aziende, SAU, dimensione media, irrigazione, seminativi, olivo da olio e prati/pascoli; 6/7 per la vite (Forte dei Marmi `n.d.`). Nessuna sottodimensione sotto 6/7 viene pubblicata e nessuna assenza viene trasformata in zero.
