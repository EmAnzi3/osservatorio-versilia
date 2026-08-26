#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Pattern non trovato: {label}")
    return text.replace(old, new, 1)


def patch_app_parts() -> None:
    rel = "assets/app-parts/03.txt"
    text = read(rel)

    helper = '''  function updateAgricultureProfileTownPosition(metric,row,choice,position) {
    if (!position || metric?.meta?.compositeType !== 'agricultureProfile') return;
    const index=Math.max(0,Number(String(choice || 'part-0').replace('part-','')) || 0);
    const localPart=row?.parts?.[index] || {};
    const totalPart=metric.aggregate?.parts?.[index] || {};
    const localRaw=localPart.value;
    const totalRaw=totalPart.value;
    const local=localRaw === null || localRaw === undefined ? NaN : Number(localRaw);
    const total=totalRaw === null || totalRaw === undefined ? NaN : Number(totalRaw);
    const share=Number.isFinite(local) && Number.isFinite(total) && total > 0 ? local / total * 100 : null;
    const overline=position.querySelector('.overline');
    const deltaEl=position.querySelector('[data-composite-delta]');
    const noteEl=position.querySelector('p');
    const aggLabel=position.querySelector('[data-composite-aggregate-label]');
    const aggValue=position.querySelector('[data-composite-aggregate-value]');
    if(overline) overline.textContent='Quota sul totale Versilia';
    if(deltaEl) deltaEl.innerHTML=share === null
      ? `n.d.<small>dato comunale non disponibile</small>`
      : `${html(number2.format(share))}%<small>del totale della coltura</small>`;
    if(noteEl) noteEl.textContent=`Quota del Comune sul totale Versilia della coltura, calcolato sui Comuni con dato disponibile (${totalPart.coverage || 'copertura dichiarata'}). I valori mancanti restano n.d.`;
    if(aggLabel) aggLabel.textContent=`Versilia · ${totalPart.label || metric.meta.label}`;
    if(aggValue) aggValue.textContent=formatValue(totalPart.value,totalPart.unit || metric.meta.unit);
  }

'''
    marker = "  function updateFiscalRecoveryTownPosition(metric,row,choice,position) {"
    if helper not in text:
        if marker not in text:
            raise RuntimeError("Pattern non trovato: helper quota colture")
        text = text.replace(marker, helper + marker, 1)

    text = replace_once(
        text,
        "    if (selectable) updateFiscalRecoveryTownPosition(metric,row,options[0]?.key || 'summary',container.querySelector('.composite-versilia-position'));",
        "    if (selectable) {\n      const initialPosition=container.querySelector('.composite-versilia-position');\n      const initialChoice=options[0]?.key || 'summary';\n      updateFiscalRecoveryTownPosition(metric,row,initialChoice,initialPosition);\n      updateAgricultureProfileTownPosition(metric,row,initialChoice,initialPosition);\n    }",
        "quota colture iniziale",
    )

    text = replace_once(
        text,
        "        updateFiscalRecoveryTownPosition(metric,row,choice,position);\n        window.dispatchEvent(new CustomEvent('ov:composite-choice',{detail:{metricKey,choice,town:town.slug}}));",
        "        updateFiscalRecoveryTownPosition(metric,row,choice,position);\n        updateAgricultureProfileTownPosition(metric,row,choice,position);\n        window.dispatchEvent(new CustomEvent('ov:composite-choice',{detail:{metricKey,choice,town:town.slug}}));",
        "quota colture cambio selezione",
    )

    old_switch = '''    } else if (metric.meta.detailGroup === 'tpl') {
      // ux-history può ricostruire l'HTML interno di #compare-bars: il listener
      // vive sul contenitore stabile e non sul singolo pulsante.
      bars.onclick = event => {
        const scaleButton = event.target.closest('button[data-scale]');
        if (scaleButton && bars.contains(scaleButton)) {
          renderCompareMetric(data,themeKey,metricKey,scaleButton.dataset.scale === 'normalized',view);
        }
      };
      bars.onchange = null;
    } else {
      bars.onclick = null;
      bars.onchange = null;
    }
'''
    new_switch = '''    } else if (hasNormalized) {
      // Lo switch assoluto/rapportato vive accanto al grafico: delega dal
      // contenitore stabile perché il render sostituisce il markup interno.
      bars.onclick = event => {
        const scaleButton = event.target.closest('button[data-scale]');
        if (scaleButton && bars.contains(scaleButton)) {
          renderCompareMetric(data,themeKey,metricKey,scaleButton.dataset.scale === 'normalized',view);
        }
      };
      bars.onchange = null;
    } else {
      bars.onclick = null;
      bars.onchange = null;
    }
'''
    text = replace_once(text, old_switch, new_switch, "switch assoluto rapportato")
    write(rel, text)


def patch_visual_grammar() -> None:
    rel = "assets/visual-grammar.js"
    text = read(rel)
    text = replace_once(
        text,
        "    if (metric.meta?.compositeType === 'distribution') return;",
        "    if (['distribution','agricultureProfile'].includes(metric.meta?.compositeType)) return;",
        "non sovrascrivere quota colture",
    )
    write(rel, text)


def main() -> None:
    patch_app_parts()
    patch_visual_grammar()
    print("Correzioni review v3 applicate: quota colture sul totale e switch rapportato delegato dal grafico.")


if __name__ == "__main__":
    main()
