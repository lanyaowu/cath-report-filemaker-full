import { useApp } from '../../state/AppContext';
import { useField, useVal } from '../../form/FormContext';
import { CheckF, Fld, NumF, SelectF, TextAreaF, TextF } from '../../form/fields';
import { Btn, Panel, Row } from '../../components/common/ui';
import * as O from '../../constants/options';
import { bsa, lvgDerived } from '../../utils/calc';
import type { CagLvg } from '../../types/model';

const WM_COLOR: Record<string, string> = { '': '#c9d1d6', N: '#6dbb7a', Hypo: '#f0d34a', SevHypo: '#f19a3e', A: '#d9534f', D: '#8e44ad', An: '#7b1e1e' };
const WM_KEYS = ['', ...O.WALL_MOTION.map((o) => o.value)];

function arc(cx: number, cy: number, rx: number, ry: number, a1: number, a2: number) {
  const p = (a: number) => [cx + rx * Math.cos((a * Math.PI) / 180), cy + ry * Math.sin((a * Math.PI) / 180)];
  const [x1, y1] = p(a1);
  const [x2, y2] = p(a2);
  const large = Math.abs(a2 - a1) > 180 ? 1 : 0;
  return `M${x1.toFixed(1)},${y1.toFixed(1)} A${rx},${ry} 0 ${large} 1 ${x2.toFixed(1)},${y2.toFixed(1)}`;
}

function Segment({ seg, d, label, lx, ly }: { seg: string; d: string; label: string; lx: number; ly: number }) {
  const f = useField<string>(`wallMotion.${seg}`);
  const next = () => f.set(WM_KEYS[(WM_KEYS.indexOf(f.value ?? '') + 1) % WM_KEYS.length]);
  return (
    <g onClick={next} style={{ cursor: 'pointer' }} data-wm={f.full} data-seg={seg}>
      <title>{`${label}: ${O.WALL_MOTION.find((o) => o.value === f.value)?.label ?? '未入力'}（クリックで切替）`}</title>
      <path d={d} stroke={WM_COLOR[f.value ?? ''] ?? '#ccc'} strokeWidth={14} fill="none" strokeLinecap="butt" />
      <text x={lx} y={ly} fontSize={11} textAnchor="middle" fill="#333">{seg}</text>
    </g>
  );
}

/** AHA 7分画の壁運動図（RAO / LAO）。分画をクリックで壁運動を順に切替 */
function LvDiagram() {
  return (
    <svg viewBox="0 0 330 190" width={330} height={190} className="lv-diagram" role="img" aria-label="左室壁運動図">
      <text x={70} y={14} fontSize={11} textAnchor="middle">RAO</text>
      <path d="M52,24 L88,24" stroke="#888" strokeWidth={2} />
      <Segment seg="1" label="Anterobasal" d={arc(70, 98, 50, 72, 200, 250)} lx={22} ly={48} />
      <Segment seg="2" label="Anterolateral" d={arc(70, 98, 50, 72, 140, 200)} lx={8} ly={120} />
      <Segment seg="3" label="Apical" d={arc(70, 98, 50, 72, 60, 140)} lx={70} ly={186} />
      <Segment seg="4" label="Diaphragmatic" d={arc(70, 98, 50, 72, 0, 60)} lx={132} ly={140} />
      <Segment seg="5" label="Posterobasal" d={arc(70, 98, 50, 72, 290, 360)} lx={130} ly={60} />
      <text x={240} y={14} fontSize={11} textAnchor="middle">LAO</text>
      <Segment seg="6" label="Septal" d={arc(240, 98, 55, 68, 100, 260)} lx={172} ly={100} />
      <Segment seg="7" label="Posterolateral" d={arc(240, 98, 55, 68, 280, 440)} lx={310} ly={100} />
    </svg>
  );
}

/** LVG タブ（scope: report.cagLvg.lvg）：参考画面なしのため一般的な左室造影報告項目から推測 */
export function LvgTab() {
  const app = useApp();
  const lvg = useVal<CagLvg['lvg']>('');
  const body = app.draft!.report.cathRecord.body;
  const hr = app.draft!.report.cathRecord.hemo.values.HR;
  const b = bsa(body.height, body.weight);

  const calc = () => {
    const out = lvgDerived(lvg.values.LVEDV, lvg.values.LVESV, b, lvg.values.HR || hr);
    if (!Object.keys(out).length) return app.toast('LVEDV・LVESV を入力してください', 'err');
    app.form!.setMany(Object.entries(out).map(([k, v]) => [`report.cagLvg.lvg.values.${k}`, v] as [string, unknown]));
    app.toast(`算出しました（BSA ${b || '未入力'}）`);
  };

  const V = (k: string, l: string, unit = '') => <NumF key={k} path={`values.${k}`} label={l} lw={72} w={60} unit={unit} />;

  return (
    <div className="lvg-layout">
      <Panel title="左室造影 (LVG)" right={<CheckF path="performed" label="施行" />}>
        <Row>
          <TextF path="view" label="撮影方向" lw={72} w={110} list={['RAO30/LAO60', 'RAO30', 'LAO60', 'Biplane']} />
          <TextF path="agent" label="造影剤" lw={50} w={120} list={O.CONTRAST_AGENTS} />
          <NumF path="volume" label="注入量" lw={50} w={44} unit="ml" />
          <NumF path="rate" label="注入速度" lw={60} w={44} unit="ml/s" />
        </Row>
        <div className="lvg-values">
          <div>
            {V('LVEDV', 'LVEDV', 'ml')}
            {V('LVESV', 'LVESV', 'ml')}
            {V('LVSV', 'LVSV', 'ml')}
            {V('EF', 'LVEF', '%')}
          </div>
          <div>
            {V('LVEDVI', 'LVEDVI', 'ml/m²')}
            {V('LVESVI', 'LVESVI', 'ml/m²')}
            {V('LVSVI', 'LVSVI', 'ml/m²')}
            {V('LVEDP', 'LVEDP', 'mmHg')}
          </div>
          <div>
            {V('HR', 'HR', '/min')}
            {V('CO', 'CO', 'L/min')}
            {V('CI', 'CI', 'L/min/m²')}
            <Fld label="" lw={72}>
              <Btn small onClick={calc} title="LVEDV/LVESV と カテ記録の身長・体重(BSA)・HR から算出">SV・EF・Index 算出</Btn>
            </Fld>
          </div>
        </div>
      </Panel>
      <div className="cols">
        <Panel title="壁運動 (AHA分画)">
          <div className="cols" style={{ alignItems: 'flex-start' }}>
            <LvDiagram />
            <div>
              {O.LV_SEGMENTS.map(([k, l]) => (
                <SelectF key={k} path={`wallMotion.${k}`} label={l} lw={110} w={120} options={O.WALL_MOTION} />
              ))}
              <div className="wm-legend">
                {O.WALL_MOTION.map((o) => (
                  <span key={o.value}>
                    <i style={{ background: WM_COLOR[o.value] }} />
                    {o.label}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </Panel>
        <Panel title="所見">
          <SelectF path="mr" label="MR (Sellers)" lw={90} w={70} options={O.SELLERS} />
          <div className="grid2 tight">
            <CheckF path="thrombus" label="LV内血栓" />
            <CheckF path="aneurysm" label="心室瘤" />
            <CheckF path="apicalBallooning" label="心尖部バルーニング" />
            <CheckF path="vsr" label="VSR" />
          </div>
          <div className="sub-title" style={{ marginTop: 8 }}>大動脈造影 (AOG)</div>
          <CheckF path="aog.performed" label="施行" />
          <SelectF path="aog.ar" label="AR (Sellers)" lw={90} w={70} options={O.SELLERS} />
          <TextF path="aog.findings" label="所見" lw={90} w={200} />
        </Panel>
      </div>
      <Panel title="LVG Comment">
        <TextAreaF path="comment" rows={3} />
      </Panel>
    </div>
  );
}
