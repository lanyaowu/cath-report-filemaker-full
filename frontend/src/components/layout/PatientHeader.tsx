import type { ReactNode } from 'react';
import { useApp } from '../../state/AppContext';
import { Calc, DateF, RadioF, RefLink, TextF } from '../../form/fields';
import { useForm } from '../../form/FormContext';
import { SEX_OPTS } from '../../constants/options';
import { ageAt, fmtDate } from '../../utils/date';
import { Panel } from '../common/ui';

/** 全画面共通の「患者属性」ヘッダ＋「カテ履歴」 */
export function PatientHeader({ extra }: { extra?: ReactNode }) {
  const app = useApp();
  const d = app.draft!;
  const f = useForm();
  const headerRef = !['patient', 'cathRecord'].includes(f.screen);
  const age = ageAt(d.patient.birthDate, d.report.header.studyDate);
  const history = app.reports
    .filter((r) => r.patientRef === d.patient.id)
    .sort((a, b) => b.header.studyDate.localeCompare(a.header.studyDate));

  return (
    <div className="hdr-row">
      <Panel title="患者属性" tone="tan" className="hdr-patient" right={headerRef ? <><span className="ref-legend"><i />参照のみ</span><RefLink to="cathRecord" /><RefLink to="patient" /></> : undefined}>
        <div className="hdr-grid">
          <DateF path="/report.header.studyDate" label="施行日" lw={48} />
          <TextF path="/patient.patientId" label="ID" lw={40} w={110} required />
          <TextF path="/report.header.cineNo" label="Cine.No" lw={60} w={96} />
          <TextF path="/report.header.pciNo" label="PCI.No" lw={56} w={96} />
          <TextF path="/patient.name" label="氏名" lw={48} w={150} required />
          <RadioF path="/patient.sex" label="性別" lw={40} options={SEX_OPTS} compact />
          <DateF path="/patient.birthDate" label="生年月日" lw={60} />
          <Calc label="年齢" lw={56} value={age} w={40} />
          <TextF path="/patient.kana" label="フリガナ" lw={48} w={150} />
          <div className="hdr-extra">{extra}</div>
        </div>
      </Panel>
      <Panel title="カテ履歴" tone="teal" className="hdr-history">
        <div className="hist-list">
          {history.length === 0 && <div className="muted">履歴なし</div>}
          {history.map((r) => (
            <button
              key={r.id}
              type="button"
              className={`hist-item ${r.id === d.report.id ? 'current' : ''}`}
              onClick={() => r.id !== d.report.id && app.openReport(r.id)}
            >
              <span>{fmtDate(r.header.studyDate)}</span>
              <span>{r.cathRecord.exam.examItems || '-'}</span>
              <span>{r.cathRecord.exam.urgency === '緊急' ? '緊急' : ''}</span>
            </button>
          ))}
        </div>
      </Panel>
    </div>
  );
}
