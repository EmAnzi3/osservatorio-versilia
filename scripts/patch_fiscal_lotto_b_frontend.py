#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_PATH = ROOT / 'assets' / 'app-parts' / '03.txt'

HELPER = r'''
  function updateFiscalRecoveryTownPosition(metric,row,choice,position) {
    if (!position || metric?.meta?.key !== 'fiscalRecoveryActivity') return;
    const overline=position.querySelector('.overline');
    const deltaEl=position.querySelector('[data-composite-delta]');
    const noteEl=position.querySelector('p');
    const aggLabel=position.querySelector('[data-composite-aggregate-label]');
    const aggValue=position.querySelector('[data-composite-aggregate-value]');
    const apply=(heading,headline,direction,note,label,value)=>{
      if(overline) overline.textContent=heading;
      if(deltaEl) deltaEl.innerHTML=`${html(headline)}<small>${html(direction)}</small>`;
      if(noteEl) noteEl.textContent=note;
      if(aggLabel) aggLabel.textContent=label;
      if(aggValue) aggValue.textContent=value;
    };

    if(choice === 'part-1') {
      const local=Number(row.parts?.[1]?.value);
      const total=Number(metric.aggregate?.parts?.[1]?.value);
      const share=Number.isFinite(local) && Number.isFinite(total) && total > 0 ? local/total*100 : 0;
      apply(
        'Peso sul totale Versilia',
        `${number1.format(share)}%`,
        'del recupero tributario complessivo',
        'Quota degli incassi da verifica e controllo del Comune sul totale registrato nei sette Comuni della Versilia.',
        'Versilia · recupero totale',
        formatValue(total,'currency')
      );
      return;
    }

    if(choice === 'part-2') {
      const local=Number(row.parts?.[2]?.value) || 0;
      const total=Number(metric.aggregate?.parts?.[2]?.value) || 0;
      const beneficiaries=metric.rows
        .map(item=>({ town:item.town, value:Number(item.parts?.[2]?.value) || 0 }))
        .filter(item=>item.value > 0)
        .sort((a,b)=>b.value-a.value);
      const share=total > 0 ? local/total*100 : 0;
      const rank=beneficiaries.findIndex(item=>item.town===row.town)+1;
      const note=local > 0
        ? `${row.town} è ${rank}° per importo attribuito tra i ${beneficiaries.length} Comuni versiliesi beneficiari. Il dato non misura l’efficacia complessiva dell’attività fiscale comunale.`
        : `${row.town} non compare tra i beneficiari del prospetto DAIT 2025. L’assenza non implica assenza di controlli o di segnalazioni comunali.`;
      apply(
        'Contributo attribuito in Versilia',
        `${number1.format(share)}%`,
        local > 0 ? 'del contributo DAIT attribuito in Versilia' : 'nessun contributo attribuito',
        note,
        `Versilia · ${beneficiaries.length} Comuni beneficiari`,
        formatValue(total,'currency')
      );
      return;
    }

    const selected=compositeSelectionOptions(metric,row).find(option=>option.key===choice) || compositeSelectionOptions(metric,row)[0];
    const agg=compositeSelectionAggregate(metric,choice);
    const delta=compositeDeltaText(selected.value,agg.value,selected.unit);
    apply(
      'Rispetto alla Versilia',
      delta.headline,
      delta.direction,
      'Il confronto con la Versilia descrive soltanto lo scostamento numerico e non esprime un giudizio di qualità.',
      agg.label,
      agg.formatted
    );
  }
'''.strip('\n')

HELPER_ANCHOR = '  function renderCompareMetric(data, themeKey, metricKey, normalized, requestedView = null) {'
INITIAL_ANCHOR = '    const tablist = container.querySelector(\'[role="tablist"]\');'
INITIAL_CALL = "    if (selectable) updateFiscalRecoveryTownPosition(metric,row,options[0]?.key || 'summary',container.querySelector('.composite-versilia-position'));"
EVENT_ANCHOR = "        window.dispatchEvent(new CustomEvent('ov:composite-choice',{detail:{metricKey,choice,town:town.slug}}));"
EVENT_CALL = '        updateFiscalRecoveryTownPosition(metric,row,choice,position);'


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise RuntimeError(f'Anchor Fiscalità Lotto B non trovato: {label}')


def patch() -> None:
    text = FRONTEND_PATH.read_text(encoding='utf-8')

    if 'function updateFiscalRecoveryTownPosition(metric,row,choice,position)' not in text:
        require(text, HELPER_ANCHOR, 'renderCompareMetric')
        text = text.replace(HELPER_ANCHOR, HELPER + '\n\n' + HELPER_ANCHOR, 1)

    if INITIAL_CALL not in text:
        require(text, INITIAL_ANCHOR, 'tablist comunale')
        text = text.replace(INITIAL_ANCHOR, INITIAL_CALL + '\n\n' + INITIAL_ANCHOR, 1)

    if EVENT_CALL not in text:
        require(text, EVENT_ANCHOR, 'evento composito comunale')
        text = text.replace(EVENT_ANCHOR, EVENT_CALL + '\n' + EVENT_ANCHOR, 1)

    FRONTEND_PATH.write_text(text, encoding='utf-8')

    verified = FRONTEND_PATH.read_text(encoding='utf-8')
    for needle, label in (
        ('function updateFiscalRecoveryTownPosition(metric,row,choice,position)', 'helper'),
        (INITIAL_CALL, 'inizializzazione'),
        (EVENT_CALL, 'cambio selettore'),
        ('Peso sul totale Versilia', 'semantica recupero totale'),
        ('nessun contributo attribuito', 'semantica DAIT'),
    ):
        if needle not in verified:
            raise RuntimeError(f'Patch Fiscalità Lotto B incompleta: {label}')

    print('Frontend Fiscalità Lotto B: semantica comunale applicata e verificata.')


if __name__ == '__main__':
    patch()
