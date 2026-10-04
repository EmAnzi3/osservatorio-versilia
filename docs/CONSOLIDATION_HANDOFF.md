# Consolidamento Osservatorio Versilia — handoff operativo

## Stato corrente — 4 ottobre 2026

- #322 mergiata su main (`c430a139`), pubblicazione Pages riuscita; il proprietario conferma il sito pubblicato. Raccolta A3 conclusa: +12 storici e +106 confronti, totali 123/137, catalogo 225 indicatori e 1.547 valori correnti. Le 76 opportunità residue restano fuori dal lotto; non riaprire GIS, ricostruzioni o ACI.
- UI approvata preservata: homepage/secondarie #313–315 e toolbar Classificazioni; Camaiore resta golden `5aaf159870912eb49bffbd044963549bfb920150`. Nessuna modifica CSS o grafici nella correzione monitor.
- Nuovo lavoro autorizzato: `fix/source-monitor-public-status`. Stato dati fermo al 31 agosto mentre il controllo quotidiano salva soltanto artifact. #144 è ancora Draft, controlla il vecchio catalogo 181/83 e non va mergiata alla cieca. Report quotidiano del 4 ottobre prima di #322: 225 indicatori / 122 fonti; catalogo dopo A3: 225 / 138.

## Correzione monitor in verifica

- Periodi equivalenti italiano/ISO non generano nuovi rilasci. Periodi con precisioni diverse o descrizioni composite richiedono verifica; cambio tecnico della fonte non certifica un nuovo dato. Le evidenze semantiche PNRR/MIMIT restano distinte.
- `periodVerifiedAt` conserva la data della verifica del periodo; `checkedAt` registra il controllo della fonte. Il tooltip della cella esistente espone entrambe senza cambiare impaginazione. Le disconnessioni HTTP non interrompono l'intero monitor. Sondaggi in parallelo: quattro globali, massimo due per portale, avanzamento ogni dieci fonti.
- Pages e il publisher Radar selezionano solo artifact live riusciti su main (schedule/manuale), con schema, date, ID/fonti e digest del catalogo corrente verificati. Mai importare valori o codice da artifact. Report offline/PR/falliti/vecchio catalogo respinti; checkout ripristinato dopo build. Il quotidiano non sovrascrive evidenze deep più recenti.
- Pages si aggiorna dopo i run del monitor autorizzati senza attendere il merge di una PR diagnostica. Il mensile continua a proporre nuovi valori soltanto per revisione, mai a pubblicarli automaticamente.
- Deep live manuale completato: 225 indicatori / 138 fonti, zero errori strutturali, 14 endpoint non raggiungibili. Due aggiornamenti da verificare: carburanti MIMIT del 3 ottobre e fotografia PNRR concluso; finanziamenti PNRR coincidenti. Nessun valore aggiornato automaticamente. Baseline e rapporto del 4 ottobre inclusi.
- Test mirati monitor/periodi/runtime/PNRR PASS. Quick finale GREEN: 250 pagine / 247 URL, 105 intestazioni su 25 pagine senza sovrapposizioni, stemmi 7/7. In ambiente locale è stata necessaria la riapplicazione dei helper branding canonici al dist dopo il subprocess di build; nessun CSS/sorgente/asserzione modificato per compensarla. Browser Stato dati desktop/mobile PASS: 225 righe, data 4 ottobre, due rilasci, date distinte, filtri/ricerca/shell e nessun overflow. Preview finale con le sette route UI approvate verificata prima della PR.
- Full locale e CI restano i gate di chiusura: consultare gli esiti nella PR del branch prima di proporre il merge. L'approvazione di #322 non sostituisce l'approvazione di questa nuova correzione.
- I test delle release proteggono dati e periodi pubblicati senza congelare lo stato operativo delle future scansioni. Il gate Stato dati e il selettore runtime verificano i periodi contro l'intero catalogo pubblico materializzato.
- Nessun merge o deploy della correzione ancora autorizzato/eseguito.

## Lavori sospesi

- Non mergiare/chiudere automaticamente #302/#303/#304 e #318–#321. #301 A6.1 resta sospesa/Draft; riallinearla al main pubblicato e rivalidare il catalogo soltanto dopo chiusura della correzione Stato dati.
