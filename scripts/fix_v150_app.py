#!/usr/bin/env python3
from pathlib import Path

root = Path(__file__).resolve().parents[1]
app_path = root / "assets" / "app-parts" / "00.txt"
migration_path = root / "scripts" / "update_toscana_indicators_v150.py"

app = app_path.read_text(encoding="utf-8")
old_app = "    landslideExposure: ['frane', 'rischio geomorfologico'], thirdSector: ['associazioni', 'volontariato'],\n"
new_app = (
    "    landslideExposure: ['frane', 'rischio geomorfologico'],\n"
    "    organicAgriculturalAreaShare: ['biologico', 'agricoltura biologica', 'sau bio'],\n"
    "    thirdSector: ['associazioni', 'volontariato'],\n"
)
if old_app in app:
    app = app.replace(old_app, new_app, 1)
elif new_app not in app:
    raise RuntimeError("Riga dei sinonimi ambientali non trovata")
app_path.write_text(app, encoding="utf-8")

migration = migration_path.read_text(encoding="utf-8")
old_logic = '''    for old, new in replacements:
        marker = new.splitlines()[-1].strip()
        if marker in text:
            continue
        if old not in text:
            raise RuntimeError(f"Punto di aggiornamento non trovato: {old.strip()}")
        text = text.replace(old, new, 1)
'''
new_logic = '''    for old, new in replacements:
        if new in text:
            continue
        if old not in text:
            raise RuntimeError(f"Punto di aggiornamento non trovato: {old.strip()}")
        text = text.replace(old, new, 1)
'''
if old_logic in migration:
    migration = migration.replace(old_logic, new_logic, 1)
elif new_logic not in migration:
    raise RuntimeError("Logica idempotente della migrazione non trovata")
migration_path.write_text(migration, encoding="utf-8")

print("Sinonimi e migrazione v1.5.0 corretti.")
