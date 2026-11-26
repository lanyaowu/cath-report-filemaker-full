import { useApp } from '../../state/AppContext';
import { Scope } from '../../form/FormContext';
import { CheckF, TextAreaF, TextF } from '../../form/fields';
import { Btn, Panel } from '../../components/common/ui';
import { ScreenFrame } from '../../components/layout/ScreenFrame';
import { ExamInfoPanel } from './ExamInfoPanel';
import { ComplicationsPanel, DoctorsPanel, HemodynamicsPanel, OtherPanel, PrognosisPanel } from './SidePanels';
import { LabsPanel } from './LabsPanel';
import { PastCommentCopy } from '../CagLvg/PastCopy';

/** カテ記録 */
export function CathRecordScreen() {
  const app = useApp();
  return (
    <ScreenFrame
      headerExtra={
        <>
          <CheckF path="/report.header.secretaryChecked" label="秘書入力確認チェック" />
          <TextF path="/report.header.accessionNo" label="AccessionNo." lw={90} w={150} />
        </>
      }
    >
      <Scope path="/report.cathRecord">
        <div className="cath-layout">
          <div className="cath-left">
            <Scope path="exam">
              <ExamInfoPanel />
            </Scope>
            <div className="cols">
              <Scope path="doctors">
                <DoctorsPanel />
              </Scope>
              <Scope path="hemo">
                <HemodynamicsPanel />
              </Scope>
            </div>
            <div className="cols">
              <Scope path="prognosis">
                <PrognosisPanel />
              </Scope>
              <Scope path="other">
                <OtherPanel />
              </Scope>
            </div>
            <Scope path="complications">
              <ComplicationsPanel />
            </Scope>
          </div>
          <div className="cath-right">
            <LabsPanel />
            <Panel title="PCIサマリー/連絡事項" right={<Btn small onClick={() => app.goto('pci')}>PCIへ</Btn>}>
              <TextAreaF path="pciSummary" rows={3} />
            </Panel>
            <Panel title="今後の方針">
              <TextAreaF path="futurePlan" rows={2} />
            </Panel>
            <Panel title="Comment" right={<PastCommentCopy target="report.cathRecord.comment" />}>
              <TextAreaF path="comment" rows={4} />
            </Panel>
          </div>
        </div>
      </Scope>
    </ScreenFrame>
  );
}
