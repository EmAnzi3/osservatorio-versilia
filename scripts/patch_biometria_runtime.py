#!/usr/bin/env python3
"""Estende i renderer canonici con le sole capacità richieste dalla v1.35.0."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMATTER = ROOT / "assets" / "app-parts" / "00.txt"
TOWN_RENDERER = ROOT / "assets" / "app-parts" / "03.txt"
VISUAL_GRAMMAR = ROOT / "assets" / "visual-grammar.js"
UNITS_MARKER = "/* OV BIOMETRIA UNITS v1.35.0 */"
SHARE_MARKER = "/* OV BIOMETRIA SHARE-OF-AGGREGATE v1.35.0 */"
ALTITUDE_MARKER = "/* OV BIOMETRIA ALTITUDE-STATS v1.35.0 */"


def patch_units() -> None:
    source = FORMATTER.read_text(encoding="utf-8")
    if UNITS_MARKER in source:
        return
    needle = "      case 'km': return `${number2.format(v)} km`;"
    replacement = """      /* OV BIOMETRIA UNITS v1.35.0 */
      case 'squareKm': return `${number2.format(v)} km²`;
      case 'peoplePerSquareKm': return `${number1.format(v)} ab./km²`;
      case 'metres': return `${number0.format(v)} m`;
      case 'km': return `${number2.format(v)} km`;"""
    if source.count(needle) != 1:
        raise RuntimeError(f"Formatter canonico non patchabile in modo univoco: {source.count(needle)} occorrenze")
    FORMATTER.write_text(source.replace(needle, replacement, 1), encoding="utf-8")


def patch_share_of_aggregate() -> None:
    source = VISUAL_GRAMMAR.read_text(encoding="utf-8")
    if SHARE_MARKER in source:
        return
    needle = "    if (key === 'population') {"
    replacement = """    /* OV BIOMETRIA SHARE-OF-AGGREGATE v1.35.0 */
    if (metric?.meta?.comparisonDifference === 'shareOfAggregate' || key === 'municipalSurface') {
      const total = finite(metric?.aggregate?.value);
      if (total === null || total <= 0) {
        return { headline:'n.d.', direction:'quota non disponibile', compact:'quota non disponibile', overline:metric?.meta?.comparisonOverline, note:metric?.meta?.comparisonNote };
      }
      const share = local / total * 100;
      const formattedShare = number1.format(share);
      const direction = metric?.meta?.comparisonDirection || 'della superficie dei 7 Comuni';
      return {
        headline: `${formattedShare}%`,
        direction,
        compact: `${formattedShare}% ${direction}`,
        overline: metric?.meta?.comparisonOverline || 'Quota sulla Versilia',
        note: metric?.meta?.comparisonNote || 'Quota della superficie comunale sul totale della superficie dei sette Comuni.',
      };
    }
    if (key === 'population') {"""
    if source.count(needle) != 1:
        raise RuntimeError(f"Visual grammar non patchabile per shareOfAggregate: {source.count(needle)} occorrenze")
    VISUAL_GRAMMAR.write_text(source.replace(needle, replacement, 1), encoding="utf-8")


def patch_altitude_stats() -> None:
    source = TOWN_RENDERER.read_text(encoding="utf-8")
    if ALTITUDE_MARKER in source:
        return
    needle = """    const agePyramidDisclosure = agePyramidMarkup(metric,row);
    return `<div class=\"composite-town-stack-shell\">${compositePartLegend(metric)}${compositeStackMarkup(parts,{ town:true, ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:5, countLabel })}"""
    replacement = """    const agePyramidDisclosure = agePyramidMarkup(metric,row);
    /* OV BIOMETRIA ALTITUDE-STATS v1.35.0 */
    const altitudeStats = metric.meta.key === 'altitudeProfile' ? row.altitudeStats : null;
    const altitudeStatsReady = altitudeStats && [altitudeStats.minM,altitudeStats.meanM,altitudeStats.maxM].every(value=>Number.isFinite(Number(value)));
    const altitudeStatsMarkup = altitudeStatsReady ? `<div class=\"composite-town-mobility\"><article><span>Quota minima</span><strong>${html(formatValue(altitudeStats.minM,'metres'))}</strong><small>${html(metric.meta.year)}</small></article><article class=\"balance\"><span>Quota media</span><strong>${html(formatValue(altitudeStats.meanM,'metres'))}</strong><small>${html(metric.meta.year)}</small></article><article><span>Quota massima</span><strong>${html(formatValue(altitudeStats.maxM,'metres'))}</strong><small>${html(metric.meta.year)}</small></article></div>` : '';
    return `${altitudeStatsMarkup}<div class=\"composite-town-stack-shell\">${compositePartLegend(metric)}${compositeStackMarkup(parts,{ town:true, ariaLabel:`${metric.meta.label} · ${row.town}`, minLabel:5, countLabel })}"""
    if source.count(needle) != 1:
        raise RuntimeError(f"Renderer comunale non patchabile per quote altimetriche: {source.count(needle)} occorrenze")
    TOWN_RENDERER.write_text(source.replace(needle, replacement, 1), encoding="utf-8")


def main() -> None:
    patch_units()
    patch_share_of_aggregate()
    patch_altitude_stats()
    print("Biometria: unità, quota sul totale Versilia e quote altimetriche abilitate nei renderer canonici.")


if __name__ == "__main__":
    main()
