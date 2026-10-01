#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-dir",type=Path,required=True)
    ap.add_argument("--dimension",required=True)
    ap.add_argument("--json-output",type=Path,required=True)
    ap.add_argument("--markdown-output",type=Path,required=True)
    args=ap.parse_args()

    rows=[]
    for path in sorted(args.input_dir.rglob("*.json")):
        try:
            value=json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(value,dict) or value.get("profileId") is None:
            continue
        rows.append({
            "profileId":value.get("profileId"),
            "rank":value.get("rank"),
            "pairCount":value.get("pairCount"),
            "metricIds":value.get("metricIds") or [],
            "status":value.get("status"),
            "probeCount":value.get("probeCount"),
            "reachableCount":value.get("reachableCount"),
            "discoveredFileCount":value.get("discoveredFileCount"),
            "discoveredFiles":value.get("discoveredFiles") or [],
            "deepFileCount":value.get("deepFileCount") or 0,
            "deepFiles":value.get("deepFiles") or [],
        })

    rows.sort(key=lambda item:(int(item.get("rank") or 9999),str(item.get("profileId") or "")))
    counts=Counter(str(item.get("status") or "UNKNOWN") for item in rows)
    payload={
        "schemaVersion":1,
        "dimension":args.dimension,
        "profileCount":len(rows),
        "pairCount":sum(int(item.get("pairCount") or 0) for item in rows),
        "statusCounts":dict(sorted(counts.items())),
        "profiles":rows,
    }
    args.json_output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

    lines=[
        f"# A3 parallel source fan-in — {args.dimension}",
        "",
        f"- Profili: **{payload['profileCount']}**",
        f"- Pair coperte dal fan-out: **{payload['pairCount']}**",
        "- Stati: "+", ".join(f"{k}={v}" for k,v in payload["statusCounts"].items()),
        "",
        "| Rank | Profilo | Pair | Stato | URL raggiunti | File candidati | Deep probe |",
        "| ---: | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for item in rows:
        lines.append(
            f"| {item.get('rank')} | {item.get('profileId')} | {item.get('pairCount')} | "
            f"{item.get('status')} | {item.get('reachableCount')}/{item.get('probeCount')} | "
            f"{item.get('discoveredFileCount')} | {item.get('deepFileCount')} |"
        )
    args.markdown_output.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(
        f"A3 fan-in {args.dimension}: {payload['profileCount']} profili · "
        f"{payload['pairCount']} pair · {dict(counts)}"
    )
    return 0


if __name__=="__main__":
    raise SystemExit(main())
