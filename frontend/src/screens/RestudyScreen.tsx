import { useApp } from '../state/AppContext';
import { Scope } from '../form/FormContext';
import { DateF, NumF, RadioF, TextAreaF, TextF } from '../form/fields';
import { Btn, Panel, Row } from '../components/common/ui';
import { ScreenFrame } from '../components/layout/ScreenFrame';
import { YN_OPTS } from '../constants/options';
import { fmtDate } from '../utils/date';

/** Restudy（フォローアップ造影：前回PCI病変の再狭窄評価。参考画面なしのため推測） */
export function RestudyScreen() {
  const app = useApp();
  const d = app.draft!;
  const prevPci = app.reports
    .filter((r) => r.patientRef === d.patient.id && r.id !== d.report.id && r.header.studyDate < d.report.header.studyDate && r.pci.lesions.some((l) => l.target))
    .sort((a, b) => b.header.studyDate.localeCompare(a.header.studyDate))[0];

  const importPrev = () => {
    if (!prevPci) return app.toast('前回のPCIレコードがありません', 'err');
    const lesions = prevPci.pci.lesions
      .filter((l) => l.target && !l.summary.restudyHidden)
      .slice(0, 5)
      .map((l) => ({ segment: `${l.targetSub} ${l.target}`.trim(), prevPct: l.post.pct || l.summary.post, currPct: '', lateLoss: '', restenosis: '' as const, tlr: '' as const, comment: '' }));
    while (lesions.length < 5) lesions.push({ segment: '', prevPct: '', currPct: '', lateLoss: '', restenosis: '', tlr: '', comment: '' });
    app.form!.setMany([
      ['report.restudy.lesions', lesions],
      ['report.restudy.interval', String(Math.round((+new Date(d.report.header.studyDate) - +new Date(prevPci.header.studyDate)) / 86400000 / 30.4))],
    ]);
  };

  return (
    <ScreenFrame>
      <Scope path="/report.restudy">
        <Panel
          title="Restudy（フォローアップ造影）"
          right={
            <Btn small onClick={importPrev}>
              前回PCI病変を取込{prevPci ? `（${fmtDate(prevPci.header.studyDate)}）` : ''}
            </Btn>
          }
        >
          <Row>
            <DateF path="date" label="Restudy日" lw={70} />
            <NumF path="interval" label="前回PCIからの期間" lw={120} w={50} unit="ヶ月" />
          </Row>
          <table className="tbl grid-tbl" style={{ marginTop: 6 }}>
            <thead>
              <tr>
                <th>病変</th>
                <th>前回Post(%)</th>
                <th>今回(%)</th>
                <th>Late loss(mm)</th>
                <th>再狭窄</th>
                <th>TLR</th>
                <th>コメント</th>
              </tr>
            </thead>
            <tbody>
              {[0, 1, 2, 3, 4].map((i) => (
                <tr key={i}>
                  <td><TextF path={`lesions.${i}.segment`} w={120} /></td>
                  <td><NumF path={`lesions.${i}.prevPct`} w={60} /></td>
                  <td><NumF path={`lesions.${i}.currPct`} w={60} /></td>
                  <td><NumF path={`lesions.${i}.lateLoss`} w={60} /></td>
                  <td><RadioF path={`lesions.${i}.restenosis`} options={YN_OPTS} compact /></td>
                  <td><RadioF path={`lesions.${i}.tlr`} options={YN_OPTS} compact /></td>
                  <td><TextF path={`lesions.${i}.comment`} w={260} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          <TextAreaF path="comment" label="コメント" lw={70} rows={3} />
        </Panel>
      </Scope>
    </ScreenFrame>
  );
}
