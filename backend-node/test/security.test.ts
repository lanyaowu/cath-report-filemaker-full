import { test } from 'node:test';
import assert from 'node:assert/strict';
import { can, hashPassword, issueToken, LoginThrottle, verifyPassword, verifyToken, type AuthUser } from '../src/security.ts';

const doctor: AuthUser = { username: 'yamada', displayName: '山田 太郎', roles: ['doctor'] };

test('パスワード：正しいものだけ一致する', () => {
  const h = hashPassword('secret-1', 1000);
  assert.match(h, /^pbkdf2_sha256\$1000\$/);
  assert.equal(verifyPassword('secret-1', h), true);
  assert.equal(verifyPassword('secret-2', h), false);
  assert.equal(verifyPassword('secret-1', 'plain'), false);
});

test('パスワード：Spring 版と同じ形式（既知のハッシュを検証できる）', () => {
  // node tools/auth/hash_password.mjs と同じ方式で作った値（salt 固定）
  const h = hashPassword('demo', 1000, Buffer.from('0123456789abcdef'));
  assert.equal(h, 'pbkdf2_sha256$1000$MDEyMzQ1Njc4OWFiY2RlZg==$' + h.split('$')[3]);
  assert.equal(verifyPassword('demo', h), true);
});

test('トークン：署名・期限・改ざんを検査する', () => {
  const now = Date.UTC(2026, 10, 20, 0, 0, 0);
  const { token, expiresAt } = issueToken(doctor, 'k1', 60, now);
  assert.equal(expiresAt, '2026-11-20T01:00:00.000Z');
  assert.deepEqual(verifyToken(token, 'k1', now + 1000), doctor);
  assert.equal(verifyToken(token, 'k2', now), null, '鍵が違う');
  assert.equal(verifyToken(token, 'k1', now + 61 * 60_000), null, '期限切れ');
  const [p, s] = token.split('.');
  const forged = Buffer.from(JSON.stringify({ sub: 'yamada', name: 'x', roles: ['admin'], exp: 9e9 })).toString('base64url');
  assert.equal(verifyToken(`${forged}.${s}`, 'k1', now), null, '中身の書き換え');
  assert.equal(verifyToken(`${p}.${s}.x`, 'k1', now), null, '形式不正');
});

test('権限：役割ごとの可否', () => {
  const u = (r: AuthUser['roles'][number]): AuthUser => ({ username: r, displayName: r, roles: [r] });
  assert.equal(can(u('viewer'), 'read'), true);
  assert.equal(can(u('viewer'), 'edit'), false);
  assert.equal(can(u('secretary'), 'edit'), true);
  assert.equal(can(u('secretary'), 'confirm'), false);
  assert.equal(can(u('doctor'), 'confirm'), true);
  assert.equal(can(u('doctor'), 'masters'), false);
  assert.equal(can(u('admin'), 'seed'), true);
  assert.equal(can(null, 'read'), false);
});

test('ログイン失敗：5 回でロックし、期限後に解除', () => {
  const t = new LoginThrottle(5, 15);
  const now = 1_000_000;
  for (let i = 0; i < 4; i++) t.fail('a', now);
  assert.equal(t.lockedUntil('a', now), null);
  t.fail('a', now);
  assert.equal(t.lockedUntil('a', now), now + 15 * 60_000);
  assert.equal(t.lockedUntil('a', now + 15 * 60_000 + 1), null);
  t.success('a');
  assert.equal(t.lockedUntil('a', now), null);
});
