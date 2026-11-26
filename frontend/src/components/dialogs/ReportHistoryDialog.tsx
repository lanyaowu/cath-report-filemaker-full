import { useEffect, useMemo, useState } from 'react';
import { useApp } from '../../state/AppContext';
import { Btn, Modal } from '../common/ui';
import { fmtDateTime } from '../../utils/date';
import { actionLabel, auditCsv, markHistory, type AuditEntry, type HistoryMark } from '../../audit/model';
import { pathLabel, sectionLabel } from '../../audit/labels';
import { ChangeTable, downloadText } from './AuditDialog';

const MARK_TEXT: Record<HistoryMark, string> = { confirm: '確定', unlock: '確定解除', afterUnlock: '確定解除後の変更', '': '' };

/** レポートの変更履歴：誰が・いつ・どの項目を変えたか（患者情報の変更も含む）。確定解除と、その後の変更を目立たせる */
export function ReportHistoryDialog({ onClose }: { onClose: () => void }) {
  const app = useApp();
  const d = app.draft;
  const [list, setList] = useState<AuditEntry[] | null>(null);
  const [err, setErr] = useState('');
  const [withPatient, setWithPatient] = useState(true);
  const [section, setSection] = useState('');

  useEffect(() => {
    if (!d) return;
    app.adapter.reportHistory(d.report.id).then(setList, (e: unknown) => {
      setErr(e instanceof Error ? e.message : String(e));
      setList([]);
    });
  }, [app.adapter, d?.report.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const marks = useMemo(() => markHistory(list ?? []), [list]);
  const sections = useMemo(() => {
    const s = new Set<string>();
    for (const e of list ?? []) for (const c of e.changes ?? []) s.add(sectionLabel(c.path, e.targetType));
    return [...s];
  }, [list]);
  const shown = (list ?? [])
    .filter((e) => withPatient || e.targetType !== 'patient')
    .map((e) => (section ? { ...e, changes: (e.changes ?? []).filter((c) => sectionLabel(c.path, e.targetType) === section) } : e))
    .filter((e) => !section || (e.changes?.length ?? 0) > 0);

  if (!d) return null;
  return (
    <Modal
      title={`変更履歴（${d.patient.name || '-'}・${d.report.header.studyDate || '-'}）`}
      onClose={onClose}
      width={980}
      footer={
        <>
          <Btn disabled={!shown.length} onClick={() => downloadText(`history_${d.report.id}.csv`, auditCsv(shown, pathLabel))}>CSV 出力</Btn>
          <Btn onClick={onClose}>閉じる</Btn>
        </>
      }
    >
      <div className="audit-filter">
        <label><input type="checkbox" checked={withPatient} onChange={(e) => setWithPatient(e.target.checked)} /> 患者情報の変更も表示</label>
        <label>
          区分{' '}
          <select className="inp" value={section} onChange={(e) => setSection(e.target.value)}>
            <option value="">（すべて）</option>
            {sections.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <span className="muted">{list ? `${shown.length} 回の保存` : '読込中…'}</span>
        {app.isDirty && <span className="audit-warn">未保存の変更は含まれていません</span>}
      </div>
      {err && <div className="audit-err">{err}</div>}
      <div className="scroll audit-scroll">
        {shown.map((e) => {
          const m = marks.get(e.id) ?? '';
          return (
            <section key={e.id} className={`hist-entry${m ? ` mark-${m}` : ''}`} data-id={e.id}>
              <header>
                <b>{fmtDateTime(e.at)}</b>
                <span>{e.displayName || e.username || '-'}</span>
                <span className="hist-act">{e.targetType === 'patient' ? `患者情報・${actionLabel(e.action)}` : actionLabel(e.action)}</span>
                {m && <span className={`hist-mark mark-${m}`}>{MARK_TEXT[m]}</span>}
                <span className="muted">{e.changeCount} 項目</span>
              </header>
              <ChangeTable entry={e} />
            </section>
          );
        })}
        {list && !shown.length && <div className="muted c" style={{ padding: 20 }}>記録はありません（変更履歴の記録を始める前に保存したレポートは、その後の保存から記録されます）</div>}
      </div>
    </Modal>
  );
}
