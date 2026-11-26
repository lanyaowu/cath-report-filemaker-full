/**
 * 臨床的な判定・変換（画面・帳票・確定時チェックで共通に使う）。
 * Thymeleaf 版は同じ規則を Java（jp.example.cathreport.service.Clinical）に実装している。変更するときは両方を直す。
 */
import type { Draft, PciLesion } from '../types/model';

const num = (s: string | undefined | null): number | null => {
  if (s == null || String(s).trim() === '') return null;
  const n = Number(String(s).replace(/[%％\s]/g, ''));
  return Number.isFinite(n) ? n : null;
};

// ---------------------------------------------------------------- 狭窄度（G-15）
/** JCS 標準（SEAMAT）の狭窄度 7 区分 */
export const JCS_BANDS = ['0%', '1-24%', '25-49%', '50-69%', '70-89%', '90-99%', '100%'] as const;
export type JcsBand = (typeof JCS_BANDS)[number];

/**
 * AHA 分類（目視）→ JCS 区分。施設の決定により「区間の上限」で対応付ける
 * （AHA 75%＝51〜75% → 50〜69%。J-PCI の「AHA 75%＝実測 50% 以上」に合う）。
 */
const AHA_TO_JCS: Record<string, JcsBand> = {
  Normal: '0%', '0': '0%', Irregular: '1-24%', '25': '1-24%', '50': '25-49%', '75': '50-69%', '90': '70-89%', '99': '90-99%', '100': '100%',
};

/** 実測の狭窄率（%DS）→ JCS 区分 */
export function jcsBandFromPct(pct: string | number | null | undefined): JcsBand | '' {
  const n = typeof pct === 'number' ? pct : num(pct ?? '');
  if (n == null || n < 0 || n > 100) return '';
  if (n === 0) return '0%';
  if (n < 25) return '1-24%';
  if (n < 50) return '25-49%';
  if (n < 70) return '50-69%';
  if (n < 90) return '70-89%';
  if (n < 100) return '90-99%';
  return '100%';
}

/** AHA 分類の値 → JCS 区分。QCA の実測値があれば実測値を優先 */
export function jcsBand(aha: string | null | undefined, qcaPct?: string | null): JcsBand | '' {
  const q = jcsBandFromPct(qcaPct ?? '');
  if (q) return q;
  return AHA_TO_JCS[String(aha ?? '').trim()] ?? '';
}

// ---------------------------------------------------------------- 手技時間（G-08）
/** HH:MM の差（分）。終了が開始より前なら日付をまたいだとみなす */
export function procedureMinutes(start: string, end: string): number | null {
  const p = (t: string) => {
    const m = /^(\d{1,2}):(\d{2})$/.exec((t ?? '').trim());
    return m ? Number(m[1]) * 60 + Number(m[2]) : null;
  };
  const a = p(start);
  const b = p(end);
  if (a == null || b == null) return null;
  return b >= a ? b - a : b + 24 * 60 - a;
}

// ---------------------------------------------------------------- CTO・J-CTO（G-25）
export const CTO_DURATION = [
  { value: '<3m', label: '3か月未満' },
  { value: '>=3m', label: '3か月以上' },
  { value: 'unknown', label: '不明' },
];
export const JCTO_ITEMS: [keyof PciLesion['cto']['jcto'], string][] = [
  ['blunt', '入口部が鈍（Blunt stump）'],
  ['calc', '閉塞部の石灰化'],
  ['bend', '閉塞部の屈曲 >45°'],
  ['len20', '閉塞長 ≥20mm'],
  ['retry', '再挑戦（過去に不成功）'],
];

const isCto = (l: PciLesion) => l.morph?.cto === 'yes';

/** J-CTO スコア（0〜5）。CTO でない、または 5 項目のうち未回答があれば null */
export function jctoScore(l: PciLesion): number | null {
  if (!isCto(l)) return null;
  const j = l.cto?.jcto;
  if (!j) return null;
  const vals = JCTO_ITEMS.map(([k]) => j[k]);
  if (vals.some((v) => v !== 'yes' && v !== 'no')) return null;
  return vals.filter((v) => v === 'yes').length;
}

/** J-CTO の未回答項目数（CTO の病変のみ） */
export function jctoMissing(l: PciLesion): number {
  if (!isCto(l)) return 0;
  return JCTO_ITEMS.filter(([k]) => l.cto?.jcto?.[k] !== 'yes' && l.cto?.jcto?.[k] !== 'no').length;
}

/** 旧項目「Age of Occlusion」から閉塞期間を推定（移行用） */
export function durationFromAge(age: string): string {
  const a = (age ?? '').trim();
  if (!a) return '';
  if (a === '>3ヶ月' || /^>|以上/.test(a)) return '>=3m';
  if (a === '<1ヶ月' || a === '1-3ヶ月' || /^</.test(a)) return '<3m';
  if (a === '不明') return 'unknown';
  return '';
}

// ---------------------------------------------------------------- ACC/AHA 病変分類（G-26）
export interface AccAhaSuggestion { type: 'A' | 'B1' | 'B2' | 'C'; c: string[]; b: string[] }

/** 病変形態の入力から ACC/AHA Type を提案する。判断材料が何も無ければ null */
export function accAhaSuggest(l: PciLesion): AccAhaSuggestion | null {
  const m = l.morph ?? {};
  const len = num(l.lengthA);
  const lenCat = len != null ? (len > 20 ? '>20' : len >= 10 ? '10-20' : '<10') : l.lengthB === '>20mm' ? '>20' : l.lengthB === '10-20mm' ? '10-20' : l.lengthB === '<10mm' ? '<10' : '';
  const answered = Object.values(m).some(Boolean) || !!l.angulation || !!l.proximalTortuosity || !!lenCat;
  if (!answered) return null;
  const c: string[] = [];
  const b: string[] = [];
  if (lenCat === '>20') c.push('病変長 >20mm');
  if (lenCat === '10-20') b.push('病変長 10〜20mm');
  if (l.proximalTortuosity === 'Severe') c.push('近位部の高度蛇行');
  if (l.proximalTortuosity === 'Moderate') b.push('近位部の中等度蛇行');
  if (l.angulation === '>90°') c.push('屈曲 >90°');
  if (l.angulation === '45-90°') b.push('屈曲 45〜90°');
  if (isCto(l)) {
    const d = l.cto?.duration || durationFromAge(l.ageOfOcclusion);
    if (d === '<3m') b.push('完全閉塞 <3か月');
    else if (d === '>=3m') c.push('完全閉塞 ≥3か月');
    else if (d === 'unknown') c.push('完全閉塞（期間不明は 3か月以上として扱う）');
    else b.push('完全閉塞（期間未入力：3か月未満として仮判定）');
  }
  if (m.eccentricity === 'yes') b.push('偏心性');
  if (m.irregular === 'yes') b.push('輪郭不整');
  if (m.calcification === 'yes') b.push('石灰化');
  if (m.ostial === 'yes') b.push('入口部');
  if (m.bifurcation === 'yes') b.push('分岐部');
  if (m.thrombus === 'yes') b.push('血栓');
  const type = c.length ? 'C' : b.length >= 2 ? 'B2' : b.length === 1 ? 'B1' : 'A';
  return { type, c, b };
}

// ---------------------------------------------------------------- 病変成功（G-27）
/** 術後の残存狭窄（%）。QCA（post.pct）を優先し、無ければ基本タブの Post */
export function postStenosis(l: PciLesion): number | null {
  return num(l.post?.pct) ?? num(l.summary?.post);
}

/** J-PCI の病変成功：術後の残存狭窄 ≤25% かつ TIMI 3。判断材料が足りなければ '' */
export function lesionSuccessSuggest(l: PciLesion): 'Success' | 'Failure' | '' {
  const p = postStenosis(l);
  const t = (l.summary?.timiPost ?? '').trim();
  if (p == null || !t) return '';
  return p <= 25 && t === '3' ? 'Success' : 'Failure';
}

// ---------------------------------------------------------------- 確定時の必須項目チェック（G-40）
const blank = (v: unknown) => v == null || (typeof v === 'string' && v.trim() === '');

/**
 * 確定前に確認したい空欄（警告のみ。確定は止めない）。
 * 必須の範囲は「心臓カテーテル検査・治療レポート 標準項目解説書」の必須（◎）のうち、本アプリにある項目。
 */
export function confirmWarnings(d: Draft): string[] {
  const w: string[] = [];
  const { patient: p, report: r } = d;
  const ex = r.cathRecord.exam;
  const rk = r.cathRecord.risk;
  const need = (cond: boolean, label: string) => cond && w.push(label);

  // 患者・検査
  need(blank(r.header.studyDate), '施行日');
  need(blank(p.sex), '性別');
  need(blank(p.birthDate), '生年月日');
  need(blank(r.cathRecord.body.height) || blank(r.cathRecord.body.weight), '身長・体重');
  need(blank(ex.urgency), '待機／緊急');
  need(!Object.values(ex.purposes).some(Boolean), '検査の目的');
  need(blank(r.cathRecord.doctors.operators[0]), '術者');
  need(blank(ex.approach), 'アプローチ');
  need(blank(ex.startTime) || blank(ex.endTime), '手技の開始・終了時刻');
  need(blank(ex.contrast.volume), '造影剤量');
  need(blank(ex.fluoroTime), '透視時間');
  need(blank(ex.totalDose), '総線量');
  // 危険因子・既往
  const riskLabels: [keyof typeof rk, string][] = [
    ['DM', 'DM'], ['HT', 'HT'], ['HL', 'HL'], ['smoking', '喫煙'],
    ['priorMI', '心筋梗塞の既往'], ['priorHF', '心不全の既往'], ['pciHx', 'PCI歴'], ['cabgHx', 'CABG歴'], ['renal', '腎不全'],
  ];
  const missingRisk = riskLabels.filter(([k]) => blank(rk[k])).map(([, l]) => l);
  need(missingRisk.length > 0, `危険因子・既往（${missingRisk.join('・')}）`);
  // 合併症
  need(blank(r.cathRecord.complications.status), '合併症の有無（カテ記録）');

  // CAG
  const cagDone = ex.purposes.CAG || /CAG/i.test(ex.examItems);
  if (cagDone) {
    const cag = r.cagLvg.cag;
    need(blank(cag.dominance), 'Dominance（CAG）');
    need(!Object.values(cag.segments).some((s) => !blank(s.stenosis)), 'セグメントの狭窄度（CAG）');
    need(blank(cag.lesions.count), '病変枝数（CAG）');
  }
  // PCI
  const lesions = r.pci.lesions.filter((l) => !blank(l.target));
  const pciDone = ex.purposes.PCI || /PCI/i.test(ex.examItems) || lesions.length > 0;
  if (pciDone) {
    need(lesions.length === 0, 'PCI の標的病変（Target）');
    lesions.forEach((l) => {
      const miss: string[] = [];
      if (blank(l.type)) miss.push('Type');
      if (blank(l.deNovoMajor)) miss.push('de novo/再狭窄');
      if (blank(l.summary.pre) && blank(l.pre.pct)) miss.push('術前狭窄度');
      if (blank(l.summary.post) && blank(l.post.pct)) miss.push('術後狭窄度');
      if (blank(l.summary.timiPre)) miss.push('TIMI Pre');
      if (blank(l.summary.timiPost)) miss.push('TIMI Post');
      if (blank(l.success)) miss.push('成否');
      if (isCto(l) && blank(l.cto.duration)) miss.push('閉塞期間');
      if (jctoMissing(l) > 0) miss.push('J-CTO');
      if (miss.length) w.push(`PCI 病変 ${l.target}（${miss.join('・')}）`);
    });
    need(blank(r.pci.jpci.info.procComp), 'PCI の手技に関連する合併症（J-PCI）');
  }
  return w;
}

/** 確定時に表示する、入力値どうしの食い違い（自動判定と異なる値） */
export function confirmMismatches(d: Draft): string[] {
  const out: string[] = [];
  d.report.pci.lesions.forEach((l) => {
    if (!l.target) return;
    const s = lesionSuccessSuggest(l);
    if (s && l.success && s !== l.success) out.push(`PCI 病変 ${l.target}：成否「${l.success}」が自動判定「${s}」と異なる`);
    const a = accAhaSuggest(l);
    if (a && l.type && a.type !== l.type) out.push(`PCI 病変 ${l.target}：Type「${l.type}」が自動提案「${a.type}」と異なる`);
  });
  return out;
}
