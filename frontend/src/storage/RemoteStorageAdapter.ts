import type { CathReport, Masters, Patient } from '../types/model';
import type { StorageAdapter } from './StorageAdapter';
import type { OptionCategory } from '../model/optionMaster';
import { DEFAULT_MASTERS, normalizePatient, normalizeReport } from '../model/defaults';

import type { AuthUser } from '../auth/permissions';
import type { AuditEntry, AuditQuery } from '../audit/model';

/** ログインが必要（401） */
export class AuthError extends Error {}

/** トークンの取得と、401 を受けたときの通知（AppContext が設定） */
export interface AuthHooks {
  token: () => string | null;
  onUnauthorized: () => void;
  /** ログイン中の利用者（Local Storage 版の監査ログに記録する） */
  user?: () => AuthUser | null;
}
const NO_AUTH: AuthHooks = { token: () => null, onUnauthorized: () => undefined };

export interface LoginResult {
  token: string;
  expiresAt: string | null;
  user: AuthUser;
}

/** {"error": "..."}（全バックエンド共通形式）からメッセージを取り出す */
async function errorMessage(res: Response, fallback: string): Promise<string> {
  const text = await res.text().catch(() => '');
  try {
    return (JSON.parse(text) as { error?: string }).error ?? (text || fallback);
  } catch {
    return text || fallback;
  }
}

/** REST API 経由で永続化（Node+MongoDB / Spring Boot+MongoDB / Spring Boot+PostgreSQL のいずれも同じ API） */
export class RemoteStorageAdapter implements StorageAdapter {
  readonly kind = 'remote' as const;
  private readonly baseUrl: string;
  private readonly auth: AuthHooks;

  constructor(baseUrl: string, auth: AuthHooks = NO_AUTH) {
    this.baseUrl = baseUrl;
    this.auth = auth;
  }

  private async req<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = {};
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    const token = this.auth.token();
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(`${this.baseUrl.replace(/\/$/, '')}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
    if (res.status === 401 && path !== '/auth/login') {
      // ログインが必要（未ログイン・期限切れ）。画面にログインダイアログを出してもらう
      this.auth.onUnauthorized();
      throw new AuthError(await errorMessage(res, 'ログインが必要です'));
    }
    if (res.status === 404) return null as T;
    if (!res.ok) {
      const msg = await errorMessage(res, res.statusText);
      // 400・403・409・429 は業務上のメッセージをそのまま表示する
      throw new Error([400, 403, 409, 429].includes(res.status) || path === '/auth/login' ? msg : `サーバーエラー ${res.status}: ${msg}`);
    }
    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
  }

  async ping(): Promise<boolean> {
    try {
      await this.req('GET', '/health');
      return true;
    } catch {
      return false;
    }
  }

  async listPatients() {
    return ((await this.req<Patient[]>('GET', '/patients')) ?? []).map(normalizePatient);
  }
  async getPatient(id: string) {
    const p = await this.req<Patient | null>('GET', `/patients/${encodeURIComponent(id)}`);
    return p ? normalizePatient(p) : null;
  }
  async savePatient(p: Patient) {
    return normalizePatient(await this.req<Patient>('PUT', `/patients/${encodeURIComponent(p.id)}`, p));
  }
  async deletePatient(id: string) {
    await this.req('DELETE', `/patients/${encodeURIComponent(id)}`);
  }
  async listReports() {
    // 一覧は画像本体(dataUrl)を除いたプロジェクションで返る
    return ((await this.req<CathReport[]>('GET', '/reports')) ?? []).map(normalizeReport);
  }
  async getReport(id: string) {
    const r = await this.req<CathReport | null>('GET', `/reports/${encodeURIComponent(id)}`);
    return r ? normalizeReport(r) : null;
  }
  async saveReport(r: CathReport) {
    return normalizeReport(await this.req<CathReport>('PUT', `/reports/${encodeURIComponent(r.id)}`, r));
  }
  async deleteReport(id: string) {
    await this.req('DELETE', `/reports/${encodeURIComponent(id)}`);
  }
  async getMasters() {
    return { ...DEFAULT_MASTERS, ...((await this.req<Masters | null>('GET', '/masters')) ?? {}) };
  }
  async saveMasters(m: Masters) {
    return this.req<Masters>('PUT', '/masters', m);
  }
  async getOptionMasters() {
    // 選択値マスタに未対応のバックエンド（404）は null → プログラムの初期値で表示する
    return this.req<OptionCategory[] | null>('GET', '/options');
  }
  async saveOptionCategory(c: OptionCategory) {
    return this.req<OptionCategory>('PUT', `/options/${encodeURIComponent(c.code)}`, c);
  }
  async resetWithSample() {
    await this.req('POST', '/admin/seed');
  }
  // ---------------------------------------------------------------- 監査ログ
  async listAudit(q: AuditQuery) {
    const p = new URLSearchParams();
    for (const [k, v] of Object.entries(q)) if (v !== undefined && v !== '' && v !== false) p.set(k, String(v));
    return (await this.req<AuditEntry[]>('GET', `/audit?${p.toString()}`)) ?? [];
  }
  async reportHistory(reportId: string) {
    return (await this.req<AuditEntry[]>('GET', `/reports/${encodeURIComponent(reportId)}/history`)) ?? [];
  }
  // ---------------------------------------------------------------- 認証
  async login(username: string, password: string): Promise<LoginResult> {
    return this.req<LoginResult>('POST', '/auth/login', { username, password });
  }
  async me(): Promise<AuthUser | null> {
    return this.req<AuthUser | null>('GET', '/auth/me');
  }
  async logout(): Promise<void> {
    await this.req('POST', '/auth/logout');
  }
}
