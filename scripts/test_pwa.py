#!/usr/bin/env python3
"""Controlli statici e browser della PWA di Osservatorio Versilia."""
from __future__ import annotations

import contextlib
import json
import os
import socket
import struct
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PWA_VERSION = "20260807-pwa1"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return


@contextlib.contextmanager
def server(directory: Path):
    old = Path.cwd()
    os.chdir(directory)
    try:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        httpd = ThreadingHTTPServer(("127.0.0.1", port), QuietHandler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}/"
        finally:
            httpd.shutdown()
            thread.join(timeout=5)
    finally:
        os.chdir(old)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    require(data[:8] == b"\x89PNG\r\n\x1a\n", f"PNG non valido: {path}")
    return struct.unpack(">II", data[16:24])


def static_checks() -> None:
    manifest_path = DIST / "site.webmanifest"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    require(manifest["name"] == "Osservatorio Versilia", "Nome manifest inatteso")
    require(manifest["display"] == "standalone", "La PWA non è in modalità standalone")
    require(manifest["start_url"] == "./" and manifest["scope"] == "./", "Scope/start_url PWA inattesi")
    require(manifest.get("id") == "./", "ID stabile della PWA mancante")

    icon_expectations = {
        "pwa/icon-180.png": (180, 180),
        "pwa/icon-192.png": (192, 192),
        "pwa/icon-512.png": (512, 512),
        "pwa/icon-maskable-512.png": (512, 512),
    }
    for relative, expected in icon_expectations.items():
        path = DIST / relative
        require(path.exists(), f"Icona PWA mancante: {relative}")
        actual = png_size(path)
        require(actual == expected, f"Dimensioni errate per {relative}: {actual}")

    icons = manifest.get("icons", [])
    require(any(icon.get("sizes") == "192x192" for icon in icons), "Icona 192 nel manifest mancante")
    require(any(icon.get("sizes") == "512x512" and icon.get("purpose") == "any" for icon in icons), "Icona 512 nel manifest mancante")
    require(any("maskable" in icon.get("purpose", "") for icon in icons), "Icona maskable nel manifest mancante")

    service_worker = (DIST / "service-worker.js").read_text(encoding="utf-8")
    require("offline.html" in service_worker, "Fallback offline non configurato")
    require("networkFirst" in service_worker, "Strategia network-first non configurata")
    require("staleWhileRevalidate" in service_worker, "Strategia cache asset non configurata")
    require("data/site-data.json" in service_worker, "Politica dati del service worker non esplicita")

    pwa_js = (DIST / "assets" / "pwa.js").read_text(encoding="utf-8")
    require("beforeinstallprompt" in pwa_js, "Prompt installazione Android/desktop mancante")
    require("Aggiungi alla schermata Home" in pwa_js, "Istruzioni iOS mancanti")
    require("Installa app" in pwa_js, "Istruzioni fallback browser mancanti")
    require("serviceWorker.register" in pwa_js, "Registrazione service worker mancante")

    pages = (
        DIST / "index.html",
        DIST / "confronta" / "demografia" / "index.html",
        DIST / "comuni" / "massarosa" / "index.html",
        DIST / "progetto" / "index.html",
    )
    for page in pages:
        text = page.read_text(encoding="utf-8")
        require(f"assets/pwa.css?v={PWA_VERSION}" in text, f"CSS PWA assente in {page}")
        require(f"assets/pwa.js?v={PWA_VERSION}" in text, f"JS PWA assente in {page}")
        require("apple-mobile-web-app-capable" in text, f"Meta iOS assente in {page}")
        require("apple-mobile-web-app-title" in text, f"Titolo app iOS assente in {page}")
        require("rel=\"apple-touch-icon\"" in text, f"Apple touch icon assente in {page}")
        require(f"site.webmanifest?v={PWA_VERSION}" in text, f"Manifest PWA non versionato in {page}")

    offline = (DIST / "offline.html").read_text(encoding="utf-8")
    require("Sei offline" in offline and "Riprova" in offline, "Pagina offline incompleta")


def browser_checks() -> None:
    chromium_path = os.environ.get("CHROMIUM_PATH")
    launch_args = {"headless": True}
    if chromium_path:
        launch_args["executable_path"] = chromium_path

    with server(DIST) as base, sync_playwright() as p:
        browser = p.chromium.launch(**launch_args)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        page.goto(base, wait_until="networkidle")
        page.wait_for_selector(".pwa-install-callout")
        page.wait_for_selector(".site-header .pwa-install-button")
        require(page.locator(".site-header .pwa-install-button").count() == 1, "Pulsante installazione header duplicato")
        callout = page.locator(".pwa-install-callout").inner_text().lower()
        require("disponibile anche come app" in callout, "Richiamo PWA in home non esplicito")
        require("porta l'osservatorio sul telefono" in callout, "Messaggio PWA in home inatteso")

        sw_scope = page.evaluate(
            """async () => {
              if (!('serviceWorker' in navigator)) return '';
              const registration = await navigator.serviceWorker.ready;
              return registration.scope;
            }"""
        )
        require(sw_scope == base, f"Scope service worker inatteso: {sw_scope!r}, atteso {base!r}")

        page.goto(base + "comuni/massarosa/", wait_until="networkidle")
        page.wait_for_selector(".site-header .pwa-install-button")
        require(page.locator(".pwa-install-callout").count() == 0, "Callout home presente in una pagina interna")

        context.close()
        browser.close()


def main() -> None:
    static_checks()
    browser_checks()
    print("PWA verificata: manifest, icone, service worker, offline e installazione visibile nel sito.")


if __name__ == "__main__":
    main()
