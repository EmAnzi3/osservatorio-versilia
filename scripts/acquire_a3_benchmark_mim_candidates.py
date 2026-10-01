#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,re
from collections import defaultdict
from pathlib import Path
import requests

BASE="https://dati.istruzione.it/opendata/opendata/catalogo/elements1/"
FILES={
 "registry_state":"SCUANAGRAFESTAT20242520250831.csv",
 "registry_private":"SCUANAGRAFEPAR20242520250831.csv",
 "classes_state":"ALUCORSOINDCLASTA20242520250831.csv",
 "classes_private":"ALUCORSOINDCLAPAR20242520250831.csv",
 "time_state":"ALUTEMPOSCUOLASTA20242520250831.csv",
 "time_private":"ALUTEMPOSCUOLAPAR20242520250831.csv",
}
def norm(x): return re.sub(r"\s+"," ",str(x or "").strip().upper())
def rows(session,name):
    r=session.get(BASE+FILES[name],timeout=240); r.raise_for_status()
    text=r.content.decode("utf-8-sig",errors="replace")
    return list(csv.DictReader(io.StringIO(text),delimiter=","))
def num(x):
    try:return float(str(x or "0").replace(",","."))
    except:return 0.0
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    s=requests.Session(); s.headers["User-Agent"]="OsservatorioVersilia-A3-MIM-benchmark/1.0"
    registry=rows(s,"registry_state")+rows(s,"registry_private")
    school={}
    for r in registry:
        code=str(r.get("CODICESCUOLA") or "").strip()
        reg=norm(r.get("REGIONE"))
        order=norm(r.get("DESCRIZIONETIPOLOGIAGRADOISTRUZIONESCUOLA"))
        if code: school[code]={"region":reg,"order":order}
    scopes={"tuscany":lambda reg:reg=="TOSCANA","italy":lambda reg:True}
    out={}
    for scope,pred in scopes.items():
        t=defaultdict(float)
        valid_orders=("PRIMARIA","SECONDARIA")
        site_codes={c for c,v in school.items() if pred(v["region"]) and any(x in v["order"] for x in valid_orders)}
        t["schoolSites"]=len(site_codes)
        for key in ("classes_state","classes_private"):
            for r in rows(s,key):
                code=str(r.get("CODICESCUOLA") or "").strip()
                info=school.get(code)
                if not info or not pred(info["region"]): continue
                order=norm(r.get("ORDINESCUOLA"))
                if not any(x in order for x in valid_orders): continue
                t["schoolStudents"]+=num(r.get("ALUNNIMASCHI"))+num(r.get("ALUNNIFEMMINE"))
                t["classes"]+=num(r.get("CLASSI"))
        for key in ("time_state","time_private"):
            for r in rows(s,key):
                code=str(r.get("CODICESCUOLA") or "").strip()
                info=school.get(code)
                if not info or not pred(info["region"]): continue
                if "PRIMARIA" not in norm(r.get("ORDINESCUOLA")): continue
                n=num(r.get("ALUNNIMASCHI"))+num(r.get("ALUNNIFEMMINE"))
                t["primaryStudents"]+=n
                if norm(r.get("TEMPOSCUOLA"))=="TEMPO PIENO": t["fullTimeStudents"]+=n
        t["studentsPerClass"]=t["schoolStudents"]/t["classes"] if t["classes"] else None
        t["primaryFullTimeShare"]=t["fullTimeStudents"]/t["primaryStudents"]*100 if t["primaryStudents"] else None
        out[scope]=dict(t)
    payload={"schemaVersion":1,"publisher":"MIM","profileId":"mim-school-year","schoolYear":"2024/25","sources":{k:BASE+v for k,v in FILES.items()},"candidates":out,"status":"ACQUIRED_CANDIDATE"}
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":payload["status"],"metrics":["schoolSites","schoolStudents","studentsPerClass","primaryFullTimeShare"],"output":str(p)},ensure_ascii=False))
if __name__=="__main__": main()
