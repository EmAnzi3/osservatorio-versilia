#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from collections import Counter

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-dir",type=Path,required=True)
    ap.add_argument("--json-output",type=Path,required=True)
    ap.add_argument("--markdown-output",type=Path,required=True)
    a=ap.parse_args()
    rows=[]
    for p in sorted(a.input_dir.rglob("*.json")):
        try:o=json.loads(p.read_text(encoding="utf-8"))
        except: continue
        if not isinstance(o,dict) or not o.get("profileId"): continue
        candidates=o.get("candidates") or {}
        rows.append({
          "profileId":o.get("profileId"),"status":o.get("status"),
          "candidateScopes":sorted(candidates.keys()) if isinstance(candidates,dict) else [],
          "candidateMetricKeys":sorted({
             k for scope in candidates.values() if isinstance(scope,dict)
             for k in scope.keys()
          }) if isinstance(candidates,dict) else [],
          "sourceFiles":len(o.get("sources") or {}) if isinstance(o.get("sources"),dict) else 0,
        })
    counts=Counter(r["status"] for r in rows)
    payload={"schemaVersion":1,"profileCount":len(rows),"statusCounts":dict(counts),"profiles":rows}
    a.json_output.parent.mkdir(parents=True,exist_ok=True)
    a.json_output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# A3 benchmark candidate acquisition","","| Profilo | Stato | Scope | Candidate keys |","| --- | --- | --- | --- |"]
    for r in rows:
        lines.append(f"| {r['profileId']} | {r['status']} | {', '.join(r['candidateScopes'])} | {', '.join(r['candidateMetricKeys'])} |")
    a.markdown_output.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"A3 benchmark candidate fan-in: {len(rows)} profili · {dict(counts)}")
if __name__=="__main__": main()
