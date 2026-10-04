#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parents[1]
SITE_DATA=ROOT/"data"/"site-data.json"
BUILDING_SNAPSHOT=ROOT/"data"/"source-snapshots"/"mim-edilizia-scolastica-versilia-2024-25.json"

BASE="https://dati.istruzione.it/opendata/opendata/catalogo/elements1/"
FILES={
    "registry_state":"SCUANAGRAFESTAT20242520250831.csv",
    "registry_private":"SCUANAGRAFEPAR20242520250831.csv",
    "classes_state":"ALUCORSOINDCLASTA20242520250831.csv",
    "classes_private":"ALUCORSOINDCLAPAR20242520250831.csv",
    "time_state":"ALUTEMPOSCUOLASTA20242520250831.csv",
    "time_private":"ALUTEMPOSCUOLAPAR20242520250831.csv",
}
BUILDING_DATASETS={
    "schoolBuildingSafetyDocs":{
        "url":BASE+"leaf/EDICONSICUREZZASTA202120242520250806.csv",
        "fields":{
            "agibilita":"CERTIFICATOSEGNALAZIONEAGIBILITA",
            "cpi":"CERTIFICATOPREVENZIONEINCENDI",
            "sciaAntincendio":"SCIAANTINCENDIO",
            "rinnovoAntincendio":"ATTESTAZIONERINNOVOPERIODICOCONFORMITAANTINCENDIO",
        },
    },
    "schoolBuildingAccessibility":{
        "url":BASE+"leaf/EDISUPBARARCSTA202120242520250806.csv",
        "fields":{"accessibilita":"ACCORGIMENTISUPERAMENTOBARRIEREARCHITETTONICHE"},
    },
    "schoolBuildingFacilities":{
        "url":BASE+"leaf/EDIAMBFUNZSTA202120242520250806.csv",
        "fields":{"mensa":"MENSA","palestra":"PALESTRA"},
    },
    "schoolBuildingAge":{
        "url":BASE+"leaf/EDIETAORIGINESTA202120242520250806.csv",
        "fields":{"periodoCostruzione":"PERIODOCOSTRUZIONE"},
    },
    "schoolBuildingTransport":{
        "url":BASE+"leaf/EDICOLLEGAMENTISTA202120242520250806.csv",
        "fields":{
            "scuolabus":"SCUOLABUS",
            "tplUrbano":"TRASPORTIPUBBLICIURBANI",
            "tplInterurbano":"TRASPORTIPUBBLICIINTERURBANI",
        },
    },
}
PERIOD_ORDER=[
    "prima del 1800",
    "tra il 1800 e il 1899",
    "tra il 1900 e il 1933",
    "tra il 1934 e il 1949",
    "tra il 1950 e il 1970",
    "tra il 1971 e il 1975",
    "tra il 1976 e il 1992",
    "tra il 1993 e il 1996",
    "tra il 1997 e il 2008",
    "tra il 2009 e il 2017",
    "dal 2018 in poi",
]
UNKNOWN={"NON DEFINITO","","-","_"}

# Il dataset edilizia contiene un plesso storico non presente nell'anagrafe
# 2024/25 usata per il join. La collocazione è verificata dall'Ufficio
# Scolastico Regionale Sicilia: TPEE816022 = Plesso "Cuore di Gesù", Marsala (TP).
# L'override serve solo a preservare correttamente Toscana/Italia; qualunque
# altro codice non mappato continua a far fallire il gate.
REGISTRY_OVERRIDES={
    "TPEE816022":{
        "region":"SICILIA",
        "town":"MARSALA",
        "order":"PRIMARIA",
        "source":"https://tp.usr.sicilia.it/download/1333/10758/10761/tabella-posti-sostegno-o-d-2025-2026.pdf",
    },
}


def norm(x):
    return re.sub(r"\s+"," ",str(x or "").strip().upper())


def canon(field,value):
    s=re.sub(r"\s+"," ",str(value or "").strip())
    return s.lower() if field=="periodoCostruzione" else s.upper()


def num(x):
    try:return float(str(x or "0").replace(",","."))
    except:return 0.0


def fetch_csv(session,url):
    r=session.get(url,timeout=240)
    r.raise_for_status()
    text=r.content.decode("utf-8-sig",errors="replace")
    if "<!doctype html" in text[:500].lower() or "<html" in text[:500].lower():
        raise RuntimeError(f"{url}: risposta HTML invece di CSV")
    try: delim=csv.Sniffer().sniff(text[:12000],delimiters=",;\t|").delimiter
    except csv.Error: delim=","
    reader=csv.DictReader(io.StringIO(text),delimiter=delim)
    rows=list(reader)
    if not rows:
        raise RuntimeError(f"{url}: CSV vuoto")
    return rows,{"url":r.url,"bytes":len(r.content),"delimiter":delim,"headers":list(reader.fieldnames or [])}


def fetch_named(session,name):
    return fetch_csv(session,BASE+FILES[name])[0]


def build_school_registry(registry_rows):
    school={}
    duplicate_conflicts=[]
    for r in registry_rows:
        code=str(r.get("CODICESCUOLA") or "").strip()
        if not code:
            continue
        info={
            "region":norm(r.get("REGIONE")),
            "town":norm(r.get("DESCRIZIONECOMUNE")),
            "order":norm(r.get("DESCRIZIONETIPOLOGIAGRADOISTRUZIONESCUOLA")),
        }
        if code in school and school[code]!=info:
            duplicate_conflicts.append({"code":code,"left":school[code],"right":info})
        school[code]=info
    if duplicate_conflicts:
        raise RuntimeError(f"Anagrafe scuole: {len(duplicate_conflicts)} codici con attributi confliggenti")
    return school


def school_candidates(school,class_rows,time_rows):
    scopes={"tuscany":lambda reg:reg=="TOSCANA","italy":lambda reg:True}
    out={}
    valid_orders=("PRIMARIA","SECONDARIA")
    for scope,pred in scopes.items():
        t=defaultdict(float)
        all_codes={c for c,v in school.items() if pred(v["region"])}
        ps_codes={c for c,v in school.items() if pred(v["region"]) and any(x in v["order"] for x in valid_orders)}
        t["schoolSitesAll"]=len(all_codes)
        t["schoolSitesPrimarySecondary"]=len(ps_codes)
        for r in class_rows:
            code=str(r.get("CODICESCUOLA") or "").strip()
            info=school.get(code)
            if not info or not pred(info["region"]):
                continue
            order=norm(r.get("ORDINESCUOLA"))
            if not any(x in order for x in valid_orders):
                continue
            t["schoolStudents"]+=num(r.get("ALUNNIMASCHI"))+num(r.get("ALUNNIFEMMINE"))
            t["classes"]+=num(r.get("CLASSI"))
        for r in time_rows:
            code=str(r.get("CODICESCUOLA") or "").strip()
            info=school.get(code)
            if not info or not pred(info["region"]):
                continue
            if "PRIMARIA" not in norm(r.get("ORDINESCUOLA")):
                continue
            n=num(r.get("ALUNNIMASCHI"))+num(r.get("ALUNNIFEMMINE"))
            t["primaryStudents"]+=n
            if norm(r.get("TEMPOSCUOLA"))=="TEMPO PIENO":
                t["fullTimeStudents"]+=n
        t["studentsPerClass"]=t["schoolStudents"]/t["classes"] if t["classes"] else None
        t["primaryFullTimeShare"]=t["fullTimeStudents"]/t["primaryStudents"]*100 if t["primaryStudents"] else None
        out[scope]=dict(t)
    return out


def reconcile_school_sites(site,school,candidates):
    public_rows={norm(row.get("town")):int(row.get("value")) for row in site["metrics"]["schoolSites"]["rows"]}
    expected=set(public_rows)
    municipal_all={town:len({code for code,info in school.items() if info["town"]==town}) for town in sorted(expected)}
    municipal_ps={town:len({code for code,info in school.items() if info["town"]==town and any(x in info["order"] for x in ("PRIMARIA","SECONDARIA"))}) for town in sorted(expected)}
    all_match=municipal_all==public_rows
    ps_match=municipal_ps==public_rows
    if all_match!=ps_match:
        basis="allSchools" if all_match else "primarySecondary"
        key="schoolSitesAll" if all_match else "schoolSitesPrimarySecondary"
        for scope in ("tuscany","italy"):
            candidates[scope]["schoolSites"]=candidates[scope][key]
        return {"status":"PASS","basis":basis,"public":public_rows,"reconciled":municipal_all if all_match else municipal_ps}
    return {"status":"AMBIGUOUS_OR_MISMATCH","public":public_rows,"allSchools":municipal_all,"primarySecondary":municipal_ps}


def building_records(rows,school,fields):
    buildings={}
    unmapped=Counter()
    overrides_used=Counter()
    for row in rows:
        code=str(row.get("CODICESCUOLA") or "").strip()
        info=school.get(code)
        if not info:
            override=REGISTRY_OVERRIDES.get(code.upper())
            if override:
                info=override
                overrides_used[code.upper()]+=1
        if not info and code.startswith("AO"):
            # La Valle d'Aosta usa codici scolastici AO* non presenti
            # nell'anagrafica nazionale ordinaria. Per benchmark regionale/
            # nazionale basta preservarne correttamente l'appartenenza regionale.
            info={"region":"VALLE D'AOSTA","town":"","order":""}
        if not info:
            unmapped[code or "<blank>"]+=1
            continue
        bid=str(row.get("CODICEEDIFICIO") or "").strip()
        if not bid:
            continue
        rec=buildings.setdefault(bid,{"regions":set(),"towns":set(),"fields":{k:set() for k in fields}})
        rec["regions"].add(info["region"])
        if info["town"]:
            rec["towns"].add(info["town"])
        for local,col in fields.items():
            rec["fields"][local].add(canon(local,row.get(col)))
    conflicts=[]
    multi_town=0
    finalized={}
    for bid,rec in buildings.items():
        if len(rec["regions"])!=1:
            conflicts.append({"building":bid,"regions":sorted(rec["regions"]),"towns":sorted(rec["towns"])})
            continue
        vals={}
        bad=False
        for local,items in rec["fields"].items():
            if len(items)!=1:
                conflicts.append({"building":bid,"field":local,"values":sorted(items)})
                bad=True
            else:
                vals[local]=next(iter(items))
        if bad:
            continue
        if len(rec["towns"])>1:
            multi_town+=1
        finalized[bid]={
            "region":next(iter(rec["regions"])),
            "towns":sorted(rec["towns"]),
            "fields":vals,
        }
    return finalized,{
        "unmappedSchoolRows":sum(unmapped.values()),
        "unmappedSchoolCodes":dict(unmapped.most_common(20)),
        "registryOverridesUsed":dict(overrides_used),
        "registryOverrideSources":{code:REGISTRY_OVERRIDES[code]["source"] for code in overrides_used},
        "conflicts":conflicts[:50],
        "conflictCount":len(conflicts),
        "multiTownBuildings":multi_town,
    }


def aggregate_buildings(records,fields,scope):
    counters={field:Counter() for field in fields}
    buildings=0
    for rec in records.values():
        if scope=="tuscany" and rec["region"]!="TOSCANA":
            continue
        buildings+=1
        for field in fields:
            counters[field][rec["fields"][field]]+=1
    return {"buildings":buildings,"fields":{field:dict(counter) for field,counter in counters.items()}}


def expected_counter(snapshot,town,field):
    return {canon(field,k):int(v or 0) for k,v in (snapshot["towns"][town][field] or {}).items()}


def versilia_reconcile(records,fields,snapshot):
    town_lookup={norm(t):t for t in snapshot["towns"]}
    actual={town:{"buildings":set(),"fields":{field:Counter() for field in fields}} for town in snapshot["towns"]}
    errors=[]
    for bid,rec in records.items():
        matched=sorted({town_lookup[t] for t in rec.get("towns",[]) if t in town_lookup})
        if len(matched)>1:
            errors.append(f"{bid}: edificio associato a più Comuni Versilia {matched}")
            continue
        if not matched:
            continue
        town=matched[0]
        actual[town]["buildings"].add(bid)
        for field in fields:
            actual[town]["fields"][field][rec["fields"][field]]+=1
    for town,expected in snapshot["towns"].items():
        if len(actual[town]["buildings"])!=int(expected["buildings"]):
            errors.append(f"{town}: edifici {len(actual[town]['buildings'])} != {expected['buildings']}")
        for field in fields:
            got=dict(actual[town]["fields"][field])
            exp=expected_counter(snapshot,town,field)
            if got!=exp:
                errors.append(f"{town}/{field}: {got} != {exp}")
    return {"status":"PASS" if not errors else "FAIL","errors":errors[:80]}


def known_total(statuses):
    return sum(int(v or 0) for k,v in statuses.items() if canon("",k) not in UNKNOWN)


def yes_share(statuses):
    den=known_total(statuses)
    return (int(statuses.get("SI",0) or 0)/den*100.0) if den else None


def age_share(statuses):
    defined=sum(int(statuses.get(k,0) or 0) for k in PERIOD_ORDER)
    old=sum(int(statuses.get(k,0) or 0) for k in PERIOD_ORDER[:5])
    return old/defined*100.0 if defined else None


def building_benchmarks(raw):
    out={}
    mapping={
        "schoolBuildingSafetyDocs":("schoolBuildingSafetyDocs","agibilita",yes_share),
        "schoolBuildingAccessibility":("schoolBuildingAccessibility","accessibilita",yes_share),
        "schoolBuildingFacilities":("schoolBuildingFacilities","mensa",yes_share),
        "schoolBuildingAge":("schoolBuildingAge","periodoCostruzione",age_share),
        "schoolBuildingTransport":("schoolBuildingTransport","scuolabus",yes_share),
    }
    for metric,(dataset,field,fn) in mapping.items():
        out[metric]={"unit":"percent","schoolYear":"2024/25"}
        for scope in ("tuscany","italy"):
            out[metric][scope]=fn(raw[dataset][scope]["fields"][field])
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    s=requests.Session()
    s.headers["User-Agent"]="OsservatorioVersilia-A3-MIM-benchmark/3.0"

    registry=fetch_named(s,"registry_state")+fetch_named(s,"registry_private")
    school=build_school_registry(registry)
    class_rows=fetch_named(s,"classes_state")+fetch_named(s,"classes_private")
    time_rows=fetch_named(s,"time_state")+fetch_named(s,"time_private")
    candidates=school_candidates(school,class_rows,time_rows)

    site=json.loads(SITE_DATA.read_text(encoding="utf-8"))
    school_sites_gate=reconcile_school_sites(site,school,candidates)

    governed=json.loads(BUILDING_SNAPSHOT.read_text(encoding="utf-8"))
    building_raw={}
    building_sources={}
    building_diagnostics={}
    reconciliation={}
    building_failures=[]
    for metric_id,spec in BUILDING_DATASETS.items():
        rows,source=fetch_csv(s,spec["url"])
        records,diag=building_records(rows,school,spec["fields"])
        building_sources[metric_id]=source
        building_diagnostics[metric_id]=diag
        if diag["unmappedSchoolRows"] or diag["conflictCount"]:
            building_failures.append(f"{metric_id}: unmapped={diag['unmappedSchoolRows']} conflicts={diag['conflictCount']}")
        reconciliation[metric_id]=versilia_reconcile(records,spec["fields"],governed)
        if reconciliation[metric_id]["status"]!="PASS":
            building_failures.extend(f"{metric_id}: {x}" for x in reconciliation[metric_id]["errors"])
        building_raw[metric_id]={
            "tuscany":aggregate_buildings(records,spec["fields"],"tuscany"),
            "italy":aggregate_buildings(records,spec["fields"],"italy"),
        }

    building_gate={"status":"PASS" if not building_failures else "FAIL","errors":building_failures[:120],"reconciliation":reconciliation}
    benchmarks=building_benchmarks(building_raw) if building_gate["status"]=="PASS" else {}

    payload={
        "schemaVersion":4,
        "publisher":"MIM — Portale unico dei dati della scuola",
        "profileId":"mim-school-year",
        "schoolYear":"2024/25",
        "sources":{k:BASE+v for k,v in FILES.items()},
        "candidates":candidates,
        "schoolSitesGate":school_sites_gate,
        "schoolBuildingSources":building_sources,
        "schoolBuildingDiagnostics":building_diagnostics,
        "schoolBuildingRaw":building_raw,
        "schoolBuildingBenchmarks":benchmarks,
        "schoolBuildingGate":building_gate,
        "status":"ACQUIRED_CANDIDATE" if building_gate["status"]=="PASS" else "BUILDING_CANDIDATE_REJECTED",
    }
    p=Path(args.output)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":payload["status"],
        "schoolSitesGate":school_sites_gate["status"],
        "schoolBuildingGate":building_gate["status"],
        "buildingMetrics":sorted(benchmarks),
        "output":str(p),
    },ensure_ascii=False))


if __name__=="__main__":
    main()
