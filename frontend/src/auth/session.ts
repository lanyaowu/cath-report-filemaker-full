import type { AuthUser } from './permissions';

/** ログイン情報（タブを閉じると消える sessionStorage に保存。保存先 URL ごと） */
export interface AuthSession {
  token: string;
  expiresAt: string | null;
  user: AuthUser;
}

const key = (url: string) => `cath.auth:${url}`;

export function loadSession(url: string): AuthSession | null {
  try {
    const s = JSON.parse(sessionStorage.getItem(key(url)) ?? 'null') as AuthSession | null;
    if (!s?.token) return null;
    if (s.expiresAt && Date.parse(s.expiresAt) <= Date.now()) {
      sessionStorage.removeItem(key(url));
      return null;
    }
    return s;
  } catch {
    return null;
  }
}

export function saveSession(url: string, s: AuthSession) {
  try {
    sessionStorage.setItem(key(url), JSON.stringify(s));
  } catch {
    /* 保存できなくてもメモリ上のトークンで動作する */
  }
}

export function clearSession(url: string) {
  try {
    sessionStorage.removeItem(key(url));
  } catch {
    /* noop */
  }
}
