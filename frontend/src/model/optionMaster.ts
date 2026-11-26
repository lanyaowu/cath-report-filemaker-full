/**
 * 選択値マスタ（画面の選択肢を DB / Local Storage で管理する）。
 *
 * - 選択肢の定義（初期値）は constants/options.ts の cat(...)。ここではマスタの型・初期値の作成・
 *   保存済みマスタとの合成・画面に出す選択肢の決定・入力チェックを行う（React に依存しない純粋な関数）。
 * - レポートに保存するのは「コード」。既存の値をそのままコードにしているため、過去のレポートは移行なしで表示できる。
 * - コードは作成後に変更しない。表示名の変更・並べ替え・使用停止（active=false）で運用する。
 *   使用停止の値は新しい入力の候補から外れるが、その値が入ったレポートでは「（使用停止）」付きで表示する。
 */
import { OPTION_CATEGORY_DEFS, type OptionCategoryDef, type Opt } from '../constants/options';
import enDict from '../i18n/en.json';
import zhDict from '../i18n/zh-CN.json';

export interface OptionItem {
  code: string;
  label: string;
  sortOrder: number;
  active: boolean;
  /** 言語ごとの表示名（例 { "en": "Radial artery", "zh-CN": "桡动脉" }）。無い言語は label を辞書で訳して表示する */
  labels?: Record<string, string>;
}

/** 表示名を持てる言語（日本語は label） */
export const LABEL_LANGS = ['en', 'zh-CN'] as const;
const DICT_EXACT: Record<string, Record<string, string>> = {
  en: (enDict as { exact: Record<string, string> }).exact,
  'zh-CN': (zhDict as { exact: Record<string, string> }).exact,
};
const HAS_JA = /[\u3040-\u30ff\u3400-\u9fff]/;
/** 初期値の英語・中国語の表示名（画面の辞書から。日本語を含む表示名だけ） */
const initialLabels = (label: string): Record<string, string> | undefined => {
  if (!HAS_JA.test(label)) return undefined;
  const out: Record<string, string> = {};
  for (const l of LABEL_LANGS) if (DICT_EXACT[l][label]) out[l] = DICT_EXACT[l][label];
  return Object.keys(out).length ? out : undefined;
};
/** 使用停止の印（言語ごと） */
const INACTIVE_BY_LANG: Record<string, string> = { en: ' (inactive)', 'zh-CN': '（已停用）' };
/** その言語の表示名 */
export const labelOf = (i: Pick<OptionItem, 'label' | 'labels'>, lang?: string): string => (lang && lang !== 'ja' && i.labels?.[lang]?.trim()) || i.label;

export interface OptionCategory {
  code: string;
  name: string;
  screen: string;
  /** false = 標準の分類・自動判定やレジストリで値を使う（管理画面で編集不可） */
  editable: boolean;
  items: OptionItem[];
  /** 楽観ロック（保存のたびに +1。未保存の初期値は 0） */
  version: number;
  updatedAt?: string;
  updatedBy?: string;
}

/** 選択値マスタで使わない値の印（使用停止） */
export const INACTIVE_SUFFIX = '（使用停止）';
export const MAX_CODE_LENGTH = 50;
export const MAX_LABEL_LENGTH = 200;

export function categoryFromDef(d: OptionCategoryDef): OptionCategory {
  return {
    code: d.code,
    name: d.name,
    screen: d.screen,
    editable: d.editable,
    version: 0,
    items: d.items.map((o, i) => ({ code: o.value, label: o.label, sortOrder: (i + 1) * 10, active: true, ...(initialLabels(o.label) ? { labels: initialLabels(o.label) } : {}) })),
  };
}

/** constants/options.ts の定義から作った初期値 */
export const defaultOptionCategories = (): OptionCategory[] => OPTION_CATEGORY_DEFS.map(categoryFromDef);

/**
 * 保存済みのマスタに、プログラムの定義を合わせる。
 * - 保存済みが無いカテゴリ（新しく追加された選択肢）は初期値を使う。
 * - 編集不可のカテゴリは、常にプログラムの定義を使う（標準の分類はプログラムと一致させる）。
 * - 名称・画面・編集可否はプログラムの定義を正とする。
 */
export function mergeWithDefaults(saved: OptionCategory[] | null | undefined): OptionCategory[] {
  const byCode = new Map((saved ?? []).map((c) => [c.code, c]));
  return OPTION_CATEGORY_DEFS.map((d) => {
    const def = categoryFromDef(d);
    const s = byCode.get(d.code);
    if (!s || !d.editable) return { ...def, version: s?.version ?? 0, updatedAt: s?.updatedAt, updatedBy: s?.updatedBy };
    return { ...s, name: d.name, screen: d.screen, editable: true, items: sortItems(s.items ?? []) };
  });
}

export const sortItems = (items: OptionItem[]) => [...items].sort((a, b) => a.sortOrder - b.sortOrder || a.code.localeCompare(b.code));

const toOpts = (o: readonly (string | Opt)[]): Opt[] => o.map((x) => (typeof x === 'string' ? { value: x, label: x } : x));

/**
 * 画面に出す選択肢。
 * @param cat      マスタのカテゴリ（無ければ fallback をそのまま使う）
 * @param fallback プログラムの定義（マスタ管理外の選択肢、またはマスタ未取得の時）
 * @param current  現在の値。使用停止・マスタに無い値でも、入っていれば選択肢に残す（select・radio 用）
 */
export function resolveOptions(cat: OptionCategory | undefined, fallback: readonly (string | Opt)[], current?: string | null, lang?: string): Opt[] {
  if (!cat) return toOpts(fallback);
  const items = sortItems(cat.items);
  const list: Opt[] = items.filter((i) => i.active).map((i) => ({ value: i.code, label: labelOf(i, lang) }));
  if (current && !list.some((o) => o.value === current)) {
    const inactive = items.find((i) => i.code === current);
    const suffix = (lang && INACTIVE_BY_LANG[lang]) || INACTIVE_SUFFIX;
    list.push({ value: current, label: inactive ? `${labelOf(inactive, lang)}${suffix}` : current });
  }
  return list;
}

/** 保存前の入力チェック（エラーがあれば日本語のメッセージ。サーバーでも同じ検査をする） */
export function validateCategory(c: OptionCategory): string[] {
  const errors: string[] = [];
  if (!c.editable) errors.push(`「${c.name}」は標準の分類のため編集できません`);
  const seen = new Set<string>();
  c.items.forEach((it, i) => {
    const row = `${i + 1} 行目`;
    const code = (it.code ?? '').trim();
    if (!code) errors.push(`${row}：コードを入力してください`);
    else if (code.length > MAX_CODE_LENGTH) errors.push(`${row}：コードは ${MAX_CODE_LENGTH} 文字以内にしてください`);
    else if (seen.has(code)) errors.push(`${row}：コード「${code}」が重複しています`);
    seen.add(code);
    const label = (it.label ?? '').trim();
    if (!label) errors.push(`${row}：表示名を入力してください`);
    else if (label.length > MAX_LABEL_LENGTH) errors.push(`${row}：表示名は ${MAX_LABEL_LENGTH} 文字以内にしてください`);
    for (const [lang, v] of Object.entries(it.labels ?? {})) {
      if (!(LABEL_LANGS as readonly string[]).includes(lang)) errors.push(`${row}：対応していない言語です: ${lang}`);
      else if ((v ?? '').trim().length > MAX_LABEL_LENGTH) errors.push(`${row}：表示名（${lang}）は ${MAX_LABEL_LENGTH} 文字以内にしてください`);
    }
  });
  if (!c.items.some((i) => i.active)) errors.push('使用中の選択値が 1 つもありません');
  return errors;
}

/** 保存用に整える（前後の空白を除き、並び順を 10, 20, 30 … に振り直す） */
export const normalizeCategory = (c: OptionCategory): OptionCategory => ({
  ...c,
  items: c.items.map((it, i) => {
    const labels = normalizeLabels(it.labels);
    return { code: it.code.trim(), label: it.label.trim(), active: !!it.active, sortOrder: (i + 1) * 10, ...(labels ? { labels } : {}) };
  }),
});

/** 言語ごとの表示名を整える（空は除く。全部空なら undefined） */
export function normalizeLabels(l: Record<string, string> | undefined): Record<string, string> | undefined {
  const out: Record<string, string> = {};
  for (const lang of LABEL_LANGS) {
    const v = (l?.[lang] ?? '').trim();
    if (v) out[lang] = v;
  }
  return Object.keys(out).length ? out : undefined;
}


/** 監査ログ用の変更の要約（サーバー backend-node/src/options.ts と同じ） */
export function summarizeOptionChange(before: OptionItem[], after: OptionItem[]): string {
  const b = new Map(before.map((i) => [i.code, i]));
  const parts: string[] = [];
  for (const a of after) {
    const o = b.get(a.code);
    if (!o) parts.push(`追加:${a.code}`);
    else {
      if (o.label !== a.label) parts.push(`表示名:${o.label}→${a.label}`);
      for (const lang of LABEL_LANGS) if ((o.labels?.[lang] ?? '') !== (a.labels?.[lang] ?? '')) parts.push(`表示名(${lang}):${o.labels?.[lang] ?? ''}→${a.labels?.[lang] ?? ''}`);
      if (o.active && !a.active) parts.push(`使用停止:${a.code}`);
      if (!o.active && a.active) parts.push(`使用再開:${a.code}`);
    }
  }
  const order = (l: OptionItem[]) => [...l].sort((x, y) => x.sortOrder - y.sortOrder).map((i) => i.code).filter((c) => b.has(c)).join('|');
  if (order(before) !== order(after)) parts.push('並べ替え');
  return parts.join(' ').slice(0, 1000);
}

/** 監査ログ（項目ごとの変更）用：選択値ごとの「表示名・使用・並び順」（サーバーと同じ。パスのコード内の「.」は「．」） */
export function optionChanges(before: OptionItem[], after: OptionItem[]): { path: string; before: string; after: string }[] {
  const key = (code: string) => code.replace(/\./g, '．');
  const use = (a: boolean | undefined) => (a === undefined ? '' : a ? '使用' : '使用停止');
  const pos = (l: OptionItem[]) => new Map(sortItems(l).map((i, n) => [i.code, n + 1]));
  const b = new Map(before.map((i) => [i.code, i]));
  const pb = pos(before);
  const pa = pos(after);
  const out: { path: string; before: string; after: string }[] = [];
  for (const a of after) {
    const o = b.get(a.code);
    if (!o || o.label !== a.label) out.push({ path: `${key(a.code)}.表示名`, before: o?.label ?? '', after: a.label });
    for (const lang of LABEL_LANGS) {
      const ob = o?.labels?.[lang] ?? '';
      const oa = a.labels?.[lang] ?? '';
      if (ob !== oa) out.push({ path: `${key(a.code)}.表示名(${lang})`, before: ob, after: oa });
    }
    if (!o || o.active !== a.active) out.push({ path: `${key(a.code)}.使用`, before: use(o?.active), after: use(a.active) });
    if (o && pb.get(a.code) !== pa.get(a.code)) out.push({ path: `${key(a.code)}.並び順`, before: String(pb.get(a.code)), after: String(pa.get(a.code)) });
  }
  return out;
}
