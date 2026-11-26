import type { CathReport, Masters, Patient } from '../types/model';
import type { StorageAdapter } from './StorageAdapter';
import { defaultOptionCategories, optionChanges, summarizeOptionChange, type OptionCategory } from '../model/optionMaster';
import { DEFAULT_MASTERS, normalizePatient, normalizeReport } from '../model/defaults';
import samplePatients from '../data/patients.json';
import sampleReports from '../data/reports.json';
import sampleMasters from '../data/masters.json';
import type { AuthUser } from '../auth/permissions';
import { auditDiff } from '../audit/diff';
import type { AuditEntry, AuditQuery } from '../audit/model';

const K = { patients: 'cath.patients', reports: 'cath.reports', masters: 'cath.masters', seeded: 'cath.seeded', audit: 'cath.audit', options: 'cath.optionMasters' };
/** Local Storage 版の監査ログに残す件数（古いものから消す。サーバー版は消さない） */
const LOCAL_AUDIT_MAX = 2000;

function read<T>(key: string, fallback: T): T {
  try {
    const s = localStorage.getItem(key);
    return s ? (JSON.parse(s) as T) : fallback;
  } catch {
    return fallback;
  }
}
function write(key: string, v: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(v));
  } catch (e) {
    throw new Error('LocalStorage への保存に失敗しました（容量超過の可能性があります。画像サイズを確認してください）');
  }
}

export class LocalStorageAdapter implements StorageAdapter {
  readonly kind = 'local' as const;

  /** デモ版のみ: サンプルデータの版。版が変わったら（新しいデモ HTML を開いたら）サンプルを再投入する */
  private readonly sampleVersion: string | undefined = (globalThis as { __DEMO_SEED_VERSION__?: string }).__DEMO_SEED_VERSION__;

  constructor(private readonly actor: () => AuthUser | null = () => null) {
    const seeded = localStorage.getItem(K.seeded);
    if (!seeded || (this.sampleVersion && seeded !== this.sampleVersion)) {
      this.seed();
    }
  }

  private seed() {
    write(K.patients, samplePatients);
    write(K.reports, sampleReports);
    write(K.masters, sampleMasters);
    localStorage.setItem(K.seeded, this.sampleVersion ?? '1');
  }

  // ---------------------------------------------------------------- 監査ログ（このブラウザ内。体験用）
  /** 記録する（容量が足りない時は古いものを捨てて記録する。業務の保存は止めない） */
  record(action: string, targetType: string, targetId: string, detail = '', changes?: AuditEntry['changes']) {
    const u = this.actor();
    const all = read<AuditEntry[]>(K.audit, []);
    const at = new Date().toISOString();
    all.push({
      id: `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`, at, username: u?.username ?? '', displayName: u?.displayName ?? '',
      action, targetType, targetId, detail, ip: 'local', changeCount: changes?.length ?? 0, ...(changes && changes.length ? { changes } : {}),
    });
    let keep = all.slice(-LOCAL_AUDIT_MAX);
    for (;;) {
      try {
        localStorage.setItem(K.audit, JSON.stringify(keep));
        return;
      } catch {
        if (keep.length <= 1) return;
        keep = keep.slice(Math.ceil(keep.length / 4));
      }
    }
  }
  async listAudit(q: AuditQuery) {
    const from = q.from ? new Date(`${q.from}T00:00:00+09:00`).toISOString() : '';
    const to = q.to ? new Date(new Date(`${q.to}T00:00:00+09:00`).getTime() + 86400_000).toISOString() : '';
    const list = read<AuditEntry[]>(K.audit, [])
      .filter((e) => (!from || e.at >= from) && (!to || e.at < to))
      .filter((e) => (!q.username || e.username === q.username) && (!q.action || e.action === q.action))
      .filter((e) => (!q.targetType || e.targetType === q.targetType) && (!q.targetId || e.targetId === q.targetId))
      .reverse()
      .slice(0, Math.max(1, Math.min(q.limit ?? 500, 5000)));
    return q.withChanges ? list : list.map(({ changes: _c, ...e }) => e);
  }
  async reportHistory(reportId: string) {
    const r = read<CathReport[]>(K.reports, []).find((x) => x.id === reportId);
    return read<AuditEntry[]>(K.audit, [])
      .filter((e) => /^(CREATE|DELETE)_/.test(e.action) || (e.action.startsWith('UPDATE_') && e.changeCount > 0))
      .filter((e) => (e.targetType === 'report' && e.targetId === reportId) || (!!r && e.targetType === 'patient' && e.targetId === r.patientRef && e.changeCount > 0))
      .reverse();
  }

  async listPatients() {
    return read<Patient[]>(K.patients, []).map((p) => normalizePatient(p));
  }
  async getPatient(id: string) {
    const p = read<Patient[]>(K.patients, []).find((x) => x.id === id);
    return p ? normalizePatient(p) : null;
  }
  async savePatient(p: Patient) {
    const all = read<Patient[]>(K.patients, []);
    const i = all.findIndex((x) => x.id === p.id);
    const old = i >= 0 ? all[i] : null;
    if (i >= 0) all[i] = p;
    else all.push(p);
    write(K.patients, all);
    const changes = auditDiff(old ? normalizePatient(old) : null, p);
    if (!old || changes.length) this.record(old ? 'UPDATE_PATIENT' : 'CREATE_PATIENT', 'patient', p.id, '', changes);
    return p;
  }
  async deletePatient(id: string) {
    write(K.patients, read<Patient[]>(K.patients, []).filter((x) => x.id !== id));
    this.record('DELETE_PATIENT', 'patient', id);
  }
  async listReports() {
    return read<CathReport[]>(K.reports, []).map((r) => normalizeReport(r));
  }
  async getReport(id: string) {
    const r = read<CathReport[]>(K.reports, []).find((x) => x.id === id);
    return r ? normalizeReport(r) : null;
  }
  async saveReport(r: CathReport) {
    const all = read<CathReport[]>(K.reports, []);
    const i = all.findIndex((x) => x.id === r.id);
    const old = i >= 0 ? all[i] : null;
    if (i >= 0) all[i] = r;
    else all.push(r);
    write(K.reports, all);
    const before = old ? normalizeReport(old) : null;
    const detail = [before?.status !== r.status ? `status:${before?.status ?? '-'}→${r.status}` : '', !!before?.verified !== !!r.verified ? `verified:${!!r.verified}` : '']
      .filter(Boolean).join(' ');
    this.record(old ? 'UPDATE_REPORT' : 'CREATE_REPORT', 'report', r.id, detail, auditDiff(before, r));
    return r;
  }
  async deleteReport(id: string) {
    write(K.reports, read<CathReport[]>(K.reports, []).filter((x) => x.id !== id));
    this.record('DELETE_REPORT', 'report', id);
  }
  async getMasters() {
    return { ...DEFAULT_MASTERS, ...read<Masters>(K.masters, DEFAULT_MASTERS) };
  }
  async saveMasters(m: Masters) {
    write(K.masters, m);
    this.record('UPDATE_MASTERS', 'masters', 'default');
    return m;
  }
  async getOptionMasters() {
    return read<OptionCategory[] | null>(K.options, null);
  }
  async saveOptionCategory(c: OptionCategory) {
    const all = read<OptionCategory[]>(K.options, []);
    const old = all.find((x) => x.code === c.code);
    if ((old?.version ?? 0) !== (c.version ?? 0)) throw new Error('この選択値は他の画面で更新されています。開き直してください');
    const saved: OptionCategory = { ...c, version: (old?.version ?? 0) + 1, updatedAt: new Date().toISOString() };
    write(K.options, [...all.filter((x) => x.code !== c.code), saved]);
    const before = old?.items ?? defaultOptionCategories().find((x) => x.code === c.code)?.items ?? [];
    this.record('UPDATE_OPTIONS', 'option', c.code, summarizeOptionChange(before, saved.items), optionChanges(before, saved.items));
    return saved;
  }
  async resetWithSample() {
    this.seed();
    this.record('SEED', 'all', '');
  }
}
