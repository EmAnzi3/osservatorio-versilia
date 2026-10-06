#!/usr/bin/env python3
"""Report publication, Radar execution and public-route integrity independently."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

DEPLOY_JOBS = {"deploy", "publish verified Radar"}
RADAR_WORKFLOW = "Radar Opportunità · refresh giornaliero"


def status_payloads(run: dict, jobs: list[dict], routes_ok: bool) -> list[dict]:
    """A skipped publication must not overwrite the last deployment's status."""
    url = run["html_url"]

    def payload(context: str, ok: bool, description: str) -> dict:
        return {"context": context, "state": "success" if ok else "failure",
                "description": description[:140], "target_url": url}

    result = [payload("ov-public-routes", routes_ok,
                      "Route pubbliche verificate" if routes_ok else
                      "Route pubbliche non verificate dopo tentativi limitati; vedere log")]
    deploy = next((job for job in jobs if job.get("name") in DEPLOY_JOBS), None)
    conclusion = deploy.get("conclusion") if deploy else "missing"
    if conclusion == "success":
        result.append(payload("ov-pages-live", routes_ok,
                              "Pages pubblicato; route pubbliche verificate" if routes_ok else
                              "Deploy riuscito; una o più route pubbliche non verificate"))
    elif conclusion not in {"skipped", "missing"}:
        result.append(payload("ov-pages-live", False, f"Tentativo di pubblicazione: {conclusion}"))

    if run.get("name") == RADAR_WORKFLOW:
        ok = run.get("conclusion") == "success" and conclusion in {"success", "skipped"} and all(
            job.get("conclusion") in {"success", "skipped"} for job in jobs
        ) and any(job.get("name") == "refresh" and job.get("conclusion") == "success" for job in jobs)
        description = "Radar verificato; pubblicazione riuscita" if ok and conclusion == "success" else (
            "Radar verificato; nessuna pubblicazione richiesta" if ok else
            f"Refresh Radar {run.get('conclusion')}; nuova pubblicazione non confermata"
        )
        result.append(payload("ov-radar-refresh", ok, description))
    return result


def check_routes(base_url: str, attempts: int = 3) -> bool:
    validator = Path(__file__).with_name("validate_public_site.py")
    for attempt in range(1, attempts + 1):
        print(f"Verifica route {attempt}/{attempts}: {base_url}", flush=True)
        try:
            check = subprocess.run([sys.executable, str(validator), "--base-url", base_url],
                                   check=False, timeout=300)
            if check.returncode == 0:
                return True
        except subprocess.TimeoutExpired:
            print("Verifica route: budget di 300 secondi esaurito", flush=True)
        if attempt < attempts:
            time.sleep(2)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--jobs", type=Path, required=True)
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()
    run = json.loads(args.run.read_text(encoding="utf-8"))
    jobs = json.loads(args.jobs.read_text(encoding="utf-8")).get("jobs", [])
    if run.get("head_branch") != "main" or run.get("status") != "completed":
        raise ValueError("Reporter richiede un run completato su main")
    statuses = status_payloads(run, jobs, check_routes(args.base_url))
    repo = os.environ["GITHUB_REPOSITORY"]
    sha = run["head_sha"]
    for status in statuses:
        subprocess.run(["gh", "api", "--method", "POST",
                        f"repos/{repo}/statuses/{sha}", "--input", "-"],
                       input=json.dumps(status), text=True, stdout=subprocess.DEVNULL, check=True)
        print(f"{status['context']}: {status['state']} — {status['description']}", flush=True)
    if not any(status["context"] == "ov-pages-live" for status in statuses):
        print("Nessun deploy tentato: stato precedente ov-pages-live conservato", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
