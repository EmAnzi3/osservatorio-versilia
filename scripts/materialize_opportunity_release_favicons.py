#!/usr/bin/env python3
"""Materializza i favicon ufficiali già verificati per la release pubblica Radar.

La build di produzione non dipende dalla rete per gli asset grafici. Le fonti
con un'icona già acquisita usano il file locale; una fonte appena entrata nel
Radar può invece usare temporaneamente il marchio tipografico della scheda,
senza bloccare la pubblicazione dei dati e senza inventare un'icona.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "opportunity-source-favicons"
EXPECTED_MIC_SHA256 = "fb5906ca71b08563282e4f48a9ada17a1f481031ada4071e85671499f84775fc"
EXPECTED_MIC_BYTES = 19912


def _public_source_ids(payload: dict[str, Any]) -> set[str]:
    out = {
        str(item.get("source_id") or "")
        for item in payload.get("opportunities") or []
        if item.get("source_id")
    }
    out.update(
        str(item.get("source_id") or "")
        for item in payload.get("archive") or []
        if item.get("source_id")
    )
    return out


def materialize(payload: dict[str, Any], dist: Path) -> dict[str, dict[str, Any]]:
    provenance_path = SOURCE / "provenance.json"
    if not provenance_path.exists():
        raise RuntimeError("Provenienza favicon Radar versionata assente")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if not isinstance(provenance, dict):
        raise RuntimeError("Provenienza favicon Radar non valida")

    public_sources = _public_source_ids(payload)
    missing = sorted(public_sources - set(provenance))

    target = dist / "assets" / "source-favicons"
    target.mkdir(parents=True, exist_ok=True)
    copied: set[str] = set()
    for source_id, meta in provenance.items():
        local = str((meta or {}).get("local") or "")
        name = Path(local).name
        if not name or name == "provenance.json" or Path(name).name != name:
            raise RuntimeError(f"Path favicon non valido per {source_id}: {local!r}")
        source = SOURCE / name
        if not source.is_file() or source.stat().st_size == 0:
            raise RuntimeError(f"Asset favicon mancante o vuoto per {source_id}: {name}")
        expected_bytes = int((meta or {}).get("bytes") or source.stat().st_size)
        if source.stat().st_size != expected_bytes:
            raise RuntimeError(
                f"Dimensione favicon incoerente per {source_id}: {source.stat().st_size}/{expected_bytes}"
            )
        shutil.copyfile(source, target / name)
        copied.add(name)

    mic = target / "mic-dgcc.png"
    if mic.stat().st_size != EXPECTED_MIC_BYTES:
        raise RuntimeError(f"Dimensione mic-dgcc inattesa: {mic.stat().st_size}")
    digest = hashlib.sha256(mic.read_bytes()).hexdigest()
    if digest != EXPECTED_MIC_SHA256:
        raise RuntimeError(f"Hash mic-dgcc inatteso: {digest}")

    (target / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    fallback = f" · fallback tipografico: {', '.join(missing)}" if missing else ""
    print(
        f"Favicon Radar locali: {len(copied)} asset · {len(public_sources) - len(missing)}/{len(public_sources)} "
        f"fonti pubbliche con icona acquisita · mic-dgcc verificato{fallback}."
    )
    return provenance


def apply_to_payload(payload: dict[str, Any], provenance: dict[str, dict[str, Any]]) -> dict[str, Any]:
    for item in payload.get("opportunities") or []:
        sid = str(item.get("source_id") or "")
        if not sid:
            continue
        presentation = item.setdefault("presentation", {})
        meta = provenance.get(sid) or {}
        presentation["source_favicon"] = str(meta.get("local") or "")
    for item in payload.get("archive") or []:
        sid = str(item.get("source_id") or "")
        if not sid:
            continue
        meta = provenance.get(sid) or {}
        item["source_favicon"] = str(meta.get("local") or "")
    return payload
