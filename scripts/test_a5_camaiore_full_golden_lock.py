#!/usr/bin/env python3
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import io
import json
import math
import re
from pathlib import Path
from urllib.parse import urljoin

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

from test_a5_camaiore_rollout import EXPECTED, VIEWPORTS, choose, discover, go, stable, state
from a3_publication_gap_audit import _finite, _valid_series

APPROVED_COMMIT = "5aaf159870912eb49bffbd044963549bfb920150"
EXPECTED_TOWN_ORDER = (
    "Camaiore",
    "Forte dei Marmi",
    "Massarosa",
    "Pietrasanta",
    "Seravezza",
    "Stazzema",
    "Viareggio",
)


def town_nav_order(page) -> list[str]:
    return page.evaluate("""() => [
      ...document.querySelectorAll('.town-context-nav .context-nav-row:first-child .context-nav-links > a')
    ].map(el => (el.textContent || '').trim())""")


def normalize_baseline_town_order(page) -> None:
    result = page.evaluate("""expected => {
      const host = document.querySelector('.town-context-nav .context-nav-row:first-child .context-nav-links');
      if (!host) return {ok:false, reason:'host-missing'};
      const links = [...host.querySelectorAll(':scope > a')];
      const byName = new Map(links.map(link => [(link.textContent || '').trim(), link]));
      const missing = expected.filter(name => !byName.has(name));
      if (missing.length) return {ok:false, reason:'links-missing', missing};
      expected.forEach(name => host.append(byName.get(name)));
      return {ok:true};
    }""", list(EXPECTED_TOWN_ORDER))
    if not result.get("ok"):
        raise AssertionError(f"Camaiore baseline town-nav normalization failed: {result}")


REVIEW_METRICS = {
    "territorialClassification",
    "population",
    "incomeDistribution",
    "employmentRate",
    "diplomaPlus",
    "lifeExpectancy",
    "outsideMunicipality",
    "roadSafety",
    "omiResidential",
    "landCoverProfile",
    "landslideExposure",
    "climateTemperatureTrend50y",
    "drinkingWaterQuality",
    "financialDebtProfile",
    "libraryLoansPerResident",
    "pnrrFunding",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_state(value):
    """Normalize browser sentinels and the rollout implementation marker only."""
    if isinstance(value, float) and not math.isfinite(value):
        return "__NONFINITE__"
    if isinstance(value, dict):
        normalized = {key: canonical_state(item) for key, item in value.items()}
        if isinstance(normalized.get("classes"), list):
            normalized["classes"] = [
                name for name in normalized["classes"]
                if name != "a5-municipal-rollout"
            ]
        return normalized
    if isinstance(value, list):
        return [canonical_state(item) for item in value]
    return value


def pixel_difference(baseline: bytes, current: bytes, threshold: int = 3) -> dict:
    first = Image.open(io.BytesIO(baseline)).convert("RGB")
    second = Image.open(io.BytesIO(current)).convert("RGB")
    if first.size != second.size:
        return {
            "same_size": False,
            "baseline_size": first.size,
            "current_size": second.size,
            "ratio": 1.0,
        }
    diff = ImageChops.difference(first, second)
    total = first.size[0] * first.size[1]
    changed = sum(1 for pixel in diff.getdata() if max(pixel) > threshold)
    return {
        "same_size": True,
        "baseline_size": first.size,
        "current_size": second.size,
        "changed": changed,
        "total": total,
        "ratio": changed / total if total else 0.0,
    }


def public_history_state(page, shell_selector='#town-topic > .history-panel.a5-shared-chart .ux-view-shell') -> dict:
    return page.evaluate(
        """selector => {
          const shell=document.querySelector(selector);
          const button=shell?.querySelector('[data-view-mode="history"]');
          const pane=shell?.querySelector('[data-view-pane="history"]');
          const text=(pane?.textContent || '').trim();
          return {
            buttonExists:Boolean(button),
            paneExists:Boolean(pane),
            disabled:Boolean(button?.disabled),
            chartCount:pane?.querySelectorAll('.ux-history-chart, .ux-two-point-chart, .trend-chart, .history-chart, [data-history-chart], svg, canvas').length || 0,
            unavailable:Boolean(
              pane?.querySelector('.ux-history-unavailable')
              || /serie storica non disponibile/i.test(text)
            ),
            contentLength:text.length,
          };
        }""", shell_selector
    )


def verified_history_upgrade(baseline_state: dict, current_state: dict, base_page, cur_page) -> tuple[bool, dict]:
    baseline_shell = baseline_state.get("semantic", {}).get("financialShell", {})
    current_shell = current_state.get("semantic", {}).get("financialShell", {})
    if baseline_shell.get("historyChart") is not False or current_shell.get("historyChart") is not True:
        return False, {}

    normalized_current = json.loads(json.dumps(current_state))
    normalized_current["semantic"]["financialShell"]["historyChart"] = False
    if baseline_state != normalized_current:
        return False, {}

    baseline_dom = public_history_state(base_page)
    current_dom = public_history_state(cur_page)
    allowed = bool(
        baseline_dom["buttonExists"]
        and baseline_dom["paneExists"]
        and baseline_dom["disabled"]
        and current_dom["buttonExists"]
        and current_dom["paneExists"]
        and not current_dom["disabled"]
        and current_dom["chartCount"] >= 1
        and not current_dom["unavailable"]
        and current_dom["contentLength"] > 0
    )
    return allowed, {"baseline": baseline_dom, "current": current_dom}


def unchanged_current_rows(before: dict, after: dict) -> bool:
    """A3 adds series to rows/parts; every pre-existing level stays frozen."""
    def strip(value):
        if isinstance(value, dict):
            return {key: strip(item) for key, item in value.items()
                    if key not in {'series', 'a3History', 'componentSeries'}}
        if isinstance(value, list):
            return [strip(item) for item in value]
        return value
    rows_before, rows_after = before.get('rows', []), after.get('rows', [])
    return (len(rows_before) == len(rows_after) == 7
            and len({r.get('code') for r in rows_after}) == 7
            and strip(rows_before) == strip(rows_after)
            and strip(before.get('aggregate')) == strip(after.get('aggregate')))


def history_note_evidence(before: dict, after: dict) -> str | None:
    """Only the existing demographic selector's source-backed availability note."""
    if (after.get('meta', {}).get('compositeType') != 'demographicBreakdown'
            or not unchanged_current_rows(before, after)):
        return None
    available = []
    for part in after['rows'][0].get('parts', []):
        series = part.get('series', {})
        if len(series.get('years', [])) > 1:
            label = part.get('label')
            matching = [next((p for p in row.get('parts', []) if p.get('label') == label), {})
                        for row in after['rows']]
            histories = [p.get('series') or {} for p in matching]
            if any(not _valid_series(s) or not all(_finite(v) for v in s['values'])
                   or not all(len(str(y)) == 4 and str(y).isdigit() for y in s['years'])
                   or not s.get('sourceSnapshot', '').startswith('data/source-snapshots/')
                   for s in histories):
                return None
            if len(set.intersection(*(set(str(y) for y in s['years']) for s in histories))) < 2:
                return None
            available.append(label)
    if not available:
        return None
    default_key = after['meta'].get('defaultAge', '') + '|' + after['meta'].get('defaultGender', '')
    defaults = [next((p for p in row['parts'] if p.get('key') == default_key), {})
                for row in after['rows']]
    if all(len(part.get('series', {}).get('years', [])) > 1 for part in defaults):
        return 'Lo storico utilizza esclusivamente gli anni omogenei presenti per tutti e sette i comuni.'
    return ('Storico non acquisito per questa fascia e questo genere. Puoi consultarlo selezionando '
            + ' oppure '.join(available) + '.')


def verify_benchmark_dom(page, selector: str, metric: dict, town: str = 'Camaiore') -> dict:
    """Verify real enriched content before any screenshot-only normalization."""
    bench = metric['meta']['benchmark']
    row = next(r for r in metric['rows'] if r['town'] == town)
    expected = [{'label': town, 'value': row.get('benchmarkValue', row['value'])},
                {'label': 'Toscana', 'value': bench['tuscany']}]
    if bench.get('italy') is not None:
        expected.append({'label': 'Italia', 'value': bench['italy']})
    result = page.locator(selector).evaluate("""(host, expected) => {
      const section=host.querySelector('.benchmark-section');
      const cards=[...host.querySelectorAll('.benchmark-card')];
      const numeric=text=>{
        const match=String(text).match(/-?[\\d.]+(?:,\\d+)?/);
        if(!match)return null;
        return Number(match[0].replaceAll('.','').replace(',','.'));
      };
      const observations=cards.map((card,i)=>{
        const strong=card.querySelector('strong'), span=card.querySelector('span');
        const rect=card.getBoundingClientRect(), valueRect=strong?.getBoundingClientRect();
        const text=strong?.textContent||'';
        const decimals=(text.match(/,(\\d+)/)||[])[1]?.length||0;
        const value=numeric(text), wanted=expected.cards[i];
        return {label:span?.textContent.trim(),value,text,
          valid:Boolean(wanted && span?.textContent.trim()===wanted.label && value!==null
            && Math.abs(value-wanted.value)<=.5*Math.pow(10,-decimals)+1e-8
            && rect.width>0 && rect.height>0 && valueRect && valueRect.right<=rect.right+.5)};
      });
      return {ok:Boolean(section && !host.querySelector('[style]')
        && cards.length===expected.cards.length && observations.every(x=>x.valid)
        && host.querySelector('.overline')?.textContent.trim()===`Confronto omogeneo · ${expected.year}`
        && host.querySelector('.benchmark-note a')?.getAttribute('href')===expected.url
        && cards.slice(1).every(card=>card.querySelector('small')?.textContent===expected.source)),observations};
    }""", {'cards': expected, 'year': str(bench['year']), 'url': bench['url'], 'source': bench['source']})
    if not result['ok']:
        raise AssertionError(f'Enriched benchmark DOM invalid: {result}')
    return result


def native_benchmark_period(native: dict, source: dict) -> str:
    """Resolve only explicit reference-period fields or a uniquely dated native title."""
    if 'year' in native:
        return str(native['year'])
    periods = {str(value) for value in (native.get('schoolYear'), source.get('year'),
               source.get('schoolYear')) if value is not None}
    if not periods:
        titles = [source.get('title', ''), (source.get('source') or {}).get('title', '')]
        periods = {year for title in titles for year in re.findall(r'\bAnno\s+((?:19|20)\d{2})\b', title, re.I)}
    if len(periods) != 1:
        raise AssertionError(f'Native benchmark period absent or ambiguous: {periods}')
    return periods.pop()


@contextmanager
def approved_classification_toolbar(base_page, cur_page, before: dict, after: dict,
                                    *, comparison=False):
    """Project only the owner-approved toolbar on the immutable reference DOM."""
    if after.get('meta', {}).get('key') != 'territorialClassification':
        yield
        return
    reference = json.loads((Path(__file__).resolve().parents[1]
                           / 'ci/a5-approved-classification-toolbar.json').read_text())
    if (reference['approvedCommit'] != '896383d3180169ec905d5e2acdd6be48cc03a766'
            or hashlib.sha256((reference['compare']['html'] + reference['town']).encode()).hexdigest() != 'c58c8b2a3cb71b6329cd83197e6f5627c5935443f9ac03a0a57c54767b083c88'
            or reference['metric'] != after['meta']['key']
            or before != after):
        raise AssertionError('Classification approval/source identity changed')
    native = '.territorial-classification-shell' if comparison else '.territorial-classification-grid'
    if base_page.locator(native).inner_html() != cur_page.locator(native).inner_html():
        raise AssertionError('Classification native content changed')
    toolbar = cur_page.locator('#compare-bars .ux-view-toolbar' if comparison
                              else '#town-topic .a5-special-renderer-toolbar')
    actions = toolbar.locator(':scope > .data-actions')
    if toolbar.count() != 1 or not toolbar.is_visible() or actions.count() != 1:
        raise AssertionError('Classification canonical toolbar absent')
    for selector in ('[data-download]', '[data-print]', 'a[href*="/indicatori/"]'):
        control = actions.locator(selector)
        if control.count() != 1 or not control.is_visible():
            raise AssertionError('Classification canonical action absent: ' + selector)
        if selector == 'a[href*="/indicatori/"]':
            if control.evaluate('e=>new URL(e.href).pathname') != '/indicatori/classificazioni-territoriali/':
                raise AssertionError('Classification indicator link changed')
        else:
            if control.evaluate("e=>getComputedStyle(e,'::before').backgroundImage") == 'none':
                raise AssertionError('Classification action icon absent: ' + selector)
    base_page.evaluate("""({reference,comparison}) => {
      if (window.__approvedClassificationRestore) throw new Error('Classification projection nested');
      if (comparison) {
        const host=document.querySelector('#compare-bars');
        const children=[...host.childNodes];
        const actions=document.querySelector('.compare-panel-heading > .data-actions');
        const parent=actions?.parentNode,next=actions?.nextSibling;
        actions?.remove();
        const native=host.querySelector('.territorial-classification-shell').innerHTML;
        host.innerHTML=reference.compare.html;
        host.querySelector('.territorial-classification-shell').innerHTML=native;
        window.__approvedClassificationRestore=()=>{host.replaceChildren(...children);if(actions)parent.insertBefore(actions,next)};
      } else {
        const chart=document.querySelector('#town-topic > .history-panel.a5-shared-chart');
        const actions=document.querySelector('#town-topic > .town-data-actions.a5-town-fallback-actions');
        if (!actions || chart.querySelector('.a5-special-renderer-toolbar')) throw new Error('Unexpected classification baseline');
        const parent=actions.parentNode,next=actions.nextSibling;
        chart.insertAdjacentHTML('afterbegin',reference.town);
        const toolbar=chart.firstElementChild;
        actions.remove();
        window.__approvedClassificationRestore=()=>{toolbar.remove();parent.insertBefore(actions,next)};
      }
    }""", {'reference': reference, 'comparison': comparison})
    try:
        yield
    finally:
        base_page.evaluate("""() => {
          window.__approvedClassificationRestore();
          delete window.__approvedClassificationRestore;
          window.scrollTo(0,0);
        }""")


@contextmanager
def screenshot_enrichment_normalization(base_page, cur_page, before: dict, after: dict,
                                        source_evidence: dict,
                                        benchmark_selector='#town-topic > .town-benchmark-host',
                                        note_selector='#town-topic > .history-panel.a5-shared-chart > .ux-view-shell > .ux-view-note',
                                        benchmark_verifier=None,
                                        diagnostic_dir: Path | None = None):
    """Replace only validated data additions for capture; restore real DOM finally."""
    restorations = []
    allowed = []
    try:
        benchmark = after.get('meta', {}).get('benchmark')
        snapshot_path = (benchmark or {}).get('sourceSnapshot')
        source = source_evidence.get(snapshot_path)
        native = ((source or {}).get('benchmarks', {}).get(after['meta']['key'])
                  or (source or {}).get('benchmark'))
        if (before.get('meta', {}).get('benchmark') is None and benchmark
                and unchanged_current_rows(before, after) and native
                and base_page.locator(benchmark_selector).count() == 1
                and cur_page.locator(benchmark_selector).count() == 1
                and base_page.locator(benchmark_selector + ' > .benchmark-unavailable').count() == 1):
            # Snapshot and public metadata must expose exactly the same acquired scopes/period.
            for field in ('year', 'tuscany', 'italy'):
                if field == 'year':
                    valid = native_benchmark_period(native, source) == str(benchmark.get(field))
                else:
                    valid = native.get(field) == benchmark.get(field)
                if not valid:
                    raise AssertionError(f'Benchmark source mismatch: {field}')
            (benchmark_verifier or verify_benchmark_dom)(cur_page, benchmark_selector, after)
            old_html = base_page.locator(benchmark_selector).inner_html()
            current_html = cur_page.locator(benchmark_selector).inner_html()
            # Render the same source-backed cards under the immutable baseline CSS.
            # This protects the new panel's typography/layout as well as old content.
            try:
                base_page.locator(benchmark_selector).evaluate('(host,html)=>host.innerHTML=html', current_html)
                baseline_transform = base_page.locator(benchmark_selector).evaluate('(node)=>getComputedStyle(node).transform')
                current_transform = cur_page.locator(benchmark_selector).evaluate('(node)=>getComputedStyle(node).transform')
                if baseline_transform != current_transform:
                    raise AssertionError(f"Enriched benchmark transform changed: {after['meta']['key']}")
                before_image = base_page.locator(benchmark_selector).screenshot(animations='disabled')
                after_image = cur_page.locator(benchmark_selector).screenshot(animations='disabled')
                diff = pixel_difference(before_image, after_image)
                if not diff['same_size'] or diff['ratio'] > .0005:
                    def styles(page):
                        return page.locator(benchmark_selector).evaluate("""host => {
                          const fields=['display','fontFamily','fontSize','fontWeight','fontStyle','lineHeight',
                            'letterSpacing','color','backgroundColor','borderColor','padding','margin',
                            'width','height','position','top','left','transform','boxShadow','textDecoration','alignItems'];
                          return [host,...host.querySelectorAll('*')].map(node=>{
                            const cs=getComputedStyle(node),r=node.getBoundingClientRect();
                            return {tag:node.tagName,classes:node.className,text:node.textContent.trim().slice(0,120),
                              hover:node.matches(':hover'),style:Object.fromEntries(fields.map(k=>[k,cs[k]])),
                              rect:{x:r.x,y:r.y,width:r.width,height:r.height}};
                          });
                        }""")
                    detail = {'metric': after['meta']['key'], 'pixelDiff': diff,
                              'baseline': styles(base_page), 'current': styles(cur_page)}
                    baseline_nodes, current_nodes = detail['baseline'], detail['current']
                    def same_native_geometry():
                        if len(baseline_nodes) != len(current_nodes):
                            return False
                        origins = [nodes[0]['rect'] for nodes in (baseline_nodes, current_nodes)]
                        for first, second in zip(baseline_nodes, current_nodes, strict=True):
                            if any(first[key] != second[key] for key in ('tag', 'classes', 'text', 'hover', 'style')):
                                return False
                            for field in ('width', 'height'):
                                if first['rect'][field] != second['rect'][field]:
                                    return False
                            for field in ('x', 'y'):
                                if abs((first['rect'][field] - origins[0][field])
                                       - (second['rect'][field] - origins[1][field])) > 1e-6:
                                    return False
                        return (baseline_nodes[0]['style']['transform'] == 'none'
                                and baseline_nodes[0]['style']['position'] == 'static')
                    if same_native_geometry():
                        # Different page heights may center screenshots at fractions of
                        # a pixel. Snap only an otherwise identical projected panel to
                        # the pixel grid; never canonicalize a CSS/layout difference.
                        original_styles = []
                        try:
                            for page, nodes in ((base_page, baseline_nodes), (cur_page, current_nodes)):
                                host = page.locator(benchmark_selector)
                                original_styles.append((host, host.get_attribute('style')))
                                fraction = nodes[0]['rect']['y'] % 1
                                host.evaluate("""(node,fraction)=>{
                                  node.style.setProperty('position','relative','important');
                                  node.style.setProperty('top',`${-fraction}px`,'important');
                                }""", fraction)
                            aligned_before = base_page.locator(benchmark_selector).screenshot(animations='disabled')
                            aligned_after = cur_page.locator(benchmark_selector).screenshot(animations='disabled')
                            aligned_diff = pixel_difference(aligned_before, aligned_after)
                        finally:
                            for host, value in reversed(original_styles):
                                host.evaluate("(node,value)=>value===null?node.removeAttribute('style'):node.setAttribute('style',value)", value)
                        detail['pixelGridDiff'] = aligned_diff
                        if aligned_diff['same_size'] and aligned_diff['ratio'] <= .0005:
                            diff = aligned_diff
                    if diagnostic_dir is not None:
                        diagnostic_dir.mkdir(parents=True, exist_ok=True)
                        name = f"benchmark-projection-{after['meta']['key']}-{cur_page.viewport_size['width']}"
                        (diagnostic_dir / (name + '-baseline.png')).write_bytes(before_image)
                        (diagnostic_dir / (name + '-current.png')).write_bytes(after_image)
                        (diagnostic_dir / (name + '-styles.json')).write_text(json.dumps(detail, indent=2) + '\n')
                    if not diff['same_size'] or diff['ratio'] > .0005:
                        raise AssertionError(f"Enriched benchmark styling changed: {after['meta']['key']}: {diff}")
            finally:
                base_page.locator(benchmark_selector).evaluate('(host,html)=>host.innerHTML=html', old_html)
            restorations.append((benchmark_selector, current_html, 'html'))
            cur_page.locator(benchmark_selector).evaluate('(host, html) => host.innerHTML=html', old_html)
            allowed.append({'kind': 'source-backed-benchmark', 'snapshot': snapshot_path})
        note = history_note_evidence(before, after)
        if note == 'Lo storico utilizza esclusivamente gli anni omogenei presenti per tutti e sette i comuni.' and benchmark_verifier is None:
            note = 'Nello storico il comune aperto è evidenziato; dalla legenda puoi mettere in primo piano un altro territorio.'
        if (note and base_page.locator(note_selector).count() == 1
                and cur_page.locator(note_selector).count() == 1
                and cur_page.locator(note_selector).inner_text() == note
                and base_page.locator(note_selector).inner_text()
                    == 'Per questo indicatore non esistono almeno due anni omogenei per tutti e sette i comuni.'):
            for part in after['rows'][0]['parts']:
                path = part.get('series', {}).get('sourceSnapshot')
                if path and path not in source_evidence:
                    raise AssertionError(f'Missing historical source evidence: {path}')
            old_text = base_page.locator(note_selector).inner_text()
            current_text = cur_page.locator(note_selector).inner_text()
            base_button = base_page.locator(note_selector).locator('..').locator('[data-view-mode="history"]')
            cur_button = cur_page.locator(note_selector).locator('..').locator('[data-view-mode="history"]')
            if (base_button.count() == cur_button.count() == 1
                    and base_button.is_disabled() and not cur_button.is_disabled()):
                current_dom = public_history_state(cur_page, note_selector.rsplit(' > ', 1)[0])
                if (not current_dom['paneExists'] or current_dom['chartCount'] < 1
                        or current_dom['unavailable']):
                    raise AssertionError('Source-backed default history chart missing')
                # The thematic lock validates its live native history before
                # temporarily restoring the button during workspace capture.
                if benchmark_verifier is None:
                    history_button_selector = note_selector.rsplit(' > ', 1)[0] + ' [data-view-mode="history"]'
                    restorations.append((history_button_selector, False, 'disabled'))
                    cur_button.evaluate('(node)=>node.disabled=true')
            restorations.append((note_selector, current_text, 'text'))
            cur_page.locator(note_selector).evaluate('(node,text)=>node.textContent=text', old_text)
            allowed.append({'kind': 'source-backed-history-note', 'note': note})
        yield allowed
    finally:
        for selector, value, kind in reversed(restorations):
            cur_page.locator(selector).evaluate(
                '(node, value) => node.' + {'html': 'innerHTML', 'text': 'textContent',
                                           'disabled': 'disabled'}[kind] + '=value', value)


def compare_screenshot(base_page, cur_page, selector: str, key: str, folder: Path, failures: list[dict]) -> None:
    base_loc = base_page.locator(selector)
    cur_loc = cur_page.locator(selector)
    if base_loc.count() != 1 or cur_loc.count() != 1:
        failures.append({
            "key": key,
            "kind": "golden-region-missing",
            "selector": selector,
            "baselineCount": base_loc.count(),
            "currentCount": cur_loc.count(),
        })
        return
    before = base_loc.screenshot(animations="disabled")
    after = cur_loc.screenshot(animations="disabled")
    diff = pixel_difference(before, after)
    if (not diff["same_size"]) or diff["ratio"] > 0.0005:
        bpath = folder / f"{key}-baseline.png"
        cpath = folder / f"{key}-current.png"
        bpath.write_bytes(before)
        cpath.write_bytes(after)
        failures.append({
            "key": key,
            "kind": "camaiore-visual-golden-diff",
            "selector": selector,
            "pixelDiff": diff,
            "baselineSha256": digest(before),
            "currentSha256": digest(after),
            "baselineImage": bpath.name,
            "currentImage": cpath.name,
        })


def load_enrichment_evidence(request, baseline_base: str, current_base: str):
    """Read effective public catalogs and the cited frozen sources once per run."""
    def read(base, path):
        response = request.get(urljoin(base, path))
        if not response.ok:
            raise AssertionError(f'Golden enrichment evidence unavailable: {path}')
        return response.json()
    before = read(baseline_base, 'data/site-data.json')['metrics']
    after = read(current_base, 'data/site-data.json')['metrics']
    paths = set()
    for metric in after.values():
        benchmark = metric.get('meta', {}).get('benchmark') or {}
        if benchmark.get('sourceSnapshot'):
            paths.add(benchmark['sourceSnapshot'])
        for row in metric.get('rows', []):
            row_path = (row.get('series') or {}).get('sourceSnapshot')
            if row_path:
                paths.add(row_path)
            for part in row.get('parts', []):
                path = (part.get('series') or {}).get('sourceSnapshot')
                if path:
                    paths.add(path)
    sources = {}
    for path in paths:
        if not path.startswith('data/source-snapshots/') or '..' in path:
            raise AssertionError(f'Unexpected golden evidence path: {path}')
        sources[path] = read(current_base, path)
    return before, after, sources


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-base", required=True)
    parser.add_argument("--baseline-base", required=True)
    parser.add_argument("--report-dir", required=True)
    args = parser.parse_args()

    folder = Path(args.report_dir)
    folder.mkdir(parents=True, exist_ok=True)
    failures: list[dict] = []
    allowed_history_upgrades: list[dict] = []
    allowed_screenshot_enrichments: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        evidence_context = browser.new_context()
        baseline_metrics, current_metrics, source_evidence = load_enrichment_evidence(
            evidence_context.request, args.baseline_base, args.current_base)
        evidence_context.close()
        probe_current = browser.new_page(viewport={"width": 1440, "height": 1100})
        probe_baseline = browser.new_page(viewport={"width": 1440, "height": 1100})
        current_contract = discover(probe_current, args.current_base)
        baseline_contract = discover(probe_baseline, args.baseline_base)
        probe_current.close()
        probe_baseline.close()

        total = sum(map(len, current_contract.values()))
        unique = len({metric for metrics in current_contract.values() for metric in metrics})
        if current_contract != baseline_contract:
            failures.append({
                "key": "catalog",
                "kind": "camaiore-contract-diff",
                "baseline": baseline_contract,
                "current": current_contract,
            })
        if total != EXPECTED or unique != EXPECTED:
            failures.append({
                "key": "catalog",
                "kind": "camaiore-golden-metric-count",
                "expected": EXPECTED,
                "total": total,
                "unique": unique,
            })

        checked = 0
        for viewport, width, height in VIEWPORTS:
            base_page = browser.new_page(viewport={"width": width, "height": height})
            cur_page = browser.new_page(viewport={"width": width, "height": height})
            baseline_errors: list[str] = []
            current_errors: list[str] = []
            base_page.on("pageerror", lambda error: baseline_errors.append(str(error)))
            cur_page.on("pageerror", lambda error: current_errors.append(str(error)))

            for theme, metrics in current_contract.items():
                go(base_page, args.baseline_base, theme, metrics[0])
                go(cur_page, args.current_base, theme, metrics[0])
                normalize_baseline_town_order(base_page)

                expected_town_order = list(EXPECTED_TOWN_ORDER)
                baseline_town_order = town_nav_order(base_page)
                current_town_order = town_nav_order(cur_page)
                if baseline_town_order != expected_town_order:
                    failures.append({
                        "key": f"{viewport}:{theme}:baseline-town-order",
                        "kind": "camaiore-baseline-town-order-normalization",
                        "value": baseline_town_order,
                        "expected": expected_town_order,
                    })
                if current_town_order != expected_town_order:
                    failures.append({
                        "key": f"{viewport}:{theme}:current-town-order",
                        "kind": "camaiore-current-town-order",
                        "value": current_town_order,
                        "expected": expected_town_order,
                    })

                if theme == next(iter(current_contract)):
                    compare_screenshot(
                        base_page,
                        cur_page,
                        ".town-hero",
                        f"{viewport}-hero",
                        folder,
                        failures,
                    )

                for metric in metrics:
                    choose(base_page, metric)
                    choose(cur_page, metric)
                    key = f"{viewport}:{theme}:{metric}"
                    with approved_classification_toolbar(base_page, cur_page,
                            baseline_metrics[metric], current_metrics[metric]):
                        baseline_raw = state(base_page)
                        current_raw = state(cur_page)
                        if "a5-municipal-rollout" not in current_raw.get("classes", []):
                            failures.append({
                                "key": key,
                                "kind": "camaiore-rollout-marker-missing",
                                "classes": current_raw.get("classes", []),
                            })
                        baseline_state = canonical_state(baseline_raw)
                        current_state = canonical_state(current_raw)
                        checked += 1

                        if baseline_state != current_state:
                            allowed_upgrade, history_detail = verified_history_upgrade(
                                baseline_state,
                                current_state,
                                base_page,
                                cur_page,
                            )
                            if allowed_upgrade:
                                allowed_history_upgrades.append({
                                    "key": key,
                                    **history_detail,
                                })
                            else:
                                failures.append({
                                    "key": key,
                                    "kind": "camaiore-computed-golden-diff",
                                    "baseline": baseline_state,
                                    "current": current_state,
                                })

                        if metric == metrics[0] or metric in REVIEW_METRICS:
                            with screenshot_enrichment_normalization(
                                    base_page, cur_page, baseline_metrics[metric],
                                    current_metrics[metric], source_evidence,
                                    diagnostic_dir=folder) as allowances:
                                allowed_screenshot_enrichments.extend({'key': key, **a} for a in allowances)
                                compare_screenshot(
                                    base_page,
                                    cur_page,
                                    "#town-topic",
                                    f"{viewport}-{theme}-{metric}",
                                    folder,
                                    failures,
                                )

            if baseline_errors:
                failures.append({"key": viewport, "kind": "baseline-page-errors", "errors": baseline_errors})
            if current_errors:
                failures.append({"key": viewport, "kind": "current-page-errors", "errors": current_errors})
            base_page.close()
            cur_page.close()

        browser.close()

    report = {
        "approved_commit": APPROVED_COMMIT,
        "town": "camaiore",
        "checked_states": checked,
        "themes": list(current_contract),
        "metric_states_per_viewport": total,
        "unique_metric_count": unique,
        "viewports": [{"name": name, "width": width, "height": height} for name, width, height in VIEWPORTS],
        "allowed_history_upgrades": allowed_history_upgrades,
        "allowed_screenshot_enrichments": allowed_screenshot_enrichments,
        "failure_count": len(failures),
        "failures": failures,
    }
    (folder / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (folder / "summary.txt").write_text(
        "A5 Camaiore full golden lock\n"
        f"approved_commit={APPROVED_COMMIT}\n"
        f"checked_states={checked}\n"
        f"allowed_history_upgrades={len(allowed_history_upgrades)}\n"
        f"failures={len(failures)}\n",
        encoding="utf-8",
    )
    if failures:
        raise SystemExit(
            f"A5 Camaiore full golden lock FAILED: {len(failures)} problemi\n"
            + json.dumps(failures[:10], ensure_ascii=False, indent=2)
        )
    print(
        f"A5 Camaiore full golden lock OK: {checked} stati "
        f"({total}/viewport) invariati rispetto a {APPROVED_COMMIT[:7]}."
    )


if __name__ == "__main__":
    main()
