import { Fragment } from 'react';
import { useVal } from '../../form/FormContext';
import { Calc, CheckF, Fld, NumF, RadioF, TextAreaF, TextF, TimeF } from '../../form/fields';
import { procedureMinutes } from '../../utils/clinical';
import { Panel, Row } from '../../components/common/ui';
import * as O from '../../constants/options';

/** 検査情報（scope: report.cathRecord.exam） */
export function ExamInfoPanel() {
  const followUp = useVal<boolean>('purposes.followUp');
  const other1 = useVal<boolean>('purposes.other1');
  const other2 = useVal<boolean>('purposes.other2');
  const cancer = useVal<boolean>('cancer');
  const aortic = useVal<boolean>('aorticDisease');
  const start = useVal<string>('startTime');
  const end = useVal<string>('endTime');
  const mins = procedureMinutes(start, end);

  return (
    <Panel
      title="検査情報"
      right={
        <Row gap={14}>
          <CheckF path="flags.ccuHotline" label="CCUホットライン" />
          <CheckF path="flags.impressiveCase" label="ImpressiveCase" />
        </Row>
      }
    >
      <div className="exam-grid">
        <div>
          <Row gap={10}>
            <RadioF path="urgency" options={O.URGENCY_OPTS} />
            <NumF path="totalCathCount" label="総カテ回数" lw={70} w={40} unit="回" />
          </Row>
          <Fld label="目的" lw={40} className="f-top">
            <div className="boxed">
              <Row gap={10}>
                {O.PURPOSES.map(([k, l]) => (
                  <CheckF key={k} path={`purposes.${k}`} label={l} />
                ))}
              </Row>
              <Row>
                <CheckF path="purposes.followUp" label="Follow-up" />
                <TextF path="followUpReason" label="理由" lw={30} w={150} readOnly={!followUp} className={!followUp ? 'disabled' : ''} />
              </Row>
              <Row>
                <CheckF path="purposes.other1" label="その他1" />
                <TextF path="other1Text" w={78} readOnly={!other1} className={!other1 ? 'disabled' : ''} />
                <CheckF path="purposes.other2" label="その他2" />
                <TextF path="other2Text" w={78} readOnly={!other2} className={!other2 ? 'disabled' : ''} />
              </Row>
            </div>
          </Fld>
          <TextF path="examItems" label="検査項目" lw={84} w={260} list={O.EXAM_ITEMS} placeholder="例: CAG,LVG,PCI" />
          <TextF path="disease" label="疾病" lw={84} w={260} list={O.DISEASES} />
          <TextF path="diagnosis" label="診断" lw={84} w={200} />
          <TextAreaF path="treatmentPolicy" label={<span>治療方針<br /><small>(冠動脈病変)</small></span>} lw={84} rows={2} />
        </div>
        <div>
          <div className="grid2 tight">
            {O.EXAM_FLAGS_LEFT.map(([k, l], i) => (
              <Fragment key={k}>
                <CheckF path={`flags.${k}`} label={l} />
                <CheckF path={`flags.${O.EXAM_FLAGS_RIGHT[i][0]}`} label={O.EXAM_FLAGS_RIGHT[i][1]} />
              </Fragment>
            ))}
          </div>
          <Row>
            <CheckF path="cancer" label="担癌患者" />
            <TextF path="cancerName" w={170} placeholder="癌の名称" readOnly={!cancer} className={!cancer ? 'disabled' : ''} />
          </Row>
          <Row>
            <CheckF path="aorticDisease" label="大動脈疾患" />
            <TextF
              path="aorticDiseaseType"
              w={170}
              placeholder="大動脈疾患分類"
              list={['胸部大動脈瘤', '腹部大動脈瘤', '大動脈解離 Stanford A', '大動脈解離 Stanford B', '大動脈弁狭窄症', 'その他']}
              readOnly={!aortic}
              className={!aortic ? 'disabled' : ''}
            />
          </Row>
          <TextF path="approach" label="アプローチ" lw={70} w={160} list={O.APPROACHES} />
          <Fld label="シース" lw={70}>
            <TextF path="sheath.name" w={130} list={O.SHEATH_NAMES} placeholder="シース" />
            <TextF path="sheath.size" w={40} list={O.SHEATH_SIZES} unit="Fr" align="right" />
          </Fld>
          <Fld label="造影剤" lw={70}>
            <TextF path="contrast.agent" w={130} list={O.CONTRAST_AGENTS} placeholder="造影剤" />
            <NumF path="contrast.volume" w={50} unit="ml" />
          </Fld>
          <Row>
            <NumF path="fluoroTime" label="透視時間" lw={70} w={50} unit="分" />
            <NumF path="totalDose" label="総線量" lw={48} w={60} unit="mGy" />
          </Row>
          <Row>
            <TimeF path="startTime" label="手技開始" lw={70} w={92} />
            <TimeF path="endTime" label="終了" lw={30} w={92} />
            <Calc label="手技時間" lw={56} value={mins == null ? '' : String(mins)} w={40} unit="分" />
          </Row>
        </div>
      </div>
    </Panel>
  );
}
