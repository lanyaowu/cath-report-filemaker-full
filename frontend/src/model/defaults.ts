import * as O from '../constants/options';
import type {
  BypassGraft, CagLvg, CathRecord, CathReport, Collateral, Conference, DateTime, DeviceItem, ImageItem, IvusLesion, MaceEntry, Masters, Patient,
  NameSize, Pci, PciLesion, Pcps, PressureCol, PressureIvus, Restudy, SectionKey, SegmentFinding, Triple,
} from '../types/model';
import { hasAnyValue, mergeDefaults } from '../utils/path';
import { newId } from '../utils/id';
import { nowIso, today } from '../utils/date';
import { durationFromAge } from '../utils/clinical';

const str = (keys: O.KL | readonly (readonly [string, ...unknown[]])[]) => Object.fromEntries(keys.map((k) => [k[0], ''])) as Record<string, any>;
const bool = (keys: O.KL | readonly (readonly [string, ...unknown[]])[]) => Object.fromEntries(keys.map((k) => [k[0], false])) as Record<string, boolean>;
const times = <T>(n: number, f: (i: number) => T) => Array.from({ length: n }, (_, i) => f(i));
const triple = (): Triple => ({ s: '', d: '', m: '' });
const dt = (): DateTime => ({ date: '', time: '' });

export function createEmptyPatient(): Patient {
  const t = nowIso();
  return {
    id: newId('pt'), patientId: '', name: '', kana: '', sex: '', birthDate: '', bloodType: '', rh: '',
    zip: '', address: '', phone: '', mobile: '',
    emergency: { name: '', relation: '', phone: '' },
    insurance: { type: '', number: '' },
    allergy: { contrast: false, contrastDetail: '', drug: false, drugDetail: '', latex: false, iodine: false, food: '' },
    infection: { hbs: '', hcv: '', hiv: '', syphilis: '', mrsa: '' },
    primaryDoctor: '', ward: '', referral: { hospital: '', doctor: '' }, dnar: false,
    pastHistory: '', familyHistory: '', medicationNote: '', notes: '', admissions: [], createdAt: t, updatedAt: t,
  };
}

export function createCathRecord(): CathRecord {
  return {
    exam: {
      urgency: '', totalCathCount: '',
      purposes: { CAG: false, PCI: false, SG: false, EVT: false, followUp: false, other1: false, other2: false },
      followUpReason: '', other1Text: '', other2Text: '', examItems: '', disease: '', diagnosis: '', treatmentPolicy: '',
      flags: { ccuHotline: false, impressiveCase: false, ...bool(O.EXAM_FLAGS_LEFT), ...bool(O.EXAM_FLAGS_RIGHT) },
      cancer: false, cancerName: '', aorticDisease: false, aorticDiseaseType: '',
      approach: '', sheath: { name: '', size: '' }, contrast: { agent: '', volume: '' }, fluoroTime: '', totalDose: '', startTime: '', endTime: '',
    },
    doctors: { attending: '', outpatient: '', operators: ['', '', ''], assistants: ['', '', ''], referralHospital: '', referralDoctor: '' },
    hemo: {
      pressures: Object.fromEntries(O.HEMO_TRIPLES.map(([k]) => [k, triple()])),
      values: { ...str(O.HEMO_VALUES_RIGHT), ...str(O.HEMO_VALVE), ...str(O.HEMO_SHUNT) },
    },
    prognosis: { deathDate: '', confirmDate: '', confirmer: '', comment: '', transferDate: '', maceRelation: '', angioFuExclude: '', angioFuExclude2: '' },
    other: { study1: '', study2: '', memo: '' },
    body: { height: '', weight: '', bodyTemp: '' },
    labs: {
      admission: { ...str(O.LAB_CHEM_1), ...str(O.LAB_CHEM_2), ...str(O.LAB_CHEM_3) },
      hbs: { date: '', hbsAg: '', hbsAgC: '' },
      hcv: { date: '', hcvAb: '', hcvAbC: '' },
      cbc: str(O.LAB_CBC), endocrine: str(O.LAB_ENDO), discharge: str(O.LAB_DISCHARGE), dischargeDate: '',
      bloodGas: str(O.LAB_GAS), legacy: str(O.LAB_LEGACY),
    },
    risk: {
      DM: '', DMtreatment: '', HD: '', CAPD: '', HT: '', HL: '', family: '',
      smoking: '', smokingPerDay: '', smokingStartAge: '', smokingQuitAge: '',
      eSmoking: '', eSmokingPerDay: '', eSmokingStartAge: '', eSmokingQuitAge: '',
      priorMI: '', priorHF: '', pciHx: '', cabgHx: '', renal: '', copd: '', pad: '',
    },
    complications: { status: '', items: bool(O.CATH_COMP), detail: '' },
    pciSummary: '', futurePlan: '', comment: '',
  };
}

/** 繰り返し項目の最大数（行・列は可変。追加はこの数まで） */
export const LIST_MAX = { collaterals: 5, grafts: 4, guiding: 5, micro: 4, gw: 5, lesions: 5, pressure: 5 } as const;

export const createCollateral = (): Collateral => ({ from: '', to: '', grade: '', state: '' });
export const createGraft = (): BypassGraft => ({ graft: '', anastomosis: '', patency: '' });
export const createGuiding = (): NameSize => ({ name: '', size: '' });
export const createText = (): string => '';

const seg = (): SegmentFinding => ({ size: '', calc: false, stenosis: '', diffuse: false, segmental: false, undefined: false, jeopardy: false, graftable: false });

export function createCagLvg(): CagLvg {
  return {
    approach: { artery: '', arterySheath: { name: '', size: '' }, vein: '', veinSheath: { name: '', size: '' }, support: '' },
    catheters: Object.fromEntries(O.CATHETER_SLOTS.map(([k]) => [k, { label: '', shape: '', size: '' }])),
    cag: {
      dominance: '',
      segments: Object.fromEntries(O.CAG_SEGMENTS.map((s) => [s.key, seg()])),
      collateralsNone: false,
      collaterals: [createCollateral()],
      grafts: [createGraft()],
      complication: '', squeezing: '', spasm: '', provocation: '',
      lesions: { count: '', LMT: false, LAD: false, LCX: false, RCA: false },
      syntax: '', euro: '', japan: '', comment: '',
    },
    lvg: {
      performed: false, view: '', agent: '', volume: '', rate: '',
      values: { LVEDV: '', LVESV: '', LVEDVI: '', LVESVI: '', LVSV: '', LVSVI: '', EF: '', CO: '', CI: '', LVEDP: '', HR: '' },
      wallMotion: str(O.LV_SEGMENTS),
      mr: '', thrombus: false, aneurysm: false, apicalBallooning: false, vsr: false,
      aog: { performed: false, ar: '', findings: '' },
      comment: '',
    },
  };
}

const devItem = (): DeviceItem => ({ category: '', name: '', size: '', length: '', pressure: '' });

export function createPciLesion(): PciLesion {
  return {
    target: '', targetSub: '', success: '', type: '', deNovoMajor: '', deNovoMinor: '',
    morph: { ...str(O.MORPH_YN), ...str(O.MORPH_YN2) },
    angulation: '', proximalTortuosity: '', ageOfOcclusion: '', branchProtection: '', lengthA: '', lengthB: '',
    pre: { ref: '', pct: '', mld: '' }, post: { ref: '', pct: '', mld: '' },
    technique: '', bmsReason1: '', bmsReason2: '', stentingReason: '', stentingMethod: '',
    device: {
      morphPost: '', items: times(10, devItem), reason: '', result: '', desHybrid: '', desBmsHybrid: '',
      failureReason: '', rotaBurr: '', protection: '',
      final: { balloon: '', stentLen: '', maxPress: '' }, overlap: { connected: '', totalLen: '', count: '' },
    },
    bif: { mainSide: '', main: { a: '', b: '' }, side: { a: '', b: '' }, stent: '', addProcedure: '', fateSB: '', kbt: { mb: '', sb: '', pressure: '' } },
    cto: { duration: '', jcto: { blunt: '', calc: '', bend: '', len20: '', retry: '' }, access: '', gwMethod: '', parallelWire: '', retro: { access: '', gc: { name: '', size: '' }, gw: '', vessel: '', channel: '', channelWire: '' } },
    comp: Object.fromEntries(O.COMP_LESION.flatMap((g) => g.items.map(([k]) => [k, '']))),
    summary: { treatment: '', tech: bool(O.PCI_TECH), pre: '', post: '', timiPre: '', timiPost: '', rentrop: '', comment: '', restudyHidden: false },
    ict: { type: '', agent: '', dose: '', result: '' },
  };
}

export function createPci(): Pci {
  return {
    basic: {
      lesionCount: '', support: '', result: '', failureReason: '', complication: '', mdct: false, ri: false, elapsed: '', killip: '',
      startComp: '', acuteComp: '', mace30: '', hospComp: '',
      guiding: [createGuiding()], micro: [''], gw: [''], patientTreatment: '',
    },
    lesions: [createPciLesion()],
    ctoScore: '',
    patientComp: str(O.COMP_PATIENT),
    patientTreat: str(O.TREAT_PATIENT),
    specificProcedure: '',
    jpci: {
      bg: {
        arrest24: '', shock24: '', ahf24: '',
        symptom1m: '', admitDx: '', other: '', stentThrombosis: false, comorbid: '',
        smoking: '', dialysis: '', lesionCount: '', lmt: '', aortic: false, aorticText: '',
      },
      pre: {
        imaging: '', imagingItems: bool(O.PREOP_IMAGING), ffrCt: '', ffr: false, ri: false, ffrValue: '', riValue: '',
        antiplatelet: '', apItems: bool(O.ANTIPLATELET), anticoag: '', acItems: bool(O.ANTICOAG), legacy: bool(O.ANTICOAG_LEGACY),
      },
      post: { antithrombotic: bool(O.POST_ANTITHROMBOTIC), antithromboticNone: false, lipid: bool(O.POST_LIPID), lipidNone: false },
      info: {
        jpciOperator: '', firstOp: '', firstOpNo: '', supervisor: '', supervisorName: '', supervisorNo: '', status: '', accessSite: '',
        procComp: '', compItems: bool(O.JPCI_COMP), nonAccessSite: false, deathDate: '', deathCause: '',
        mcs: '', mcsItems: bool(O.MCS_ITEMS), mcsTiming: str(O.MCS_ITEMS), imaging: '', imagingItems: bool(O.IMAGING_ITEMS),
      },
      discharge: { pciResult: '' },
    },
    risk: { staged: false, stagedText: '', hbrMajor: bool(O.HBR_MAJOR), hbrMinor: bool(O.HBR_MINOR), credo: bool(O.CREDO_ITEMS), st: bool(O.ST_RISK), daptMonths: '', memo: '' },
    ami: { onset: dt(), call: dt(), sceneArr: dt(), sceneDep: dt(), hospArr: dt(), cathLab: dt(), firstDevice: dt() },
  };
}

export const createPressureCol = (): PressureCol => ({
  lesion: '', phase: '', drug: '', dominancy: '', priorMI: '', priorMISite: '', stent: '', stentLesion: '',
  metrics: str(O.PRESSURE_METRICS), qca: str(O.QCA_METRICS),
});
const ivusSet = () => Object.fromEntries(O.IVUS_METRICS.map(([k]) => [k, { lesion: '', proximal: '', distal: '' }]));
export const createIvusLesion = (): IvusLesion => ({ site: '', pre: ivusSet(), post: ivusSet(), fibrofatty: false, fibrous: false, calcification: false, calcDegree: '', device: '', comment: '' });

export function createPressureIvus(): PressureIvus {
  return { pressure: [createPressureCol()], lesions: [createIvusLesion()] };
}

export function createPcps(): Pcps {
  return {
    arrest: dt(), call: dt(), sceneArr: dt(), sceneDep: dt(), hospArr: dt(), cathLab: dt(), start: dt(),
    firstEcg: '', operators: ['', '', ''], primingOperator: '', rosc: '',
    detail: { inflowSite: '', inflowSize: '', outflowSite: '', outflowSize: '', initialFlow: '', weaningDate: '', outcome: '', comment: '' },
  };
}

const med = () => ({ drug: '', dose: '', usage: '', days: '' });
export function createConference(): Conference {
  return {
    wardDoctor: '', disease: '', nyha: '', ccs: '', onsetCourse: '', comment: '',
    notPerformed: bool(O.CONF_TABS),
    prevPci: times(5, () => ({ date: '', site: '', device: '', note: '' })),
    scinti: { date: '', type: '', ischemia: '', infarct: '', sss: '', srs: '', sds: '', ef: '', findings: '' },
    mdct: { date: '', calciumScore: '', cadRads: '', findings: '' },
    ucg: { date: '', LVDd: '', LVDs: '', IVS: '', PW: '', EF: '', LAD: '', EA: '', Ee: '', TRPG: '', valve: '', wallMotion: '' },
    treadmill: { date: '', protocol: '', mets: '', maxHr: '', result: '', stChange: '', findings: '', prescriptions: times(6, med) },
    clinical: { diagnoses: '', infectionNote: '' },
    history: { past: '', course: '' },
    dischargeRx: times(10, med),
  };
}

const ev = () => ({ checked: false, date: '' });
export function createMaceEntry(): MaceEntry {
  return {
    mace: '', pciDate: '', lastVisit: '',
    negative: { checked: false, date: '' },
    positive: { checked: false, lastConfirmDate: '' },
    death: { ...ev(), cause: '', st: '' },
    acs: { ...ev(), st: '', content: '', st1st: '' },
    stroke: ev(), hf: ev(),
    bleeding: { ...ev(), site: '' },
    revasc: { ...ev(), site: '' },
    other: { ...ev(), text: '' },
  };
}

export function createRestudy(): Restudy {
  return {
    date: '', interval: '',
    lesions: times(5, () => ({ segment: '', prevPct: '', currPct: '', lateLoss: '', restenosis: '' as const, tlr: '' as const, comment: '' })),
    comment: '',
  };
}

export function createImageItem(): ImageItem {
  return { id: newId('img'), category: '', takenAt: '', view: '', lesion: '', title: '', description: '', fileName: '', mimeType: '', dataUrl: '', keyImage: false };
}

export const SECTION_FACTORIES: Record<SectionKey, () => any> = {
  cathRecord: createCathRecord,
  cagLvg: createCagLvg,
  pci: createPci,
  pressureIvus: createPressureIvus,
  pcps: createPcps,
  conference: createConference,
  mace: () => times(5, createMaceEntry),
  images: () => [],
  restudy: createRestudy,
};

export function createEmptyReport(patientRef = ''): CathReport {
  const t = nowIso();
  return {
    id: newId('rp'),
    patientRef,
    status: '入力中',
    verified: false,
    header: { studyDate: today(), cineNo: '', pciNo: '', accessionNo: '', secretaryChecked: false, summary: false, submitted: false, qca: false, registrant: '' },
    cathRecord: createCathRecord(),
    cagLvg: createCagLvg(),
    pci: createPci(),
    pressureIvus: createPressureIvus(),
    pcps: createPcps(),
    conference: createConference(),
    mace: times(5, createMaceEntry),
    images: [],
    restudy: createRestudy(),
    history: [],
    createdAt: t,
    updatedAt: t,
  };
}

/** 保存済み（または部分的な）データを全項目を持つ構造に正規化 */
export function normalizeReport(r: Partial<CathReport> & { id: string }): CathReport {
  const base = createEmptyReport(r.patientRef ?? '');
  const merged = mergeDefaults(base, r);
  fitLists(merged, r);
  migrateReport(merged, r);
  merged.images = (r.images ?? []).map((i) => mergeDefaults(createImageItem(), i));
  merged.history = r.history ?? [];
  return merged;
}

/**
 * 繰り返し項目を可変長に整える（読込時）。
 * 各要素を既定値で補い、末尾の空の要素を取り除く（最低 1 件）。
 * 途中の空の要素は詰めない（病変番号などの並びを変えないため）。
 * 最大数を超えて入力済みの旧データは、消さずにそのまま残す（追加だけできなくなる）。
 */
export function fitList<T>(src: unknown, create: () => T): T[] {
  const arr = Array.isArray(src) ? src.map((x) => mergeDefaults(create(), x)) : [];
  let n = arr.length;
  while (n > 0 && !hasAnyValue(arr[n - 1])) n--;
  return n === 0 ? [create()] : arr.slice(0, n);
}

function fitLists(m: CathReport, raw: any) {
  const cag = raw?.cagLvg?.cag, basic = raw?.pci?.basic;
  m.cagLvg.cag.collaterals = fitList(cag?.collaterals, createCollateral);
  m.cagLvg.cag.grafts = fitList(cag?.grafts, createGraft);
  m.pci.basic.guiding = fitList(basic?.guiding, createGuiding);
  m.pci.basic.micro = fitList(basic?.micro, createText);
  m.pci.basic.gw = fitList(basic?.gw, createText);
  m.pci.lesions = fitList(raw?.pci?.lesions, createPciLesion);
  // Pressure Wire の病変 N と IVUS の Lesion N は同じ病変：数をそろえ、病変名は Pressure Wire 側（pressure[N].lesion）に一本化
  const [pw, ivus] = fitPair(raw?.pressureIvus?.pressure, createPressureCol, raw?.pressureIvus?.lesions, createIvusLesion);
  pw.forEach((c, i) => {
    // 旧データ：Pressure Wire が空で IVUS の部位だけある時は移す（両方あって違う時は Pressure Wire を優先。IVUS 側の値は残す）
    if (!c.lesion && ivus[i].site) c.lesion = ivus[i].site;
  });
  m.pressureIvus.pressure = pw;
  m.pressureIvus.lesions = ivus;
}

/** 同じ番号で対になる 2 つの配列を、同じ数にそろえて整える（末尾の「両方とも空」を除く。最低 1 件） */
export function fitPair<A, B>(sa: unknown, ca: () => A, sb: unknown, cb: () => B): [A[], B[]] {
  const a = Array.isArray(sa) ? sa.map((x) => mergeDefaults(ca(), x)) : [];
  const b = Array.isArray(sb) ? sb.map((x) => mergeDefaults(cb(), x)) : [];
  let n = Math.max(a.length, b.length);
  while (n > 0 && !hasAnyValue(a[n - 1]) && !hasAnyValue(b[n - 1])) n--;
  n = Math.max(n, 1);
  const pad = <T,>(arr: T[], c: () => T) => Array.from({ length: n }, (_, i) => arr[i] ?? c());
  return [pad(a, ca), pad(b, cb)];
}

/** 既往歴・併存症の移動（J-PCI → カテ記録）。旧データの jpci.bg にある値を、カテ記録が空なら移す */
export const MOVED_HISTORY = ['priorMI', 'priorHF', 'pciHx', 'cabgHx', 'renal', 'copd', 'pad'] as const;

/** 旧形式のデータを現在の形式へ移す（読込時に毎回実行。値が移った後は何もしない） */
function migrateReport(m: CathReport, raw: Partial<CathReport>) {
  const oldBg = ((raw.pci as any)?.jpci?.bg ?? {}) as Record<string, string>;
  const risk = m.cathRecord.risk as unknown as Record<string, string>;
  for (const k of MOVED_HISTORY) if (!risk[k] && oldBg[k]) risk[k] = oldBg[k];
  const bg = m.pci.jpci.bg as unknown as Record<string, unknown>;
  for (const k of MOVED_HISTORY) delete bg[k];
  // CTO：旧「Age of Occlusion」から閉塞期間を補完
  m.pci.lesions.forEach((l) => {
    if (l.morph.cto === 'yes' && !l.cto.duration) l.cto.duration = durationFromAge(l.ageOfOcclusion);
  });
}

export function normalizePatient(p: Partial<Patient> & { id: string }): Patient {
  const merged = mergeDefaults(createEmptyPatient(), p);
  merged.admissions = (p.admissions ?? []).map((a) => mergeDefaults({ admitDate: '', dischargeDate: '', doctor: '', diagnosis: '', summary: '' }, a));
  return merged;
}

export const DEFAULT_MASTERS: Masters = {
  doctors: ['山田 太郎', '佐藤 健一', '鈴木 一郎', '高橋 誠', '田中 修', '伊藤 直樹'],
  hospitals: ['市民病院', '中央クリニック', '山の手内科', '港北循環器クリニック'],
  devices: [
    { category: 'DES', name: 'Xience Skypoint' },
    { category: 'DES', name: 'Synergy XD' },
    { category: 'DES', name: 'Resolute Onyx' },
    { category: 'DES', name: 'Ultimaster Nagomi' },
    { category: 'DES', name: 'Orsiro Mission' },
    { category: 'Balloon', name: 'Ryurei' },
    { category: 'Balloon', name: 'Emerge' },
    { category: 'NC Balloon', name: 'NC Trek' },
    { category: 'NC Balloon', name: 'Hiryu' },
    { category: 'Scoring', name: 'Scoreflex' },
    { category: 'Cutting', name: 'Wolverine' },
    { category: 'DCB', name: 'SeQuent Please' },
    { category: 'DCB', name: 'Agent' },
    { category: 'Rota burr', name: 'Rotablator' },
    { category: 'IVL', name: 'Shockwave C2+' },
    { category: 'Aspiration', name: 'Thrombuster III' },
    { category: 'Filter', name: 'Filtrap' },
    { category: 'Guiding', name: 'Launcher' },
    { category: 'Guiding', name: 'Heartrail' },
    { category: 'Micro', name: 'Corsair Pro' },
    { category: 'Micro', name: 'Caravel' },
    { category: 'Micro', name: 'Finecross' },
    { category: 'GW', name: 'Sion blue' },
    { category: 'GW', name: 'Runthrough NS' },
    { category: 'GW', name: 'Gaia Next 1' },
    { category: 'GW', name: 'Fielder XT-A' },
    { category: 'GW', name: 'Ultimate Bros 3' },
  ],
};
