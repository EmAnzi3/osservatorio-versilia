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


def main() -> None:
    port = preflight.free_port()
    base = f"http://127.0.0.1:{port}/"
    with tempfile.TemporaryDirectory(prefix="ov-a4-final-") as temporary:
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
                result = subprocess.run(
                    (preflight.PYTHON, "scripts/test_visual_regression.py", "--base", base),
                    cwd=ROOT,
                    check=False,
                )
                raise SystemExit(result.returncode)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)


if __name__ == "__main__":
    main()
