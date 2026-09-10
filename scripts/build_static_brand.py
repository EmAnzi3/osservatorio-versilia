#!/usr/bin/env python3
"""Transactional entry point for the production static build."""
from __future__ import annotations

import runpy
from pathlib import Path

from playwright.sync_api import Page

from build_static_brand_impl import *  # noqa: F401,F403
from ephemeral_build_workspace import public_build_workspace

ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = ROOT / "scripts" / "build_static_brand_impl.py"
OPPORTUNITY_MATERIALIZER = ROOT / "scripts" / "materialize_opportunity_release_snapshot.py"


# Temporary CI diagnostic: identify the prerender route/runtime error before
# producing the verified preview artifact. This is removed once the fault is fixed.
_ORIGINAL_GOTO = Page.goto
_ORIGINAL_WAIT_FOR_SELECTOR = Page.wait_for_selector


def _diagnostic_goto(self, url, *args, **kwargs):
    if not getattr(self, "_ov_prerender_diagnostics", False):
        self._ov_prerender_diagnostics = True
        self.on(
            "console",
            lambda message: print(
                f"PRERENDER CONSOLE [{self.url}] {message.type}: {message.text}",
                flush=True,
            )
            if message.type == "error"
            else None,
        )
        self.on(
            "pageerror",
            lambda error: print(f"PRERENDER PAGEERROR [{self.url}]: {error}", flush=True),
        )
    print(f"PRERENDER NAVIGATE: {url}", flush=True)
    return _ORIGINAL_GOTO(self, url, *args, **kwargs)


def _diagnostic_wait_for_selector(self, selector, *args, **kwargs):
    try:
        return _ORIGINAL_WAIT_FOR_SELECTOR(self, selector, *args, **kwargs)
    except Exception:
        try:
            app = self.locator("#app")
            snapshot = app.inner_html()[:3000] if app.count() else "<missing #app>"
        except Exception as error:
            snapshot = f"<unable to inspect #app: {error}>"
        print(f"PRERENDER FAILURE [{self.url}] selector={selector}: {snapshot}", flush=True)
        raise


Page.goto = _diagnostic_goto
Page.wait_for_selector = _diagnostic_wait_for_selector


if __name__ == "__main__":
    with public_build_workspace():
        # Il Radar pubblico deve essere ricostruito nello stesso workspace effimero
        # della build. In questo modo Pages applica sempre replay audit + matrice al
        # daily verificato disponibile, senza riscrivere i dati canonici nel repo.
        runpy.run_path(str(OPPORTUNITY_MATERIALIZER), run_name="__main__")
        runpy.run_path(str(IMPLEMENTATION), run_name="__main__")
