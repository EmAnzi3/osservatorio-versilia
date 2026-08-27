#!/usr/bin/env python3
"""Regression gate: gli storici Cultura non devono restare bloccati in cache."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PART = (ROOT / "assets" / "app-parts" / "03.txt").read_text(encoding="utf-8")

assert "const VERSION='20260827-v121-history-ui2';" in APP, "Cache-buster app non aggiornato"
assert "ov-pwa-20260827-v121-history-ui2" in SW, "Versione service worker non aggiornata"
assert "app-parts" in SW and "\\d{2}\\.txt" in SW, "I moduli .txt non sono gestiti esplicitamente dal service worker"
assert "networkFirst(request)" in SW, "Policy network-first assente"
assert "function libraryHistoryTableMarkup(metric)" in PART, "Renderer storico Cultura assente"
assert "Media comuni con dato" in PART, "Colonna media storica assente"
assert "libraryHistoryTableMarkup(metric)" in PART, "Storico non collegato al rendering del confronto"

print("Cache policy Cultura verificata: app-parts versionati e network-first, renderer storico presente.")
