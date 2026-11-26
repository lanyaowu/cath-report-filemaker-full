import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkReportSave, checkVersion, jsonEqual, RuleError, stampHistory } from '../src/rules.ts';
import type { AuthUser } from '../src/security.ts';

const U = (role: AuthUser['roles'][number]): AuthUser => ({ username: role, displayName: `${role}名`, roles: [role] });
const base = () => ({
  id: 'rp-1', patientRef: 'pt-1', status: '入力中', verified: false,
  header: { studyDate: '2026-11-02', registrant: '山田 太郎' }, cathRecord: { exam: { diagnosis: 'AP' } },
  history: [{ at: '2026-11-02T00:00:00Z', by: '山田 太郎', action: '新規作成' }], version: 2,
});
const err = (fn: () => void) => {
  try { fn(); } catch (e) { if (e instanceof RuleError) return `${e.status} ${e.message}`; throw e; }
  return 'OK';
};

test('jsonEqual：キーの順序と undefined を無視', () => {
  assert.equal(jsonEqual({ a: 1, b: [1, { c: 2 }] }, { b: [1, { c: 2 }], a: 1, d: undefined }), true);
  assert.equal(jsonEqual({ a: 1 }, { a: '1' }), false);
  assert.equal(jsonEqual([1, 2], [2, 1]), false);
});

test('権限：閲覧者は保存できない／秘書は確定・照合できない', () => {
  const old = base();
  assert.match(err(() => checkReportSave(U('viewer'), old, { ...base() })), /^403 .*編集/);
  assert.match(err(() => checkReportSave(U('secretary'), old, { ...base(), status: '確定' })), /^403 .*確定/);
  assert.match(err(() => checkReportSave(U('secretary'), old, { ...base(), verified: true })), /^403 .*照合/);
  assert.equal(err(() => checkReportSave(U('secretary'), old, { ...base(), cathRecord: { exam: { diagnosis: 'OMI' } } })), 'OK');
  assert.equal(err(() => checkReportSave(U('doctor'), old, { ...base(), status: '確定', verified: true })), 'OK');
  assert.match(err(() => checkReportSave(U('secretary'), null, { ...base(), status: '確定' })), /^403/, '新規で確定');
});

test('確定ロック：確定済みは内容を変更できない（ステータス・照合・登録者・履歴は可）', () => {
  const locked = { ...base(), status: '確定' };
  const doc = U('doctor');
  assert.match(err(() => checkReportSave(doc, locked, { ...locked, cathRecord: { exam: { diagnosis: 'OMI' } } })), /^409 確定済み/);
  assert.equal(err(() => checkReportSave(doc, locked, { ...locked, verified: true, header: { ...locked.header, registrant: '佐藤 健一' } })), 'OK');
  assert.equal(err(() => checkReportSave(doc, locked, { ...locked, version: 9, updatedAt: 'x', history: [...locked.history, { at: 'n', by: 'x', action: '保存' }] })), 'OK');
  assert.equal(err(() => checkReportSave(doc, locked, { ...locked, status: '入力中', cathRecord: { exam: { diagnosis: 'OMI' } } })), 'OK', '確定解除と同時なら可');
});

test('登録履歴：既存の履歴は変更・削除できない', () => {
  const doc = U('doctor');
  assert.match(err(() => checkReportSave(doc, base(), { ...base(), history: [] })), /^409 登録履歴/);
  assert.match(err(() => checkReportSave(doc, base(), { ...base(), history: [{ ...base().history[0], by: '他人' }] })), /^409 登録履歴/);
});

test('stampHistory：追加分の記録者をログイン利用者にする／追加がなければ1件追加', () => {
  const r = { ...base(), history: [...base().history, { at: 't', by: '自己申告', action: '保存（カテ記録）' }] };
  stampHistory(U('doctor'), 1, r);
  assert.deepEqual(r.history.map((h) => h.by), ['山田 太郎', 'doctor名']);
  const r2: Record<string, unknown> = { ...base() };
  stampHistory(U('secretary'), 1, r2, 'NOW');
  assert.deepEqual((r2.history as { by: string; action: string; at: string }[])[1], { at: 'NOW', by: 'secretary名', action: '保存' });
});

test('checkVersion：新規は 0、更新は一致すれば +1、不一致・未指定は 409', () => {
  assert.equal(checkVersion('レポート', null, undefined), 0);
  assert.equal(checkVersion('レポート', { version: 2 }, 2), 3);
  assert.equal(checkVersion('レポート', {}, 0), 1, 'version の無い既存データは 0');
  assert.match(err(() => checkVersion('レポート', { version: 2 }, 1)), /^409 このレポートは他の端末/);
  assert.match(err(() => checkVersion('患者', { version: 2 }, undefined)), /^409 version が必要/);
});
