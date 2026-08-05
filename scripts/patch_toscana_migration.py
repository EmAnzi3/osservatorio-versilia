#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parent / "update_toscana_indicators_v150.py"
text = path.read_text(encoding="utf-8")

start_marker = '        (\n            "    landslideExposure:'
end_marker = '        (\n            "      case \'studentsPerClass\''

start = text.find(start_marker)
end = text.find(end_marker, start + 1 if start >= 0 else 0)
if start < 0 or end < 0:
    raise RuntimeError("Blocco ambientale non trovato nella migrazione")

replacement = '''        (
            "    landslideExposure: ['frane', 'rischio geomorfologico'], thirdSector: ['associazioni', 'volontariato'],\\n",
            "    landslideExposure: ['frane', 'rischio geomorfologico'],\\n"
            "    organicAgriculturalAreaShare: ['biologico', 'agricoltura biologica', 'sau bio'],\\n"
            "    thirdSector: ['associazioni', 'volontariato'],\\n",
        ),
'''

text = text[:start] + replacement + text[end:]
path.write_text(text, encoding="utf-8")
print("Migrazione Toscana allineata ai sorgenti correnti.")
