#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parent / "update_toscana_indicators_v150.py"
text = path.read_text(encoding="utf-8")

old_format = '''def format_value(value: float, unit: str) -> str:
    if unit == "minutes":
        return f"{value:.1f}".replace(".", ",") + " min"
    return f"{value:.1f}".replace(".", ",") + "%"
'''
new_format = '''def format_value(value: float, unit: str) -> str:
    formatted = f"{value:.1f}".replace(".", ",")
    if unit == "minutes":
        return formatted + " min"
    if unit == "per1000":
        return formatted + " ogni 1.000"
    return formatted + "%"
'''
if old_format in text:
    text = text.replace(old_format, new_format, 1)
elif new_format not in text:
    raise RuntimeError("Funzione di formattazione non trovata nella migrazione")

correct_environment = '''        (
            "    landslideExposure: ['frane', 'rischio geomorfologico'], thirdSector: ['associazioni', 'volontariato'],\\n",
            "    landslideExposure: ['frane', 'rischio geomorfologico'],\\n"
            "    organicAgriculturalAreaShare: ['biologico', 'agricoltura biologica', 'sau bio'],\\n"
            "    thirdSector: ['associazioni', 'volontariato'],\\n",
        ),
'''
if correct_environment not in text:
    start_marker = '        (\n            "    landslideExposure:'
    end_marker = '        (\n            "      case \'studentsPerClass\''
    start = text.find(start_marker)
    end = text.find(end_marker, start + 1 if start >= 0 else 0)
    if start < 0 or end < 0:
        raise RuntimeError("Blocco ambientale non trovato nella migrazione")
    text = text[:start] + correct_environment + text[end:]

path.write_text(text, encoding="utf-8")
print("Migrazione Toscana allineata ai sorgenti correnti.")
