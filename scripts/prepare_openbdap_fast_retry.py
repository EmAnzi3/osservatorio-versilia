#!/usr/bin/env python3
"""Bound OpenBDAP network attempts inside CI without weakening data checks."""
from pathlib import Path

path = Path(__file__).with_name("expand_bilanci_history_v160.py")
text = path.read_text(encoding="utf-8")
replacements = {
    '        ("proxy raw CorsProxy", f"https://corsproxy.io/?url={encoded}"),\n': '',
    '    for round_number in range(1, 5):': '    for round_number in range(1, 2):',
    '                response = session.get(transport_url, timeout=base.TIMEOUT)':
        '                response = session.get(transport_url, timeout=30)',
    '        if round_number < 4:': '        if round_number < 1:',
}
for old, new in replacements.items():
    if old not in text:
        raise RuntimeError(f"Patch CI non applicabile: {old}")
    text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Tentativi OpenBDAP CI limitati: fonte invariata, timeout ridotto, controlli integri.")
