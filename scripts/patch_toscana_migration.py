#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parent / "update_toscana_indicators_v150.py"
text = path.read_text(encoding="utf-8")
text = text.replace(
    "landslideExposure: ['frane', 'rischio frana', 'dissesto']",
    "landslideExposure: ['frane', 'rischio geomorfologico']",
    1,
)
old_block = '''        (
            "    landslideExposure: ['frane', 'rischio geomorfologico'],\\n",
            "    landslideExposure: ['frane', 'rischio geomorfologico'],\\n"
            "    organicAgriculturalAreaShare: ['biologico', 'agricoltura biologica', 'sau bio'],\\n",
        ),'''
new_block = '''        (
            "    landslideExposure: ['frane', 'rischio geomorfologico'], thirdSector: ['associazioni', 'volontariato'],\\n",
            "    landslideExposure: ['frane', 'rischio geomorfologico'],\\n"
            "    organicAgriculturalAreaShare: ['biologico', 'agricoltura biologica', 'sau bio'],\\n"
            "    thirdSector: ['associazioni', 'volontariato'],\\n",
        ),'''
if old_block in text:
    text = text.replace(old_block, new_block, 1)
elif new_block not in text:
    raise RuntimeError("Blocco ambientale non trovato nella migrazione")
path.write_text(text, encoding="utf-8")
print("Migrazione Toscana allineata ai sorgenti correnti.")
