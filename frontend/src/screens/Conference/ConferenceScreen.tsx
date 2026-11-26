import { useState } from 'react';
import { useApp } from '../../state/AppContext';
import { Scope, useVal } from '../../form/FormContext';
import { Calc, CheckF, DateF, Fld, NumF, RadioF, RefLink, SelectF, TextAreaF, TextF, TripleF } from '../../form/fields';
import { Btn, Panel, Row, Tabs } from '../../components/common/ui';
import { ScreenFrame } from '../../components/layout/ScreenFrame';
import * as O from '../../constants/options';
import { bmi, bsa } from '../../utils/calc';
import { fmtDate } from '../../utils/date';
import { hasAnyValue } from '../../utils/path';
import type { CathReport, Conference, MedRow, Patient } from '../../types/model';

const CR = '/report.cathRecord';

/** 基本・血行動態・危険因子（多くの項目はカテ記録・LVG・患者情報と共通データ） */
function BasicTab() {
  const app = useApp();
  const body = useVal<CathReport['cathRecord']['body']>(`${CR}.body`);
  const patient = useVal<Patient>('/patient');
  const conf = useVal<Conference>('');
  const r = app.draft!.report;

  const copyCag = () => {
    const c = r.cagLvg.cag.comment;
    if (!c) return app.toast('CAGコメントがありません', 'err');
    app.form!.set('report.conference.comment', conf.comment ? `${conf.comment}\n${c}` : c);
  };
  const copyHistory = () => {
    const a = patient.admissions[patient.admissions.length - 1];
    if (!a) return app.toast('病歴総括のデータがありません', 'err');
    const text = `${fmtDate(a.admitDate)}〜${fmtDate(a.dischargeDate)} ${a.diagnosis}（${a.doctor}）\n${a.summary}`;
    app.form!.set('report.conference.onsetCourse', conf.onsetCourse ? `${conf.onsetCourse}\n${text}` : text);
  };
  const markNotPerformed = () => {
    const entries: [string, unknown][] = (['scinti', 'mdct', 'ucg', 'treadmill'] as const)
      .filter((k) => !hasAnyValue({ ...conf[k], prescriptions: undefined }))
      .map((k) => [`report.conference.notPerformed.${k}`, true]);
    if (!entries.length) return app.toast('未入力の検査はありません');
    app.form!.setMany(entries);
    app.toast(`${entries.length}件の検査を「未実施」にしました`);
  };

  return (
    <div className="conf-basic">
      <div className="conf-left">
        <Row align="flex-start">
          <Btn small onClick={() => app.toast('電子カルテ連携は未設定です', 'err')}>取得</Btn>
          <div>
            <NumF path={`${CR}.body.height`} label="身長" lw={40} w={60} unit="cm" />
            <NumF path={`${CR}.body.weight`} label="体重" lw={40} w={60} unit="kg" />
          </div>
          <div>
            <Calc label="BSA" lw={36} value={bsa(body.height, body.weight)} w={60} />
            <Calc label="BMI" lw={36} value={bmi(body.height, body.weight)} w={60} />
          </div>
          <TextF path="wardDoctor" label="病棟主治医" lw={80} w={160} list={app.masters.doctors} />
        </Row>
        <Row align="flex-start" style={{ marginTop: 10 }}>
          <div style={{ flex: 1 }}>
            <TextAreaF path="disease" label="疾病" lw={60} rows={3} />
          </div>
          <div>
            <SelectF path="nyha" label="NYHA" lw={50} w={70} options={O.NYHA} />
            <SelectF path="ccs" label="CCS" lw={50} w={70} options={O.CCS} />
          </div>
        </Row>
        <div className="right">
          <Btn small onClick={copyCag}>CAGコメントをコピー</Btn>
        </div>
        <TextAreaF path="onsetCourse" label={<span>Onset<br />and<br />Course</span>} lw={60} rows={9} />
        <TextAreaF path="comment" label="コメント" lw={60} rows={11} />
      </div>

      <div className="conf-right">
        <div className="right" style={{ marginBottom: 4 }}><span className="ref-legend"><i />参照のみ</span> <RefLink to="cathRecord">危険因子・血行動態・身長体重・予後はカテ記録で編集</RefLink> <RefLink to="cagLvg">LVG値はCAG/LVGで編集</RefLink></div>
        <div className="cols" style={{ gap: 12 }}>
          <div>
            <RadioF path={`${CR}.risk.DM`} label="DM" lw={60} options={O.PM_OPTS} compact />
            <RadioF path={`${CR}.risk.CAPD`} label="CAPD" lw={60} options={O.PM2_OPTS} compact />
            <RadioF path={`${CR}.risk.HD`} label="HD" lw={60} options={O.PM_OPTS} compact />
            <RadioF path={`${CR}.risk.HT`} label="HT" lw={60} options={O.PM_OPTS} compact />
            <RadioF path={`${CR}.risk.HL`} label="HL" lw={60} options={O.PM_OPTS} compact />
            <RadioF path={`${CR}.risk.family`} label="家族歴" lw={60} options={O.PM_OPTS} compact />
            <Row>
              <RadioF path={`${CR}.risk.smoking`} label="喫煙" lw={60} options={O.SMOKING_OPTS} compact />
              <NumF path={`${CR}.risk.smokingPerDay`} w={40} unit="本/日" />
            </Row>
          </div>
          <div>
            <TextF path={`${CR}.risk.DMtreatment`} label="治療" lw={40} w={90} />
          </div>
        </div>
        <div className="cols" style={{ marginTop: 8, gap: 12 }}>
          <div>
            {O.HEMO_TRIPLES.filter(([k]) => k !== 'AoPre').map(([k, l]) => (
              <TripleF key={k} path={`${CR}.hemo.pressures.${k}`} label={l} lw={50} w={44} />
            ))}
            <Fld label="CO(I)" lw={50}>
              <NumF path={`${CR}.hemo.values.CO`} w={60} />
              <span>(</span>
              <NumF path={`${CR}.hemo.values.CI`} w={60} />
              <span>)</span>
            </Fld>
          </div>
          <div>
            {(
              [
                ['LVEDV', 'LVEDVI', 'LVEDV(I)'],
                ['LVESV', 'LVESVI', 'LVESV(I)'],
                ['LVSV', 'LVSVI', 'LVSV(I)'],
              ] as const
            ).map(([a, b, l]) => (
              <Fld key={a} label={l} lw={70}>
                <NumF path={`/report.cagLvg.lvg.values.${a}`} w={56} />
                <NumF path={`/report.cagLvg.lvg.values.${b}`} w={56} />
              </Fld>
            ))}
            <NumF path="/report.cagLvg.lvg.values.EF" label="LVEF" lw={70} w={56} />
            <div className="muted small">LVG・血行動態は参照のみ</div>
          </div>
        </div>
        <div className="cols" style={{ marginTop: 8, alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            <Row>
              <DateF path={`${CR}.prognosis.deathDate`} label="死亡日" lw={70} />
              <DateF path={`${CR}.prognosis.confirmDate`} label="確認日" lw={50} />
            </Row>
            <TextF path={`${CR}.prognosis.confirmer`} label="確認者" lw={70} w={120} list={app.masters.doctors} />
            <TextAreaF path={`${CR}.prognosis.comment`} label="予後コメント" lw={70} rows={2} />
          </div>
          <div className="col-btns">
            <Btn onClick={markNotPerformed}>検査未実施</Btn>
            <Btn onClick={copyHistory}>病歴総括から<br />コピー</Btn>
          </div>
        </div>
        <div className="history-box">
          <div>
            <b>病歴総括</b> <span className="small">「コピー」ボタンを押すと病歴総括のデータをコピーします／「入院日」をクリックすると患者情報入力（病歴総括）に移動します</span>
          </div>
          <table className="tbl small-tbl">
            <thead>
              <tr><th>入院日</th><th>退院日</th><th>入院主治医</th><th>診断</th></tr>
            </thead>
            <tbody>
              {patient.admissions.map((a, i) => (
                <tr key={i}>
                  <td><button type="button" className="link-btn" onClick={() => app.goto('patient')}>{fmtDate(a.admitDate)}</button></td>
                  <td>{fmtDate(a.dischargeDate)}</td>
                  <td>{a.doctor}</td>
                  <td>{a.diagnosis}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function NotPerformed({ k }: { k: string }) {
  return (
    <div className="right">
      <CheckF path={`notPerformed.${k}`} label="検査未実施" />
    </div>
  );
}

function MedTable({ path, rows }: { path: string; rows: MedRow[] }) {
  return (
    <table className="tbl grid-tbl">
      <thead>
        <tr><th>#</th><th>薬剤名</th><th>用量</th><th>用法</th><th>日数</th></tr>
      </thead>
      <tbody>
        {rows.map((_, i) => (
          <tr key={i}>
            <td className="c">{i + 1}</td>
            <td><TextF path={`${path}.${i}.drug`} w={220} list={['アスピリン100mg', 'プラスグレル3.75mg', 'クロピドグレル75mg', 'ロスバスタチン5mg', 'アトルバスタチン10mg', 'エゼチミブ10mg', 'ビソプロロール2.5mg', 'エナラプリル5mg', 'ボノプラザン10mg', 'エドキサバン60mg']} /></td>
            <td><TextF path={`${path}.${i}.dose`} w={80} /></td>
            <td><TextF path={`${path}.${i}.usage`} w={160} list={O.DRUG_USAGE} /></td>
            <td><NumF path={`${path}.${i}.days`} w={50} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function PrevPciTab() {
  const app = useApp();
  const d = app.draft!;
  const conf = useVal<Conference>('');
  const past = app.reports
    .filter((r) => r.patientRef === d.patient.id && r.id !== d.report.id && r.pci.lesions.some((l) => l.target))
    .sort((a, b) => b.header.studyDate.localeCompare(a.header.studyDate));
  return (
    <>
      <Panel title="当院PCI歴（自動）" tone="plain">
        <table className="tbl small-tbl">
          <thead><tr><th>施行日</th><th>病変</th><th>デバイス</th><th>結果</th></tr></thead>
          <tbody>
            {past.length === 0 && <tr><td colSpan={4} className="muted">なし</td></tr>}
            {past.flatMap((r) =>
              r.pci.lesions.filter((l) => l.target).map((l, i) => (
                <tr key={r.id + i}>
                  <td>{fmtDate(r.header.studyDate)}</td>
                  <td>{l.targetSub} {l.target}</td>
                  <td>{l.device.items.filter((x) => x.name).map((x) => `${x.name} ${x.size}${x.length ? `x${x.length}` : ''}`).join(', ')}</td>
                  <td>{l.summary.pre && `${l.summary.pre}% → ${l.summary.post}%`}</td>
                </tr>
              )),
            )}
          </tbody>
        </table>
      </Panel>
      <Panel title="他院PCI歴（手入力）" tone="plain">
        <table className="tbl grid-tbl">
          <thead><tr><th>施行日</th><th>部位</th><th>デバイス</th><th>備考</th></tr></thead>
          <tbody>
            {conf.prevPci.map((_, i) => (
              <tr key={i}>
                <td><DateF path={`prevPci.${i}.date`} /></td>
                <td><TextF path={`prevPci.${i}.site`} w={100} /></td>
                <td><TextF path={`prevPci.${i}.device`} w={200} /></td>
                <td><TextF path={`prevPci.${i}.note`} w={300} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </>
  );
}

/** カンファレンス */
export function ConferenceScreen() {
  const app = useApp();
  const [tab, setTab] = useState('basic');
  const conf = app.draft!.report.conference;
  const has: Record<string, boolean> = {
    basic: !!(conf.disease || conf.onsetCourse || conf.comment),
    prevPci: hasAnyValue(conf.prevPci),
    scinti: hasAnyValue(conf.scinti) || conf.notPerformed.scinti,
    mdct: hasAnyValue(conf.mdct) || conf.notPerformed.mdct,
    ucg: hasAnyValue(conf.ucg) || conf.notPerformed.ucg,
    treadmill: hasAnyValue(conf.treadmill) || conf.notPerformed.treadmill,
    clinical: hasAnyValue(conf.clinical),
    history: hasAnyValue(conf.history),
    dischargeRx: hasAnyValue(conf.dischargeRx),
  };

  return (
    <ScreenFrame
      headerExtra={
        <>
          <CheckF path="/report.header.summary" label="サマリー" />
          <CheckF path="/report.header.submitted" label="提出" />
        </>
      }
    >
      <Row style={{ marginBottom: 4 }}>
        <Btn small onClick={() => app.goto('images')}>心電図 表示</Btn>
        <Btn small onClick={() => app.goto('images')}>X-P 表示</Btn>
        <Btn small onClick={() => window.print()}>🖨 カンファレンスシート</Btn>
        <Btn small onClick={() => window.print()}>🖨 入院サマリー</Btn>
      </Row>
      <Scope path="/report.conference">
        <Tabs active={tab} onChange={setTab} tabs={O.CONF_TABS.map(([k, l]) => ({ key: k, label: l, hasData: has[k] }))} />
        <div className="tab-body">
          {tab === 'basic' && <BasicTab />}
          {tab === 'prevPci' && <PrevPciTab />}
          {tab === 'scinti' && (
            <Scope path="scinti">
              <Scope path="/report.conference"><NotPerformed k="scinti" /></Scope>
              <div className="grid3">
                <DateF path="date" label="検査日" lw={80} />
                <SelectF path="type" label="種類" lw={80} w={120} options={O.SCINTI_TYPES} />
                <NumF path="ef" label="EF" lw={80} w={50} unit="%" />
                <TextF path="ischemia" label="虚血部位" lw={80} w={160} />
                <TextF path="infarct" label="梗塞部位" lw={80} w={160} />
                <span />
                <NumF path="sss" label="SSS" lw={80} w={50} />
                <NumF path="srs" label="SRS" lw={80} w={50} />
                <NumF path="sds" label="SDS" lw={80} w={50} />
              </div>
              <TextAreaF path="findings" label="所見" lw={80} rows={5} />
            </Scope>
          )}
          {tab === 'mdct' && (
            <Scope path="mdct">
              <Scope path="/report.conference"><NotPerformed k="mdct" /></Scope>
              <Row>
                <DateF path="date" label="検査日" lw={80} />
                <NumF path="calciumScore" label="石灰化スコア" lw={90} w={70} unit="AU" />
                <SelectF path="cadRads" label="CAD-RADS" lw={80} w={70} options={O.CAD_RADS} />
              </Row>
              <TextAreaF path="findings" label="所見" lw={80} rows={8} />
            </Scope>
          )}
          {tab === 'ucg' && (
            <Scope path="ucg">
              <Scope path="/report.conference"><NotPerformed k="ucg" /></Scope>
              <div className="grid4">
                <DateF path="date" label="検査日" lw={60} />
                <NumF path="LVDd" label="LVDd" lw={60} w={50} unit="mm" />
                <NumF path="LVDs" label="LVDs" lw={60} w={50} unit="mm" />
                <NumF path="EF" label="EF" lw={60} w={50} unit="%" />
                <NumF path="IVS" label="IVS" lw={60} w={50} unit="mm" />
                <NumF path="PW" label="PW" lw={60} w={50} unit="mm" />
                <NumF path="LAD" label="LAD" lw={60} w={50} unit="mm" />
                <NumF path="EA" label="E/A" lw={60} w={50} />
                <NumF path="Ee" label="E/e'" lw={60} w={50} />
                <NumF path="TRPG" label="TRPG" lw={60} w={50} unit="mmHg" />
              </div>
              <TextF path="wallMotion" label="壁運動" lw={60} w={400} />
              <TextAreaF path="valve" label="弁膜症" lw={60} rows={3} />
            </Scope>
          )}
          {tab === 'treadmill' && (
            <Scope path="treadmill">
              <Scope path="/report.conference"><NotPerformed k="treadmill" /></Scope>
              <div className="grid3">
                <DateF path="date" label="検査日" lw={80} />
                <SelectF path="protocol" label="プロトコル" lw={80} w={140} options={O.TREADMILL_PROTOCOLS} />
                <NumF path="mets" label="METs" lw={80} w={50} />
                <NumF path="maxHr" label="最大HR" lw={80} w={50} unit="/min" />
                <SelectF path="result" label="判定" lw={80} w={100} options={O.TREADMILL_RESULTS} />
                <TextF path="stChange" label="ST変化" lw={80} w={140} />
              </div>
              <TextAreaF path="findings" label="所見" lw={80} rows={3} />
              <div className="sub-title">処方（入院時）</div>
              <MedTable path="prescriptions" rows={conf.treadmill.prescriptions} />
            </Scope>
          )}
          {tab === 'clinical' && (
            <>
              <TextAreaF path="clinical.diagnoses" label="臨床診断" lw={80} rows={6} />
              <div className="sub-title">感染症（患者情報・カテ記録と共通）　<span className="ref-legend"><i />参照のみ</span> <RefLink to="patient" /> <RefLink to="cathRecord" /></div>
              <div className="grid3">
                <RadioF path="/patient.infection.hbs" label="HBs抗原" lw={80} options={O.PM_OPTS} compact />
                <RadioF path="/patient.infection.hcv" label="HCV抗体" lw={80} options={O.PM_OPTS} compact />
                <RadioF path="/patient.infection.hiv" label="HIV" lw={80} options={O.PM_OPTS} compact />
                <RadioF path="/patient.infection.syphilis" label="梅毒" lw={80} options={O.PM_OPTS} compact />
                <RadioF path="/patient.infection.mrsa" label="MRSA" lw={80} options={O.PM_OPTS} compact />
              </div>
              <Row>
                <TextF path={`${CR}.labs.hbs.hbsAg`} label="HBs抗原(定性)" lw={100} w={60} />
                <NumF path={`${CR}.labs.hbs.hbsAgC`} label="HBs抗原C" lw={70} w={60} />
                <TextF path={`${CR}.labs.hcv.hcvAb`} label="HCV抗体(定性)" lw={100} w={60} />
                <NumF path={`${CR}.labs.hcv.hcvAbC`} label="HCV抗体C" lw={70} w={60} />
              </Row>
              <TextAreaF path="clinical.infectionNote" label="備考" lw={80} rows={2} />
            </>
          )}
          {tab === 'history' && (
            <>
              <TextAreaF path="/patient.pastHistory" label="既往歴" lw={60} rows={5} />
              <div className="muted small" style={{ marginLeft: 66 }}>※既往歴は患者情報と共通（参照のみ） <RefLink to="patient" /></div>
              <TextAreaF path="history.course" label="経過" lw={60} rows={10} />
            </>
          )}
          {tab === 'dischargeRx' && <MedTable path="dischargeRx" rows={conf.dischargeRx} />}
        </div>
      </Scope>
    </ScreenFrame>
  );
}
