import { useState } from 'react';
import { useApp } from '../../state/AppContext';
import { CheckF, DateF, Fld, NumF, RadioF, TextAreaF, TextF, TripleF } from '../../form/fields';
import { useVal } from '../../form/FormContext';
import { Btn, Panel } from '../../components/common/ui';
import { MasterDialog } from '../../components/dialogs/MasterDialog';
import * as O from '../../constants/options';

/** 主治医・術者・紹介医（scope: report.cathRecord.doctors）。術者・助手は3名まで */
export function DoctorsPanel() {
  const app = useApp();
  const [dlg, setDlg] = useState(false);
  const docs = app.masters.doctors;
  return (
    <Panel title="主治医・術者・紹介医" right={<Btn small onClick={() => setDlg(true)}>マスタ編集</Btn>}>
      <TextF path="attending" label="主治医" lw={72} w={110} list={docs} />
      <TextF path="outpatient" label="外来主治医" lw={72} w={110} list={docs} />
      <Fld label="術者" lw={72}>
        {[0, 1, 2].map((i) => (
          <TextF key={i} path={`operators.${i}`} w={82} list={docs} />
        ))}
      </Fld>
      <Fld label="助手" lw={72}>
        {[0, 1, 2].map((i) => (
          <TextF key={i} path={`assistants.${i}`} w={82} list={docs} />
        ))}
      </Fld>
      <TextF path="referralHospital" label="紹介病院" lw={72} w={160} list={app.masters.hospitals} />
      <TextF path="referralDoctor" label="紹介医" lw={72} w={110} />
      {dlg && <MasterDialog initialTab="doctors" onClose={() => setDlg(false)} />}
    </Panel>
  );
}

/** Hemodynamics（scope: report.cathRecord.hemo） */
export function HemodynamicsPanel() {
  const app = useApp();
  return (
    <Panel title="Hemodynamics" right={<Btn small onClick={() => app.toast('ポリグラフ連携は未設定です', 'err')}>数値取得</Btn>}>
      <div className="hemo-grid">
        <div>
          {O.HEMO_TRIPLES.map(([k, l]) => (
            <TripleF key={k} path={`pressures.${k}`} label={l} lw={46} w={36} />
          ))}
        </div>
        <div>
          {O.HEMO_VALUES_RIGHT.map(([k, l]) => (
            <NumF key={k} path={`values.${k}`} label={l} lw={44} w={52} />
          ))}
        </div>
      </div>
      <div className="hemo-grid" style={{ marginTop: 6 }}>
        <div>
          {O.HEMO_VALVE.map(([k, l]) => (
            <NumF key={k} path={`values.${k}`} label={l} lw={46} w={56} />
          ))}
        </div>
        <div>
          {O.HEMO_SHUNT.map(([k, l]) => (
            <NumF key={k} path={`values.${k}`} label={l} lw={44} w={52} />
          ))}
        </div>
      </div>
      <div className="muted small">（収縮期 / 拡張期 / 平均）mmHg</div>
    </Panel>
  );
}

/** 転帰および予後など（scope: report.cathRecord.prognosis） */
export function PrognosisPanel() {
  const app = useApp();
  return (
    <Panel title="転帰および予後など">
      <DateF path="deathDate" label="死亡日" lw={130} />
      <DateF path="confirmDate" label="確認日" lw={130} />
      <TextF path="confirmer" label="確認者" lw={130} w={128} list={app.masters.doctors} />
      <TextAreaF path="comment" label="予後コメント" lw={130} rows={2} />
      <DateF path="transferDate" label="転帰日" lw={130} />
      <TextF path="maceRelation" label="MACEと当院経過関係" lw={130} w={200} list={['当院通院中', '紹介元通院', '転院', '死亡', '不明']} />
      <TextF path="angioFuExclude" label="AngioFU対象外理由" lw={130} w={200} list={['高齢', '腎機能障害', '本人希望せず', '他院フォロー', '死亡']} />
      <TextF path="angioFuExclude2" label="" lw={130} w={200} />
    </Panel>
  );
}

/** その他（scope: report.cathRecord.other） */
export function OtherPanel() {
  return (
    <Panel title="その他">
      <Fld label="Study1" lw={46}>
        <TextF path="study1" w={130} />
        <TextF path="study2" label="2" lw={14} w={130} />
      </Fld>
      <TextF path="memo" label="メモ" lw={46} w={290} />
    </Panel>
  );
}

/** 合併症（全検査共通。scope: report.cathRecord.complications） */
export function ComplicationsPanel() {
  const status = useVal<string>('status');
  const off = status !== 'yes';
  return (
    <Panel title="合併症（全検査共通）" right={<RadioF path="status" options={O.UMU_OPTS} compact />}>
      <div className={`check-grid cg-3 ${off ? 'disabled-box' : ''}`}>
        {O.CATH_COMP.map(([k, l]) => (
          <CheckF key={k} path={`items.${k}`} label={l} />
        ))}
      </div>
      <TextF path="detail" label="内容・対応" lw={70} w="calc(100% - 80px)" />
      <div className="muted small">PCI の手技に関わる詳細は PCI 画面（Complication・J-PCI）にも記録します。</div>
    </Panel>
  );
}
