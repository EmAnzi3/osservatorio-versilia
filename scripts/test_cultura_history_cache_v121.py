#!/usr/bin/env python3
"""Regression gate: gli storici Cultura non devono restare bloccati in cache."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
SW = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PART = (ROOT / "assets" / "app-parts" / "03.txt").read_text(encoding="utf-8")
BUILD_BRAND = (ROOT / "scripts" / "build_static_brand.py").read_text(encoding="utf-8")
BUILD_SAFE = (ROOT / "scripts" / "build_static_safe.py").read_text(encoding="utf-8")
UX_HISTORY = (ROOT / "assets" / "ux-history.js").read_text(encoding="utf-8")

# La preview e la produzione non caricano assets/app.js: build_static.py crea
# assets/app-bundle.js e build_static_brand.py ne decide la query di cache-busting.
# Il gate deve quindi controllare soprattutto il bundle realmente referenziato dall'HTML.
assert "const VERSION='20260827-v121-history-ui2';" in APP, "Cache-buster app sorgente non aggiornato"
assert 'APP_BUNDLE_ASSET_VERSION = "20260827-v121-history-ui3"' in BUILD_BRAND, "Cache-buster del bundle di produzione non aggiornato"
assert 'rf\'src="\\1?v={APP_BUNDLE_ASSET_VERSION}"\'' in BUILD_BRAND, "La build non applica il cache-buster al bundle di produzione"
assert 'PWA_JS_REVISION = "catalog-v121"' in BUILD_BRAND, "Revisione PWA del catalogo non aggiornata"
assert 'HISTORY_ASSET_VERSION = "20260827-v121-history-ui5"' in BUILD_SAFE, "Cache-buster degli asset storici non aggiornato"
assert 'script in {"ux-history-core.js", "ux-history.js"}' in BUILD_SAFE, "ux-history.js non usa il cache-buster storico dedicato"
assert "const HOTFIX_VERSION = '20260827-v121-history-ui5';" in UX_HISTORY, "Fetch dati dell'enhancer storico non versionato"
assert UX_HISTORY.count("LIBRARY_HISTORY_KEYS.has(selected.key)") >= 2, "L'enhancer 7/7 deve lasciare intatti gli storici Cultura sia nel confronto sia nelle schede comunali"
assert "ov-pwa-20260827-v121-history-ui2" in SW, "Versione service worker non aggiornata"
assert "app-parts" in SW and "\\d{2}\\.txt" in SW, "I moduli .txt non sono gestiti esplicitamente dal service worker"
assert "networkFirst(request)" in SW, "Policy network-first assente"
assert "function libraryHistoryTableMarkup(metric)" in PART, "Renderer storico Cultura assente"
assert "Media comuni con dato" in PART, "Colonna media storica assente"
assert "libraryHistoryTableMarkup(metric)" in PART, "Storico non collegato al rendering del confronto"

print("Cache policy Cultura verificata: bundle e enhancer storici versionati; il renderer parziale del lotto non viene più sovrascritto dal contratto 7/7.")

assert "toolkit.viewShellMarkup(currentMarkup, historyMarkup, true, note)" in UX_HISTORY, "Lo switch Attuale/Storico Cultura deve essere ricostruito nel confronto"
assert "toolkit.viewShellMarkup(currentMarkup, historyMarkup, historyAvailable, note)" in UX_HISTORY, "Lo switch Attuale/Storico Cultura deve essere ricostruito nelle schede comunali"
