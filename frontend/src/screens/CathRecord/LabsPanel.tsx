import { useState } from 'react';
import { useApp } from '../../state/AppContext';
import { useVal } from '../../form/FormContext';
import { Calc, DateF, Fld, NumF, RadioF, TextF } from '../../form/fields';
import { Btn, Panel, Tabs } from '../../components/common/ui';
import * as O from '../../constants/options';
import { bmi, bsa, isAbnormal } from '../../utils/calc';
import { joinPath } from '../../utils/path';
import type { CathRecord } from '../../types/model';

/** 1検査値（基準範囲外はピンク表示） */
export function LabF({ base, def, lw = 64 }: { base: string; def: O.LabDef; lw?: number }) {
  const [k, label, unit, lo, hi] = def;
  const path = joinPath(base, k);
  const v = useVal<string>(path);
  const range = lo != null || hi != null ? ` 基準 ${lo ?? ''}〜${hi ?? ''}` : '';
  return <NumF path={path} label={label} lw={lw} w={52} abnormal={isAbnormal(v, lo, hi)} title={`${unit}${range}`} />;
}

export function LabColumn({ base, defs, lw }: { base: string; defs: O.LabDef[]; lw?: number }) {
  return (
    <div className="lab-col">
      {defs.map((d) => (
        <LabF key={d[0]} base={base} def={d} lw={lw} />
      ))}
    </div>
  );
}

/** 危険因子（scope: report.cathRecord.risk） */
function RiskFactors() {
  return (
    <div className="risk-box">
      <div className="risk-grid">
        <RadioF path="risk.DM" label="DM" lw={40} options={O.PM_OPTS} />
        <RadioF path="risk.family" label="家族歴" lw={50} options={O.PM_OPTS} />
        <TextF path="risk.DMtreatment" label="治療" lw={40} w={110} list={['食事療法', '内服', 'インスリン', 'GLP-1RA']} />
        <RadioF path="risk.smoking" label="喫煙" lw={50} options={O.SMOKING_OPTS} />
        <RadioF path="risk.HD" label="HD" lw={40} options={O.PM2_OPTS} />
        <Fld>
          <NumF path="risk.smokingStartAge" w={34} unit="歳〜" />
          <NumF path="risk.smokingPerDay" w={34} unit="本/日" />
          <NumF path="risk.smokingQuitAge" w={34} unit="歳禁煙" />
        </Fld>
        <RadioF path="risk.CAPD" label="CAPD" lw={40} options={O.PM2_OPTS} />
        <RadioF path="risk.eSmoking" label="電子煙草" lw={50} options={O.SMOKING_OPTS} />
        <RadioF path="risk.HT" label="HT" lw={40} options={O.PM_OPTS} />
        <Fld>
          <NumF path="risk.eSmokingStartAge" w={34} unit="歳〜" />
          <NumF path="risk.eSmokingPerDay" w={34} unit="本/日" />
          <NumF path="risk.eSmokingQuitAge" w={34} unit="歳禁煙" />
        </Fld>
        <span />
        <RadioF path="risk.HL" label="HL" lw={50} options={O.PM_OPTS} />
      </div>
      <div className="risk-sub">既往歴・併存症 <small>（全検査で記録。J-PCI タブはここを参照）</small></div>
      <div className="risk-grid risk-grid-hx">
        <RadioF path="risk.priorMI" label="心筋梗塞" lw={64} options={O.UMU_OPTS} />
        <RadioF path="risk.renal" label="腎不全" lw={60} options={O.PM_OPTS} />
        <RadioF path="risk.priorHF" label="心不全" lw={64} options={O.UMU_OPTS} />
        <RadioF path="risk.copd" label="COPD" lw={60} options={O.PM_OPTS} />
        <RadioF path="risk.pciHx" label="PCI歴" lw={64} options={O.UMU_OPTS} />
        <RadioF path="risk.pad" label="AAA/PAD" lw={60} options={O.PM_OPTS} />
        <RadioF path="risk.cabgHx" label="CABG歴" lw={64} options={O.UMU_OPTS} />
      </div>
    </div>
  );
}

/** 検査値・危険因子（scope: report.cathRecord） */
export function LabsPanel() {
  const app = useApp();
  const [tab, setTab] = useState('adm');
  const [sub, setSub] = useState('chem');
  const body = useVal<CathRecord['body']>('body');
  const d = app.draft!;

  const copyPrevious = () => {
    const prev = app.reports
      .filter((r) => r.patientRef === d.patient.id && r.id !== d.report.id && r.header.studyDate <= d.report.header.studyDate)
      .sort((a, b) => b.header.studyDate.localeCompare(a.header.studyDate))[0];
    if (!prev) return app.toast('前回のカテ記録がありません', 'err');
    app.form!.setMany([
      ['report.cathRecord.labs', prev.cathRecord.labs],
      ['report.cathRecord.risk', prev.cathRecord.risk],
      ['report.cathRecord.body', prev.cathRecord.body],
    ]);
    app.toast(`${prev.header.studyDate} のデータをコピーしました（保存で確定）`);
  };

  return (
    <Panel tone="plain" className="labs-panel">
      <Tabs
        active={tab}
        onChange={setTab}
        tabs={[
          { key: 'adm', label: '入院時(カテ時)' },
          { key: 'dis', label: '退院時(カテ時)' },
          { key: 'gas', label: '血ガス/AQT' },
          { key: 'old', label: '旧項目' },
        ]}
      />
      {tab === 'adm' && (
        <>
          <Tabs
            small
            active={sub}
            onChange={setSub}
            tabs={[
              { key: 'chem', label: '検査値・危険因子' },
              { key: 'cbc', label: '入院時血算' },
              { key: 'endo', label: '甲状腺・副腎系/検尿(入院カテ時)' },
            ]}
          />
          {sub === 'chem' && (
            <>
              <div className="lab-grid">
                <LabColumn base="labs.admission" defs={O.LAB_CHEM_1} lw={44} />
                <LabColumn base="labs.admission" defs={O.LAB_CHEM_2} lw={76} />
                <LabColumn base="labs.admission" defs={O.LAB_CHEM_3} lw={62} />
                {/* 身体検査項目（MDA-LDL グループの右）＋ その下に HBs抗原・HCV抗体 */}
                <div className="lab-col lab-col-body">
                  <NumF path="body.bodyTemp" label="体温(カテ日)" lw={70} w={50} unit="℃" />
                  <NumF path="body.height" label="身長" lw={70} w={50} unit="cm" />
                  <NumF path="body.weight" label="体重" lw={70} w={50} unit="kg" />
                  <Calc label="BSA" lw={70} value={bsa(body.height, body.weight)} w={50} unit="m²" />
                  <Calc label="BMI" lw={70} value={bmi(body.height, body.weight)} w={50} />
                  <div className="lab-sep" />
                  <DateF path="labs.hbs.date" label="検査日" lw={70} w={116} />
                  <TextF path="labs.hbs.hbsAg" label="HBs抗原" lw={70} w={50} list={['(-)', '(+)', '(±)']} />
                  <NumF path="labs.hbs.hbsAgC" label="HBs抗原C" lw={70} w={50} />
                  <div className="lab-sep" />
                  <DateF path="labs.hcv.date" label="検査日" lw={70} w={116} />
                  <TextF path="labs.hcv.hcvAb" label="HCV抗体" lw={70} w={50} list={['(-)', '(+)', '(±)']} />
                  <NumF path="labs.hcv.hcvAbC" label="HCV抗体C" lw={70} w={50} />
                </div>
              </div>
              <div className="labs-bottom">
                <div className="labs-btns">
                  <Btn small onClick={copyPrevious}>前回からコピー</Btn>
                  <Btn small onClick={() => app.toast('検査システム連携は未設定です', 'err')}>採血取得</Btn>
                </div>
                <RiskFactors />
              </div>
            </>
          )}
          {sub === 'cbc' && <LabColumn base="labs.cbc" defs={O.LAB_CBC} lw={70} />}
          {sub === 'endo' && <LabColumn base="labs.endocrine" defs={O.LAB_ENDO} lw={90} />}
        </>
      )}
      {tab === 'dis' && (
        <>
          <DateF path="labs.dischargeDate" label="採血日" lw={60} />
          <div className="lab-grid">
            <LabColumn base="labs.discharge" defs={O.LAB_DISCHARGE.slice(0, 7)} lw={50} />
            <LabColumn base="labs.discharge" defs={O.LAB_DISCHARGE.slice(7)} lw={50} />
          </div>
        </>
      )}
      {tab === 'gas' && <LabColumn base="labs.bloodGas" defs={O.LAB_GAS} lw={80} />}
      {tab === 'old' && <LabColumn base="labs.legacy" defs={O.LAB_LEGACY} lw={70} />}
    </Panel>
  );
}
