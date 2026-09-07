#!/usr/bin/env python3
"""Single entry point for the declarative content and workflow architecture."""
from __future__ import annotations

from content_contract import validate_content_contract
from workflow_contract import validate_workflow_contract


def main() -> None:
    content = validate_content_contract()
    workflows = validate_workflow_contract()
    print(
        "ARCHITECTURE CONTRACT: GREEN — "
        f"{content['towns']} comuni, {content['themes']} temi, {content['metrics']} indicatori, "
        f"{content['pages']} route, {workflows['workflows']} workflow; "
        f"storage={content['storage']}; visual={content['visualizations']}"
    )


if __name__ == "__main__":
    main()
