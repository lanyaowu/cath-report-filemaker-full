import type { ReactNode } from 'react';
import { TextF } from '../../form/fields';
import { LIST_MAX, createPciLesion } from '../../model/defaults';
import { AddRowBtn, DelRowBtn, range, useCount } from '../../form/repeat';
import { CAG_SEGMENTS } from '../../constants/options';

/** 病変（Target）の列番号。数は可変（最大 LIST_MAX.lesions） */
export function useLesions(): number[] {
  return range(useCount('lesions'));
}
export const TARGET_LIST = CAG_SEGMENTS.map((s) => `#${s.key.replace(/^\D+/, '') || s.key}`);

export interface GridRow {
  label: ReactNode;
  /** 区切り見出し行（<Bifurcation> 等） */
  section?: boolean;
  render?: (i: number) => ReactNode;
  tone?: 'green' | 'blue';
}

/**
 * PCI の病変単位グリッド（Target 列。数は可変で最大 5 列）。scope: report.pci
 * 各タブで Target は共通（lesions[i].target）。どのタブからでも病変を追加・削除できる。
 */
export function LesionGrid({ rows, labelWidth = 190, withSub = false }: { rows: GridRow[]; labelWidth?: number; withSub?: boolean }) {
  const LESIONS = useLesions();
  const empty = range(LIST_MAX.lesions - LESIONS.length);
  let n = 0;
  return (
    <table className="lesion-grid">
      <colgroup>
        <col style={{ width: labelWidth }} />
      </colgroup>
      <thead>
        <tr>
          <th className="lg-label">
            Target <span className="tab-arrow">▶</span>
            <div className="lg-add">
              <AddRowBtn path="lesions" max={LIST_MAX.lesions} create={createPciLesion} label="病変" title="病変（Target）を追加" />
            </div>
          </th>
          {LESIONS.map((i) => (
            <th key={i} className="lg-target">
              <div className="lg-target-in">
                <TextF path={`lesions.${i}.target`} w={withSub ? 64 : '96%'} list={TARGET_LIST} placeholder={`病変${i + 1}`} />
                {withSub && <TextF path={`lesions.${i}.targetSub`} w={70} list={['LMT', 'LAD', 'LCX', 'RCA', 'Dx', 'OM', 'PL', 'PD', 'SVG', 'ITA']} placeholder="血管" />}
                <DelRowBtn path="lesions" index={i} create={createPciLesion} what="病変" />
              </div>
            </th>
          ))}
          {empty.map((k) => <th key={`e${k}`} className="lg-empty" />)}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, ri) => {
          if (r.section) {
            n = 0;
            return (
              <tr key={ri} className="lg-section">
                <th>{r.label}</th>
                {LESIONS.map((i) => (
                  <td key={i} />
                ))}
                {empty.map((k) => <td key={`e${k}`} className="lg-empty" />)}
              </tr>
            );
          }
          const tone = r.tone ?? (n++ % 2 === 0 ? 'green' : 'blue');
          return (
            <tr key={ri} className={`lg-${tone}`}>
              <th>{r.label}</th>
              {LESIONS.map((i) => (
                <td key={i}>
                  <div className="lg-cell">{r.render?.(i)}</div>
                </td>
              ))}
              {empty.map((k) => <td key={`e${k}`} className="lg-empty" />)}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
