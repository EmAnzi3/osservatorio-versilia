#!/usr/bin/env python3
"""Transactional source workspace for public build materializers.

Release overlays may temporarily adapt canonical sources before prerendering, but
they must never leave those adaptations in the checkout or hide them behind Git
index flags. This module snapshots the tracked workspace, verifies the declared
mutation boundary, restores the exact pre-build bytes and clears legacy
``assume-unchanged`` flags after every build, including failed builds.
"""
from __future__ import annotations

import json
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "ci" / "build-materialization-contract.json"


def load_build_materialization_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def validate_build_materialization_contract() -> dict[str, int]:
    contract = load_build_materialization_contract()
    if contract.get("schemaVersion") != 1:
        raise RuntimeError("Schema build-materialization-contract non supportato")

    entrypoint = str(contract.get("entrypoint") or "")
    implementation = str(contract.get("implementation") or "")
    if entrypoint != "scripts/build_static_brand.py":
        raise RuntimeError(f"Entrypoint build inatteso: {entrypoint}")
    if implementation != "scripts/build_static_brand_impl.py":
        raise RuntimeError(f"Implementazione build inattesa: {implementation}")

    materializers = list(contract.get("publicMaterializers") or [])
    allowed = list(contract.get("trackedMutationAllowlist") or [])
    generated = list(contract.get("ephemeralGeneratedPaths") or [])
    forbidden_prefixes = tuple(contract.get("forbiddenMutationPrefixes") or [])
    forbidden_paths = set(contract.get("forbiddenMutationPaths") or [])

    for label, values in (
        ("publicMaterializers", materializers),
        ("trackedMutationAllowlist", allowed),
        ("ephemeralGeneratedPaths", generated),
    ):
        if len(values) != len(set(values)):
            raise RuntimeError(f"Duplicati nel contratto build: {label}")

    if set(allowed) & set(generated):
        raise RuntimeError("Un path non può essere insieme tracked e generated")

    for relative in (entrypoint, implementation, *materializers, *allowed):
        if not relative or not (ROOT / relative).is_file():
            raise RuntimeError(f"Path dichiarato nel contratto build assente: {relative}")

    for relative in allowed:
        if relative in forbidden_paths or any(relative.startswith(prefix) for prefix in forbidden_prefixes):
            raise RuntimeError(f"Mutazione transitoria vietata dal contratto: {relative}")

    return {
        "materializers": len(materializers),
        "allowed_mutations": len(allowed),
        "generated": len(generated),
    }


def _git_available() -> bool:
    return (ROOT / ".git").exists()


def _run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _tracked_paths() -> tuple[str, ...]:
    result = _run_git("ls-files", "-z")
    return tuple(
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    )


def _bytes_or_none(relative: str) -> bytes | None:
    path = ROOT / relative
    if not path.exists():
        return None
    return path.read_bytes()


def _restore(relative: str, baseline: bytes | None) -> None:
    path = ROOT / relative
    if baseline is None:
        if path.exists():
            path.unlink()
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(baseline)


def _clear_assume_unchanged(paths: set[str]) -> None:
    if not paths or not _git_available():
        return
    tracked = set(_tracked_paths())
    candidates = sorted(paths & tracked)
    if candidates:
        _run_git("update-index", "--no-assume-unchanged", "--", *candidates)


@contextmanager
def public_build_workspace() -> Iterator[None]:
    """Run a public build as a transaction over the source checkout."""
    summary = validate_build_materialization_contract()
    contract = load_build_materialization_contract()
    allowed = set(contract["trackedMutationAllowlist"])
    generated = set(contract["ephemeralGeneratedPaths"])
    strict = _git_available()

    _clear_assume_unchanged(allowed)
    tracked = set(_tracked_paths()) if strict else set(allowed)
    tracked_baseline = {relative: _bytes_or_none(relative) for relative in tracked}
    generated_baseline = {relative: _bytes_or_none(relative) for relative in generated}

    caught: BaseException | None = None
    unexpected: set[str] = set()
    changed: set[str] = set()
    try:
        yield
    except BaseException as error:
        caught = error
        raise
    finally:
        changed = {
            relative
            for relative, baseline in tracked_baseline.items()
            if _bytes_or_none(relative) != baseline
        }
        unexpected = changed - allowed if strict else set()

        for relative in changed:
            _restore(relative, tracked_baseline[relative])
        for relative, baseline in generated_baseline.items():
            if _bytes_or_none(relative) != baseline:
                _restore(relative, baseline)

        _clear_assume_unchanged(allowed | changed)

        residue = {
            relative
            for relative, baseline in tracked_baseline.items()
            if _bytes_or_none(relative) != baseline
        }
        generated_residue = {
            relative
            for relative, baseline in generated_baseline.items()
            if _bytes_or_none(relative) != baseline
        }
        if residue or generated_residue:
            message = (
                "Ripristino workspace build incompleto: "
                f"tracked={sorted(residue)}, generated={sorted(generated_residue)}"
            )
            if caught is not None:
                try:
                    caught.add_note(message)
                except AttributeError:
                    pass
            else:
                raise RuntimeError(message)

        if unexpected:
            message = (
                "Builder fuori contratto: ha modificato sorgenti non dichiarate: "
                + ", ".join(sorted(unexpected))
            )
            if caught is not None:
                try:
                    caught.add_note(message)
                except AttributeError:
                    pass
            else:
                raise RuntimeError(message)

        if caught is None:
            print(
                "Workspace build ripristinato: "
                f"{len(changed)} mutazioni transitorie su {summary['allowed_mutations']} ammesse; "
                f"{summary['generated']} path generati effimeri."
            )
