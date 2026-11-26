import { useState, type ReactNode } from 'react';
import { Scope, useVal } from '../../form/FormContext';
import { CheckF, NumF, RadioF, TextF } from '../../form/fields';
import { Tabs } from '../../components/common/ui';
import * as O from '../../constants/options';
import { useLesions } from './LesionGrid';
import type { PciLesion } from '../../types/model';

const KV = ({ label, children }: { label: string; children: ReactNode }) => (
  <tr>
    <th>{label}</th>
    <td>{children}</td>
  </tr>
);

/** 検索用タブ：病変単位の主要項目を1画面に集約（各タブと同じデータを参照） scope: report.pci */
export function SearchTab() {
  const [idx, setIdx] = useState('0');
  const lesions = useVal<PciLesion[]>('lesions');
  const LESIONS = useLesions();
  const cur = Number(idx) < LESIONS.length ? idx : '0';
  return (
    <div>
      <Tabs
        small
        active={cur}
        onChange={setIdx}
        tabs={LESIONS.map((i) => ({ key: String(i), label: `病変${i + 1} ${lesions[i].target}`, hasData: !!lesions[i].target }))}
      />
      <Scope path={`lesions.${cur}`}>
        <table className="tbl search-top">
          <thead>
            <tr>
              <th>Target</th>
              {O.PCI_TECH.slice(0, 10).map(([k, l]) => (
                <th key={k} className="vt">{l}</th>
              ))}
              <th>Pre</th>
              <th>Post</th>
              <th>TIMI</th>
              <th>Comment</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><TextF path="target" w={140} /></td>
              {O.PCI_TECH.slice(0, 10).map(([k]) => (
                <td key={k} className="c"><CheckF path={`summary.tech.${k}`} /></td>
              ))}
              <td><NumF path="summary.pre" w={70} /></td>
              <td><NumF path="summary.post" w={70} /></td>
              <td><TextF path="summary.timiPost" w={50} list={O.TIMI} /></td>
              <td><TextF path="summary.comment" w={300} /></td>
            </tr>
          </tbody>
        </table>

        <div className="search-blocks">
          <table className="kv-tbl">
            <tbody>
              <KV label="Type"><TextF path="type" w="100%" list={O.LESION_TYPES} /></KV>
              <KV label="de novo..."><TextF path="deNovoMajor" w="100%" list={O.DENOVO_MAJOR} /></KV>
              {[...O.MORPH_YN, ...O.MORPH_YN2].map(([k, l]) => (
                <KV key={k} label={l}><RadioF path={`morph.${k}`} options={O.YN_OPTS} compact /></KV>
              ))}
              <KV label="Angulation"><TextF path="angulation" w="100%" list={O.ANGULATION} /></KV>
              <KV label="ProximalTortuosity"><TextF path="proximalTortuosity" w="100%" list={O.TORTUOSITY} /></KV>
              <KV label="Age of Occlusion"><TextF path="ageOfOcclusion" w="100%" /></KV>
              <KV label="Branch Protection"><TextF path="branchProtection" w="100%" /></KV>
              <KV label="Ref. Length">
                <NumF path="lengthA" w="30%" />
                <NumF path="pre.ref" w="30%" />
              </KV>
              <KV label="Pre %,MLD">
                <NumF path="pre.pct" w="45%" />
                <NumF path="pre.mld" w="45%" />
              </KV>
              <KV label="Post %,MLD">
                <NumF path="post.pct" w="45%" />
                <NumF path="post.mld" w="45%" />
              </KV>
              <KV label="Technique"><TextF path="technique" w="100%" /></KV>
              <KV label="BMS選択の理由"><TextF path="bmsReason1" w="100%" /></KV>
            </tbody>
          </table>
          <table className="kv-tbl">
            <tbody>
              <KV label="病変形態(post)"><TextF path="device.morphPost" w="100%" /></KV>
              {[0, 1, 2, 3, 4, 5, 6].map((k) => (
                <DeviceKV key={k} k={k} />
              ))}
              <KV label="理由"><TextF path="device.reason" w="100%" /></KV>
              <KV label="結果"><TextF path="device.result" w="100%" list={O.PCI_RESULTS} /></KV>
            </tbody>
          </table>
          <table className="kv-tbl">
            <tbody>
              <KV label="ICT or IVT"><TextF path="ict.type" w="100%" list={['ICT', 'IVT']} /></KV>
              <KV label="血栓溶解剤"><TextF path="ict.agent" w="100%" list={['ウロキナーゼ', 't-PA', 'モンテプラーゼ']} /></KV>
              <KV label="投与量"><TextF path="ict.dose" w="100%" /></KV>
              <KV label="TIMI Pre"><TextF path="summary.timiPre" w="100%" list={O.TIMI} /></KV>
              <KV label="TIMI Post"><TextF path="summary.timiPost" w="100%" list={O.TIMI} /></KV>
              <KV label="結果"><TextF path="ict.result" w="100%" /></KV>
            </tbody>
          </table>
        </div>
      </Scope>
    </div>
  );
}

function DeviceKV({ k }: { k: number }) {
  return (
    <>
      <KV label={`Device${k + 1}`}>
        <TextF path={`device.items.${k}.category`} w="34%" list={O.DEVICE_CATEGORIES} />
        <TextF path={`device.items.${k}.name`} w="62%" />
      </KV>
      <KV label="サイズ.長さ.圧">
        <NumF path={`device.items.${k}.size`} w="30%" />
        <NumF path={`device.items.${k}.length`} w="30%" />
        <NumF path={`device.items.${k}.pressure`} w="30%" />
      </KV>
    </>
  );
}
