# Contratto UX · Percorsi su mobile e tablet

La lista dei percorsi è una superficie primaria dell'interfaccia e non può essere compressa a una o poche righe sopra la mappa. Allo stesso modo, la mappa non può impedire all'utente di continuare o invertire lo scorrimento verticale della pagina.

Regole vincolanti per viewport fino a 820 px:

- la lista `#routeList` deve avere almeno 340 px di altezza utile;
- devono risultare visibili almeno 3 card complete contemporaneamente quando il filtro restituisce abbastanza risultati;
- la lista deve essere realmente scorrevole quando i risultati eccedono lo spazio disponibile;
- lo scroll interno della lista deve poter tornare allo scroll della pagina quando raggiunge un'estremità;
- la mappa deve iniziare dopo la lista e non può sovrapporsi o tagliarla;
- un gesto verticale con un dito sopra la mappa deve restare disponibile per lo scorrimento della pagina: il trascinamento Leaflet è quindi disattivato di default fino a 820 px;
- zoom tramite controlli e selezione dei tracciati devono restare disponibili anche con il trascinamento mobile disattivato;
- deve essere sempre disponibile sulla mappa un controllo esplicito `↑ Percorsi` che riporti all'elenco, come via di uscita indipendente dal comportamento touch del browser;
- non è ammesso overflow orizzontale della pagina;
- eventuali futuri redesign possono sostituire la lista con un selettore equivalente, ma non possono ridurre l'accesso ai percorsi o reintrodurre una trappola di scroll senza aggiornare esplicitamente questo contratto e i relativi test browser.

Il contratto è verificato da `scripts/test_percorsi_mobile_list_contract.py` ed è eseguito nella pipeline canonica GitHub Pages.
