#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[1]


def check_execution_budget(path: str, scan_id: str, build_id: str) -> None:
    contract = json.loads((ROOT / "ci/workflow-contract.json").read_text(encoding="utf-8"))
    entry = next(item for item in contract["workflows"] if item["path"] == path)
    budget = entry["executionBudgetMinutes"]
    assert all(type(value) is int and value > 0 for value in budget.values())
    assert budget["job"] >= budget["scan"] + budget["build"] + budget["overhead"], (
        "Il job deve lasciare tempo a setup, report ed evidenze anche dopo scan/build completi"
    )
    source = (ROOT / path).read_text(encoding="utf-8")
    job_timeout = re.search(r"^    timeout-minutes: (\d+)$", source, re.MULTILINE)
    assert job_timeout and int(job_timeout.group(1)) == budget["job"]
    for stage, step_id in (("scan", scan_id), ("build", build_id)):
        timeout = re.search(rf"id: {re.escape(step_id)}\n        timeout-minutes: (\d+)", source)
        assert timeout and int(timeout.group(1)) == budget[stage], (path, stage)


def main() -> int:
    daily = (ROOT / ".github/workflows/opportunity-radar-daily.yml").read_text(encoding="utf-8")
    pages = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    live_status = (ROOT / ".github/workflows/pages-live-status.yml").read_text(encoding="utf-8")
    quality_gate = (ROOT / ".github/workflows/opportunity-radar-v044-ci.yml").read_text(encoding="utf-8")

    assert "OPPORTUNITY_DISCOVERY_POLICY: verified-opportunities-v1" in daily
    dry_run_scan = quality_gate.split(
        "- name: Run current live discovery through production entrypoint", 1
    )[1].split("\n      - name:", 1)[0]
    assert "OPPORTUNITY_DISCOVERY_POLICY: verified-opportunities-v1" in dry_run_scan, (
        "Il dry-run produttivo deve usare la stessa politica discovery del primario"
    )
    assert "opportunity_seed_source_health.sh" in daily
    assert "scripts/opportunity_shadow_compare.py" in daily
    assert "'comparison': os.environ.get('COMPARISON_STATUS')" in daily
    assert "python scripts/build_public_site.py" in daily
    assert "python scripts/test_site_consistency.py" in daily
    assert "python scripts/test_opportunity_release_browser.py" in daily
    assert "gh pr create" not in daily
    assert "gh workflow run pages.yml" not in daily
    assert "Persist verified snapshot as runtime state" in daily
    assert "actions/upload-pages-artifact@v3" in daily
    assert "actions/deploy-pages@v4" in daily
    assert "Notify owner after successful publication" in daily
    assert "Notify owner about blocked publication" in daily
    assert daily.count("python scripts/opportunity_owner_notification.py") == 2
    assert daily.index("Checkout notification helper") < daily.index("Deploy verified Radar")
    assert daily.index("Deploy verified Radar") < daily.index("Notify owner after successful publication")
    publish_section = daily.split("  publish:", 1)[1]
    report_download = publish_section.split("- name: Download readable run report", 1)[1].split(
        "- name: Notify owner after successful publication", 1
    )[0]
    report_notification = publish_section.split(
        "- name: Notify owner after successful publication", 1
    )[1].split("- name: Close legacy daily snapshot pull request", 1)[0]
    assert "if:" not in report_download
    assert "if: needs.refresh.outputs.owner_notification_needed == 'true'" in report_notification
    assert "publication_requires_notification(report)" in daily
    assert (
        'marker="radar-published:${{ needs.refresh.outputs.reference_date }}:'
        '${{ needs.refresh.outputs.fingerprint }}"'
    ) in daily
    assert 'gh pr list --repo "$GITHUB_REPOSITORY"' in daily
    assert 'gh pr close "$PR_NUMBER" --repo "$GITHUB_REPOSITORY"' in daily
    assert "la pubblicazione Radar resta valida" in daily

    assert "Select latest verified Radar runtime snapshot" in pages
    assert "scripts/opportunity_runtime_snapshot.py" in pages
    assert "Radar Opportunità · refresh giornaliero" in live_status
    assert "publish verified Radar" in live_status

    assert "github.event.pull_request.number || 'production'" in daily
    check_execution_budget(".github/workflows/opportunity-radar-daily.yml", "live_scan", "validate_build")
    from test_pages_live_status import main as test_statuses
    test_statuses()

    print("Workflow automatico Radar: scan -> gate -> deploy -> notifica PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
