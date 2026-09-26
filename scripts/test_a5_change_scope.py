#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
    changed=set(filter(None,git("diff","--name-only",f"{checkpoint}..HEAD").splitlines()))
    unexpected=sorted(changed-allowed)
    missing_policy=sorted(path for path in changed if path not in allowed)

    print(f"Checkpoint: {checkpoint}")
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
