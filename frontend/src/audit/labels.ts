/**
 * 監査ログの表示：項目のパスを日本語の見出しにする（例：pci.lesions.0.qca.pre.DS → PCI › 病変1 › QCA › 術前 › DS）。
 * 辞書は audit-labels.json（Thymeleaf 版は src/main/resources/audit-labels.json に同じ内容）。
 * 辞書に無い名前は英字のまま出す（パスそのものも画面に表示する）。
 */
import LABELS from './audit-labels.json';

const L = LABELS as { sections: Record<string, string>; patient: Record<string, string>; words: Record<string, string>; indexed: Record<string, string> };

/** 配列の番号の見出し（辞書は「親.名前」→「名前」の順に探す）：pci.lesions.0 → 病変1、pressureIvus.lesions.0 → IVUS Lesion 1、その他は #1 */
function indexTemplate(parts: string[], i: number): string | undefined {
  const name = parts[i - 1] ?? '';
  return L.indexed[`${parts[i - 2] ?? ''}.${name}`] ?? L.indexed[name];
}

export function pathLabel(path: string, targetType: string): string {
  const parts = path.split('.');
  const out: string[] = [];
  parts.forEach((p, i) => {
    if (/^\d+$/.test(p)) {
      const t = indexTemplate(parts, i);
      out.push(t ? t.replace('{n}', String(Number(p) + 1)) : `#${Number(p) + 1}`);
      return;
    }
    // 番号の見出しに名前を含む配列は、名前を重ねて出さない（病変 › 病変1 → 病変1）
    if (/^\d+$/.test(parts[i + 1] ?? '') && indexTemplate(parts, i + 1)) return;
    if (i === 0) {
      const dict = targetType === 'patient' ? L.patient : L.sections;
      out.push(dict[p] ?? L.words[p] ?? p);
      return;
    }
    out.push(L.words[p] ?? p);
  });
  return out.join(' › ');
}

/** 先頭の名前（画面の区分）：表示のまとまりに使う */
export function sectionLabel(path: string, targetType: string): string {
  const p = path.split('.')[0];
  if (targetType === 'patient') return '患者情報';
  return L.sections[p] ?? p;
}

/** 値の表示：true は ✓、空は（空） */
export function valueText(v: string): string {
  if (v === 'true') return '✓';
  return v === '' ? '（空）' : v;
}
