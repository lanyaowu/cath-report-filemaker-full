import { useVal } from '../../form/FormContext';
import { Calc, CheckF, NumF, TextAreaF, TextF } from '../../form/fields';
import { Row } from '../../components/common/ui';
import * as O from '../../constants/options';
import { credoScore, judgeHbr } from '../../utils/calc';
import type { Pci } from '../../types/model';

/** 出血・血栓リスク タブ scope: report.pci */
export function BleedingRiskTab() {
  const risk = useVal<Pci['risk']>('risk');
  const hbr = judgeHbr(risk.hbrMajor, risk.hbrMinor);
  const credo = credoScore(risk.credo, O.CREDO_POINTS);
  const anyCredo = Object.values(risk.credo).some(Boolean);

  return (
    <div className="risk-layout">
      <Row>
        <CheckF path="risk.staged" label="Staged PCI" />
        <TextF path="risk.stagedText" w={480} readOnly={!risk.staged} />
      </Row>
      <div className="cols" style={{ alignItems: 'flex-start', gap: 24 }}>
        <div style={{ flex: 1 }}>
          <div className="sub-title">高出血リスク</div>
          <p className="small">少なくとも主要項目を1つ、あるいは副次項目を2つ満たした場合に高出血リスク(HBR)と定義する。</p>
          <div className="cols" style={{ alignItems: 'flex-start' }}>
            <div style={{ flex: 1.2 }}>
              <div className="small">＜主要項目＞</div>
              {O.HBR_MAJOR.map(([k, l]) => (
                <div key={k}>
                  <CheckF path={`risk.hbrMajor.${k}`} label={l} />
                </div>
              ))}
            </div>
            <div style={{ flex: 1 }}>
              <div className="small">＜副次項目＞</div>
              {O.HBR_MINOR.map(([k, l]) => (
                <div key={k}>
                  <CheckF path={`risk.hbrMinor.${k}`} label={l} />
                </div>
              ))}
            </div>
          </div>
          <Calc label={<b style={{ color: 'red' }}>High Bleeding Risk:</b>} lw={150} value={hbr} w={80} className={hbr === 'HBR' ? 'abn' : ''} />
        </div>

        <div style={{ flex: 1 }}>
          <div className="sub-title">血栓リスク</div>
          <p className="small">
            血栓リスク(心筋梗塞・ステント血栓症・虚血性脳卒中)の予測スコア（CREDO-Kyoto リスクスコア）
            <br />
            0〜1：低リスク　2〜3：中リスク　4≦：高リスク
          </p>
          <table className="credo">
            <tbody>
              {O.CREDO_ITEMS.map(([k, l, p]) => (
                <tr key={k}>
                  <td><CheckF path={`risk.credo.${k}`} label={l} /></td>
                  <td className="num">{p}</td>
                </tr>
              ))}
              <tr className="sum">
                <td>スコアの範囲</td>
                <td className="num">0〜12</td>
              </tr>
            </tbody>
          </table>
          <Calc
            label={<b style={{ color: 'red' }}>血栓リスクスコア:</b>}
            lw={150}
            value={anyCredo ? `${credo.score} 点（${credo.level}）` : ''}
            w={140}
            className={credo.score >= 4 ? 'abn' : ''}
          />
          <div className="sub-title" style={{ marginTop: 6 }}>ステント血栓症リスク因子</div>
          <div className="check-grid cg-2">
            {O.ST_RISK.map(([k, l]) => (
              <CheckF key={k} path={`risk.st.${k}`} label={l} />
            ))}
          </div>
          <Row style={{ marginTop: 6 }} align="flex-start">
            <NumF path="risk.daptMonths" label={<b>方針 DAPT推奨期間</b>} lw={130} w={40} unit="ヶ月" />
            <div style={{ flex: 1 }}>
              <TextAreaF path="risk.memo" label={<b>Memo</b>} lw={40} rows={4} />
            </div>
          </Row>
        </div>
      </div>
    </div>
  );
}
