#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from opportunity_run_report import incomplete_run_stages


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/opportunity-radar-daily-v2-shadow.yml"


def _failure_matrix() -> None:
    stages = ("scan", "validation", "build", "report", "comparison")
    green = {stage: "success" for stage in stages}
    assert incomplete_run_stages(green) == {}
    for failed_stage in stages:
        statuses = dict(green)
        statuses[failed_stage] = "failure"
        assert incomplete_run_stages(statuses) == {failed_stage: "failure"}
    skipped = dict(green)
    skipped["validation"] = "skipped"
    skipped["build"] = "skipped"
    assert set(incomplete_run_stages(skipped)) == {"validation", "build"}


def main() -> int:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "  schedule:" not in workflow
    assert "  pull_request:" not in workflow
    assert "opportunity_seed_source_health.sh" in workflow
    assert "OPPORTUNITY_DISCOVERY_POLICY: verified-opportunities-v1" in workflow
    assert "contents: read" in workflow
    for forbidden in (
        "contents: write",
        "pages: write",
        "issues: write",
        "actions/deploy-pages",
        "actions/upload-pages-artifact",
        "git push",
        "gh issue create",
    ):
        assert forbidden not in workflow, forbidden

    required = (
        "Seed from latest verified production snapshot",
        "Scan live sources in shadow mode",
        "Validate shadow candidate",
        "Build and smoke-test shadow candidate",
        "Generate shadow run report",
        "Compare shadow candidate with production state",
        "Upload complete shadow evidence",
        "Enforce complete shadow run",
        "python -m playwright install --with-deps chromium",
        "scripts/opportunity_shadow_compare.py",
        "failure_stage:",
        'exit 97',
    )
    for marker in required:
        assert marker in workflow, marker

    assert workflow.index("Generate shadow run report") < workflow.index("Upload complete shadow evidence")
    assert workflow.index("Compare shadow candidate with production state") < workflow.index("Upload complete shadow evidence")
    assert workflow.index("Upload complete shadow evidence") < workflow.index("Enforce complete shadow run")

    assert "timeout-minutes: 60" in workflow
    assert "id: scan\n        timeout-minutes: 30" in workflow
    assert "id: build\n        timeout-minutes: 20" in workflow
    comparison = workflow.split("      - name: Compare shadow candidate with production state", 1)[1].split("      - name: Build and smoke-test shadow candidate", 1)[0]
    assert "steps.validation.outcome == 'success'" in comparison
    assert "steps.build.outcome" not in comparison
    assert workflow.index("Compare shadow candidate with production state") < workflow.index("Build and smoke-test shadow candidate")

    _failure_matrix()
    print("Workflow Radar v2 shadow e failure matrix: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
