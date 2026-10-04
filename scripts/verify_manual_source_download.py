#!/usr/bin/env python3
"""Validate operator-supplied official archives without editing data or live results.

Usage: python scripts/verify_manual_source_download.py --source aci FILE
       python scripts/verify_manual_source_download.py --source ars --indicator 255 FILE
The caller records the official download URL and acquisition date separately.
A matching historical archive does not prove that it is the latest release.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_MEMBER_BYTES = 32 * 1024 * 1024


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verify(path: Path, source: str, indicator: int | None, root: Path = ROOT) -> dict:
    raw = path.read_bytes()
    if len(raw) > MAX_MEMBER_BYTES:
        raise ValueError('Archive exceeds 32 MiB limit')
    result = {'method': 'operator_supplied_official_download', 'fileName': path.name,
              'archiveSha256': sha(raw), 'archiveBytes': len(raw),
              'liveAcquisitionVerified': False, 'latestReleaseVerified': False}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        # Read in memory only; reject expansion bombs and ambiguous sources.
        if sum(x.file_size for x in archive.infolist()) > MAX_MEMBER_BYTES:
            raise ValueError('Expanded archive exceeds 32 MiB limit')
        if archive.testzip() is not None:
            raise ValueError('Archive CRC mismatch')
        if source == 'aci':
            snapshot_path = root / 'data/source-snapshots/a3-aci-vehicle-benchmark-2024.json'
            snapshot = json.loads(snapshot_path.read_text())
            expected = snapshot['source']
            member = expected['archiveMember']
            if member not in archive.namelist():
                raise ValueError('Unsupported ACI release/member: validate schema and municipal panel before import')
            workbook = archive.read(member)
            result.update(sourceUrl=expected['archiveUrl'], metricKeys=['motorization', 'pollutingCars'],
                          referencePeriod=str(snapshot['referenceYear']), member=member,
                          memberSha256=sha(workbook), memberBytes=len(workbook),
                          matchesPublishedSnapshot=(sha(raw) == expected['archiveSha256']
                                                    and sha(workbook) == expected['workbookSha256']))
        else:
            if indicator is None:
                raise ValueError('ARS requires --indicator')
            snapshot_path = root / 'data/source-snapshots/ars-salute-11-v140.json'
            snapshot = json.loads(snapshot_path.read_text())['indicators'].get(str(indicator))
            if snapshot is None:
                snapshot_path = root / 'data/source-snapshots/ars-a3-5-legacy-history.json'
                candidates = json.loads(snapshot_path.read_text())['indicators']
                snapshot = next((dict(v, key=k) for k, v in candidates.items() if v['indicatorId'] == indicator), None)
            if snapshot is None:
                raise ValueError('ARS indicator not supported by the versioned snapshots')
            names = [n for n in archive.namelist() if n.lower().endswith('.csv')]
            if len(names) != 1:
                raise ValueError('Expected exactly one CSV')
            payload = archive.read(names[0])
            reader = csv.DictReader(io.StringIO(payload.decode('utf-8-sig')))
            required = {'id_indicatore', 'anno', 'codice_geografia', 'geografia', 'den', 'num',
                        'misura_grezza', 'misura_standardizzata', 'liminf', 'limsup', 'sesso', 'strato1', 'strato2'}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError('ARS CSV schema mismatch')
            rows = list(reader)
            if not rows or any(r['id_indicatore'].strip() != str(indicator) for r in rows):
                raise ValueError('ARS indicator identity mismatch')
            periods = sorted({r['anno'].strip() for r in rows})
            result.update(sourceUrl=snapshot['exportUrl'], metricKeys=[snapshot['key']],
                          referencePeriod=periods[-1], periods=periods, records=len(rows),
                          member=names[0], memberSha256=sha(payload), memberBytes=len(payload),
                          matchesPublishedSnapshot=(sha(payload) == snapshot['sourceFile']['sha256']
                                                    and len(payload) == snapshot['sourceFile']['bytes']))
        result['snapshotPath'] = str(snapshot_path.relative_to(root))
        result['verdict'] = 'published_snapshot_revalidated' if result['matchesPublishedSnapshot'] else 'different_candidate_requires_validation'
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    parser.add_argument('--source', choices=['aci', 'ars'], required=True)
    parser.add_argument('--indicator', type=int)
    args = parser.parse_args()
    try:
        result = verify(args.file, args.source, args.indicator)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, UnicodeError) as exc:
        print(json.dumps({'verdict': 'rejected', 'error': str(exc), 'liveAcquisitionVerified': False}))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
