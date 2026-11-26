import { test } from 'node:test';
import assert from 'node:assert/strict';
import { deepEqual, getAt, hasAnyValue, mergeDefaults, setAt } from '../src/utils/path';
import { createEmptyReport, normalizeReport, SECTION_FACTORIES } from '../src/model/defaults';
import { ownerOf } from '../src/model/ownership';
import { hasPermission, type AuthUser } from '../src/auth/permissions';

test('パス操作：getAt・setAt はイミュータブル', () => {
  const a = { x: { y: [1, { z: 'a' }] } };
  const b = setAt(a, 'x.y.1.z', 'b');
  assert.equal(getAt(b, 'x.y.1.z'), 'b');
  assert.equal(getAt(a, 'x.y.1.z'), 'a', '元のオブジェクトは変わらない');
  assert.equal(b.x.y[0], a.x.y[0]);
  assert.equal(getAt(a, 'x.nope.z'), undefined);
});

test('mergeDefaults：欠けた項目を既定値で補い、既存の値と未知の項目は残す', () => {
  const m = mergeDefaults({ a: '', b: { c: false, d: '' }, list: [{ v: '' }, { v: '' }] }, { a: '1', b: { c: true }, extra: 9, list: [{ v: 'x' }] });
  assert.deepEqual(m, { a: '1', b: { c: true, d: '' }, extra: 9, list: [{ v: 'x' }, { v: '' }] });
});

test('normalizeReport：旧データ（項目不足）を補完し、version などサーバーの項目は残す', () => {
  const r = normalizeReport({ id: 'rp-1', patientRef: 'pt-1', header: { studyDate: '2026-11-02' }, version: 3 } as never);
  const empty = createEmptyReport('pt-1');
  assert.equal(r.header.studyDate, '2026-11-02');
  assert.deepEqual(Object.keys(r.cathRecord).sort(), Object.keys(empty.cathRecord).sort());
  assert.equal((r as unknown as { version: number }).version, 3);
});

test('画面クリア：各セクションの既定値は空', () => {
  for (const [k, f] of Object.entries(SECTION_FACTORIES)) assert.equal(hasAnyValue(f()), false, k);
});

test('deepEqual（変更の検出）', () => {
  const r = createEmptyReport('pt-1');
  assert.equal(deepEqual(r, JSON.parse(JSON.stringify(r))), true);
  assert.equal(deepEqual(r, setAt(r, 'cathRecord.exam.diagnosis', 'AP')), false);
});

test('主画面：危険因子はカテ記録が主', () => {
  assert.ok(ownerOf('report.cathRecord.risk.DM'));
  assert.equal(ownerOf('report.header.cineNoXX'), null);
});

test('権限表（サーバーと同じ）', () => {
  const u = (r: AuthUser['roles'][number]): AuthUser => ({ username: r, displayName: r, roles: [r] });
  assert.equal(hasPermission(u('viewer'), 'edit'), false);
  assert.equal(hasPermission(u('secretary'), 'edit'), true);
  assert.equal(hasPermission(u('secretary'), 'confirm'), false);
  assert.equal(hasPermission(u('doctor'), 'verify'), true);
  assert.equal(hasPermission(u('doctor'), 'seed'), false);
  assert.equal(hasPermission(null, 'read'), false);
});
