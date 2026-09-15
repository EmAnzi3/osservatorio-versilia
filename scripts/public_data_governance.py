#!/usr/bin/env python3
"""General post-build governance gate for the effective public release."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from public_build_snapshot import (
    DIST,
    effective_public_catalog,
    validate_public_governance,
    validate_public_snapshot,
)
from public_data_lineage import validate_lineage, write_lineage
from public_readme_status import release_summary, validate_readme

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON non-oggetto: {path}")
    return value


def align_status_metadata() -> None:
    catalog = effective_public_catalog()
    path = DIST / "data" / "data-status.json"
    status = _load(path)
    status["catalogVersion"] = str(catalog.get("version") or "")
    status["catalogUpdated"] = str(catalog.get("updated") or "")
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_release_surfaces() -> dict[str, Any]:
    catalog = effective_public_catalog()
    summary = release_summary()
    status = _load(DIST / "data" / "data-status.json")
    if status.get("catalogVersion") != summary["version"]:
        raise RuntimeError("Versione catalogo assente/non allineata nello Stato dati")
    if status.get("catalogUpdated") != summary["updated"]:
        raise RuntimeError("Data catalogo assente/non allineata nello Stato dati")
    if status.get("metricCount") != summary["total"]:
        raise RuntimeError("Conteggio Stato dati non allineato alla release")

    homepage = (DIST / "index.html").read_text(encoding="utf-8")
    required_home = (
        f"{summary['towns']} comuni",
        f"{summary['themes']} temi",
        f"{summary['total']} indicatori",
        summary["version"],
        summary["updated"],
    )
    missing = [value for value in required_home if value not in homepage]
    if missing:
        raise RuntimeError(f"Homepage non allineata alla release: mancano {missing}")

    status_page = (DIST / "stato-dati" / "index.html").read_text(encoding="utf-8")
    if f"Dettaglio dei {summary['total']} indicatori" not in status_page:
        raise RuntimeError("Pagina Stato dati non allineata al conteggio pubblico")

    if str(catalog.get("version") or "") != summary["version"] or str(catalog.get("updated") or "") != summary["updated"]:
        raise RuntimeError("Riepilogo release non derivato dal catalogo pubblico")
    return summary


def finalize_public_data_governance() -> dict[str, Any]:
    validate_public_snapshot()
    align_status_metadata()
    governance = validate_public_governance()
    lineage = write_lineage()
    validate_lineage()
    summary = validate_readme()
    surfaces = validate_release_surfaces()
    if summary != surfaces:
        raise RuntimeError("Riepilogo README e superfici pubbliche divergenti")
    print(
        "Governance catalogo pubblico verificata: "
        f"{governance['public_metrics']} ID pubblicati = "
        f"{governance['status_metrics']} ID Stato dati = "
        f"{governance['source_policies']} policy fonte."
    )
    print(
        f"Lineage pubblica derivata: {lineage['metricCount']} indicatori · "
        f"{len(lineage['materializationChain'])} passaggi dichiarati."
    )
    print(
        f"Superfici release riconciliate: {summary['version']} · {summary['total']} indicatori · "
        f"{summary['updated']} · governance "
        f"{governance['public_metrics']}/{governance['status_metrics']}/{governance['source_policies']}."
    )
    print("PUBLIC DATA GOVERNANCE: GREEN")
    return {"summary": summary, "governance": governance, "lineage": lineage}


if __name__ == "__main__":
    finalize_public_data_governance()
