/**
 * 選択値マスタ（画面の選択肢）の入力チェックと変更内容の要約。
 * 画面（frontend/src/model/optionMaster.ts の validateCategory）と同じ規則をサーバーでも強制する。
 *
 * MongoDB のドキュメント（コレクション option_categories、_id = カテゴリコード）：
 *   { _id: 'APPROACH', name, screen, editable, version, updatedAt, updatedBy,
 *     items: [{ code, label, labels?: { en: '…', 'zh-CN': '…' }, sortOrder, active }] }   ← 選択値はカテゴリに埋め込む
 *   labels は言語ごとの表示名（無い言語は画面が label を辞書で訳して表示する）
 * 変更前の内容は option_category_history に残す（監査ログ audit_log には要約を記録）。
 */
import { RuleError } from './rules.js';
import type { AuditChange } from './auditDiff.js';

export interface OptionItem {
  code: string;
  label: string;
  sortOrder: number;
  active: boolean;
  /** 言語ごとの表示名（例 { "en": "Radial artery", "zh-CN": "桡动脉" }） */
  labels?: Record<string, string>;
}

/** 表示名を持てる言語（日本語は label） */
export const LABEL_LANGS = ['en', 'zh-CN'] as const;

export interface OptionCategory {
  code: string;
  name: string;
  screen: string;
  editable: boolean;
  items: OptionItem[];
  version: number;
  updatedAt?: string;
  updatedBy?: string;
}

export const MAX_CODE_LENGTH = 50;
export const MAX_LABEL_LENGTH = 200;
export const MAX_ITEMS = 500;

const str = (v: unknown) => (typeof v === 'string' ? v.trim() : '');

/**
 * 保存する選択値を検査して整える（並び順は送られた順に 10, 20, 30 … と振り直す）。
 * - 標準の分類（editable=false）は変更できない
 * - 保存済みのコードは削除できない（使用停止にする）。過去のレポートに保存されている値のため
 */
export function checkOptionItems(old: OptionCategory, body: unknown): OptionItem[] {
  if (!old.editable) throw new RuleError(400, `「${old.name}」は標準の分類のため編集できません`);
  const raw = (body as { items?: unknown })?.items;
  if (!Array.isArray(raw)) throw new RuleError(400, 'items（選択値の一覧）が必要です');
  if (raw.length > MAX_ITEMS) throw new RuleError(400, `選択値は ${MAX_ITEMS} 件までです`);
  const errors: string[] = [];
  const seen = new Set<string>();
  const items = raw.map((r, i): OptionItem => {
    const o = (r ?? {}) as Record<string, unknown>;
    const row = `${i + 1} 行目`;
    const code = str(o.code);
    const label = str(o.label);
    if (!code) errors.push(`${row}：コードを入力してください`);
    else if (code.length > MAX_CODE_LENGTH) errors.push(`${row}：コードは ${MAX_CODE_LENGTH} 文字以内にしてください`);
    else if (seen.has(code)) errors.push(`${row}：コード「${code}」が重複しています`);
    seen.add(code);
    if (!label) errors.push(`${row}：表示名を入力してください`);
    else if (label.length > MAX_LABEL_LENGTH) errors.push(`${row}：表示名は ${MAX_LABEL_LENGTH} 文字以内にしてください`);
    const labels: Record<string, string> = {};
    if (o.labels != null && (typeof o.labels !== 'object' || Array.isArray(o.labels))) errors.push(`${row}：labels の形式が不正です`);
    else
      for (const [lang, v] of Object.entries((o.labels ?? {}) as Record<string, unknown>)) {
        if (!(LABEL_LANGS as readonly string[]).includes(lang)) errors.push(`${row}：対応していない言語です: ${lang}`);
        else if (str(v).length > MAX_LABEL_LENGTH) errors.push(`${row}：表示名（${lang}）は ${MAX_LABEL_LENGTH} 文字以内にしてください`);
        else if (str(v)) labels[lang] = str(v);
      }
    return { code, label, sortOrder: (i + 1) * 10, active: o.active !== false, ...(Object.keys(labels).length ? { labels } : {}) };
  });
  const removed = old.items.filter((o) => !seen.has(o.code)).map((o) => o.code);
  if (removed.length) errors.push(`保存済みの選択値は削除できません（使用停止にしてください）: ${removed.join(', ')}`);
  if (items.length && !items.some((i) => i.active)) errors.push('使用中の選択値が 1 つもありません');
  if (errors.length) throw new RuleError(400, errors.join(' / '));
  return items;
}

/** 監査ログ用の変更の要約（例：追加:IVL 使用停止:Filtrap 表示名:Ryurei→Ryurei NC 並べ替え） */
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

/**
 * 監査ログ（項目ごとの変更）用：選択値ごとの「表示名・使用・並び順」の変更前→変更後。
 * パスは「コード.項目」（コードの中の「.」は全角の「．」に置き換え。監査画面がパスを「.」で区切るため）。
 */
export function optionChanges(before: OptionItem[], after: OptionItem[]): AuditChange[] {
  const key = (code: string) => code.replace(/\./g, '．');
  const use = (a: boolean | undefined) => (a === undefined ? '' : a ? '使用' : '使用停止');
  const pos = (l: OptionItem[]) => new Map([...l].sort((x, y) => x.sortOrder - y.sortOrder).map((i, n) => [i.code, n + 1]));
  const b = new Map(before.map((i) => [i.code, i]));
  const pb = pos(before);
  const pa = pos(after);
  const out: AuditChange[] = [];
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
