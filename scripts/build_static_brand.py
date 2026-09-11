#!/usr/bin/env python3
"""Transactional entry point for the production static build."""
from __future__ import annotations

import runpy
from pathlib import Path

from build_static_brand_impl import *  # noqa: F401,F403
from ephemeral_build_workspace import public_build_workspace

ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = ROOT / "scripts" / "build_static_brand_impl.py"
OPPORTUNITY_MATERIALIZER = ROOT / "scripts" / "materialize_opportunity_release_snapshot.py"
FRAGILITA_MATERIALIZER = (ROOT / "scripts" / "materialize_fragilita_release.py").resolve()
FRAGILITA_RUNTIME_PATCH = (ROOT / "scripts" / "patch_fragilita_runtime.py").resolve()
ECONOMIA_PRODOTTA_MATERIALIZER = ROOT / "scripts" / "materialize_economia_prodotta_release.py"
BIOMETRIA_MATERIALIZER = ROOT / "scripts" / "materialize_biometria_comune_release.py"

_ORIGINAL_RUN_PATH = runpy.run_path


def _run_path_with_fragilita_r3_fix(path_name, *args, **kwargs):
    """Execute the v1.33 runtime materializer with the two R3 grouping fixes.

    This keeps the production build transactional: the tracked patch source is not
    rewritten inside the ephemeral workspace, while the generated runtime receives
    exactly the reviewed R3 expressions before prerendering.
    """
    path = Path(path_name).resolve()
    if path == FRAGILITA_MATERIALIZER:
        result = _ORIGINAL_RUN_PATH(path_name, *args, **kwargs)
        _ORIGINAL_RUN_PATH(str(ECONOMIA_PRODOTTA_MATERIALIZER), run_name="__main__")
        _ORIGINAL_RUN_PATH(str(BIOMETRIA_MATERIALIZER), run_name="__main__")
        return result
    if path != FRAGILITA_RUNTIME_PATCH:
        return _ORIGINAL_RUN_PATH(path_name, *args, **kwargs)

    source = path.read_text(encoding="utf-8")
    fixes = (
        (
            'b=replace_once(b,"(omi || stock || securityMeasures) ? options[0] : null)"',
            'b=replace_once(b,"((omi || stock || securityMeasures) ? options[0] : null)"',
        ),
        (
            '","securityMeasures ? compositeSelectionAggregate(metric,\'part-0\') : (hydroRisk ? compositeSelectionAggregate(metric,metric.meta.defaultScenario) : null)",\'town aggregate summary\')',
            '","(securityMeasures ? compositeSelectionAggregate(metric,\'part-0\') : (hydroRisk ? compositeSelectionAggregate(metric,metric.meta.defaultScenario) : null))",\'town aggregate summary\')',
        ),
    )
    for old, new in fixes:
        if source.count(old) != 1:
            raise RuntimeError(f"Fix R3 fragilità non applicabile in modo univoco: {old}")
        source = source.replace(old, new, 1)

    globals_dict = {
        "__name__": kwargs.get("run_name") or "<run_path>",
        "__file__": str(path),
        "__cached__": None,
        "__doc__": None,
        "__loader__": None,
        "__package__": "",
        "__spec__": None,
    }
    exec(compile(source, str(path), "exec"), globals_dict)
    return globals_dict


if __name__ == "__main__":
    with public_build_workspace():
        # Il Radar pubblico deve essere ricostruito nello stesso workspace effimero
        # della build. In questo modo Pages applica sempre replay audit + matrice al
        # daily verificato disponibile, senza riscrivere i dati canonici nel repo.
        _ORIGINAL_RUN_PATH(str(OPPORTUNITY_MATERIALIZER), run_name="__main__")
        runpy.run_path = _run_path_with_fragilita_r3_fix
        try:
            _ORIGINAL_RUN_PATH(str(IMPLEMENTATION), run_name="__main__")
        finally:
            runpy.run_path = _ORIGINAL_RUN_PATH
