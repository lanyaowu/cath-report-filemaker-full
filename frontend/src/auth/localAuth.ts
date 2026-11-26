import type { AuthUser, Role } from './permissions';
import users from '../data/users.json';

/**
 * Local Storage（デモ）用のログイン。
 * サーバーと同じ利用者定義（sample-data/users.json：PBKDF2-SHA256 のハッシュ）で、ブラウザ内で照合する。
 * 画面の体験用であり、端末内のデータを守るものではない（本番は Remote DB に固定し、サーバーで認証する）。
 */
interface UserDef { username: string; displayName: string; roles: string[]; password: string }

const defs = users as UserDef[];

/** ログイン画面に出すデモ用の利用者（パスワードは README と同じ demo-<ユーザー名>） */
export const DEMO_USERS: AuthUser[] = defs.map((u) => ({ username: u.username, displayName: u.displayName, roles: u.roles as Role[] }));

const b64 = (s: string) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));

export async function localLogin(username: string, password: string): Promise<AuthUser> {
  const fail = () => new Error('ユーザー名またはパスワードが違います');
  const u = defs.find((x) => x.username === username);
  const [alg, iter, salt, hash] = (u?.password ?? '').split('$');
  if (!u || alg !== 'pbkdf2_sha256') throw fail();
  const subtle = globalThis.crypto?.subtle;
  if (!subtle) throw new Error('このブラウザではパスワードを確認できません（https または ファイルとして開いてください）');
  const key = await subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']);
  const want = b64(hash);
  const got = new Uint8Array(
    await subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt: b64(salt), iterations: Number(iter) }, key, want.length * 8),
  );
  let diff = got.length ^ want.length;
  for (let i = 0; i < want.length; i++) diff |= got[i] ^ want[i];
  if (diff !== 0) throw fail();
  return { username: u.username, displayName: u.displayName, roles: u.roles as Role[] };
}
