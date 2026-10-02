#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import audit_agcom_primary as ag

ROOT = Path(__file__).resolve().parents[1]
PARSER_SCHEMA_VERSION = 3
SITE = ROOT / "data" / "site-data.json"
TUSCANY_PREFIXES = {"045","046","047","048","049","050","051","052","053","100"}
PERCENT_METRICS = {
    "ftthCoverageDesi": "copertura_ftth_desi_pct",
    "ftthCoverage20m": "copertura_ftth_20m_pct",
}
ABS_METRICS = {
    "ftthReachedHouseholds": "famiglie_ftth",
    "ftthUnreachedHouseholds": "famiglie_ftth",
}

def finite(v: Any, label: str) -> float:
    if isinstance(v, bool) or not isinstance(v, (int,float)):
        raise RuntimeError(f"{label}: numerico atteso")
    x=float(v)
    if not math.isfinite(x):
        raise RuntimeError(f"{label}: non finito")
    return x

def weighted(rows: list[dict[str,Any]], pct_key: str) -> float:
    num=0.0; den=0.0
    for r in rows:
        households=r.get("famiglie_residenti")
        pct=r.get(pct_key)
        if not isinstance(households,int) or households <= 0:
            raise RuntimeError(f"AGCOM: famiglie residenti invalide per {r.get('comune')}")
        if not isinstance(pct,(int,float)) or isinstance(pct,bool) or not 0 <= float(pct) <= 100:
            raise RuntimeError(f"AGCOM: percentuale {pct_key} invalida per {r.get('comune')}")
        num += households * float(pct)
        den += households
    if den <= 0:
        raise RuntimeError("AGCOM: denominatore famiglie nullo")
    return num/den

def public_reconcile(site: dict[str,Any], primary: dict[str,dict[str,Any]]) -> list[str]:
    errors=[]
    for metric_id,source_key in PERCENT_METRICS.items():
        metric=(site.get("metrics") or {}).get(metric_id) or {}
        rows=metric.get("rows") or []
        if len(rows)!=7:
            errors.append(f"{metric_id}: righe pubbliche {len(rows)} != 7")
            continue
        for row in rows:
            code=str(row.get("code") or "")
            src=primary.get(code)
            if src is None:
                errors.append(f"{metric_id}/{code}: riga AGCOM assente")
                continue
            expected=src.get(source_key)
            observed=row.get("value")
            if expected is None or observed is None or not math.isclose(float(observed),float(expected),rel_tol=0.0,abs_tol=1e-9):
                errors.append(f"{metric_id}/{code}: {observed} != {expected}")
    return errors

def scope_rows(primary: dict[str,dict[str,Any]], tuscany: bool) -> list[dict[str,Any]]:
    out=[]
    for code,row in primary.items():
        if not (len(code)==6 and code.isdigit()):
            continue
        if tuscany and code[:3] not in TUSCANY_PREFIXES:
            continue
        out.append(row)
    return out

def abs_diagnostics(rows: list[dict[str,Any]]) -> dict[str,Any]:
    missing_reached=[]
    missing_within20=[]
    total_households=0
    reached=0
    within20=0
    for r in rows:
        h=r.get("famiglie_residenti")
        if not isinstance(h,int) or h<=0:
            continue
        total_households += h
        f=r.get("famiglie_ftth")
        f20=r.get("famiglie_ftth_20m")
        if f is None:
            missing_reached.append(r.get("comune"))
        else:
            reached += int(f)
        if f20 is None:
            missing_within20.append(r.get("comune"))
        else:
            within20 += int(f20)
    return {
        "residentHouseholds":total_households,
        "knownFtthHouseholds":reached,
        "knownFtthHouseholdsWithin20m":within20,
        "missingFtthHouseholdCells":len(missing_reached),
        "missingFtth20mCells":len(missing_within20),
        "sampleMissingReached":missing_reached[:20],
        "sampleMissing20m":missing_within20[:20],
    }

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()

    site=json.loads(SITE.read_text(encoding="utf-8"))
    required={str(t.get("code")) for t in site.get("towns",[]) if t.get("code")}
    primary,url,discovery=ag.acquire_primary_rows(required)

    italy=scope_rows(primary,False)
    tuscany=scope_rows(primary,True)
    if not (7800 <= len(italy) <= 8000):
        raise RuntimeError(f"AGCOM: copertura Italia inattesa {len(italy)}")
    if not (270 <= len(tuscany) <= 280):
        raise RuntimeError(f"AGCOM: copertura Toscana inattesa {len(tuscany)}")

    errors=public_reconcile(site,primary)
    benchmarks={}
    for metric_id,key in PERCENT_METRICS.items():
        benchmarks[metric_id]={
            "year":"31 dicembre 2025",
            "unit":"percent",
            "formula":"media delle percentuali comunali AGCOM ponderata per famiglie residenti",
            "tuscany":weighted(tuscany,key),
            "italy":weighted(italy,key),
        }

    abs_diag={"tuscany":abs_diagnostics(tuscany),"italy":abs_diagnostics(italy)}
    abs_publishable=all(
        diag["missingFtthHouseholdCells"]==0 and diag["missingFtth20mCells"]==0
        for diag in abs_diag.values()
    )
    if abs_publishable:
        for scope_name,rows in (("tuscany",tuscany),("italy",italy)):
            pass
        tus=abs_diag["tuscany"]; ita=abs_diag["italy"]
        benchmarks["ftthReachedHouseholds"]={
            "year":"31 dicembre 2025","unit":"number",
            "formula":"somma famiglie FTTH ufficiali",
            "tuscany":tus["knownFtthHouseholds"],"italy":ita["knownFtthHouseholds"],
        }
        benchmarks["ftthUnreachedHouseholds"]={
            "year":"31 dicembre 2025","unit":"number",
            "formula":"somma famiglie residenti - somma famiglie FTTH, solo con conteggi ufficiali completi",
            "tuscany":tus["residentHouseholds"]-tus["knownFtthHouseholds"],
            "italy":ita["residentHouseholds"]-ita["knownFtthHouseholds"],
        }

    status="ACQUIRED_CANDIDATE" if not errors else "CANDIDATE_REJECTED"
    payload={
        "schemaVersion":1,
        "publisher":"AGCOM — Broadband Map, reportistica comunale",
        "profileId":"agcom-quarterly",
        "referenceDate":"31/12/2025",
        "status":status,
        "source":{"url":url,"discovery":discovery,"rowCount":len(primary),"parserSchemaVersion":PARSER_SCHEMA_VERSION},
        "benchmarks":benchmarks,
        "qualityGate":{
            "status":"PASS" if not errors else "FAIL",
            "municipalityCountItaly":len(italy),
            "municipalityCountTuscany":len(tuscany),
            "publicPercentageReconciliation":"2 metrics × 7/7 PASS" if not errors else "FAIL",
            "errors":errors,
        },
        "absoluteCounts":{
            "status":"PASS" if abs_publishable else "BLOCKED_MISSING_OFFICIAL_CELLS",
            "diagnostics":abs_diag,
            "note":"Nessun conteggio assoluto viene ricostruito dalle percentuali. Le due metriche assolute sono candidate solo se tutte le celle ufficiali sono presenti in entrambi gli scope."
        }
    }
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":status,
        "candidateMetrics":sorted(benchmarks),
        "italyRows":len(italy),
        "tuscanyRows":len(tuscany),
        "absoluteCounts":payload["absoluteCounts"]["status"],
        "output":str(out)
    },ensure_ascii=False))

if __name__=="__main__":
    main()
