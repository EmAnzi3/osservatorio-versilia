#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    daily = (ROOT / ".github/workflows/opportunity-radar-daily.yml").read_text(encoding="utf-8")
    pages = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    live_status = (ROOT / ".github/workflows/pages-live-status.yml").read_text(encoding="utf-8")

    assert "gh pr create" not in daily
    assert "gh workflow run pages.yml" not in daily
    assert "Persist verified snapshot as runtime state" in daily
    assert "actions/upload-pages-artifact@v3" in daily
    assert "actions/deploy-pages@v4" in daily
    assert "Notify owner after successful publication" in daily
    assert "Notify owner about blocked publication" in daily
    assert daily.index("Deploy verified Radar") < daily.index("Notify owner after successful publication")
    publish_section = daily.split("  publish:", 1)[1]
    report_download = publish_section.split("- name: Download readable run report", 1)[1].split(
        "- name: Notify owner after successful publication", 1
    )[0]
    report_notification = publish_section.split(
        "- name: Notify owner after successful publication", 1
    )[1].split("- name: Close legacy daily snapshot pull request", 1)[0]
    assert "if:" not in report_download
    assert "if:" not in report_notification
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

    print("Workflow automatico Radar: scan -> gate -> deploy -> notifica PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
