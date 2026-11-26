import { useState } from 'react';
import { useVal } from '../../form/FormContext';
import { Calc, DateTimeF } from '../../form/fields';
import { Btn, Modal } from '../../components/common/ui';
import { diffMinutes, fmtMinutes } from '../../utils/date';
import type { DateTime, Pci } from '../../types/model';

export function amiTimes(a: Pci['ami']) {
  return {
    o2b: diffMinutes(a.onset, a.firstDevice),
    d2b: diffMinutes(a.hospArr, a.firstDevice),
    door2lab: diffMinutes(a.hospArr, a.cathLab),
    call2door: diffMinutes(a.call, a.hospArr),
    lab2device: diffMinutes(a.cathLab, a.firstDevice),
  };
}

const STEPS: [keyof Pci['ami'], string][] = [
  ['onset', '発症'],
  ['call', '入電・覚知(119番)'],
  ['sceneArr', '現場着'],
  ['sceneDep', '現場発'],
  ['hospArr', '病院着'],
  ['cathLab', 'カテ室入室'],
  ['firstDevice', '最初のdevice使用'],
];

/** 時間経過シート（STEMI / PCPS 共用） */
export function TimelineSheet({ title, steps, onClose }: { title: string; steps: { label: string; dt: DateTime }[]; onClose: () => void }) {
  const valid = steps.filter((s) => s.dt.date && s.dt.time);
  const t0 = valid.length ? new Date(`${valid[0].dt.date}T${valid[0].dt.time}`).getTime() : 0;
  const tEnd = valid.length ? new Date(`${valid[valid.length - 1].dt.date}T${valid[valid.length - 1].dt.time}`).getTime() : 1;
  const span = Math.max(tEnd - t0, 1);
  return (
    <Modal title={title} onClose={onClose} width={640} footer={<Btn onClick={() => window.print()}>印刷</Btn>}>
      {valid.length < 2 ? (
        <p className="muted">日付・時刻を2つ以上入力してください。</p>
      ) : (
        <svg viewBox="0 0 600 80" width="100%" className="timeline">
          <line x1={20} y1={40} x2={580} y2={40} stroke="#567" strokeWidth={3} />
          {valid.map((s, i) => {
            const x = 20 + (560 * (new Date(`${s.dt.date}T${s.dt.time}`).getTime() - t0)) / span;
            return (
              <g key={s.label}>
                <circle cx={x} cy={40} r={6} fill="#2e7d6b" />
                <text x={x} y={i % 2 ? 70 : 20} fontSize={10} textAnchor="middle">{s.label}</text>
                <text x={x} y={i % 2 ? 58 : 32} fontSize={10} textAnchor="middle" fill="#555">{s.dt.time}</text>
              </g>
            );
          })}
        </svg>
      )}
      <table className="tbl" style={{ marginTop: 8 }}>
        <tbody>
          {steps.map((s, i) => (
            <tr key={s.label}>
              <th style={{ textAlign: 'right' }}>{s.label}</th>
              <td>{s.dt.date} {s.dt.time}</td>
              <td className="muted">{i > 0 ? fmtMinutes(diffMinutes(steps[i - 1].dt, s.dt)) : ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </Modal>
  );
}

/** AMI タブ scope: report.pci */
export function AmiTab() {
  const ami = useVal<Pci['ami']>('ami');
  const t = amiTimes(ami);
  const [sheet, setSheet] = useState(false);
  return (
    <div className="ami-layout">
      <div className="ami-sheet-btn">
        <Btn onClick={() => setSheet(true)}>🖨 STEMI時間経過シート</Btn>
      </div>
      <div>
        <div className="dt-head"><span>日付</span><span>時間</span></div>
        {STEPS.slice(0, 5).map(([k, l]) => (
          <DateTimeF key={k} path={`ami.${k}`} label={l} lw={150} />
        ))}
        <Calc label="入電 − 病院着時間" lw={150} value={fmtMinutes(t.call2door)} w={120} />
      </div>
      <div>
        <div className="dt-head"><span>日付</span><span>時間</span></div>
        {STEPS.slice(5).map(([k, l]) => (
          <DateTimeF key={k} path={`ami.${k}`} label={`${l}時間`} lw={150} />
        ))}
        <Calc label="Onset to balloon時間" lw={150} value={fmtMinutes(t.o2b)} w={120} />
        <Calc label="Door to balloon時間" lw={150} value={fmtMinutes(t.d2b)} w={120} className={t.d2b != null && t.d2b > 90 ? 'abn' : ''} />
        <Calc label="病院着 − カテ室入室時間" lw={150} value={fmtMinutes(t.door2lab)} w={120} />
      </div>
      {sheet && <TimelineSheet title="STEMI時間経過シート" steps={STEPS.map(([k, l]) => ({ label: l, dt: ami[k] }))} onClose={() => setSheet(false)} />}
    </div>
  );
}
