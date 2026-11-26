import { useApp } from '../../state/AppContext';
import { useField, useVal } from '../../form/FormContext';
import { CheckF, NumF, RadioF, TextAreaF, TextF } from '../../form/fields';
import { Btn, Note, Row } from '../../components/common/ui';
import * as O from '../../constants/options';
import { jcsBand } from '../../utils/clinical';
import type { CagLvg } from '../../types/model';
import { AddRowBtn, DelRowBtn, range, useCount } from '../../form/repeat';
import { LIST_MAX, createCollateral, createGraft } from '../../model/defaults';
import { PastCagCopy, PastCommentCopy } from './PastCopy';

/** 表セル用ラジオ（同じ値を再クリックで解除） */
function CellRadio({ path, value }: { path: string; value: string }) {
  const f = useField<string>(path);
  return (
    <input
      type="radio"
      className={f.changed ? 'changed' : ''}
      checked={f.value === value}
      onChange={() => f.set(value)}
      onClick={() => f.value === value && f.set('')}
      aria-label={value}
      value={value}
      data-path={f.full}
    />
  );
}

function CellCheck({ path }: { path: string }) {
  const f = useField<boolean>(path);
  return <input type="checkbox" className={f.changed ? 'changed' : ''} checked={!!f.value} onChange={(e) => f.set(e.target.checked)} data-path={f.full} />;
}

function SegmentTable() {
  const app = useApp();
  const segments = useVal<CagLvg['cag']['segments']>('segments');
  const setAllNormal = () =>
    app.form!.setMany(
      O.CAG_SEGMENTS.filter((s) => !segments[s.key]?.stenosis).map((s) => [`report.cagLvg.cag.segments.${s.key}.stenosis`, 'Normal'] as [string, unknown]),
    );
  return (
    <table className="seg-tbl">
      <thead>
        <tr>
          <th>
            <button type="button" className="normal-btn" onClick={setAllNormal} title="未入力のセグメントをすべて Normal にする">
              Normal
            </button>
          </th>
          {O.SEG_SIZES.map((s) => (
            <th key={s} className="vt">{s}</th>
          ))}
          <th className="vt sep-l">Calcification</th>
          {O.STENOSIS.map((s, i) => (
            <th key={s} className={`vt ${i === 0 ? 'sep-l' : ''} ${O.STENOSIS_SIGNIFICANT.has(s) ? 'sig' : ''}`}>
              {s === '100' ? '100(%)' : s}
            </th>
          ))}
          {O.SEG_FLAGS.map(([k, l], i) => (
            <th key={k} className={`vt ${i === 0 ? 'sep-l' : ''}`}>{l}</th>
          ))}
          <th className="sep-l jcs-h" title="JCS 標準（SEAMAT）の狭窄度区分。AHA 分類を区間の上限で対応付けて自動表示">JCS区分</th>
        </tr>
      </thead>
      <tbody>
        {O.CAG_SEGMENTS.map((s) => {
          const p = `segments.${s.key}`;
          const sten = segments[s.key]?.stenosis;
          return (
            <tr key={s.key} className={`${s.groupStart ? 'grp' : ''} ${O.STENOSIS_SIGNIFICANT.has(sten) ? 'row-sig' : ''}`}>
              <th className="seg-name">{s.label}</th>
              {O.SEG_SIZES.map((v) => (
                <td key={v}><CellRadio path={`${p}.size`} value={v} /></td>
              ))}
              <td className="sep-l"><CellCheck path={`${p}.calc`} /></td>
              {O.STENOSIS.map((v, i) => (
                <td key={v} className={`${i === 0 ? 'sep-l' : ''} ${O.STENOSIS_SIGNIFICANT.has(v) ? 'sig' : ''}`}>
                  <CellRadio path={`${p}.stenosis`} value={v} />
                </td>
              ))}
              {O.SEG_FLAGS.map(([k], i) => (
                <td key={k} className={i === 0 ? 'sep-l' : ''}><CellCheck path={`${p}.${k}`} /></td>
              ))}
              <td className="sep-l jcs-c">{jcsBand(sten)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

/** 送達元 → 送達先 / J / State */
function Collaterals() {
  const none = useVal<boolean>('collateralsNone');
  const n = useCount('collaterals');
  return (
    <div className={`route-box ${none ? 'disabled-box' : ''}`}>
      {/* 見出しは入力行と同じ幅・間隔（送達元〜送達先 / J / State / ✖ の列）で並べる */}
      <div className="route-head">
        <span className="rh-lead" style={{ width: 210 }}>
          <b>Collaterals</b>
          <CheckF path="collateralsNone" label="なし" />
        </span>
        <span className="rh-col" style={{ width: 64 }}>J(Rentrop)</span>
        <span className="rh-col" style={{ width: 90 }}>State</span>
        <span className="rh-sp" />
      </div>
      {range(n).map((i) => (
        <div className="route-row" key={i}>
          <TextF path={`collaterals.${i}.from`} w={92} placeholder="送達元" list={['LAD', 'LAD septal', 'LCX', 'RCA', 'Conus', 'Kugel', 'Bridge', 'Epicardial']} readOnly={none} />
          <span className="arrow">→</span>
          <TextF path={`collaterals.${i}.to`} w={92} placeholder="送達先" list={O.CAG_SEGMENTS.map((s) => s.key)} readOnly={none} />
          <TextF path={`collaterals.${i}.grade`} w={64} list={O.RENTROP} readOnly={none} align="center" />
          <TextF path={`collaterals.${i}.state`} w={90} list={O.COLLATERAL_STATE} readOnly={none} />
          <DelRowBtn path="collaterals" index={i} create={createCollateral} what="側副血行" disabled={none} />
        </div>
      ))}
      <div className="rep-foot">
        <AddRowBtn path="collaterals" max={LIST_MAX.collaterals} create={createCollateral} label="側副血行を追加" disabled={none} />
      </div>
    </div>
  );
}

/** グラフト名称 → 吻合部 / 通行状態 */
function BypassGrafts() {
  const n = useCount('grafts');
  return (
    <div className="route-box">
      <div className="route-head">
        <span className="rh-lead" style={{ width: 216 }}>
          <b>Bypass Grafts</b>
        </span>
        <span className="rh-col" style={{ width: 110 }}>通行状態</span>
        <span className="rh-sp" />
      </div>
      {range(n).map((i) => (
        <div className="route-row" key={i}>
          <TextF path={`grafts.${i}.graft`} w={80} placeholder="グラフト" list={O.GRAFT_NAMES} />
          <span className="arrow">→</span>
          <TextF path={`grafts.${i}.anastomosis`} w={110} placeholder="吻合部" list={O.CAG_SEGMENTS.map((s) => s.key)} />
          <TextF path={`grafts.${i}.patency`} w={110} list={O.GRAFT_PATENCY} />
          <DelRowBtn path="grafts" index={i} create={createGraft} what="グラフト" />
        </div>
      ))}
      <div className="rep-foot">
        <AddRowBtn path="grafts" max={LIST_MAX.grafts} create={createGraft} label="グラフトを追加" />
      </div>
    </div>
  );
}

/** CAG タブ（scope: report.cagLvg.cag） */
export function CagTab() {
  const app = useApp();
  const segments = useVal<CagLvg['cag']['segments']>('segments');

  const deriveVessels = () => {
    const sig = (keys: string[], lmt = false) =>
      keys.some((k) => {
        const s = segments[k]?.stenosis;
        return lmt ? ['50', '75', '90', '99', '100'].includes(s) : O.STENOSIS_SIGNIFICANT.has(s);
      });
    const LMT = sig(['LMT5'], true);
    const LAD = sig(['LAD6', 'LAD7', 'LAD8', 'LAD9', 'LAD10']);
    const LCX = sig(['LCX11', 'HL', 'LCX12', 'LCX13', 'LCX14', 'LCX15']);
    const RCA = sig(['RCA1', 'RCA2', 'RCA3', 'RCA4AV', 'RCA4PD']);
    const count = [LAD || LMT, LCX || LMT, RCA].filter(Boolean).length;
    app.form!.setMany([
      ['report.cagLvg.cag.lesions', { count: String(count), LMT, LAD, LCX, RCA }],
    ]);
  };

  return (
    <div className="cag-layout">
      <div className="cag-left">
        <SegmentTable />
        <div className="center" style={{ marginTop: 6 }}>
          <PastCagCopy />
        </div>
      </div>
      <div className="cag-right">
        <div className="cols">
          <Collaterals />
          <BypassGrafts />
        </div>
        <div className="cols" style={{ alignItems: 'flex-start' }}>
          <div style={{ flex: 1 }}>
            <TextF path="complication" label="合併症" lw={50} w={260} />
            <RadioF path="squeezing" label="Squeezing" lw={130} options={O.PM2_OPTS} />
            <RadioF path="spasm" label="Spasm" lw={130} options={O.PM2_OPTS} />
            <TextF path="provocation" label="Provocation of Spasm" lw={130} w={120} list={['Ach', 'Er', '陰性']} />
            <TextF path="dominance" label="Dominance" lw={130} w={120} list={O.DOMINANCY} />
          </div>
          <div>
            <div className="boxed vessel-box">
              <Row>
                <NumF path="lesions.count" label="病変枝数" lw={60} w={40} />
                <Btn small onClick={deriveVessels} title="75%以上（LMTは50%以上）の狭窄から算出">所見から算出</Btn>
              </Row>
              <div className="grid2 tight">
                <CheckF path="lesions.LMT" label="LMT" />
                <CheckF path="lesions.LAD" label="LAD" />
                <CheckF path="lesions.LCX" label="LCX" />
                <CheckF path="lesions.RCA" label="RCA" />
              </div>
            </div>
            <Note>
              ※術前の本幹病変あるいは治療適用病変のみチェックしてください
              <br />
              BypassGraftでプロテクトされている場合はチェックを外してください
            </Note>
          </div>
          <div>
            <NumF path="syntax" label="Syntax Score" lw={90} w={56} />
            <NumF path="euro" label="Euro Score" lw={90} w={56} />
            <NumF path="japan" label="Japan Score" lw={90} w={56} />
          </div>
        </div>
        <div className="comment-head">
          <span>Comment</span>
          <PastCommentCopy target="report.cagLvg.cag.comment" />
        </div>
        <TextAreaF path="comment" rows={9} />
      </div>
    </div>
  );
}
