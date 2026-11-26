import { useApp } from '../../state/AppContext';
import { useVal } from '../../form/FormContext';
import { Calc, CheckF, DateF, Fld, NumF, RadioF, RefLink, SelectF, TextF } from '../../form/fields';
import { Btn, Note, Row } from '../../components/common/ui';
import * as O from '../../constants/options';
import { amiTimes } from './AmiTab';
import { PreopMeds } from './BasicTab';
import type { Pci, PciLesion } from '../../types/model';
import { lesionSuccessSuggest } from '../../utils/clinical';

/** 成否＋自動判定（術後の残存狭窄 ≤25% かつ TIMI 3 → Success） */
function SuccessCell({ i, l }: { i: number; l: PciLesion }) {
  const app = useApp();
  const sg = lesionSuccessSuggest(l);
  const diff = !!sg && !!l.success && sg !== l.success;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
      <SelectF path={`lesions.${i}.success`} w={80} options={['Success', 'Failure']} />
      {sg && (
        <span className={`suggest ${diff ? 'suggest-diff' : ''}`} title="J-PCI の病変成功：術後の残存狭窄 25% 以下かつ TIMI 3">
          判定 <b>{sg}</b>
          {sg !== l.success && (
            <button type="button" className="get-btn" onClick={() => app.form!.set(`report.pci.lesions.${i}.success`, sg)}>
              適用
            </button>
          )}
        </span>
      )}
    </div>
  );
}

const H = ({ children }: { children: string }) => <div className="jpci-h">{children}</div>;

/** J-PCI タブ scope: report.pci（J-PCI レジストリ登録項目） */
export function JpciTab() {
  const app = useApp();
  const pci = useVal<Pci>('');
  const info = pci.jpci.info;
  const d2b = amiTimes(pci.ami).d2b;
  const docs = app.masters.doctors;

  return (
    <div className="jpci">
      <div className="jpci-left">
        <H>＜患者背景＞</H>
        <div className="cols" style={{ gap: 18 }}>
          <div>
            {O.JPCI_BG_UMU_LEFT.map(([k, l]) => (
              <RadioF key={k} path={`/report.cathRecord.risk.${k}`} label={l} lw={120} options={O.UMU_OPTS} compact />
            ))}
          </div>
          <div>
            <div className="sub-title">24時間以内の</div>
            {O.JPCI_BG_24H.map(([k, l]) => (
              <RadioF key={k} path={`jpci.bg.${k}`} label={l} lw={100} options={O.UMU_OPTS} compact />
            ))}
          </div>
        </div>
        <SelectF path="jpci.bg.symptom1m" label="一ヶ月以内の症状の有無" lw={150} w={160} options={O.SYMPTOMS_1M} />
        <SelectF path="jpci.bg.admitDx" label="今回入院に至った診断名" lw={150} w={160} options={O.JPCI_DX} />
        <Row>
          <TextF path="jpci.bg.other" label="その他" lw={150} w={160} />
          <Calc label="Door to balloon Time" lw={130} value={d2b ?? ''} w={50} unit="min" />
        </Row>
        <Note color="#555" style={{ textAlign: 'right', fontSize: 10 }}>※ST上昇型AMIのみ（AMIタブより自動算出）</Note>
        <Row>
          <RadioF path="jpci.bg.comorbid" label="併発疾患" lw={150} options={[{ value: 'no', label: '無' }, { value: 'unknown', label: '不明' }]} compact />
          <CheckF path="jpci.bg.stentThrombosis" label="ステント血栓症" />
        </Row>
        <div className="right"><span className="ref-legend"><i />参照のみ</span> <RefLink to="cathRecord">既往歴・DM・HT・HD・HL・腎不全・COPD・PAD・Hb・Cr はカテ記録で編集</RefLink></div>
        <div className="cols" style={{ gap: 12 }}>
          <div>
            <RadioF path="/report.cathRecord.risk.DM" label="DM" lw={150} options={O.PM_OPTS} compact />
            <RadioF path="/report.cathRecord.risk.HT" label="HT" lw={150} options={O.PM_OPTS} compact />
            <RadioF path="jpci.bg.smoking" label="喫煙(過去1年以内)" lw={150} options={O.JPCI_SMOKING_OPTS} compact />
            <RadioF path="jpci.bg.dialysis" label="維持透析" lw={150} options={O.PM_OPTS} compact />
            <RadioF path="/report.cathRecord.risk.pad" label="末梢血管障害(AAA/PAD)" lw={150} options={O.PM_OPTS} compact />
          </div>
          <div>
            <RadioF path="/report.cathRecord.risk.HD" label="HD" lw={110} options={O.PM_OPTS} compact />
            <RadioF path="/report.cathRecord.risk.HL" label="HL" lw={110} options={O.PM_OPTS} compact />
            <RadioF path="/report.cathRecord.risk.renal" label="腎不全" lw={110} options={O.PM_OPTS} compact />
            <RadioF path="/report.cathRecord.risk.copd" label="慢性肺疾患(COPD)" lw={110} options={O.PM_OPTS} compact />
            <Row>
              <NumF path="/report.cathRecord.labs.cbc.Hb" label="Hb" lw={110} w={50} title="カテ記録（入院時血算）と共通" />
              <NumF path="/report.cathRecord.labs.admission.Cr" label="Cr" lw={24} w={50} title="カテ記録と共通" />
            </Row>
          </div>
        </div>
        <Row>
          <NumF path="jpci.bg.lesionCount" label="標的病変数" lw={150} w={60} />
          <RadioF path="jpci.bg.lmt" label="左主幹部病変" lw={90} options={O.UM_OPTS} compact />
        </Row>

        <Row style={{ marginTop: 6 }}>
          <H>＜術前検査・投薬＞</H>
          <CheckF path="jpci.bg.aortic" label="大動脈疾患" />
          <TextF path="jpci.bg.aorticText" w={140} />
        </Row>
        <PreopMeds />
        <Row>
          <NumF path="jpci.pre.ffrCt" label="非侵襲的FFR-CT実測値" lw={150} w={50} />
          <CheckF path="jpci.pre.ffr" label="FFR" />
          <NumF path="jpci.pre.ffrValue" label="FFR実測値" lw={70} w={50} />
          <CheckF path="jpci.pre.ri" label="Resting index" />
          <NumF path="jpci.pre.riValue" label="実測値" lw={44} w={50} />
        </Row>
        <div className="legacy-box">
          <span className="small">※旧項目</span>
          <div className="check-grid cg-2">
            {O.ANTICOAG_LEGACY.map(([k, l]) => (
              <CheckF key={k} path={`jpci.pre.legacy.${k}`} label={l} />
            ))}
          </div>
        </div>

        <H>＜術後情報＞</H>
        <Fld label="抗血栓薬(PCI後投薬)" lw={130} className="f-top">
          <div>
            <div className="boxed check-grid cg-4">
              {O.POST_ANTITHROMBOTIC.map(([k, l]) => (
                <CheckF key={k} path={`jpci.post.antithrombotic.${k}`} label={l} />
              ))}
            </div>
            <CheckF path="jpci.post.antithromboticNone" label="抗血栓薬なし" />
          </div>
        </Fld>
        <Fld label="抗脂質薬(PCI後投薬)" lw={130} className="f-top">
          <div>
            <div className="boxed check-grid cg-4">
              {O.POST_LIPID.map(([k, l]) => (
                <CheckF key={k} path={`jpci.post.lipid.${k}`} label={l} />
              ))}
            </div>
            <CheckF path="jpci.post.lipidNone" label="抗脂質薬なし" />
          </div>
        </Fld>
      </div>

      <div className="jpci-right">
        <Row>
          <H>＜PCI基本情報＞</H>
          <Btn small onClick={() => app.toast('J-PCI 登録フォーム（外部）は未設定です', 'err')}>J-PCI登録フォーム</Btn>
        </Row>
        <TextF path="jpci.info.jpciOperator" label="JPCI術者" lw={110} w={160} list={docs} />
        <Row>
          <TextF path="jpci.info.firstOp" label="第一術者" lw={110} w={160} list={docs} />
          <TextF path="jpci.info.firstOpNo" label="第一術者会員番号" lw={110} w={110} />
        </Row>
        <RadioF path="jpci.info.supervisor" label="指導医の有無" lw={110} options={O.UMU_OPTS} compact />
        <Row>
          <TextF path="jpci.info.supervisorName" label="指導医" lw={110} w={160} list={docs} />
          <TextF path="jpci.info.supervisorNo" label="指導医会員番号" lw={110} w={110} />
        </Row>
        <RadioF path="jpci.info.status" label="PCIのステータス" lw={110} options={O.URGENCY_OPTS} compact />
        <div className="right"><RefLink to="cathRecord">透視時間・造影剤はカテ記録で編集</RefLink></div>
        <Row>
          <NumF path="/report.cathRecord.exam.fluoroTime" label="透視時間" lw={110} w={50} unit="分" title="カテ記録と共通" />
          <TextF path="/report.cathRecord.exam.contrast.agent" label="造影剤" lw={50} w={110} list={O.CONTRAST_AGENTS} />
          <NumF path="/report.cathRecord.exam.contrast.volume" w={50} unit="ml" />
          <TextF path="jpci.info.accessSite" label="アクセスサイト" lw={80} w={110} list={['橈骨動脈', '遠位橈骨動脈', '大腿動脈', '上腕動脈']} />
        </Row>

        <div className="sub-title" style={{ marginTop: 4 }}>合併症</div>
        <RadioF path="jpci.info.procComp" label="手技に関連する合併症" lw={150} options={O.UMU_OPTS} compact />
        <div className={`check-grid cg-2 indent ${info.procComp === 'no' ? 'disabled-box' : ''}`}>
          {O.JPCI_COMP.map(([k, l]) => (
            <CheckF key={k} path={`jpci.info.compItems.${k}`} label={l} />
          ))}
          <CheckF path="jpci.info.nonAccessSite" label="(非アクセスサイトの場合)" />
        </div>
        <Row>
          <DateF path="jpci.info.deathDate" label="院内死亡日" lw={110} />
          <TextF path="jpci.info.deathCause" label="死因" lw={40} w={170} />
        </Row>

        <div className="sub-title">PCI施行にあたっての補助循環デバイスの使用</div>
        <Row>
          <RadioF path="jpci.info.mcs" options={O.UM_OPTS} compact />
          {O.MCS_ITEMS.map(([k, l]) => (
            <CheckF key={k} path={`jpci.info.mcsItems.${k}`} label={l} />
          ))}
        </Row>
        <div className="grid2 tight">
          {O.MCS_ITEMS.map(([k, l]) => (
            <RadioF key={k} path={`jpci.info.mcsTiming.${k}`} label={`${l} タイミング`} lw={110} options={O.TIMING_OPTS} compact />
          ))}
        </div>

        <div className="sub-title">PCI施行にあたっての血管内イメージングデバイスの使用</div>
        <Row>
          <RadioF path="jpci.info.imaging" options={O.UM_OPTS} compact />
          {O.IMAGING_ITEMS.map(([k, l]) => (
            <CheckF key={k} path={`jpci.info.imagingItems.${k}`} label={l} />
          ))}
        </Row>

        <H>＜PCI病変情報＞</H>
        <table className="tbl small-tbl">
          <thead>
            <tr><th>Target</th><th>病変性状</th><th>成否</th><th>使用機器</th></tr>
          </thead>
          <tbody>
            {pci.lesions.map((l, i) => (
              <tr key={i}>
                <td>{l.target}</td>
                <td>{[l.type && `Type ${l.type}`, l.deNovoMajor, l.morph.cto === 'yes' && 'CTO', l.morph.bifurcation === 'yes' && '分岐部'].filter(Boolean).join(' / ')}</td>
                <td>
                  <SuccessCell i={i} l={l} />
                </td>
                <td className="ellipsis">{l.device.items.filter((d) => d.name).map((d) => `${d.name} ${d.size}${d.length ? `x${d.length}` : ''}`).join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="muted small">病変性状・使用機器は「病変形態」「Device」タブから自動表示</div>

        <Row style={{ marginTop: 6 }}>
          <H>＜退院時情報＞</H>
          <Note style={{ background: '#ffff3b', color: '#000', padding: '0 4px' }}>※通常は押さないでください</Note>
        </Row>
        <Row>
          <TextF path="jpci.discharge.pciResult" label="PCI結果" lw={110} w={140} list={['成功', '不成功', '部分成功']} />
          <Btn small onClick={() => window.print()}>J-PCI 一括印刷</Btn>
        </Row>
      </div>
    </div>
  );
}
