#!/usr/bin/env python3
"""Wrapper fail-closed per la materializzazione Bilanci v1.39.

Lo ZIP OpenBDAP può essere rigenerato senza modificare i CSV utili. Se lo SHA
del contenitore differisce dalla baseline v1.6, accetta il download soltanto
quando gli SHA dei due membri usati dalla v1.39 (missioni e Allegato A) restano
identici a quelli versionati. In caso contrario interrompe la preview.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

import requests

import materialize_bilanci_v139 as impl

ROOT = Path(__file__).resolve().parents[1]
BASELINE = json.loads((ROOT / "data/source-snapshots/bilanci-v1.6.0.json").read_text(encoding="utf-8"))
MISSION_SUFFIX = impl.MISSION_MEMBER
RESULT_SUFFIX = impl.RESULT_MEMBER


def digest_member(raw: bytes, suffix: str) -> str:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        hits = [info for info in archive.infolist() if info.filename.endswith(suffix)]
        if len(hits) != 1:
            raise RuntimeError(f"{suffix}: atteso un membro, trovati {len(hits)}")
        return hashlib.sha256(archive.read(hits[0])).hexdigest()


def year_from_url(url: str) -> str:
    match = re.search(r"/Rendiconto/(20\d{2})/", url)
    if not match:
        raise RuntimeError(f"Anno non ricavabile da URL OpenBDAP: {url}")
    return match.group(1)


def verified_download(session: requests.Session, url: str, expected_container_sha: str) -> bytes:
    response = session.get(url, timeout=impl.TIMEOUT)
    response.raise_for_status()
    raw = response.content
    current_container = hashlib.sha256(raw).hexdigest()
    if current_container == expected_container_sha:
        return raw

    year = year_from_url(url)
    meta = BASELINE["source"]["years"][year]
    current_mission = digest_member(raw, MISSION_SUFFIX)
    current_result = digest_member(raw, RESULT_SUFFIX)
    expected_mission = meta["selected_files"]["spese_missioni"]["sha256"]
    expected_result = meta["selected_files"]["risultato"]["sha256"]

    if current_mission != expected_mission or current_result != expected_result:
        raise RuntimeError(
            "OpenBDAP historical target drift "
            f"{year}: container {current_container} != {expected_container_sha}; "
            f"missioni {current_mission} != {expected_mission}; "
            f"risultato {current_result} != {expected_result}"
        )

    print(
        f"OpenBDAP {year}: ZIP rigenerato, ma i due CSV target coincidono con la baseline; "
        "materializzazione consentita."
    )
    return raw


impl.download_verified = verified_download

if __name__ == "__main__":
    impl.main()
