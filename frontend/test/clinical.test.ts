import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  accAhaSuggest, confirmMismatches, confirmWarnings, durationFromAge, jcsBand, jcsBandFromPct, jctoScore, lesionSuccessSuggest, procedureMinutes,
} from '../src/utils/clinical';
import { createEmptyPatient, createEmptyReport, createPciLesion, normalizeReport } from '../src/model/defaults';
import type { Draft, PciLesion } from '../src/types/model';

const lesion = (f: (l: PciLesion) => void) => {
  const l = createPciLesion();
  f(l);
  return l;
};

test('狭窄度：AHA 分類 → JCS 区分（区間の上限で対応付け）', () => {
  assert.equal(jcsBand('Normal'), '0%');
  assert.equal(jcsBand('Irregular'), '1-24%');
  assert.equal(jcsBand('25'), '1-24%');
  assert.equal(jcsBand('50'), '25-49%');
  assert.equal(jcsBand('75'), '50-69%');
  assert.equal(jcsBand('90'), '70-89%');
  assert.equal(jcsBand('99'), '90-99%');
  assert.equal(jcsBand('100'), '100%');
  assert.equal(jcsBand(''), '');
  // QCA の実測値を優先
  assert.equal(jcsBand('75', '72'), '70-89%');
  assert.equal(jcsBandFromPct('0'), '0%');
  assert.equal(jcsBandFromPct('24.9'), '1-24%');
  assert.equal(jcsBandFromPct('49'), '25-49%');
  assert.equal(jcsBandFromPct('69'), '50-69%');
  assert.equal(jcsBandFromPct('90'), '90-99%');
  assert.equal(jcsBandFromPct('100'), '100%');
  assert.equal(jcsBandFromPct('abc'), '');
  assert.equal(jcsBandFromPct('120'), '');
});

test('手技時間：日付をまたぐ場合を含む', () => {
  assert.equal(procedureMinutes('09:10', '10:25'), 75);
  assert.equal(procedureMinutes('23:30', '00:40'), 70);
  assert.equal(procedureMinutes('9:00', ''), null);
  assert.equal(procedureMinutes('xx', '10:00'), null);
});

test('J-CTO：CTO 以外・未回答は null、5 項目回答で合計', () => {
  assert.equal(jctoScore(createPciLesion()), null);
  const l = lesion((x) => {
    x.morph.cto = 'yes';
    x.cto.jcto = { blunt: 'yes', calc: 'yes', bend: 'no', len20: 'yes', retry: '' };
  });
  assert.equal(jctoScore(l), null);
  l.cto.jcto.retry = 'no';
  assert.equal(jctoScore(l), 3);
  l.cto.jcto = { blunt: 'no', calc: 'no', bend: 'no', len20: 'no', retry: 'no' };
  assert.equal(jctoScore(l), 0);
});

test('閉塞期間：旧 Age of Occlusion から推定', () => {
  assert.equal(durationFromAge('<1ヶ月'), '<3m');
  assert.equal(durationFromAge('1-3ヶ月'), '<3m');
  assert.equal(durationFromAge('>3ヶ月'), '>=3m');
  assert.equal(durationFromAge('不明'), 'unknown');
  assert.equal(durationFromAge(''), '');
});

test('ACC/AHA：特徴から A/B1/B2/C を提案', () => {
  assert.equal(accAhaSuggest(createPciLesion()), null); // 判断材料なし
  assert.equal(accAhaSuggest(lesion((l) => { l.lengthA = '8'; l.morph.eccentricity = 'no'; }))?.type, 'A');
  assert.equal(accAhaSuggest(lesion((l) => { l.lengthA = '15'; }))?.type, 'B1');
  assert.equal(accAhaSuggest(lesion((l) => { l.lengthA = '15'; l.morph.calcification = 'yes'; }))?.type, 'B2');
  assert.equal(accAhaSuggest(lesion((l) => { l.lengthB = '>20mm'; }))?.type, 'C');
  assert.equal(accAhaSuggest(lesion((l) => { l.angulation = '>90°'; }))?.type, 'C');
  assert.equal(accAhaSuggest(lesion((l) => { l.proximalTortuosity = 'Severe'; }))?.type, 'C');
  assert.equal(accAhaSuggest(lesion((l) => { l.morph.cto = 'yes'; l.cto.duration = '<3m'; }))?.type, 'B1');
  assert.equal(accAhaSuggest(lesion((l) => { l.morph.cto = 'yes'; l.cto.duration = '>=3m'; }))?.type, 'C');
  assert.equal(accAhaSuggest(lesion((l) => { l.morph.cto = 'yes'; l.cto.duration = 'unknown'; }))?.type, 'C');
  // 旧項目の Age of Occlusion も使う
  assert.equal(accAhaSuggest(lesion((l) => { l.morph.cto = 'yes'; l.ageOfOcclusion = '>3ヶ月'; }))?.type, 'C');
  const s = accAhaSuggest(lesion((l) => { l.morph.thrombus = 'yes'; l.morph.ostial = 'yes'; l.angulation = '45-90°'; }));
  assert.equal(s?.type, 'B2');
  assert.equal(s?.b.length, 3);
});

test('病変成功：術後 ≤25% かつ TIMI 3', () => {
  assert.equal(lesionSuccessSuggest(createPciLesion()), '');
  assert.equal(lesionSuccessSuggest(lesion((l) => { l.summary.post = '0'; l.summary.timiPost = '3'; })), 'Success');
  assert.equal(lesionSuccessSuggest(lesion((l) => { l.summary.post = '25'; l.summary.timiPost = '3'; })), 'Success');
  assert.equal(lesionSuccessSuggest(lesion((l) => { l.summary.post = '30'; l.summary.timiPost = '3'; })), 'Failure');
  assert.equal(lesionSuccessSuggest(lesion((l) => { l.summary.post = '0'; l.summary.timiPost = '2'; })), 'Failure');
  // QCA（post.pct）を優先
  assert.equal(lesionSuccessSuggest(lesion((l) => { l.summary.post = '0'; l.post.pct = '40'; l.summary.timiPost = '3'; })), 'Failure');
});

test('旧データの移行：J-PCI の既往歴 → カテ記録、Age of Occlusion → 閉塞期間', () => {
  const raw: any = createEmptyReport('pt1');
  raw.pci.jpci.bg = { ...raw.pci.jpci.bg, priorMI: 'yes', pciHx: 'no', renal: '+', copd: '-', pad: 'unknown' };
  delete raw.cathRecord.risk.priorMI;
  delete raw.cathRecord.risk.renal;
  raw.pci.lesions[0].morph.cto = 'yes';
  raw.pci.lesions[0].ageOfOcclusion = '>3ヶ月';
  delete raw.pci.lesions[0].cto.duration;
  const m = normalizeReport(raw);
  assert.equal(m.cathRecord.risk.priorMI, 'yes');
  assert.equal(m.cathRecord.risk.pciHx, 'no');
  assert.equal(m.cathRecord.risk.renal, '+');
  assert.equal(m.cathRecord.risk.copd, '-');
  assert.equal(m.cathRecord.risk.pad, 'unknown');
  assert.equal((m.pci.jpci.bg as any).priorMI, undefined, '移した項目は J-PCI 側から消す');
  assert.equal(m.pci.lesions[0].cto.duration, '>=3m');
  assert.deepEqual(m.cathRecord.complications.items.death, false);
  // カテ記録に値があれば上書きしない
  const raw2: any = createEmptyReport('pt1');
  raw2.cathRecord.risk.priorMI = 'no';
  raw2.pci.jpci.bg.priorMI = 'yes';
  assert.equal(normalizeReport(raw2).cathRecord.risk.priorMI, 'no');
});

test('確定時の警告：空のレポートは主要項目を列挙、入力すると消える', () => {
  const d: Draft = { patient: createEmptyPatient(), report: createEmptyReport('pt1') };
  const w = confirmWarnings(d);
  for (const x of ['性別', '生年月日', '待機／緊急', '術者', '手技の開始・終了時刻', '合併症の有無（カテ記録）']) assert.ok(w.includes(x), x);
  assert.ok(!w.some((x) => x.startsWith('Dominance')), 'CAG をしていなければ CAG の項目は出さない');

  const r = d.report;
  d.patient.sex = 'M';
  d.patient.birthDate = '1950-01-01';
  Object.assign(r.cathRecord.body, { height: '170', weight: '65' });
  Object.assign(r.cathRecord.exam, { urgency: '待機', approach: 'Rt Radial', startTime: '09:00', endTime: '10:00', fluoroTime: '10', totalDose: '500' });
  r.cathRecord.exam.purposes.CAG = true;
  r.cathRecord.exam.contrast.volume = '80';
  r.cathRecord.doctors.operators[0] = '山田 太郎';
  Object.assign(r.cathRecord.risk, { DM: '-', HT: '+', HL: '-', smoking: '-', priorMI: 'no', priorHF: 'no', pciHx: 'no', cabgHx: 'no', renal: '-' });
  r.cathRecord.complications.status = 'no';
  assert.deepEqual(confirmWarnings(d), ['Dominance（CAG）', 'セグメントの狭窄度（CAG）', '病変枝数（CAG）']);
  r.cagLvg.cag.dominance = 'Right';
  r.cagLvg.cag.segments.LAD7.stenosis = '90';
  r.cagLvg.cag.lesions.count = '1';
  assert.deepEqual(confirmWarnings(d), []);

  // PCI の病変
  const l = r.pci.lesions[0];
  l.target = '#7';
  const w2 = confirmWarnings(d);
  assert.ok(w2.some((x) => x.startsWith('PCI 病変 #7')));
  Object.assign(l, { type: 'B1', deNovoMajor: 'de novo', success: 'Failure' });
  Object.assign(l.summary, { pre: '90', post: '0', timiPre: '3', timiPost: '3' });
  r.pci.jpci.info.procComp = 'no';
  assert.deepEqual(confirmWarnings(d), []);
  assert.deepEqual(confirmMismatches(d), ['PCI 病変 #7：成否「Failure」が自動判定「Success」と異なる']);
});
