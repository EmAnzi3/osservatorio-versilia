#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import preflight  # noqa: E402


def run_check(label: str, command, failures: list[tuple[str, int]]) -> None:
    print(f"\n===== SWEEP: {label} =====", flush=True)
    print("    " + " ".join(str(part) for part in command), flush=True)
    result = subprocess.run(list(command), cwd=ROOT, check=False)
    if result.returncode:
        failures.append((label, result.returncode))
        print(f"===== SWEEP FAILED: {label} (exit {result.returncode}) =====", flush=True)
    else:
        print(f"===== SWEEP PASSED: {label} =====", flush=True)


def main() -> None:
    failures: list[tuple[str, int]] = []
    (ROOT / "reports/mobilita-v119-browser").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports/erp-arrears-v125-browser").mkdir(parents=True, exist_ok=True)

    port = preflight.free_port()
    base = f"http://127.0.0.1:{port}/"
    with tempfile.TemporaryDirectory(prefix="ov-a5-sweep-") as temporary:
        temp_dir = Path(temporary)
        log_path = temp_dir / "preview.log"
        with log_path.open("wb") as log:
            process = subprocess.Popen(
                (preflight.PYTHON, "scripts/preview_dist.py", "--port", str(port), "--directory", "dist"),
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                preflight.wait_for_server(base, process, log_path)
                for label, command in preflight.browser_commands(base):
                    run_check(f"browser: {label}", command, failures)
                try:
                    preflight.validate_monthly_state(temp_dir)
                    print("\n===== SWEEP PASSED: monthly state =====", flush=True)
                except Exception as exc:
                    failures.append(("monthly state", 1))
                    print(f"\n===== SWEEP FAILED: monthly state =====\n{exc}", flush=True)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)

    for label, script, *args in preflight.STATIC_FULL_TESTS:
        run_check(
            f"static: {label}",
            (preflight.PYTHON, script, *args),
            failures,
        )

    print("\n\n========== A5 FULL SWEEP SUMMARY ==========", flush=True)
    if failures:
        for label, code in failures:
            print(f"FAIL  {label}  (exit {code})", flush=True)
        print(f"TOTAL FAILURES: {len(failures)}", flush=True)
        raise SystemExit(1)

    print("ALL BROWSER + MONTHLY + STATIC FULL CHECKS PASSED", flush=True)


if __name__ == "__main__":
    main()
