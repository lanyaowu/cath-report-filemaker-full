import { useApp } from '../../state/AppContext';
import { Fld, TextF } from '../../form/fields';
import { Btn, Panel } from '../../components/common/ui';
import * as O from '../../constants/options';

/** カテーテル（scope: report.cagLvg）：Approach 5項目＋Catheter 10項目（形状・サイズ） */
export function CatheterPanel() {
  const app = useApp();
  const copyFromRecord = () => {
    const e = app.draft!.report.cathRecord.exam;
    app.form!.setMany([
      ['report.cagLvg.approach.artery', e.approach],
      ['report.cagLvg.approach.arterySheath', { ...e.sheath }],
    ]);
  };
  return (
    <Panel title="カテーテル" right={<Btn small onClick={copyFromRecord}>カテ記録のアプローチを反映</Btn>}>
      <div className="catheter-layout">
        <div className="approach">
          <div className="sub-title">Approach</div>
          <div className="approach-grid">
            <TextF path="approach.artery" label="Artery" lw={50} w={120} list={O.APPROACHES} />
            <TextF path="approach.vein" label="Vein" lw={40} w={120} list={['Rt Femoral V', 'Lt Femoral V', 'Rt Internal Jugular V', 'Rt Brachial V']} />
            <Fld label="シース" lw={50}>
              <TextF path="approach.arterySheath.name" w={92} list={O.SHEATH_NAMES} placeholder="名称" />
              <TextF path="approach.arterySheath.size" w={34} list={O.SHEATH_SIZES} unit="Fr" align="right" />
            </Fld>
            <Fld label="シース" lw={40}>
              <TextF path="approach.veinSheath.name" w={92} list={O.SHEATH_NAMES} placeholder="名称" />
              <TextF path="approach.veinSheath.size" w={34} list={O.SHEATH_SIZES} unit="Fr" align="right" />
            </Fld>
            <TextF path="approach.support" label="サポート" lw={50} w={160} list={O.SUPPORTS} />
          </div>
        </div>
        <div className="catheters">
          <div className="sub-title">Catheter <span className="muted small">（形状 / サイズFr）</span></div>
          <div className="catheter-grid">
            {O.CATHETER_SLOTS.map(([k, l]) => (
              <Fld key={k} label={k.startsWith('custom') ? undefined : l} lw={62}>
                {k.startsWith('custom') && <TextF path={`catheters.${k}.label`} w={58} placeholder={l} />}
                <TextF path={`catheters.${k}.shape`} w={110} list={O.CATHETER_SHAPES} />
                <TextF path={`catheters.${k}.size`} w={34} list={O.SHEATH_SIZES} align="right" />
              </Fld>
            ))}
          </div>
        </div>
      </div>
    </Panel>
  );
}
