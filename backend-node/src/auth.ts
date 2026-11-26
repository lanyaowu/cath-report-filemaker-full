/** 認証（ログイン・トークン検査）と監査ログ */
import { randomBytes } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { Router, type NextFunction, type Request, type Response } from 'express';
import type { Document } from 'mongodb';
import { config } from './config.js';
import { coll } from './db.js';
import type { AuditChange } from './auditDiff.js';
import { can, issueToken, LoginThrottle, PERMISSION_LABEL, verifyPassword, verifyToken, type AuthUser, type Permission, type Role } from './security.js';

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Express {
    interface Request {
      user?: AuthUser;
    }
  }
}

interface UserDef extends AuthUser { password: string; disabled?: boolean }

const DEV_USER: AuthUser = { username: 'dev', displayName: '開発ユーザー（認証なし）', roles: ['admin'] };
const secret = config.authSecret || randomBytes(32).toString('hex');
const throttle = new LoginThrottle();
let users: Map<string, UserDef> = new Map();

export function loadUsers() {
  if (!config.authEnabled) {
    console.warn('[auth] AUTH_ENABLED=false：認証なしで動作します（開発専用）');
    return;
  }
  if (!config.authSecret) console.warn('[auth] AUTH_SECRET が未設定のため、起動ごとに鍵を生成します（再起動でログアウトされます）');
  const list = JSON.parse(readFileSync(config.usersFile, 'utf-8')) as UserDef[];
  users = new Map(list.filter((u) => !u.disabled).map((u) => [u.username, { ...u, roles: u.roles as Role[] }]));
  console.log(`[auth] 利用者 ${users.size} 名を読み込みました: ${config.usersFile}`);
}

// ---------------------------------------------------------------- 監査ログ
export const AUDIT = 'audit_log';

export async function audit(req: Request, action: string, targetType = '', targetId = '', detail = '', changes?: AuditChange[]) {
  const u = req.user;
  const doc = {
    at: new Date().toISOString(), username: u?.username ?? '', displayName: u?.displayName ?? '',
    action, targetType, targetId, detail, ip: req.ip ?? '',
    // 変わった項目（保存の時。パス・変更前・変更後）
    changeCount: changes?.length ?? 0, ...(changes && changes.length ? { changes } : {}),
  };
  try {
    await coll(AUDIT).insertOne(doc as Document);
  } catch (e) {
    console.error('[audit] 記録に失敗しました', e, doc); // 監査ログの失敗で業務を止めない（ログには残す）
  }
}

// ---------------------------------------------------------------- 認証の検査（/api 配下）
const PUBLIC = new Set(['GET /health', 'POST /auth/login']);

export function authenticate(req: Request, res: Response, next: NextFunction) {
  if (req.method === 'OPTIONS' || PUBLIC.has(`${req.method} ${req.path}`)) return next();
  if (!config.authEnabled) {
    req.user = DEV_USER;
    return next();
  }
  const h = req.get('authorization') ?? '';
  const user = h.startsWith('Bearer ') ? verifyToken(h.slice(7), secret) : null;
  if (!user || !users.has(user.username)) return res.status(401).json({ error: 'ログインが必要です（期限切れの場合は再ログインしてください）' });
  req.user = { ...user, roles: users.get(user.username)!.roles }; // 役割は最新の定義を使う
  return next();
}

/** 権限がなければ 403 */
export const allow = (p: Permission) => (req: Request, res: Response, next: NextFunction) =>
  can(req.user, p) ? next() : res.status(403).json({ error: `この操作の権限がありません（${PERMISSION_LABEL[p]}）` });

// ---------------------------------------------------------------- ログイン API
export const authApi = Router();

authApi.post('/auth/login', async (req, res) => {
  const username = String(req.body?.username ?? '').trim();
  const password = String(req.body?.password ?? '');
  if (!config.authEnabled) return res.json({ token: 'auth-disabled', expiresAt: null, user: DEV_USER });
  const until = throttle.lockedUntil(username);
  if (until) {
    await audit(req, 'LOGIN_LOCKED', 'user', username);
    return res.status(429).json({ error: `ログインに続けて失敗したため、${new Date(until).toLocaleTimeString('ja-JP')} までログインできません` });
  }
  const u = users.get(username);
  if (!u || !verifyPassword(password, u.password)) {
    throttle.fail(username);
    await audit(req, 'LOGIN_FAILURE', 'user', username);
    return res.status(401).json({ error: 'ユーザー名またはパスワードが違います' });
  }
  throttle.success(username);
  const user: AuthUser = { username: u.username, displayName: u.displayName, roles: u.roles };
  req.user = user;
  await audit(req, 'LOGIN', 'user', username);
  res.json({ ...issueToken(user, secret, config.authTokenTtlMinutes), user });
});

authApi.get('/auth/me', (req, res) => res.json(req.user));

authApi.post('/auth/logout', async (req, res) => {
  await audit(req, 'LOGOUT', 'user', req.user?.username ?? '');
  res.status(204).end();
});

/** API の形：_id を id（文字列）に。変更の記録を始める前の記録は changeCount 0 */
export const auditOut = ({ _id, ...d }: Document) => ({ id: String(_id), changeCount: 0, ...d });

/** 監査ログの検索（管理者のみ）。withChanges=true で変わった項目も返す */
authApi.get('/audit', allow('audit'), async (req, res, next) => {
  try {
    const { from, to, username, action, targetType, targetId, withChanges } = req.query as Record<string, string | undefined>;
    const f: Record<string, unknown> = {};
    // 期間は日本時間の日付（YYYY-MM-DD）。at は UTC の ISO 文字列
    const jst = (d: string, add = 0) => new Date(new Date(`${d}T00:00:00+09:00`).getTime() + add * 86400_000).toISOString();
    if (from || to) f.at = { ...(from ? { $gte: jst(from) } : {}), ...(to ? { $lt: jst(to, 1) } : {}) };
    if (username) f.username = username;
    if (action) f.action = action;
    if (targetType) f.targetType = targetType;
    if (targetId) f.targetId = targetId;
    const limit = Math.max(1, Math.min(Number(req.query.limit ?? 500) || 500, 5000));
    const list = await coll(AUDIT)
      .find(f, withChanges === 'true' ? {} : { projection: { changes: 0 } })
      .sort({ at: -1, _id: -1 })
      .limit(limit)
      .toArray();
    res.json(list.map(auditOut));
  } catch (e) {
    next(e);
  }
});
