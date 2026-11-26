import { test } from 'node:test';
import assert from 'node:assert/strict';
import { LIST_MAX, createEmptyReport, createPciLesion, fitList, normalizeReport } from '../src/model/defaults';

test('繰り返し項目：新規レポートは各 1 件から始まる', () => {
  const r = createEmptyReport('pt-1');
  assert.equal(r.cagLvg.cag.collaterals.length, 1);
  assert.equal(r.cagLvg.cag.grafts.length, 1);
  assert.equal(r.pci.basic.guiding.length, 1);
  assert.equal(r.pci.basic.micro.length, 1);
  assert.equal(r.pci.basic.gw.length, 1);
  assert.equal(r.pci.lesions.length, 1);
  assert.equal(r.pressureIvus.pressure.length, 1);
});

test('繰り返し項目：最大数', () => {
  assert.deepEqual({ ...LIST_MAX }, { collaterals: 5, grafts: 4, guiding: 5, micro: 4, gw: 5, lesions: 5, pressure: 5 });
});

test('fitList：末尾の空は除き、途中の空は残す（最低 1 件）', () => {
  const mk = () => ({ a: '', b: '' });
  assert.deepEqual(fitList([{ a: 'x' }, { a: '' }, { b: 'y' }, {}, { a: '' }], mk), [{ a: 'x', b: '' }, { a: '', b: '' }, { a: '', b: 'y' }]);
  assert.deepEqual(fitList([], mk), [{ a: '', b: '' }]);
  assert.deepEqual(fitList(undefined, mk), [{ a: '', b: '' }]);
  assert.deepEqual(fitList(['', '', ''], () => ''), ['']);
});

test('fitList：最大数を超えた入力済みの旧データは消さない', () => {
  const gw = ['A', 'B', 'C', 'D', 'E', 'F', '', '', '', ''];
  assert.deepEqual(fitList(gw, () => ''), ['A', 'B', 'C', 'D', 'E', 'F']);
});

test('normalizeReport：旧形式（固定数の配列）を可変長に整え、各要素を既定値で補う', () => {
  const base = createEmptyReport('pt-1') as any;
  const old = JSON.parse(JSON.stringify(base));
  old.cagLvg.cag.collaterals = [{ from: 'LAD', to: 'RCA4PD', grade: '2', state: '' }, ...Array(4).fill({ from: '', to: '', grade: '', state: '' })];
  old.pci.basic.gw = ['Sion blue', 'Gaia Next 1', ...Array(8).fill('')];
  old.pci.lesions = [{ target: '#7' }, { target: '' }, { target: '#2' }, createPciLesion(), createPciLesion()];
  old.pressureIvus.pressure = [{ lesion: 'LAD6' }, { lesion: '' }, { lesion: '' }];
  const r = normalizeReport(old);
  assert.equal(r.cagLvg.cag.collaterals.length, 1);
  assert.deepEqual(r.pci.basic.gw, ['Sion blue', 'Gaia Next 1']);
  assert.equal(r.pci.lesions.length, 3);
  assert.equal(r.pci.lesions[1].target, '');
  assert.equal(r.pci.lesions[2].target, '#2');
  // 要素が部分的でも全項目を持つ
  assert.equal(typeof r.pci.lesions[2].cto.jcto.blunt, 'string');
  assert.equal(r.pci.lesions[2].device.items.length, 10);
  assert.equal(r.pressureIvus.pressure.length, 1);
  assert.equal(r.pressureIvus.pressure[0].metrics.FFR, '');
});

test('Pressure Wire と IVUS Lesion：数をそろえ、病変名は Pressure Wire 側に一本化', () => {
  const base = createEmptyReport('pt-1') as any;
  // IVUS だけの旧データ（Lesion 1〜4 固定、Pressure Wire 3 列は空）
  const a = JSON.parse(JSON.stringify(base));
  a.pressureIvus.pressure = [{ lesion: '' }, { lesion: '' }, { lesion: '' }];
  a.pressureIvus.lesions = [{ site: 'LAD#7', comment: 'x' }, {}, {}, {}];
  let r = normalizeReport(a);
  assert.equal(r.pressureIvus.pressure.length, 1);
  assert.equal(r.pressureIvus.lesions.length, 1);
  assert.equal(r.pressureIvus.pressure[0].lesion, 'LAD#7');
  // Pressure Wire 2 列・IVUS は 3 番目だけ
  const b = JSON.parse(JSON.stringify(base));
  b.pressureIvus.pressure = [{ lesion: 'LCX#13' }, { lesion: 'LAD#6' }, { lesion: '' }];
  b.pressureIvus.lesions = [{ site: '' }, { site: 'LAD#7' }, { site: 'RCA#2', comment: 'y' }, {}];
  r = normalizeReport(b);
  assert.equal(r.pressureIvus.pressure.length, 3);
  assert.equal(r.pressureIvus.lesions.length, 3);
  assert.equal(r.pressureIvus.pressure[1].lesion, 'LAD#6'); // 食い違いは Pressure Wire を優先
  assert.equal(r.pressureIvus.lesions[1].site, 'LAD#7'); // IVUS 側の値は残す
  assert.equal(r.pressureIvus.pressure[2].lesion, 'RCA#2'); // Pressure Wire が空なら IVUS の部位を移す
  assert.equal(typeof r.pressureIvus.pressure[2].metrics.FFR, 'string');
});
