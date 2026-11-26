import { useApp } from '../../state/AppContext';
import { useVal } from '../../form/FormContext';
import { NumF, RadioF, SelectF, TextF } from '../../form/fields';
import { Btn } from '../../components/common/ui';
import { Note, Panel } from '../../components/common/ui';
import { LesionGrid, type GridRow } from './LesionGrid';
import * as O from '../../constants/options';
import type { PciLesion } from '../../types/model';
import { accAhaSuggest, CTO_DURATION, jctoMissing, jctoScore, JCTO_ITEMS } from '../../utils/clinical';

const yn = (path: string) => <RadioF path={path} options={O.YN_OPTS} compact />;
const txt = (path: string, list?: (string | O.Opt)[]) => <TextF path={path} w="100%" list={list} />;

/** Type 欄＋ACC/AHA の自動提案（形態の入力から A/B1/B2/C を提案。「適用」で Type に反映） */
function TypeCell({ i }: { i: number }) {
  const app = useApp();
  const l = useVal<PciLesion>(`lesions.${i}`);
  const sg = accAhaSuggest(l);
  const diff = !!sg && !!l.type && sg.type !== l.type;
  const why = sg ? [...sg.c.map((x) => `C：${x}`), ...sg.b.map((x) => `B：${x}`)].join('\n') || '該当する特徴なし（Type A）' : '';
  return (
    <div style={{ width: '100%' }}>
      {txt(`lesions.${i}.type`, O.LESION_TYPES)}
      {sg && (
        <div className={`suggest ${diff ? 'suggest-diff' : ''}`} title={`ACC/AHA 分類の自動提案\n${why}`}>
          提案 <b>{sg.type}</b>
          {sg.type !== l.type && (
            <button type="button" className="get-btn" onClick={() => app.form!.set(`report.pci.lesions.${i}.type`, sg.type)}>
              適用
            </button>
          )}
          {diff && <span className="suggest-note">入力と異なる</span>}
        </div>
      )}
    </div>
  );
}

/** J-CTO スコアの表示（病変ごと） */
function JctoCell({ i }: { i: number }) {
  const l = useVal<PciLesion>(`lesions.${i}`);
  if (l.morph.cto !== 'yes') return <span className="muted small">CTO 以外</span>;
  const sc = jctoScore(l);
  const miss = jctoMissing(l);
  return sc == null ? <span className="muted small">未回答 {miss} 項目</span> : <b className="calc-v">{sc} 点{sc >= 3 ? '（very difficult）' : sc === 2 ? '（difficult）' : sc === 1 ? '（intermediate）' : '（easy）'}</b>;
}

/** 病変形態タブ */
export function MorphTab() {
  const app = useApp();
  const lesions = useVal<PciLesion[]>('lesions');

  /** Pressure/IVUS 画面の QCA から Ref/%DS/MLD を取得（Target が一致する列、pre/post で振分け） */
  const fetchQca = (i: number, phase: 'pre' | 'post') => {
    const t = lesions[i].target.replace('#', '');
    const cols = app.draft!.report.pressureIvus.pressure;
    const col = cols.find((c) => t && c.lesion.includes(t) && (phase === 'post' ? c.phase === 'post PCI' : c.phase !== 'post PCI'));
    if (!col || !(col.qca.refDiameter || col.qca.pctDS || col.qca.mld)) {
      app.toast('Pressure/IVUS 画面に該当病変の QCA がありません', 'err');
      return;
    }
    app.form!.set(`report.pci.lesions.${i}.${phase}`, { ref: col.qca.refDiameter, pct: col.qca.pctDS, mld: col.qca.mld });
  };

  const qcaRow = (phase: 'pre' | 'post') => (i: number) => (
    <>
      <NumF path={`lesions.${i}.${phase}.ref`} w={44} title="Ref (mm)" />
      <NumF path={`lesions.${i}.${phase}.pct`} w={40} title="%DS" />
      <NumF path={`lesions.${i}.${phase}.mld`} w={44} title="MLD (mm)" />
      <button type="button" className="get-btn" onClick={() => fetchQca(i, phase)}>
        取得
      </button>
    </>
  );

  const rows: GridRow[] = [
    { label: 'Type（ACC/AHA）', render: (i) => <TypeCell i={i} /> },
    {
      label: (
        <span className="two-line">
          de novo...<small>大分類 / 小分類</small>
        </span>
      ),
      render: (i) => (
        <>
          <TextF path={`lesions.${i}.deNovoMajor`} w="48%" list={O.DENOVO_MAJOR} />
          <TextF path={`lesions.${i}.deNovoMinor`} w="48%" list={O.DENOVO_MINOR} />
        </>
      ),
    },
    ...O.MORPH_YN.map(([k, l]) => ({ label: l, render: (i: number) => yn(`lesions.${i}.morph.${k}`) })),
    { label: 'Angulation', render: (i) => txt(`lesions.${i}.angulation`, O.ANGULATION) },
    ...O.MORPH_YN2.map(([k, l]) => ({ label: l, render: (i: number) => yn(`lesions.${i}.morph.${k}`) })),
    { label: 'ProximalTortuosity', render: (i) => txt(`lesions.${i}.proximalTortuosity`, O.TORTUOSITY) },
    { label: 'Age of Occlusion', render: (i) => txt(`lesions.${i}.ageOfOcclusion`, ['<1ヶ月', '1-3ヶ月', '>3ヶ月', '不明']) },
    { label: 'Branch Protection', render: (i) => txt(`lesions.${i}.branchProtection`, ['GW', 'Balloon', 'Stent', 'なし']) },
    {
      label: 'Length',
      render: (i) => (
        <>
          <NumF path={`lesions.${i}.lengthA`} w={50} unit="mm" />
          <TextF path={`lesions.${i}.lengthB`} w={70} list={['<10mm', '10-20mm', '>20mm']} />
        </>
      ),
    },
    { label: 'Pre  Ref. ,%,MLD', render: qcaRow('pre') },
    { label: 'Post Ref. ,%,MLD', render: qcaRow('post') },
    { label: 'Technique', render: (i) => txt(`lesions.${i}.technique`, ['Direct stenting', 'Pre-dilatation', 'POBA', 'DCB only', 'Atherectomy+Stent']) },
    {
      label: (
        <span className="two-line">
          BMS選択の理由<small>(Reason of not DES)</small>
        </span>
      ),
      render: (i) => (
        <div style={{ width: '100%' }}>
          {txt(`lesions.${i}.bmsReason1`, ['出血リスク', 'DAPT継続困難', '手術予定', '大血管径'])}
          {txt(`lesions.${i}.bmsReason2`)}
        </div>
      ),
    },
    { label: 'Reason of Stenting', render: (i) => txt(`lesions.${i}.stentingReason`, ['de novo lesion', 'Bail out', 'Suboptimal result', 'Dissection']) },
    { label: 'Method of Stenting', render: (i) => txt(`lesions.${i}.stentingMethod`, ['Angio guided', 'IVUS guided', 'OCT guided', 'Physiology guided']) },
  ];
  return <LesionGrid rows={rows} withSub labelWidth={170} />;
}

/** Device タブ */
export function DeviceTab() {
  const app = useApp();
  const lesions = useVal<PciLesion[]>('lesions');
  const devNames = (cat: string) => app.masters.devices.filter((d) => !cat || d.category === cat).map((d) => d.name);

  const deriveFinal = (i: number) => {
    const items = lesions[i].device.items.filter((d) => d.name || d.category);
    const nums = (xs: string[]) => xs.map(Number).filter((x) => isFinite(x) && x > 0);
    const balloons = nums(items.filter((d) => /Balloon|NC|Scoring|Cutting|DCB/.test(d.category)).map((d) => d.size));
    const stents = nums(items.filter((d) => /DES|BMS/.test(d.category)).map((d) => d.length));
    const press = nums(items.map((d) => d.pressure));
    app.form!.set(`report.pci.lesions.${i}.device.final`, {
      balloon: balloons.length ? String(Math.max(...balloons)) : '',
      stentLen: stents.length ? String(stents.reduce((a, b) => a + b, 0)) : '',
      maxPress: press.length ? String(Math.max(...press)) : '',
    });
  };

  const rows: GridRow[] = [{ label: '病変形態(post)', render: (i) => txt(`lesions.${i}.device.morphPost`) }];
  for (let k = 0; k < 10; k++) {
    rows.push(
      {
        label: `Device${k + 1}`,
        tone: 'blue',
        render: (i) => (
          <>
            <TextF path={`lesions.${i}.device.items.${k}.category`} w="34%" list={O.DEVICE_CATEGORIES} />
            <TextF path={`lesions.${i}.device.items.${k}.name`} w="62%" list={devNames(lesions[i].device.items[k]?.category)} />
          </>
        ),
      },
      {
        label: 'サイズ.長さ.圧',
        tone: 'green',
        render: (i) => (
          <>
            <NumF path={`lesions.${i}.device.items.${k}.size`} w="31%" title="サイズ(mm)" />
            <NumF path={`lesions.${i}.device.items.${k}.length`} w="31%" title="長さ(mm)" />
            <NumF path={`lesions.${i}.device.items.${k}.pressure`} w="31%" title="圧(atm)" />
          </>
        ),
      },
    );
  }
  rows.push(
    {
      label: '理由、結果',
      render: (i) => (
        <>
          <TextF path={`lesions.${i}.device.reason`} w="48%" />
          <TextF path={`lesions.${i}.device.result`} w="48%" list={O.PCI_RESULTS} />
        </>
      ),
    },
    { label: 'DESs Hybrid', render: (i) => yn(`lesions.${i}.device.desHybrid`) },
    { label: 'DES-BMS Hybrid', render: (i) => yn(`lesions.${i}.device.desBmsHybrid`) },
    { label: 'Reason for failure', render: (i) => txt(`lesions.${i}.device.failureReason`, ['GW不通過', 'Device不通過', '解離', '穿孔', 'その他']) },
    { label: 'Rota burr size', render: (i) => txt(`lesions.${i}.device.rotaBurr`, ['1.25', '1.5', '1.75', '2.0', '2.15']) },
    { label: 'Protection Device', render: (i) => txt(`lesions.${i}.device.protection`, ['Filtrap', 'Parachute', 'なし']) },
    {
      label: (
        <span className="two-line">
          最終Balloon径<small>総Stent長, MaxPress</small>
        </span>
      ),
      render: (i) => (
        <>
          <NumF path={`lesions.${i}.device.final.balloon`} w="27%" />
          <NumF path={`lesions.${i}.device.final.stentLen`} w="27%" />
          <NumF path={`lesions.${i}.device.final.maxPress`} w="27%" />
          <button type="button" className="get-btn" title="Device1〜10から算出" onClick={() => deriveFinal(i)}>
            算出
          </button>
        </>
      ),
    },
    {
      label: (
        <span className="two-line">
          stent連続<small>連続総長, 連続総数</small>
        </span>
      ),
      render: (i) => (
        <>
          <TextF path={`lesions.${i}.device.overlap.connected`} w="31%" list={['有', '無']} />
          <NumF path={`lesions.${i}.device.overlap.totalLen`} w="31%" />
          <NumF path={`lesions.${i}.device.overlap.count`} w="31%" />
        </>
      ),
    },
  );
  return (
    <>
      <LesionGrid rows={rows} labelWidth={150} />
      <Note style={{ textAlign: 'center', fontWeight: 600 }}>※複数ステントが連結（オーバーラップ）した場合、中枢側病変部位のみに記載すること</Note>
    </>
  );
}

/** Bif/CTO タブ */
export function BifCtoTab() {
  const pair = (a: string, b: string, la?: (string | O.Opt)[], lb?: (string | O.Opt)[]) => (
    <>
      <TextF path={a} w="34%" list={la} />
      <TextF path={b} w="62%" list={lb} />
    </>
  );
  const rows: GridRow[] = [
    { label: '<Bifurcation>', section: true },
    { label: 'Main/Side branch', render: (i) => txt(`lesions.${i}.bif.mainSide`, ['Medina 1,1,1', 'Medina 1,1,0', 'Medina 1,0,1', 'Medina 0,1,1', 'Medina 1,0,0', 'Medina 0,1,0', 'Medina 0,0,1']) },
    { label: 'Main branch', render: (i) => pair(`lesions.${i}.bif.main.a`, `lesions.${i}.bif.main.b`, ['LAD', 'LCX', 'RCA', 'LMT'], ['Stent', 'Balloon', 'GW only']) },
    { label: 'Side branch', render: (i) => pair(`lesions.${i}.bif.side.a`, `lesions.${i}.bif.side.b`, ['Dx', 'OM', 'PL', 'PD', 'LCX', 'Septal'], ['Stent', 'Balloon', 'GW only', 'なし']) },
    { label: 'Bifurcation Stent', render: (i) => txt(`lesions.${i}.bif.stent`, O.BIF_STENTS) },
    { label: 'Add Procedure', render: (i) => txt(`lesions.${i}.bif.addProcedure`, ['KBT', 'POT', 'POT-side-POT', 'Re-POT', 'DCB to SB']) },
    { label: 'Fate of SB', render: (i) => txt(`lesions.${i}.bif.fateSB`, ['TIMI3', 'TIMI2', 'TIMI1', 'TIMI0', '閉塞']) },
    { label: '<KBT>', section: true },
    {
      label: 'Balloon Diam ( MB,SB ),Pressure',
      render: (i) => (
        <>
          <NumF path={`lesions.${i}.bif.kbt.mb`} w="31%" title="MB径" />
          <NumF path={`lesions.${i}.bif.kbt.sb`} w="31%" title="SB径" />
          <NumF path={`lesions.${i}.bif.kbt.pressure`} w="31%" title="圧" />
        </>
      ),
    },
    { label: '<CTO>', section: true },
    { label: '閉塞期間', render: (i) => <SelectFW path={`lesions.${i}.cto.duration`} /> },
    ...JCTO_ITEMS.map(([k, l]) => ({ label: `J-CTO：${l}`, render: (i: number) => yn(`lesions.${i}.cto.jcto.${k}`) })),
    { label: 'J-CTO スコア（病変）', tone: 'blue' as const, render: (i: number) => <JctoCell i={i} /> },
    { label: 'Access', render: (i) => txt(`lesions.${i}.cto.access`, O.CTO_ACCESS) },
    { label: 'Method of GW passing', render: (i) => txt(`lesions.${i}.cto.gwMethod`, O.GW_METHOD) },
    { label: 'Parallel wire', render: (i) => yn(`lesions.${i}.cto.parallelWire`) },
    { label: '<Retro>', section: true },
    { label: 'Access', render: (i) => txt(`lesions.${i}.cto.retro.access`, ['Septal', 'Epicardial', 'Graft']) },
    {
      label: 'GC',
      render: (i) => (
        <>
          <TextF path={`lesions.${i}.cto.retro.gc.name`} w="70%" list={['EBU3.5', 'EBU3.75', 'AL1', 'JR4', 'SAL1']} />
          <TextF path={`lesions.${i}.cto.retro.gc.size`} w="26%" list={O.SHEATH_SIZES} />
        </>
      ),
    },
    { label: 'GW', render: (i) => txt(`lesions.${i}.cto.retro.gw`, ['Sion', 'Suoh 03', 'Fielder XT-R', 'Gaia Next']) },
    { label: 'Vessel', render: (i) => txt(`lesions.${i}.cto.retro.vessel`, ['LAD', 'LCX', 'RCA']) },
    { label: 'Channel', render: (i) => txt(`lesions.${i}.cto.retro.channel`, ['Septal CC', 'Epicardial CC', 'Atrial']) },
    { label: 'Channel Passing Wire', render: (i) => txt(`lesions.${i}.cto.retro.channelWire`) },
  ];
  return (
    <>
      <LesionGrid rows={rows} labelWidth={200} />
      <CtoScoreAll />
    </>
  );
}

/** Complication タブ */
export function ComplicationTab() {
  const rows: GridRow[] = O.COMP_LESION.flatMap((g) => [
    { label: <i>{g.title}</i>, section: true } as GridRow,
    ...g.items.map(([k, l]) => ({ label: l, render: (i: number) => yn(`lesions.${i}.comp.${k}`) })),
  ]);
  return (
    <div className="cols" style={{ alignItems: 'flex-start' }}>
      <div style={{ flex: '1 1 760px' }}>
        <LesionGrid rows={rows} labelWidth={230} />
        <TextF path="specificProcedure" label={<b>Specific procedure</b>} lw={130} w={240} />
      </div>
      <div style={{ width: 330 }}>
        <Panel title={<i>Patient complication</i>} tone="plain">
          {O.COMP_PATIENT.map(([k, l]) => (
            <RadioF key={k} path={`patientComp.${k}`} label={<b>{l}</b>} lw={200} options={O.YN_OPTS} compact />
          ))}
        </Panel>
        <Panel title={<i>Treatment to patient</i>} tone="plain">
          {O.TREAT_PATIENT.map(([k, l]) => (
            <RadioF key={k} path={`patientTreat.${k}`} label={<b>{l}</b>} lw={200} options={O.YN_OPTS} compact />
          ))}
        </Panel>
      </div>
    </div>
  );
}


const SelectFW = ({ path }: { path: string }) => <SelectF path={path} w="100%" options={CTO_DURATION} />;

/** 手技全体の CTO Score（旧項目）。病変ごとの J-CTO の最大値を反映できる */
function CtoScoreAll() {
  const app = useApp();
  const lesions = useVal<PciLesion[]>('lesions');
  const scores = lesions.map(jctoScore).filter((x): x is number => x != null);
  return (
    <div className="row" style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 6 }}>
      <NumF path="ctoScore" label="CTO Score（J-CTO・手技全体）" lw={190} w={48} />
      <Btn small disabled={!scores.length} onClick={() => app.form!.set('report.pci.ctoScore', String(Math.max(...scores)))}>
        病変の最大値を反映
      </Btn>
      <span className="muted small">J-CTO は病変ごとに入力します（上の表）。</span>
    </div>
  );
}
