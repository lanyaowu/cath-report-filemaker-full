import { test } from 'node:test';
import assert from 'node:assert/strict';
import { bmi, bsa, credoScore, isAbnormal, ivusDerived, judgeHbr, lvgDerived } from '../src/utils/calc';
import { ageAt, diffDays, diffMinutes, fmtMinutes } from '../src/utils/date';

test('BSA（DuBois）・BMI', () => {
  assert.equal(bsa('170', '65'), '1.75'); // 0.007184 × 65^0.425 × 170^0.725
  assert.equal(bmi('170', '65'), '22.5');
  assert.equal(bsa('', '65'), '');
  assert.equal(bmi('170', 'x'), '');
});

test('LVG：SV・EF・各 Index', () => {
  assert.deepEqual(lvgDerived('120', '50', '1.6', '70'), { LVSV: '70', EF: '58.3', CO: '4.9', LVEDVI: '75', LVESVI: '31.3', LVSVI: '43.8', CI: '3.06' });
  assert.deepEqual(lvgDerived('', '50', '1.6', '70'), {});
});

test('J-HBR：主要1つ以上 または 副次2つ以上', () => {
  assert.equal(judgeHbr({ a: false }, { x: false }), '');
  assert.equal(judgeHbr({ a: true }, {}), 'HBR');
  assert.equal(judgeHbr({}, { x: true }), 'non-HBR');
  assert.equal(judgeHbr({}, { x: true, y: true }), 'HBR');
});

test('CREDO-Kyoto：点数とリスク区分', () => {
  const pts = { a: 1, b: 2, c: 2 };
  assert.deepEqual(credoScore({ a: true }, pts), { score: 1, level: '低リスク' });
  assert.deepEqual(credoScore({ a: true, b: true }, pts), { score: 3, level: '中リスク' });
  assert.deepEqual(credoScore({ a: true, b: true, c: true }, pts), { score: 5, level: '高リスク' });
});

test('IVUS 派生値・基準値外', () => {
  assert.deepEqual(ivusDerived('10', '4', '1.0', '0.2'), { plaqueCSA: '6', plaqueBurden: '60', eccentricity: '0.8' });
  assert.equal(isAbnormal('42', 10, 40), true);
  assert.equal(isAbnormal('', 10, 40), false);
  assert.equal(isAbnormal('25', 10, 40), false);
});

test('日付：年齢・日数差・時間差', () => {
  assert.equal(ageAt('1952-04-12', '2026-11-02'), '74');
  assert.equal(ageAt('1952-11-03', '2026-11-02'), '73');
  assert.equal(diffDays('2026-11-01', '2026-11-20'), '19');
  const m = diffMinutes({ date: '2026-11-02', time: '10:00' }, { date: '2026-11-02', time: '11:30' });
  assert.equal(Math.abs(m ?? 0), 90);
  assert.equal(typeof fmtMinutes(90), 'string');
});
