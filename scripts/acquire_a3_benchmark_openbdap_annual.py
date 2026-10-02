#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import zipfile
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

import requests

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"data/site-data.json"
BASELINE=ROOT/"data/source-snapshots/bilanci-v1.6.0.json"
V139=ROOT/"data/source-snapshots/bilanci-v139.json"
DEMOGRAPHY=ROOT/"data/source-snapshots/a3-istat-demography-benchmark-2026.json"
BASE="https://openbdap.rgs.mef.gov.it"
PORTAL=BASE+"/it/FET/Analizza"
ARCHIVE="/Datasets_FET/Rendiconto/2025/2025_Rendiconto - Schemi di bilancio_TOSCANA.zip"
MEMBERS={
 "entrate":"Rendiconto SDB Entrate Riepilogo Titoli_TOSCANA.csv",
 "spese":"Rendiconto SDB Spese Riepilogo Titoli_TOSCANA.csv",
 "missioni":"Rendiconto SDB Spese Riepilogo Missioni_TOSCANA.csv",
 "risultato":"Rendiconto SDB Allegato A Risultato di Amministrazione_TOSCANA.csv",
}
EXPECTED_TUSCANY_MUNICIPALITIES=273

BASELINE_METRICS={
 "currentRevenueAccruedPerResident",
 "currentExpenditureCommittedPerResident",
 "capitalExpenditureCommittedPerResident",
 "ownRevenueShare",
 "currentCollectionCapacity",
 "currentPaymentCapacity",
 "availableAdministrationResultPerResident",
 "educationMissionExpenditurePerResident",
 "socialMissionExpenditurePerResident",
 "environmentMissionExpenditurePerResident",
 "mobilityMissionExpenditurePerResident",
 "cultureSportMissionExpenditurePerResident",
 "tourismDevelopmentMissionExpenditurePerResident",
}
V139_METRICS={
 "fcdePerResident",
 "yearEndCashFundPerResident",
 "generalAdministrationMissionExpenditurePerResident",
 "territorialPlanningMissionExpenditurePerResident",
 "civilProtectionMissionExpenditurePerResident",
 "economicDevelopmentMissionExpenditurePerResident",
}
MISSION_CODES={
 "educationMissionExpenditurePerResident":("04",),
 "socialMissionExpenditurePerResident":("12",),
 "environmentMissionExpenditurePerResident":("09",),
 "mobilityMissionExpenditurePerResident":("10",),
 "cultureSportMissionExpenditurePerResident":("05","06"),
 "tourismDevelopmentMissionExpenditurePerResident":("07","14"),
 "generalAdministrationMissionExpenditurePerResident":("01",),
 "territorialPlanningMissionExpenditurePerResident":("08",),
 "civilProtectionMissionExpenditurePerResident":("11",),
 "economicDevelopmentMissionExpenditurePerResident":("14",),
}
RESULT_CODES={
 "availableAdministrationResultPerResident":"0502",
 "fcdePerResident":"0491",
 "yearEndCashFundPerResident":"0495",
}
UNITS={
 **{k:"currency" for k in (
  "currentRevenueAccruedPerResident","currentExpenditureCommittedPerResident",
  "capitalExpenditureCommittedPerResident","availableAdministrationResultPerResident",
  "fcdePerResident","yearEndCashFundPerResident",
  *MISSION_CODES.keys(),
 )},
 "ownRevenueShare":"percent",
 "currentCollectionCapacity":"percent",
 "currentPaymentCapacity":"percent",
}

def decode(raw:bytes)->str:
    for enc in ("utf-8-sig","utf-8","cp1252","latin-1"):
        try: return raw.decode(enc)
        except UnicodeDecodeError: pass
    return raw.decode("latin-1",errors="replace")

def num(value):
    text=str(value or "").strip()
    if not text: return None
    if "," in text and "." not in text: text=text.replace(",",".")
    try:
        x=float(text)
        return x if math.isfinite(x) else None
    except ValueError:
        return None

def member_rows(archive:zipfile.ZipFile,suffix:str):
    hits=[x for x in archive.infolist() if x.filename.endswith(suffix)]
    if len(hits)!=1: raise RuntimeError(f"{suffix}: atteso 1 CSV, trovati {len(hits)}")
    reader=csv.DictReader(io.StringIO(decode(archive.read(hits[0]))),delimiter=";")
    return [{k:v for k,v in row.items() if k and k.strip()} for row in reader]

def is_tuscany_municipality(row):
    return (
      str(row.get("Codice Tipologia Soggetto") or "").strip()=="ELCOMU"
      and str(row.get("Codice Regione") or "").strip().zfill(2)=="09"
    )

def code(row):
    prov=str(row.get("Codice Provincia") or "").strip().zfill(3)
    com=str(row.get("Codice Comune") or "").strip().zfill(3)
    return prov+com if prov.strip("0") and com.strip("0") else ""

def unique_by(rows,key_field,value_field=None):
    out=defaultdict(list)
    for row in rows:
        if not is_tuscany_municipality(row): continue
        c=code(row)
        k=str(row.get(key_field) or "").strip()
        if c and k: out[(c,k)].append(row)
    return out

def exact(index,c,k,field):
    hits=index.get((c,k),[])
    if len(hits)!=1: return None,f"rows={len(hits)}"
    value=num(hits[0].get(field))
    if value is None: return None,"non-numeric"
    return value,None

def public_expected():
    baseline=json.loads(BASELINE.read_text(encoding="utf-8"))
    v139=json.loads(V139.read_text(encoding="utf-8"))
    expected={}
    town_codes={town:str(payload["code"]) for town,payload in baseline["raw"].items()}
    for metric_id in BASELINE_METRICS:
        expected[metric_id]={
          town:float(baseline["metrics"][metric_id]["values"][town]["2025"])
          for town in town_codes
        }
    for metric_id in V139_METRICS:
        expected[metric_id]={}
        for town,payload in v139["series"][metric_id]["towns"].items():
            years=list(payload["years"]); values=list(payload["values"])
            idx=years.index(2025)
            expected[metric_id][town]=float(values[idx])
    return expected,town_codes

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",required=True); a=ap.parse_args()
    session=requests.Session()
    session.headers["User-Agent"]="OsservatorioVersilia-A3-OpenBDAP-benchmark/1.0"
    url=BASE+quote(ARCHIVE,safe="/:_-.")
    response=session.get(url,timeout=240); response.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        entrate=member_rows(archive,MEMBERS["entrate"])
        spese=member_rows(archive,MEMBERS["spese"])
        missioni=member_rows(archive,MEMBERS["missioni"])
        risultato=member_rows(archive,MEMBERS["risultato"])

    eidx=unique_by(entrate,"Codice Titolo")
    sidx=unique_by(spese,"Codice Titolo")
    midx=unique_by(missioni,"Codice Missione")
    ridx=unique_by(risultato,"Cod Voce Ris Amm Rend")

    municipality_codes=sorted({
      code(row) for row in entrate if is_tuscany_municipality(row) and code(row)
    })
    if len(municipality_codes)!=EXPECTED_TUSCANY_MUNICIPALITIES:
        raise RuntimeError(
          f"OpenBDAP: Comuni Toscana inattesi {len(municipality_codes)} != {EXPECTED_TUSCANY_MUNICIPALITIES}"
        )

    demo=json.loads(DEMOGRAPHY.read_text(encoding="utf-8"))
    population=float(demo["rcs"]["scopes"]["tuscany"]["population"])
    if int(demo["rcs"]["scopes"]["tuscany"]["municipalityCount"])!=EXPECTED_TUSCANY_MUNICIPALITIES:
        raise RuntimeError("OpenBDAP: denominatore demografico Toscana non allineato")
    expected,town_codes=public_expected()
    reverse={v:k for k,v in town_codes.items()}

    blocked={}
    benchmarks={}
    metric_details={}

    def build(metric_id):
        values={}
        missing=[]
        for c in municipality_codes:
            try:
                if metric_id=="currentRevenueAccruedPerResident":
                    parts=[exact(eidx,c,k,"Accertamenti") for k in ("01","02","03")]
                    if any(err for _,err in parts): raise ValueError(str(parts))
                    values[c]=sum(v for v,_ in parts)
                elif metric_id=="currentExpenditureCommittedPerResident":
                    v,err=exact(sidx,c,"01","Impegni")
                    if err: raise ValueError(err)
                    values[c]=v
                elif metric_id=="capitalExpenditureCommittedPerResident":
                    v,err=exact(sidx,c,"02","Impegni")
                    if err: raise ValueError(err)
                    values[c]=v
                elif metric_id=="ownRevenueShare":
                    p13=[exact(eidx,c,k,"Accertamenti") for k in ("01","03")]
                    p123=[exact(eidx,c,k,"Accertamenti") for k in ("01","02","03")]
                    if any(err for _,err in p13+p123): raise ValueError("title row")
                    values[c]=(sum(v for v,_ in p13),sum(v for v,_ in p123))
                elif metric_id=="currentCollectionCapacity":
                    receipts=[exact(eidx,c,k,"Riscossioni in C/Competenza") for k in ("01","02","03")]
                    accruals=[exact(eidx,c,k,"Accertamenti") for k in ("01","02","03")]
                    if any(err for _,err in receipts+accruals): raise ValueError("title row")
                    values[c]=(sum(v for v,_ in receipts),sum(v for v,_ in accruals))
                elif metric_id=="currentPaymentCapacity":
                    paid,err1=exact(sidx,c,"01","Pagamenti in C/Competenza")
                    committed,err2=exact(sidx,c,"01","Impegni")
                    if err1 or err2: raise ValueError(f"{err1}/{err2}")
                    values[c]=(paid,committed)
                elif metric_id in RESULT_CODES:
                    v,err=exact(ridx,c,RESULT_CODES[metric_id],"Totale di Gestione")
                    if err: raise ValueError(err)
                    values[c]=v
                elif metric_id in MISSION_CODES:
                    parts=[exact(midx,c,k,"Impegni") for k in MISSION_CODES[metric_id]]
                    if any(err for _,err in parts): raise ValueError(str(parts))
                    values[c]=sum(v for v,_ in parts)
                else:
                    raise KeyError(metric_id)
            except Exception as exc:
                missing.append(f"{c}:{exc}")
        if missing:
            blocked[metric_id]={
              "reason":"copertura Toscana incompleta; righe assenti non convertite in zero",
              "missingCount":len(missing),"sample":missing[:20],
            }
            return

        if metric_id in {"ownRevenueShare","currentCollectionCapacity","currentPaymentCapacity"}:
            numerator=sum(v[0] for v in values.values())
            denominator=sum(v[1] for v in values.values())
            regional=numerator/denominator*100.0
        else:
            total=sum(float(v) for v in values.values())
            regional=total/population

        reconcile_errors=[]
        for c,town in reverse.items():
            if c not in values: reconcile_errors.append(f"{town}: source row absent"); continue
            if metric_id in {"ownRevenueShare","currentCollectionCapacity","currentPaymentCapacity"}:
                live=float(values[c][0])/float(values[c][1])*100.0
            else:
                town_pop=float(json.loads(BASELINE.read_text(encoding="utf-8"))["raw"][town]["years"]["2025"]["population_at_1_january"])
                live=float(values[c])/town_pop
            if not math.isclose(live,float(expected[metric_id][town]),rel_tol=0.0,abs_tol=1e-7):
                reconcile_errors.append(f"{town}: {live} != {expected[metric_id][town]}")
        if reconcile_errors:
            blocked[metric_id]={
              "reason":"7/7 public reconciliation FAIL against versioned public source snapshot",
              "errors":reconcile_errors,
            }
            return
        benchmarks[metric_id]={
          "year":"2025","unit":UNITS[metric_id],
          "formula":"aggregazione di numeratori/denominatori OpenBDAP sul perimetro comunale Toscana; nessuna media semplice",
          "tuscany":regional,"italy":None,
        }
        metric_details[metric_id]={
          "municipalities":len(values),"publicReconciliation":"7/7 PASS"
        }

    for metric_id in sorted(BASELINE_METRICS|V139_METRICS):
        build(metric_id)

    payload={
      "schemaVersion":1,
      "publisher":"Ragioneria Generale dello Stato — OpenBDAP",
      "profileId":"openbdap-annual",
      "referenceYear":2025,
      "status":"ACQUIRED_CANDIDATE" if benchmarks else "CANDIDATE_REJECTED",
      "sourceUrl":PORTAL,
      "sourceArchive":response.url,
      "tuscanyMunicipalityCount":len(municipality_codes),
      "populationDenominator":{"value":population,"year":"2025","municipalities":EXPECTED_TUSCANY_MUNICIPALITIES,"source":"Istat RCS/P02 governed snapshot"},
      "benchmarks":benchmarks,
      "qualityGate":{
        "status":"PASS" if benchmarks else "FAIL",
        "candidateMetrics":sorted(benchmarks),
        "metricDetails":metric_details,
        "rule":"ogni metrica è indipendente; copertura 273/273 Toscana e riconciliazione 7/7 obbligatorie",
      },
      "blocked":blocked,
      "notAttempted":{
        "rigidExpenditureShare":"PDI regionale richiede contratto benchmark distinto; non si usa media/mediana comunale come proxy regionale",
        "cashReceiptsPerResident":"fonte SIOPE, non Schemi OpenBDAP",
        "cashBalancePerResident":"fonte SIOPE, non Schemi OpenBDAP",
        "financialDebtProfile":"composito: richiede componenti benchmark distinti",
        "securityMissionExpenditurePerResident":"formula/codice missione da certificare prima del benchmark",
      },
    }
    p=Path(a.output); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
      "status":payload["status"],"candidateMetrics":sorted(benchmarks),
      "candidateCount":len(benchmarks),"blockedCount":len(blocked),
      "tuscanyMunicipalities":len(municipality_codes)
    },ensure_ascii=False))

if __name__=="__main__":
    main()
