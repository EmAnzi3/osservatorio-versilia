#!/usr/bin/env python3
"""Materializzatore review Bilanci v1.39 basato sulla fonte OpenBDAP corrente.

La baseline v1.6 resta immutata e continua a descrivere gli archivi usati per
le metriche legacy. Per i sei indicatori nuovi della v1.39 usiamo invece gli
archivi ufficiali OpenBDAP disponibili al momento della build, perché RGS può
rigenerare anche i CSV storici. Ogni download viene validato come ZIP, i due
CSV effettivamente usati vengono hashati e la snapshot v1.39 registra gli SHA
correnti insieme al confronto con la baseline. Nessuna metrica legacy viene
ricalcolata: materialize_bilanci_v139.py contiene una guardia esplicita sulla
serie Turismo + sviluppo (M07+M14).
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

import materialize_bilanci_v139 as impl

ROOT = Path(__file__).resolve().parents[1]
BASELINE_PATH = ROOT / "data/source-snapshots/bilanci-v1.6.0.json"
OUT_PATH = ROOT / "data/source-snapshots/bilanci-v139.json"
BASELINE = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
MISSION_SUFFIX = impl.MISSION_MEMBER
RESULT_SUFFIX = impl.RESULT_MEMBER
CURRENT: dict[str, dict] = {}


def year_from_url(url: str) -> str:
    match = re.search(r"/Rendiconto/(20\d{2})/", url)
    if not match:
        raise RuntimeError(f"Anno non ricavabile da URL OpenBDAP: {url}")
    return match.group(1)


def member_digest(raw: bytes, suffix: str) -> tuple[str, int, str]:
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        hits = [info for info in archive.infolist() if info.filename.endswith(suffix)]
        if len(hits) != 1:
            raise RuntimeError(f"{suffix}: atteso un membro, trovati {len(hits)}")
        payload = archive.read(hits[0])
        return hashlib.sha256(payload).hexdigest(), len(payload), hits[0].filename


def current_download(session: requests.Session, url: str, expected_container_sha: str) -> bytes:
    response = session.get(url, timeout=impl.TIMEOUT)
    response.raise_for_status()
    raw = response.content

    # Verifica strutturale minima: deve essere uno ZIP leggibile con entrambi i
    # prospetti usati dalla v1.39. La validità numerica/7 su 7 è controllata dal
    # materializzatore e dal test dedicato, non viene inferita dagli hash.
    try:
        mission_sha, mission_bytes, mission_name = member_digest(raw, MISSION_SUFFIX)
        result_sha, result_bytes, result_name = member_digest(raw, RESULT_SUFFIX)
    except zipfile.BadZipFile as exc:
        raise RuntimeError(f"OpenBDAP non ha restituito uno ZIP valido: {url}") from exc

    year = year_from_url(url)
    baseline_meta = BASELINE["source"]["years"][year]
    baseline_mission = baseline_meta["selected_files"]["spese_missioni"]["sha256"]
    baseline_result = baseline_meta["selected_files"]["risultato"]["sha256"]
    container_sha = hashlib.sha256(raw).hexdigest()

    CURRENT[year] = {
        "url": response.url,
        "bytes": len(raw),
        "sha256": container_sha,
        "baseline_sha256": expected_container_sha,
        "container_drift": container_sha != expected_container_sha,
        "selected_files": {
            "spese_missioni": {
                "name": mission_name,
                "bytes": mission_bytes,
                "sha256": mission_sha,
                "baseline_sha256": baseline_mission,
                "drift": mission_sha != baseline_mission,
            },
            "risultato": {
                "name": result_name,
                "bytes": result_bytes,
                "sha256": result_sha,
                "baseline_sha256": baseline_result,
                "drift": result_sha != baseline_result,
            },
        },
    }

    status = "drift" if CURRENT[year]["container_drift"] else "stable"
    print(
        f"OpenBDAP {year}: fonte corrente acquisita ({status}); "
        f"missioni={'changed' if mission_sha != baseline_mission else 'same'}, "
        f"risultato={'changed' if result_sha != baseline_result else 'same'}."
    )
    return raw


def patch_snapshot() -> None:
    snapshot = json.loads(OUT_PATH.read_text(encoding="utf-8"))
    snapshot["scope"] = (
        "Sei indicatori Bilanci v1.39.0 materializzati dagli archivi ufficiali "
        "OpenBDAP correnti 2019–2025; la baseline v1.6 resta immutata per le metriche legacy."
    )
    snapshot["generated_at"] = datetime.now(timezone.utc).isoformat()
    snapshot["source"]["archive_policy"] = (
        "Gli SHA v1.6 sono conservati come confronto di provenienza, non come vincolo sui nuovi indicatori: "
        "OpenBDAP può revisionare gli archivi storici. La v1.39 congela gli SHA correnti dei due CSV usati."
    )
    snapshot["source"]["archives"] = {year: CURRENT[year] for year in sorted(CURRENT)}
    snapshot["policy"]["legacy_recalculation"] = (
        "vietata: gli indicatori già pubblicati non vengono ricalcolati dagli archivi correnti"
    )
    OUT_PATH.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


impl.download_verified = current_download

if __name__ == "__main__":
    impl.main()
    patch_snapshot()
