#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

DEDICATED={
    "istat-business-annual":"scripts/acquire_a3_benchmark_istat_business_asia_ul.py",
    "mim-school-year":"scripts/acquire_a3_benchmark_mim_candidates.py",
    "mef-irpef-annual":"scripts/acquire_a3_benchmark_mef_residual_candidates.py",
    "istat-geografia-comunale-2021":"scripts/acquire_a3_benchmark_geography_candidates.py",
    "istat-agriculture-census-2020":"scripts/acquire_a3_benchmark_agriculture_candidates.py",
    "siope-monthly":"scripts/acquire_a3_benchmark_siope_candidates.py",
    "regione-toscana-indicatori-comunali":"scripts/acquire_a3_benchmark_toscana_indicators.py",
    "istat-demography-annual":"scripts/acquire_a3_benchmark_demography_candidates.py",
    "istat-census-annual":"scripts/acquire_a3_benchmark_census_candidates.py",
}


def load(path:Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run(cmd:list[str])->subprocess.CompletedProcess[str]:
    return subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)


def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--registry",type=Path,required=True)
    ap.add_argument("--profile",required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()

    manifest=load(args.manifest)
    entry=next((x for x in manifest.get("profiles",[]) if x.get("profileId")==args.profile),None)
    if not entry:
        raise RuntimeError(f"Profilo {args.profile} assente dal manifest")

    args.output.parent.mkdir(parents=True,exist_ok=True)
    raw_output=args.output.with_suffix(".raw.json")

    dynamic_script="scripts/acquire_a3_benchmark_"+re.sub(r"[^a-z0-9]+","_",args.profile.lower()).strip("_")+".py"
    script=DEDICATED.get(args.profile)
    if args.profile == "mef-irpef-annual" and entry.get("metricIds") == ["income"]:
        script = "scripts/acquire_a3_benchmark_mef_taxable_income_annual.py"
    if args.profile == "istat-business-annual" and entry.get("metricIds") == ["microUnits"]:
        script = "scripts/acquire_a3_benchmark_istat_business_micro_units.py"
    if script is None and (ROOT/dynamic_script).exists():
        script=dynamic_script

    if script is not None:
        cmd=[sys.executable,script,"--output",str(raw_output)]
        if args.profile=="istat-census-annual":
            metric_ids=entry.get("metricIds") or []
            if metric_ids:
                cmd.extend(["--metrics", ",".join(str(x) for x in metric_ids)])
        proc=run(cmd)
        if proc.returncode!=0:
            payload={
                "schemaVersion":1,
                "profileId":args.profile,
                "pairCount":entry.get("pairCount"),
                "mode":"dedicated",
                "script":script,
                "status":"DEDICATED_ACQUISITION_FAILED",
                "returnCode":proc.returncode,
                "stdout":proc.stdout[-12000:],
                "stderr":proc.stderr[-12000:],
            }
        else:
            value=load(raw_output)
            payload={
                "schemaVersion":1,
                "profileId":args.profile,
                "pairCount":entry.get("pairCount"),
                "mode":"dedicated",
                "script":script,
                "status":value.get("status") or "DEDICATED_ACQUIRED",
                "result":value,
                "stdout":proc.stdout[-12000:],
            }
    elif args.profile=="openbdap-annual":
        audit=args.output.with_name("openbdap-source-audit.json")
        proc=run([sys.executable,"scripts/probe_bilanci_v139_sources.py","--output",str(audit)])
        value=load(audit) if audit.exists() else {}
        payload={
            "schemaVersion":1,
            "profileId":args.profile,
            "pairCount":entry.get("pairCount"),
            "mode":"source-audit",
            "script":"scripts/probe_bilanci_v139_sources.py",
            "status":"SOURCE_AUDIT_PASS" if value.get("hard_gate")=="PASS" else "SOURCE_AUDIT_BLOCKED",
            "result":value,
            "returnCode":proc.returncode,
            "stdout":proc.stdout[-12000:],
            "stderr":proc.stderr[-12000:],
        }
    else:
        proc=run([
            sys.executable,"scripts/probe_a3_fanout_source.py",
            "--manifest",str(args.manifest),
            "--registry",str(args.registry),
            "--profile",args.profile,
            "--deep-files","12",
            "--output",str(raw_output),
        ])
        value=load(raw_output) if raw_output.exists() else {}
        payload={
            "schemaVersion":1,
            "profileId":args.profile,
            "pairCount":entry.get("pairCount"),
            "mode":"deep-discovery",
            "script":"scripts/probe_a3_fanout_source.py",
            "status":value.get("status") or ("DISCOVERY_FAILED" if proc.returncode else "DISCOVERY_COMPLETE"),
            "result":value,
            "returnCode":proc.returncode,
            "stdout":proc.stdout[-12000:],
            "stderr":proc.stderr[-12000:],
        }

    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "profile":args.profile,
        "pairCount":entry.get("pairCount"),
        "mode":payload["mode"],
        "status":payload["status"],
        "output":str(args.output),
    },ensure_ascii=False))

    # Source/data problems are evidence, not CI infrastructure failures.
    # The worker fails only if it could not produce its evidence artifact.
    if not args.output.exists():
        raise SystemExit(2)


if __name__=="__main__":
    main()
