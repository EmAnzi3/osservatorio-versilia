#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, math, urllib.request
from pathlib import Path

import audit_waste_cost_ispra as src

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data/site-data.json"
REGIONAL_URL="https://www.catasto-rifiuti.isprambiente.it/index.php?aa=2024&advice=si&pg=costiregione"
PROVINCE_URL="https://www.catasto-rifiuti.isprambiente.it/index.php?aa=2024&p={page}&pg=provincia"
LUCCA_MUNICIPAL_URL="https://www.catasto-rifiuti.isprambiente.it/index.php?aa=2024&p={page}&pg=comune&regid=09046"
NATIONAL_URL="https://www.catasto-rifiuti.isprambiente.it/index.php?aa=2024&pg=nazione"

def fetch_url(url):
    request=urllib.request.Request(url,headers=src.UA)
    with urllib.request.urlopen(request,timeout=45) as response:
        return response.read().decode("utf-8",errors="replace")

def population_number(value):
    text=str(value or "").strip().replace("\u00a0","").replace(" ","")
    if not text: return None
    if "," not in text:
        text=text.replace(".","")
    else:
        text=text.replace(".","").split(",",1)[0]
    try: return float(int(text))
    except ValueError: return None

def percent_number(value):
    return src.number(str(value or "").strip().rstrip("%"))

def parse_production_row(row,*,municipal=False):
    if municipal:
        if len(row)<9: return None
        code=str(row[2]).strip()
        if not (len(code)==8 and code.isdigit()): return None
        population=population_number(row[1]); rd=src.number(row[4]); ru=src.number(row[5])
        pct=percent_number(row[6]); pc_ru=src.number(row[8])
        if None in (population,rd,ru,pct,pc_ru): return None
        if src.norm(row[3])!="comune": return None
        return {"name":str(row[0]).strip(),"code":code,"population":population,"rd":rd,"ru":ru,"pct":pct,"pcRu":pc_ru}
    if len(row)<9: return None
    code=str(row[2]).strip()
    if not (len(code)==5 and code.isdigit()): return None
    population=population_number(row[3]); rd=src.number(row[4]); ru=src.number(row[5])
    if None in (population,rd,ru): return None
    return {"region":str(row[0]).strip(),"province":str(row[1]).strip(),"code":code,"population":population,"rd":rd,"ru":ru}

def province_production():
    found={}
    pages=[]
    empty_after=0
    for page in range(1,12):
        url=PROVINCE_URL.format(page=page); pages.append(url)
        table=src.Tables(); table.feed(fetch_url(url))
        added=0
        for row in table.rows:
            item=parse_production_row(row)
            if item is None: continue
            code=item["code"]
            if code in found:
                old=found[code]
                if any(not math.isclose(float(old[k]),float(item[k]),rel_tol=0.0,abs_tol=.001) for k in ("population","rd","ru")):
                    raise RuntimeError(f"ISPRA: provincia duplicata incoerente {code}")
                continue
            found[code]=item; added+=1
        if added==0:
            empty_after+=1
            if page>=6 and empty_after>=2: break
        else:
            empty_after=0
    if not 95<=len(found)<=120:
        raise RuntimeError(f"ISPRA: copertura provinciale Italia inattesa {len(found)}")
    tuscany=[x for x in found.values() if str(x["code"]).startswith("09")]
    if len(tuscany)!=10:
        sample=[{"code":x["code"],"region":x["region"],"province":x["province"]} for x in list(found.values())[:20]]
        raise RuntimeError(f"ISPRA: province Toscana inattese {len(tuscany)}; sample={sample}")
    return list(found.values()),tuscany,pages

def lucca_municipal_production():
    found={}
    pages=[]
    for page in (1,2,3):
        url=LUCCA_MUNICIPAL_URL.format(page=page); pages.append(url)
        table=src.Tables(); table.feed(fetch_url(url))
        added=0
        for row in table.rows:
            item=parse_production_row(row,municipal=True)
            if item is None: continue
            found[src.norm(item["name"])]=item; added+=1
        if page>=2 and added==0: break
    if not 30<=len(found)<=40:
        raise RuntimeError(f"ISPRA: comuni provincia Lucca inattesi {len(found)}")
    return found,pages

def aggregate_production(rows):
    population=sum(float(r["population"]) for r in rows)
    rd=sum(float(r["rd"]) for r in rows)
    ru=sum(float(r["ru"]) for r in rows)
    if population<=0 or ru<=0 or not 0<=rd<=ru:
        raise RuntimeError("ISPRA: aggregato produzione non valido")
    return {
        "population":population,"rdTonnes":rd,"ruTonnes":ru,
        "recycling":rd/ru*100.0,
        "wastePerResident":ru*1000.0/population,
        "residualWaste":(ru-rd)*1000.0/population,
    }

def official_national_2024():
    table=src.Tables(); table.feed(fetch_url(NATIONAL_URL))
    hits=[]
    for row in table.rows:
        if len(row)<7 or src.norm(row[0])!="italia": continue
        population=population_number(row[1])
        rd=src.number(row[2]); ru=src.number(row[3]); pct=percent_number(row[4])
        if None in (population,rd,ru,pct) or ru<=0: continue
        hits.append({
            "population":population,"rdTonnes":rd,"ruTonnes":ru,
            "recycling":rd/ru*100.0,"publishedRecycling":pct,"rawRow":row
        })
    if len(hits)!=1:
        raise RuntimeError(f"ISPRA: riga nazionale ITALIA 2024 non univoca {hits}")
    return hits[0]

def official_regional_costs():
    request=urllib.request.Request(REGIONAL_URL,headers=src.UA)
    with urllib.request.urlopen(request,timeout=45) as response:
        text=response.read().decode("utf-8",errors="replace")
    table=src.Tables(); table.feed(text)
    out={}
    for row in table.rows:
        if len(row)<12: continue
        name=src.norm(row[0])
        if name not in {"toscana","italia"}: continue
        value=src.number(row[-1])
        if value is None or not 50<=value<=1000: continue
        out[name]={"ctot":float(value),"rawRow":row}
    if set(out)!={"toscana","italia"}:
        raise RuntimeError(f"ISPRA: righe ufficiali Toscana/Italia CTOTab non univoche: {out}")
    return out

def all_tuscany_rows():
    found={}
    aggregates=[]
    pages=[]
    for page in range(1,20):
        text=src.fetch(page); table=src.Tables(); table.feed(text); pages.append(src.URL.format(page=page))
        valid_on_page=0
        for row in table.rows:
            if len(row)<5: continue
            municipalities=src.number(row[2])
            population=src.number(row[3])
            ctot=src.number(row[-1])
            name=src.norm(row[0])
            if municipalities is not None and population is not None and population>0 and ctot is not None and 230<=int(round(municipalities))<=280:
                aggregates.append({"municipalityCount":int(round(municipalities)),"population":population,"ctot":ctot,"rawRow":row,"page":page})
                continue
            if municipalities is None or int(round(municipalities))!=1 or population is None or population<=0 or ctot is None:
                continue
            if not name: continue
            if name in found:
                old=found[name]
                if not math.isclose(old["population"],population,abs_tol=.5) or not math.isclose(old["ctot"],ctot,abs_tol=.01):
                    raise RuntimeError(f"ISPRA duplicato incoerente {row[0]}")
            found[name]={"label":row[0],"population":population,"ctot":ctot}
            valid_on_page+=1
        if page>=10 and valid_on_page==0:
            break
    return found,aggregates,pages

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    site=json.loads(SITE.read_text(encoding="utf-8"))
    rows,aggregates,pages=all_tuscany_rows()
    if not 230<=len(rows)<=280: raise RuntimeError(f"ISPRA: copertura comunale Toscana inattesa {len(rows)}")
    official=official_regional_costs()
    regional={"ctot":official["toscana"]["ctot"],"rawRow":official["toscana"]["rawRow"],"source":REGIONAL_URL}
    national={"ctot":official["italia"]["ctot"],"rawRow":official["italia"]["rawRow"],"source":REGIONAL_URL}
    italy_provinces,tuscany_provinces,province_pages=province_production()
    lucca_production,municipal_pages=lucca_municipal_production()
    production_tuscany=aggregate_production(tuscany_provinces)
    production_italy=aggregate_production(italy_provinces)
    national_control=official_national_2024()
    errors=[]
    for key in ("rdTonnes","ruTonnes"):
        if not math.isclose(production_italy[key],national_control[key],rel_tol=0.0,abs_tol=1.0):
            errors.append(f"national/{key}: province sum {production_italy[key]} != official {national_control[key]}")
    public={str(r["town"]):float(r["value"]) for r in site["metrics"]["wasteServiceCost"]["rows"]}
    if len(public)!=7: errors.append(f"wasteServiceCost pubblico {len(public)}/7")
    for town,observed in public.items():
        got=rows.get(src.norm(town))
        if not got: errors.append(f"{town}: ISPRA assente"); continue
        if not math.isclose(observed,float(got["ctot"]),rel_tol=0.0,abs_tol=.011):
            errors.append(f"{town}: {observed} != {got['ctot']}")
    metric_checks={
        "recycling":("pct",.011),
        "wastePerResident":("pcRu",.11),
        "residualWaste":(None,.25),
    }
    for metric_id,(source_key,tolerance) in metric_checks.items():
        metric=(site.get("metrics") or {}).get(metric_id) or {}
        public_rows=metric.get("rows") or []
        if len(public_rows)!=7:
            errors.append(f"{metric_id} pubblico {len(public_rows)}/7")
            continue
        for row in public_rows:
            town=str(row.get("town") or "")
            got=lucca_production.get(src.norm(town))
            if not got:
                errors.append(f"{metric_id}/{town}: ISPRA produzione assente")
                continue
            if source_key is None:
                expected=(float(got["ru"])-float(got["rd"]))*1000.0/float(got["population"])
            else:
                expected=float(got[source_key])
            observed=float(row.get("value"))
            if not math.isclose(observed,expected,rel_tol=0.0,abs_tol=tolerance):
                errors.append(f"{metric_id}/{town}: {observed} != {expected}")
    pop=sum(v["population"] for v in rows.values())
    weighted=sum(v["population"]*v["ctot"] for v in rows.values())/pop
    regional_value=float(regional["ctot"])
    gate="PASS" if not errors else "FAIL"
    payload={
      "schemaVersion":1,"publisher":"ISPRA — Catasto Nazionale Rifiuti","profileId":"ispra-environment-annual","referenceYear":2024,
      "status":"ACQUIRED_CANDIDATE" if gate=="PASS" else "CANDIDATE_REJECTED",
      "sources":{"template":src.URL,"pagesScanned":pages},
      "benchmarks":{
        "wasteServiceCost":{"year":"2024","unit":"currency","formula":"CTOTab regionale/nazionale ufficiale ISPRA","tuscany":regional_value,"italy":float(national["ctot"])},
        "recycling":{"year":"2024","unit":"percent","formula":"Σ RD / Σ RU × 100, aggregazione quantità provinciali ISPRA","tuscany":production_tuscany["recycling"],"italy":production_italy["recycling"]},
        "wastePerResident":{"year":"2024","unit":"kgPerResident","formula":"Σ RU (t) × 1000 / Σ popolazione, aggregazione provinciale ISPRA","tuscany":production_tuscany["wastePerResident"],"italy":production_italy["wastePerResident"]},
        "residualWaste":{"year":"2024","unit":"kgPerResident","formula":"(Σ RU - Σ RD) (t) × 1000 / Σ popolazione, aggregazione provinciale ISPRA","tuscany":production_tuscany["residualWaste"],"italy":production_italy["residualWaste"]}
      },
      "raw":{
        "tuscanyMunicipalitiesWithCost":len(rows),"municipalWeightedCheck":weighted,
        "regionalOfficial":regional,"nationalOfficial":national,
        "production":{"tuscany":production_tuscany,"italy":production_italy,"nationalControl":national_control,"provincePages":province_pages,"municipalPages":municipal_pages}
      },
      "qualityGate":{"status":gate,"publicReconciliation":"4 metrics × 7/7 towns PASS" if gate=="PASS" else "FAIL","errors":errors},
      "blocked":{}
    }
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"candidateMetrics":sorted(payload["benchmarks"]),"tuscany":regional_value,"townsWithCost":len(rows),"officialItaly":float(national["ctot"]),"weightedMunicipalCheck":weighted,"gate":payload["qualityGate"]},ensure_ascii=False))
if __name__=="__main__": main()
