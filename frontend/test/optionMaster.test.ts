import { test } from 'node:test';
import assert from 'node:assert/strict';
import { APPROACHES, categoryOf, OPTION_CATEGORY_DEFS, PM_OPTS, TIMI } from '../src/constants/options';
import {
  defaultOptionCategories,
  INACTIVE_SUFFIX,
  mergeWithDefaults,
  normalizeCategory,
  optionChanges,
  summarizeOptionChange,
  resolveOptions,
  validateCategory,
  type OptionCategory,
} from '../src/model/optionMaster';
import optionSeed from '../src/data/option-masters.json';

const byCode = (list: OptionCategory[], code: string) => list.find((c) => c.code === code)!;

test('選択値マスタ：40 カテゴリ（編集可 26・標準の分類 14）、コードの重複なし', () => {
  assert.equal(OPTION_CATEGORY_DEFS.length, 40);
  assert.equal(OPTION_CATEGORY_DEFS.filter((d) => d.editable).length, 26);
  assert.equal(new Set(OPTION_CATEGORY_DEFS.map((d) => d.code)).size, 40);
  for (const d of OPTION_CATEGORY_DEFS) assert.equal(new Set(d.items.map((i) => i.value)).size, d.items.length, d.code);
});

test('選択値マスタ：配列からカテゴリを引ける（マスタ管理外は undefined）', () => {
  assert.equal(categoryOf(APPROACHES), 'APPROACH');
  assert.equal(categoryOf(TIMI), 'TIMI');
  assert.equal(categoryOf(PM_OPTS), undefined);
  assert.equal(categoryOf(['Rt Radial']), undefined);
});

test('選択値マスタ：初期値は現在の値をそのままコードにする（既存レポートの移行が不要）', () => {
  const c = byCode(defaultOptionCategories(), 'APPROACH');
  assert.deepEqual(c.items.map((i) => i.code), APPROACHES);
  assert.deepEqual(c.items.map((i) => i.label), APPROACHES);
  assert.ok(c.items.every((i) => i.active));
  assert.equal(c.version, 0);
});

test('選択値マスタ：初期データ（sample-data/option-masters.json）がプログラムの定義と一致する', () => {
  assert.deepEqual(optionSeed, defaultOptionCategories().map(({ version: _v, ...c }) => c));
});

test('resolveOptions：使用停止は候補から外し、並び順に従う', () => {
  const c = byCode(defaultOptionCategories(), 'APPROACH');
  c.items[0].active = false; // Rt Radial
  c.items[1].sortOrder = 1; // Lt Radial を先頭へ
  const o = resolveOptions(c, APPROACHES);
  assert.equal(o[0].value, 'Lt Radial');
  assert.ok(!o.some((x) => x.value === 'Rt Radial'));
});

test('resolveOptions：保存済みの値は使用停止・マスタに無くても表示する', () => {
  const c = byCode(defaultOptionCategories(), 'APPROACH');
  c.items[0].active = false;
  const o = resolveOptions(c, APPROACHES, 'Rt Radial');
  assert.deepEqual(o[o.length - 1], { value: 'Rt Radial', label: `Rt Radial${INACTIVE_SUFFIX}` });
  const o2 = resolveOptions(c, APPROACHES, '旧データの値');
  assert.deepEqual(o2[o2.length - 1], { value: '旧データの値', label: '旧データの値' });
  // 空の値は足さない
  assert.equal(resolveOptions(c, APPROACHES, '').length, APPROACHES.length - 1);
});

test('resolveOptions：表示名を変えてもコード（保存される値）は変わらない', () => {
  const c = byCode(defaultOptionCategories(), 'CONTRAST_AGENT');
  c.items[0].label = 'イオパミロン370（100mL）';
  const o = resolveOptions(c, []);
  assert.deepEqual(o[0], { value: 'イオパミロン370', label: 'イオパミロン370（100mL）' });
});

test('resolveOptions：マスタが無ければプログラムの定義のまま', () => {
  assert.deepEqual(resolveOptions(undefined, ['a', 'b'], 'x'), [
    { value: 'a', label: 'a' },
    { value: 'b', label: 'b' },
  ]);
});

test('mergeWithDefaults：保存済みを使い、新しいカテゴリは初期値、標準の分類は常にプログラムの定義', () => {
  const saved: OptionCategory[] = [
    { ...byCode(defaultOptionCategories(), 'APPROACH'), version: 3, items: [{ code: 'X', label: 'X', sortOrder: 10, active: true }] },
    { ...byCode(defaultOptionCategories(), 'TIMI'), version: 2, items: [{ code: '9', label: '9', sortOrder: 10, active: true }] },
    { code: 'OBSOLETE', name: '廃止', screen: '-', editable: true, version: 1, items: [] },
  ];
  const m = mergeWithDefaults(saved);
  assert.equal(m.length, 40);
  assert.deepEqual(byCode(m, 'APPROACH').items.map((i) => i.code), ['X']);
  assert.equal(byCode(m, 'APPROACH').version, 3);
  assert.deepEqual(byCode(m, 'TIMI').items.map((i) => i.code), TIMI);
  assert.equal(byCode(m, 'TIMI').version, 2);
  assert.equal(byCode(m, 'CONTRAST_AGENT').version, 0);
  assert.ok(!m.some((c) => c.code === 'OBSOLETE'));
  assert.equal(mergeWithDefaults(null).length, 40);
});

test('validateCategory：コード・表示名の必須、重複、標準の分類、使用中 0 件', () => {
  const c = byCode(defaultOptionCategories(), 'APPROACH');
  assert.deepEqual(validateCategory(c), []);
  const bad = { ...c, items: [...c.items, { code: 'Rt Radial', label: '', sortOrder: 999, active: true }, { code: ' ', label: 'x', sortOrder: 1000, active: true }] };
  const e = validateCategory(bad);
  assert.ok(e.some((m) => m.includes('重複')));
  assert.ok(e.some((m) => m.includes('表示名を入力')));
  assert.ok(e.some((m) => m.includes('コードを入力')));
  assert.ok(validateCategory(byCode(defaultOptionCategories(), 'TIMI')).some((m) => m.includes('編集できません')));
  assert.ok(validateCategory({ ...c, items: c.items.map((i) => ({ ...i, active: false })) }).some((m) => m.includes('1 つもありません')));
});

test('normalizeCategory：空白を除き、並び順を振り直す', () => {
  const c = byCode(defaultOptionCategories(), 'APPROACH');
  const n = normalizeCategory({ ...c, items: [{ code: ' A ', label: ' あ ', sortOrder: 99, active: true }, { code: 'B', label: 'い', sortOrder: 1, active: false }] });
  assert.deepEqual(n.items, [
    { code: 'A', label: 'あ', active: true, sortOrder: 10 },
    { code: 'B', label: 'い', active: false, sortOrder: 20 },
  ]);
});

test('監査ログ用：変更の要約と項目ごとの変更（サーバーと同じ形）', () => {
  const it = (code: string, label: string, active: boolean, sortOrder: number) => ({ code, label, active, sortOrder });
  const before = [it('IABP', 'IABP', true, 10), it('PCPS', 'PCPS', true, 20)];
  const after = [it('PCPS', 'PCPS', true, 10), it('IABP', 'IABP', false, 20), it('ECMO', 'ECMO', true, 30)];
  assert.equal(summarizeOptionChange(before, after), '使用停止:IABP 追加:ECMO 並べ替え');
  assert.deepEqual(optionChanges(before, after).map((c) => c.path), ['PCPS.並び順', 'IABP.使用', 'IABP.並び順', 'ECMO.表示名', 'ECMO.使用']);
});
