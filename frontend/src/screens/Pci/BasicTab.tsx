import { useApp } from '../../state/AppContext';
import { useVal } from '../../form/FormContext';
import { Calc, CheckF, Fld, NumF, RadioF, RefLink, SelectF, TextF } from '../../form/fields';
import { Btn, Note, Row } from '../../components/common/ui';
import * as O from '../../constants/options';
import { TARGET_LIST, useLesions } from './LesionGrid';
import { AddRowBtn, DelRowBtn, range, useCount } from '../../form/repeat';
import { LIST_MAX, createGuiding, createText } from '../../model/defaults';
import { amiTimes } from './AmiTab';
import type { Pci } from '../../types/model';

/** 術前検査・投薬（J-PCI と共通データ） scope: report.pci */
export function PreopMeds({ compact }: { compact?: boolean }) {
  const pre = useVal<Pci['jpci']['pre']>('jpci.pre');
  const box = (items: O.KL, base: string, disabled: boolean) => (
    <div className={`boxed check-grid ${compact ? 'cg-3' : 'cg-3'} ${disabled ? 'disabled-box' : ''}`}>
      {items.map(([k, l]) => (
        <CheckF key={k} path={`${base}.${k}`} label={l} />
      ))}
    </div>
  );
  return (
    <div className="preop">
      <div className="sub-title">術前画像・負荷検査の施行</div>
      <Row align="flex-start">
        <RadioF path="jpci.pre.imaging" options={O.UM_OPTS} compact />
        {box(O.PREOP_IMAGING, 'jpci.pre.imagingItems', pre.imaging === 'no')}
      </Row>
      <div className="sub-title">術前抗血小板薬の使用</div>
      <Row align="flex-start">
        <RadioF path="jpci.pre.antiplatelet" options={O.UM_OPTS} compact />
        {box(O.ANTIPLATELET, 'jpci.pre.apItems', pre.antiplatelet === 'no')}
      </Row>
      <div className="sub-title">術前抗凝固薬の使用</div>
      <Row align="flex-start">
        <RadioF path="jpci.pre.anticoag" options={O.UM_OPTS} compact />
        {box(O.ANTICOAG, 'jpci.pre.acItems', pre.anticoag === 'no')}
      </Row>
    </div>
  );
}

/** 基本タブ scope: report.pci */
export function BasicTab() {
  const app = useApp();
  const ami = useVal<Pci['ami']>('ami');
  const t = amiTimes(ami);
  const docs = app.masters.devices;
  const names = (cat: string) => docs.filter((d) => d.category === cat).map((d) => d.name);
  const LESIONS = useLesions();
  const nGuiding = useCount('basic.guiding');
  const nMicro = useCount('basic.micro');
  const nGw = useCount('basic.gw');
  const passPrint = (k: string) => () => {
    app.toast(`連携パス（${k}）を印刷します`);
    setTimeout(() => window.print(), 300);
  };

  return (
    <div className="pci-basic">
      <div className="pb-top">
        <div>
          <NumF path="basic.lesionCount" label="標的病変数" lw={80} w={60} />
          <SelectF path="basic.support" label="サポート" lw={80} w={170} options={O.SUPPORTS} />
          <SelectF path="basic.result" label="PCI結果" lw={80} w={120} options={O.PCI_RESULTS} />
          <TextF path="basic.failureReason" label="不成功理由" lw={80} w={170} />
          <SelectF path="basic.complication" label="合併症" lw={80} w={170} options={['なし', '手技関連合併症あり', '出血性合併症', '血管合併症', 'その他']} />
        </div>
        <div>
          <NumF path="/report.cagLvg.cag.syntax" label="Syntax Score" lw={136} w={60} title="CAG画面と共通" />
          <NumF path="/report.cagLvg.cag.euro" label="Euro Score" lw={136} w={60} />
          <NumF path="/report.cagLvg.cag.japan" label="Japan Score" lw={136} w={60} />
          <div style={{ paddingLeft: 140 }}><RefLink to="cagLvg">スコアはCAGで編集</RefLink></div>
          <div className="sub-title">AMI</div>
          <Row>
            <NumF path="basic.elapsed" label="Elapsed Time" lw={136} w={60} unit="min" />
            <SelectF path="basic.killip" label="Killip" lw={40} w={60} options={['I', 'II', 'III', 'IV']} />
          </Row>
          <Calc label="Door to Balloon Time" lw={136} value={t.d2b ?? ''} w={60} unit="min" />
          <div className="muted small" style={{ paddingLeft: 140 }}>AMIタブの時刻から自動算出</div>
        </div>
        <div>
          <CheckF path="basic.mdct" label="MDCT施行" />
          <br />
          <CheckF path="basic.ri" label="RI施行" />
        </div>
        <div>
          <TextF path="basic.startComp" label="手技開始時合併症" lw={110} w={170} />
          <TextF path="basic.acuteComp" label="急性期合併症" lw={110} w={170} />
          <TextF path="basic.mace30" label="30日MACE" lw={110} w={170} />
          <TextF path="basic.hospComp" label="In Hospital合併症" lw={110} w={170} />
          <Note color="#2255cc" style={{ textAlign: 'right' }}>※枠の色がグレーは検索用です</Note>
        </div>
      </div>

      <div className="pb-mid">
        <div className="pass-btns">
          <Btn onClick={passPrint('DES')}>連携パス印刷<br />(DES)</Btn>
          <Btn onClick={passPrint('BMS')}>連携パス印刷<br />(BMS)</Btn>
          <Btn onClick={passPrint('DCB')}>連携パス印刷<br />(DCB)</Btn>
        </div>
        {/* ガイディングカテーテル・マイクロカテーテル・ガイドワイヤー・術前検査・投薬 を横並び */}
        <div className="boxed device-group">
          <div className="dg-title">ガイディングカテーテル</div>
          {range(nGuiding).map((i) => (
            <Fld key={i}>
              <TextF path={`basic.guiding.${i}.name`} w={150} list={['Launcher EBU3.5', 'Launcher JL4', 'Launcher JR4', 'Heartrail SPB3.5', 'Heartrail IL3.5', 'Hyperion SPB']} />
              <TextF path={`basic.guiding.${i}.size`} w={36} list={O.SHEATH_SIZES} align="right" unit="Fr" />
              <DelRowBtn path="basic.guiding" index={i} create={createGuiding} what="ガイディングカテーテル" />
            </Fld>
          ))}
          <AddRowBtn path="basic.guiding" max={LIST_MAX.guiding} create={createGuiding} />
        </div>
        <div className="boxed device-group">
          <div className="dg-title">マイクロカテーテル</div>
          {range(nMicro).map((i) => (
            <Fld key={i}>
              <TextF path={`basic.micro.${i}`} w={140} list={names('Micro')} />
              <DelRowBtn path="basic.micro" index={i} create={createText} what="マイクロカテーテル" />
            </Fld>
          ))}
          <AddRowBtn path="basic.micro" max={LIST_MAX.micro} create={createText} />
        </div>
        <div className="boxed device-group">
          <div className="dg-title">ガイドワイヤー</div>
          <div className="gw-grid">
            {range(nGw).map((i) => (
              <Fld key={i}>
                <TextF path={`basic.gw.${i}`} w={120} list={names('GW')} />
                <DelRowBtn path="basic.gw" index={i} create={createText} what="ガイドワイヤー" />
              </Fld>
            ))}
          </div>
          <AddRowBtn path="basic.gw" max={LIST_MAX.gw} create={createText} />
        </div>
        <div className="boxed device-group preop-wrap">
          <div className="dg-title">術前検査・投薬 <span className="muted small">（J-PCIタブと共通）</span></div>
          <PreopMeds compact />
        </div>
      </div>
      <TextF path="basic.patientTreatment" label={<b>患者単位治療</b>} lw={110} w={180} list={['PCI', 'PCI+CABG', 'CABG', '薬物療法']} />

      <div className="lesion-summary-wrap">
      <table className="tbl lesion-summary">
        <thead>
          <tr>
            <th>Target</th>
            <th>病変単位治療</th>
            {O.PCI_TECH.map(([k, l]) => (
              <th key={k} className="vt">{l}</th>
            ))}
            <th>Pre</th>
            <th>Post</th>
            <th>TIMI Pre</th>
            <th>Post</th>
            <th>Rentrop</th>
            <th>Comment</th>
            <th>Restudy非表示</th>
          </tr>
        </thead>
        <tbody>
          {LESIONS.map((i) => (
            <tr key={i}>
              <td><TextF path={`lesions.${i}.target`} w={80} list={TARGET_LIST} /></td>
              <td><TextF path={`lesions.${i}.summary.treatment`} w={110} /></td>
              {O.PCI_TECH.map(([k]) => (
                <td key={k} className="c"><CheckF path={`lesions.${i}.summary.tech.${k}`} /></td>
              ))}
              <td><NumF path={`lesions.${i}.summary.pre`} w={50} /></td>
              <td><NumF path={`lesions.${i}.summary.post`} w={50} /></td>
              <td><TextF path={`lesions.${i}.summary.timiPre`} w={40} list={O.TIMI} align="center" /></td>
              <td><TextF path={`lesions.${i}.summary.timiPost`} w={40} list={O.TIMI} align="center" /></td>
              <td><TextF path={`lesions.${i}.summary.rentrop`} w={40} list={O.RENTROP} align="center" /></td>
              <td><TextF path={`lesions.${i}.summary.comment`} w={200} /></td>
              <td className="c"><CheckF path={`lesions.${i}.summary.restudyHidden`} /></td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}
