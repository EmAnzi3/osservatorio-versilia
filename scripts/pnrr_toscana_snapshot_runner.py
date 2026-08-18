#!/usr/bin/env python3
"""Esegue audit e inventario PNRR sulla stessa fotografia CSV locale.

Il download viene effettuato dal workflow con retry; questo runner evita due
richieste consecutive al server regionale e registra l'hash SHA-256 del file
esaminato. Nessun dato canonico viene modificato.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import pnrr_toscana_audit as audit
import pnrr_toscana_forensic as forensic


def local_records(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = sorted(audit.REQUIRED_FIELDS - fields)
        if missing:
            raise RuntimeError(f"Tracciato PNRR Toscana incompleto: {', '.join(missing)}")
        for field in audit.CONCLUSION_FIELDS:
            if field not in fields:
                raise RuntimeError(f"Campo conclusione assente: {field}")
        yield from reader


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=Path("data/site-data.json"))
    parser.add_argument("--audit-json", type=Path, default=Path("reports/pnrr-toscana-audit.json"))
    parser.add_argument("--audit-md", type=Path, default=Path("reports/pnrr-toscana-audit.md"))
    parser.add_argument("--forensic-json", type=Path, default=Path("reports/pnrr-toscana-forensic.json"))
    parser.add_argument("--forensic-md", type=Path, default=Path("reports/pnrr-toscana-forensic.md"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = json.loads(args.data.read_text(encoding="utf-8"))
    source_hash = sha256(args.source)

    audit_result = audit.audit_records(data, local_records(args.source))
    audit_result["sourceSnapshotSha256"] = source_hash
    write_json(args.audit_json, audit_result)
    args.audit_md.parent.mkdir(parents=True, exist_ok=True)
    args.audit_md.write_text(audit.markdown(audit_result), encoding="utf-8")

    original_iter = audit.iter_csv_records
    audit.iter_csv_records = lambda url=audit.MAIN_CSV_URL: local_records(args.source)
    try:
        forensic_result = forensic.build_forensic(data)
    finally:
        audit.iter_csv_records = original_iter
    forensic_result["sourceSnapshotSha256"] = source_hash
    if forensic_result["selectedUniqueProjects"] != 107:
        raise SystemExit(
            f"Fotografia inattesa: attesi 107 progetti, trovati {forensic_result['selectedUniqueProjects']}"
        )
    if forensic_result["crossTownDuplicateProjectIds"]:
        raise SystemExit("Uno o più ID progetto risultano attribuiti a più Comuni del perimetro")
    write_json(args.forensic_json, forensic_result)
    args.forensic_md.parent.mkdir(parents=True, exist_ok=True)
    args.forensic_md.write_text(forensic.markdown(forensic_result), encoding="utf-8")

    print(audit.markdown(audit_result))
    print("\n---\n")
    print(forensic.markdown(forensic_result))
    print(f"SHA256 fotografia fonte: {source_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
