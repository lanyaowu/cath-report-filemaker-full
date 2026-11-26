import type { AuditChange } from './diff';

/** 監査ログの 1 件（全バックエンド共通の API の形） */
export interface AuditEntry {
  id: string;
  at: string;
  username: string;
  displayName: string;
  action: string;
  targetType: string;
  targetId: string;
  detail: string;
  ip: string;
  /** 変わった項目の数 */
  changeCount: number;
  /** 変わった項目（withChanges のとき・レポートの変更履歴） */
  changes?: AuditChange[];
}

export interface AuditQuery {
  from?: string;
  to?: string;
  username?: string;
  action?: string;
  targetType?: string;
  targetId?: string;
  limit?: number;
  withChanges?: boolean;
}

export const AUDIT_ACTION_LABEL: Record<string, string> = {
  LOGIN: 'ログイン', LOGIN_FAILURE: 'ログイン失敗', LOGIN_LOCKED: 'ログインのロック', LOGOUT: 'ログアウト',
  VIEW_PATIENT: '患者の閲覧', VIEW_REPORT: 'レポートの閲覧',
  CREATE_PATIENT: '患者の登録', UPDATE_PATIENT: '患者の更新', DELETE_PATIENT: '患者の削除',
  CREATE_REPORT: 'レポートの作成', UPDATE_REPORT: 'レポートの更新', DELETE_REPORT: 'レポートの削除',
  UPDATE_MASTERS: 'マスタの更新', UPDATE_OPTIONS: '選択値マスタの更新', SEED: 'サンプルデータの投入',
};
export const actionLabel = (a: string) => AUDIT_ACTION_LABEL[a] ?? a;

export const TARGET_LABEL: Record<string, string> = { patient: '患者', report: 'レポート', user: '利用者', masters: 'マスタ', option: '選択値', all: '全データ' };

/** レポートの変更履歴：確定・確定解除の印を付ける（古い順に見て、確定解除〜次の確定までの変更に印） */
export type HistoryMark = 'confirm' | 'unlock' | 'afterUnlock' | '';

export function markHistory(entriesNewestFirst: AuditEntry[]): Map<string, HistoryMark> {
  const marks = new Map<string, HistoryMark>();
  let unlocked = false;
  for (const e of [...entriesNewestFirst].reverse()) {
    const st = e.targetType === 'report' ? e.changes?.find((c) => c.path === 'status') : undefined;
    let m: HistoryMark = '';
    if (st && st.before === '確定' && st.after !== '確定') {
      m = 'unlock';
      unlocked = true;
    } else if (st && st.after === '確定') {
      m = unlocked && (e.changes?.length ?? 0) > 1 ? 'afterUnlock' : 'confirm';
      unlocked = false;
    } else if (unlocked && e.targetType === 'report' && (e.changes?.length ?? 0) > 0) {
      m = 'afterUnlock';
    }
    marks.set(e.id, m);
  }
  return marks;
}

/** CSV（Excel で開ける UTF-8 BOM 付き）。変更のある記録は項目ごとに 1 行 */
export function auditCsv(entries: AuditEntry[], label: (path: string, targetType: string) => string): string {
  const q = (s: string) => `"${String(s ?? '').replace(/"/g, '""')}"`;
  const rows = [['日時', '利用者', '表示名', '操作', '対象', '対象ID', '詳細', 'IP', '項目', '項目（パス）', '変更前', '変更後']];
  for (const e of entries) {
    const base = [e.at, e.username, e.displayName, actionLabel(e.action), TARGET_LABEL[e.targetType] ?? e.targetType, e.targetId, e.detail, e.ip];
    if (e.changes && e.changes.length) for (const c of e.changes) rows.push([...base, label(c.path, e.targetType), c.path, c.before, c.after]);
    else rows.push([...base, '', '', '', '']);
  }
  return '﻿' + rows.map((r) => r.map(q).join(',')).join('\r\n') + '\r\n';
}
