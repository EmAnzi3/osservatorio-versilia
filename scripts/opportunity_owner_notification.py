#!/usr/bin/env python3
"""Keep complete Radar reports on one owner issue, with resumable comments."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

# Leave room for markers and continuation headings below GitHub's body limit.
PART_BYTES = 48_000


def split_markdown(text: str, max_bytes: int = PART_BYTES) -> list[str]:
    chunks, current, size = [], [], 0
    for line in text.splitlines(keepends=True):
        data = line.encode('utf-8')
        if size and size + len(data) > max_bytes:
            chunks.append(''.join(current)); current, size = [], 0
        while len(data) > max_bytes:
            fragment = data[:max_bytes].decode('utf-8', errors='ignore')
            if not fragment:
                raise ValueError('Budget insufficiente per un carattere Unicode')
            chunks.append(fragment)
            data = data[len(fragment.encode('utf-8')):]
        current.append(data.decode('utf-8')); size += len(data)
    if current:
        chunks.append(''.join(current))
    return chunks or ['']


def _gh(args):
    return subprocess.run(['gh', *args], check=True, capture_output=True, text=True).stdout.strip()


def notify_owner(*, repo, marker, title, body, assignee, gh=_gh):
    chunks = split_markdown(body)
    token = f'<!-- {marker} -->'
    issues = json.loads(gh(['issue', 'list', '--repo', repo, '--state', 'all', '--limit', '100', '--json', 'body,url']))
    existing = next((item for item in issues if token in (item.get('body') or '')), None)
    with TemporaryDirectory(prefix='radar-owner-notification-') as directory:
        root = Path(directory)
        if existing:
            issue_url = existing['url']
        else:
            first = chunks[0]
            if token not in first:
                first = token + '\n' + first
            if len(chunks) > 1:
                first += '\n\n**Rapporto completo:** prosegue nei commenti di questa stessa segnalazione. Nessun documento è omesso; i collegamenti restano diretti.\n'
            path = root/'body.md'; path.write_text(first, encoding='utf-8')
            issue_url = gh(['issue', 'create', '--repo', repo, '--title', title,
                            '--body-file', str(path), '--assignee', assignee]).splitlines()[-1]
        if len(chunks) > 1:
            comments = json.loads(gh(['issue', 'view', issue_url, '--repo', repo, '--json', 'comments'])).get('comments') or []
            for index, chunk in enumerate(chunks[1:], start=2):
                part_marker = f'<!-- {marker}:part:{index} -->'
                if any(part_marker in (c.get('body') or '') for c in comments):
                    continue
                prefix = part_marker + f'\n## Rapporto completo · parte {index}/{len(chunks)}\n\n'
                # Continue the review table with its headings when split mid-table.
                headers = list(re.finditer(r'^(\|.*\|\n)(\|[ :|\-]+\|\n)', ''.join(chunks[:index-1]), re.M))
                if chunk.startswith('|') and not re.match(r'^\|.*\|\n\|[ :|\-]+\|\n', chunk) and headers:
                    prefix += headers[-1].group(0)
                path = root/f'part-{index}.md'; path.write_text(prefix+chunk, encoding='utf-8')
                gh(['issue', 'comment', issue_url, '--repo', repo, '--body-file', str(path)])
    return issue_url


def main():
    parser = argparse.ArgumentParser()
    for name in ('repo', 'marker', 'title', 'assignee', 'body-file'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    print(notify_owner(repo=args.repo, marker=args.marker, title=args.title, assignee=args.assignee,
                       body=Path(args.body_file).read_text(encoding='utf-8')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
