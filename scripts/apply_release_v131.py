#!/usr/bin/env python3
"""Apply the reviewed v1.3.1 source payload before build and deployment."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHUNKS = ROOT / "data" / "releases" / "v1.3.1"
EXPECTED_SHA256 = "da54c66d139914e389f595371d442b5a9aab65f60da5693455540d5d0dd45ec9"
EXPECTED_VERSION = "2026.08.05-v1.3.1"
ALLOWED_PREFIXES = (
    "data/site-data.json",
    "assets/app-parts/",
    "assets/static.css",
    "assets/fidelity.css",
    "assets/fidelity.js",
)


def safe_member(name: str) -> bool:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        return False
    return any(name == prefix or name.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def main() -> None:
    files = sorted(CHUNKS.glob("*.b64"))
    if not files:
        raise RuntimeError("Payload v1.3.1 assente")
    encoded = "".join(path.read_text(encoding="ascii").strip() for path in files)
    archive = base64.b64decode(encoded, validate=True)
    digest = hashlib.sha256(archive).hexdigest()
    if digest != EXPECTED_SHA256:
        raise RuntimeError(f"Hash payload inatteso: {digest}")

    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        members = tar.getmembers()
        invalid = [member.name for member in members if not safe_member(member.name)]
        if invalid:
            raise RuntimeError(f"Percorsi non consentiti nel payload: {invalid}")
        tar.extractall(ROOT, members=members, filter="data")

    data = json.loads((ROOT / "data" / "site-data.json").read_text(encoding="utf-8"))
    if data.get("version") != EXPECTED_VERSION:
        raise RuntimeError(f"Versione dati inattesa: {data.get('version')}")
    if len(data.get("metrics", {})) != 69:
        raise RuntimeError("Il payload non contiene i 69 indicatori approvati")
    print(f"Payload {EXPECTED_VERSION} applicato e verificato.")


if __name__ == "__main__":
    main()
