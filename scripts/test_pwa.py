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
PWA_VERSION = "20260807-pwa6"


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
    require("ov-pwa-20260807-6" in service_worker, "Versione cache PWA non aggiornata")
    require("offline.html" in service_worker, "Fallback offline non configurato")
    require("networkFirst" in service_worker, "Strategia network-first assente")
    require("staleWhileRevalidate" in service_worker, "Strategia cache asset assente")
    require("\\.(?:js|css)$" in service_worker, "JS/CSS non protetti da network-first")
    require("site.webmanifest" in service_worker, "Manifest non aggiornato network-first")

    pwa_js = (DIST / "assets" / "pwa.js").read_text(encoding="utf-8")
    require("beforeinstallprompt" in pwa_js, "Evento installazione mancante")
    require("isAndroid" in pwa_js and "isChromeAndroid" in pwa_js, "Rilevamento Android incompleto")
    require("Installa nella schermata App" in pwa_js, "Istruzioni Samsung mancanti")
    require("Aggiungere alla schermata Home?" in pwa_js, "Distinzione shortcut Android mancante")
    require("il sito non può forzare un WebAPK" in pwa_js, "Limite WebAPK non dichiarato")
    require("new MutationObserver(scheduleMount)" not in pwa_js,
            "Il bootstrap PWA osserva ancora ricorsivamente l'intero DOM")
    require("keepHeaderInstallButtonAlive" in pwa_js,
            "Manca la protezione contro il remount dell'header")
    require("observer.observe(mount, { childList: true })" in pwa_js,
            "La protezione header non è limitata al contenitore diretto")

    for page in (
        DIST / "index.html",
        DIST / "confronta" / "demografia" / "index.html",
        DIST / "comuni" / "massarosa" / "index.html",
        DIST / "progetto" / "index.html",
    ):
        text = page.read_text(encoding="utf-8")
        require(f"assets/pwa.css?v={PWA_VERSION}" in text, f"CSS PWA assente in {page}")
        require(f"assets/pwa.js?v={PWA_VERSION}" in text, f"JS PWA assente in {page}")
        require(f"site.webmanifest?v={PWA_VERSION}" in text, f"Manifest non versionato in {page}")
        require("apple-mobile-web-app-capable" in text, f"Meta iOS assente in {page}")

    offline = (DIST / "offline.html").read_text(encoding="utf-8")
    require("Sei offline" in offline and "Riprova" in offline, "Pagina offline incompleta")


def simulate_install_prompt(page, marker: str) -> None:
    page.evaluate(
        f"""() => {{
          window.{marker} = false;
          const event = new Event('beforeinstallprompt', {{ cancelable: true }});
          Object.defineProperty(event, 'prompt', {{
            value: () => {{ window.{marker} = true; return Promise.resolve(); }}
          }});
          Object.defineProperty(event, 'userChoice', {{
            value: Promise.resolve({{ outcome: 'dismissed' }})
          }});
          window.dispatchEvent(event);
        }}"""
    )


def verify_no_idle_pwa_mutation(page) -> None:
    page.evaluate(
        """() => {
          window.__ovPwaMutations = 0;
          const target = document.querySelector('[data-pwa-install-action] span');
          window.__ovObserver = new MutationObserver(records => {
            window.__ovPwaMutations += records.length;
          });
          if (target) window.__ovObserver.observe(target, { childList: true, subtree: true, characterData: true });
        }"""
    )
    page.wait_for_timeout(300)
    mutations = page.evaluate("window.__ovPwaMutations")
    page.evaluate("window.__ovObserver?.disconnect()")
    require(mutations == 0, f"Bootstrap PWA continua a mutare il DOM a riposo: {mutations} mutazioni")


def verify_header_button_survives_remount(page) -> None:
    page.wait_for_selector(".site-header .pwa-install-button")
    page.evaluate(
        """() => {
          const mount = document.getElementById('site-header-mount');
          const header = mount?.querySelector('.site-header');
          if (!mount || !header) throw new Error('Header mount non trovato');
          const clone = header.cloneNode(true);
          clone.querySelector('[data-pwa-header-install]')?.remove();
          mount.replaceChildren(clone);
        }"""
    )
    page.wait_for_selector(".site-header .pwa-install-button")
    require(page.locator(".site-header .pwa-install-button").count() == 1,
            "Il pulsante installazione non è stato ripristinato dopo il remount dell'header")


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
        page.wait_for_selector(".pwa-install-callout")
        page.wait_for_selector(".site-header .pwa-install-button")
        require(page.locator(".site-header .pwa-install-button").count() == 1, "Pulsante header duplicato")
        verify_header_button_survives_remount(page)
        verify_no_idle_pwa_mutation(page)
        simulate_install_prompt(page, "__ovDesktopPrompt")
        page.wait_for_timeout(50)
        action = page.locator(".pwa-callout-action")
        require("installa app" in action.inner_text().lower(), "Desktop non passa allo stato installabile")
        action.click()
        page.wait_for_timeout(100)
        require(page.evaluate("window.__ovDesktopPrompt === true"), "Desktop non usa il prompt nativo")
        desktop.close()

        chrome_ua = (
            "Mozilla/5.0 (Linux; Android 16; SM-S942B) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/150.0.0.0 Mobile Safari/537.36"
        )
        chrome = browser.new_context(
            viewport={"width": 390, "height": 844}, user_agent=chrome_ua, is_mobile=True, has_touch=True
        )
        chrome_internal = chrome.new_page()
        chrome_internal.goto(base + "comuni/massarosa/", wait_until="networkidle")
        verify_header_button_survives_remount(chrome_internal)
        header_action = chrome_internal.locator(".site-header .pwa-install-button")
        require(header_action.is_visible(), "Pulsante installazione non visibile nell'header mobile")
        header_action.tap()
        chrome_internal.wait_for_selector("#pwa-install-dialog[open]")
        chrome_internal.locator(".pwa-dialog-close").tap()
        chrome_internal.close()

        # Nuovo tab nello stesso contesto: il Service Worker resta attivo, ma il
        # test home non eredita il DOM volutamente clonato nel test precedente.
        chrome_page = chrome.new_page()
        chrome_page.goto(base, wait_until="networkidle")
        chrome_page.wait_for_selector(".pwa-install-callout")
        chrome_action = chrome_page.locator(".pwa-callout-action")
        require("come installare" in chrome_action.inner_text().lower(), "CTA Chrome Android ambiguo")
        simulate_install_prompt(chrome_page, "__ovChromePrompt")
        chrome_action.tap()
        chrome_page.wait_for_selector("#pwa-install-dialog[open]")
        require(chrome_page.evaluate("window.__ovChromePrompt === false"),
                "Il sito ha invocato direttamente il prompt Android")
        dialog = chrome_page.locator("#pwa-install-dialog").inner_text().lower()
        require("installa con chrome" in dialog, "Istruzioni Chrome Android assenti")
        require("riquadro 1×1" in dialog, "Shortcut 1×1 non spiegato")
        require("non può forzare un webapk" in dialog, "Limite WebAPK non spiegato")
        verify_no_idle_pwa_mutation(chrome_page)
        chrome.close()

        samsung_ua = (
            "Mozilla/5.0 (Linux; Android 16; SM-S942B) AppleWebKit/537.36 "
            "(KHTML, like Gecko) SamsungBrowser/28.0 Chrome/130.0.0.0 Mobile Safari/537.36"
        )
        samsung = browser.new_context(
            viewport={"width": 390, "height": 844}, user_agent=samsung_ua, is_mobile=True, has_touch=True
        )
        samsung_page = samsung.new_page()
        samsung_page.goto(base, wait_until="networkidle")
        samsung_page.wait_for_selector(".pwa-install-callout")
        samsung_action = samsung_page.locator(".pwa-callout-action")
        require("come installare" in samsung_action.inner_text().lower(), "CTA Samsung ambiguo")
        simulate_install_prompt(samsung_page, "__ovSamsungPrompt")
        samsung_action.tap()
        samsung_page.wait_for_selector("#pwa-install-dialog[open]")
        require(samsung_page.evaluate("window.__ovSamsungPrompt === false"),
                "Il sito ha invocato direttamente il prompt Samsung")
        samsung_dialog = samsung_page.locator("#pwa-install-dialog").inner_text().lower()
        require("installa nella schermata app" in samsung_dialog, "Percorso Samsung app assente")
        require("riquadro 1×1" in samsung_dialog, "Shortcut Samsung non distinto")
        samsung.close()

        browser.close()


def main() -> None:
    static_checks()
    browser_checks()
    print("PWA verificata: pulsante header persistente, nessun loop DOM e istruzioni Android corrette.")


if __name__ == "__main__":
    main()
