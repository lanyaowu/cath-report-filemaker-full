/**
 * 認証・権限の中核（依存なし。Spring 版の jp.example.cathreport.security と同じ仕様）
 *  - パスワード：PBKDF2-HMAC-SHA256  形式 "pbkdf2_sha256$反復回数$salt(Base64)$hash(Base64)"
 *  - トークン　：base64url(JSON {sub,name,roles,exp}) + "." + base64url(HMAC-SHA256(secret, 前半))
 */
import { createHmac, pbkdf2Sync, randomBytes, timingSafeEqual } from 'node:crypto';

export type Role = 'admin' | 'doctor' | 'secretary' | 'viewer';
export type Permission = 'read' | 'edit' | 'confirm' | 'verify' | 'deleteReport' | 'deletePatient' | 'masters' | 'seed' | 'audit';

export interface AuthUser {
  username: string;
  displayName: string;
  roles: Role[];
}

/** 役割ごとの権限（全バックエンド・Thymeleaf 版で共通） */
export const PERMISSIONS: Record<Permission, Role[]> = {
  read: ['admin', 'doctor', 'secretary', 'viewer'],
  edit: ['admin', 'doctor', 'secretary'],
  confirm: ['admin', 'doctor'],
  verify: ['admin', 'doctor'],
  deleteReport: ['admin', 'doctor'],
  deletePatient: ['admin'],
  masters: ['admin'],
  seed: ['admin'],
  audit: ['admin'],
};

export const PERMISSION_LABEL: Record<Permission, string> = {
  read: '閲覧', edit: '編集', confirm: '確定・確定解除', verify: '照合', deleteReport: 'レポート削除',
  deletePatient: '患者削除', masters: 'マスタ編集', seed: 'サンプルデータ投入', audit: '監査ログの閲覧',
};

export const can = (u: AuthUser | null | undefined, p: Permission) => !!u && u.roles.some((r) => PERMISSIONS[p].includes(r));

// ---------------------------------------------------------------- パスワード
const ITERATIONS = 120_000;

export function hashPassword(password: string, iterations = ITERATIONS, salt = randomBytes(16)): string {
  const hash = pbkdf2Sync(password, salt, iterations, 32, 'sha256');
  return `pbkdf2_sha256$${iterations}$${salt.toString('base64')}$${hash.toString('base64')}`;
}

export function verifyPassword(password: string, stored: string): boolean {
  const [alg, it, saltB64, hashB64] = String(stored ?? '').split('$');
  if (alg !== 'pbkdf2_sha256' || !it || !saltB64 || !hashB64) return false;
  const expected = Buffer.from(hashB64, 'base64');
  const actual = pbkdf2Sync(password, Buffer.from(saltB64, 'base64'), Number(it), expected.length, 'sha256');
  return expected.length === actual.length && timingSafeEqual(expected, actual);
}

// ---------------------------------------------------------------- トークン
const b64u = (b: Buffer) => b.toString('base64url');
const sign = (secret: string, data: string) => createHmac('sha256', secret).update(data).digest();

export function issueToken(u: AuthUser, secret: string, ttlMinutes: number, now = Date.now()): { token: string; expiresAt: string } {
  const exp = Math.floor(now / 1000) + ttlMinutes * 60;
  const payload = b64u(Buffer.from(JSON.stringify({ sub: u.username, name: u.displayName, roles: u.roles, exp }), 'utf-8'));
  return { token: `${payload}.${b64u(sign(secret, payload))}`, expiresAt: new Date(exp * 1000).toISOString() };
}

/** 正しいトークンなら利用者を返す（署名不一致・期限切れ・形式不正は null） */
export function verifyToken(token: string, secret: string, now = Date.now()): AuthUser | null {
  const [payload, sig, extra] = String(token ?? '').split('.');
  if (!payload || !sig || extra !== undefined) return null;
  const expected = sign(secret, payload);
  const actual = Buffer.from(sig, 'base64url');
  if (expected.length !== actual.length || !timingSafeEqual(expected, actual)) return null;
  try {
    const p = JSON.parse(Buffer.from(payload, 'base64url').toString('utf-8'));
    if (typeof p.exp !== 'number' || p.exp * 1000 <= now) return null;
    return { username: String(p.sub), displayName: String(p.name ?? p.sub), roles: Array.isArray(p.roles) ? p.roles : [] };
  } catch {
    return null;
  }
}

// ---------------------------------------------------------------- ログイン失敗の制限
export class LoginThrottle {
  private readonly fails = new Map<string, { count: number; until: number }>();
  private readonly maxFailures: number;
  private readonly lockMinutes: number;
  constructor(maxFailures = 5, lockMinutes = 15) {
    this.maxFailures = maxFailures;
    this.lockMinutes = lockMinutes;
  }
  /** ロック中なら解除時刻（ms）を返す */
  lockedUntil(username: string, now = Date.now()): number | null {
    const f = this.fails.get(username);
    return f && f.until > now ? f.until : null;
  }
  fail(username: string, now = Date.now()) {
    const f = this.fails.get(username);
    const count = (f && f.until <= now && f.count >= this.maxFailures ? 0 : f?.count ?? 0) + 1;
    this.fails.set(username, { count, until: count >= this.maxFailures ? now + this.lockMinutes * 60_000 : 0 });
  }
  success(username: string) {
    this.fails.delete(username);
  }
}
