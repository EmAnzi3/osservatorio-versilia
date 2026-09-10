"""Configurazione indicatori Frame SBS Territoriale per Economia prodotta v1.34.0."""
from __future__ import annotations

SOURCE_URL = "https://www.istat.it/tavole-di-dati/risultati-economici-delle-imprese-e-delle-multinazionali-a-livello-territoriale-anno-2023/"
SOURCE_LABEL = "Istat — Frame SBS Territoriale"
TOWN_ORDER = ("Massarosa", "Viareggio", "Camaiore", "Pietrasanta", "Seravezza", "Forte dei Marmi", "Stazzema")
SCOPES = (("total", "Totale"), ("industry", "Industria"), ("services", "Servizi"))
ECONOMIA_PRODOTTA_KEYS = (
    "businessTurnover", "businessValueAdded", "labourProductivity",
    "turnoverPerPersonEmployed", "valueAddedTurnoverShare",
    "averageGrossRemunerationPerEmployee", "labourCost", "grossOperatingMargin",
)
ADDITIVE_KEYS = (
    "businessTurnover",
    "businessValueAdded",
    "labourCost",
    "grossOperatingMargin",
)
NEW_KEYS = tuple(k for k in ECONOMIA_PRODOTTA_KEYS if k not in {"businessValueAdded", "labourProductivity"})

CONFIG = {
    "businessTurnover": {
        "label": "Fatturato delle unità locali", "short": "Fatturato", "unit": "millionCurrency", "years": list(range(2015, 2024)),
        "description": "Fatturato prodotto dalle unità locali delle imprese di industria e servizi localizzate nel comune.",
        "methodType": "Dato ufficiale", "formula": "Valore del fatturato pubblicato direttamente da Istat Frame SBS Territoriale.",
        "caveat": "Valore nominale a prezzi correnti: descrive la scala economica localizzata nel comune e non coincide con il PIL comunale.",
        "searchTerms": ["fatturato", "ricavi", "vendite", "economia prodotta", "frame sbs"],
    },
    "businessValueAdded": {
        "label": "Valore aggiunto delle unità locali", "short": "Valore aggiunto", "unit": "millionCurrency", "years": list(range(2015, 2024)),
        "description": "Valore aggiunto attribuito da Istat alle unità locali delle imprese di industria e servizi nel comune. Non è il PIL comunale.",
        "methodType": "Dato ufficiale", "formula": "Valore aggiunto pubblicato direttamente da Istat Frame SBS Territoriale.",
        "caveat": "Valore nominale a prezzi correnti. La serie 2015–2023 mantiene il perimetro Frame SBS Territoriale e non va interpretata come PIL comunale.",
        "searchTerms": ["valore aggiunto", "ricchezza prodotta", "produzione", "frame sbs"],
    },
    "labourProductivity": {
        "label": "Valore aggiunto per addetto", "short": "VA per addetto", "unit": "currency", "years": list(range(2015, 2024)),
        "description": "Produttività nominale del lavoro: valore aggiunto per addetto delle unità locali di industria e servizi.",
        "methodType": "Dato ufficiale", "formula": "Indicatore pubblicato direttamente da Istat: valore aggiunto / addetti.",
        "caveat": "Indicatore nominale a prezzi correnti; non misura da solo efficienza tecnica, salari o benessere e risente della composizione settoriale locale.",
        "searchTerms": ["produttività", "valore aggiunto per addetto", "produttività nominale", "frame sbs"],
    },
    "turnoverPerPersonEmployed": {
        "label": "Fatturato per addetto", "short": "Fatturato per addetto", "unit": "currency", "years": list(range(2015, 2024)),
        "description": "Fatturato delle unità locali rapportato al numero dei loro addetti.",
        "methodType": "Elaborazione Osservatorio su dati ufficiali", "formula": "fatturato / addetti",
        "caveat": "Rapporto elaborato sui valori Frame SBS Territoriale dello stesso anno e perimetro. È nominale e dipende fortemente dalla composizione settoriale.",
        "searchTerms": ["fatturato per addetto", "ricavi per addetto", "vendite per lavoratore"],
    },
    "valueAddedTurnoverShare": {
        "label": "Valore aggiunto sul fatturato", "short": "VA sul fatturato", "unit": "percent", "years": list(range(2015, 2024)),
        "description": "Quota del fatturato che si traduce in valore aggiunto nelle unità locali localizzate nel comune.",
        "methodType": "Dato ufficiale", "formula": "Indicatore pubblicato direttamente da Istat: valore aggiunto / fatturato × 100.",
        "caveat": "Il rapporto è influenzato dalla struttura settoriale e dall’intensità di acquisti intermedi; non è una misura di utile netto.",
        "searchTerms": ["valore aggiunto sul fatturato", "quota valore aggiunto", "incidenza valore aggiunto"],
    },
    "averageGrossRemunerationPerEmployee": {
        "label": "Retribuzione media lorda per dipendente", "short": "Retribuzione per dipendente", "unit": "currency", "years": list(range(2015, 2024)),
        "description": "Retribuzioni lorde annue delle unità locali rapportate al numero dei dipendenti.",
        "methodType": "Dato ufficiale", "formula": "Indicatore pubblicato direttamente da Istat: retribuzioni / dipendenti.",
        "caveat": "Importo lordo medio annuo a prezzi correnti; non coincide con il reddito netto del lavoratore né con il costo complessivo del lavoro.",
        "searchTerms": ["retribuzione media", "stipendio lordo", "dipendenti", "salari"],
    },
    "labourCost": {
        "label": "Costo del lavoro", "short": "Costo del lavoro", "unit": "millionCurrency", "years": [2021, 2022, 2023],
        "description": "Costo del lavoro sostenuto dalle unità locali, comprensivo di retribuzioni e oneri a carico del datore di lavoro.",
        "methodType": "Dato ufficiale", "formula": "Valore del costo del lavoro pubblicato direttamente nelle tavole comunali Frame SBS 2021–2023.",
        "caveat": "La serie comunale assoluta acquisita è disponibile dal 2021; gli anni precedenti non vengono stimati o ricostruiti.",
        "searchTerms": ["costo del lavoro", "costo personale", "oneri lavoro"],
    },
    "grossOperatingMargin": {
        "label": "Margine operativo lordo", "short": "MOL", "unit": "millionCurrency", "years": [2021, 2022, 2023],
        "description": "Margine operativo lordo delle unità locali, ricostruito dai due aggregati ufficiali disponibili nello stesso perimetro.",
        "methodType": "Elaborazione Osservatorio su dati ufficiali", "formula": "valore aggiunto − costo del lavoro",
        "caveat": "Elaborabile in modo omogeneo dal 2021, quando il costo del lavoro assoluto compare nelle tavole comunali acquisite. Non è utile netto.",
        "searchTerms": ["margine operativo lordo", "mol", "margine operativo"],
    },
}
