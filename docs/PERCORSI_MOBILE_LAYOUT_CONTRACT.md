# Contratto UX · Percorsi su mobile e tablet

La lista dei percorsi è una superficie primaria dell'interfaccia e non può essere compressa a una o poche righe sopra la mappa.

Regole vincolanti per viewport fino a 820 px:

- la lista `#routeList` deve avere almeno 340 px di altezza utile;
- devono risultare visibili almeno 3 card complete contemporaneamente quando il filtro restituisce abbastanza risultati;
- la lista deve essere realmente scorrevole quando i risultati eccedono lo spazio disponibile;
- la mappa deve iniziare dopo la lista e non può sovrapporsi o tagliarla;
- non è ammesso overflow orizzontale della pagina;
- eventuali futuri redesign possono sostituire la lista con un selettore equivalente, ma non possono ridurre l'accesso ai percorsi senza aggiornare esplicitamente questo contratto e i relativi test browser.

Il contratto è verificato da `scripts/test_percorsi_mobile_list_contract.py` ed è eseguito nella pipeline canonica GitHub Pages.
