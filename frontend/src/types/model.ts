/**
 * 心カテーテルレポート データモデル
 *
 * 永続化単位（MongoDB コレクション）:
 *   patients     … Patient（患者マスタ）
 *   cath_reports … CathReport（1回のカテ検査＝1ドキュメント。各画面のデータをサブドキュメントとして保持）
 *   masters      … Masters（術者・デバイスマスタ）
 *
 * CathReport.patientRef → Patient.id（N:1）
 * 画面間で共有する項目は同じパスを参照する（例：透視時間はカテ記録と J-PCI で共通）。
 * 入力値は原則 string（空文字=未入力）。数値は表示・計算時に変換する。
 */

export type YN = '' | 'yes' | 'no';
export type PM = '' | '-' | '+' | 'unknown';
export type UMU = '' | 'yes' | 'no' | 'unknown';
export type Timing = '' | 'pre' | 'intra' | 'post';
export type Flags = Record<string, boolean>;
export type YNMap = Record<string, YN>;
export type StrMap = Record<string, string>;

export interface Triple { s: string; d: string; m: string } // 収縮期/拡張期/平均
export interface NameSize { name: string; size: string }
export interface ShapeSize { label: string; shape: string; size: string }
export interface DateTime { date: string; time: string }

// ============ 患者 ============
export interface Admission { admitDate: string; dischargeDate: string; doctor: string; diagnosis: string; summary: string }
export interface Patient {
  id: string;
  patientId: string; // 病院ID
  name: string;
  kana: string;
  sex: '' | 'M' | 'F';
  birthDate: string;
  bloodType: string;
  rh: string;
  zip: string;
  address: string;
  phone: string;
  mobile: string;
  emergency: { name: string; relation: string; phone: string };
  insurance: { type: string; number: string };
  allergy: { contrast: boolean; contrastDetail: string; drug: boolean; drugDetail: string; latex: boolean; iodine: boolean; food: string };
  infection: { hbs: PM; hcv: PM; hiv: PM; syphilis: PM; mrsa: PM };
  primaryDoctor: string;
  ward: string;
  referral: { hospital: string; doctor: string };
  dnar: boolean;
  pastHistory: string;
  familyHistory: string;
  medicationNote: string;
  notes: string;
  admissions: Admission[]; // 病歴総括
  createdAt: string;
  updatedAt: string;
}

// ============ カテ記録 ============
export interface CathRecord {
  exam: {
    urgency: '' | '待機' | '緊急';
    totalCathCount: string;
    purposes: { CAG: boolean; PCI: boolean; SG: boolean; EVT: boolean; followUp: boolean; other1: boolean; other2: boolean };
    followUpReason: string;
    other1Text: string;
    other2Text: string;
    examItems: string;
    disease: string;
    diagnosis: string;
    treatmentPolicy: string;
    flags: Flags; // CCUホットライン, ImpressiveCase, PTCRA, Ach provocation ...
    cancer: boolean;
    cancerName: string;
    aorticDisease: boolean;
    aorticDiseaseType: string;
    approach: string;
    sheath: NameSize;
    contrast: { agent: string; volume: string };
    fluoroTime: string;
    totalDose: string;
    /** 手技の開始・終了時刻（HH:MM）。手技時間は算出（保存しない） */
    startTime: string;
    endTime: string;
  };
  doctors: { attending: string; outpatient: string; operators: string[]; assistants: string[]; referralHospital: string; referralDoctor: string };
  hemo: { pressures: Record<string, Triple>; values: StrMap };
  prognosis: { deathDate: string; confirmDate: string; confirmer: string; comment: string; transferDate: string; maceRelation: string; angioFuExclude: string; angioFuExclude2: string };
  other: { study1: string; study2: string; memo: string };
  body: { height: string; weight: string; bodyTemp: string }; // BSA・BMI は算出値（保存しない）
  labs: {
    admission: StrMap;
    hbs: { date: string; hbsAg: string; hbsAgC: string };
    hcv: { date: string; hcvAb: string; hcvAbC: string };
    cbc: StrMap;
    endocrine: StrMap;
    discharge: StrMap;
    dischargeDate: string;
    bloodGas: StrMap;
    legacy: StrMap;
  };
  risk: {
    DM: PM; DMtreatment: string; HD: PM; CAPD: PM; HT: PM; HL: PM; family: PM;
    smoking: '' | '-' | '+' | 'past' | 'unknown'; smokingPerDay: string; smokingStartAge: string; smokingQuitAge: string;
    eSmoking: '' | '-' | '+' | 'past' | 'unknown'; eSmokingPerDay: string; eSmokingStartAge: string; eSmokingQuitAge: string;
    /** 既往歴（全検査で記録。J-PCI タブはここを参照） */
    priorMI: UMU; priorHF: UMU; pciHx: UMU; cabgHx: UMU;
    /** 併存症（全検査で記録。J-PCI タブはここを参照） */
    renal: PM; copd: PM; pad: PM;
  };
  /** 合併症（PCI の有無にかかわらず全検査で記録） */
  complications: { status: UMU; items: Flags; detail: string };
  pciSummary: string;
  futurePlan: string;
  comment: string;
}

// ============ 病変（Target）を軸にしたデータ連携 ============
/*
 * 病変を表すデータは画面ごとに別の配列にあり、つながり方は次の 4 種類（詳細は docs/ER.md「病変（Target）のデータ連携」）。
 *  [同一] 1 つのデータを複数のタブ・画面に表示する
 *    - Pci.lesions[i]      … PCI の全タブ（基本・病変形態・Device・Bif/CTO・Complication・J-PCI・検索用）で同じ病変 i
 *    - PressureCol[N].lesion … Pressure Wire の病変 N と IVUS の Lesion N の病変名（IvusLesion.site は旧データ用）
 *  [同じ番号] 配列の番号 N が同じ病変を指す
 *    - PressureIvus.pressure[N] ↔ PressureIvus.lesions[N]（数をそろえ、追加・削除も一緒）
 *  [名前の一致] 文字列で探す・候補に出す（キーは持たない）
 *    - PciLesion.target の候補 = CAG セグメント（CAG_SEGMENTS → #1〜#15・HL・#4AV・#4PD）
 *    - PCI「QCA 取得」：PciLesion.target と PressureCol.lesion の一致で列を探し、qca を pre/post へ複写
 *    - ImageItem.lesion の候補 = PciLesion.target
 *  [複写・集計] ボタンや表示時に値を写す・数える（元を直しても写した先は変わらない）
 *    - Restudy.lesions ← 前回 PCI レポートの lesions（targetSub + target、術後 %）
 *    - カンファレンス「当院 PCI 歴」・集計・検査報告書・確定前の確認 … target のある病変だけを対象にする
 */

// ============ CAG / LVG ============
export interface SegmentFinding {
  size: string; calc: boolean; stenosis: string;
  diffuse: boolean; segmental: boolean; undefined: boolean; jeopardy: boolean; graftable: boolean;
}
export interface Collateral { from: string; to: string; grade: string; state: string }
export interface BypassGraft { graft: string; anastomosis: string; patency: string }
export interface CagLvg {
  approach: { artery: string; arterySheath: NameSize; vein: string; veinSheath: NameSize; support: string };
  catheters: Record<string, ShapeSize>;
  cag: {
    dominance: string;
    segments: Record<string, SegmentFinding>;
    collateralsNone: boolean;
    collaterals: Collateral[];
    grafts: BypassGraft[];
    complication: string;
    squeezing: '' | '-' | '+';
    spasm: '' | '-' | '+';
    provocation: string;
    /** 病変枝数と枝（「所見から算出」で segments の有意狭窄から設定） */
    lesions: { count: string; LMT: boolean; LAD: boolean; LCX: boolean; RCA: boolean };
    syntax: string; euro: string; japan: string;
    comment: string;
  };
  lvg: {
    performed: boolean;
    view: string;
    agent: string; volume: string; rate: string;
    values: StrMap; // LVEDV, LVESV, LVEDVI, LVESVI, LVSV, LVSVI, EF, CO, CI, LVEDP, HR
    wallMotion: StrMap; // AHA 1..7
    mr: string;
    thrombus: boolean; aneurysm: boolean; apicalBallooning: boolean; vsr: boolean;
    aog: { performed: boolean; ar: string; findings: string };
    comment: string;
  };
}

// ============ PCI ============
export interface DeviceItem { category: string; name: string; size: string; length: string; pressure: string }
export interface PciLesion {
  /** 対象病変（例 #7）。PCI の全タブで共通の病変キー。候補は CAG セグメント。空の病変は集計・帳票・Restudy の対象外 */
  target: string;
  /** 対象血管（LAD・RCA など） */
  targetSub: string;
  success: string;
  type: string;
  deNovoMajor: string;
  deNovoMinor: string;
  morph: YNMap;
  angulation: string;
  proximalTortuosity: string;
  ageOfOcclusion: string;
  branchProtection: string;
  lengthA: string;
  lengthB: string;
  /** 術前 QCA（Ref・%DS・MLD）。Pressure/IVUS の QCA から「取得」で複写できる */
  pre: { ref: string; pct: string; mld: string };
  /** 術後 QCA。術後 %DS は summary.post より優先して判定・帳票・Restudy に使う */
  post: { ref: string; pct: string; mld: string };
  technique: string;
  bmsReason1: string;
  bmsReason2: string;
  stentingReason: string;
  stentingMethod: string;
  device: {
    morphPost: string;
    items: DeviceItem[];
    reason: string; result: string;
    desHybrid: YN; desBmsHybrid: YN;
    failureReason: string; rotaBurr: string; protection: string;
    final: { balloon: string; stentLen: string; maxPress: string };
    overlap: { connected: string; totalLen: string; count: string };
  };
  bif: { mainSide: string; main: { a: string; b: string }; side: { a: string; b: string }; stent: string; addProcedure: string; fateSB: string; kbt: { mb: string; sb: string; pressure: string } };
  cto: {
    /** 閉塞期間（<3m／>=3m／unknown） */
    duration: string;
    /** J-CTO スコアの 5 項目（yes/no）。スコアは算出 */
    jcto: { blunt: YN; calc: YN; bend: YN; len20: YN; retry: YN };
    access: string; gwMethod: string; parallelWire: YN; retro: { access: string; gc: NameSize; gw: string; vessel: string; channel: string; channelWire: string } };
  comp: YNMap;
  /** 基本タブの病変単位治療。pre・post（%）は QCA の pre.pct・post.pct と別の欄（QCA が空の時の代わりに使う） */
  summary: { treatment: string; tech: Flags; pre: string; post: string; timiPre: string; timiPost: string; rentrop: string; comment: string; restudyHidden: boolean };
  ict: { type: string; agent: string; dose: string; result: string };
}
export interface Pci {
  basic: {
    /** lesionCount：標的病変数（手入力。J-PCI の jpci.bg.lesionCount とは別の欄で、lesions の数とも連動しない） */
    lesionCount: string; support: string; result: string; failureReason: string; complication: string;
    mdct: boolean; ri: boolean; elapsed: string; killip: string;
    startComp: string; acuteComp: string; mace30: string; hospComp: string;
    guiding: NameSize[]; micro: string[]; gw: string[]; patientTreatment: string;
  };
  /** 病変 1〜5（可変。最大 LIST_MAX.lesions）。番号 i は PCI の全タブで同じ病変 */
  lesions: PciLesion[];
  /** 手技全体の CTO スコア（病変ごとの J-CTO の最大値を「反映」で設定） */
  ctoScore: string;
  patientComp: YNMap;
  patientTreat: YNMap;
  specificProcedure: string;
  jpci: {
    bg: {
      arrest24: UMU; shock24: UMU; ahf24: UMU;
      symptom1m: string; admitDx: string; other: string; stentThrombosis: boolean; comorbid: '' | 'no' | 'unknown';
      smoking: '' | '-' | 'past' | 'current'; dialysis: PM;
      /** lesionCount・lmt：J-PCI の標的病変数・左主幹部病変（手入力。PCI 基本の lesionCount・CAG の cag.lesions とは連動しない） */
      lesionCount: string; lmt: '' | 'yes' | 'no'; aortic: boolean; aorticText: string;
    };
    pre: { imaging: '' | 'yes' | 'no'; imagingItems: Flags; ffrCt: string; ffr: boolean; ri: boolean; ffrValue: string; riValue: string; antiplatelet: '' | 'yes' | 'no'; apItems: Flags; anticoag: '' | 'yes' | 'no'; acItems: Flags; legacy: Flags };
    post: { antithrombotic: Flags; antithromboticNone: boolean; lipid: Flags; lipidNone: boolean };
    info: {
      jpciOperator: string; firstOp: string; firstOpNo: string; supervisor: UMU; supervisorName: string; supervisorNo: string;
      status: '' | '待機' | '緊急'; accessSite: string; procComp: UMU; compItems: Flags; nonAccessSite: boolean;
      deathDate: string; deathCause: string; mcs: '' | 'yes' | 'no'; mcsItems: Flags; mcsTiming: Record<string, Timing>;
      imaging: '' | 'yes' | 'no'; imagingItems: Flags;
    };
    discharge: { pciResult: string };
  };
  risk: { staged: boolean; stagedText: string; hbrMajor: Flags; hbrMinor: Flags; credo: Flags; st: Flags; daptMonths: string; memo: string };
  ami: { onset: DateTime; call: DateTime; sceneArr: DateTime; sceneDep: DateTime; hospArr: DateTime; cathLab: DateTime; firstDevice: DateTime };
}

// ============ Pressure / IVUS ============
export interface PressureCol {
  /** 病変名（例 LAD#6）。IVUS の Lesion N（同じ番号）の対象部位としても表示・編集する。PCI の QCA 取得は target とこの値の一致で探す */
  lesion: string;
  phase: string; drug: string; dominancy: string;
  priorMI: string; priorMISite: string; stent: string; stentLesion: string;
  metrics: StrMap; qca: StrMap;
}
export type IvusPos = { lesion: string; proximal: string; distal: string };
export interface IvusLesion {
  /** 旧：部位。病変名は PressureCol[N].lesion に一本化（読込時、Pressure Wire 側が空ならこの値を移す。食い違う時は残すだけ） */
  site: string;
  pre: Record<string, IvusPos>;
  post: Record<string, IvusPos>;
  fibrofatty: boolean; fibrous: boolean; calcification: boolean; calcDegree: string;
  device: string; comment: string;
}
/** pressure[N] と lesions[N] は同じ病変 N（数は同じ。1〜5、追加・削除も一緒） */
export interface PressureIvus { pressure: PressureCol[]; lesions: IvusLesion[] }

// ============ PCPS ============
export interface Pcps {
  arrest: DateTime; call: DateTime; sceneArr: DateTime; sceneDep: DateTime; hospArr: DateTime; cathLab: DateTime; start: DateTime;
  firstEcg: string; operators: string[]; primingOperator: string; rosc: string;
  detail: { inflowSite: string; inflowSize: string; outflowSite: string; outflowSize: string; initialFlow: string; weaningDate: string; outcome: string; comment: string };
}

// ============ カンファレンス ============
export interface MedRow { drug: string; dose: string; usage: string; days: string }
export interface Conference {
  wardDoctor: string; disease: string; nyha: string; ccs: string; onsetCourse: string; comment: string;
  notPerformed: Flags;
  prevPci: { date: string; site: string; device: string; note: string }[];
  scinti: { date: string; type: string; ischemia: string; infarct: string; sss: string; srs: string; sds: string; ef: string; findings: string };
  mdct: { date: string; calciumScore: string; cadRads: string; findings: string };
  ucg: { date: string; LVDd: string; LVDs: string; IVS: string; PW: string; EF: string; LAD: string; EA: string; Ee: string; TRPG: string; valve: string; wallMotion: string };
  treadmill: { date: string; protocol: string; mets: string; maxHr: string; result: string; stChange: string; findings: string; prescriptions: MedRow[] };
  clinical: { diagnoses: string; infectionNote: string };
  history: { past: string; course: string };
  dischargeRx: MedRow[];
}

// ============ MACE ============
export interface MaceEvent { checked: boolean; date: string }
export interface MaceEntry {
  mace: string; pciDate: string; lastVisit: string;
  negative: { checked: boolean; date: string };
  positive: { checked: boolean; lastConfirmDate: string };
  death: MaceEvent & { cause: string; st: YN };
  acs: MaceEvent & { st: YN; content: string; st1st: YN };
  stroke: MaceEvent;
  hf: MaceEvent;
  bleeding: MaceEvent & { site: string };
  revasc: MaceEvent & { site: string };
  other: MaceEvent & { text: string };
}

// ============ 画像 ============
export interface ImageItem {
  /** lesion：対象病変（自由入力。候補は PCI の target。キーではない） */
  id: string; category: string; takenAt: string; view: string; lesion: string;
  title: string; description: string; fileName: string; mimeType: string; dataUrl: string; keyImage: boolean;
}

// ============ Restudy（推測項目） ============
export interface Restudy {
  date: string; interval: string;
  /** 再評価する病変。「前回 PCI 病変を取込」で前回レポートの lesions（restudyHidden 以外）から segment＝targetSub + target、prevPct＝術後 % を複写 */
  lesions: { segment: string; prevPct: string; currPct: string; lateLoss: string; restenosis: YN; tlr: YN; comment: string }[];
  comment: string;
}

// ============ レポート ============
export interface ReportHistory { at: string; by: string; action: string }
export interface CathReport {
  id: string;
  patientRef: string;
  status: '入力中' | '確定';
  verified: boolean; // 照合済
  header: { studyDate: string; cineNo: string; pciNo: string; accessionNo: string; secretaryChecked: boolean; summary: boolean; submitted: boolean; qca: boolean; registrant: string };
  cathRecord: CathRecord;
  cagLvg: CagLvg;
  pci: Pci;
  pressureIvus: PressureIvus;
  pcps: Pcps;
  conference: Conference;
  mace: MaceEntry[];
  images: ImageItem[];
  restudy: Restudy;
  history: ReportHistory[];
  createdAt: string;
  updatedAt: string;
}

export type SectionKey = 'cathRecord' | 'cagLvg' | 'pci' | 'pressureIvus' | 'pcps' | 'conference' | 'mace' | 'images' | 'restudy';

export interface Masters { doctors: string[]; devices: { category: string; name: string }[]; hospitals: string[] }

/** 編集対象（患者＋レポートを1つのフォームとして扱う） */
export interface Draft { patient: Patient; report: CathReport }
