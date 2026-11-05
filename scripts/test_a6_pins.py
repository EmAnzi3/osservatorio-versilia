#!/usr/bin/env python3
"""Contratto del registro unico delle impronte A6."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "ci" / "a6-source-pins.json"
HEX = re.compile(r"""['"][0-9a-f]{64}['"]""")
USE = re.compile(r"""_pin\('([a-z_]+#\d+)'\)""")


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["pins"]
    assert all(re.fullmatch(r"[0-9a-f]{64}", v) for v in registry.values()), "impronte non valide nel registro"
    used: set[str] = set()
    for path in sorted((ROOT / "scripts").glob("semantic_query_*adapters*.py")):
        text = path.read_text(encoding="utf-8")
        assert not HEX.search(text), f"{path.name}: impronta scritta nel codice invece che nel registro"
        keys = USE.findall(text)
        module = path.stem.replace("semantic_query_", "").replace("_adapters", "")
        assert all(k.split("#")[0] == module for k in keys), f"{path.name}: impronta di un altro adattatore"
        used.update(keys)
    assert used == set(registry), f"registro e codice disallineati: {sorted(used ^ set(registry))[:10]}"

    probe = (
        "import sys; sys.path.insert(0, 'scripts'); import a6_pins, json;"
        "name = sorted(a6_pins.pins())[0]; pin = a6_pins.Pin(name); other = '0' * 64;"
        "print(json.dumps([pin == str(pin), other != pin, (other, 1) == (pin, 1), a6_pins.RECORDED.get(name)]))"
    )
    normal = json.loads(subprocess.check_output([sys.executable, "-c", probe], cwd=ROOT, env={**os.environ, "A6_REPIN": "0"}))
    assert normal == [True, True, False, None], normal
    repin = json.loads(subprocess.check_output([sys.executable, "-c", probe], cwd=ROOT, env={**os.environ, "A6_REPIN": "1"}))
    assert repin[1] is False and repin[2] is True and repin[3] == "0" * 64, repin
    print(f"Registro impronte A6: {len(registry)} impronte, nessuna nel codice; confronto normale e ri-registrazione PASS")


if __name__ == "__main__":
    main()
