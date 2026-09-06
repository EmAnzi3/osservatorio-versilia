#!/usr/bin/env python3
"""Local/CI preflight for Osservatorio Versilia.

Usage:
  python scripts/preflight.py --quick
  python scripts/preflight.py --full

Quick is the mandatory pre-push gate: source contract, canonical data checks,
build, special-page materialization and static site-wide consistency.
Full adds the browser and long-running regression suite. CI may pass
--skip-quick to Full only after the Quick job has succeeded and its dist/
artifact has been restored.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PYTHON = sys.executable

JSON_CONTRACTS = (
    "data/site-data.json",
    "data/source-registry.json",
    "data/source-monitor-state.json",
    "data/source-snapshots/istat-demography-lotto-a-2026-08.json",
    "data/source-snapshots/istat-rcs-demography-2025.json",
    "data/source-snapshots/mef-income-lotto-a-2024.json",
    "data/source-snapshots/fiscal-lotto-b-2025.json",
    "data/source-snapshots/rgs-amministrazione-2024.json",
    "data/source-snapshots/rgs-formazione-2024.json",
    "data/source-snapshots/istat-lavoro-istruzione-eta-genere-2024.json",
    "data/source-snapshots/mobilita-tpl-2026-08-26.json",
    "data/source-snapshots/istat-agricoltura-territorio-2020.json",
    "data/source-snapshots/costa-mare-v123.json",
    "data/source-snapshots/attivita-estrattive-v128.json",
    "data/source-snapshots/erp-lucca-arrears-2020-2024.json",
)

CANONICAL_TESTS = (
    ("finalize catalog", "scripts/finalize_catalog_release.py", "--check"),
    ("catalog release", "scripts/test_catalog_release_v116.py"),
    ("costi/fiscalita/redditi", "scripts/test_costi_fiscalita_redditi_draft.py"),
    ("demography materialized", "scripts/test_demography_lotto_a_materialized.py"),
    ("demography v5", "scripts/test_demography_lotto_a_v5.py"),
    ("demography RCS", "scripts/test_demography_rcs_lotto_a.py"),
    ("income", "scripts/test_income_lotto_a_v2.py"),
    ("fiscal", "scripts/test_fiscal_lotto_b.py"),
    ("PNRR draft", "scripts/test_pnrr_toscana_draft.py"),
    ("PNRR review", "scripts/test_pnrr_toscana_review.py"),
    ("amministrazione", "scripts/test_amministrazione_lotto_a.py"),
    ("lavoro/istruzione", "scripts/test_lavoro_istruzione_eta_genere.py"),
    ("mobilita TPL", "scripts/test_mobilita_tpl_v119.py"),
    ("agricoltura", "scripts/test_agricoltura_territorio_v120.py"),
    ("cultura", "scripts/test_cultura_biblioteche_v121.py"),
    ("costa e mare", "scripts/test_costa_mare_v123.py"),
    ("attivita estrattive", "scripts/test_attivita_estrattive_v128.py"),
    ("ambiente/acqua", "scripts/test_ambiente_acqua_v124_ui.py"),
    ("ERP", "scripts/test_erp_arrears_v125.py"),
    ("investimenti", "scripts/test_investimenti_versilia.py"),
)

COMPILE_MANIFEST = "scripts/preflight_compile.txt"

STATIC_FULL_TESTS = (
    ("data status", "scripts/test_data_status.py"),
    ("static regression", "scripts/test_static.py"),
    ("launch foundations", "scripts/test_launch_foundations.py"),
    ("indicator pages and SEO", "scripts/test_indicator_pages.py"),
    ("composite indicators", "scripts/test_composite_indicators.py"),
    ("brand identity", "scripts/test_brand_identity.py"),
    ("PWA", "scripts/test_pwa.py"),
    ("visual grammar", "scripts/test_visual_grammar.py"),
    ("release compatibility", "scripts/test_release_v170_compat.py"),
    ("history compatibility", "scripts/test_history_v180.py"),
    ("source links", "scripts/test_source_links_v160.py"),
    ("SIOPE history", "scripts/test_siope_history_v160.py"),
    ("AGID indicators", "scripts/test_agid_indicators.py"),
    ("AGID idempotence", "scripts/test_agid_refresh_idempotent.py"),
    ("ATECO/AGCOM audit", "scripts/test_ateco_agcom_audit.py"),
    ("AGCOM percentages", "scripts/test_agcom_primary_percentages.py"),
    ("monthly data check", "scripts/test_monthly_data_check.py"),
    ("PNRR audit", "scripts/test_pnrr_toscana_audit.py"),
    ("PNRR status integration", "scripts/test_pnrr_status_integration.py"),
)


def compile_targets() -> tuple[str, ...]:
    path = ROOT / COMPILE_MANIFEST
    return tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


class PreflightError(RuntimeError):
    pass


def command_text(command: Sequence[str]) -> str:
    return " ".join(str(part) for part in command)


def run(label: str, command: Sequence[str], *, plan: bool = False) -> None:
    print(f"\n==> {label}\n    {command_text(command)}", flush=True)
    if plan:
        return
    subprocess.run(list(command), cwd=ROOT, check=True)


def run_python(label: str, script: str, *args: str, plan: bool = False) -> None:
    run(label, (PYTHON, script, *args), plan=plan)


def node_check(path: str, *, plan: bool = False) -> None:
    if not plan and shutil.which("node") is None:
        raise PreflightError("Node.js non disponibile: impossibile eseguire node --check")
    run(f"node syntax: {path}", ("node", "--check", path), plan=plan)


def validate_required_paths(paths: Iterable[str], *, plan: bool = False) -> None:
    print("\n==> required paths", flush=True)
    for relative in paths:
        print(f"    {relative}")
        if not plan and not (ROOT / relative).exists():
            raise PreflightError(f"File richiesto mancante: {relative}")


def validate_json_contracts(*, plan: bool = False) -> None:
    print("\n==> JSON contracts", flush=True)
    for relative in JSON_CONTRACTS:
        print(f"    {relative}")
        if plan:
            continue
        path = ROOT / relative
        with path.open("r", encoding="utf-8") as handle:
            json.load(handle)


def git_source_clean(*, plan: bool = False) -> None:
    if not (ROOT / ".git").exists():
        print("\n==> git source diff: skipped (.git non presente)", flush=True)
        return
    run(
        "build must not rewrite canonical sources",
        ("git", "diff", "--exit-code", "--", ".", ":(exclude)dist"),
        plan=plan,
    )


def verify_crests(*, plan: bool = False) -> None:
    print("\n==> municipal crests", flush=True)
    if plan:
        return
    crests = (
        "massarosa.png",
        "viareggio.svg",
        "camaiore.svg",
        "pietrasanta.svg",
        "seravezza.png",
        "forte-dei-marmi.svg",
        "stazzema.webp",
    )
    for crest in crests:
        path = DIST / "crests" / crest
        if not path.exists() or path.stat().st_size == 0:
            raise PreflightError(f"Stemma mancante: {crest}")
    for crest in ("viareggio.svg", "camaiore.svg", "pietrasanta.svg", "forte-dei-marmi.svg"):
        if mimetypes.guess_type(crest)[0] != "image/svg+xml":
            raise PreflightError(f"MIME SVG inatteso: {crest}")
    print("    7/7 stemmi verificati")


def quick(*, plan: bool = False) -> None:
    print("\n### OV PREFLIGHT QUICK ###", flush=True)
    validate_required_paths(
        (
            "requirements-ci.txt",
            COMPILE_MANIFEST,
            "scripts/build_static_brand.py",
            "scripts/test_site_consistency.py",
            "scripts/test_site_chrome.py",
            "scripts/copy_percorsi_dist.py",
            "assets/visual-grammar.js",
            "assets/pnrr-town-detail.js",
        ),
        plan=plan,
    )
    validate_json_contracts(plan=plan)

    core_compile = (
        "scripts/preflight.py",
        "scripts/site_chrome.py",
        "scripts/preview_dist.py",
        "scripts/test_site_chrome.py",
        "scripts/test_site_consistency.py",
        "scripts/test_site_chrome_browser.py",
    )
    run("compile core CI scripts", (PYTHON, "-m", "py_compile", *core_compile), plan=plan)
    run(
        "compile active CI maintenance scripts",
        (PYTHON, "-m", "py_compile", *compile_targets()),
        plan=plan,
    )
    for javascript in (
        "assets/visual-grammar.js",
        "assets/pnrr-town-detail.js",
        "assets/data-status.js",
        "assets/pwa.js",
        "service-worker.js",
        "assets/ux-accordion.js",
        "assets/ux-history.js",
        "assets/ux-history-core.js",
        "percorsi/app.js",
        "percorsi/data-loader.js",
    ):
        node_check(javascript, plan=plan)

    run_python("site chrome unit contract", "scripts/test_site_chrome.py", plan=plan)
    run_python(
        "site consistency source-only",
        "scripts/test_site_consistency.py",
        "--source-only",
        plan=plan,
    )

    for label, script, *args in CANONICAL_TESTS:
        run_python(f"canonical: {label}", script, *args, plan=plan)

    run_python("build pre-rendered site", "scripts/build_static_brand.py", plan=plan)
    git_source_clean(plan=plan)

    run_python("materialize data status", "scripts/build_data_status.py", plan=plan)
    run_python("inject data status runtime", "scripts/inject_data_status_runtime.py", plan=plan)

    run_python("build PNRR deep dive", "scripts/build_pnrr_toscana_deep_dive.py", plan=plan)
    run_python("inject PNRR town experience", "scripts/inject_pnrr_town_experience.py", plan=plan)
    run_python("PNRR draft contract", "scripts/test_pnrr_toscana_draft.py", plan=plan)
    run_python("PNRR review contract", "scripts/test_pnrr_toscana_review.py", plan=plan)

    run_python("include Percorsi Versilia", "scripts/copy_percorsi_dist.py", plan=plan)
    node_check("dist/assets/app-bundle.js", plan=plan)
    run_python("Percorsi draft contract", "scripts/test_percorsi_draft.py", plan=plan)
    run_python("Percorsi accordion overlap", "scripts/test_accordion_no_overlap.py", plan=plan)
    run_python("Percorsi refinements", "scripts/test_percorsi_refinements.py", plan=plan)

    run_python("site-wide consistency", "scripts/test_site_consistency.py", plan=plan)
    verify_crests(plan=plan)
    print("\nQUICK PREFLIGHT: GREEN", flush=True)


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(base: str, process: subprocess.Popen[bytes], log_path: Path) -> None:
    for _ in range(40):
        if process.poll() is not None:
            text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
            raise PreflightError(f"Preview server terminato prematuramente.\n{text}")
        try:
            with urllib.request.urlopen(base, timeout=0.5) as response:
                if response.status < 500:
                    return
        except Exception:
            time.sleep(0.25)
    text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    raise PreflightError(f"Preview server non pronto su {base}.\n{text}")


def browser_commands(base: str) -> list[tuple[str, tuple[str, ...]]]:
    return [
        ("Demography browser", (PYTHON, "scripts/test_demography_lotto_a_browser_v2.py", "--base", base)),
        ("Income browser", (PYTHON, "scripts/test_income_lotto_a_browser.py", "--base", base)),
        ("Fiscalita browser", (PYTHON, "scripts/test_fiscal_lotto_b_browser.py", "--base", base)),
        ("Amministrazione browser", (PYTHON, "scripts/test_amministrazione_lotto_a_browser.py", "--base", base)),
        ("Lavoro/istruzione browser", (PYTHON, "scripts/test_lavoro_istruzione_eta_genere_browser.py", "--base", base)),
        ("Lavoro pyramid browser", (PYTHON, "scripts/test_lavoro_istruzione_versilia_pyramid_browser.py", "--base", base)),
        ("Mobilita browser", (PYTHON, "scripts/test_mobilita_tpl_v119_browser.py", "--base", base, "--screenshots-dir", "reports/mobilita-v119-browser")),
        ("Agricoltura interactions", (PYTHON, "scripts/test_agricoltura_review_interactions_v120.py")),
        ("Costa browser", (PYTHON, "scripts/test_costa_mare_v123_browser.py", "--base", base)),
        ("Attivita estrattive browser", (PYTHON, "scripts/test_attivita_estrattive_v128_browser.py", "--base", base)),
        ("Ambiente acqua browser", (PYTHON, "scripts/test_ambiente_acqua_v124_browser.py", "--base", base)),
        ("ERP browser", (PYTHON, "scripts/test_erp_arrears_v125_browser.py", "--base", base, "--screenshots-dir", "reports/erp-arrears-v125-browser")),
        ("Investimenti browser", (PYTHON, "scripts/test_investimenti_versilia_browser.py", "--base", base)),
        ("Salute finanziaria browser", (PYTHON, "scripts/test_salute_finanziaria_v129_browser.py", "--base", base)),
        ("PNRR town browser", (PYTHON, "scripts/test_pnrr_toscana_town_browser.py", "--base", base)),
        ("Income/inflation browser", (PYTHON, "scripts/check_income_inflation_history_browser.py", "--base", base)),
        ("Data status browser", (PYTHON, "scripts/test_data_status_browser.py", "--base", base)),
        ("Chart surfaces", (PYTHON, "scripts/test_chart_surfaces.py")),
        ("Accordion/history UX", (PYTHON, "scripts/test_ux_experiment.py")),
        ("Mobile interactions", (PYTHON, "scripts/test_mobile_interactions.py")),
        ("Accordion persistence", (PYTHON, "scripts/test_accordion_tools_persistence.py")),
        ("Exports", (PYTHON, "scripts/test_exports_v161.py")),
        ("Percorsi mobile", (PYTHON, "scripts/test_percorsi_mobile_list_contract.py", "--base", base)),
        ("Site chrome browser", (PYTHON, "scripts/test_site_chrome_browser.py", "--base", base)),
    ]


def validate_monthly_state(temp_dir: Path, *, plan: bool = False) -> None:
    report_md = temp_dir / "report.md"
    report_json = temp_dir / "report.json"
    state_json = temp_dir / "state.json"
    run(
        "monthly monitor offline",
        (
            PYTHON,
            "scripts/monthly_data_check_status.py",
            "--mode",
            "offline",
            "--report-md",
            str(report_md),
            "--report-json",
            str(report_json),
            "--next-state",
            str(state_json),
        ),
        plan=plan,
    )
    if plan:
        return
    site = json.loads((ROOT / "data/site-data.json").read_text(encoding="utf-8"))
    state = json.loads(state_json.read_text(encoding="utf-8"))
    if state.get("schemaVersion") != 2:
        raise PreflightError("Monthly monitor: schemaVersion != 2")
    if len(state.get("metrics", {})) != len(site.get("metrics", {})):
        raise PreflightError("Monthly monitor: numero metriche non allineato al catalogo")


def full(*, skip_quick: bool = False, plan: bool = False) -> None:
    print("\n### OV PREFLIGHT FULL ###", flush=True)
    if not skip_quick:
        quick(plan=plan)
    elif not plan and not DIST.exists():
        raise PreflightError("--skip-quick richiede un dist/ gia materializzato dal Quick job")

    if not plan and shutil.which("node") is None:
        raise PreflightError("Node.js non disponibile")

    # Cheap post-build regressions always precede browser work.
    for label, script, *args in STATIC_FULL_TESTS:
        run_python(f"static full: {label}", script, *args, plan=plan)

    (ROOT / "reports/mobilita-v119-browser").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports/erp-arrears-v125-browser").mkdir(parents=True, exist_ok=True)

    if plan:
        base = "http://127.0.0.1:<dynamic>/"
        for label, command in browser_commands(base):
            run(label, command, plan=True)
        with tempfile.TemporaryDirectory(prefix="ov-preflight-") as temporary:
            validate_monthly_state(Path(temporary), plan=True)
        print("\nFULL PREFLIGHT PLAN: OK", flush=True)
        return

    port = free_port()
    base = f"http://127.0.0.1:{port}/"
    with tempfile.TemporaryDirectory(prefix="ov-preflight-") as temporary:
        temp_dir = Path(temporary)
        log_path = temp_dir / "preview.log"
        with log_path.open("wb") as log:
            process = subprocess.Popen(
                (PYTHON, "scripts/preview_dist.py", "--port", str(port), "--directory", "dist"),
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
            try:
                wait_for_server(base, process, log_path)
                for label, command in browser_commands(base):
                    run(label, command)
                validate_monthly_state(temp_dir)
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)

    print("\nFULL PREFLIGHT: GREEN", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Osservatorio Versilia preflight")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--quick", action="store_true", help="mandatory fast pre-push gate")
    mode.add_argument("--full", action="store_true", help="complete browser/regression gate")
    parser.add_argument(
        "--skip-quick",
        action="store_true",
        help="Full only: reuse dist produced by a previously successful Quick job",
    )
    parser.add_argument("--plan", action="store_true", help="print commands without executing them")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.skip_quick and not args.full:
        raise SystemExit("--skip-quick e valido solo con --full")
    try:
        if args.quick:
            quick(plan=args.plan)
        else:
            full(skip_quick=args.skip_quick, plan=args.plan)
    except subprocess.CalledProcessError as exc:
        print(f"\nPREFLIGHT FAILED: {command_text(exc.cmd)} -> exit {exc.returncode}", file=sys.stderr)
        raise SystemExit(exc.returncode) from exc
    except (PreflightError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"\nPREFLIGHT FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
