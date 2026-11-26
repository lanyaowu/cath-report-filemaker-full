/**
 * レポート保存時の業務ルール（サーバー側で強制する。Spring 版の ReportRules と同じ仕様）
 *  1. 権限：編集・確定/確定解除（status の変更）・照合（verified の変更）
 *  2. 確定ロック：確定済みのまま保存する場合、ステータス・照合・登録者・履歴以外は変更不可
 *  3. 登録履歴：既存の履歴は変更・削除不可（追加のみ）。追加分の記録者はログイン中の利用者
 */
import { can, PERMISSION_LABEL, type AuthUser, type Permission } from './security.js';

export class RuleError extends Error {
  readonly status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export const LOCKED_STATUS = '確定';
/** 確定済みでも変更できる項目（画面の UNLOCKED と同じ）と、比較の対象外（サーバーが管理する項目） */
const IGNORE_TOP = new Set(['id', '_id', 'status', 'verified', 'history', 'version', 'createdAt', 'updatedAt']);
const IGNORE_HEADER = new Set(['registrant']);

export function requirePermission(u: AuthUser | undefined, p: Permission) {
  if (!can(u, p)) throw new RuleError(403, `この操作の権限がありません（${PERMISSION_LABEL[p]}）`);
}

/** JSON として等しいか（キーの順序は無視。undefined のキーは無いものとみなす） */
export function jsonEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (a === null || b === null || typeof a !== 'object' || typeof b !== 'object') return false;
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  if (Array.isArray(a)) {
    const bb = b as unknown[];
    return a.length === bb.length && a.every((v, i) => jsonEqual(v, bb[i]));
  }
  const ka = Object.keys(a).filter((k) => (a as Record<string, unknown>)[k] !== undefined);
  const kb = Object.keys(b).filter((k) => (b as Record<string, unknown>)[k] !== undefined);
  return ka.length === kb.length && ka.every((k) => jsonEqual((a as Record<string, unknown>)[k], (b as Record<string, unknown>)[k]));
}

function lockedContent(r: Record<string, unknown>) {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(r)) {
    if (IGNORE_TOP.has(k)) continue;
    if (k === 'header' && v && typeof v === 'object') {
      out.header = Object.fromEntries(Object.entries(v).filter(([hk]) => !IGNORE_HEADER.has(hk)));
    } else out[k] = v;
  }
  return out;
}

type Report = Record<string, unknown> & { status?: unknown; verified?: unknown; history?: unknown };

/** 保存してよいか検査する（違反は RuleError）。old は保存済みのレポート（新規は null） */
export function checkReportSave(u: AuthUser | undefined, old: Report | null, neu: Report) {
  requirePermission(u, 'edit');
  const oldStatus = String(old?.status ?? '入力中');
  const newStatus = String(neu.status ?? '入力中');
  if (oldStatus !== newStatus) requirePermission(u, 'confirm');
  if (!!old?.verified !== !!neu.verified) requirePermission(u, 'verify');
  if (!old) return;
  if (oldStatus === LOCKED_STATUS && newStatus === LOCKED_STATUS && !jsonEqual(lockedContent(old), lockedContent(neu))) {
    throw new RuleError(409, '確定済みのため編集できません（ステータスを「入力中」に戻してください）');
  }
  const oldH = Array.isArray(old.history) ? old.history : [];
  const newH = Array.isArray(neu.history) ? neu.history : [];
  if (newH.length < oldH.length || !oldH.every((h, i) => jsonEqual(h, newH[i]))) {
    throw new RuleError(409, '登録履歴は変更・削除できません（追加のみ）');
  }
}

/** 今回追加された履歴の記録者をログイン中の利用者にする。追加がなければ1件追加する */
export function stampHistory(u: AuthUser, oldLength: number, neu: Report, now = new Date().toISOString()) {
  const h: Record<string, unknown>[] = Array.isArray(neu.history) ? [...(neu.history as Record<string, unknown>[])] : [];
  if (h.length <= oldLength) h.push({ at: now, by: u.displayName, action: oldLength === 0 ? '新規作成' : '保存' });
  for (let i = oldLength; i < h.length; i++) h[i] = { ...h[i], by: u.displayName };
  neu.history = h;
}

/** 楽観ロック：保存済み（version 無しは 0）と送られた version を照合 */
export function checkVersion(kind: 'レポート' | '患者' | '選択値マスタ', stored: { version?: unknown } | null, sent: unknown): number {
  if (!stored) return 0;
  const current = Number(stored.version ?? 0);
  if (sent === undefined || sent === null || sent === '') {
    throw new RuleError(409, `version が必要です（この${kind}を再読み込みしてから保存してください）`);
  }
  if (Number(sent) !== current) throw new RuleError(409, `この${kind}は他の端末で更新されています。再読み込みしてください`);
  return current + 1;
}
