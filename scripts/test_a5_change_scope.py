#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args=parser.parse_args()

    cfg=json.loads(Path(args.config).read_text(encoding="utf-8"))
    checkpoint=cfg["checkpoint"]
    allowed=set(cfg["allowed_paths"])

    git("cat-file","-e",f"{checkpoint}^{{commit}}")
    target="HEAD"
    base=None
    if os.environ.get("GITHUB_EVENT_NAME","") == "pull_request":
        parents=git("rev-list","--parents","-n","1","HEAD").split()
        if len(parents) >= 3:
            base=parents[1]
            target=parents[2]

    changed=set(filter(None,git("diff","--name-only",f"{checkpoint}..{target}").splitlines()))
    upstream_only=set()
    if base:
        # Keep the approval checkpoint as the temporal boundary, but ignore a
        # post-checkpoint path only when the PR head is byte-identical to the
        # current base branch for that path. This admits merged upstream work
        # without widening the A5 allowlist or hiding branch-owned changes.
        for path in changed:
            same_as_base=subprocess.run(
                ["git","diff","--quiet",base,target,"--",path],
                check=False,
            ).returncode == 0
            if same_as_base:
                upstream_only.add(path)
        changed -= upstream_only
        baseline_label=(
            f"Checkpoint: {checkpoint} · target: {target} · base: {base} · "
            f"upstream-only ignored: {len(upstream_only)}"
        )
    else:
        baseline_label=f"Checkpoint: {checkpoint} · target: {target}"

    unexpected=sorted(changed-allowed)
    missing_policy=sorted(path for path in changed if path not in allowed)

    print(baseline_label)
    print(f"Scopo: {cfg.get('purpose','')}")
    print("File cambiati:")
    for path in sorted(changed):
        print(f"  - {path}")

    if unexpected or missing_policy:
        print("ERRORE: il batch ha modificato file fuori dallo scope dichiarato:")
        for path in sorted(set(unexpected+missing_policy)):
            print(f"  - {path}")
        raise SystemExit(1)

    print(f"Scope lock OK: {len(changed)} file, tutti autorizzati dal batch.")


if __name__ == "__main__":
    main()
