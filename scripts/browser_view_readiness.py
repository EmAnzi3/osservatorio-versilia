"""Read-only readiness for client-rendered, prerendered OV test views."""
from urllib.parse import parse_qs, urlparse

def goto_reading_view(page, url):
    # Check the selected view and fonts, rather than unrelated photo traffic.
    if not getattr(page, "_reading_hydration_observer", False):
        page.add_init_script("""(() => {
          let initial = null;
          window.__readingClientRendered = false;
          const observer = new MutationObserver(() => {
            const child = document.querySelector('#app')?.firstElementChild;
            if (!initial && child) initial = child;
            else if (initial && child && child !== initial) {
              window.__readingClientRendered = true;
              observer.disconnect();
            }
          });
          observer.observe(document, {childList:true, subtree:true});
        })()""")
        page._reading_hydration_observer = True
    # Global load/DOMContentLoaded can include resources outside the tested view.
    # App rendering, selected metric and fonts are checked explicitly below.
    response = page.goto(url, wait_until="commit")
    assert response is not None and response.ok, f"Navigation failed: {url}"
    # start() replaces #app only after catalog and optional climate reads.
    page.wait_for_function("window.__readingClientRendered === true")
    metric = parse_qs(urlparse(url).query).get("indicatore", [None])[0]
    if metric:
        page.locator(f'[data-metric="{metric}"].active').first.wait_for(state="visible")
        page.locator(".reading-scale").first.wait_for(state="visible")
    elif urlparse(url).path.rstrip("/").endswith("progetto"):
        page.locator("#sistema-territoriale").wait_for(state="visible")
    else:
        page.locator("#home-explorer .comparison-dot").first.wait_for(state="visible")
    page.wait_for_function("document.fonts.status === 'loaded'", timeout=15000)
    return response

