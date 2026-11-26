import { useState } from 'react';
import { useApp } from '../state/AppContext';
import { Scope, useVal } from '../form/FormContext';
import { Calc, DateF, DateTimeF, Fld, NumF, SelectF, TextAreaF, TextF } from '../form/fields';
import { Btn, Panel } from '../components/common/ui';
import { ScreenFrame } from '../components/layout/ScreenFrame';
import { TimelineSheet } from './Pci/AmiTab';
import { FIRST_ECG } from '../constants/options';
import { diffMinutes, fmtMinutes } from '../utils/date';
import type { Pcps } from '../types/model';

const LEFT: [keyof Pcps, string][] = [
  ['arrest', '心停止時間'],
  ['call', '入電・覚知(119番)'],
  ['sceneArr', '現場着'],
  ['sceneDep', '現場発'],
  ['hospArr', '病院着'],
];

function PcpsBody() {
  const app = useApp();
  const p = useVal<Pcps>('');
  const [sheet, setSheet] = useState(false);
  const docs = app.masters.doctors;
  const steps = [...LEFT, ['cathLab', 'カテ室入室'] as const, ['start', 'PCPS開始'] as const].map(([k, l]) => ({ label: l, dt: p[k as 'arrest'] }));

  return (
    <Panel title="PCPS" right={<Btn small onClick={() => setSheet(true)}>🖨 PCPS時間経過シート</Btn>}>
      <div className="pcps-layout">
        <div>
          <div className="dt-head"><span>日付</span><span>時間</span></div>
          {LEFT.map(([k, l]) => (
            <DateTimeF key={k} path={k} label={k === 'arrest' ? <span>心停止時間<br /><small>(不明の場合は119番通報時間)</small></span> : l} lw={170} />
          ))}
          <div style={{ height: 14 }} />
          <Calc label="心停止 − PCPS開始時間" lw={170} value={fmtMinutes(diffMinutes(p.arrest, p.start))} w={120} />
          <Calc label="病院着 − PCPS開始時間" lw={170} value={fmtMinutes(diffMinutes(p.hospArr, p.start))} w={120} />
          <Calc label="カテ室入室時間 − PCPS開始時間" lw={170} value={fmtMinutes(diffMinutes(p.cathLab, p.start))} w={120} />
        </div>
        <div>
          <div className="dt-head"><span>日付</span><span>時間</span></div>
          <DateTimeF path="cathLab" label="カテ室入室時間" lw={130} />
          <DateTimeF path="start" label="PCPS開始時間" lw={130} />
          <SelectF path="firstEcg" label="初回心電図" lw={130} w={200} options={FIRST_ECG} />
          <Fld label="術者" lw={130}>
            {[0, 1, 2].map((i) => (
              <TextF key={i} path={`operators.${i}`} w={96} list={docs} />
            ))}
          </Fld>
          <TextF path="primingOperator" label="PCPSプライミング術者" lw={130} w={130} />
          <TextF path="rosc" type="time" label="自己心拍再開" lw={130} w={96} />
        </div>
      </div>
      <div className="sub-title" style={{ marginTop: 10 }}>PCPS詳細（推測項目）</div>
      <div className="grid3">
        <TextF path="detail.outflowSite" label="脱血部位" lw={80} w={110} list={['Rt FV', 'Lt FV', 'Rt IJV']} />
        <TextF path="detail.outflowSize" label="脱血管" lw={60} w={70} list={['19.5Fr', '21Fr', '22Fr', '24Fr']} />
        <NumF path="detail.initialFlow" label="初期流量" lw={70} w={50} unit="L/min" />
        <TextF path="detail.inflowSite" label="送血部位" lw={80} w={110} list={['Rt FA', 'Lt FA']} />
        <TextF path="detail.inflowSize" label="送血管" lw={60} w={70} list={['15Fr', '16.5Fr', '18Fr']} />
        <DateF path="detail.weaningDate" label="離脱日" lw={70} />
        <TextF path="detail.outcome" label="転帰" lw={80} w={200} list={['離脱', '離脱予定', 'VAD移行', '死亡']} />
      </div>
      <TextAreaF path="detail.comment" label="コメント" lw={80} rows={2} />
      {sheet && <TimelineSheet title="PCPS時間経過シート" steps={steps} onClose={() => setSheet(false)} />}
    </Panel>
  );
}

/** PCPS */
export function PcpsScreen() {
  return (
    <ScreenFrame>
      <Scope path="/report.pcps">
        <PcpsBody />
      </Scope>
    </ScreenFrame>
  );
}
