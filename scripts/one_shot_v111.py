#!/usr/bin/env python3
from pathlib import Path
import base64
import gzip

ROOT = Path(__file__).resolve().parents[1]
payload = ''.join((ROOT / '.tmp' / f'v111-{index}.b64').read_text(encoding='utf-8').strip() for index in range(1, 5))
source = gzip.decompress(base64.b64decode(payload))
exec(compile(source, 'one-shot-v111-embedded.py', 'exec'))
