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

RESIDUAL_LABELS = {
    "Salute finanziaria browser",
}


def run_check(label: str, command, failures: list[tuple[str, int]]) -> None:
    print(f"\n===== RESIDUAL: {label} =====", flush=True)
    print("    " + " ".join(str(part) for part in command), flush=True)
    result = subprocess.run(list(command), cwd=ROOT, check=False)
    if result.returncode:
        failures.append((label, result.returncode))
        print(f"===== RESIDUAL FAILED: {label} (exit {result.returncode}) =====", flush=True)
    else:
        print(f"===== RESIDUAL PASSED: {label} =====", flush=True)


def main() -> None:
    failures: list[tuple[str, int]] = []
    (ROOT / "reports/mobilita-v119-browser").mkdir(parents=True, exist_ok=True)

    port = preflight.free_port()
    base = f"http://127.0.0.1:{port}/"
    with tempfile.TemporaryDirectory(prefix="ov-a5-residual-") as temporary:
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
                commands = [(label, command) for label, command in preflight.browser_commands(base) if label in RESIDUAL_LABELS]
                missing = RESIDUAL_LABELS - {label for label, _ in commands}
                if missing:
                    raise RuntimeError(f"Residual labels mancanti: {sorted(missing)}")
                for label, command in commands:
                    run_check(label, command, failures)

                if not failures:
                    print("\n===== A4: validate existing baseline =====", flush=True)
                    validate = (
                        preflight.PYTHON,
                        "scripts/test_visual_regression.py",
                        "--base",
                        base,
                    )
                    run_check("A4 visual regression validate", validate, failures)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)

    print("\n========== A5 RESIDUAL SUMMARY ==========", flush=True)
    if failures:
        for label, code in failures:
            print(f"FAIL  {label}  (exit {code})", flush=True)
        print(f"TOTAL RESIDUAL FAILURES: {len(failures)}", flush=True)
        raise SystemExit(1)

    print("ALL RESIDUAL CHECKS + A4 VALIDATION PASSED", flush=True)


if __name__ == "__main__":
    main()
