#!/usr/bin/env python3
"""Exercise deployment/refresh/route combinations without network or status writes."""
import subprocess
from types import SimpleNamespace
from unittest.mock import patch

from pages_live_status import RADAR_WORKFLOW, check_routes, status_payloads


def main() -> int:
    run = {"name": RADAR_WORKFLOW, "conclusion": "cancelled", "html_url": "https://github.com/example/run"}
    jobs = [{"name": "refresh", "conclusion": "cancelled"},
            {"name": "publish verified Radar", "conclusion": "skipped"}]
    def statuses(ok: bool) -> dict:
        return {item["context"]: item for item in status_payloads(run, jobs, ok)}

    for routes in (True, False):
        result = statuses(routes)
        assert "ov-pages-live" not in result
        assert result["ov-radar-refresh"]["state"] == "failure"
        assert result["ov-public-routes"]["state"] == ("success" if routes else "failure")
    run["conclusion"] = "success"
    jobs[0]["conclusion"] = "success"
    assert statuses(True)["ov-radar-refresh"]["state"] == "success"
    assert "ov-pages-live" not in statuses(True)  # successful dry-run
    jobs[1]["conclusion"] = "success"
    assert statuses(True)["ov-pages-live"]["state"] == "success"
    assert statuses(False)["ov-pages-live"]["state"] == "failure"
    assert statuses(False)["ov-radar-refresh"]["state"] == "success"
    jobs[1]["conclusion"] = "failure"
    run["conclusion"] = "failure"
    assert statuses(True)["ov-pages-live"]["state"] == "failure"
    assert statuses(True)["ov-radar-refresh"]["state"] == "failure"
    run["conclusion"] = "success"
    jobs.pop()
    assert statuses(True)["ov-radar-refresh"]["state"] == "failure"  # missing publisher is uncertain
    run["name"] = "Deploy GitHub Pages"
    jobs[:] = [{"name": "deploy", "conclusion": "success"}]
    assert set(statuses(True)) == {"ov-public-routes", "ov-pages-live"}
    jobs[0]["conclusion"] = "skipped"
    assert set(statuses(False)) == {"ov-public-routes"}
    jobs.clear()
    assert set(statuses(True)) == {"ov-public-routes"}
    with patch("pages_live_status.subprocess.run", side_effect=[SimpleNamespace(returncode=1), SimpleNamespace(returncode=0)]) as probe, patch("pages_live_status.time.sleep"):
        assert check_routes("https://example.test/")
        assert probe.call_count == 2
    with patch("pages_live_status.subprocess.run", side_effect=subprocess.TimeoutExpired("validator", 300)) as probe, patch("pages_live_status.time.sleep"):
        assert not check_routes("https://example.test/")
        assert probe.call_count == 3
    print("Publication/refresh/routes: independent statuses and skipped-deploy preservation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
