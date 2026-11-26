import type { ReactNode } from 'react';
import type { Draft, PciLesion } from '../../types/model';
import * as O from '../../constants/options';
import { ageAt, fmtDate } from '../../utils/date';
import { bsa } from '../../utils/calc';
import { accAhaSuggest, jcsBand, jctoScore, lesionSuccessSuggest, postStenosis, procedureMinutes, CTO_DURATION } from '../../utils/clinical';

/**
 * レポートの帳票（紹介医・カルテ添付用。G-41）。
 * 構成は「標準項目解説書」11章：適応 → 手技の概要 → 所見 → 治療 → 合併症 → 結論・方針。
 * 未入力の欄は出さない。Thymeleaf 版は templates/print.html が同じ構成。
 */
const has = (v: unknown) => v != null && String(v).trim() !== '';
const join = (xs: (string | false | null | undefined)[], sep = '、') => xs.filter((x): x is string => !!x && x.trim() !== '').join(sep);
const segLabel = (k: string) => (k === 'HL' ? 'HL' : `#${k.replace(/^\D+/, '')}`);

function Sec({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rp-sec">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function KV({ rows }: { rows: [string, ReactNode][] }) {
  const r = rows.filter(([, v]) => has(typeof v === 'string' ? v : v ? 'x' : ''));
  if (!r.length) return null;
  return (
    <table className="rp-kv">
      <tbody>
        {r.map(([k, v]) => (
          <tr key={k}>
            <th>{k}</th>
            <td>{v}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function ReportPrintBody({ d }: { d: Draft }) {
  const { patient: p, report: r } = d;
  const cr = r.cathRecord;
  const ex = cr.exam;
  const rk = cr.risk;
  const cag = r.cagLvg.cag;
  const lvg = r.cagLvg.lvg;
  const pci = r.pci;
  const mins = procedureMinutes(ex.startTime, ex.endTime);
  const risk = join([
    ...(['DM', 'HT', 'HL'] as const).map((k) => (rk[k] === '+' ? k : '')),
    rk.smoking === '+' ? '喫煙' : rk.smoking === 'past' ? '喫煙（過去）' : '',
    rk.HD === '+' ? '透析' : '',
    rk.family === '+' ? '家族歴' : '',
  ]);
  const hx = join([
    rk.priorMI === 'yes' && '心筋梗塞', rk.priorHF === 'yes' && '心不全', rk.pciHx === 'yes' && 'PCI', rk.cabgHx === 'yes' && 'CABG',
    rk.renal === '+' && '腎不全', rk.copd === '+' && 'COPD', rk.pad === '+' && 'AAA/PAD',
  ]);
  const segs = O.CAG_SEGMENTS.map((s) => ({ key: s.key, f: cag.segments[s.key] })).filter(({ f }) => f && has(f.stenosis) && f.stenosis !== 'Normal');
  const sig = segs.filter(({ f }) => O.STENOSIS_SIGNIFICANT.has(f.stenosis));
  const lesions = pci.lesions.filter((l) => has(l.target));
  const wm = O.LV_SEGMENTS.filter(([k]) => has(lvg.wallMotion[k]) && lvg.wallMotion[k] !== 'N').map(
    ([k, l]) => `${l}：${O.WALL_MOTION.find((o) => o.value === lvg.wallMotion[k])?.label ?? lvg.wallMotion[k]}`,
  );
  const crComp = O.CATH_COMP.filter(([k]) => cr.complications.items[k]).map(([, l]) => l);
  const jComp = O.JPCI_COMP.filter(([k]) => pci.jpci.info.compItems[k]).map(([, l]) => l);
  const devices = (l: PciLesion) => l.device.items.filter((x) => has(x.name) || has(x.category)).map((x) => join([x.category, x.name, has(x.size) ? `${x.size}${has(x.length) ? `×${x.length}` : ''}mm` : '', has(x.pressure) ? `${x.pressure}atm` : ''], ' '));

  return (
    <div className="rp">
      <header className="rp-head">
        <h2>心臓カテーテル検査・治療レポート</h2>
        <div className="rp-status">{r.status}{r.verified ? '・照合済' : ''}</div>
      </header>
      <table className="rp-pt">
        <tbody>
          <tr>
            <th>施行日</th><td>{fmtDate(r.header.studyDate)}</td>
            <th>ID</th><td>{p.patientId}</td>
            <th>氏名</th><td>{p.name}{has(p.kana) ? `（${p.kana}）` : ''}</td>
          </tr>
          <tr>
            <th>性別・年齢</th><td>{join([p.sex === 'M' ? '男性' : p.sex === 'F' ? '女性' : '', has(ageAt(p.birthDate, r.header.studyDate)) ? `${ageAt(p.birthDate, r.header.studyDate)}歳` : ''], '・')}</td>
            <th>身長・体重</th><td>{join([has(cr.body.height) ? `${cr.body.height}cm` : '', has(cr.body.weight) ? `${cr.body.weight}kg` : '', bsa(cr.body.height, cr.body.weight) ? `BSA ${bsa(cr.body.height, cr.body.weight)}m²` : ''], '・')}</td>
            <th>Cine/PCI No</th><td>{join([r.header.cineNo, r.header.pciNo], ' / ')}</td>
          </tr>
        </tbody>
      </table>

      <Sec title="適応">
        <KV
          rows={[
            ['区分', join([ex.urgency, O.PURPOSES.filter(([k]) => (ex.purposes as any)[k]).map(([, l]) => l).join('・'), ex.purposes.followUp ? `Follow-up${has(ex.followUpReason) ? `（${ex.followUpReason}）` : ''}` : ''], '／')],
            ['疾病・診断', join([ex.disease, ex.diagnosis], '／')],
            ['危険因子', risk],
            ['既往・併存症', hx],
            ['紹介元', join([cr.doctors.referralHospital, cr.doctors.referralDoctor], ' ')],
          ]}
        />
      </Sec>

      <Sec title="手技の概要">
        <KV
          rows={[
            ['術者', join([...cr.doctors.operators, ...cr.doctors.assistants.map((a) => (has(a) ? `${a}（助手）` : ''))])],
            ['検査項目', ex.examItems],
            ['アプローチ', join([ex.approach, join([ex.sheath.name, has(ex.sheath.size) ? `${ex.sheath.size}Fr` : ''], ' ')], '・')],
            ['手技時間', has(ex.startTime) || has(ex.endTime) ? `${ex.startTime}〜${ex.endTime}${mins != null ? `（${mins}分）` : ''}` : ''],
            ['造影剤', join([ex.contrast.agent, has(ex.contrast.volume) ? `${ex.contrast.volume}mL` : ''], ' ')],
            ['透視・線量', join([has(ex.fluoroTime) ? `透視 ${ex.fluoroTime}分` : '', has(ex.totalDose) ? `総線量 ${ex.totalDose}mGy` : ''], '、')],
            ['補助循環', r.cagLvg.approach.support],
          ]}
        />
      </Sec>

      <Sec title="所見">
        <KV
          rows={[
            ['Dominance', cag.dominance],
            ['病変枝数', has(cag.lesions.count) ? `${cag.lesions.count}枝${join([cag.lesions.LMT && 'LMT', cag.lesions.LAD && 'LAD', cag.lesions.LCX && 'LCX', cag.lesions.RCA && 'RCA']) ? `（${join([cag.lesions.LMT && 'LMT', cag.lesions.LAD && 'LAD', cag.lesions.LCX && 'LCX', cag.lesions.RCA && 'RCA'])}）` : ''}` : ''],
            ['有意狭窄', sig.length ? join(sig.map(({ key, f }) => `${segLabel(key)} ${f.stenosis}%`)) : segs.length ? 'なし' : ''],
            ['側副血行', cag.collateralsNone ? 'なし' : join(cag.collaterals.filter((c) => has(c.from) || has(c.to)).map((c) => `${c.from}→${c.to}${has(c.grade) ? `（Rentrop ${c.grade}）` : ''}`))],
            ['グラフト', join(cag.grafts.filter((g) => has(g.graft)).map((g) => `${g.graft}→${g.anastomosis} ${g.patency}`))],
            ['冠攣縮', join([cag.spasm === '+' ? '攣縮あり' : cag.spasm === '-' ? '攣縮なし' : '', has(cag.provocation) ? `誘発：${cag.provocation}` : ''], '、')],
            ['スコア', join([has(cag.syntax) ? `SYNTAX ${cag.syntax}` : '', has(cag.euro) ? `EuroSCORE ${cag.euro}` : '', has(cag.japan) ? `JapanSCORE ${cag.japan}` : ''])],
          ]}
        />
        {segs.length > 0 && (
          <table className="rp-tbl">
            <thead>
              <tr><th>セグメント</th><th>狭窄度（AHA）</th><th>JCS 区分</th><th>所見</th></tr>
            </thead>
            <tbody>
              {segs.map(({ key, f }) => (
                <tr key={key} className={O.STENOSIS_SIGNIFICANT.has(f.stenosis) ? 'rp-sig' : ''}>
                  <td>{segLabel(key)}</td>
                  <td>{f.stenosis}{/^\d+$/.test(f.stenosis) ? '%' : ''}</td>
                  <td>{jcsBand(f.stenosis)}</td>
                  <td>{join([f.calc && '石灰化', ...O.SEG_FLAGS.filter(([k]) => (f as any)[k]).map(([, l]) => l)])}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {(lvg.performed || has(lvg.values.EF)) && (
          <KV
            rows={[
              ['LVG', join([has(lvg.values.EF) ? `EF ${lvg.values.EF}%` : '', has(lvg.values.LVEDV) ? `EDV ${lvg.values.LVEDV}mL` : '', has(lvg.values.LVESV) ? `ESV ${lvg.values.LVESV}mL` : '', has(lvg.values.LVEDP) ? `LVEDP ${lvg.values.LVEDP}mmHg` : ''])],
              ['壁運動', wm.length ? join(wm) : O.LV_SEGMENTS.some(([k]) => lvg.wallMotion[k] === 'N') ? '異常なし' : ''],
              ['MR・その他', join([has(lvg.mr) ? `MR ${lvg.mr}度` : '', lvg.thrombus && 'LV内血栓', lvg.aneurysm && '心室瘤', lvg.apicalBallooning && '心尖部バルーニング', lvg.vsr && 'VSR', lvg.aog.performed && has(lvg.aog.ar) ? `AR ${lvg.aog.ar}度` : ''])],
            ]}
          />
        )}
        {has(cag.comment) && <p className="rp-text">{cag.comment}</p>}
      </Sec>

      {lesions.length > 0 && (
        <Sec title="治療（PCI）">
          <table className="rp-tbl">
            <thead>
              <tr><th>病変</th><th>Type</th><th>性状</th><th>狭窄度 術前→術後</th><th>TIMI</th><th>使用機器</th><th>成否</th></tr>
            </thead>
            <tbody>
              {lesions.map((l, i) => {
                const pre = has(l.pre.pct) ? l.pre.pct : l.summary.pre;
                const post = postStenosis(l);
                const sc = jctoScore(l);
                return (
                  <tr key={i}>
                    <td>{l.target}{has(l.targetSub) ? ` ${l.targetSub}` : ''}</td>
                    <td>{l.type || accAhaSuggest(l)?.type ? `${l.type || `（提案 ${accAhaSuggest(l)?.type}）`}` : ''}</td>
                    <td>{join([l.deNovoMajor, l.morph.cto === 'yes' ? `CTO${has(l.cto.duration) ? `（${CTO_DURATION.find((o) => o.value === l.cto.duration)?.label}）` : ''}${sc != null ? ` J-CTO ${sc}` : ''}` : '', l.morph.bifurcation === 'yes' ? `分岐部${has(l.bif.mainSide) ? `（${l.bif.mainSide}）` : ''}` : '', l.morph.calcification === 'yes' && '石灰化', l.morph.thrombus === 'yes' && '血栓'])}</td>
                    <td>{has(pre) || post != null ? `${pre}% → ${post ?? ''}%` : ''}<div className="rp-sub">{join([jcsBand('', pre), post != null ? jcsBand('', String(post)) : ''], ' → ')}</div></td>
                    <td>{join([l.summary.timiPre, l.summary.timiPost], ' → ')}</td>
                    <td>{join(devices(l), '／')}</td>
                    <td>{l.success || (lesionSuccessSuggest(l) ? `（判定 ${lesionSuccessSuggest(l)}）` : '')}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <KV
            rows={[
              ['手技の結果', pci.basic.result],
              ['イメージング', join(O.IMAGING_ITEMS.filter(([k]) => pci.jpci.info.imagingItems[k]).map(([, l]) => l))],
              ['補助循環', join(O.MCS_ITEMS.filter(([k]) => pci.jpci.info.mcsItems[k]).map(([, l]) => l))],
              ['DAPT 期間', has(pci.risk.daptMonths) ? `${pci.risk.daptMonths}か月` : ''],
            ]}
          />
          {has(cr.pciSummary) && <p className="rp-text">{cr.pciSummary}</p>}
        </Sec>
      )}

      <Sec title="合併症">
        {!has(cr.complications.status) && !has(pci.jpci.info.procComp) && <p className="rp-text muted">記載なし</p>}
        <KV
          rows={[
            ['検査全体', cr.complications.status === 'no' ? 'なし' : cr.complications.status === 'unknown' ? '不明' : join([...crComp, cr.complications.detail])],
            ['PCI（J-PCI）', pci.jpci.info.procComp === 'no' ? 'なし' : pci.jpci.info.procComp === 'unknown' ? '不明' : join(jComp)],
          ]}
        />
      </Sec>

      <Sec title="結論・方針">
        <KV
          rows={[
            ['治療方針', ex.treatmentPolicy],
            ['今後の方針', cr.futurePlan],
            ['コメント', cr.comment],
          ]}
        />
      </Sec>

      <footer className="rp-foot">
        <span>記載：{join([...cr.doctors.operators].slice(0, 1))}</span>
        <span>確認者署名：＿＿＿＿＿＿＿＿＿＿</span>
        <span>出力日：{fmtDate(new Date().toISOString().slice(0, 10))}</span>
      </footer>
      <div className="rp-note">狭窄度の JCS 区分は、AHA 分類（目視）を区間の上限で対応付けた参考値（QCA の実測値があれば実測値から）。</div>
    </div>
  );
}

/** 帳票の表示（画面の上に重ねて表示し、印刷時は帳票だけを出す） */
export function ReportPrintOverlay({ d, onClose }: { d: Draft; onClose: () => void }) {
  return (
    <div className="print-overlay">
      <div className="print-bar no-print">
        <b>検査報告書</b>
        <span className="muted small">未入力の欄は表示しません。A4 縦で印刷されます。</span>
        <button type="button" className="btn btn-primary" onClick={() => window.print()}>
          🖨 印刷
        </button>
        <button type="button" className="btn btn-normal" onClick={onClose}>
          閉じる
        </button>
      </div>
      <div className="print-page">
        <ReportPrintBody d={d} />
      </div>
    </div>
  );
}
