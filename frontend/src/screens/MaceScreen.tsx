import { useState, type ReactNode } from 'react';
import { useApp } from '../state/AppContext';
import { Scope, useVal } from '../form/FormContext';
import { Calc, CheckF, DateF, RadioF, TextAreaF, TextF } from '../form/fields';
import { Btn, Note, Row, Tabs } from '../components/common/ui';
import { ScreenFrame } from '../components/layout/ScreenFrame';
import { MACE_LEVEL, opts } from '../constants/options';
import { diffDays } from '../utils/date';
import { hasAnyValue } from '../utils/path';
import type { MaceEntry } from '../types/model';

const UM = opts(['yes', '有'], ['no', '無']);

/** PCI後経過日数（PCI施行日からの日数を自動計算） */
function Days({ date }: { date: string }) {
  const pciDate = useVal<string>('pciDate');
  return <Calc label="PCI後経過日数" lw={84} value={diffDays(pciDate, date)} w={44} className="small-calc" />;
}

function EventBox({ path, title, children }: { path: string; title: string; children?: ReactNode }) {
  const ev = useVal<{ checked: boolean; date: string }>(path);
  return (
    <div className={`mace-box ${ev.checked ? 'on' : ''}`}>
      <div className="mace-title">
        <CheckF path={`${path}.checked`} label={<b>{title}</b>} />
      </div>
      <Row gap={4}>
        <DateF path={`${path}.date`} label="日付" lw={30} />
        <Days date={ev.date} />
      </Row>
      {children}
    </div>
  );
}

function MaceTab() {
  const app = useApp();
  const m = useVal<MaceEntry>('');
  return (
    <div className="mace">
      <Row gap={24} align="flex-start">
        <div>
          <TextF path="mace" label="MACE" lw={50} w={50} list={MACE_LEVEL} />
          <Note>f/uカテ施行時もしくは外来通院時に記入</Note>
        </div>
        <Row>
          <DateF path="pciDate" label="PCI行った日付" lw={90} />
          <Btn small onClick={() => app.form!.set('report.mace', app.draft!.report.mace.map((x) => (x.pciDate ? x : { ...x, pciDate: app.draft!.report.header.studyDate })))}>
            施行日を反映
          </Btn>
        </Row>
        <div>
          <div className="small">当院最終受診日</div>
          <Row gap={4}>
            <DateF path="lastVisit" label="日付" lw={30} />
            <Days date={m.lastVisit} />
          </Row>
        </div>
      </Row>

      <div className="mace-frame">
        <Row>
          <CheckF path="negative.checked" label="PCI後MACE(−)確認日" />
          <DateF path="negative.date" label="日付" lw={40} />
          <span>【</span>
          <Days date={m.negative.date} />
          <span>】</span>
        </Row>
      </div>

      <div className="mace-frame">
        <Row>
          <CheckF path="positive.checked" label="PCI後MACE(+)" />
          <DateF path="positive.lastConfirmDate" label="最終転帰確認日" lw={100} />
          <span>【</span>
          <Days date={m.positive.lastConfirmDate} />
          <span>】</span>
        </Row>
        <div className={`mace-grid ${m.positive.checked ? '' : 'disabled-box'}`}>
          <EventBox path="death" title="全死亡">
            <TextF path="death.cause" label="原因" lw={40} w={160} list={['心臓死', '非心臓死', '不明']} />
            <RadioF path="death.st" label="ステント血栓症" lw={100} options={UM} compact />
          </EventBox>
          <EventBox path="acs" title="非致死性ACS">
            <RadioF path="acs.st" label="ステント血栓症" lw={100} options={UM} compact />
            <TextF path="acs.content" label="ACS内容" lw={60} w={160} list={['STEMI', 'NSTEMI', 'UAP']} />
            <RadioF path="acs.st1st" label="ステント血栓症 1回目" lw={130} options={UM} compact />
          </EventBox>
          <div>
            <EventBox path="stroke" title="非致死性脳梗塞" />
            <EventBox path="hf" title="非致死性心不全" />
          </div>
          <EventBox path="bleeding" title="非致死性出血">
            <TextAreaF path="bleeding.site" label="出血部位" lw={60} rows={2} />
          </EventBox>
          <EventBox path="revasc" title="血行再建">
            <TextAreaF path="revasc.site" label="血行再建部位" lw={80} rows={2} />
          </EventBox>
          <EventBox path="other" title="その他・ACS複数回症例">
            <TextAreaF path="other.text" rows={3} />
          </EventBox>
        </div>
      </div>
    </div>
  );
}

/** MACE（MACE 1〜5） */
export function MaceScreen() {
  const [tab, setTab] = useState('0');
  const mace = useApp().draft!.report.mace;
  return (
    <ScreenFrame>
      <Scope path="/report.mace">
        <Tabs active={tab} onChange={setTab} tabs={[0, 1, 2, 3, 4].map((i) => ({ key: String(i), label: `MACE ${i + 1}`, hasData: hasAnyValue(mace[i]) }))} />
        <div className="tab-body">
          <Scope path={tab} key={tab}>
            <MaceTab />
          </Scope>
        </div>
      </Scope>
    </ScreenFrame>
  );
}
