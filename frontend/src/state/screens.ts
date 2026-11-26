import type { SectionKey } from '../types/model';

export type ScreenKey =
  | 'list' | 'patient' | 'cathRecord' | 'cagLvg' | 'restudy' | 'pci' | 'pressureIvus' | 'images' | 'pcps' | 'conference' | 'mace' | 'stats';

export interface ScreenDef { key: ScreenKey; label: string; section?: SectionKey; needsRecord: boolean }

export const SCREENS: ScreenDef[] = [
  { key: 'list', label: '一覧', needsRecord: false },
  { key: 'patient', label: '患者情報入力', needsRecord: true },
  { key: 'cathRecord', label: 'カテ記録', section: 'cathRecord', needsRecord: true },
  { key: 'cagLvg', label: 'CAG/LVG', section: 'cagLvg', needsRecord: true },
  { key: 'restudy', label: 'Restudy', section: 'restudy', needsRecord: true },
  { key: 'pci', label: 'PCI', section: 'pci', needsRecord: true },
  { key: 'pressureIvus', label: 'Pressure/IVUS', section: 'pressureIvus', needsRecord: true },
  { key: 'images', label: '画像', section: 'images', needsRecord: true },
  { key: 'pcps', label: 'PCPS', section: 'pcps', needsRecord: true },
  { key: 'conference', label: 'カンファレンス', section: 'conference', needsRecord: true },
  { key: 'mace', label: 'MACE', section: 'mace', needsRecord: true },
  { key: 'stats', label: '集計', needsRecord: false },
];

export const screenLabel = (k: ScreenKey) => SCREENS.find((s) => s.key === k)?.label ?? k;
