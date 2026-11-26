import type { ScreenKey } from '../state/screens';

/**
 * 画面間共有項目の「主画面（編集できる画面）」定義。
 * ここに無い項目は、表示している画面で編集可。
 * ここにある項目は owner の画面でのみ編集でき、他の画面では参照表示（編集不可）になる。
 */
export interface Ownership {
  /** ドット区切りパスの前方一致（配列添字は数字のまま） */
  prefix: string;
  owner: ScreenKey[];
  /** 参照画面（ドキュメント・ツールチップ用） */
  refs: string;
}

export const OWNERSHIP: Ownership[] = [
  // 患者属性（ヘッダ）は 患者情報入力・カテ記録 で編集、他画面は参照
  { prefix: 'patient.patientId', owner: ['patient', 'cathRecord'], refs: '全画面ヘッダ' },
  { prefix: 'patient.name', owner: ['patient', 'cathRecord'], refs: '全画面ヘッダ' },
  { prefix: 'patient.kana', owner: ['patient', 'cathRecord'], refs: '全画面ヘッダ' },
  { prefix: 'patient.sex', owner: ['patient', 'cathRecord'], refs: '全画面ヘッダ' },
  { prefix: 'patient.birthDate', owner: ['patient', 'cathRecord'], refs: '全画面ヘッダ' },
  { prefix: 'patient.infection', owner: ['patient'], refs: 'カンファレンス（臨床診断/感染症）' },
  { prefix: 'patient.pastHistory', owner: ['patient'], refs: 'カンファレンス（既往歴/経過）' },
  // レポートヘッダ（施行日・Cine No・PCI No）はカテ記録で編集
  { prefix: 'report.header.studyDate', owner: ['cathRecord', 'patient'], refs: '全画面ヘッダ' },
  { prefix: 'report.header.cineNo', owner: ['cathRecord', 'patient'], refs: '全画面ヘッダ' },
  { prefix: 'report.header.pciNo', owner: ['cathRecord', 'patient', 'pci'], refs: '全画面ヘッダ' },
  // カテ記録が主
  { prefix: 'report.cathRecord.exam.fluoroTime', owner: ['cathRecord'], refs: 'PCI（J-PCI）' },
  { prefix: 'report.cathRecord.exam.contrast', owner: ['cathRecord'], refs: 'PCI（J-PCI）' },
  { prefix: 'report.cathRecord.risk', owner: ['cathRecord'], refs: 'PCI（J-PCI）・カンファレンス' },
  { prefix: 'report.cathRecord.labs.cbc.Hb', owner: ['cathRecord'], refs: 'PCI（J-PCI）' },
  { prefix: 'report.cathRecord.labs.admission.Cr', owner: ['cathRecord'], refs: 'PCI（J-PCI）' },
  { prefix: 'report.cathRecord.labs.hbs', owner: ['cathRecord'], refs: 'カンファレンス（臨床診断/感染症）' },
  { prefix: 'report.cathRecord.labs.hcv', owner: ['cathRecord'], refs: 'カンファレンス（臨床診断/感染症）' },
  { prefix: 'report.cathRecord.body', owner: ['cathRecord'], refs: 'カンファレンス' },
  { prefix: 'report.cathRecord.hemo', owner: ['cathRecord'], refs: 'カンファレンス' },
  { prefix: 'report.cathRecord.prognosis', owner: ['cathRecord'], refs: 'カンファレンス' },
  // CAG/LVG が主
  { prefix: 'report.cagLvg.cag.syntax', owner: ['cagLvg'], refs: 'PCI（基本）' },
  { prefix: 'report.cagLvg.cag.euro', owner: ['cagLvg'], refs: 'PCI（基本）' },
  { prefix: 'report.cagLvg.cag.japan', owner: ['cagLvg'], refs: 'PCI（基本）' },
  { prefix: 'report.cagLvg.lvg.values', owner: ['cagLvg'], refs: 'カンファレンス' },
];

const SCREEN_NAME: Partial<Record<ScreenKey, string>> = {
  patient: '患者情報入力', cathRecord: 'カテ記録', cagLvg: 'CAG/LVG', pci: 'PCI', conference: 'カンファレンス',
};
export const screenName = (k: ScreenKey) => SCREEN_NAME[k] ?? k;

export function ownerOf(path: string): Ownership | null {
  for (const o of OWNERSHIP) if (path === o.prefix || path.startsWith(o.prefix + '.')) return o;
  return null;
}
