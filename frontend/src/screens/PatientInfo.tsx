import { useApp } from '../state/AppContext';
import { Scope, useVal } from '../form/FormContext';
import { CheckF, DateF, RadioF, SelectF, TextAreaF, TextF } from '../form/fields';
import { Btn, Panel, Row } from '../components/common/ui';
import { ScreenFrame } from '../components/layout/ScreenFrame';
import { PM_OPTS, SEX_OPTS } from '../constants/options';
import { ageAt, fmtDate } from '../utils/date';
import type { Admission } from '../types/model';

const LW = 96;

/** 患者情報入力（参考画面なし：診療録・J-PCI 患者背景から推測した項目） */
export function PatientInfo() {
  const app = useApp();
  const d = app.draft!;
  const admissions = useVal<Admission[]>('/patient.admissions');
  const reports = app.reports.filter((r) => r.patientRef === d.patient.id);

  return (
    <ScreenFrame>
      <Scope path="/patient">
        <div className="cols">
          <div className="col" style={{ flex: '1 1 460px' }}>
            <Panel title="基本情報">
              <div className="grid2">
                <TextF path="patientId" label="患者ID" lw={LW} w={140} required />
                <TextF path="name" label="氏名" lw={LW} w={180} required />
                <TextF path="kana" label="フリガナ" lw={LW} w={180} />
                <RadioF path="sex" label="性別" lw={LW} options={SEX_OPTS} />
                <DateF path="birthDate" label="生年月日" lw={LW} />
                <div className="f">
                  <label className="lbl" style={{ width: LW }}>年齢</label>
                  <span className="calc" style={{ width: 40 }}>{ageAt(d.patient.birthDate)}</span>
                </div>
                <SelectF path="bloodType" label="血液型" lw={LW} options={['A', 'B', 'O', 'AB']} w={60} />
                <SelectF path="rh" label="Rh" lw={LW} options={['+', '-']} w={60} />
                <TextF path="zip" label="郵便番号" lw={LW} w={90} />
                <TextF path="address" label="住所" lw={LW} w={260} />
                <TextF path="phone" label="電話" lw={LW} w={130} />
                <TextF path="mobile" label="携帯" lw={LW} w={130} />
              </div>
            </Panel>
            <Panel title="緊急連絡先・保険">
              <div className="grid2">
                <TextF path="emergency.name" label="連絡先氏名" lw={LW} w={140} />
                <TextF path="emergency.relation" label="続柄" lw={LW} w={80} list={['妻', '夫', '長男', '長女', '次男', '次女', 'その他']} />
                <TextF path="emergency.phone" label="連絡先電話" lw={LW} w={130} />
                <SelectF path="insurance.type" label="保険種別" lw={LW} options={['社保', '国保', '後期高齢', '生保', '自費']} w={100} />
                <TextF path="insurance.number" label="保険者番号" lw={LW} w={130} />
              </div>
            </Panel>
            <Panel title="主治医・紹介元">
              <div className="grid2">
                <TextF path="primaryDoctor" label="主治医" lw={LW} w={130} list={app.masters.doctors} />
                <TextF path="ward" label="病棟" lw={LW} w={80} list={['CCU', 'ICU', '5東', '5西', '6東', '6西']} />
                <TextF path="referral.hospital" label="紹介病院" lw={LW} w={180} list={app.masters.hospitals} />
                <TextF path="referral.doctor" label="紹介医" lw={LW} w={130} />
                <CheckF path="dnar" label="DNAR" />
              </div>
            </Panel>
          </div>

          <div className="col" style={{ flex: '1 1 420px' }}>
            <Panel title="アレルギー">
              <Row>
                <CheckF path="allergy.contrast" label="造影剤" />
                <TextF path="allergy.contrastDetail" w={200} placeholder="症状・時期" />
              </Row>
              <Row>
                <CheckF path="allergy.drug" label="薬剤" />
                <TextF path="allergy.drugDetail" w={200} placeholder="薬剤名" />
              </Row>
              <Row>
                <CheckF path="allergy.iodine" label="ヨード" />
                <CheckF path="allergy.latex" label="ラテックス" />
                <TextF path="allergy.food" label="食物" lw={40} w={150} />
              </Row>
            </Panel>
            <Panel title="感染症">
              <div className="grid2">
                <RadioF path="infection.hbs" label="HBs抗原" lw={70} options={PM_OPTS} />
                <RadioF path="infection.hcv" label="HCV抗体" lw={70} options={PM_OPTS} />
                <RadioF path="infection.hiv" label="HIV" lw={70} options={PM_OPTS} />
                <RadioF path="infection.syphilis" label="梅毒" lw={70} options={PM_OPTS} />
                <RadioF path="infection.mrsa" label="MRSA" lw={70} options={PM_OPTS} />
              </div>
            </Panel>
            <Panel title="既往歴・家族歴・内服">
              <TextAreaF path="pastHistory" label="既往歴" lw={70} rows={2} />
              <TextAreaF path="familyHistory" label="家族歴" lw={70} rows={2} />
              <TextAreaF path="medicationNote" label="常用薬" lw={70} rows={2} />
              <TextAreaF path="notes" label="備考" lw={70} rows={2} />
            </Panel>
          </div>
        </div>

        <Panel
          title="病歴総括（入院歴）"
          right={
            <Btn small onClick={() => app.form!.set('patient.admissions', [...admissions, { admitDate: '', dischargeDate: '', doctor: '', diagnosis: '', summary: '' }])}>
              ＋ 追加
            </Btn>
          }
        >
          <table className="tbl grid-tbl">
            <thead>
              <tr><th>入院日</th><th>退院日</th><th>入院主治医</th><th>診断</th><th>要約</th><th /></tr>
            </thead>
            <tbody>
              {admissions.map((_, i) => (
                <tr key={i}>
                  <td><DateF path={`admissions.${i}.admitDate`} /></td>
                  <td><DateF path={`admissions.${i}.dischargeDate`} /></td>
                  <td><TextF path={`admissions.${i}.doctor`} w={110} list={app.masters.doctors} /></td>
                  <td><TextF path={`admissions.${i}.diagnosis`} w={150} /></td>
                  <td><TextF path={`admissions.${i}.summary`} w={320} /></td>
                  <td>
                    <Btn small onClick={() => app.form!.set('patient.admissions', admissions.filter((__, j) => j !== i))}>削除</Btn>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      </Scope>

      <Panel title="この患者のカテレポート">
        <table className="tbl">
          <thead>
            <tr><th>施行日</th><th>Cine No</th><th>検査項目</th><th>疾病</th><th>ステータス</th><th /></tr>
          </thead>
          <tbody>
            {reports.map((r) => (
              <tr key={r.id} className={r.id === d.report.id ? 'current' : ''}>
                <td>{fmtDate(r.header.studyDate)}</td>
                <td>{r.header.cineNo}</td>
                <td>{r.cathRecord.exam.examItems}</td>
                <td>{r.cathRecord.exam.disease}</td>
                <td>{r.status}</td>
                <td>{r.id !== d.report.id && <Btn small onClick={() => app.openReport(r.id, 'cathRecord')}>開く</Btn>}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ marginTop: 4 }}>
          <Btn small kind="primary" onClick={() => app.newReport(d.patient)} disabled={app.isNew}>
            この患者で新規カテレポート作成
          </Btn>
        </div>
      </Panel>
    </ScreenFrame>
  );
}
