#!/usr/bin/env python3
"""Esegue Lighthouse su pagine rappresentative e applica soglie minime stabili."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

LIGHTHOUSE_VERSION = "13.4.1"
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
TRANSIENT_LIGHTHOUSE_ERRORS = (
    "Waiting for DevTools protocol response has exceeded the allotted time",
    "Network.getResponseBody",
    "TargetClosedError",
    "Target page, context or browser has been closed",
    "ECONNRESET",
    "Connection reset by peer",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def chromium_paths() -> list[str]:
    """Restituisce browser Chromium/Chrome utilizzabili, privilegiando Chrome di sistema."""
    candidates: list[str] = []

    explicit = os.environ.get("LIGHTHOUSE_CHROME_PATH")
    if explicit:
        candidates.append(explicit)

    for executable in (
        "google-chrome-stable",
        "google-chrome",
        "chromium",
        "chromium-browser",
    ):
        resolved = shutil.which(executable)
        if resolved:
            candidates.append(resolved)

    with sync_playwright() as playwright:
        candidates.append(playwright.chromium.executable_path)

    unique: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = str(Path(candidate).resolve())
        except OSError:
            resolved = candidate
        if resolved in seen or not Path(resolved).exists():
            continue
        seen.add(resolved)
        unique.append(resolved)

    require(unique, "Nessun Chrome/Chromium disponibile per Lighthouse")
    return unique


def lighthouse_launcher(npm: str) -> list[str]:
    """Usa la versione Lighthouse dichiarata, senza dipendere da un globale obsoleto."""
    lighthouse = shutil.which("lighthouse")
    if lighthouse:
        probe = subprocess.run(
            [lighthouse, "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=30,
        )
        if probe.returncode == 0 and probe.stdout.strip() == LIGHTHOUSE_VERSION:
            return [lighthouse]
    return [
        npm,
        "exec",
        "--yes",
        f"--package=lighthouse@{LIGHTHOUSE_VERSION}",
        "--",
        "lighthouse",
    ]


def _is_transient_lighthouse_failure(output: str) -> bool:
    return any(marker in output for marker in TRANSIENT_LIGHTHOUSE_ERRORS)


def run_lighthouse(base: str, output_dir: Path) -> list[Path]:
    npm = shutil.which("npm")
    require(npm is not None, "npm non disponibile: impossibile eseguire Lighthouse")
    launcher = lighthouse_launcher(npm)
    timeout = int(os.environ.get("LIGHTHOUSE_TIMEOUT_SECONDS", "300"))
    max_attempts = max(1, int(os.environ.get("LIGHTHOUSE_MAX_ATTEMPTS", "3")))
    retry_delay = max(0.0, float(os.environ.get("LIGHTHOUSE_RETRY_DELAY_SECONDS", "2")))
    output_dir.mkdir(parents=True, exist_ok=True)

    browsers = chromium_paths()
    base_env = os.environ.copy()
    reports: list[Path] = []

    for name, route in PAGES:
        report = output_dir / f"{name}.json"
        command = [
            *launcher,
            urljoin(base, route),
            "--quiet",
            "--preset=desktop",
            "--throttling-method=provided",
            "--only-categories=performance,accessibility,best-practices,seo",
            "--disable-storage-reset",
            "--output=json",
            f"--output-path={report}",
            "--chrome-flags=--headless=new --no-sandbox --disable-dev-shm-usage --disable-background-networking",
        ]

        last_exit: int | str = "n/a"
        last_output = ""
        succeeded = False
        attempts_used = 0
        for attempt in range(1, max_attempts + 1):
            attempts_used = attempt
            report.unlink(missing_ok=True)
            browser = browsers[(attempt - 1) % len(browsers)]
            env = base_env.copy()
            env["CHROME_PATH"] = browser
            try:
                completed = subprocess.run(
                    command,
                    env=env,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,
                    check=False,
                )
                last_exit = completed.returncode
                last_output = completed.stdout or ""
                if completed.returncode == 0 and report.exists():
                    succeeded = True
                    break
                transient = _is_transient_lighthouse_failure(last_output)
            except subprocess.TimeoutExpired as exc:
                last_exit = "timeout"
                payload = exc.stdout or ""
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8", errors="replace")
                last_output = str(payload)
                transient = True

            if not transient or attempt >= max_attempts:
                break
            next_browser = browsers[attempt % len(browsers)]
            print(
                f"Lighthouse transient failure su {route or '/'} con {Path(browser).name}: "
                f"tentativo {attempt}/{max_attempts}; prossimo browser {Path(next_browser).name} tra {retry_delay:g}s."
            )
            if retry_delay:
                time.sleep(retry_delay)

        require(
            succeeded,
            f"Lighthouse fallito su {route or '/'} dopo {attempts_used} tentativo/i "
            f"(exit {last_exit}):\n{last_output[-4000:]}",
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
