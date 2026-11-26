import { useState, type ReactNode } from 'react';
import { useApp } from '../../state/AppContext';
import { Scope, useResolve, useVal } from '../../form/FormContext';
import { CheckF, NumF, TextF } from '../../form/fields';
import { Btn, Row, Tabs } from '../../components/common/ui';
import { ScreenFrame } from '../../components/layout/ScreenFrame';
import * as O from '../../constants/options';
import { hasAnyValue } from '../../utils/path';
import { ivusDerived, num } from '../../utils/calc';
import { AddRowBtn, DelRowBtn, range, useCount } from '../../form/repeat';
import { LIST_MAX, createIvusLesion, createPressureCol } from '../../model/defaults';

/** Pressure Wire の病変 N と IVUS の Lesion N は同じ病変（数・病変名を共有）。scope: report.pressureIvus */
const IVUS_LINK = [{ path: 'lesions', create: createIvusLesion }];
const PW_LINK = [{ path: '/report.pressureIvus.pressure', create: createPressureCol }];
const DEL_NOTE = '（Pressure Wire の列と Lesion タブの両方）';
import type { IvusLesion, PressureCol } from '../../types/model';


/** Pressure Wire タブ scope: report.pressureIvus */
function PressureWireTab() {
  const cols = useVal<PressureCol[]>('pressure');
  const COLS = range(useCount('pressure'));
  /** 列は入力した病変の数だけ（表の幅は列数に合わせて伸びる） */
  const pad = null;
  const ffrFlag = (v: string) => {
    const n = num(v);
    return n != null && n <= 0.8;
  };
  const nhprFlag = (v: string) => {
    const n = num(v);
    return n != null && n <= 0.89;
  };
  const head = (label: string, render: (i: number) => ReactNode, sep = false) => (
    <tr className={sep ? 'pw-sep' : ''}>
      <th className="pw-head">{label}</th>
      {COLS.map((i) => (
        <td key={i}>{render(i)}</td>
      ))}
      {pad}
    </tr>
  );
  return (
    <table className="pw-tbl">
      <tbody>
        <tr className="pw-ctl">
          <th className="pw-head">
            <AddRowBtn path="pressure" max={LIST_MAX.pressure} create={createPressureCol} label="病変を追加" linked={IVUS_LINK} />
          </th>
          {COLS.map((i) => (
            <td key={i} className="pw-ctl-cell">
              <span className="muted small">病変{i + 1}</span>
              <DelRowBtn path="pressure" index={i} create={createPressureCol} what="病変" linked={IVUS_LINK} note={DEL_NOTE} />
            </td>
          ))}
          {pad}
        </tr>
        <tr className="pw-sep">
          <th className="pw-head">
            <i>病変</i>
            <br />
            <i>(診断のみ,pre PCI,post PCI)</i>
          </th>
          {COLS.map((i) => (
            <td key={i}>
              <TextF path={`pressure.${i}.lesion`} w="100%" list={O.CAG_SEGMENTS.map((s) => s.key)} placeholder="病変" />
              <TextF path={`pressure.${i}.phase`} w="100%" list={O.PRESSURE_PHASE} placeholder="診断のみ / pre PCI / post PCI" />
            </td>
          ))}
          {pad}
        </tr>
        {head('薬剤', (i) => <TextF path={`pressure.${i}.drug`} w="100%" list={O.HYPEREMIC_DRUGS} />, true)}
        {head('Dominancy', (i) => <TextF path={`pressure.${i}.dominancy`} w="100%" list={O.DOMINANCY} />, true)}
        <tr className="pw-sep">
          <th className="pw-head"><i>prior MI(+,-)</i><br /><i>prior MI site</i></th>
          {COLS.map((i) => (
            <td key={i}>
              <TextF path={`pressure.${i}.priorMI`} w="100%" list={['+', '-']} />
              <TextF path={`pressure.${i}.priorMISite`} w="100%" />
            </td>
          ))}
          {pad}
        </tr>
        <tr className="pw-sep">
          <th className="pw-head"><i>Stent(+,-)</i><br /><i>Stent Lesion</i></th>
          {COLS.map((i) => (
            <td key={i}>
              <TextF path={`pressure.${i}.stent`} w="100%" list={['+', '-']} />
              <TextF path={`pressure.${i}.stentLesion`} w="100%" />
            </td>
          ))}
          {pad}
        </tr>
        <tr>
          <th className="pw-head center"><i>Pressure</i></th>
          {COLS.map((i) => <td key={i} />)}
          {pad}
        </tr>
        {O.PRESSURE_METRICS.map(([k, l]) => (
          <tr key={k}>
            <th className="pw-sub">{l}</th>
            {COLS.map((i) => {
              const v = cols[i].metrics[k];
              const abn = k === 'FFR' || k === 'ffrAngio' ? ffrFlag(v) : ['iFR', 'RFR', 'DFR', 'dPR', 'baselinePdPa'].includes(k) ? nhprFlag(v) : false;
              return (
                <td key={i}>
                  <NumF path={`pressure.${i}.metrics.${k}`} w="100%" abnormal={abn} />
                </td>
              );
            })}
            {pad}
          </tr>
        ))}
        <tr className="pw-sep-top">
          <th className="pw-sub">QCA</th>
          {COLS.map((i) => <td key={i} />)}
          {pad}
        </tr>
        {O.QCA_METRICS.map(([k, l]) => (
          <tr key={k}>
            <th className="pw-sub">{l}</th>
            {COLS.map((i) => (
              <td key={i}>
                <NumF path={`pressure.${i}.qca.${k}`} w="100%" />
              </td>
            ))}
            {pad}
          </tr>
        ))}
        <tr>
          <td colSpan={COLS.length + 1} className="muted small">
            ピンク：虚血陽性の目安（FFR≦0.80、iFR/RFR/DFR/dPR/Pd/Pa≦0.89）。QCA は PCI「病変形態」タブの「取得」で参照されます。
          </td>
        </tr>
      </tbody>
    </table>
  );
}

/** IVUS Lesion タブ scope: report.pressureIvus.lesions.N（対象部位は Pressure Wire の病変名を共有） */
function IvusLesionTab({ index }: { index: number }) {
  const app = useApp();
  const les = useVal<IvusLesion>('');
  const sitePath = `/report.pressureIvus.pressure.${index}.lesion`;
  const base = useVal<string>(sitePath);
  const resolve = useResolve();
  const calc = () => {
    const entries: [string, unknown][] = [];
    const prefix = resolve('');
    for (const phase of ['pre', 'post'] as const) {
      for (const [pos] of O.IVUS_POS) {
        const p = les[phase];
        const d = ivusDerived(p.vesselCSA[pos as 'lesion'], p.lumenCSA[pos as 'lesion'], p.maxPT[pos as 'lesion'], p.minPT[pos as 'lesion']);
        if (d.plaqueCSA) entries.push([`${prefix}.${phase}.plaqueCSA.${pos}`, d.plaqueCSA]);
        if (d.plaqueBurden) entries.push([`${prefix}.${phase}.plaqueBurden.${pos}`, d.plaqueBurden]);
        if (d.eccentricity) entries.push([`${prefix}.${phase}.eccentricity.${pos}`, d.eccentricity]);
      }
    }
    if (!entries.length) return app.toast('血管CSA・内腔CSA（偏心率は最大/最小プラーク厚）を入力してください', 'err');
    app.form!.setMany(entries);
  };
  const derived = new Set(['plaqueCSA', 'plaqueBurden', 'eccentricity']);
  return (
    <div>
      <table className="ivus-tbl">
        <thead>
          <tr>
            <th className="left">対象部位</th>
            <th colSpan={6} className="left">
              <TextF path={sitePath} w={180} list={O.CAG_SEGMENTS.map((s) => s.key)} placeholder="Pressure Wire の病変と共通" />
              <TextF path="device" label="カテーテル" lw={70} w={140} list={['OptiCross', 'AltaView', 'Eagle Eye', 'Dragonfly(OCT)', 'FastView(OFDI)']} />
              {!base && <span className="muted small">（未入力）</span>}
              <span style={{ marginLeft: 'auto' }}>
                <DelRowBtn path="/report.pressureIvus.lesions" index={index} create={createIvusLesion} what="病変" linked={PW_LINK} note={DEL_NOTE} text="この病変を削除" />
              </span>
            </th>
          </tr>
          <tr>
            <th />
            <th colSpan={3}>Pre</th>
            <th colSpan={3}>Post</th>
          </tr>
          <tr>
            <th />
            {['pre', 'post'].map((ph) =>
              O.IVUS_POS.map(([k, l]) => (
                <th key={ph + k} className="small">
                  {k === 'lesion' ? l : `対象セグメント ${l}`}
                </th>
              )),
            )}
          </tr>
        </thead>
        <tbody>
          {O.IVUS_METRICS.map(([m, l]) => (
            <tr key={m}>
              <th className="left">{l}{derived.has(m) && <span className="muted small"> *</span>}</th>
              {['pre', 'post'].map((ph) =>
                O.IVUS_POS.map(([k]) => (
                  <td key={ph + k}>
                    <NumF path={`${ph}.${m}.${k}`} w={90} />
                  </td>
                )),
              )}
            </tr>
          ))}
          <tr>
            <th className="left">性状</th>
            <td colSpan={6}>
              <Row gap={20}>
                <CheckF path="fibrofatty" label="fibrofatty" />
                <CheckF path="fibrous" label="fibrous" />
                <CheckF path="calcification" label="calcification(" />
                <NumF path="calcDegree" w={44} unit=")度" />
              </Row>
            </td>
          </tr>
        </tbody>
      </table>
      <Row style={{ marginTop: 6 }}>
        <Btn small onClick={calc}>* 派生値を算出（プラークCSA・面積率・偏心率）</Btn>
        <TextF path="comment" label="コメント" lw={60} w={420} />
      </Row>
    </div>
  );
}

/** Pressure / IVUS */
export function PressureIvusScreen() {
  const [tabSel, setTab] = useState('pw');
  const pi = useApp().draft!.report.pressureIvus;
  const n = Math.max(1, pi.pressure.length);
  const tab = tabSel !== 'pw' && Number(tabSel.slice(1)) >= n ? 'pw' : tabSel;
  return (
    <ScreenFrame>
      <Scope path="/report.pressureIvus">
        <div className="tabs-with-add">
          <Tabs
            active={tab}
            onChange={setTab}
            tabs={[
              { key: 'pw', label: 'Pressure Wire', hasData: hasAnyValue(pi.pressure) },
              ...range(n).map((i) => ({
                key: `l${i}`,
                label: `Lesion ${i + 1}${pi.pressure[i]?.lesion ? ` ${pi.pressure[i].lesion}` : ''}`,
                hasData: hasAnyValue(pi.lesions[i]),
              })),
            ]}
          />
          <AddRowBtn path="pressure" max={LIST_MAX.pressure} create={createPressureCol} label="Lesion" title="病変（Pressure Wire の列と Lesion タブ）を追加" linked={IVUS_LINK} />
        </div>
        <div className="tab-body">
          {tab === 'pw' ? (
            <PressureWireTab />
          ) : (
            <Scope path={`lesions.${tab.slice(1)}`} key={tab}>
              <IvusLesionTab index={Number(tab.slice(1))} />
            </Scope>
          )}
        </div>
      </Scope>
    </ScreenFrame>
  );
}
