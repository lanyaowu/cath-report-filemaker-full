import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { checkOptionItems, optionChanges, summarizeOptionChange, type OptionCategory, type OptionItem } from '../src/options.ts';
import { checkVersion, RuleError } from '../src/rules.ts';

const it = (code: string, label = code, active = true, sortOrder = 0): OptionItem => ({ code, label, active, sortOrder });
const cat = (items: OptionItem[], editable = true): OptionCategory => ({ code: 'APPROACH', name: 'アプローチ部位', screen: 'カテ記録', editable, items, version: 2 });
const err = (fn: () => void) => {
  try { fn(); } catch (e) { if (e instanceof RuleError) return `${e.status} ${e.message}`; throw e; }
  return 'OK';
};

test('選択値マスタ：追加・表示名の変更・使用停止・並べ替えができ、並び順を振り直す', () => {
  const old = cat([it('Rt Radial', 'Rt Radial', true, 10), it('Lt Radial', 'Lt Radial', true, 20)]);
  const items = checkOptionItems(old, { items: [it(' Lt Radial ', '左橈骨'), it('Rt Radial', 'Rt Radial', false), it('Distal', '遠位橈骨')] });
  assert.deepEqual(items, [
    { code: 'Lt Radial', label: '左橈骨', active: true, sortOrder: 10 },
    { code: 'Rt Radial', label: 'Rt Radial', active: false, sortOrder: 20 },
    { code: 'Distal', label: '遠位橈骨', active: true, sortOrder: 30 },
  ]);
  assert.equal(summarizeOptionChange(old.items, items), '表示名:Lt Radial→左橈骨 使用停止:Rt Radial 追加:Distal 並べ替え');
});

test('選択値マスタ：保存済みのコードは削除できない・重複・必須・標準の分類は 400', () => {
  const old = cat([it('A'), it('B')]);
  assert.match(err(() => checkOptionItems(old, { items: [it('A')] })), /^400 .*削除できません.*B/);
  assert.match(err(() => checkOptionItems(old, { items: [it('A'), it('B'), it('A')] })), /^400 .*重複/);
  assert.match(err(() => checkOptionItems(old, { items: [it('A'), it('B', '')] })), /^400 .*表示名を入力/);
  assert.match(err(() => checkOptionItems(old, { items: [it('A'), it('B'), it('')] })), /^400 .*コードを入力/);
  assert.match(err(() => checkOptionItems(old, { items: [it('A', 'A', false), it('B', 'B', false)] })), /^400 .*1 つもありません/);
  assert.match(err(() => checkOptionItems(cat([it('3')], false), { items: [it('3')] })), /^400 .*標準の分類/);
  assert.match(err(() => checkOptionItems(old, {})), /^400 .*items/);
});

test('選択値マスタ：version が違えば 409（同時更新）', () => {
  assert.equal(checkVersion('選択値マスタ', { version: 2 }, 2), 3);
  assert.match(err(() => checkVersion('選択値マスタ', { version: 3 }, 2)), /^409 .*選択値マスタ/);
});

test('選択値マスタ：初期データは 40 カテゴリ・コードの重複なし', () => {
  const data = JSON.parse(readFileSync(new URL('../../sample-data/option-masters.json', import.meta.url), 'utf-8')) as OptionCategory[];
  assert.equal(data.length, 40);
  assert.equal(new Set(data.map((c) => c.code)).size, 40);
  for (const c of data) assert.equal(new Set(c.items.map((i) => i.code)).size, c.items.length, c.code);
});

test('選択値マスタ：監査ログの項目ごとの変更（表示名・使用・並び順。コードの「.」は「．」）', () => {
  const before = [it('JL3.5', 'JL3.5', true, 10), it('JR4', 'JR4', true, 20)];
  const after = [it('JR4', 'JR4', false, 10), it('JL3.5', 'JL 3.5', true, 20), it('AL1', 'AL1', true, 30)];
  assert.deepEqual(optionChanges(before, after), [
    { path: 'JR4.使用', before: '使用', after: '使用停止' },
    { path: 'JR4.並び順', before: '2', after: '1' },
    { path: 'JL3．5.表示名', before: 'JL3.5', after: 'JL 3.5' },
    { path: 'JL3．5.並び順', before: '1', after: '2' },
    { path: 'AL1.表示名', before: '', after: 'AL1' },
    { path: 'AL1.使用', before: '', after: '使用' },
  ]);
  assert.deepEqual(optionChanges(before, before), []);
});

test('選択値マスタ：言語ごとの表示名（en・zh-CN。空は持たない・他の言語は不可・監査ログに残す）', () => {
  const old = cat([{ ...it('頓用', '頓用', true, 10), labels: { 'zh-CN': '必要时' } }, it('就寝前', '就寝前', true, 20)]);
  const out = checkOptionItems(old, { items: [{ code: '頓用', label: '頓用', labels: { 'zh-CN': ' 按需 ' } }, { code: '就寝前', label: '就寝前', labels: { 'zh-CN': '' } }] });
  assert.deepEqual(out[0].labels, { 'zh-CN': '按需' });
  assert.equal(out[1].labels, undefined);
  assert.equal(summarizeOptionChange(old.items, out), '表示名(zh-CN):必要时→按需');
  assert.deepEqual(optionChanges(old.items, out), [{ path: '頓用.表示名(zh-CN)', before: '必要时', after: '按需' }]);
  assert.throws(() => checkOptionItems(old, { items: [{ code: '頓用', label: '頓用', labels: { fr: 'PRN' } }, { code: '就寝前', label: '就寝前' }] }), /対応していない言語です: fr/);
  assert.throws(() => checkOptionItems(old, { items: [{ code: '頓用', label: '頓用', labels: 'x' }, { code: '就寝前', label: '就寝前' }] }), /labels の形式が不正です/);
  assert.throws(() => checkOptionItems(old, { items: [{ code: '頓用', label: '頓用', labels: { 'zh-CN': 'x'.repeat(201) } }, { code: '就寝前', label: '就寝前' }] }), /200 文字以内/);
});

test('選択値マスタ：英語の表示名も持てる', () => {
  const old = cat([it('頓用', '頓用', true, 10), it('就寝前', '就寝前', true, 20)]);
  const out = checkOptionItems(old, { items: [{ code: '頓用', label: '頓用', labels: { en: 'As needed', 'zh-CN': '必要时' } }, { code: '就寝前', label: '就寝前' }] });
  assert.deepEqual(out[0].labels, { en: 'As needed', 'zh-CN': '必要时' });
  assert.equal(summarizeOptionChange(old.items, out), '表示名(en):→As needed 表示名(zh-CN):→必要时');
});
