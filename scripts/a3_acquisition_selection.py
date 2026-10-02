#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from a3_bulk_acquisition_worker import DEDICATED

def load(p:Path):
    v=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(v,dict): raise RuntimeError(f"JSON non-oggetto: {p}")
    return v

def dynamic_path(profile:str)->str:
    slug=re.sub(r"[^a-z0-9]+","_",profile.lower()).strip("_")
    return f"scripts/acquire_a3_benchmark_{slug}.py"

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--changed-files",type=Path)
    ap.add_argument("--mode",choices=("auto","full"),default="auto")
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--matrix-output",type=Path,required=True)
    a=ap.parse_args()
    manifest=load(a.manifest)
    profiles=list(manifest.get("profiles") or [])
    if not profiles: raise RuntimeError("Manifest vuoto")
    selected=profiles
    reason="full-fanout" if a.mode=="full" else "auto-full-fanout"
    # A3 closure is intentionally source-profile parallel: a PR synchronization must
    # not collapse the matrix to the single acquisition script that changed. That
    # serializes source -> CI -> source and defeats the bulk fan-out/fan-in design.
    # Keep all manifest profiles independent and let blocked/mismatch workers report
    # evidence without preventing the remaining workers from progressing.
    if False and a.mode=="auto" and a.changed_files and a.changed_files.exists():
        changed={line.strip() for line in a.changed_files.read_text(encoding="utf-8").splitlines() if line.strip()}
        structural={
          ".github/workflows/a3-benchmark-bulk-acquisition.yml",
          "scripts/a3_bulk_acquisition_worker.py",
          "scripts/a3_acquisition_selection.py",
          "scripts/probe_a3_fanout_source.py",
          "scripts/probe_bilanci_v139_sources.py",
          "data/source-snapshots/a3-benchmark-fanout-current.json",
        }
        if not (changed & structural):
            inverse={path:profile for profile,path in DEDICATED.items()}
            for item in profiles:
                inverse.setdefault(dynamic_path(str(item.get("profileId") or "")),str(item.get("profileId") or ""))
            wanted={inverse[path] for path in changed if path in inverse and inverse[path]}
            if wanted:
                selected=[p for p in profiles if p.get("profileId") in wanted]
                reason="changed-dedicated-profiles"
    payload={**manifest,"selectedProfileCount":len(selected),"selectedPairCount":sum(int(x.get("pairCount") or 0) for x in selected),"profiles":selected,"selectionReason":reason}
    matrix={"include":[{"profileId":x["profileId"],"rank":int(x.get("rank") or 0),"pairCount":int(x.get("pairCount") or 0)} for x in selected]}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    a.matrix_output.write_text(json.dumps(matrix,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    print(f"A3 acquisition selection: {len(selected)}/{len(profiles)} profili · {payload['selectedPairCount']} coppie · {reason}")
    for x in selected: print(f"A3_SELECTED {x['profileId']} :: {x.get('pairCount')}")

if __name__=="__main__": main()
