#!/usr/bin/env python3
"""Shared declarative GitHub Actions architecture for Osservatorio Versilia."""
from __future__ import annotations

import json
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

    canonical = contract["canonical"]
    required_checks = canonical["requiredPullRequestChecks"]
    assert required_checks == ["quick", "full"], f"Required checks inattesi: {required_checks}"

    pages_path = ROOT / canonical["pagesWorkflow"]
    pages = pages_path.read_text(encoding="utf-8")
    for check in required_checks:
        assert f"\n  {check}:\n" in pages, f"Job canonico assente: {check}"
    for name, command in canonical["commands"].items():
        assert command in pages, f"Comando canonico {name} assente da {pages_path}: {command}"
    assert "needs.build.result == 'success'" in pages, "Deploy non vincolato al successo del build"

    reporter_path = ROOT / canonical["liveStatusWorkflow"]
    reporter = reporter_path.read_text(encoding="utf-8")
    assert canonical["liveStatusContext"] in reporter, "Context live status non dichiarato nel reporter"
    assert 'job.get("name") == "deploy"' in reporter, "Reporter non verifica il vero job deploy"
    assert 'job.get("conclusion") == "success"' in reporter, "Reporter non verifica il successo del deploy"

    by_category = Counter(entry["category"] for entry in entries if entry["status"] == "active")
    return {"workflows": len(actual), "categories": dict(sorted(by_category.items()))}
