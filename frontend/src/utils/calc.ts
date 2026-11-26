/** 臨床計算（BSA・BMI・LV容積指標・出血/血栓リスクスコア・IVUS派生値） */

export const num = (s: unknown): number | null => {
  if (s === '' || s == null) return null;
  const n = Number(s);
  return isFinite(n) ? n : null;
};

const r = (v: number, d = 1) => {
  const p = 10 ** d;
  return String(Math.round(v * p) / p);
};

/** DuBois式 BSA (m²) */
export function bsa(heightCm: string, weightKg: string): string {
  const h = num(heightCm);
  const w = num(weightKg);
  if (!h || !w) return '';
  return r(0.007184 * w ** 0.425 * h ** 0.725, 2);
}

export function bmi(heightCm: string, weightKg: string): string {
  const h = num(heightCm);
  const w = num(weightKg);
  if (!h || !w) return '';
  return r(w / (h / 100) ** 2, 1);
}

/** LVG: EDV/ESV から SV・EF・各インデックスを算出 */
export function lvgDerived(edv: string, esv: string, bsaStr: string, hr: string) {
  const e = num(edv);
  const s = num(esv);
  const b = num(bsaStr);
  const h = num(hr);
  const out: Record<string, string> = {};
  if (e != null && s != null && e > 0) {
    const sv = e - s;
    out.LVSV = r(sv, 1);
    out.EF = r((sv / e) * 100, 1);
    if (h) out.CO = r((sv * h) / 1000, 2);
    if (b) {
      out.LVEDVI = r(e / b, 1);
      out.LVESVI = r(s / b, 1);
      out.LVSVI = r(sv / b, 1);
      if (h) out.CI = r((sv * h) / 1000 / b, 2);
    }
  }
  return out;
}

/** 日本版高出血リスク(J-HBR)：主要1つ以上 または 副次2つ以上 */
export function judgeHbr(major: Record<string, boolean>, minor: Record<string, boolean>): string {
  const ma = Object.values(major).filter(Boolean).length;
  const mi = Object.values(minor).filter(Boolean).length;
  if (ma === 0 && mi === 0) return '';
  return ma >= 1 || mi >= 2 ? 'HBR' : 'non-HBR';
}

/** CREDO-Kyoto 血栓リスクスコア */
export function credoScore(items: Record<string, boolean>, points: Record<string, number>) {
  const score = Object.entries(items).reduce((s, [k, v]) => s + (v ? points[k] ?? 0 : 0), 0);
  const level = score <= 1 ? '低リスク' : score <= 3 ? '中リスク' : '高リスク';
  return { score, level };
}

/** IVUS: プラークCSA・プラーク面積率・偏心率 */
export function ivusDerived(vesselCsa: string, lumenCsa: string, maxTh: string, minTh: string) {
  const v = num(vesselCsa);
  const l = num(lumenCsa);
  const mx = num(maxTh);
  const mn = num(minTh);
  const out: { plaqueCSA?: string; plaqueBurden?: string; eccentricity?: string } = {};
  if (v != null && l != null && v > 0) {
    out.plaqueCSA = r(v - l, 2);
    out.plaqueBurden = r(((v - l) / v) * 100, 1);
  }
  if (mx != null && mn != null && mx > 0) out.eccentricity = r((mx - mn) / mx, 2);
  return out;
}

/** 検査値が基準範囲外か */
export function isAbnormal(value: string, lo?: number, hi?: number): boolean {
  const v = num(value);
  if (v == null) return false;
  if (lo != null && v < lo) return true;
  if (hi != null && v > hi) return true;
  return false;
}
