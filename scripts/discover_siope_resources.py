#!/usr/bin/env python3
"""Materialize the verified official CKAN identifiers for SIOPE histories."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "source-snapshots" / "siope-resource-discovery.json"
DUMP_BASE = "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/datastore/dump"

# Exact package/resource identifiers previously resolved through the official
# BDAP CKAN catalogue by exact dataset title. The 2018 resources are excluded:
# the published historical series intentionally starts from 2019.
VERIFIED_DATASETS = {
    "entrata-2019-toscana": ("7deb457c-3207-481f-bed0-ffd45be4ff59", "2019 - Toscana - SIOPE Movimenti cumulati mensili di Entrata"),
    "spesa-2019-toscana": ("3a937353-ee1f-43a7-86be-1c753adec130", "2019 - Toscana - SIOPE Movimenti cumulati mensili di Spesa"),
    "entrata-2020-toscana": ("5cb68fcb-af2b-41f6-8fbc-f7da82a4581c", "2020 - Toscana - SIOPE Movimenti cumulati mensili di Entrata"),
    "spesa-2020-toscana": ("805c62a2-8aad-47e9-a830-188aca557f96", "2020 - Toscana - SIOPE Movimenti cumulati mensili di Spesa"),
    "entrata-2021-toscana": ("74f98a70-7d92-434b-843d-1cf4844447ae", "2021 - Toscana - SIOPE Movimenti cumulati mensili di Entrata"),
    "spesa-2021-toscana": ("1a083d8b-39e5-41be-b1d1-32808f3c6ace", "2021 - Toscana - SIOPE Movimenti cumulati mensili di Spesa"),
    "entrata-2022-toscana": ("0a571dea-2e80-4200-9939-d193d167e4a5", "2022 - Toscana - SIOPE Movimenti cumulati mensili di Entrata"),
    "spesa-2022-toscana": ("c50b15ff-996b-4410-ba43-19f374c515ce", "2022 - Toscana - SIOPE Movimenti cumulati mensili di Spesa"),
    "entrata-2023-toscana": ("413d73f7-a7e6-4ee1-a94b-dbe1a1d612a6", "2023 - Toscana - SIOPE Movimenti cumulati mensili di Entrata"),
    "spesa-2023-toscana": ("21c5bf70-8495-47e8-8419-310f7b776f0e", "2023 - Toscana - SIOPE Movimenti cumulati mensili di Spesa"),
    "entrata-2024-toscana": ("c5788656-d6a4-4e50-bf2b-1e4f7887d4aa", "2024 - Toscana - SIOPE Movimenti cumulati mensili di Entrata"),
    "spesa-2024-toscana": ("5604bf94-08db-40ec-a5f9-403687f4576a", "2024 - Toscana - SIOPE Movimenti cumulati mensili di Spesa"),
    "entrata-2025-toscana": ("4dbef43d-72fa-4fe2-a716-45986be658f2", "2025 - Toscana - SIOPE Movimenti cumulati mensili di Entrata"),
    "spesa-2025-toscana": ("74533d22-b1c2-4d89-b1b9-b98e6c9713ff", "2025 - Toscana - SIOPE Movimenti cumulati mensili di Spesa"),
}


def package(identifier: str, title: str) -> dict:
    return {
        "id": identifier,
        "name": identifier,
        "title": title,
        "url": f"https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/dataset/{identifier}",
        "resources": [
            {
                "id": identifier,
                "name": f"{title} — CSV",
                "format": "CSV",
                "mimetype": "text/csv",
                "resource_type": "file",
                "url": f"{DUMP_BASE}/{identifier}.csv",
            }
        ],
    }


def main() -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalogue": "BDAP Open Data — API CKAN v3",
        "api": "https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3",
        "coverage": "2019-2025",
        "manifest_method": "Identificativi risolti per titolo ufficiale esatto e congelati per riproducibilità.",
        "datasets": {
            label: package(identifier, title)
            for label, (identifier, title) in VERIFIED_DATASETS.items()
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Manifesto ufficiale SIOPE 2019-2025 materializzato in {OUT}")

    # Temporary read-only diagnostics. It runs only when the generated builder
    # is present and does not write data or alter validation outcomes.
    diagnostic = ROOT / "scripts" / "diagnose_siope_2019.py"
    builder = ROOT / "scripts" / "build_siope_history.py"
    if diagnostic.exists() and builder.exists():
        try:
            import diagnose_siope_2019
            diagnose_siope_2019.main()
        except Exception as exc:
            print(f"DIAGNOSTICA SIOPE 2019 CONCLUSA CON ESITO: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
