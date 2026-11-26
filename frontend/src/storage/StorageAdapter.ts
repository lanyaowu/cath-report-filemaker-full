import type { CathReport, Masters, Patient } from '../types/model';
import type { AuditEntry, AuditQuery } from '../audit/model';
import type { OptionCategory } from '../model/optionMaster';

export type StorageKind = 'local' | 'remote';

/**
 * 永続化の抽象。LocalStorage 版と Remote(REST→MongoDB) 版を同一インターフェースで切替える。
 * Remote の REST API 仕様は Node 版 / Spring Boot 版バックエンドで共通（docs/api.md 参照）。
 */
export interface StorageAdapter {
  readonly kind: StorageKind;
  listPatients(): Promise<Patient[]>;
  getPatient(id: string): Promise<Patient | null>;
  savePatient(p: Patient): Promise<Patient>;
  deletePatient(id: string): Promise<void>;
  listReports(): Promise<CathReport[]>;
  getReport(id: string): Promise<CathReport | null>;
  saveReport(r: CathReport): Promise<CathReport>;
  deleteReport(id: string): Promise<void>;
  getMasters(): Promise<Masters>;
  saveMasters(m: Masters): Promise<Masters>;
  /** 選択値マスタ（保存済みのカテゴリ。サーバーが未対応・未保存なら null → プログラムの初期値を使う） */
  getOptionMasters(): Promise<OptionCategory[] | null>;
  /** 選択値マスタの 1 カテゴリを保存（version が保存時と違えばエラー） */
  saveOptionCategory(c: OptionCategory): Promise<OptionCategory>;
  /** サンプルデータを投入（既存データは置換） */
  resetWithSample(): Promise<void>;
  /** 監査ログの検索（新しい順。管理者のみ） */
  listAudit(q: AuditQuery): Promise<AuditEntry[]>;
  /** レポートの変更履歴（そのレポートと患者の作成・削除と、項目が変わった更新。変わった項目つき。新しい順） */
  reportHistory(reportId: string): Promise<AuditEntry[]>;
}
