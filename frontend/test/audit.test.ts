import { test } from 'node:test';
import assert from 'node:assert/strict';
import { auditDiff } from '../src/audit/diff';
import { auditCsv, markHistory, type AuditEntry } from '../src/audit/model';
import { pathLabel } from '../src/audit/labels';
import { createEmptyReport, normalizeReport } from '../src/model/defaults';

test('監査ログ：変わった項目だけを取り出す（配列は番号、変更前・変更後つき）', () => {
  const a = createEmptyReport('pt-1');
  const b = normalizeReport(JSON.parse(JSON.stringify(a)));
  b.pci.lesions[0].target = '#7';
  b.header.cineNo = 'C-1';
  const ch = auditDiff(a, b);
  assert.deepEqual(ch.map((c) => c.path).sort(), ['header.cineNo', 'pci.lesions.0.target']);
  assert.deepEqual(ch.find((c) => c.path === 'pci.lesions.0.target'), { path: 'pci.lesions.0.target', before: '', after: '#7' });
});

test('監査ログ：version・更新日時・登録履歴・画像本体は記録しない。false と空は同じ', () => {
  const ch = auditDiff(
    { version: 1, updatedAt: 'x', history: [{ a: 1 }], images: [{ fileName: 'a.png', dataUrl: 'data:1' }], flag: false, n: null },
    { version: 2, updatedAt: 'y', history: [{ a: 1 }, { a: 2 }], images: [{ fileName: 'b.png', dataUrl: 'data:2' }], flag: undefined, n: '' },
  );
  assert.deepEqual(ch, [{ path: 'images.0.fileName', before: 'a.png', after: 'b.png' }]);
  assert.deepEqual(auditDiff({ x: true }, { x: false }), [{ path: 'x', before: 'true', after: '' }]);
});

test('監査ログ：新規は空でない項目、削除された配列の要素も記録。長い値は 200 文字で切る', () => {
  assert.deepEqual(auditDiff(null, { a: '1', b: '', c: { d: '2' } }).map((c) => c.path), ['a', 'c.d']);
  assert.deepEqual(auditDiff({ l: ['x', 'y'] }, { l: ['x'] }), [{ path: 'l.1', before: 'y', after: '' }]);
  const long = 'あ'.repeat(300);
  assert.equal(auditDiff({ a: '' }, { a: long })[0].after.length, 201);
});

test('監査ログ：項目名の表示', () => {
  assert.equal(pathLabel('pci.lesions.0.target', 'report'), 'PCI › 病変1 › Target');
  assert.equal(pathLabel('pressureIvus.pressure.4.lesion', 'report'), 'Pressure/IVUS › Pressure Wire 病変5 › 病変名');
  assert.equal(pathLabel('name', 'patient'), '氏名');
  assert.equal(pathLabel('pci.basic.gw.2.name', 'report'), 'PCI › 基本 › GW 3 本目 › 名称');
  assert.equal(pathLabel('mace.0.death.checked', 'report'), 'MACE 1 回目 › 死亡 › 確認');
  assert.equal(pathLabel('unknownKey.x', 'report'), 'unknownKey › x');
});

const E = (id: string, changes: AuditEntry['changes']): AuditEntry => ({
  id, at: id, username: 'u', displayName: 'U', action: 'UPDATE_REPORT', targetType: 'report', targetId: 'rp', detail: '', ip: '', changeCount: changes?.length ?? 0, changes,
});

test('監査ログ：確定解除と、次の確定までの変更に印を付ける', () => {
  const newest = [
    E('5', [{ path: 'header.cineNo', before: 'A', after: 'B' }]),
    E('4', [{ path: 'status', before: '入力中', after: '確定' }]),
    E('3', [{ path: 'pci.lesions.0.target', before: '#6', after: '#7' }]),
    E('2', [{ path: 'status', before: '確定', after: '入力中' }]),
    E('1', [{ path: 'status', before: '入力中', after: '確定' }]),
  ];
  const m = markHistory(newest);
  assert.deepEqual(['1', '2', '3', '4', '5'].map((k) => m.get(k)), ['confirm', 'unlock', 'afterUnlock', 'confirm', '']);
});

test('監査ログ：CSV は BOM 付き、変更は 1 項目 1 行', () => {
  const csv = auditCsv([E('1', [{ path: 'a', before: 'x"y', after: '' }, { path: 'b', before: '', after: '1' }]), E('2', [])], (p) => p);
  assert.ok(csv.startsWith('﻿"日時"'));
  assert.equal(csv.trim().split('\r\n').length, 4);
  assert.ok(csv.includes('"x""y"'));
});
