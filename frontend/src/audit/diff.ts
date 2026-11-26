/**
 * 監査ログ：保存前後の JSON を比べて、変わった項目（パス・変更前・変更後）を取り出す。
 *
 * 全バックエンド・Thymeleaf 版で同じ規則（Java は audit/AuditDiff.java、レビュー版は tools/review/engine.js、
 * Node.js は backend-node/src/auditDiff.ts。変える時は全部そろえる）。
 *  - JSON を「パス → 文字列」に平らにして比べる（配列は番号：pci.lesions.0.target）
 *  - 記録しない：先頭の version・updatedAt・createdAt・history・_id（サーバーが付ける値・登録履歴）、
 *    どこにあっても dataUrl（画像本体。代わりにファイル名などのメタ情報の変化が残る）
 *  - null・false・項目なしは、空（''）と同じとみなす（チェックを外す true→false は記録される）
 *  - 値は 200 文字までに切る。1 回の保存で記録するのは 1,000 項目まで
 */
export interface AuditChange {
  path: string;
  before: string;
  after: string;
}

export const AUDIT_EXCLUDE_TOP = new Set(['version', 'updatedAt', 'createdAt', 'history', '_id']);
export const AUDIT_EXCLUDE_KEY = new Set(['dataUrl']);
export const AUDIT_MAX_VALUE = 200;
export const AUDIT_MAX_CHANGES = 1000;

function flatten(v: unknown, prefix: string, out: Map<string, string>) {
  if (v === null || v === undefined) {
    if (prefix) out.set(prefix, '');
    return;
  }
  if (Array.isArray(v)) {
    v.forEach((x, i) => flatten(x, prefix ? `${prefix}.${i}` : String(i), out));
    return;
  }
  if (typeof v === 'object') {
    for (const [k, x] of Object.entries(v as Record<string, unknown>)) {
      if (!prefix && AUDIT_EXCLUDE_TOP.has(k)) continue;
      if (AUDIT_EXCLUDE_KEY.has(k)) continue;
      flatten(x, prefix ? `${prefix}.${k}` : k, out);
    }
    return;
  }
  if (!prefix) return;
  out.set(prefix, typeof v === 'boolean' ? (v ? 'true' : '') : String(v));
}

export function flattenForAudit(v: unknown): Map<string, string> {
  const m = new Map<string, string>();
  flatten(v, '', m);
  return m;
}

const cut = (s: string) => (s.length > AUDIT_MAX_VALUE ? `${s.slice(0, AUDIT_MAX_VALUE)}…` : s);

/** before が null なら新規（空でない項目だけが残る） */
export function auditDiff(before: unknown, after: unknown): AuditChange[] {
  const b = flattenForAudit(before ?? {});
  const a = flattenForAudit(after ?? {});
  const out: AuditChange[] = [];
  const push = (path: string) => {
    const x = b.get(path) ?? '';
    const y = a.get(path) ?? '';
    if (x !== y && out.length < AUDIT_MAX_CHANGES) out.push({ path, before: cut(x), after: cut(y) });
  };
  for (const k of a.keys()) push(k);
  for (const k of b.keys()) if (!a.has(k)) push(k);
  return out;
}
