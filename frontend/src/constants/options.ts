/**
 * 画面項目の定義（キー・表示ラベル・選択肢）。
 * 既定値生成（model/defaults.ts）と画面描画の両方がこの定義を参照するため、
 * 項目を追加する場合はここに1行足すだけで、データモデルと画面に反映される。
 * 参考: 日本循環器学会 心臓カテーテル検査報告書項目 / J-PCI レジストリ項目定義
 */

export type KL = readonly (readonly [string, string])[]; // [key, label]
export type Opt = { value: string; label: string };
export const opts = (...xs: (string | [string, string])[]): Opt[] =>
  xs.map((x) => (Array.isArray(x) ? { value: x[0], label: x[1] } : { value: x, label: x }));

// ---- 選択値マスタ（DB で管理する選択肢） ----
/**
 * cat(...) で定義した選択肢は「選択値マスタ」に登録され、画面ではマスタ（DB / Local Storage）の内容で表示する。
 * ここに書いた値はマスタの初期値（初回投入・サーバーにマスタが無い時の既定）として使う。
 * editable: false は標準の分類や自動判定・レジストリで値を使うもの（管理画面で編集不可）。
 * 保存されるのはコード（= ここに書いた値）なので、既存のレポートはそのまま表示できる。
 */
export interface OptionCategoryDef {
  code: string;
  name: string;
  screen: string;
  editable: boolean;
  items: Opt[];
}
export const OPTION_CATEGORY_DEFS: OptionCategoryDef[] = [];
const CATEGORY_OF = new WeakMap<object, string>();
/** 選択肢の配列が対応する選択値マスタのカテゴリコード（マスタ管理外なら undefined） */
export const categoryOf = (list: readonly unknown[] | undefined): string | undefined => (list ? CATEGORY_OF.get(list) : undefined);
function cat<T extends string | Opt>(code: string, name: string, screen: string, values: T[], o: { editable?: boolean } = {}): T[] {
  OPTION_CATEGORY_DEFS.push({
    code, name, screen, editable: o.editable ?? true,
    items: values.map((v): Opt => (typeof v === 'string' ? { value: v, label: v } : (v as Opt))),
  });
  CATEGORY_OF.set(values, code);
  return values;
}

// ---- 汎用選択肢 ----
export const PM_OPTS = opts(['-', '−'], ['+', '+'], ['unknown', '不明']);
export const PM2_OPTS = opts(['-', '−'], ['+', '+']);
export const YN_OPTS = opts(['yes', 'Yes'], ['no', 'No']);
export const UMU_OPTS = opts(['yes', '有'], ['no', '無'], ['unknown', '不明']);
export const UM_OPTS = opts(['yes', '有'], ['no', '無']);
export const URGENCY_OPTS = opts('待機', '緊急');
export const SMOKING_OPTS = opts(['-', '−'], ['+', '+'], ['past', '過去'], ['unknown', '不明']);
export const JPCI_SMOKING_OPTS = opts(['-', '−'], ['past', '過去'], ['current', '現在']);
export const TIMING_OPTS = opts(['pre', '術前'], ['intra', '術中'], ['post', '術後']);
export const SEX_OPTS = opts(['M', 'M'], ['F', 'F']);

// ---- カテ記録 ----
export const PURPOSES: KL = [
  ['CAG', 'CAG'],
  ['PCI', 'PCI'],
  ['SG', 'S-G'],
  ['EVT', 'EVT'],
];
export const EXAM_FLAGS_LEFT: KL = [
  ['ptcra', 'PTCRA'],
  ['pwIfr', 'Pressurewire(iFR)'],
  ['pwRfr', 'Pressurewire(RFR)'],
];
export const EXAM_FLAGS_RIGHT: KL = [
  ['achProvocation', 'Ach provocation'],
  ['cfrImr', 'CFR IMR'],
  ['ppg', 'PPG'],
];
export const EXAM_ITEMS = cat('EXAM_ITEM', '検査項目', 'カテ記録', ['CAG', 'LVG', 'AOG', 'RHC', 'PCI', 'EVT', 'IVUS', 'OCT/OFDI', 'Pressure study', 'FFR', 'iFR', 'RFR', 'Ach負荷', 'Biopsy', 'temporary PM', 'PCPS', 'IABP', 'Impella']);
export const DISEASES = cat('DISEASE', '疾患名', 'カテ記録', ['AP', 'u-AP', 'SAP', 'AMI', 'OMI', 'SMI', 'VSA', 'CSA', 'HF', 'DCM', 'HCM', 'HOCM', 'VT', 'SSS', 'AVB', 'AS', 'MR', 'LEAD', 'AAA', '虚血性心疾患疑い']);
export const APPROACHES = cat('APPROACH', 'アプローチ部位', 'カテ記録・CAG', ['Rt Radial', 'Lt Radial', 'Rt Femoral', 'Lt Femoral', 'Rt Brachial', 'Lt Brachial', 'Distal Radial(Rt)', 'Distal Radial(Lt)']);
export const SHEATH_SIZES = cat('SHEATH_SIZE', 'シース・カテーテル径（Fr）', 'カテ記録・CAG・PCI', ['4', '5', '6', '7', '8']);
export const CONTRAST_AGENTS = cat('CONTRAST_AGENT', '造影剤', 'カテ記録・CAG', ['イオパミロン370', 'オムニパーク350', 'オプチレイ350', 'ビジパーク320', 'イオメロン350']);

export const HEMO_TRIPLES: KL = [
  ['RA', 'RA'],
  ['RV', 'RV'],
  ['PA', 'PA'],
  ['PCW', 'PCW'],
  ['LV', 'LV'],
  ['LVpost', 'LVpost'],
  ['Ao', 'Ao'],
  ['AoPre', 'Ao pre'],
];
export const HEMO_VALUES_RIGHT: KL = [
  ['HR', 'HR'],
  ['CO', 'CO'],
  ['CI', 'CI'],
  ['SV', 'SV'],
  ['SI', 'SI'],
  ['dpdt', 'dp/dt'],
];
export const HEMO_VALVE: KL = [
  ['MVG', 'MVG'],
  ['MVA', 'MVA'],
  ['AVG', 'AVG'],
  ['AVA', 'AVA'],
];
export const HEMO_SHUNT: KL = [
  ['LtoR', 'L→R'],
  ['RtoL', 'R→L'],
  ['QpQs', 'Qp/Qs'],
  ['RpRs', 'Rp/Rs'],
];

/** 検査値（キー, ラベル, 単位, 下限, 上限）。範囲外はピンク表示 */
export type LabDef = readonly [string, string, string, number?, number?];
export const LAB_CHEM_1: LabDef[] = [
  ['AST', 'AST', 'U/L', 13, 30],
  ['ALT', 'ALT', 'U/L', 7, 30],
  ['LDH', 'LDH', 'U/L', 124, 222],
  ['ALP', 'ALP', 'U/L', 38, 113],
  ['GGT', 'γ-GTP', 'U/L', 9, 64],
  ['TB', 'T-B', 'mg/dL', 0.4, 1.5],
  ['DB', 'D-B', 'mg/dL', 0, 0.4],
  ['Alb', 'Alb', 'g/dL', 4.1, 5.1],
  ['Cr', 'Cr', 'mg/dL', 0.46, 1.07],
  ['GFR', 'GFR', 'mL/min', 60],
  ['UA', 'UA', 'mg/dL', 2.6, 7.0],
  ['Na', 'Na', 'mEq/L', 138, 145],
  ['K', 'K', 'mEq/L', 3.6, 4.8],
  ['Cl', 'Cl', 'mEq/L', 101, 108],
  ['Ca', 'Ca', 'mg/dL', 8.8, 10.1],
  ['CRP', 'CRP', 'mg/dL', 0, 0.14],
];
export const LAB_CHEM_2: LabDef[] = [
  ['TnI', 'トロポニンI', 'ng/mL', 0, 0.026],
  ['TnT', 'トロポニンT', 'ng/mL', 0, 0.014],
  ['FBS', 'FBS', 'mg/dL', 73, 109],
  ['HbA1c', 'HbA1c(NGSP)', '%', 4.9, 6.0],
  ['Insulin', 'Insulin', 'μU/mL', 1.7, 10.4],
  ['BNP', 'BNP', 'pg/mL', 0, 18.4],
  ['HANP', 'HANP', 'pg/mL', 0, 43],
  ['TG', 'TG', 'mg/dL', 40, 149],
  ['HDL', 'HDL', 'mg/dL', 40],
  ['LDL', 'LDL', 'mg/dL', 0, 119],
];
export const LAB_CHEM_3: LabDef[] = [
  ['MDALDL', 'MDA-LDL', 'U/L'],
  ['NEFA', 'NEFA', 'mEq/L'],
  ['DHLA', 'ジホモ-G', 'μg/mL'],
  ['AA', 'アラキドン', 'μg/mL'],
  ['EPA', 'エイコサペ', 'μg/mL'],
  ['DHA', 'ドコサヘキ', 'μg/mL'],
  ['EPAAA', 'EPA/AA', ''],
  ['AcAc', 'アセト酢', 'μmol/L'],
  ['BOHB', '3-ヒドロ', 'μmol/L'],
  ['TKetone', '総ケトン', 'μmol/L'],
];
export const LAB_CBC: LabDef[] = [
  ['WBC', 'WBC', '/μL', 3300, 8600],
  ['RBC', 'RBC', '万/μL', 386, 492],
  ['Hb', 'Hb', 'g/dL', 11.6, 16.8],
  ['Ht', 'Ht', '%', 35.1, 48.6],
  ['Plt', 'Plt', '万/μL', 15.8, 34.8],
  ['MCV', 'MCV', 'fL', 83.6, 98.2],
  ['Neut', 'Neut', '%'],
  ['Lymph', 'Lymph', '%'],
  ['PTINR', 'PT-INR', '', 0.85, 1.15],
  ['APTT', 'APTT', '秒', 24, 34],
  ['Fib', 'Fib', 'mg/dL', 200, 400],
  ['DD', 'D-dimer', 'μg/mL', 0, 1.0],
];
export const LAB_ENDO: LabDef[] = [
  ['TSH', 'TSH', 'μIU/mL', 0.5, 5.0],
  ['FT3', 'FT3', 'pg/mL', 2.3, 4.0],
  ['FT4', 'FT4', 'ng/dL', 0.9, 1.7],
  ['Cortisol', 'コルチゾール', 'μg/dL'],
  ['ACTH', 'ACTH', 'pg/mL'],
  ['Aldo', 'アルドステロン', 'pg/mL'],
  ['PRA', 'レニン活性', 'ng/mL/h'],
  ['UProt', '尿蛋白', ''],
  ['UGlu', '尿糖', ''],
  ['UOB', '尿潜血', ''],
  ['UACR', '尿Alb/Cr', 'mg/gCr', 0, 30],
];
export const LAB_DISCHARGE: LabDef[] = [
  ['AST', 'AST', 'U/L', 13, 30],
  ['ALT', 'ALT', 'U/L', 7, 30],
  ['LDH', 'LDH', 'U/L', 124, 222],
  ['CK', 'CK', 'U/L', 59, 248],
  ['Cr', 'Cr', 'mg/dL', 0.46, 1.07],
  ['GFR', 'GFR', 'mL/min', 60],
  ['Hb', 'Hb', 'g/dL', 11.6, 16.8],
  ['BNP', 'BNP', 'pg/mL', 0, 18.4],
  ['LDL', 'LDL', 'mg/dL', 0, 119],
  ['HDL', 'HDL', 'mg/dL', 40],
  ['TG', 'TG', 'mg/dL', 40, 149],
  ['HbA1c', 'HbA1c', '%', 4.9, 6.0],
  ['CRP', 'CRP', 'mg/dL', 0, 0.14],
];
export const LAB_GAS: LabDef[] = [
  ['pH', 'pH', '', 7.35, 7.45],
  ['pCO2', 'pCO2', 'mmHg', 35, 45],
  ['pO2', 'pO2', 'mmHg', 80, 100],
  ['HCO3', 'HCO3', 'mEq/L', 22, 26],
  ['BE', 'BE', 'mEq/L', -2, 2],
  ['SaO2', 'SaO2', '%', 95],
  ['SvO2', 'SvO2', '%', 60, 80],
  ['Lac', 'Lactate', 'mmol/L', 0, 2],
  ['ACT', 'ACT', '秒'],
  ['AQT_TnT', 'AQT TnT', 'ng/mL', 0, 0.014],
  ['AQT_CKMB', 'AQT CK-MB', 'ng/mL'],
];
export const LAB_LEGACY: LabDef[] = [
  ['TC', 'T-Cho', 'mg/dL', 142, 248],
  ['ApoA1', 'ApoA1', 'mg/dL'],
  ['ApoB', 'ApoB', 'mg/dL'],
  ['Lpa', 'Lp(a)', 'mg/dL', 0, 30],
  ['RLP', 'RLP-C', 'mg/dL'],
  ['hsCRP', 'hs-CRP', 'mg/dL'],
  ['CK', 'CK', 'U/L', 59, 248],
  ['CKMB', 'CK-MB', 'U/L', 0, 12],
];

// ---- CAG ----
export type SegDef = { key: string; label: string; groupStart?: boolean };
export const CAG_SEGMENTS: SegDef[] = [
  { key: 'RCA1', label: 'RCA1', groupStart: true },
  { key: 'RCA2', label: '2' },
  { key: 'RCA3', label: '3' },
  { key: 'RCA4AV', label: '4AV' },
  { key: 'RCA4PD', label: '4PD' },
  { key: 'LMT5', label: 'LMT5', groupStart: true },
  { key: 'LAD6', label: 'LAD6', groupStart: true },
  { key: 'LAD7', label: '7' },
  { key: 'LAD8', label: '8' },
  { key: 'LAD9', label: '9' },
  { key: 'LAD10', label: '10' },
  { key: 'LCX11', label: 'LCX11', groupStart: true },
  { key: 'HL', label: 'HL' },
  { key: 'LCX12', label: '12' },
  { key: 'LCX13', label: '13' },
  { key: 'LCX14', label: '14' },
  { key: 'LCX15', label: '15' },
];
export const SEG_SIZES = ['Large', 'Small', 'Absent'];
export const STENOSIS = ['Normal', 'Irregular', '25', '50', '75', '90', '99', '100'];
export const STENOSIS_SIGNIFICANT = new Set(['75', '90', '99', '100']);
export const SEG_FLAGS: KL = [
  ['diffuse', 'Diffuse'],
  ['segmental', 'Segmental'],
  ['undefined', 'Undefined'],
  ['jeopardy', 'Jeopardy'],
  ['graftable', 'Graftable'],
];
export const RENTROP = cat('RENTROP', 'Rentrop 分類', 'CAG・PCI', ['0', '1', '2', '3'], { editable: false });
export const COLLATERAL_STATE = cat('COLLATERAL_STATE', '側副血行の状態', 'CAG', ['Good', 'Poor', 'Well-developed', 'Faint']);
export const GRAFT_NAMES = cat('GRAFT_NAME', 'バイパスグラフト', 'CAG', ['LITA', 'RITA', 'RA', 'GEA', 'SVG']);
export const GRAFT_PATENCY = cat('GRAFT_PATENCY', 'グラフトの開存', 'CAG', ['Patent', 'Stenosis', 'Occluded', 'String sign']);

export const CATHETER_SLOTS: KL = [
  ['LCA', 'LCA'],
  ['RCA', 'RCA'],
  ['LV', 'LV'],
  ['LIMA', 'LIMA'],
  ['RIMA', 'RIMA'],
  ['GEA', 'GEA'],
  ['RadialA', 'Radial.A'],
  ['SVG', 'SVG'],
  ['custom1', '任意1'],
  ['custom2', '任意2'],
];
export const CATHETER_SHAPES = cat('CATHETER_SHAPE', 'カテーテル形状', 'CAG', ['JL3.5', 'JL4', 'JL5', 'JR4', 'JR5', 'AL1', 'AL2', 'AR1', 'IM', 'Tiger II', 'Ikari L', 'Pigtail', 'Multipurpose', 'BLK']);
export const SHEATH_NAMES = cat('SHEATH_NAME', 'シース（製品）', 'カテ記録・CAG', ['Glidesheath Slender', 'Radifocus', 'Super Sheath', 'Parent Plus', 'Prelude']);

// ---- LVG（推測項目：AHA 7分画） ----
export const LV_SEGMENTS: KL = [
  ['1', '1 Anterobasal'],
  ['2', '2 Anterolateral'],
  ['3', '3 Apical'],
  ['4', '4 Diaphragmatic'],
  ['5', '5 Posterobasal'],
  ['6', '6 Septal'],
  ['7', '7 Posterolateral'],
];
export const WALL_MOTION = opts(
  ['N', 'Normal'],
  ['Hypo', 'Hypokinesis'],
  ['SevHypo', 'Severe hypo'],
  ['A', 'Akinesis'],
  ['D', 'Dyskinesis'],
  ['An', 'Aneurysm'],
);
export const SELLERS = cat('SELLERS', 'Sellers 分類', 'LVG', ['0', 'I', 'II', 'III', 'IV'], { editable: false });

// ---- PCI ----
export const PCI_TECH: KL = [
  ['LMT', 'LMT'],
  ['POBA', 'POBA'],
  ['STENT', 'STENT'],
  ['Cutting', 'Cutting'],
  ['Rota', 'Rota'],
  ['DCA', 'DCA'],
  ['ICT', 'ICT'],
  ['ASP', 'ASP'],
  ['DCB', 'DCB'],
  ['OAS', 'OAS'],
  ['IVL', 'IVL'],
  ['Bioadaptor', 'Bioadaptor'],
];
export const MORPH_YN: KL = [
  ['eccentricity', 'Eccentricity'],
  ['calcification', 'Calcification'],
  ['bifurcation', 'Bifurcation'],
  ['irregular', 'Irregular'],
  ['thrombus', 'Thrombus'],
];
export const MORPH_YN2: KL = [
  ['cto', 'CTO'],
  ['dissection', 'Dissection'],
  ['haziness', 'Haziness'],
  ['ostial', 'Ostial'],
];
export const LESION_TYPES = cat('LESION_TYPE', 'ACC/AHA 病変 Type', 'PCI', ['A', 'B1', 'B2', 'C'], { editable: false });
export const DENOVO_MAJOR = cat('DENOVO_MAJOR', '病変区分（de novo／再狭窄）', 'PCI', ['de novo', 'restenosis', 'ISR', 'graft']);
export const DENOVO_MINOR = cat('DENOVO_MINOR', '病変区分（詳細）', 'PCI', ['focal', 'diffuse', 'proliferative', 'occlusive', 'edge']);
export const ANGULATION = cat('ANGULATION', '屈曲（Angulation）', 'PCI', ['<45°', '45-90°', '>90°'], { editable: false });
export const TORTUOSITY = cat('TORTUOSITY', '近位部の蛇行', 'PCI', ['None', 'Moderate', 'Severe'], { editable: false });
export const TIMI = cat('TIMI', 'TIMI 分類', 'PCI', ['0', '1', '2', '3'], { editable: false });
export const PCI_RESULTS = cat('PCI_RESULT', 'PCI 結果', 'PCI', ['Success', 'Partial success', 'Failure'], { editable: false });
export const DEVICE_CATEGORIES = cat('DEVICE_CATEGORY', 'デバイス種別', 'PCI・マスタ', ['Balloon', 'NC Balloon', 'Scoring', 'Cutting', 'DES', 'BMS', 'DCB', 'Rota burr', 'OAS', 'IVL', 'DCA', 'Aspiration', 'Filter']);
export const BIF_STENTS = cat('BIF_STENT', '分岐部ステント手技', 'PCI', ['Provisional', 'T-stent', 'TAP', 'Culotte', 'Crush', 'DK-crush', 'V-stent', 'SKS']);
export const CTO_ACCESS = cat('CTO_ACCESS', 'CTO アクセス', 'PCI', ['Antegrade', 'Retrograde', 'Both']);
export const GW_METHOD = cat('GW_METHOD', 'CTO ガイドワイヤー通過法', 'PCI', ['Single wire', 'Parallel wire', 'IVUS guided', 'ADR', 'Reverse CART', 'CART']);
export const SUPPORTS = cat('SUPPORT', '補助循環・サポート', 'CAG・PCI', ['IABP', 'PCPS', 'Impella', 'Temporary PM', 'なし']);

export const COMP_LESION: { title: string; items: KL }[] = [
  {
    title: '<Complication due to procedure>',
    items: [
      ['residualDissectGW', 'Residual dissect due to GW'],
      ['residualDissectGC', 'Residual dissect due to GC'],
      ['residualDissectDevice', 'Residual dissect due to device'],
      ['residualPlaqueThrombus', 'Residual plaque thrombus'],
      ['perforation', 'Perforation'],
      ['stentDislodge', 'Stent dislodge'],
      ['lossSideBranch', 'Loss of major side branch'],
    ],
  },
  {
    title: '<Treatment to lesion>',
    items: [
      ['additionalStenting', 'Additional stenting'],
      ['longInflation', 'Long inflation'],
      ['joStent', 'Jo stent'],
      ['veinCoveredStent', 'Vein covered stent'],
    ],
  },
  {
    title: '<Final angiographic result>',
    items: [
      ['slowNoFlow', 'Slow No flow'],
      ['distalEmbolism', 'Distal occlusion due to embolism'],
      ['abruptLabo', 'Abrupt closure in labo'],
      ['worsening', 'Worsening than pre PCI'],
      ['abruptHosp', 'Abrupt closure in hosp'],
      ['stentThrombosis', 'Stent thrombosis'],
    ],
  },
];
export const COMP_PATIENT: KL = [
  ['deathProcedure', 'Death due to procedure'],
  ['cardiacDeath', 'Cardiac death'],
  ['QMI', 'QMI'],
  ['NQMI', 'NQMI'],
  ['nonCardiacDeath', 'Non cardiac death'],
  ['sequela', 'Sequela of other organ'],
  ['pericardialHematoma', 'Pericardial hematoma'],
  ['vascular', 'Vascular complication'],
  ['shockArrest', 'Shock Arrest VT vf'],
  ['CHF', 'CHF'],
  ['foreignBody', '異物遺残'],
  ['unsuccessOther', 'Unsuccess of the other lesion'],
];
export const TREAT_PATIENT: KL = [
  ['IABP', 'IABP'],
  ['PCPS', 'PCPS'],
  ['CABG', 'CABG'],
  ['rePCI', 're PCI'],
  ['pericardiocentesis', 'Pericardiocentesis'],
  ['transfusion', 'Blood transfusion'],
  ['otherOperation', 'Other operation'],
];

// J-PCI
export const JPCI_BG_UMU_LEFT: KL = [
  ['pciHx', 'PCI歴'],
  ['cabgHx', 'CABG歴'],
  ['priorMI', '心筋梗塞の既往'],
  ['priorHF', '心不全の既往'],
];
export const JPCI_BG_24H: KL = [
  ['arrest24', '心肺停止'],
  ['shock24', '心原性ショック'],
  ['ahf24', '急性心不全'],
];
export const SYMPTOMS_1M = cat('JPCI_SYMPTOM_1M', '1か月以内の症状（J-PCI）', 'PCI（J-PCI）', ['無症状', '安定狭心症', '不安定狭心症', 'NSTEMI', 'STEMI', '心不全', 'その他'], { editable: false });
export const JPCI_DX = cat('JPCI_DX', '入院時診断（J-PCI）', 'PCI（J-PCI）', ['安定冠動脈疾患', '不安定狭心症', 'NSTEMI', 'STEMI', '無症候性心筋虚血', 'その他'], { editable: false });
export const PREOP_IMAGING: KL = [
  ['ct', '冠動脈CT'],
  ['stressEcho', '負荷エコー'],
  ['other', 'その他'],
  ['stressEcg', '負荷心電図'],
  ['stressMri', '負荷MRI'],
  ['stressScinti', '負荷シンチ'],
  ['ffrRi', 'FFR/Resting index'],
];
export const ANTIPLATELET: KL = [
  ['aspirin', 'アスピリン'],
  ['prasugrel', 'プラスグレル'],
  ['otherAp', 'その他の抗血小板薬'],
  ['clopidogrel', 'クロピドグレル'],
  ['ticagrelor', 'チカグレロル'],
];
export const ANTICOAG: KL = [
  ['warfarin', 'ワーファリン'],
  ['doac', 'DOAC'],
  ['otherAc', 'その他の抗凝固薬'],
];
export const ANTICOAG_LEGACY: KL = [
  ['dabigatran', 'ダビガトラン'],
  ['apixaban', 'アピキサバン'],
  ['rivaroxaban', 'リバロキサバン'],
  ['edoxaban', 'エドキサバン'],
];
export const POST_ANTITHROMBOTIC: KL = [
  ['aspirin', 'アスピリン'],
  ['prasugrel', 'プラスグレル'],
  ['otherAp', 'その他の抗血小板薬'],
  ['doac', 'DOAC'],
  ['clopidogrel', 'クロピドグレル'],
  ['ticagrelor', 'チカグレロル'],
  ['warfarin', 'ワーファリン'],
  ['otherAc', 'その他の抗凝固薬'],
];
export const POST_LIPID: KL = [
  ['statinHigh', 'スタチン(高強度)'],
  ['ezetimibe', 'エゼチミブ'],
  ['evolocumab', 'エボロクマブ'],
  ['otherLipid', 'その他の抗脂質薬'],
  ['statinLow', 'スタチン(非高強度)'],
  ['bempedoic', 'ベンペド酸'],
  ['inclisiran', 'インクリシラン'],
];
export const JPCI_COMP: KL = [
  ['death', '院内死亡'],
  ['qmi', 'Q波梗塞'],
  ['nqmi', '非Q波梗塞'],
  ['tamponade', '心タンポナーデ'],
  ['hfShock', '補助循環や強心薬を必要とする心不全・ショック'],
  ['stentThrombosis', 'ステント血栓症(院内発症)'],
  ['bleeding', '輸血を必要とする出血性合併症'],
  ['emergencySurgery', '緊急手術'],
];
export const MCS_ITEMS: KL = [
  ['IABP', 'IABP'],
  ['PCPS', 'PCPS'],
  ['Impella', 'Impella'],
  ['LVAD', 'LVAD'],
  ['other', 'その他'],
];
export const IMAGING_ITEMS: KL = [
  ['IVUS', 'IVUS'],
  ['OCT', 'OCT'],
  ['OFDI', 'OFDI'],
  ['angioscopy', '血管内視鏡'],
  ['other', 'その他'],
];

// 出血・血栓リスク
export const HBR_MAJOR: KL = [
  ['otherMajor', '（その他・主要項目）'],
  ['lowWeight', '低体重・フレイル（男性<55kg 女性<50kg）'],
  ['ckdSevere', 'CKD(重度腎機能低下) eGFR<30mL/min/1.73m²'],
  ['anemia', '貧血 Hb<11g/dL(男女共)'],
  ['hf', '心不全'],
  ['oac', '抗凝固薬の長期服用'],
  ['pvd', 'PVD'],
  ['priorBleeding', '非外傷性出血の既往'],
  ['cvd', '脳血管障害(1年以内の外傷性脳出血も含む)'],
  ['thrombocytopenia', '血小板減少症 血小板<100×10⁹/L'],
  ['malignancy', '活動性悪性腫瘍（1年以内に診断かつ/または現在治療を要する）'],
  ['cirrhosis', '門脈圧亢進症を伴う肝硬変'],
  ['bleedingDiathesis', '慢性の出血性素因'],
  ['surgeryDapt', 'DAPT期間中の延期不可能な大手術'],
  ['recentSurgery', 'PCI施行前30日以内の大きな手術または大きな外傷'],
];
export const HBR_MINOR: KL = [
  ['age75', '年齢(≧75歳)'],
  ['ckdModerate', 'CKD(中程度腎機能低下) eGFR 30〜59'],
  ['mildAnemia', '軽度貧血 Hb 11.0〜12.9g/dL(男女共)'],
  ['nsaids', 'NSAIDs ステロイド服用'],
  ['ischemicStroke', '主要項目に該当しない虚血性脳卒中の既往'],
];
export const CREDO_ITEMS: (readonly [string, string, number])[] = [
  ['ckd', 'CKD(透析またはeGFR<30mL/min/1.73m²)', 2],
  ['af', '心房細動', 2],
  ['pvd', 'PVD', 2],
  ['anemia', '貧血(Hb値<11g/dL)', 2],
  ['age75', '年齢(≧75歳)', 1],
  ['hf', '心不全', 1],
  ['dm', '糖尿病', 1],
  ['cto', '慢性完全閉塞(CTO)', 1],
];
export const CREDO_POINTS: Record<string, number> = Object.fromEntries(CREDO_ITEMS.map(([k, , p]) => [k, p]));
export const ST_RISK: KL = [
  ['firstGenDes', '第1世代DES'],
  ['svgStent', 'SVGに対するステント'],
  ['stents3', '3本以上のステント留置'],
  ['priorSt', 'DAPT治療下におけるステント血栓症の既往'],
  ['lesions3', '3病変以上の治療'],
  ['smallVessel', '小血管ステント'],
  ['bif2', '分岐部2ステント'],
  ['acs', 'ACS'],
  ['longStent', '総ステント長>60mm'],
  ['dmCkdCto', 'DM(CKD/CTO)'],
];

// ---- Pressure / IVUS ----
export const PRESSURE_METRICS: KL = [
  ['baselinePdPa', 'Baseline Pd/Pa'],
  ['FFR', 'FFR'],
  ['iFR', 'iFR'],
  ['hiFR', 'Hyperemic iFR'],
  ['RFR', 'RFR'],
  ['hRFR', 'Hyperemic RFR'],
  ['DFR', 'DFR'],
  ['hDFR', 'Hyperemic DFR'],
  ['dPR', 'dPR'],
  ['hdPR', 'Hyperemic dPR'],
  ['ffrAngio', 'FFR angio'],
  ['cfrThermo', 'CFR-thermo'],
  ['IMR', 'IMR'],
  ['tmnRest', 'Tmn-rest'],
  ['tmnHyper', 'Tmn-hyperemia'],
  ['PPG', 'PPG'],
];
export const QCA_METRICS: KL = [
  ['pctDS', '%Diameter Stenosis'],
  ['lesionLength', 'Lesion Length'],
  ['refDiameter', 'Reference Diameter'],
  ['mld', 'Minimum Lesion Diameter'],
  ['plaqueVolume', 'Plaque Volume'],
];
export const PRESSURE_PHASE = cat('PRESSURE_PHASE', 'Pressure 測定時期', 'Pressure/IVUS', ['診断のみ', 'pre PCI', 'post PCI']);
export const HYPEREMIC_DRUGS = cat('HYPEREMIC_DRUG', '最大充血薬', 'Pressure/IVUS', ['ATP', 'パパベリン', 'ニコランジル', 'アデノシン']);
export const DOMINANCY = cat('DOMINANCE', '優位性（Dominance）', 'CAG・Pressure/IVUS', ['Right', 'Left', 'Balanced'], { editable: false });
export const IVUS_METRICS: KL = [
  ['minLD', '最小内腔径'],
  ['maxLD', '最大内腔径'],
  ['lumenCSA', '内腔CSA'],
  ['vesselCSA', '血管CSA'],
  ['plaqueCSA', 'プラークCSA'],
  ['maxPT', '最大プラーク厚さ'],
  ['minPT', '最小プラーク厚さ'],
  ['plaqueBurden', 'プラーク面積率'],
  ['eccentricity', '偏心率'],
];
export const IVUS_POS: KL = [
  ['lesion', '病変部位'],
  ['proximal', 'Proximal'],
  ['distal', 'Distal'],
];

// ---- PCPS ----
export const FIRST_ECG = cat('FIRST_ECG', '初回心電図', 'PCPS', ['VF', 'pulseless VT', 'PEA', 'Asystole', 'Sinus', 'その他']);

// ---- MACE ----
export const MACE_LEVEL = cat('MACE_LEVEL', 'MACE レベル', 'MACE', ['0', '1', '2', '3'], { editable: false });

// ---- 画像 ----
export const IMAGE_CATEGORIES = cat('IMAGE_CATEGORY', '画像の種別', '画像', ['Cine', 'ECG', 'X-P', 'IVUS', 'OCT', 'UCG', 'CT', 'Scinti', 'Other']);
export const IMAGE_VIEWS = cat('IMAGE_VIEW', '撮影方向', '画像', ['RAO30', 'LAO45', 'RAO30/CAU25', 'RAO30/CRA30', 'LAO45/CRA25', 'LAO45/CAU30', 'AP/CRA30', 'Spider', 'Lateral', 'PA', 'AP']);

// ---- カンファレンス ----
export const NYHA = cat('NYHA', 'NYHA 分類', 'カンファレンス', ['I', 'II', 'III', 'IV'], { editable: false });
export const CCS = cat('CCS', 'CCS 分類', 'カンファレンス', ['I', 'II', 'III', 'IV'], { editable: false });
export const CONF_TABS: KL = [
  ['basic', '基本・血行動態・危険因子'],
  ['prevPci', 'Previous PCI'],
  ['scinti', 'Scintigram'],
  ['mdct', 'MDCT'],
  ['ucg', 'UCG'],
  ['treadmill', 'Treadmill/処方'],
  ['clinical', '臨床診断/感染症'],
  ['history', '既往歴/経過'],
  ['dischargeRx', '退院時処方'],
];
export const SCINTI_TYPES = cat('SCINTI_TYPE', 'シンチグラム種別', 'カンファレンス', ['Tl負荷', 'Tc負荷', 'BMIPP', 'MIBG', 'PYP']);
export const CAD_RADS = cat('CAD_RADS', 'CAD-RADS', 'カンファレンス', ['0', '1', '2', '3', '4A', '4B', '5', 'N'], { editable: false });
export const TREADMILL_PROTOCOLS = cat('TREADMILL_PROTOCOL', 'トレッドミル プロトコル', 'カンファレンス', ['Bruce', 'Modified Bruce', 'Naughton']);
export const TREADMILL_RESULTS = cat('TREADMILL_RESULT', 'トレッドミル 判定', 'カンファレンス', ['陰性', '陽性', '判定不能']);
export const DRUG_USAGE = cat('DRUG_USAGE', '用法', 'カンファレンス', ['1日1回朝食後', '1日2回朝夕食後', '1日3回毎食後', '就寝前', '頓用']);

/** 合併症（全検査共通・カテ記録）。JCS 標準の合併症区分に、診断カテで起こりうるものを加えた */
export const CATH_COMP: KL = [
  ['death', '死亡'],
  ['mi', '心筋梗塞'],
  ['stroke', '脳卒中'],
  ['arrhythmia', '重症不整脈（VT/VF・高度房室ブロック）'],
  ['tamponade', '心タンポナーデ'],
  ['shock', '心原性ショック'],
  ['vascular', 'アクセス部位の合併症（血腫・仮性動脈瘤など）'],
  ['bleeding', '輸血を要する出血'],
  ['contrastReaction', '造影剤アレルギー反応'],
  ['cin', '造影剤腎症'],
  ['emergencySurgery', '緊急手術'],
  ['other', 'その他'],
];
