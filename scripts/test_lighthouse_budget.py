#!/usr/bin/env python3
"""Esegue Lighthouse su pagine rappresentative e applica soglie minime stabili."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

LIGHTHOUSE_VERSION = "12.8.2"
PAGES = (
    ("home", ""),
    ("tema-demografia", "confronta/demografia/?indicatore=population"),
    ("comune-massarosa", "comuni/massarosa/?tema=demografia&indicatore=population"),
    ("stato-dati", "stato-dati/"),
)
THRESHOLDS = {
    "performance": 0.70,
    "accessibility": 0.90,
    "best-practices": 0.90,
    "seo": 0.90,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def chromium_path() -> str:
    with sync_playwright() as playwright:
        path = playwright.chromium.executable_path
    require(Path(path).exists(), f"Chromium Playwright non trovato: {path}")
    return path


def run_lighthouse(base: str, output_dir: Path) -> list[Path]:
    npm = shutil.which("npm")
    require(npm is not None, "npm non disponibile: impossibile eseguire Lighthouse")
    output_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["CHROME_PATH"] = chromium_path()
    reports: list[Path] = []

    for name, route in PAGES:
        report = output_dir / f"{name}.json"
        command = [
            npm,
            "exec",
            "--yes",
            f"--package=lighthouse@{LIGHTHOUSE_VERSION}",
            "--",
            "lighthouse",
            urljoin(base, route),
            "--quiet",
            "--preset=desktop",
            "--throttling-method=provided",
            "--only-categories=performance,accessibility,best-practices,seo",
            "--output=json",
            f"--output-path={report}",
            "--chrome-flags=--headless --no-sandbox --disable-dev-shm-usage",
        ]
        completed = subprocess.run(
            command,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=120,
            check=False,
        )
        require(
            completed.returncode == 0 and report.exists(),
            f"Lighthouse fallito su {route or '/'} (exit {completed.returncode}):\n{completed.stdout[-4000:]}",
        )
        reports.append(report)

    return reports


def validate_reports(reports: list[Path], output_dir: Path) -> None:
    failures: list[str] = []
    summary: dict[str, dict[str, int]] = {}

    for path in reports:
        payload = json.loads(path.read_text(encoding="utf-8"))
        categories = payload.get("categories", {})
        scores: dict[str, int] = {}
        for category, threshold in THRESHOLDS.items():
            raw = categories.get(category, {}).get("score")
            if raw is None:
                failures.append(f"{path.stem}: categoria {category} assente")
                continue
            score = float(raw)
            scores[category] = round(score * 100)
            if score + 1e-9 < threshold:
                failures.append(
                    f"{path.stem}: {category} {scores[category]} < {round(threshold * 100)}"
                )
        summary[path.stem] = scores

    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if failures:
        raise AssertionError("Lighthouse budget fallito:\n- " + "\n- ".join(failures))
    print("Lighthouse budget passed: performance >= 70, accessibility/best-practices/SEO >= 90.")


def run_budget(base: str, output_dir: Path) -> None:
    reports = run_lighthouse(base.rstrip("/") + "/", output_dir)
    validate_reports(reports, output_dir)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--output-dir", default="reports/lighthouse")
    args = parser.parse_args()
    run_budget(args.base, Path(args.output_dir).resolve())
