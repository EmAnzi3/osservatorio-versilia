#!/usr/bin/env python3
"""Declarative entry point for the site-wide consistency gate."""
from __future__ import annotations

import site_consistency_impl as _impl
from content_contract import configured_paths, expected_pages as _expected_pages, validate_content_contract
from ephemeral_build_workspace import validate_build_materialization_contract
from site_consistency_impl import *  # noqa: F401,F403
from workflow_contract import validate_workflow_contract


def main() -> None:
    content = validate_content_contract()
    workflows = validate_workflow_contract()
    build_workspace = validate_build_materialization_contract()
    _impl.SPECIAL_PUBLIC_PAGES = configured_paths("builderTraceExceptions")
    _impl.NO_SHELL_PAGES = configured_paths("noShell")
    _impl.NO_FOOTER_PAGES = configured_paths("noFooter")
    _impl.expected_pages = _expected_pages
    print(
        "Contratto architetturale verificato: "
        f"{content['metrics']} indicatori, {content['pages']} route, {workflows['workflows']} workflow, "
        f"{build_workspace['allowed_mutations']} mutazioni build transitorie dichiarate."
    )
    _impl.main()


if __name__ == "__main__":
    main()
