#!/usr/bin/env python3
"""Shared declarative GitHub Actions architecture for Osservatorio Versilia."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "ci" / "workflow-contract.json"
ALLOWED_CATEGORIES = {"canonical", "automation", "data-audit", "probe", "specialized-gate"}
ALLOWED_STATES = {"active", "quarantined", "retired"}


def load_contract() -> dict[str, Any]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def validate_workflow_contract() -> dict[str, Any]:
    contract = load_contract()
    assert contract.get("schemaVersion") == 1
    entries = contract.get("workflows", [])
    assert isinstance(entries, list) and entries, "Manifest workflow vuoto"

    paths = [entry["path"] for entry in entries]
    duplicates = [path for path, count in Counter(paths).items() if count > 1]
    assert not duplicates, f"Workflow registrati più volte: {duplicates}"
    for entry in entries:
        assert entry.get("category") in ALLOWED_CATEGORIES, f"Categoria workflow invalida: {entry}"
        assert entry.get("status") in ALLOWED_STATES, f"Stato workflow invalido: {entry}"

    declared_present = {
        entry["path"] for entry in entries if entry["status"] in {"active", "quarantined"}
    }
    declared_retired = {entry["path"] for entry in entries if entry["status"] == "retired"}
    actual = {
        path.relative_to(ROOT).as_posix()
        for pattern in ("*.yml", "*.yaml")
        for path in (ROOT / ".github" / "workflows").glob(pattern)
    }
    assert actual == declared_present, (
        f"Inventario workflow fuori contratto; non dichiarati={sorted(actual - declared_present)}, "
        f"mancanti={sorted(declared_present - actual)}"
    )
    assert not (actual & declared_retired), f"Workflow retired ancora presenti: {sorted(actual & declared_retired)}"

    for entry in entries:
        allowed = entry.get("allowedTriggers")
        if allowed is None:
            continue
        assert isinstance(allowed, list) and allowed and all(isinstance(event, str) for event in allowed)
        source = (ROOT / entry["path"]).read_text(encoding="utf-8")
        trigger_block = re.search(r"^on:\n((?:[ \t].*\n|\n)*)", source, re.MULTILINE)
        assert trigger_block, f"Trigger workflow non leggibili: {entry['path']}"
        triggers = set(re.findall(r"^  ([a-z_]+):", trigger_block.group(1), re.MULTILINE))
        assert triggers == set(allowed), (
            f"Trigger workflow fuori contratto: {entry['path']}: {sorted(triggers)} != {sorted(allowed)}"
        )

    canonical = contract["canonical"]
    effective_checks = canonical.get("effectiveCatalogChecks", [])
    assert any(check.get("script") == "scripts/test_a7_static_pilot.py" and check.get("args") == ["--catalog", "dist/data/site-data.json"] for check in effective_checks), (
        "Gate A7 sul catalogo effettivo assente dal Quick canonico"
    )
    required_checks = canonical["requiredPullRequestChecks"]
    assert required_checks == ["quick", "full"], f"Required checks inattesi: {required_checks}"

    pages_path = ROOT / canonical["pagesWorkflow"]
    pages = pages_path.read_text(encoding="utf-8")
    for check in required_checks:
        assert f"\n  {check}:\n" in pages, f"Job canonico assente: {check}"
    for name, command in canonical["commands"].items():
        assert command in pages, f"Comando canonico {name} assente da {pages_path}: {command}"
    quick_job = pages.split("\n  quick:\n", 1)[1].split("\n  full:\n", 1)[0]
    preview_build = canonical["commands"]["previewBuild"]
    preview_ui = canonical["commands"]["previewUI"]
    upload_preview = "name: Upload verified preview"
    assert preview_build in quick_job, "Preview priva della validazione pubblica completa"
    assert preview_ui in quick_job, "Preview priva della UI approvata"
    assert upload_preview in quick_job, "Upload preview canonico assente"
    assert quick_job.index(canonical["commands"]["quick"]) < quick_job.index(preview_ui) < quick_job.index(preview_build) < quick_job.index(upload_preview), (
        "La preview deve essere completata dopo Quick e prima dell'upload"
    )
    assert "needs.build.result == 'success'" in pages, "Deploy non vincolato al successo del build"

    reporter_path = ROOT / canonical["liveStatusWorkflow"]
    reporter = reporter_path.read_text(encoding="utf-8")
    assert canonical["liveStatusContext"] in reporter, "Context live status non dichiarato nel reporter"
    assert '"Radar Opportunità · refresh giornaliero"' in reporter, (
        "Reporter live non osserva la pubblicazione automatica del Radar"
    )
    assert "python scripts/pages_live_status.py" in reporter
    status_script = (ROOT / "scripts/pages_live_status.py").read_text(encoding="utf-8")
    assert '{"deploy", "publish verified Radar"}' in status_script
    for context in (canonical["liveStatusContext"], canonical["publicRoutesContext"], canonical["radarRefreshContext"]):
        assert context in status_script, f"Context non implementato: {context}"
    assert any(check["script"] == "scripts/test_pages_live_status.py" for check in canonical["quickChecks"]), (
        "Matrice dei context indipendenti assente dal Quick canonico"
    )

    by_category = Counter(entry["category"] for entry in entries if entry["status"] == "active")
    return {"workflows": len(actual), "categories": dict(sorted(by_category.items()))}
