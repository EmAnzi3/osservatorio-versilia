#!/usr/bin/env python3
"""Controlli tecnici PWA senza UI di installazione."""
from __future__ import annotations

import contextlib
import json
import os
import re
import socket
import struct
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PWA_VERSION = "20260813-pwa8"


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
    manifest = json.loads((DIST / "site.webmanifest").read_text(encoding="utf-8"))
    require(manifest["name"] == "Osservatorio Versilia", "Nome manifest inatteso")
    require(manifest["display"] == "standalone", "La PWA non è in modalità standalone")
    require(manifest["start_url"] == "./" and manifest["scope"] == "./", "Scope/start_url PWA inattesi")
    require(manifest.get("id") == "./", "ID stabile della PWA mancante")

    expected_icons = {
        "pwa/icon-180.png": (180, 180),
        "pwa/icon-192.png": (192, 192),
        "pwa/icon-512.png": (512, 512),
        "pwa/icon-maskable-512.png": (512, 512),
    }
    for relative, expected in expected_icons.items():
        path = DIST / relative
        require(path.exists(), f"Icona PWA mancante: {relative}")
        require(png_size(path) == expected, f"Dimensioni errate per {relative}")

    icons = manifest.get("icons", [])
    require(any(icon.get("sizes") == "192x192" for icon in icons), "Icona 192 mancante")
    require(any(icon.get("sizes") == "512x512" for icon in icons), "Icona 512 mancante")
    require(any("maskable" in icon.get("purpose", "") for icon in icons), "Icona maskable mancante")

    service_worker = (DIST / "service-worker.js").read_text(encoding="utf-8")
    source_worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    source_version = re.search(r"const VERSION = ['\"]([^'\"]+)['\"]", source_worker)
    require(source_version is not None, "Versione cache PWA sorgente non riconoscibile")
    require(source_version.group(1) in service_worker, "La cache PWA pubblicata non coincide con la revisione sorgente")
    require("offline.html" in service_worker, "Fallback offline non configurato")
    require("networkFirst" in service_worker, "Strategia network-first assente")
    require("staleWhileRevalidate" in service_worker, "Strategia cache asset assente")

    pwa_js = (DIST / "assets" / "pwa.js").read_text(encoding="utf-8")
    require("navigator.serviceWorker.register" in pwa_js, "Registrazione service worker assente")
    for forbidden in (
        "beforeinstallprompt",
        "pwa-install-button",
        "pwa-install-callout",
        "pwa-install-dialog",
        "Come installare",
        "Installa app",
    ):
        require(forbidden not in pwa_js, f"UI installazione ancora presente nel runtime: {forbidden}")

    for page in (
        DIST / "index.html",
        DIST / "confronta" / "demografia" / "index.html",
        DIST / "comuni" / "massarosa" / "index.html",
        DIST / "progetto" / "index.html",
    ):
        text = page.read_text(encoding="utf-8")
        require(f"assets/pwa.css?v={PWA_VERSION}" in text, f"CSS PWA assente in {page}")
        require(f"assets/pwa.js?v={PWA_VERSION}&rev=install-ui-off" in text,
                f"JS PWA non forzato alla versione senza UI in {page}")
        require(f"site.webmanifest?v={PWA_VERSION}" in text, f"Manifest non versionato in {page}")
        require("apple-mobile-web-app-capable" in text, f"Meta iOS assente in {page}")

    offline = (DIST / "offline.html").read_text(encoding="utf-8")
    require("Sei offline" in offline and "Riprova" in offline, "Pagina offline incompleta")


def verify_no_install_ui(page, context: str) -> None:
    page.wait_for_selector(".site-header")
    require(page.locator(".pwa-install-button").count() == 0, f"Pulsante installazione presente: {context}")
    require(page.locator(".pwa-install-callout").count() == 0, f"Callout installazione presente: {context}")
    require(page.locator("#pwa-install-dialog").count() == 0, f"Dialog installazione presente: {context}")


def browser_checks() -> None:
    chromium_path = os.environ.get("CHROMIUM_PATH")
    launch_args: dict[str, object] = {"headless": True}
    if chromium_path:
        launch_args["executable_path"] = chromium_path

    with server(DIST) as base, sync_playwright() as p:
        browser = p.chromium.launch(**launch_args)

        desktop = browser.new_context(viewport={"width": 1280, "height": 900})
        page = desktop.new_page()
        page.goto(base, wait_until="networkidle")
        verify_no_install_ui(page, "desktop home")
        registration = page.evaluate("navigator.serviceWorker?.controller !== undefined")
        require(registration is True, "API service worker non disponibile nel contesto di test")
        desktop.close()

        android_ua = (
            "Mozilla/5.0 (Linux; Android 16; SM-S942B) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/150.0.0.0 Mobile Safari/537.36"
        )
        mobile = browser.new_context(
            viewport={"width": 390, "height": 844}, user_agent=android_ua, is_mobile=True, has_touch=True
        )
        mobile_page = mobile.new_page()
        mobile_page.goto(base, wait_until="networkidle")
        verify_no_install_ui(mobile_page, "Android home")
        mobile_page.goto(base + "comuni/massarosa/", wait_until="networkidle")
        verify_no_install_ui(mobile_page, "Android scheda comune")
        mobile.close()

        browser.close()


def main() -> None:
    static_checks()
    browser_checks()
    print("PWA verificata: supporto tecnico/offline attivo, UI di installazione assente.")


if __name__ == "__main__":
    main()
