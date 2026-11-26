import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createTranslator, type Dictionary } from '../src/i18n/translator';
import zh from '../src/i18n/zh-CN.json';
import en from '../src/i18n/en.json';
import { resolveOptions, normalizeCategory, validateCategory, optionChanges, summarizeOptionChange, defaultOptionCategories, type OptionCategory } from '../src/model/optionMaster';

const dict = zh as unknown as Dictionary;
const dicts = { en: en as unknown as Dictionary, 'zh-CN': dict };

test('辞書：完全一致とパターン（{} の数が訳と同じ・英語と中国語で同じ見出し）', () => {
  for (const d of Object.values(dicts)) {
    assert.ok(Object.keys(d.exact).length > 1000);
    for (const [ja, z] of d.patterns) assert.equal(ja.split('{}').length, z.split('{}').length, ja);
    for (const [ja, z] of Object.entries(d.exact)) assert.ok(z.trim(), ja);
  }
  assert.deepEqual(Object.keys(dicts.en.exact).sort(), Object.keys(dicts['zh-CN'].exact).sort());
  assert.deepEqual(dicts.en.patterns.map((p) => p[0]).sort(), dicts['zh-CN'].patterns.map((p) => p[0]).sort());
});

test('翻訳：英語（並べた語句の区切りは英語の形に）', () => {
  const tr = createTranslator(dicts);
  tr.select('en');
  assert.equal(tr.t('ログアウト'), 'Log out');
  assert.equal(tr.t('カテ記録'), 'Cath record');
  assert.equal(tr.t('この患者には 3 件のレポートがあるため削除できません'), 'This patient has 3 reports and cannot be deleted');
  assert.equal(tr.t('男性・74歳'), 'Male / 74 y');
  assert.equal(tr.t('HT、喫煙（過去）、家族歴'), 'HT, Smoking (former), Family history');
  assert.equal(tr.t('TIMI'), 'TIMI');
  tr.select('zh-CN');
  assert.equal(tr.t('ログアウト'), '退出登录', '言語を切り替えると別の辞書');
});

test('翻訳：日本語のままなら何もしない・中文で完全一致・前後の空白を残す', () => {
  const tr = createTranslator(dicts);
  assert.equal(tr.t('保存'), '保存');
  // DOM なしで試すため、最小限の document を渡す
  const t2 = createTranslator(dicts);
  const fakeDoc = { documentElement: { lang: '' }, title: '', body: null, defaultView: { confirm: () => true, alert: () => undefined, prompt: () => null } } as unknown as Document;
  t2.start('zh-CN', fakeDoc);
  assert.equal(t2.t('ログアウト'), '退出登录');
  assert.equal(t2.t('  カテ記録 '), '  导管记录 ');
  assert.equal(t2.t('入力中'), '录入中');
  assert.equal(t2.t('TIMI'), 'TIMI', '英語の医学用語は変えない');
  assert.equal(t2.t('伊藤 直樹'), '伊藤 直樹', '辞書に無い人名はそのまま');
});

test('翻訳：パターン（可変部分・可変部分の中の訳・改行ごと）', () => {
  const tr = createTranslator(dicts);
  const fakeDoc = { documentElement: { lang: '' }, title: '', body: null, defaultView: { confirm: () => true, alert: () => undefined, prompt: () => null } } as unknown as Document;
  tr.start('zh-CN', fakeDoc);
  assert.equal(tr.t('この患者には 3 件のレポートがあるため削除できません'), '该患者有 3 份报告，无法删除');
  assert.equal(tr.t('伊藤 直樹 さんでログインしました'), '已以 伊藤 直樹 身份登录');
  assert.equal(tr.t('72歳'), '72岁');
  assert.equal(tr.t('カテ記録歳'), 'カテ記録歳', '短いパターンは数値だけ');
  assert.equal(tr.t('保存\nログアウト'), '保存\n退出登录');
  assert.equal(tr.t('＋ グラフトを追加'), '＋ ' + tr.t('グラフトを追加'), '記号で始まる文言は中身を訳す');
  assert.equal(tr.t('鈴木 一郎 保存（カテ記録）'), '鈴木 一郎 保存（导管记录）');
  assert.equal(tr.t('男性・74歳'), '男・74岁', '「・」「、」で並べた語句は 1 つずつ');
  assert.equal(tr.t('HT、喫煙（過去）、家族歴'), 'HT、吸烟（既往）、家族史');
  assert.equal(fakeDoc.documentElement.lang, 'zh-CN');
});

const cat = (): OptionCategory => ({
  code: 'X', name: 'テスト', screen: 'カテ記録', editable: true, version: 1,
  items: [
    { code: '橈骨動脈', label: '橈骨動脈', sortOrder: 10, active: true, labels: { 'zh-CN': '桡动脉' } },
    { code: '大腿動脈', label: '大腿動脈', sortOrder: 20, active: true },
    { code: '上腕動脈', label: '上腕動脈', sortOrder: 30, active: false, labels: { 'zh-CN': '肱动脉' } },
  ],
});

test('選択値マスタ：言語ごとの表示名（無ければ日本語の表示名。値はコードのまま）', () => {
  const ja = resolveOptions(cat(), [], '上腕動脈');
  assert.deepEqual(ja.map((o) => o.label), ['橈骨動脈', '大腿動脈', '上腕動脈（使用停止）']);
  const z = resolveOptions(cat(), [], '上腕動脈', 'zh-CN');
  assert.deepEqual(z.map((o) => o.label), ['桡动脉', '大腿動脈', '肱动脉（已停用）']);
  assert.deepEqual(z.map((o) => o.value), ['橈骨動脈', '大腿動脈', '上腕動脈']);
});

test('選択値マスタ：中国語の表示名の整形・入力チェック・監査ログ', () => {
  const c = cat();
  c.items[1].labels = { 'zh-CN': '  股动脉 ' };
  c.items[0].labels = { 'zh-CN': '' };
  const n = normalizeCategory(c);
  assert.equal(n.items[0].labels, undefined);
  assert.deepEqual(n.items[1].labels, { 'zh-CN': '股动脉' });
  assert.deepEqual(validateCategory(n), []);
  const bad = cat();
  bad.items[0].labels = { 'zh-CN': 'x'.repeat(201), fr: 'Radiale' };
  const e = validateCategory(bad);
  assert.ok(e.some((m) => m.includes('表示名（zh-CN）は 200 文字以内')));
  assert.ok(e.some((m) => m.includes('対応していない言語です: fr')));
  const ch = optionChanges(cat().items, n.items);
  assert.deepEqual(ch.filter((x) => x.path.includes('zh-CN')), [
    { path: '橈骨動脈.表示名(zh-CN)', before: '桡动脉', after: '' },
    { path: '大腿動脈.表示名(zh-CN)', before: '', after: '股动脉' },
  ]);
  assert.match(summarizeOptionChange(cat().items, n.items), /表示名\(zh-CN\):→股动脉/);
});

test('選択値マスタ：初期値の中国語の表示名は画面の辞書から', () => {
  const all = defaultOptionCategories().flatMap((c) => c.items);
  assert.deepEqual(all.find((i) => i.label === 'イオパミロン370')?.labels, { en: 'Iopamiron 370', 'zh-CN': '碘帕醇 370' });
  assert.equal(all.find((i) => i.label === 'Rt Radial')?.labels, undefined, '英語の表示名には付けない');
  assert.ok(all.filter((i) => i.labels).length > 20);
});
