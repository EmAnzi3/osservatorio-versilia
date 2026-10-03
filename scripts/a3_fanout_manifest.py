#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--backlog",type=Path,required=True)
    ap.add_argument("--dimension",required=True)
    ap.add_argument("--max-profiles",type=int,default=12)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--matrix-output",type=Path,required=True)
    args=ap.parse_args()

    backlog=load(args.backlog)
    bundles=backlog.get("bundles")
    if not isinstance(bundles,list):
        raise RuntimeError("Backlog A3 senza bundles")

    selected=[]
    seen=set()
    for bundle in bundles:
        if not isinstance(bundle,dict) or bundle.get("dimension")!=args.dimension:
            continue
        profile=str(bundle.get("profileId") or "").strip()
        if not profile or profile in seen:
            continue
        selected.append({
            "profileId":profile,
            "bundleId":str(bundle.get("bundleId") or ""),
            "rank":int(bundle.get("rank") or 0),
            "pairCount":int(bundle.get("pairCount") or 0),
            "metricIds":list(bundle.get("metricIds") or []),
            "sourceReferences":list(bundle.get("sourceReferences") or []),
            "publisher":str(bundle.get("publisher") or ""),
            "costPoints":int(bundle.get("costPoints") or 0),
            "priorityIndex":float(bundle.get("priorityIndex") or 0.0),
        })
        seen.add(profile)
        if len(selected)>=args.max_profiles:
            break

    if not selected:
        raise RuntimeError(f"Nessun bundle selezionato per {args.dimension}")

    payload={
        "schemaVersion":1,
        "dimension":args.dimension,
        "selectedProfileCount":len(selected),
        "selectedPairCount":sum(item["pairCount"] for item in selected),
        "profiles":selected,
    }
    matrix={"include":[
        {
            "profileId":item["profileId"],
            "rank":item["rank"],
            "pairCount":item["pairCount"],
        }
        for item in selected
    ]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    args.matrix_output.write_text(json.dumps(matrix,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    print(
        f"A3 fan-out {args.dimension}: {len(selected)} profili · "
        f"{payload['selectedPairCount']} coppie candidate."
    )
    for item in selected:
        print(
            f"A3_FANOUT #{item['rank']} {item['profileId']} :: "
            f"{item['pairCount']} pair :: priority={item['priorityIndex']}"
        )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
