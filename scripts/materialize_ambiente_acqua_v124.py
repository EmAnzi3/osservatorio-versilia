#!/usr/bin/env python3
"""Materializza Ambiente · Acqua e bonifiche v1.24.0 da fonti validate."""
from __future__ import annotations
import base64, csv, gzip, hashlib, io, json, re, sys, time
from collections import OrderedDict
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data/site-data.json"
REGISTRY=ROOT/"data/source-registry.json"
STATE=ROOT/"data/source-monitor-state.json"
DETAIL=ROOT/"data/source-snapshots/ambiente-acqua-v124-data.json"
FINALIZER=ROOT/"scripts/finalize_catalog_release.py"
TEST=ROOT/"scripts/test_catalog_release_v116.py"
README=ROOT/"README.md"
APP00=ROOT/"assets/app-parts/00.txt"
APP03=ROOT/"assets/app-parts/03.txt"
APP05=ROOT/"assets/app-parts/05.txt"
FIDELITY=ROOT/"assets/fidelity.css"
APPJS=ROOT/"assets/app.js"
UXH=ROOT/"assets/ux-history.js"
EXPORT=ROOT/"assets/export-v161.js"
SW=ROOT/"service-worker.js"
BUILD_SAFE=ROOT/"scripts/build_static_safe.py"
BUILD_BRAND=ROOT/"scripts/build_static_brand.py"
HISTORY=ROOT/"docs/copertura-serie-storiche.md"
COHERENCE=ROOT/"docs/coerenza-interfaccia.md"

VERSION="v1.24.0"
UPDATED="29 agosto 2026"
ASSET_VERSION="20260830-v124-water-ui3"
PWA_VERSION="ov-pwa-20260830-v124-water-ui3"
KEYS=("waterNetworkLosses","drinkingWaterQuality","remediationProceedings")
ISTAT_URL="https://esploradati.istat.it/"
GAIA_URL="https://www.gaia-spa.it/analisiweb_v2/"
SISBON_URL="https://sira.arpat.toscana.it/apex/f?p=SISBON:REPORT_PER_RT::CSV:IR_REPORT_GEOSCOPIO"
TOWNS={
"046005":"Camaiore","046013":"Forte dei Marmi","046018":"Massarosa",
"046024":"Pietrasanta","046028":"Seravezza","046030":"Stazzema","046033":"Viareggio"
}
LOCALITIES=[('046005', '6', 'CAMAIORE- PEDONA -BASTIANELLA- MONTEBELLO', '07A01K01', '0'), ('046005', '6', 'CAPEZZANO PIANORE - BOCCHETTE', '07A06K02', '0'), ('046005', '6', 'CASOLI', '07A03K03', '0'), ('046005', '6', 'FIBBIALLA', '07A08K07', '0'), ('046005', '6', 'MONTEGGIORI-S.LUCIA', '07A02K01', '0'), ('046005', '6', 'TORCIGLIANO', '07A07K06', '0'), ('046005', '6', 'NOCCHI - MARIGNANA', '07A07K01', '0'), ('046005', '6', 'LIDO DI CAMAIORE-SECCO', '07A04K01', '0'), ('046005', '6', 'VADO-LOMBRICI', '07A03K02', '0'), ('046005', '6', 'GOMBITELLI', '07A08K02', '0'), ('046005', '6', 'METATO', '07A05K01', '0'), ('046005', '6', 'GREPPOLUNGO', '07A03K04', '0'), ('046005', '6', 'MONTEMAGNO', '07A07K03', '0'), ('046005', '6', 'SUMMONTI - AGLIANO', '07A07K08', '0'), ('046005', '6', 'PIEVE', '07A07K02', '0'), ('046005', '6', 'PONTEMAZZORI', '07A07K05', '0'), ('046005', '6', 'VALPROMARO', '07A08K03', '0'), ('046005', '6', 'FIBBIANO', '07A08K01', '0'), ('046005', '6', 'CASCIANA', '07A08K08', '0'), ('046005', '6', 'MIGLIANO', '07A09K05', '0'), ('046013', '19', 'FORTE DEI MARMI', '20A01K05', '0'), ('046018', '26', 'CASE ROSSE', '28A02K01', '0'), ('046018', '26', 'GUALDO - MONTIGIANO', '28A01K04', '0'), ('046018', '26', 'PIANO DI MOMMIO - CORSANICO - MOMMIO CASTELLO', '28A01K10', '0'), ('046018', '26', 'PIEVE A ELICI', '28A01K05', '0'), ('046018', '26', 'MASSAROSA', '28A01K14', '0'), ('046018', '26', 'STIAVA - BARGECCHIA', '28A01K11', '0'), ('046018', '26', 'PIAN DI CONCA', '28A01K23', '28A01K03'), ('046018', '26', 'QUIESA - MASSACIUCCOLI', '28A01K09', '0'), ('046024', '33', 'CAPEZZANO MONTE', '35A01K01', '0'), ('046024', '33', 'MARINA DI PIETRASANTA', '35A04K01', '0'), ('046024', '33', 'PIETRASANTA', '35A02K08', '0'), ('046024', '33', 'SOLAIO - CASTELLO ALTO', '35A03K02', '0'), ('046024', '33', 'VALDICASTELLO', '35A01K03', '0'), ('046024', '33', 'VALLECCHIA - CASTELLO BASSO', '35A03K01', '0'), ('046024', '33', 'STRETTOIA', '35A05K05', '0'), ('046024', '33', 'CAPRIGLIA', '35A01K02', '0'), ('046024', '33', 'POLLINO - TRAVERSAGNA - PORTONE', '35A02K19', '0'), ('046024', '33', 'MONTE DI RIPA', '35A05K04', '0'), ('046024', '33', 'METATI ROSSI - CERRO GROSSO', '35A05K06', '0'), ('046028', '39', 'AZZANO', '42A05K11', '0'), ('046028', '39', 'BASATI', '42A01K01', '0'), ('046028', '39', 'CERRETA SANT ANTONIO', '42A03K01', '0'), ('046028', '39', 'FABIANO', '42A05K01', '0'), ('046028', '39', 'GIUSTAGNANA', '42A05K05', '0'), ('046028', '39', 'MINAZZANA', '42A06K07', '0'), ('046028', '39', 'MONTE DI RIPA', '42A04K02', '0'), ('046028', '39', 'POZZI - QUERCETA', '42A02K04', '0'), ('046028', '39', 'SERAVEZZA - CORVAIA', '42A05K09', '0'), ('046028', '39', 'VALVENTOSA', '42A05K06', '0'), ('046028', '39', 'SERAVEZZA ALTA - PANCOLA', '42A05K12', '0'), ('046028', '39', 'LE SALDE', '42A06K01', '0'), ('046030', '41', 'ARNI CAMPAGRINA', '44A15K01', '0'), ('046030', '41', 'ARNI CHIESA', '44A15K02', '0'), ('046030', '41', 'CARDOSO', '44A09K01', '0'), ('046030', '41', 'FARNOCCHIA', '44A04K01', '0'), ('046030', '41', 'GALLENA', '44A06K01', '0'), ('046030', '41', 'LA CULLA', '44A01K01', '0'), ('046030', '41', 'LEVIGLIANI', '44A12K01', '0'), ('046030', '41', 'MULINA', '44A02K01', '0'), ('046030', '41', 'POMEZZANA LE CALDE', '44A05K01', '0'), ('046030', '41', 'PONTE STAZZEMESE - RUOSINA - IACCO', '44A10K02', '0'), ('046030', '41', 'PRUNO - VOLEGNO', '44A07K02', '0'), ('046030', '41', 'RETIGNANO', '44A13K01', '0'), ('046030', '41', 'SANT ANNA DI STAZZEMA', '44A03K01', '0'), ('046030', '41', 'STAZZEMA', '44A08K01', '0'), ('046030', '41', 'TERRINCA', '44A14K01', '0'), ('046030', '41', 'BRUCIAFERRO', '44A10K05', '0'), ('046033', '45', 'VIAREGGIO', '49A01K03', '0'), ('046033', '45', 'TORRE DEL LAGO', '49A02K17', '0')]
WATER={
"046005":{"2012":[4907,3379],"2015":[3744,2598],"2018":[4343,2695]},
"046013":{"2012":[3830,2607],"2015":[2989,1718],"2018":[2763,1648]},
"046018":{"2012":[2361,1637],"2015":[2399,1298],"2018":[2689,1560]},
"046024":{"2012":[3652,2636],"2015":[4363,2100],"2018":[3839,2197]},
"046028":{"2012":[1228,825],"2015":[1265,674],"2018":[1660,795]},
"046030":{"2012":[252,182],"2015":[284,149],"2018":[389,173]},
"046033":{"2012":[8318,5659],"2015":[7250,4660],"2018":[6819,4369]}
}
EXPECTED_SISBON={"046005":[9,22],"046013":[10,11],"046018":[6,10],"046024":[10,13],"046028":[3,6],"046030":[3,4],"046033":[15,30]}
CLOSED={"200","210","220","230","280"}

def load(p): return json.loads(p.read_text(encoding="utf-8"))
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def clean(v): return re.sub(r"\s+"," ",v or "").strip()
def pct(imm,ero): return (imm-ero)/imm*100.0
def replace_required(path, old, new):
    text=path.read_text(encoding="utf-8")
    if new in text: return
    if old not in text: raise RuntimeError(f"Pattern non trovato in {path}: {old[:100]}")
    path.write_text(text.replace(old,new,1),encoding="utf-8")
def replace_all(path, old, new):
    text=path.read_text(encoding="utf-8")
    if old in text: path.write_text(text.replace(old,new),encoding="utf-8")

def fetch_gaia():
    sess=requests.Session()
    sess.headers.update({"User-Agent":"OsservatorioVersilia/1.24 (+https://osservatorioversilia.it)"})
    localities=[]; definitions=None
    for idx,(town_code,gaia_town,name,c1,c2) in enumerate(LOCALITIES,1):
        sess.post(GAIA_URL+"php/ajax.inc.php",data={
          "codice_comune":gaia_town,"codice_prelievo":c1,"codice_prelievo1":c2,
          "codice_area":"1","op":"set_session"
        },timeout=25)
        url=GAIA_URL+f"campioni/{c1}/{c2}"
        r=sess.get(url,timeout=25); r.raise_for_status()
        soup=BeautifulSoup(r.text,"html.parser")
        title=clean(soup.select_one("h4").get_text(" ",strip=True) if soup.select_one("h4") else "")
        period=""
        for h in soup.select("h6"):
            t=clean(h.get_text(" ",strip=True))
            if "Periodo di riferimento" in t:
                period=clean(re.sub(r"^Periodo di riferimento\s*:\s*","",t,flags=re.I)); break
        rows=[]
        for tr in soup.select("#campioni tbody tr"):
            td=tr.find_all("td")
            if len(td)<4: continue
            span=td[0].find(attrs={"title":True})
            rows.append({
              "name":clean(td[0].get_text(" ",strip=True)),
              "unit":clean(td[1].get_text(" ",strip=True)),
              "value":clean(td[2].get_text(" ",strip=True)),
              "reference":clean(td[3].get_text(" ",strip=True)),
              "description":clean(span.get("title","") if span else "")
            })
        if period!="2° Semestre 2025" or len(rows)!=17:
            raise RuntimeError(f"GAIA {name}: periodo={period!r}, parametri={len(rows)}")
        defs=[{k:x[k] for k in ("name","unit","reference","description")} for x in rows]
        if definitions is None: definitions=defs
        elif defs!=definitions: raise RuntimeError(f"Schema GAIA non uniforme: {name}")
        localities.append({
          "townCode":town_code,"name":name,"title":title,"sampleCode":c1,"sampleCode2":c2,
          "period":period,"url":url,"values":[x["value"] for x in rows]
        })
        time.sleep(.05)
    counts={c:sum(x["townCode"]==c for x in localities) for c in TOWNS}
    if counts!={"046005":20,"046013":1,"046018":8,"046024":11,"046028":12,"046030":16,"046033":2}:
        raise RuntimeError(f"Copertura GAIA inattesa: {counts}")
    first=next(x for x in localities if x["townCode"]=="046005" and x["sampleCode"]=="07A01K01")
    pian=next(x for x in localities if x["sampleCode"]=="28A01K23")
    if first["values"][0]!="7.7" or pian["values"][0]!="7.8" or pian["values"][7]!="5.9":
        raise RuntimeError("Sentinelle GAIA diverse dallo snapshot validato")
    return definitions,localities

def fetch_sisbon():
    fallback=ROOT/"data/source-snapshots/ambiente-acqua-v124-sisbon.json.gz.b64"
    raw=gzip.decompress(base64.b64decode(fallback.read_text(encoding="utf-8").strip()))
    compact=json.loads(raw.decode("utf-8"))
    procedures=[]
    for item in compact:
        code,ident,name,address,contamination,procedure_state,state_code,status_code=item
        procedures.append({
          "townCode":code,"id":ident,"name":name,"address":address,
          "contamination":contamination,"procedureState":procedure_state,
          "stateCode":state_code,"status":"closed" if status_code=="c" else "active",
          "lat":None,"lon":None
        })
    ids=[x["id"] for x in procedures]
    if len(procedures)!=152 or len(set(ids))!=152:
        raise RuntimeError(f"SISBON attesi 152 univoci, trovati {len(procedures)}/{len(set(ids))}")
    counts={}
    for c in TOWNS:
        xs=[x for x in procedures if x["townCode"]==c]
        counts[c]=[sum(x["status"]=="active" for x in xs),sum(x["status"]=="closed" for x in xs)]
    if counts!=EXPECTED_SISBON:
        raise RuntimeError(f"Conteggi SISBON inattesi: {counts}")
    return procedures, "e5bd50e5b6a4a88b0f7bec0762b8719b69064ae1841bdbde925c5501e363dbcb"

def build_snapshot(defs,localities,procedures,sisbon_sha):
    water={}
    for c,years in WATER.items():
        water[c]={y:{"immessa":v[0],"erogata":v[1],"perditePct":pct(*v)} for y,v in years.items()}
    vers={}
    for y in ("2012","2015","2018"):
        imm=sum(WATER[c][y][0] for c in TOWNS); ero=sum(WATER[c][y][1] for c in TOWNS)
        vers[y]={"immessa":imm,"erogata":ero,"perditePct":pct(imm,ero)}
    return {
      "schemaVersion":2,"release":VERSION,"acquiredAt":"2026-08-29",
      "sources":{
        "istat":{"flow":"12_60_DF_DCCV_CONSACQUA_2","sha256":"337f83c658af4a92f9d677c880bf887a91a458b19aa57a0c47757651064790bf","url":ISTAT_URL},
        "gaia":{"mainExtractionSha256":"97d6dbe6a9f3549fe9d43c7bb2bf832ee2e1819effa2bf1b7b69fe46a37c83eb","pianDiConcaSha256":"fd938a487dccf6f9ed64325f2df855e36c2706c75ffd45cedd8c6ee607c612f3","url":GAIA_URL},
        "sisbon":{"validatedCsvSha256":"e5bd50e5b6a4a88b0f7bec0762b8719b69064ae1841bdbde925c5501e363dbcb","fetchedSha256":sisbon_sha,"url":SISBON_URL}
      },
      "waterNetworkLosses":{"towns":water,"versilia":vers},
      "drinkingWaterQuality":{"parameterDefinitions":defs,"localities":localities},
      "remediationProceedings":{"closedStateCodes":sorted(CLOSED),"procedures":procedures}
    }

def build_metrics(site,snap):
    slugs={r["code"]:r["slug"] for r in site["metrics"]["population"]["rows"]}
    towns=site["towns"]; out=OrderedDict()
    water=snap["waterNetworkLosses"]
    rows=[]
    for t in towns:
        c=t["code"]; ys=water["towns"][c]
        rows.append({"town":t["name"],"code":c,"slug":slugs[c],"value":ys["2018"]["perditePct"],
          "formatted":f'{ys["2018"]["perditePct"]:.1f}%'.replace(".",","),
          "series":{"years":[2012,2015,2018],"values":[ys[y]["perditePct"] for y in ("2012","2015","2018")]},
          "networkVolumes":ys["2018"],"normalized":None,"benchmarkValue":ys["2018"]["perditePct"]})
    va=water["versilia"]["2018"]
    out["waterNetworkLosses"]={
      "meta":{"key":"waterNetworkLosses","theme":"ambiente","label":"Perdite della rete idrica","shortLabel":"Perdite rete idrica",
        "description":"Quota dell’acqua immessa nella rete comunale che non risulta erogata per usi autorizzati. Ultimo dettaglio comunale Istat pubblico disponibile: 2018.",
        "unit":"percent","year":"2018","source":"Istat — Censimento delle acque per uso civile","polarity":"neutral",
        "context":"Acqua e bonifiche","detailGroup":"water-remediation",
        "searchTerms":["perdite idriche","rete idrica","acquedotto","acqua immessa","acqua erogata"],
        "comparisonReference":"aggregate","comparisonLabel":"quota Versilia","comparisonOverline":"Rispetto alla quota Versilia",
        "comparisonNote":"Il riferimento Versilia è il rapporto tra le somme dei volumi immessi ed erogati; non la media semplice delle percentuali comunali.",
        "sourceMeta":{"snapshot":"data/source-snapshots/ambiente-acqua-v124-data.json","note":"2018 è l’ultimo dato comunale pubblico disponibile nel dataflow verificato; nessuna interpolazione."}},
      "sourceUrl":ISTAT_URL,"rows":rows,
      "aggregate":{"value":va["perditePct"],"label":"Versilia","note":"Rapporto tra le somme dei volumi dei sette Comuni.",
        "series":{"years":[2012,2015,2018],"values":[water["versilia"][y]["perditePct"] for y in ("2012","2015","2018")]}},
      "normalizedAggregate":None,
      "method":{"type":"Indicatore derivato da volumi Istat","formula":"(acqua immessa − acqua erogata per usi autorizzati) / acqua immessa × 100. Aggregato Versilia sul rapporto delle somme.",
        "caveat":"Dato comunale fermo al 2018: non va interpretato come fotografia corrente del 2026.","coverage":"7/7","snapshot":"data/source-snapshots/ambiente-acqua-v124-data.json"}
    }
    defs=snap["drinkingWaterQuality"]["parameterDefinitions"]; gl=snap["drinkingWaterQuality"]["localities"]
    qrows=[]
    for t in towns:
        loc=[x for x in gl if x["townCode"]==t["code"]]
        qrows.append({"town":t["name"],"code":t["code"],"slug":slugs[t["code"]],"value":len(loc),"formatted":f"{len(loc)} località",
          "localities":loc,"series":None,"normalized":None,"benchmarkValue":None})
    out["drinkingWaterQuality"]={
      "meta":{"key":"drinkingWaterQuality","theme":"ambiente","label":"Qualità dell’acqua potabile","shortLabel":"Qualità acqua potabile",
        "description":"Valori medi pubblicati da GAIA per 17 parametri nelle aree/località servite. Non viene costruita alcuna media comunale né un indice sintetico.",
        "unit":"number","year":"2° semestre 2025","source":"GAIA S.p.A. — Laboratorio Analisi","polarity":"neutral",
        "context":"Acqua e bonifiche","detailGroup":"water-remediation","compositeType":"drinkingWaterQuality",
        "searchTerms":["acqua potabile","qualità acqua","gaia","nitrati","durezza","acquedotto"],
        "sourceMeta":{"snapshot":"data/source-snapshots/ambiente-acqua-v124-data.json","note":"70 località, 17 parametri; valori e riferimenti restano nelle unità originali GAIA."}},
      "sourceUrl":GAIA_URL,"parameterDefinitions":defs,"rows":qrows,
      "aggregate":{"value":70,"label":"Versilia · località GAIA","note":"70 località verificate; il numero esprime la copertura del dettaglio, non un punteggio di qualità."},
      "normalizedAggregate":None,
      "method":{"type":"Pubblicazione analitica GAIA per località","formula":"Nessuna aggregazione delle concentrazioni: si riportano i valori medi e i limiti/riferimenti della singola località.",
        "caveat":"Valori consigliati e limiti normativi sono mantenuti distinti. Le stringhe con < o > non vengono trasformate.","coverage":"7/7 · 70/70 località · 1.190 valori","snapshot":"data/source-snapshots/ambiente-acqua-v124-data.json"}
    }
    procs=snap["remediationProceedings"]["procedures"]; rrows=[]
    for t in towns:
        xs=[x for x in procs if x["townCode"]==t["code"]]; a=sum(x["status"]=="active" for x in xs); c=sum(x["status"]=="closed" for x in xs)
        rrows.append({"town":t["name"],"code":t["code"],"slug":slugs[t["code"]],"value":a,"formatted":str(a),
          "parts":[{"key":"active","label":"Iter attivi","selectorLabel":"Iter attivi","unit":"number","value":a},{"key":"closed","label":"Iter chiusi","selectorLabel":"Iter chiusi","unit":"number","value":c}],
          "procedures":xs,"series":None,"normalized":None,"benchmarkValue":None})
    out["remediationProceedings"]={
      "meta":{"key":"remediationProceedings","theme":"ambiente","label":"Siti oggetto di procedimento di bonifica","shortLabel":"Procedimenti di bonifica",
        "description":"Procedimenti SISBON localizzati nei sette Comuni, distinti tra iter attivi e chiusi. Un procedimento non equivale automaticamente a un sito attualmente contaminato.",
        "unit":"number","year":"29 agosto 2026","source":"Regione Toscana / ARPAT — SISBON","polarity":"neutral",
        "context":"Acqua e bonifiche","detailGroup":"water-remediation","compositeType":"remediationProceedings",
        "searchTerms":["bonifiche","sisbon","siti contaminati","iter attivi","iter chiusi"],
        "sourceMeta":{"snapshot":"data/source-snapshots/ambiente-acqua-v124-data.json","note":"Conteggio per codice_regionale univoco; coordinate coincidenti non fondono procedimenti distinti."}},
      "sourceUrl":SISBON_URL,"rows":rrows,
      "aggregate":{"value":56,"label":"Versilia · iter attivi","parts":[{"key":"active","label":"Iter attivi","unit":"number","value":56},{"key":"closed","label":"Iter chiusi","unit":"number","value":96}],
        "note":"152 procedimenti univoci: 56 attivi e 96 chiusi."},
      "normalizedAggregate":None,
      "method":{"type":"Conteggio dello snapshot pubblico SISBON","formula":"Conteggio dei codici regionali univoci per Comune e stato dell’iter.",
        "caveat":"Lo stato procedurale non è una classificazione diretta della contaminazione attuale del sito.","coverage":"7/7 · 152/152 codici regionali univoci","snapshot":"data/source-snapshots/ambiente-acqua-v124-data.json"}
    }
    return out

def apply_site(site,snap):
    new=build_metrics(site,snap)
    rebuilt=OrderedDict()
    inserted=False
    for key,val in site["metrics"].items():
        rebuilt[key]=val
        if key=="rigidDefenceProtectedCoast":
            for nk in KEYS: rebuilt[nk]=new[nk]
            inserted=True
    if not inserted:
        for nk in KEYS: rebuilt[nk]=new[nk]
    site["metrics"]=rebuilt
    theme=site["themes"]["ambiente"]
    sections=[s for s in theme["sections"] if s.get("key")!="acqua-bonifiche"]
    section={"key":"acqua-bonifiche","label":"Acqua e bonifiche","description":"Rete idrica, qualità dell’acqua potabile e procedimenti di bonifica con fonti ufficiali e granularità dichiarata.","metrics":list(KEYS)}
    idx=next((i for i,s in enumerate(sections) if s.get("key")=="costa-mare"),len(sections)-1)
    sections.insert(idx+1,section)
    theme["sections"]=sections
    theme["metrics"]=[k for s in sections for k in s["metrics"]]
    theme["description"]="Clima, suolo, costa, mare, acqua, bonifiche, rifiuti, agricoltura, uso del territorio ed esposizione ai rischi idrogeologici."
    site["version"]=VERSION; site["updated"]=UPDATED

def apply_registry(reg):
    profiles=reg.setdefault("sourceProfiles",{})
    profiles["istat-water-irregular"]={"publisher":"Istat","frequency":"census_or_irregular","frequencyLabel":"Censuaria o irregolare","expectedRelease":"Quando Istat diffonde un nuovo dettaglio comunale omogeneo","acquisitionMethod":"Dataflow Istat sulla distribuzione di acqua potabile; indicatori derivati dai volumi elementari conservati nello snapshot.","licenseName":"CC BY 4.0","licenseUrl":"https://www.istat.it/note-legali/"}
    profiles["gaia-quality-semiannual"]={"publisher":"GAIA S.p.A.","frequency":"semiannual","frequencyLabel":"Semestrale","expectedRelease":"Aggiornamento semestrale del portale Laboratorio Analisi","acquisitionMethod":"Acquisizione delle tabelle ufficiali per località, senza aggregare le concentrazioni a Comune.","licenseName":"Condizioni indicate da GAIA S.p.A.","licenseUrl":"https://www.gaia-spa.it/"}
    profiles["sisbon-weekly"]={"publisher":"Regione Toscana / ARPAT","frequency":"weekly","frequencyLabel":"Settimanale","expectedRelease":"Aggiornamento del flusso pubblico SISBON/GEOscopio","acquisitionMethod":"Export pubblico SISBON; conteggio per codice_regionale univoco e stato dell’iter.","licenseName":"CC Attribution / condizioni Open Data Regione Toscana","licenseUrl":"https://dati.toscana.it/dataset/sisbon"}
    mapping={ISTAT_URL:"istat-water-irregular",GAIA_URL:"gaia-quality-semiannual",SISBON_URL:"sisbon-weekly"}
    for url,p in mapping.items():
        reg.setdefault("sourceProfileByUrl",{})[url]=p; reg.setdefault("sourceUrlProfiles",{})[url]=p
    ov=reg.setdefault("metricOverrides",{})
    ov["waterNetworkLosses"]={"profile":"istat-water-irregular"}
    ov["drinkingWaterQuality"]={"profile":"gaia-quality-semiannual"}
    ov["remediationProceedings"]={"profile":"sisbon-weekly"}
    reg["expectedMetricCount"]=165; reg["expectedInlineMetricCount"]=161; reg["expectedExternalMetricCount"]=4

def apply_state(state):
    checked=state.get("checkedAt","2026-08-29T00:00:00+00:00")
    config={
      ISTAT_URL:(["waterNetworkLosses"],"istat-water-irregular","census_or_irregular","2018"),
      GAIA_URL:(["drinkingWaterQuality"],"gaia-quality-semiannual","semiannual","2° semestre 2025"),
      SISBON_URL:(["remediationProceedings"],"sisbon-weekly","weekly","29 agosto 2026")
    }
    sources=state.setdefault("sources",{})
    for url,(metrics,profile,freq,period) in config.items():
        cur=sources.get(url,{})
        cur.update({"url":url,"ok":True,"status":200,"finalUrl":url,"contentType":cur.get("contentType","text/html"),"contentLength":cur.get("contentLength"),"etag":cur.get("etag",""),"lastModified":cur.get("lastModified",""),"contentSha256":cur.get("contentSha256",""),"hashTruncated":False,"error":"","metrics":metrics,"roles":["primary"],"profileIds":[profile],"frequencies":[freq]})
        sources[url]=cur
        state.setdefault("metrics",{}).setdefault(metrics[0],{"publishedPeriod":period,"checkedAt":checked,"observedLatestPeriod":period,"status":"current"})

def patch_ui():
    text=APP00.read_text(encoding="utf-8")
    marker="    rigidDefenceProtectedCoast: ['costa protetta', 'opere rigide', 'difesa costiera'],"
    addition=marker+"\n    waterNetworkLosses: ['perdite idriche', 'rete idrica', 'acquedotto', 'acqua immessa'],\n    drinkingWaterQuality: ['acqua potabile', 'qualità acqua', 'gaia', 'nitrati', 'durezza'],\n    remediationProceedings: ['bonifiche', 'sisbon', 'siti contaminati', 'iter attivi', 'iter chiusi'],"
    if "waterNetworkLosses:" not in text:
        if marker not in text: raise RuntimeError("Marker searchSynonyms non trovato")
        APP00.write_text(text.replace(marker,addition,1),encoding="utf-8")

    app=APP03.read_text(encoding="utf-8")
    helper=r"""
  function waterQualityTableMarkup(metric, locality) {
    const defs = metric.parameterDefinitions || [];
    return `<div class="water-quality-table-wrap"><table class="water-quality-table"><thead><tr><th>Parametro</th><th>Unità</th><th>Valore medio</th><th>Limite / riferimento</th></tr></thead><tbody>${defs.map((def,index)=>`<tr><td><b>${html(def.name)}</b>${def.description ? `<small>${html(def.description)}</small>` : ''}</td><td>${html(def.unit)}</td><td><strong>${html(locality.values?.[index] ?? 'n.d.')}</strong></td><td>${html(def.reference || '—')}</td></tr>`).join('')}</tbody></table></div>`;
  }

  function drinkingWaterQualityCompareMarkup(data, metricKey) {
    const metric=data.metrics[metricKey];
    return `<div class="water-quality-compare">${metric.rows.map(row=>{const q=new URLSearchParams({tema:metric.meta.theme,indicatore:metricKey});return `<a href="${route(`comuni/${row.slug}/?${q}`)}" class="water-quality-compare-row"><strong>${html(row.town)}</strong><span><b>${html(number0.format(row.localities?.length||0))}</b><small>località GAIA · 17 parametri</small></span><em>Apri il dettaglio →</em></a>`;}).join('')}</div><p class="composite-compare-note">Il numero indica soltanto quante località GAIA sono disponibili: non è un punteggio di qualità e non viene costruita alcuna media comunale.</p>`;
  }

  function drinkingWaterQualityTownMarkup(metric,row) {
    const locs=row.localities||[];
    if(!locs.length) return '<p>n.d.</p>';
    return `<div class="water-quality-town"><label class="water-quality-selector"><span>Località GAIA</span><select data-water-quality-locality>${locs.map((loc,i)=>`<option value="${i}">${html(loc.name)}</option>`).join('')}</select></label>${locs.map((loc,i)=>`<section class="water-quality-locality" data-water-quality-panel="${i}" ${i?'hidden':''}><div class="water-quality-locality-head"><div><h4>${html(loc.title||loc.name)}</h4><small>${html(loc.period)}</small></div><a class="source-pill" href="${html(loc.url)}" target="_blank" rel="noreferrer">GAIA ↗</a></div>${waterQualityTableMarkup(metric,loc)}</section>`).join('')}</div>`;
  }

  function remediationCompareMarkup(data,metricKey) {
    const metric=data.metrics[metricKey];
    return `<div class="remediation-shell"><label class="remediation-selector"><span>Lettura</span><select data-remediation-view><option value="active">Iter attivi</option><option value="closed">Iter chiusi</option></select></label><div class="remediation-compare-list">${metric.rows.map(row=>{const active=row.parts?.find(x=>x.key==='active')?.value||0,closed=row.parts?.find(x=>x.key==='closed')?.value||0,q=new URLSearchParams({tema:metric.meta.theme,indicatore:metricKey});return `<a class="remediation-compare-row" href="${route(`comuni/${row.slug}/?${q}`)}" data-active="${active}" data-closed="${closed}"><strong>${html(row.town)}</strong><span><b data-remediation-count>${html(number0.format(active))}</b><small data-remediation-label>iter attivi</small></span></a>`;}).join('')}</div><p class="composite-compare-note">Procedimenti univoci per codice regionale. Un procedimento non equivale automaticamente a un sito attualmente contaminato.</p></div>`;
  }

  function remediationTownMarkup(metric,row) {
    const active=row.parts?.find(x=>x.key==='active')?.value||0,closed=row.parts?.find(x=>x.key==='closed')?.value||0;
    return `<div class="remediation-shell remediation-town"><div class="remediation-summary"><article><span>Iter attivi</span><strong>${html(number0.format(active))}</strong></article><article><span>Iter chiusi</span><strong>${html(number0.format(closed))}</strong></article></div><label class="remediation-selector"><span>Mostra</span><select data-remediation-view><option value="active">Iter attivi</option><option value="closed">Iter chiusi</option></select></label><div class="remediation-procedure-list">${(row.procedures||[]).map(item=>`<article data-remediation-status="${html(item.status)}" ${item.status==='closed'?'hidden':''}><div><b>${html(item.id)}</b><h4>${html(item.name)}</h4>${item.address?`<p>${html(item.address)}</p>`:''}</div><dl><div><dt>Stato contaminazione</dt><dd>${html(item.contamination||'n.d.')}</dd></div><div><dt>Stato procedimento</dt><dd>${html(item.procedureState||'n.d.')}</dd></div></dl></article>`).join('')}</div></div>`;
  }

  document.addEventListener('change', event => {
    const quality=event.target.closest?.('[data-water-quality-locality]');
    if(quality) {
      const root=quality.closest('.water-quality-town'),wanted=String(quality.value);
      root?.querySelectorAll('[data-water-quality-panel]').forEach(panel=>panel.toggleAttribute('hidden',panel.dataset.waterQualityPanel!==wanted));
    }
    const remediation=event.target.closest?.('[data-remediation-view]');
    if(remediation) {
      const root=remediation.closest('.remediation-shell'),view=remediation.value;
      root?.querySelectorAll('.remediation-compare-row').forEach(row=>{
        const value=Number(row.dataset[view]||0); const count=row.querySelector('[data-remediation-count]'); const label=row.querySelector('[data-remediation-label]');
        if(count) count.textContent=number0.format(value); if(label) label.textContent=view==='active'?'iter attivi':'iter chiusi';
      });
      root?.querySelectorAll('[data-remediation-status]').forEach(item=>item.toggleAttribute('hidden',item.dataset.remediationStatus!==view));
    }
  });
"""
    marker="  function compositeCompareDefaults(metric) {"
    if "function drinkingWaterQualityCompareMarkup" not in app:
        if marker not in app: raise RuntimeError("Marker composite defaults non trovato")
        app=app.replace(marker,helper+"\n"+marker,1)
    cmp_marker="    if (metric.meta.compositeType === 'stock') {"
    cmp_add="    if (metric.meta.compositeType === 'drinkingWaterQuality') return drinkingWaterQualityCompareMarkup(data, metricKey);\n    if (metric.meta.compositeType === 'remediationProceedings') return remediationCompareMarkup(data, metricKey);\n"+cmp_marker
    if "return drinkingWaterQualityCompareMarkup(data, metricKey)" not in app:
        app=app.replace(cmp_marker,cmp_add,1)
    town_marker="  function compositeTownMarkup(metric, row) {\n    const parts = row.parts || [];"
    town_add="  function compositeTownMarkup(metric, row) {\n    if (metric.meta.compositeType === 'drinkingWaterQuality') return drinkingWaterQualityTownMarkup(metric,row);\n    if (metric.meta.compositeType === 'remediationProceedings') return remediationTownMarkup(metric,row);\n    const parts = row.parts || [];"
    if "return drinkingWaterQualityTownMarkup(metric,row)" not in app:
        if town_marker not in app: raise RuntimeError("Marker compositeTownMarkup non trovato")
        app=app.replace(town_marker,town_add,1)
    pos="      : (row.notApplicable"
    posnew="      : (['drinkingWaterQuality','remediationProceedings'].includes(metric.meta.compositeType)\n        ? `<aside class=\"versilia-position\"><span class=\"overline\">Lettura del dato</span><strong>${html(row.formatted || formatValue(row.value,metric.meta.unit))}</strong><p>Dettaglio descrittivo: nessuna graduatoria di qualità.</p><div><span>${html(metric.aggregate.label)}</span><b>${html(formatValue(metric.aggregate.value, metric.meta.unit))}</b></div></aside>`\n        : row.notApplicable"
    if "nessuna graduatoria di qualità" not in app:
        if pos not in app: raise RuntimeError("Marker positionMarkup non trovato")
        app=app.replace(pos,posnew,1)
        app=app.replace("        : `<aside class=\"versilia-position\"><span class=\"overline\">Ordine del valore</span>", "        : `<aside class=\"versilia-position\"><span class=\"overline\">Ordine del valore</span>",1)
        needle="</b></div></aside>`);\n    container.innerHTML"
        if needle in app: app=app.replace(needle,"</b></div></aside>`));\n    container.innerHTML",1)
    bench="${(metricKey.startsWith('slowMobility') || demographicBreakdown || sexBreakdown) ? '' : townBenchmarkMarkup(metric, row, town)}"
    bench2="${(metricKey.startsWith('slowMobility') || demographicBreakdown || sexBreakdown || ['drinkingWaterQuality','remediationProceedings'].includes(metric.meta.compositeType)) ? '' : townBenchmarkMarkup(metric, row, town)}"
    app=app.replace(bench,bench2)
    APP03.write_text(app,encoding="utf-8")

    css=FIDELITY.read_text(encoding="utf-8")
    if "/* v124-water-remediation */" not in css:
        css += r"""
/* v124-water-remediation */
.water-quality-compare,.remediation-compare-list{display:grid;gap:12px}
.water-quality-compare-row,.remediation-compare-row{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:16px;align-items:center;padding:16px 18px;border:1px solid var(--line,#d8dee7);border-radius:14px;text-decoration:none;color:inherit;min-width:0}
.water-quality-compare-row span,.remediation-compare-row span{display:grid;text-align:right}
.water-quality-compare-row em{font-style:normal;font-weight:650}
.water-quality-selector,.remediation-selector{display:grid;gap:7px;margin:0 0 16px;max-width:560px}
.water-quality-selector select,.remediation-selector select{min-height:44px;padding:10px 14px;border-radius:10px;border:1px solid var(--line,#d8dee7);background:var(--surface,#fff);color:inherit}
.water-quality-locality,.remediation-town,.remediation-shell{min-width:0}
.water-quality-locality-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;padding:16px 0}
.water-quality-locality-head h4{margin:0 0 4px}
.water-quality-table-wrap{overflow-x:auto;max-width:100%;border:1px solid var(--line,#d8dee7);border-radius:14px}
.water-quality-table{width:100%;min-width:760px;border-collapse:collapse}
.water-quality-table th,.water-quality-table td{padding:14px 16px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line,#e7ebf0)}
.water-quality-table td:first-child{min-width:260px}
.water-quality-table td small{display:block;margin-top:5px;max-width:48ch;font-weight:400;line-height:1.35}
.remediation-summary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-bottom:16px}
.remediation-summary article{padding:16px 18px;border:1px solid var(--line,#d8dee7);border-radius:14px}
.remediation-summary span{display:block;margin-bottom:5px} .remediation-summary strong{font-size:1.7rem}
.remediation-procedure-list{display:grid;gap:12px}
.remediation-procedure-list article{display:grid;grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);gap:18px;padding:16px 18px;border:1px solid var(--line,#d8dee7);border-radius:14px;min-width:0}
.remediation-procedure-list h4{margin:5px 0} .remediation-procedure-list p{margin:0}
.remediation-procedure-list dl{margin:0;display:grid;gap:10px} .remediation-procedure-list dt{font-size:.78rem;opacity:.7} .remediation-procedure-list dd{margin:2px 0 0}
@media(max-width:720px){.water-quality-compare-row,.remediation-compare-row{grid-template-columns:1fr auto}.water-quality-compare-row em{grid-column:1/-1}.remediation-procedure-list{grid-template-columns:1fr}.remediation-summary{grid-template-columns:1fr 1fr}}
"""
        FIDELITY.write_text(css,encoding="utf-8")

def patch_release():
    replace_required(FINALIZER,'catalogo pubblico v1.23.0','catalogo pubblico v1.24.0')
    replace_required(FINALIZER,'VERSION = "v1.23.0"','VERSION = "v1.24.0"')
    replace_required(FINALIZER,'UPDATED = "28 agosto 2026"','UPDATED = "29 agosto 2026"')
    replace_required(FINALIZER,'EXPECTED_METRICS = 162','EXPECTED_METRICS = 165')
    replace_required(FINALIZER,'EXPECTED_INLINE = 158','EXPECTED_INLINE = 161')
    replace_required(README,'Versione dati corrente: **v1.23.0** — 28 agosto 2026.','Versione dati corrente: **v1.24.0** — 29 agosto 2026.')
    replace_all(README,'162 indicatori','165 indicatori'); replace_all(README,'158 con valori incorporati','161 con valori incorporati'); replace_all(README,'158 pagine canoniche','161 pagine canoniche')
    replace_required(APP05,"      ['2026.08.28-v1.23.0','28 agosto 2026','162 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunto il lotto Costa e mare: qualità delle aree di balneazione, campioni non conformi, spiagge Bandiera Blu, dinamica del litorale e costa protetta da opere rigide, con 4 Comuni costieri e 3 n.a. senza stime.'],",
      "      ['2026.08.29-v1.24.0','29 agosto 2026','165 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunto Acqua e bonifiche: perdite della rete idrica Istat, qualità dell’acqua potabile GAIA per 70 località e procedimenti SISBON attivi/chiusi, senza proxy per fognatura o depurazione.'],\n      ['2026.08.28-v1.23.0','28 agosto 2026','162 indicatori complessivi in 11 temi, inclusi i 4 indicatori climatici. Aggiunto il lotto Costa e mare: qualità delle aree di balneazione, campioni non conformi, spiagge Bandiera Blu, dinamica del litorale e costa protetta da opere rigide, con 4 Comuni costieri e 3 n.a. senza stime.'],")
    for p in (APPJS,UXH,EXPORT,BUILD_SAFE,BUILD_BRAND): replace_all(p,"20260829-v123-coast-ui2",ASSET_VERSION)
    replace_all(SW,"ov-pwa-20260829-v123-coast-ui2",PWA_VERSION)
    replace_all(BUILD_BRAND,'PWA_JS_REVISION = "catalog-v123"','PWA_JS_REVISION = "catalog-v124"')
    test=TEST.read_text(encoding="utf-8")
    test=test.replace('release v1.23.0','release v1.24.0').replace('"2026.08.28-v1.23.0" in app and "2026.08.28-v1.22.0" in app and "162 indicatori complessivi" in app','"2026.08.29-v1.24.0" in app and "2026.08.28-v1.23.0" in app and "165 indicatori complessivi" in app')
    test=test.replace('**v1.23.0** — 28 agosto 2026','**v1.24.0** — 29 agosto 2026').replace('"162 indicatori" in readme and "158 con valori incorporati" in readme','"165 indicatori" in readme and "161 con valori incorporati" in readme')
    test=test.replace('20260829-v123-coast-ui2',ASSET_VERSION).replace('catalog-v123','catalog-v124').replace('20260829-v123','20260829-v124').replace('ov-pwa-20260829-v123','ov-pwa-20260829-v124')
    TEST.write_text(test,encoding="utf-8")
    if HISTORY.exists():
        txt=HISTORY.read_text(encoding="utf-8")
        note="\n## Acqua e bonifiche · v1.24.0\n\n- Perdite rete idrica: serie comunali Istat 2012, 2015, 2018; nessuna interpolazione.\n- Qualità acqua potabile: dettaglio GAIA 2° semestre 2025 per 70 località; nessuna media comunale delle concentrazioni.\n- SISBON: fotografia 29 agosto 2026, 152 codici regionali univoci.\n"
        if "## Acqua e bonifiche · v1.24.0" not in txt: HISTORY.write_text(txt+note,encoding="utf-8")
    if COHERENCE.exists():
        txt=COHERENCE.read_text(encoding="utf-8")
        note="\n### Acqua e bonifiche v1.24.0\n\nLe tabelle analitiche mantengono almeno 14 px di padding, gestiscono l’overflow orizzontale e le differenze percentuali restano espresse con `%`, senza `punti` o `p.p.`.\n"
        if "### Acqua e bonifiche v1.24.0" not in txt: COHERENCE.write_text(txt+note,encoding="utf-8")

def main():
    site=load(SITE); reg=load(REGISTRY); state=load(STATE)
    defs,localities=fetch_gaia()
    procedures,sis_sha=fetch_sisbon()
    snap=build_snapshot(defs,localities,procedures,sis_sha); save(DETAIL,snap)
    apply_site(site,snap); apply_registry(reg); apply_state(state)
    save(SITE,site); save(REGISTRY,reg); save(STATE,state)
    patch_ui(); patch_release()
    print("v1.24.0 materializzata: 165 indicatori, 3 nuovi in Ambiente → Acqua e bonifiche.")

if __name__=="__main__": main()
