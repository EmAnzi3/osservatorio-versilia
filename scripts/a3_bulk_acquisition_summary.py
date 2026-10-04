#!/usr/bin/env python3
from __future__ import annotations

import argparse,json
from collections import Counter
from pathlib import Path


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-dir",type=Path,required=True)
    ap.add_argument("--json-output",type=Path,required=True)
    ap.add_argument("--markdown-output",type=Path,required=True)
    a=ap.parse_args()

    rows=[]
    for p in sorted(a.input_dir.rglob("*.json")):
        if p.name.endswith(".raw.json"):
            continue
        try:o=json.loads(p.read_text(encoding="utf-8"))
        except:continue
        if not isinstance(o,dict) or not o.get("profileId"):continue
        result=o.get("result") if isinstance(o.get("result"),dict) else {}
        rows.append({
            "profileId":o.get("profileId"),
            "pairCount":int(o.get("pairCount") or 0),
            "mode":str(o.get("mode") or "unknown"),
            "status":str(o.get("status") or "UNKNOWN"),
            "candidateKeys":sorted((result.get("benchmarks") or {}).keys()) if isinstance(result.get("benchmarks"),dict) else [],
            "candidateScopes":sorted((result.get("candidates") or {}).keys()) if isinstance(result.get("candidates"),dict) else [],
            "discoveredFiles":int(result.get("discoveredFileCount") or 0),
            "deepFiles":int(result.get("deepFileCount") or 0),
            "hardGate":result.get("hard_gate"),
        })

    rows.sort(key=lambda x:(-x["pairCount"],x["profileId"]))
    payload={
        "schemaVersion":1,
        "profileCount":len(rows),
        "pairCount":sum(x["pairCount"] for x in rows),
        "statusCounts":dict(Counter(x["status"] for x in rows)),
        "modeCounts":dict(Counter(x["mode"] for x in rows)),
        "profiles":rows,
    }
    a.json_output.parent.mkdir(parents=True,exist_ok=True)
    a.json_output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=[
        "# A3 benchmark bulk acquisition",
        "",
        f"- Profili: **{payload['profileCount']}**",
        f"- Pair coperte: **{payload['pairCount']}**",
        f"- Modalità: {', '.join(f'{k}={v}' for k,v in sorted(payload['modeCounts'].items()))}",
        "",
        "| Profilo | Pair | Modalità | Stato | Candidate | Deep files |",
        "| --- | ---: | --- | --- | --- | ---: |",
    ]
    for x in rows:
        cand=", ".join(x["candidateKeys"] or x["candidateScopes"])
        if x["hardGate"]: cand=(cand+"; " if cand else "")+f"hardGate={x['hardGate']}"
        lines.append(f"| {x['profileId']} | {x['pairCount']} | {x['mode']} | {x['status']} | {cand} | {x['deepFiles']} |")
    a.markdown_output.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"A3 bulk acquisition: {payload['profileCount']} profili · {payload['pairCount']} pair · {payload['statusCounts']}")


if __name__=="__main__":
    main()
