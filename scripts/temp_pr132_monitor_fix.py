#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(value: str, old: str, new: str, label: str) -> str:
    count = value.count(old)
    if count != 1:
        raise SystemExit(f"{label}: attesa 1 occorrenza, trovate {count}")
    return value.replace(old, new, 1)


# 1) ARPAT/SISBON: il cambio di host del portale è un redirect tecnico.
registry_path = ROOT / "data/source-registry.json"
registry = json.loads(registry_path.read_text(encoding="utf-8"))
policies = registry.setdefault("sourceChangePolicies", {})
arpat_url = "https://sira.arpat.toscana.it/apex/f?p=SISBON%3AREPORT_PER_RT%3A%3ACSV%3AIR_REPORT_GEOSCOPIO"
policies[arpat_url] = {
    "redirectChange": "informational",
    "reason": "Endpoint SISBON ARPAT: il passaggio tecnico dal dominio sira.arpat.toscana.it al portale www.arpat.toscana.it/sira non equivale a un nuovo rilascio; periodo e dati restano verificati separatamente.",
}
registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# 2) Regressione specifica: stesso periodo/logical source, nuovo host ARPAT.
test_path = ROOT / "scripts/test_monthly_data_check.py"
value = test_path.read_text(encoding="utf-8")
anchor = '''    assert not arpat_changes["added"]
    assert not arpat_changes["removed"]
    assert not arpat_changes["redirect"]

    istat_url = "https://esploradati.istat.it/"
'''
replacement = '''    assert not arpat_changes["added"]
    assert not arpat_changes["removed"]
    assert not arpat_changes["redirect"]

    arpat_redirect_target = "https://www.arpat.toscana.it/sira/?p=SISBON%3AREPORT_PER_RT%3A%3ACSV%3AIR_REPORT_GEOSCOPIO"
    arpat_redirect = checker.compare_states(
        {"sources": {arpat_canonical: {"ok": True, "finalUrl": arpat_canonical}}},
        {arpat_canonical: {
            "ok": True,
            "finalUrl": arpat_redirect_target,
            "redirectChangePolicy": "informational",
            "redirectChangeReason": "migrazione tecnica portale SISBON",
        }},
    )
    assert not arpat_redirect["redirect"]
    assert arpat_redirect["informationalRedirect"] == [{
        "url": arpat_canonical,
        "before": arpat_canonical,
        "after": checker.canonical_url(arpat_redirect_target),
        "reason": "migrazione tecnica portale SISBON",
    }]

    istat_url = "https://esploradati.istat.it/"
'''
if "migrazione tecnica portale SISBON" not in value:
    value = replace_once(value, anchor, replacement, "test redirect ARPAT")
test_path.write_text(value, encoding="utf-8")


# 3) La PR nata dal falso positivo non deve conservare stato/report del run.
subprocess.run(["git", "fetch", "origin", "main"], cwd=ROOT, check=True)
subprocess.run(
    ["git", "checkout", "origin/main", "--", "data/source-monitor-state.json", "reports/data-checks/2026-08.md"],
    cwd=ROOT,
    check=True,
)

# Il bootstrap è temporaneo e non deve rimanere nel diff finale.
Path(__file__).unlink()
